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
from backend.search_fix import enhanced_search_database  # Import the enhanced search
from backend.utils import log_message
import logging

logger = logging.getLogger(__name__)

search_bp = Blueprint("search", __name__)

def get_utc_now():
    """Helper function to get current UTC time"""
    return datetime.now(timezone.utc)

def get_search_results(query_id):
    """Get search results from database by query ID"""
    try:
        # Use the relationship on SearchQuery to get results
        query = SearchQuery.query.get(query_id)
        if not query:
            logger.error(f"Query {query_id} not found")
            return []
            
        results = query.results.all()
        return [result.data for result in results if result.result_data]
    except Exception as e:
        logger.error(f"Error retrieving search results for query {query_id}: {e}")
        return []

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
    errors = []
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
    """Handle search form display (GET) and search execution (POST)"""
    if request.method == "POST":
        try:            # Enhanced CSRF validation - skip in testing mode
            if not current_app.config.get('TESTING'):
                try:
                    # Get and validate CSRF token
                    csrf_token = request.form.get('csrf_token')
                    session_token = session.get('csrf_token')
                    cookie_token = request.cookies.get('csrf_token')
                    
                    # Log detailed token information for debugging
                    logger.info(f"CSRF token from form: {csrf_token[:5]}... (length: {len(csrf_token) if csrf_token else 0})")
                    logger.info(f"CSRF token from session: {session_token[:5] if session_token else None}... (length: {len(session_token) if session_token else 0})")
                    logger.info(f"CSRF token from cookie: {cookie_token[:5] if cookie_token else None}... (length: {len(cookie_token) if cookie_token else 0})")
                    logger.info(f"Session keys: {list(session.keys())}")
                    
                    # Check if token exists in form
                    if not csrf_token:
                        logger.error("CSRF token missing from form data")
                        raise ValidationError("Missing CSRF token")
                    
                    # Auto-fix the session if needed by copying from cookie
                    if not session_token and cookie_token:
                        logger.warning("Missing session token but cookie token exists - auto-fixing")
                        session['csrf_token'] = cookie_token
                        session.modified = True
                        session_token = cookie_token
                    
                    # Validate the token
                    try:
                        validate_csrf(csrf_token)
                        logger.info("CSRF token validation successful")
                    except ValidationError as ve:
                        # Try fallback validation with token from cookie
                        if cookie_token and cookie_token != csrf_token:
                            logger.warning("Primary validation failed, trying with cookie token")
                            try:
                                validate_csrf(cookie_token)
                                logger.info("CSRF validation successful with cookie token")
                                # Update form token for future validation
                                csrf_token = cookie_token
                            except ValidationError:
                                # Both validations failed, raise the original error
                                raise ve
                        else:
                            # No fallback available, re-raise
                            raise ve
                    
                except ValidationError as csrf_error:
                    logger.error(f"CSRF validation failed: {str(csrf_error)}")
                    
                    # Generate a new token
                    from flask_wtf.csrf import generate_csrf
                    new_token = generate_csrf()
                    session['csrf_token'] = new_token
                    session.modified = True
                    logger.info(f"Regenerated new CSRF token: {new_token[:5]}...")
                    
                    # Redirect back to the search page with a user-friendly message
                    flash("Sicherheitstoken ungültig oder abgelaufen. Bitte versuchen Sie es erneut.", "warning")
                    return redirect(url_for("search.index"))

            # Clean up old results periodically
            if not hasattr(current_app, 'last_cleanup'):
                current_app.last_cleanup = get_utc_now()
            if get_utc_now() - current_app.last_cleanup > timedelta(hours=24):
                clean_expired_results()
                current_app.last_cleanup = get_utc_now()

            # Get and validate search parameters
            search_mode = request.form.get("search_mode", "simple")
            databases = request.form.getlist("databases")
            
            # Get the correct query input based on the search_mode
            if search_mode == "simple":
                query = request.form.get("simple_query_content", "").strip()
            elif search_mode == "person":
                # For person search, the main "query" might be constructed differently
                # or might not be a single text field.
                # For now, let's assume person_name is the primary identifier
                # and additional_terms can supplement it.
                person_name = request.form.get("person_name", "").strip()
                additional_terms = request.form.get("additional_terms", "").strip()
                if person_name and additional_terms:
                    query = f"{person_name} AND {additional_terms}"
                elif person_name:
                    query = person_name
                else:
                    query = additional_terms # Or handle as an error if person_name is required
                # If selected_person_ids are used, they should be fetched here
                # selected_person_ids = request.form.get("selected_person_ids")
            elif search_mode == "advanced":
                query = request.form.get("search_query", "").strip() # from advanced search main input
                # Potentially combine with other advanced fields
            else: # Default or unknown search mode
                query = request.form.get("query", "").strip() # Fallback, though ideally each mode has specific handling

            # Input validation
            if not query:
                flash("Bitte geben Sie einen Suchbegriff ein.", "warning")
                return redirect(url_for("search.index"))
            
            if not databases:
                flash("Bitte wählen Sie mindestens eine Datenbank aus.", "warning")
                return redirect(url_for("search.index"))            # Execute search with better error handling
            logger.info(f"Starting search: mode={search_mode}, query='{query}', databases={databases}")
            start_time = get_utc_now()
            
            try:
                # Show searching status to the user in the session
                session['search_status'] = 'searching'
                session['search_start_time'] = get_utc_now().isoformat()
                session.modified = True
                  # Use enhanced search function with error handling
                results, search_errors = enhanced_search_database(
                    query=query,
                    databases=databases,
                    search_mode=search_mode,
                    timeout=60  # Set a reasonable timeout
                )
                
                if search_errors:
                    for db_error in search_errors:
                        errors.append({
                            'database': db_error.get('database', 'Unknown'),
                            'error': db_error.get('error', 'Unknown error'),
                            'time': db_error.get('time', 0)
                        })
                
                # Record overall search metrics
                search_time = (get_utc_now() - start_time).total_seconds()
                result_count = len(results)
                logger.info(f"Total search completed in {search_time:.2f}s, found {result_count} results")
                
                # Store errors in session for display on results page
                if errors:
                    session['search_errors'] = errors
                
                # Clear search status
                session.pop('search_status', None)
                session.pop('search_start_time', None)
                
                # Handle case where no results were found
                if not results:
                    if errors:
                        error_dbs = ", ".join([e['database'] for e in errors])
                        flash(f"Fehler bei der Suche in {error_dbs}. Bitte versuchen Sie es später erneut.", "warning")
                    else:
                        flash("Keine Ergebnisse gefunden.", "info")
                    return redirect(url_for("search.index"))
                
            except Exception as search_error:
                search_time = (get_utc_now() - start_time).total_seconds()
                logger.error(f"Search failed in {search_time:.2f}s: {search_error}")
                
                # Clear search status and flash error
                session.pop('search_status', None)
                session.pop('search_start_time', None)
                
                # Provide a user-friendly error message based on exception details
                error_message = str(search_error)
                if "API key" in error_message.lower() or "api_key" in error_message.lower():
                    flash(f"Suchfehler: API-Schlüssel fehlt oder ist ungültig für einen der ausgewählten Dienste.", "error")
                elif "timeout" in error_message.lower():
                    flash(f"Suchfehler: Zeitüberschreitung bei der Verbindung zu einem der Dienste. Bitte versuchen Sie es später erneut.", "error")
                elif "format" in error_message.lower() or "parse" in error_message.lower():
                    flash(f"Suchfehler: Problem beim Verarbeiten der Antwort von einem der Dienste.", "error")
                else:
                    flash(f"Suchfehler: {error_message}", "error")
                
                return redirect(url_for("search.index"))

            # Save search query and results to database
            try:
                # Parse dates if provided
                start_date = request.form.get('start_date')
                end_date = request.form.get('end_date')
                if start_date or end_date:
                    start_date, end_date = parse_date_range(start_date, end_date)

                # Create search query record
                search_query = SearchQuery(
                    name=f"Suche vom {get_utc_now().strftime('%Y-%m-%d %H:%M:%S')}",
                    search_text=query,  # Changed from query=query
                    database=','.join(databases),  # Join list into comma-separated string
                    search_mode=search_mode,
                    additional_terms=request.form.get('additional_terms', '').strip(),
                    start_date=start_date,
                    end_date=end_date,
                    person_name=request.form.get('person_name', '').strip()
                )
                db.session.add(search_query)
                db.session.commit()
                logger.info(f"Saved search query with ID: {search_query.id}")

                # Save results using the new helper function
                saved_count = save_search_results(search_query, results)
                if saved_count < result_count:
                    logger.warning(f"Only {saved_count} of {result_count} results were saved successfully")

                # Store only references in session
                session['current_query_id'] = search_query.id
                session['query_timestamp'] = search_query.timestamp.isoformat()
                session['result_count'] = saved_count
                session.modified = True

                return redirect(url_for("search.results"))

            except Exception as db_error:
                logger.error(f"Database error: {str(db_error)}")
                db.session.rollback()
                flash("Fehler beim Speichern der Suchergebnisse.", "error")
                return redirect(url_for("search.index"))

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            flash(f"Fehler bei der Suche: {str(e)}", "error")
            return redirect(url_for("search.index"))

    # GET request - show search form
    return render_template("search.html", databases=["PubMed", "Deutsche Nationalbibliothek"])

