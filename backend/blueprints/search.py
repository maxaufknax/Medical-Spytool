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
                results = []
                search_errors = {}
                search_summary = {}

                if search_mode == 'advanced':
                    all_results_advanced = [] # Renamed to avoid conflict with outer 'results'
                    logger.info(f"Preparing for advanced search. Main search term: '{main_search_term}'. Databases: {selected_databases}")
                    for db_name in selected_databases:
                        advanced_query_str = _construct_advanced_query_string(request.form, db_name)
                        if not advanced_query_str:
                            logger.warning(f"Skipping {db_name} for advanced search as no query was constructed (main term: '{main_search_term}').")
                            search_summary[db_name] = {"count": 0, "error": "No query constructed"}
                            continue

                        logger.info(f"Calling search_single_database for '{db_name}' with query: '{advanced_query_str}', mode: '{search_mode}'")
                        single_db_search_timeout = 25
                        db_search_result = search_single_database(
                            query=advanced_query_str,
                            db_name=db_name,
                            search_mode=search_mode,
                            db_timeout=single_db_search_timeout
                        )
                        logger.info(f"Raw result from search_single_database for '{db_name}': {db_search_result}")
                        
                        all_results_advanced.extend(db_search_result.get("results", []))
                        if db_search_result.get("error"):
                            search_errors[db_name] = db_search_result.get("error")
                        search_summary[db_name] = { # Store more info for summary
                            "count": db_search_result.get("count", 0),
                            "duration": db_search_result.get("duration", 0),
                            "error": db_search_result.get("error")
                        }
                    
                    results = all_results_advanced # Assign to outer results
                    # search_summary already populated with details per DB
                    search_summary['total_results'] = sum(item.get("count", 0) for item in search_summary.values() if isinstance(item, dict))
                    search_summary['databases_with_errors'] = len(search_errors)
                    logger.info(f"Advanced search raw results: {results}")
                    logger.info(f"Advanced search errors: {search_errors}")
                    logger.info(f"Advanced search summary: {search_summary}")

                else: # Simple or Person search
                    logger.info(f"Calling search_database with query='{query}', databases={selected_databases}, mode='{search_mode}'")
                    results, search_errors, search_summary = search_database(
                        query=query,
                        databases=selected_databases,
                        search_mode=search_mode,
                        timeout=30
                    )
                    logger.info(f"Raw results from search_database: {results}")
                    logger.info(f"Search errors from search_database: {search_errors}")
                    logger.info(f"Search summary from search_database: {search_summary}")
                
                # Process and save search results
                saved_count, query_obj = _process_search_results(results, search_errors, search_summary, term_for_storage, selected_databases, search_mode)
                
                query_obj_id = query_obj.id if query_obj else None
                logger.info(f"Processing complete. saved_count: {saved_count}, query_obj.id: {query_obj_id}")

                # Update search status based on results
                if saved_count > 0:
                    session['search_status'] = 'completed'
                    flash(f'{saved_count} Ergebnisse gefunden.', 'success')
                    logger.info(f"Redirecting to results page. saved_count: {saved_count}, query_obj.id: {query_obj_id}")
                    return redirect(url_for('search.results'))
                else:
                    session['search_status'] = 'no_results'
                    flash('Keine Ergebnisse gefunden.', 'info')
                    logger.info(f"Redirecting to search index (no results). saved_count: {saved_count}, query_obj.id: {query_obj_id}")
                    return redirect(url_for('search.index'))
                    
            except Exception as e:
                logger.error("Error during search execution: %s", str(e), exc_info=True)
                session['search_status'] = 'error'
                session['search_error_internal'] = str(e) 
                flash('Ein Fehler ist während des Suchvorgangs aufgetreten. Möglicherweise sind nicht alle Datenbanken durchsucht worden oder Ergebnisse unvollständig. Bitte versuchen Sie es später erneut oder überprüfen Sie Ihre Suchanfrage.', 'error')
                # Log values before redirect in exception case as well
                # query_obj might not be defined here if error happened before _process_search_results
                # saved_count might also not be defined.
                logger.info(f"Redirecting to search index due to error. Session status: {session.get('search_status')}")
                return redirect(url_for('search.index'))
            finally:
                session.modified = True
                
        except Exception as e:
            logger.error(f"Unexpected error in search route: {str(e)}", exc_info=True)
            session['search_status'] = 'error'
            session['search_error'] = str(e)
            flash('Ein unerwarteter Fehler ist aufgetreten.', 'error')
            return redirect(url_for('search.index'))
    
    # GET request - show search form
    return render_template('search.html', 
                         databases=['PubMed', 'Deutsche Nationalbibliothek'],
                         search_status=session.get('search_status', 'idle'))

