#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Search Blueprint
This blueprint handles the search functionality of the application.
"""

import json
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app, make_response
from flask_wtf.csrf import validate_csrf, ValidationError
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.models import db, SearchQuery, SearchResult, Person
from backend.search import search_database, parse_date_range
from backend.connectors import get_connector_for_database
from backend.utils import log_message
from backend.api_utils import search_status_response
import logging

logger = logging.getLogger(__name__)

search_bp = Blueprint("search", __name__)

@search_bp.route("/status", methods=["GET"])
def check_search_status():
    """
    AJAX endpoint to check the current search status
    Returns JSON with search status information
    """
    logger.info("Entering check_search_status endpoint")
    search_status = session.get('search_status', 'idle')
    start_time_str = session.get('search_start_time')
    current_query_id = session.get('current_query_id')
    search_errors_session = session.get('search_errors', [])

    logger.info(f"Session search_status: {search_status}")
    logger.info(f"Session current_query_id: {current_query_id}")
    logger.info(f"Session search_errors: {search_errors_session}")
    logger.info(f"Session search_start_time: {start_time_str}")
    
    # Check if search has been running too long
    if start_time_str and search_status == 'searching':
        try:
            start_time = datetime.fromisoformat(start_time_str)
            current_time = get_utc_now()
            duration = (current_time - start_time).total_seconds()
            
            # If search has been running for more than 45 seconds, consider it stuck
            if duration > 45:
                logger.warning(f"Search appears to be stuck, running for {duration:.2f}s")
                search_status = 'timeout'
                session['search_status'] = 'timeout'
                session.modified = True
        except Exception as e:
            logger.error(f"Error calculating search duration: {str(e)}")
    
    # Get any errors from the session
    # errors = session.get('search_errors', []) # Already fetched as search_errors_session
    redirect_url = None
    
    # Add redirect URL if search is complete and we have results
    if search_status == 'completed' and current_query_id:
        redirect_url = url_for('search.results')
    elif search_status in ('error', 'no_results', 'timeout'):
        redirect_url = url_for('search.index')
    
    # Use the standardized API response
    response_data = {
        "status": search_status,
        "errors": search_errors_session, # Use the variable already fetched
        "redirect_url": redirect_url,
        "query_id": current_query_id
    }
    logger.info(f"Returning search status response: {response_data}")
    return search_status_response(
        status=search_status,
        errors=search_errors_session, # Use the variable already fetched
        redirect_url=redirect_url,
        query_id=current_query_id
    )

def get_utc_now():
    """Helper function to get current UTC time"""
    return datetime.now(timezone.utc)

def get_search_results(query_id, page, per_page):
    """Get paginated search results from database by query ID"""
    try:
        # Fetch paginated results for this query
        pagination = SearchResult.query.filter_by(query_id=query_id).order_by(
            SearchResult.database,
            SearchResult.timestamp
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        # Extract the actual result data for the current page
        # The pagination object itself will be returned.
        # items_on_page = [result.result_data for result in pagination.items if result.result_data]
        return pagination # Return the whole pagination object
    except Exception as e:
        logger.error(f"Error fetching paginated results for query {query_id}: {str(e)}", exc_info=True)
        return None # Return None or an empty pagination object on error

def clean_expired_results():
    """Clean up old search results from database"""
    try:
        expiry = get_utc_now() - timedelta(days=7)  # Keep results for 7 days
        old_queries = SearchQuery.query.filter(SearchQuery.timestamp < expiry).all()
        
        for query in old_queries:
            # Delete associated results first
            SearchResult.query.filter_by(query_id=query.id).delete()
            db.session.delete(query)
        
        db.session.commit()
        logger.info(f"Cleaned up {len(old_queries)} expired search queries and their results")
    except Exception as e:
        logger.error(f"Error cleaning up expired results: {e}")
        db.session.rollback()

def save_search_results(query_obj, results):
    """Save search results to database with validation"""
    if not results:
        return 0
        
    saved_count = 0
    errors = []  # Initialize errors list
    batch_size = 100

    try:
        # Save results in batches to prevent memory issues
        for i in range(0, len(results), batch_size):
            batch = results[i:i + batch_size]
            result_objects = []
            
            for result in batch:
                try:
                    # Ensure result is a dict
                    result_data = result if isinstance(result, dict) else {}
                    
                    # Create result object with required fields
                    result_obj = SearchResult(
                        query_id=query_obj.id,
                        database=result_data.get('Database', 'Unknown'),
                        result_data=json.dumps(result_data)
                    )
                    
                    # Try to validate before saving
                    try:
                        result_obj.validate_result_data()
                        result_objects.append(result_obj)
                        saved_count += 1
                    except ValueError as ve:
                        # Add missing required fields if possible
                        if 'Title' not in result_data:
                            result_data['Title'] = 'Untitled'
                        if 'Authors' not in result_data:
                            result_data['Authors'] = []
                        if 'Publication Year' not in result_data:
                            result_data['Publication Year'] = 'Unknown'
                        if 'Database' not in result_data:
                            result_data['Database'] = 'Unknown'
                            
                        # Try validation again after fixing
                        result_obj.result_data = json.dumps(result_data)
                        try:
                            result_obj.validate_result_data()
                            result_objects.append(result_obj)
                            saved_count += 1
                        except ValueError as ve2:
                            errors.append(f"Invalid result data after fix attempt: {str(ve2)}")
                            continue
                            
                except Exception as e:
                    errors.append(f"Error processing result: {str(e)}")
                    continue
            
            if result_objects:
                try:
                    db.session.bulk_save_objects(result_objects)
                    db.session.commit()
                    logger.info(f"Saved batch of {len(result_objects)} results")
                except Exception as e:
                    db.session.rollback()
                    errors.append(f"Error saving batch: {str(e)}")
                    continue
        
        if errors:
            logger.warning(f"Encountered {len(errors)} errors while saving results: {'; '.join(errors)}")
            
        return saved_count
        
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Failed to save search results: {str(e)}")

@search_bp.route("/", methods=["GET", "POST"])
def index():
    """Handle search form display and search execution"""
    logger.info(f"Entering search index route - Method: {request.method}")
    
    if request.method == "POST":
        logger.info("Processing POST request for search")
        logger.info(f"Request form data: {request.form.to_dict(flat=False)}")
        try:
            # CSRF validation
            csrf_token = request.form.get('csrf_token')
            logger.info(f"CSRF token received: {csrf_token[:20] if csrf_token else 'None'}...")
            
            if not csrf_token:
                logger.warning("Missing CSRF token in search request")
                flash('Sicherheitstoken fehlt. Bitte laden Sie die Seite neu.', 'error')
                return redirect(url_for('search.index'))
            
            try:
                validate_csrf(csrf_token)
                logger.info("CSRF validation successful")
            except ValidationError as e:
                logger.warning(f"Invalid CSRF token in search request: {str(e)}")
                flash('Ungültiges oder abgelaufenes Sicherheitstoken. Bitte laden Sie die Seite neu.', 'error')
                return redirect(url_for('search.index'))
            
            # Get and validate search parameters
            search_mode = request.form.get('search_mode', 'simple')
            selected_databases = request.form.getlist('databases')
            
            # For person search, also check person_databases field
            if search_mode == 'person' and not selected_databases:
                selected_databases = request.form.getlist('person_databases')
            
            # If still no databases, try both (defensive programming)
            if not selected_databases:
                all_db_fields = request.form.getlist('databases') + request.form.getlist('person_databases')
                selected_databases = list(set(all_db_fields))  # Remove duplicates
            
            # Debug logging
            # logger.info(f"Search request: mode={search_mode}") # Will be logged later with query
            # logger.info(f"Form data: {dict(request.form.lists())}") # Already logged as request.form.to_dict(flat=False)
            # logger.info(f"Selected databases: {selected_databases}") # Will be logged later with query
            
            # Determine query based on search mode
            query = None
            main_search_term = None # For advanced search logging
            if search_mode == 'simple':
                query = request.form.get('simple_query_content', '').strip()
            elif search_mode == 'person':
                query = _construct_person_search_query(request.form)
            elif search_mode == 'advanced':
                # Main search terms for advanced search
                query = request.form.get('search_query', '').strip() # This will be the base for advanced_query_str
                main_search_term = query # Store the original main term for logging
            else:
                logger.error(f"Invalid search mode: {search_mode}")
                flash('Unbekannter Suchmodus.', 'error')
                return redirect(url_for('search.index'))

            # Validate query and database selection
            # For advanced search, the main query might be empty if only other fields are used,
            # but _construct_advanced_query_string handles this.
            # However, for simple/person, the constructed query must be non-empty.
            if search_mode != 'advanced' and not query:
                logger.warning(f"Empty search query submitted for {search_mode} mode.")
                flash('Bitte geben Sie einen Suchbegriff ein.', 'warning')
                return redirect(url_for('search.index'))
            elif search_mode == 'advanced' and not main_search_term and not request.form.get('additional_terms') and not request.form.get('advanced_selected_person_ids') and not request.form.get('author') and not request.form.get('year_from') and not request.form.get('year_to') and not request.form.get('title'):
                logger.warning("Empty search query and no advanced criteria submitted for advanced mode.")
                flash('Bitte geben Sie mindestens einen Suchbegriff oder ein Suchkriterium ein.', 'warning')
                return redirect(url_for('search.index'))

            if not selected_databases:
                logger.warning("No databases selected for search")
                flash('Bitte wählen Sie mindestens eine Datenbank aus.', 'warning')
                return redirect(url_for('search.index'))
            
            # Log determined parameters
            log_query_identifier = main_search_term if search_mode == 'advanced' else query
            logger.info(f"Search parameters determined: search_mode='{search_mode}', query='{log_query_identifier}', selected_databases={selected_databases}")

            # Clear any existing search status
            _clear_search_session_data()
            
            # Set initial search status
            session['search_status'] = 'searching'
            session['search_start_time'] = get_utc_now().isoformat()
            session.modified = True
            
            # logger.info(f"Starting search: mode={search_mode}, databases={selected_databases}") # Covered by the more detailed log above

            # Store the main search term for display and for SearchQuery record
            # main_search_term is already set for advanced, query holds the value for simple/person
            term_for_storage = main_search_term if search_mode == 'advanced' else query

            try:
                # `search_database` now returns a list of outcome dictionaries, one for each DB.
                # Each outcome: {"database": str, "results": list, "count": int, "error": str|None, "duration": float}
                
                db_outcomes = []
                aggregated_results = []
                search_errors_dict = {} # Collect errors by db_name
                search_summary_dict = {} # Collect summary by db_name

                # Default per-database timeout
                # For advanced search, it's 25s. For simple/person, it was 30s implicitly.
                # The refactored search_database takes db_timeout.
                per_db_timeout = 25 if search_mode == 'advanced' else 30

                if search_mode == 'advanced':
                    logger.info(f"Preparing for advanced search (parallel). Main search term: '{main_search_term}'. Databases: {selected_databases}")
                    
                    # Extract common advanced search parameters from the form
                    adv_main_query_term = request.form.get('search_query', '').strip()
                    # search_field for the main query term (assuming new HTML field name 'search_field_advanced')
                    adv_field_for_main_query = request.form.get('search_field_advanced', 'All Fields') 
                    
                    adv_additional_terms = request.form.get('additional_terms', '').strip()
                    # General author, title, journal filters (assuming new HTML field names)
                    adv_author_filter_form = request.form.get('author_advanced', '').strip() 
                    adv_title_filter_form = request.form.get('title_advanced', '').strip()
                    adv_journal_filter_form = request.form.get('journal_advanced', '').strip()

                    # Date range, language, pub_type from Step 3 of advanced search form
                    adv_year_from = request.form.get('start_date', '').strip() # HTML uses 'start_date'
                    adv_year_to = request.form.get('end_date', '').strip()     # HTML uses 'end_date'
                    adv_language_form = request.form.get('language', '').strip() # HTML uses 'language'
                    adv_pub_type_form = request.form.get('publication_type', '').strip() # HTML uses 'publication_type'

                    # Database-specific filters from Step 4 of advanced search form
                    adv_pubmed_full_text_only = request.form.get('full_text_only') == 'on'
                    adv_pubmed_free_access_only = request.form.get('free_access_only') == 'on'
                    adv_dnb_online_only = request.form.get('online_only') == 'on'
                    adv_dnb_academic_only = request.form.get('academic_only') == 'on'
                    
                    # Consolidate author information from selected persons and general author field
                    final_author_filter = adv_author_filter_form
                    adv_selected_person_ids_str = request.form.get('advanced_selected_person_ids', '')
                    if adv_selected_person_ids_str:
                        try:
                            person_ids = [int(pid) for pid in adv_selected_person_ids_str.split(',') if pid.isdigit()]
                            if person_ids:
                                persons_selected = Person.query.filter(Person.id.in_(person_ids)).all()
                                if persons_selected:
                                    # Create a combined author string for the connectors.
                                    # This is a simplified approach. Connectors might need to parse "OR" or expect lists.
                                    # Example for PubMed: "Doe J OR Smith A"
                                    # Example for DNB: 'dc.creator all "Doe J" OR dc.creator all "Smith A"' (handled by connector)
                                    person_author_strings = []
                                    for p in persons_selected:
                                        # Basic name format, connectors can refine this with specific field tags if needed
                                        name_str = f"{p.last_name} {p.first_name[0] if p.first_name else ''}".strip()
                                        if name_str:
                                            person_author_strings.append(name_str)
                                    
                                    if person_author_strings:
                                        selected_persons_as_authors = " OR ".join(f'"{name}"' for name in person_author_strings)
                                        if final_author_filter: # If general author field also has input
                                            final_author_filter = f"({final_author_filter}) OR ({selected_persons_as_authors})"
                                        else:
                                            final_author_filter = selected_persons_as_authors
                        except Exception as e:
                            logger.error(f"Error processing advanced_selected_person_ids: {e}", exc_info=True)
                            # Don't let this break the search; proceed with any typed author_filter

                    # Prepare filter_kwargs to be passed to each thread task
                    filter_kwargs_for_advanced = {
                        "additional_terms": adv_additional_terms,
                        "date_range": parse_date_range(adv_year_from, adv_year_to),
                        "language": adv_language_form if adv_language_form else None,
                        "pub_type": adv_pub_type_form if adv_pub_type_form else None,
                        "field": adv_field_for_main_query, # Pass the field for the main query
                        "author_filter": final_author_filter if final_author_filter else None,
                        "title_filter": adv_title_filter_form if adv_title_filter_form else None,
                        "journal_filter": adv_journal_filter_form if adv_journal_filter_form else None,
                        # Database-specific flags (connectors need to be updated to accept these in **kwargs)
                        "pubmed_full_text_only": adv_pubmed_full_text_only,
                        "pubmed_free_access_only": adv_pubmed_free_access_only,
                        "dnb_online_only": adv_dnb_online_only,
                        "dnb_academic_only": adv_dnb_academic_only,
                    }

                    # Use ThreadPoolExecutor to run searches in parallel
                    # The number of workers can be adjusted. Max workers = number of DBs or a fixed pool size.
                    # Using up to len(selected_databases) workers, but ThreadPoolExecutor default is often reasonable (e.g., min(32, os.cpu_count() + 4))
                    max_workers = min(len(selected_databases), current_app.config.get('MAX_SEARCH_WORKERS', 5)) # Configurable max workers
                    
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        future_to_db = {
                            executor.submit(
                                search_database, # Target function
                                query=adv_main_query_term,
                                databases=[db_name], # search_database expects a list
                                search_mode=search_mode,
                                db_timeout=per_db_timeout,
                                **filter_kwargs_for_advanced # Pass all collected advanced filters
                            ): db_name for db_name in selected_databases
                        }
                        
                        for future in as_completed(future_to_db):
                            db_name_completed = future_to_db[future]
                            try:
                                # search_database returns a list of outcomes; for a single DB, it's a list with one item.
                                outcome_list = future.result() 
                                if outcome_list:
                                    db_outcomes.append(outcome_list[0])
                                else: # Should ideally not happen if search_database is robust
                                    logger.error(f"Parallel search for {db_name_completed} returned empty or invalid outcome list.")
                                    db_outcomes.append({
                                        "database": db_name_completed, "results": [], "count": 0,
                                        "error": f"Search task for {db_name_completed} failed to produce a valid outcome.", 
                                        "duration": 0.0
                                    })
                            except Exception as exc:
                                logger.error(f"Parallel search for {db_name_completed} generated an exception: {exc}", exc_info=True)
                                db_outcomes.append({
                                    "database": db_name_completed, "results": [], "count": 0,
                                    "error": f"Exception during search for {db_name_completed}: {str(exc)}", 
                                    "duration": 0.0 # Duration might be unknown or partial
                                })
                else: # Simple or Person search - executed sequentially as before, or could also be parallelized if needed.
                      # For now, keeping simple/person search sequential as per original structure unless specified.
                    # `query` is already set (simple_query_content or from _construct_person_search_query)
                    # `term_for_storage` is also set.
                    # We might have additional common filters for simple/person search from the UI
                    # (e.g. date range). These should be extracted from request.form.
                    
                    simple_person_additional_terms = request.form.get('simple_person_additional_terms', '') # Example name
                    simple_person_date_from = request.form.get('simple_person_date_from', '')
                    simple_person_date_to = request.form.get('simple_person_date_to', '')
                    simple_person_language = request.form.get('simple_person_language', '')
                    simple_person_pub_type = request.form.get('simple_person_pub_type', '')
                    simple_person_field = request.form.get('simple_person_field', 'All Fields')


                    logger.info(f"Calling search_database (mode: {search_mode}) with query='{query}', databases={selected_databases}")
                    db_outcomes = search_database(
                        query=query, # This is simple_query_content or _construct_person_search_query output
                        databases=selected_databases,
                        search_mode=search_mode,
                        person_name=request.form.get('person_name_for_association', '') if search_mode == 'person' else '', # For result association
                        db_timeout=per_db_timeout,
                        # Pass relevant kwargs from form for simple/person searches
                        additional_terms=simple_person_additional_terms,
                        date_range=parse_date_range(simple_person_date_from, simple_person_date_to),
                        language=simple_person_language if simple_person_language else None,
                        pub_type=simple_person_pub_type if simple_person_pub_type else None,
                        field=simple_person_field
                    )

                # Process all outcomes (common for all search modes)
                for outcome in db_outcomes:
                    db_name = outcome["database"]
                    aggregated_results.extend(outcome["results"]) # Collect all results
                    if outcome["error"]:
                        search_errors_dict[db_name] = outcome["error"]
                    search_summary_dict[db_name] = {
                        "count": outcome["count"],
                        "duration": outcome["duration"],
                        "error": outcome["error"]
                    }
                
                search_summary_dict['total_results'] = sum(item.get("count", 0) for item in search_summary_dict.values() if isinstance(item, dict))
                search_summary_dict['databases_with_errors'] = len(search_errors_dict)

                logger.info(f"Aggregated results count: {len(aggregated_results)}")
                logger.info(f"Aggregated search errors: {search_errors_dict}")
                logger.info(f"Aggregated search summary: {search_summary_dict}")
                
                # Process and save search results
                # _process_search_results expects: results (list), search_errors (dict), search_summary (dict)
                saved_count, query_obj = _process_search_results(
                    aggregated_results, 
                    search_errors_dict, 
                    search_summary_dict, 
                    term_for_storage, 
                    selected_databases, 
                    search_mode
                )

                query_obj_id = query_obj.id if query_obj else None # query_obj can be None if _process_search_results fails
                logger.info(f"Processing complete. saved_count: {saved_count}, query_obj.id: {query_obj_id}")

                # Update search status based on results
                if saved_count > 0:
                    session['search_status'] = 'completed'
                    session['current_query_id'] = query_obj_id # Ensure this is set for redirect
                    flash(f'{saved_count} Ergebnisse gefunden.', 'success')
                    logger.info(f"Redirecting to results page. query_id: {query_obj_id}")
                    return redirect(url_for('search.results'))
                else:
                    session['search_status'] = 'no_results'
                    if query_obj_id: # If query was saved but no results
                         session['current_query_id'] = query_obj_id
                    flash('Keine Ergebnisse gefunden.', 'info')
                    logger.info(f"Redirecting to search index (no results). query_id: {query_obj_id}")
                    return redirect(url_for('search.index'))
                    
            except Exception as e:
                logger.error("Error during search execution: %s", str(e), exc_info=True)
                session['search_status'] = 'error'
                # Use a more generic error key for session unless specific internal needed
                session['search_errors_summary'] = str(e) # search_error_internal was used before
                flash('Ein Fehler ist während des Suchvorgangs aufgetreten. Möglicherweise sind nicht alle Datenbanken durchsucht worden oder Ergebnisse unvollständig. Bitte versuchen Sie es später erneut oder überprüfen Sie Ihre Suchanfrage.', 'error')
                logger.info(f"Redirecting to search index due to error. Session status: {session.get('search_status')}")
                return redirect(url_for('search.index'))
            finally:
                session.modified = True # Ensure session changes are saved
                
        except Exception as e: # Outer try-except for general errors like CSRF issues
            logger.error(f"Unexpected error in search POST route: {str(e)}", exc_info=True)
            session['search_status'] = 'error'
            session['search_errors_summary'] = f"Unerwarteter Systemfehler: {str(e)}"
            flash('Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es erneut.', 'error')
            return redirect(url_for('search.index'))
    
    # GET request - show search form
    # Clear previous search status from session to avoid showing old messages on new GET
    # _clear_search_session_data() # Or selectively clear, e.g. session.pop('search_status', None)
    return render_template('search.html',
                         databases=current_app.config.get('SUPPORTED_DATABASES', ['PubMed', 'Deutsche Nationalbibliothek']),
                         search_status=session.get('search_status', 'idle'))

# Removed _construct_advanced_query_string as its logic for building database-specific
# queries is now handled by the individual connector's `construct_query` method.
# The main `index` route now directly extracts raw parameters from the form for advanced search
# and passes them to the `search_database` function.

@search_bp.before_request
def log_request_info():
    """Log request information and ensure session validity."""
    logger.debug(f"Request to {request.path}, Session ID: {session.sid if session else 'No session'}")
    if session: # Make session permanent for its lifetime
        session.permanent = True
    
    # Check for and clean up very old search results from the database (e.g., older than 7 days)
    # This is a good place for periodic cleanup, but should not run on every request
    # Consider a separate scheduled task or running it less frequently
    if not hasattr(current_app, 'last_cleanup_time') or \
       (get_utc_now() - current_app.last_cleanup_time > timedelta(hours=24)):
        try:
            clean_expired_results() # Defined in this file
            current_app.last_cleanup_time = get_utc_now()
            logger.info("Periodic cleanup of old search results performed.")
        except Exception as e:
            logger.error(f"Error during periodic cleanup: {str(e)}")

    # Check session timestamp for current_query_id expiry
    query_timestamp_str = session.get('query_timestamp') # This was used for session result expiry
    if query_timestamp_str:
        try:
            query_time = datetime.fromisoformat(query_timestamp_str)
            # If query_id is older than, say, 1 hour, clear it to avoid showing stale results
            if get_utc_now() - query_time > timedelta(hours=1): 
                session.pop('current_query_id', None)
                session.pop('query_timestamp', None) # Also remove its timestamp
                # search_summary and search_errors related to this query_id should also be cleared
                session.pop('search_summary', None)
                session.pop('search_errors', None)
                session.modified = True
                logger.info("Cleared expired current_query_id and related data from session.")
        except ValueError: # Invalid isoformat string
            logger.warning(f"Invalid query_timestamp in session: {query_timestamp_str}. Clearing.")
            session.pop('current_query_id', None)
            session.pop('query_timestamp', None)
            session.modified = True
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"Error checking current_query_id expiry in session: {e}")
            # Defensively clear potentially problematic session data
            session.pop('current_query_id', None)
            session.pop('query_timestamp', None)
            session.modified = True


def _construct_person_search_query(form_data):
    """
    Helper function to construct a search query string for 'person' search mode.
    This typically combines names of selected persons and any additional keywords.
    The exact query syntax might need to be adjusted based on how connectors'
    `construct_query` methods expect person information (e.g., as part of the main query string
    or through specific parameters).
    """
    selected_person_ids_str = form_data.get('selected_person_ids', '')
    additional_keywords = form_data.get('person_search_keywords', '').strip()
    
    if not selected_person_ids_str:
        # This case should ideally be caught by form validation before calling this.
        logger.warning("No person IDs selected for person search mode.")
        flash('Bitte wählen Sie mindestens eine Person für die personenbezogene Suche aus.', 'warning')
        return None # Or raise ValueError

    try:
        selected_person_ids = [int(pid) for pid in selected_person_ids_str.split(',') if pid.isdigit()]
        if not selected_person_ids:
            logger.warning("No valid person IDs found after parsing.")
            flash('Ungültige Personenauswahl.', 'warning')
            return None

        persons = Person.query.filter(Person.id.in_(selected_person_ids)).all()
        if not persons:
            logger.warning(f"No persons found in database for IDs: {selected_person_ids_str}")
            flash('Ausgewählte Personen nicht gefunden.', 'warning')
            return None

        # Construct a query string part for person names.
        # This is a simple OR combination. Connectors might need more specific formatting.
        # Example: "(John Doe) OR (Jane Smith)"
        person_name_parts = []
        for p in persons:
            # Ensure names are quoted if they contain spaces, for many search engines
            full_name = f"{p.first_name} {p.last_name}".strip()
            if full_name:
                 # Basic quoting, might need refinement based on target search engine syntax
                person_name_parts.append(f'"{full_name}"') # Example: "\"John Doe\""

        if not person_name_parts:
            logger.warning("Selected persons have no names to search for.")
            return None # Or handle as an error

        # Combine person names with OR
        person_query_segment = " OR ".join(person_name_parts)
        
        # If there are additional keywords, combine with AND
        if additional_keywords:
            # Ensure keywords are also appropriately formatted/quoted if needed
            # Example: ("(John Doe) OR (Jane Smith)") AND (additional keywords)
            # Using parentheses for clarity and correct precedence
            return f"({person_query_segment}) AND ({additional_keywords})"
        
        return person_query_segment # Just the person names query
        
    except ValueError as ve: # e.g. int(pid) fails
        logger.error(f"Invalid person ID format in selected_person_ids: {selected_person_ids_str}. Error: {ve}", exc_info=True)
        flash('Ungültiges Format für Personenauswahl.', 'error')
        return None
    except Exception as e: # Catch-all for other unexpected errors (e.g., DB query fails)
        logger.error(f"Error constructing person search query: {str(e)}", exc_info=True)
        flash('Fehler bei der Erstellung der Personensuchanfrage.', 'error')
        return None

def _clear_search_session_data():
    """Helper function to clear search-related session data before a new search."""
    keys_to_clear = [
        'search_status', 
        'search_start_time', 
        'search_errors',      # Errors per DB from previous search
        'search_summary',     # Summary per DB from previous search
        'current_query_id',   # ID of the last SearchQuery object
        'search_errors_summary', # General error message for the whole search
        'search_error_internal' # Old key, ensure it's cleared
    ]
    
    cleared_keys_count = 0
    for key in keys_to_clear:
        if session.pop(key, None) is not None:
            cleared_keys_count +=1
            
    if cleared_keys_count > 0:
        session.modified = True
        logger.debug(f"Cleared {cleared_keys_count} search-related keys from session.")

def _process_search_results(aggregated_results, search_errors_dict, search_summary_dict, 
                            query_text_for_storage, selected_databases_list, search_mode_used):
    """
    Processes aggregated search results, saves them, and updates session.
    Args:
        aggregated_results (list): Combined list of all search results from all databases.
        search_errors_dict (dict): Dictionary of errors by database name.
        search_summary_dict (dict): Dictionary of summaries by database name.
        query_text_for_storage (str): The main search term or constructed query string to be stored.
        selected_databases_list (list): List of database names that were searched.
        search_mode_used (str): The search mode ('simple', 'person', 'advanced').
    Returns:
        tuple: (saved_count, query_obj) 
               - saved_count (int): Number of results saved.
               - query_obj (SearchQuery|None): The created SearchQuery object, or None if creation failed.
    """
    try:
        # Create a single SearchQuery record for this entire search operation
        search_query_record = SearchQuery(
            search_text=query_text_for_storage, # The overall query
            database=','.join(selected_databases_list), # Store all searched DBs
            search_mode=search_mode_used,
            timestamp=get_utc_now()
            # query_details = json.dumps(search_summary_dict) # Optionally store full summary
        )
        db.session.add(search_query_record)
        db.session.commit() # Commit to get an ID for search_query_record
        logger.info(f"Created SearchQuery record with ID: {search_query_record.id} for search text: '{query_text_for_storage}'")
        
        # Save individual results to SearchResult, linking them to the SearchQuery record
        # The `save_search_results` function already handles batching and validation.
        saved_count = save_search_results(search_query_record, aggregated_results)
        logger.info(f"Saved {saved_count} individual results for SearchQuery ID: {search_query_record.id}")
        
        # Update session with information about this search operation
        session['current_query_id'] = search_query_record.id
        session['query_timestamp'] = search_query_record.timestamp.isoformat() # For session result expiry
        
        # Store summary and errors (these are dicts with per-DB info)
        session['search_summary'] = search_summary_dict 
        session['search_errors'] = [{'database': db, 'error': err} for db, err in search_errors_dict.items() if err]
        
        if search_errors_dict:
            logger.warning(f"Search completed with errors in some databases: {search_errors_dict}")
        
        session.modified = True # Ensure session is saved
        return saved_count, search_query_record
        
    except Exception as e:
        logger.error(f"Error processing and saving search results: {str(e)}", exc_info=True)
        # Avoid setting search_status here, let the main route handler do it
        # session['search_status'] = 'error' # This was done here before
        session['search_errors_summary'] = f"Fehler bei Ergebnisverarbeitung: {str(e)}"
        session.modified = True
        # Return 0 saved and None for query_obj to indicate failure at this stage
        return 0, None 


@search_bp.route("/results")
def results():
    """Display paginated search results for a given query ID stored in session."""
    query_id = session.get('current_query_id')
    
    if not query_id:
        logger.info("Results page: No current_query_id in session.")
        flash("Keine aktiven Suchergebnisse gefunden. Bitte starten Sie eine neue Suche.", "warning")
        return redirect(url_for("search.index"))

    try:
        search_query_obj = SearchQuery.query.get(query_id)
        if not search_query_obj:
            logger.warning(f"Results page: SearchQuery object not found for ID {query_id}.")
            flash("Die gesuchten Ergebnisse oder die Suchanfrage wurden nicht gefunden.", "warning")
            session.pop('current_query_id', None) # Clear invalid query_id
            session.modified = True
            return redirect(url_for("search.index"))
        
        page = request.args.get('page', 1, type=int)
        # Use a configurable PER_PAGE, e.g., from app config
        per_page = current_app.config.get('RESULTS_PER_PAGE', 20) 

        # Get paginated results from the database using the helper
        results_pagination = get_search_results(query_id, page, per_page)

        if results_pagination is None: # Should mean an error occurred in get_search_results
            logger.error(f"Results page: get_search_results returned None for query_id {query_id}.")
            flash("Fehler beim Laden der Ergebnisse.", "error")
            return redirect(url_for("search.index"))

        # The .items attribute of the pagination object contains SearchResult records for the current page.
        # We need to parse their .result_data (JSON string) into dictionaries for the template.
        results_on_page = []
        for search_result_item in results_pagination.items:
            if search_result_item.result_data:
                try:
                    # Ensure result_data is a string before parsing, though it should be from DB
                    if isinstance(search_result_item.result_data, str):
                        parsed_data = json.loads(search_result_item.result_data)
                        # Add the SearchResult ID itself if needed in template, e.g., for linking
                        parsed_data['_search_result_id'] = search_result_item.id 
                        results_on_page.append(parsed_data)
                    else: # Should not happen if data is stored correctly
                        logger.warning(f"Non-string result_data found for SearchResult item {search_result_item.id}, query {query_id}. Type: {type(search_result_item.result_data)}")
                        results_on_page.append({"Title": "Fehlerhafte Daten", "_search_result_id": search_result_item.id})
                except json.JSONDecodeError:
                    logger.error(f"Error decoding JSON for SearchResult item {search_result_item.id} in query {query_id}. Data: {search_result_item.result_data[:100]}...")
                    # Add a placeholder or skip if data is corrupted
                    results_on_page.append({"Title": "Fehler beim Laden dieses Eintrags", "_search_result_id": search_result_item.id})
            else: # result_data is None or empty
                 results_on_page.append({"Title": "Keine Daten für diesen Eintrag", "_search_result_id": search_result_item.id})


        # Get search summary and errors from session (these are dicts with per-DB info)
        search_summary_from_session = session.get('search_summary', {})
        search_errors_from_session = session.get('search_errors', []) # This is a list of dicts
        
        return render_template(
            "results.html",
            results_page=results_pagination,  # The pagination object for page navigation
            results=results_on_page,          # List of result dicts for display
            query=search_query_obj,           # The SearchQuery object
            search_errors=search_errors_from_session, # Errors per DB
            search_summary=search_summary_from_session  # Summary per DB
            # total_results is available via results_pagination.total
        )
        
    except Exception as e:
        logger.error(f"Error displaying results for query_id {query_id}: {str(e)}", exc_info=True)
        flash("Ein unerwarteter Fehler ist beim Anzeigen der Ergebnisse aufgetreten.", "error")
        return redirect(url_for("search.index"))