@search_bp.route("/results")
def results():
    """Show search results"""
    query_id = session.get('current_query_id')
    if not query_id:
        flash("Keine aktiven Suchergebnisse gefunden.", "warning")
        return redirect(url_for("search.index"))

    try:        # Get query details
        query = SearchQuery.query.get(query_id)
        if not query:
            flash("Die gesuchten Ergebnisse wurden nicht gefunden.", "warning")
            return redirect(url_for("search.index"))        
        
        # Get results from database
        results = get_search_results(query_id)
        
        # Get search errors if any from the connectors
        search_errors = []
        search_summary = {}
        
        # Attempt to get errors and result counts for each database
        for db_name in query.database.split(','):
            connector = get_connector_for_database(db_name)
            if connector and connector.last_error:
                search_errors.append({
                    'database': db_name,
                    'error': connector.last_error
                })
                
            # Count results per database
            db_results = [r for r in results if r.get('Datenbank') == db_name]
            search_summary[db_name] = len(db_results)
        
        return render_template(
            "results.html",
            results=results,
            query=query,
            search_errors=search_errors,
            search_summary=search_summary
        )

    except Exception as e:
        logger.error(f"Error displaying results: {str(e)}")
        flash("Fehler beim Anzeigen der Ergebnisse.", "error")
        return redirect(url_for("search.index"))

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