def _construct_advanced_query_string(form_data, database_name):
    """Helper function to construct advanced search query string."""
    query_parts = []
    
    # Main search query
    main_query = form_data.get('search_query', '').strip()
    if main_query:
        query_parts.append(f"({main_query})")
        
    # Additional terms
    additional_terms = form_data.get('additional_terms', '').strip()
    if additional_terms:
        query_parts.append(f"AND ({additional_terms})")
        
    # Selected persons
    selected_person_ids_str = form_data.get('advanced_selected_person_ids', '')
    if selected_person_ids_str:
        try:
            selected_person_ids = [int(pid) for pid in selected_person_ids_str.split(',') if pid.isdigit()]
            persons = Person.query.filter(Person.id.in_(selected_person_ids)).all()
            if persons:
                person_queries = []
                for p in persons:
                    if database_name == 'PubMed':
                        person_queries.append(f"{p.last_name} {p.first_name[0]}[AU]")
                    elif database_name == 'Deutsche Nationalbibliothek':
                        person_queries.append(f"per={p.first_name} {p.last_name}")
                    else:
                        person_queries.append(f"{p.first_name} {p.last_name}")
                
                if person_queries:
                    query_parts.append(f"AND ({' OR '.join(person_queries)})")
        except Exception as e:
            logger.error(f"Error processing person IDs for advanced search: {str(e)}")
    
    # Author
    author = form_data.get('author', '').strip()
    if author:
        if database_name == 'PubMed':
            query_parts.append(f"AND ({author}[AU])")
        else:
            query_parts.append(f"AND (author:{author})")
    
    # Year range
    year_from = form_data.get('year_from', '').strip()
    year_to = form_data.get('year_to', '').strip()
    if year_from or year_to:
        if database_name == 'PubMed':
            if year_from and year_to:
                query_parts.append(f"AND (\"{year_from}\"[Date - Publication] : \"{year_to}\"[Date - Publication])")
            elif year_from:
                query_parts.append(f"AND (\"{year_from}\"[Date - Publication] : 3000[Date - Publication])")
            elif year_to:
                query_parts.append(f"AND (1800[Date - Publication] : \"{year_to}\"[Date - Publication])")
        else:
            if year_from and year_to:
                query_parts.append(f"AND (year:{year_from}-{year_to})")
            elif year_from:
                query_parts.append(f"AND (year:>={year_from})")
            elif year_to:
                query_parts.append(f"AND (year:<={year_to})")
    
    # Title keywords
    title = form_data.get('title', '').strip()
    if title:
        if database_name == 'PubMed':
            query_parts.append(f"AND ({title}[TI])")
        else:
            query_parts.append(f"AND (title:{title})")
    
    # Join all parts
    if not query_parts:
        return ""
    
    # Remove the first "AND" if the query starts with it
    query_string = " ".join(query_parts)
    if query_string.startswith("AND "):
        query_string = query_string[4:]
    
    return query_string

@search_bp.before_request
def log_request_info():
    """Log request information and ensure session validity"""
    logger.debug(f"Request path: {request.path}")
    session.permanent = True  # Ensure session stays alive during search
    
    # Check session expiry
    timestamp = session.get('query_timestamp')
    if timestamp:
        try:
            search_time = datetime.fromisoformat(timestamp)
            if get_utc_now() - search_time > timedelta(hours=1):
                # Clear expired search results from session
                session.pop('current_query_id', None)
                session.pop('query_timestamp', None)
                session.pop('result_count', None)
                session.modified = True
                logger.info("Cleared expired search results from session")
        except Exception as e:
            logger.error(f"Error checking session expiry: {e}")
            # Clear invalid session data
            session.pop('query_timestamp', None)

def _construct_person_search_query(form_data):
    """Helper function to construct person search query"""
    selected_person_ids_str = form_data.get('selected_person_ids', '')
    additional_keywords = form_data.get('person_search_keywords', '').strip()
    
    if not selected_person_ids_str:
        flash('Bitte wählen Sie mindestens eine Person für die personenbezogene Suche aus.', 'warning')
        return None

    try:
        selected_person_ids = [int(pid) for pid in selected_person_ids_str.split(',') if pid.isdigit()]
        persons = Person.query.filter(Person.id.in_(selected_person_ids)).all()
        
        if not persons:
            flash('Ausgewählte Personen nicht gefunden.', 'warning')
            return None

        # Construct query string
        person_names = [f"{p.first_name} {p.last_name}" for p in persons]
        query_parts = [f"({name})" for name in person_names]
        
        if additional_keywords:
            return f"({' OR '.join(query_parts)}) AND ({additional_keywords})"
        return ' OR '.join(query_parts)
        
    except Exception as e:
        logger.error(f"Error constructing person search query: {str(e)}", exc_info=True)
        return None

def _clear_search_session_data():
    """Helper function to clear search-related session data"""
    keys_to_clear = [
        'search_status',
        'search_start_time',
        'search_error',
        'search_summary',
        'search_errors',
        'current_query_id'
    ]
    
    for key in keys_to_clear:
        session.pop(key, None)
    session.modified = True

def _process_search_results(results, search_errors, search_summary, query, selected_databases, search_mode):
    """
    Process search results and update session status accordingly
    
    Args:
        results (list): List of search results
        search_errors (dict): Dictionary of errors by database
        search_summary (dict): Summary of search results by database
        query (str): The search query
        selected_databases (list): List of selected databases
        search_mode (str): The search mode used
        
    Returns:
        tuple: (saved_count, query_obj) containing the number of saved results and the query object
    """
    try:
        # Create search query record
        search_query = SearchQuery(
            search_text=query,
            database=','.join(selected_databases),
            search_mode=search_mode,
            timestamp=get_utc_now()
        )
        db.session.add(search_query)
        db.session.commit()
        logger.info(f"Created search query record with ID: {search_query.id}")
        
        # Save results
        saved_count = save_search_results(search_query, results)
        logger.info(f"Saved {saved_count} results for query ID: {search_query.id}")
        
        # Update session with search information
        session['current_query_id'] = search_query.id
        session['search_summary'] = search_summary
        
        if search_errors:
            session['search_errors'] = [{'database': db, 'error': err} for db, err in search_errors.items()]
            logger.warning(f"Search completed with errors: {search_errors}")
        
        # Update search status based on results
        if saved_count > 0:
            session['search_status'] = 'completed'
            logger.info(f"Search completed successfully with {saved_count} results")
        else:
            session['search_status'] = 'no_results'
            logger.info("Search completed with no results")
        
        session.modified = True
        return saved_count, search_query
        
    except Exception as e:
        logger.error(f"Error processing search results: {str(e)}", exc_info=True)
        session['search_status'] = 'error'
        session['search_error'] = str(e)
        session.modified = True
        raise

@search_bp.route("/results")
def results():
    """Show search results"""
    query_id = session.get('current_query_id')
    if not query_id:
        flash("Keine aktiven Suchergebnisse gefunden.", "warning")
        return redirect(url_for("search.index"))

    try:
        # Get query details and results
        query = SearchQuery.query.get(query_id)
        if not query:
            flash("Die gesuchten Ergebnisse wurden nicht gefunden.", "warning")
            return redirect(url_for("search.index"))
        
        # Get page number from request, default to 1
        page = request.args.get('page', 1, type=int)
        per_page = 20  # Or get from config, e.g., current_app.config.get('PER_PAGE', 20)

        # Get paginated results from database
        results_pagination = get_search_results(query_id, page, per_page)

        if results_pagination is None:
            flash("Fehler beim Laden der Ergebnisse.", "error")
            return redirect(url_for("search.index"))

        # Extract items for the current page to be displayed
        # The .items attribute of the pagination object contains the records for the current page.
        # These items already have .result_data, but we need to parse the JSON for the template.
        results_on_page = []
        for item in results_pagination.items:
            if item.result_data:
                try:
                    results_on_page.append(json.loads(item.result_data))
                except json.JSONDecodeError:
                    logger.error(f"Error decoding JSON for result item {item.id} in query {query_id}")
                    results_on_page.append({}) # Add empty dict or skip

        # Get search summary and errors from session
        search_summary = session.get('search_summary', {}) # This is overall summary
        search_errors = session.get('search_errors', [])
        
        # Render results template
        return render_template(
            "results.html",
            results_page=results_pagination, # Pass the pagination object
            results=results_on_page, # Pass the actual items for the current page
            query=query,
            search_errors=search_errors,
            search_summary=search_summary,
            # total_results is now part of results_pagination.total
        )
        
    except Exception as e:
        logger.error(f"Error displaying results: {str(e)}", exc_info=True)
        flash("Fehler beim Anzeigen der Ergebnisse.", "error")
        return redirect(url_for("search.index"))
