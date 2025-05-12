#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Web-based scientific publication search tool
Version 3.0

This Flask application provides a web interface for searching scientific publications
in various databases, including PubMed and the Deutsche Nationalbibliothek (DNB).
It includes advanced search, analysis, and export functionality.
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
import pandas as pd
from io import BytesIO

# Import custom modules
from backend.config import load_settings, save_settings
from backend.connectors import get_connector_for_database
from backend.search import search_database, parse_date_range
from backend.utils import generate_filename, export_to_csv, export_to_excel, log_message, get_log_messages, clear_log_messages
from backend.models import db, SearchQuery, SearchResult, Person, Setting, LogEntry

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("medicalspy.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MedicalSpy")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Configure database
database_url = os.environ.get('DATABASE_URL')
logger.info("Establishing database connection...")
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Prüft die Verbindung vor Verwendung
    'pool_recycle': 280,    # Verbindung nach 280 Sekunden erneuern
    'pool_timeout': 30,     # Timeout für Pool-Verbindungen
    'max_overflow': 5,      # Erlaubt 5 zusätzliche Verbindungen außerhalb des Pools
}
db.init_app(app)

# Create database tables if they don't exist
try:
    with app.app_context():
        db.create_all()
        logger.info("Database tables created (if they didn't exist already)")
except Exception as e:
    logger.error(f"Fehler beim Erstellen der Datenbanktabellen: {str(e)}")
    logger.error("Die Anwendung wird dennoch fortgesetzt, aber Datenbankoperationen könnten fehlschlagen.")

# Initialize session variables if not present
@app.before_request
def before_request():
    if 'search_results' not in session:
        session['search_results'] = []
    if 'saved_queries' not in session:
        # Load saved queries from database
        try:
            with app.app_context():
                queries = db.session.query(SearchQuery).all()
                session['saved_queries'] = [query.to_dict() for query in queries]
        except Exception as e:
            logger.error(f"Fehler beim Laden der gespeicherten Suchanfragen: {str(e)}")
            session['saved_queries'] = []
    if 'settings' not in session:
        # Load settings from database
        try:
            with app.app_context():
                session['settings'] = Setting.get_settings_dict()
        except Exception as e:
            logger.error(f"Fehler beim Laden der Einstellungen: {str(e)}")
            session['settings'] = {
                'output_path': './output',
                'person_list_path': './person_lists',
                'unique_filenames': True,
                'output_columns': [],
                'default_database': 'PubMed'
            }
    if 'persons' not in session:
        # Load persons from database
        try:
            with app.app_context():
                persons = Person.query.all()
                session['persons'] = [person.to_dict() for person in persons]
        except Exception as e:
            logger.error(f"Fehler beim Laden der Personen: {str(e)}")
            session['persons'] = []

# Add context processor to provide current year to all templates
@app.context_processor
def inject_current_year():
    """Add current year to all templates"""
    return {'current_year': datetime.now().year}

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """
    Health check endpoint for monitoring and container orchestration.
    Returns a 200 OK response if the application is running correctly.
    """
    health = {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0",
        "database": "unknown"
    }
    
    # Check database connection
    try:
        # Try a simple database query
        from sqlalchemy import text
        with app.app_context():
            db.session.execute(text("SELECT 1")).scalar()
            health["database"] = "connected"
    except Exception as e:
        health["status"] = "degraded"
        health["database"] = "error"
        health["error"] = str(e)
    
    # Return different status codes based on health status
    status_code = 200 if health["status"] == "ok" else 503
    
    return jsonify(health), status_code

@app.route('/persons')
def persons():
    """Render the persons management page"""
    with app.app_context():
        persons_list = db.session.query(Person).all()
        persons = [person.to_dict() for person in persons_list]
    return render_template('persons.html', persons=persons)

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Render the search page or perform a search"""
    databases = ["PubMed", "Deutsche Nationalbibliothek"]
    
    # Initialize variables with safe defaults
    persons = []
    saved_queries = []
    
    # Fetch persons for autocomplete with error handling
    try:
        persons_list = db.session.query(Person).all()
        persons = [person.to_dict() for person in persons_list]
    except Exception as e:
        app.logger.error(f"Error fetching persons for search page: {str(e)}")
        # Try to retrieve from session as fallback
        persons = session.get('persons', [])
        
    # Fetch saved queries with error handling
    try:
        saved_queries_list = db.session.query(SearchQuery).order_by(SearchQuery.created_at.desc()).limit(20).all()
        saved_queries = [query.to_dict() for query in saved_queries_list]
        session['saved_queries'] = saved_queries  # Update session
    except Exception as e:
        app.logger.error(f"Error fetching saved queries for search page: {str(e)}")
        # Try to retrieve from session as fallback
        saved_queries = session.get('saved_queries', [])
    
    if request.method == 'POST':
        # Get the search mode
        search_mode = request.form.get('search_mode', 'simple')
        
        # Common parameters
        # Unterstützt sowohl alte als auch neue Form der Datenbankauswahl
        selected_databases = request.form.getlist('databases[]')
        if not selected_databases:
            # Fallback für die alte Methode mit einem einzelnen "database" Feld
            selected_database = request.form.get('database', 'PubMed')
            selected_databases = [selected_database]
        
        start_date = request.form.get('start_date', '')
        end_date = request.form.get('end_date', '')
        date_range = parse_date_range(start_date, end_date)
        additional_terms = request.form.get('additional_terms', '')
        
        # Additional parameters for advanced search
        language = request.form.get('language', '')
        publication_type = request.form.get('publication_type', '')
        
        # Handle different search modes
        if search_mode == 'simple':
            # Simple search mode
            search_query = request.form.get('search_query', '')
            person_name = ''
            
            databases_str = ", ".join(selected_databases)
            log_message(f"Starting simple search for '{search_query}' in {databases_str}")
            
            # Validate search query
            if not search_query:
                flash("Bitte geben Sie einen Suchbegriff ein.", "warning")
                log_message("Simple search attempted with empty query")
                return redirect(url_for('search'))
                
            # Perform the search
            return perform_multi_database_search(search_query, selected_databases, person_name, additional_terms, date_range, start_date, end_date)
            
        elif search_mode == 'database':
            # Database search mode
            search_query = request.form.get('search_query', '')
            person_name = request.form.get('person_name', '')
            
            databases_str = ", ".join(selected_databases)
            log_message(f"Starting database search for '{search_query}' in {databases_str} with person: {person_name}")
            
            # Validate search query
            if not search_query:
                flash("Bitte geben Sie einen Suchbegriff ein.", "warning")
                log_message("Database search attempted with empty query")
                return redirect(url_for('search'))
                
            # Perform the search
            return perform_multi_database_search(search_query, selected_databases, person_name, additional_terms, date_range, start_date, end_date)
            
        elif search_mode == 'person':
            # Person search mode
            selected_person_ids = request.form.get('selected_person_ids', '')
            
            databases_str = ", ".join(selected_databases)
            log_message(f"Starting person search for persons with IDs: {selected_person_ids} in {databases_str}")
            
            # Validate person selection
            if not selected_person_ids:
                flash("Bitte wählen Sie mindestens eine Person für die Suche aus.", "warning")
                log_message("Person search attempted with no persons selected")
                return redirect(url_for('search'))
                
            # Get the persons from the database
            persons_list = []
            
            try:
                # Handle single ID case
                if isinstance(selected_person_ids, (int, str)):
                    person_ids = [int(selected_person_ids)]
                else:
                    # Try to parse as JSON first (for updated client code)
                    try:
                        person_ids = json.loads(selected_person_ids)
                    except json.JSONDecodeError:
                        # Fallback to comma-separated (for backward compatibility)
                        person_ids = selected_person_ids.split(',')
                
                for person_id in person_ids:
                    person = db.session.query(Person).get(int(person_id))
                    if person:
                        persons_list.append(person)
            except Exception as e:
                flash(f"Fehler beim Abrufen der Personen: {str(e)}", "danger")
                log_message(f"Error retrieving persons: {str(e)}", level="ERROR")
                return redirect(url_for('search'))
                
            if not persons_list:
                flash("Keine gültigen Personen mit den angegebenen IDs gefunden.", "warning")
                log_message("Personensuche mit ungültigen Personen-IDs versucht")
                return redirect(url_for('search'))
                
            # Perform search for each person and combine results
            all_results = []
            for person in persons_list:
                person_query = f"{person.first_name} {person.last_name}"
                log_message(f"Searching for person: {person.name} ({person_query})")
                
                # Suche für diese Person in allen ausgewählten Datenbanken
                for db_name in selected_databases:
                    try:
                        log_message(f"Searching {db_name} for person: {person.name} ({person_query})")
                        
                        # Get connector for the current database
                        connector = get_connector_for_database(db_name, api_key=session['settings'].get('pubmed_api_key', ''))
                        
                        # Execute search
                        results = search_database(
                            connector, 
                            person_query, 
                            person_name=person.name,
                            additional_terms=additional_terms,
                            date_range=date_range
                        )
                        
                        # Add database name to each result
                        for result in results:
                            result['Database'] = db_name
                        
                        if results:
                            log_message(f"Found {len(results)} results for {person.name} in {db_name}")
                            all_results.extend(results)
                        else:
                            log_message(f"No results found for {person.name} in {db_name}")
                        
                    except Exception as e:
                        log_message(f"Error searching for {person.name} in {db_name}: {str(e)}", level="ERROR")
                        # Continue with other databases and persons
                    
            # Save combined results
            if all_results:
                # Remove duplicate results (if any)
                # using a simple approach - checking by title equality
                unique_results = []
                titles_seen = set()
                
                for result in all_results:
                    title = result.get('Titel', '')
                    if title and title not in titles_seen:
                        titles_seen.add(title)
                        unique_results.append(result)
                
                # Speichere nur die Query-ID in der Session, nicht die kompletten Ergebnisse
                
                # Save to database
                try:
                    # Create a search query for the person search
                    person_names = [p.name for p in persons_list]
                    person_names_str = ", ".join(person_names)
                    
                    # Store databases as comma-separated string
                    databases_str = ", ".join(selected_databases)
                    
                    search_query_obj = SearchQuery()
                    search_query_obj.name = f"Person search in {databases_str}: {person_names_str[:50]}{'...' if len(person_names_str) > 50 else ''}"
                    search_query_obj.query = ""  # No direct query for person search
                    search_query_obj.database = databases_str
                    search_query_obj.additional_terms = additional_terms
                    search_query_obj.start_date = start_date
                    search_query_obj.end_date = end_date
                    search_query_obj.person_name = person_names_str
                    search_query_obj.search_mode = 'person'
                    db.session.add(search_query_obj)
                    db.session.flush()  # Get ID without committing
                    
                    # Speichere die Query-ID in der Session für späteren Zugriff auf die Ergebnisse
                    session['current_query_id'] = search_query_obj.id
                    session['results_count'] = len(unique_results)
                    session.modified = True
                    
                    # Save each result
                    for result in unique_results:
                        # Extract database from result if available, or use the first selected database
                        result_database = result.get('Database', selected_databases[0])
                        
                        result_obj = SearchResult()
                        result_obj.query_id = search_query_obj.id
                        result_obj.database = result_database
                        result_obj.result_data = result
                        db.session.add(result_obj)
                    
                    db.session.commit()
                    log_message(f"Person search results saved to database. Query ID: {search_query_obj.id}")
                    
                except Exception as e:
                    db.session.rollback()
                    log_message(f"Failed to save person search results to database: {str(e)}", level="ERROR")
                
                log_message(f"Person search complete. Found {len(unique_results)} unique results across {len(persons_list)} persons.")
                flash(f"{len(unique_results)} Ergebnisse für {len(persons_list)} Personen gefunden.", "success")
                return redirect(url_for('results'))
            else:
                flash("Keine Ergebnisse für die ausgewählten Personen gefunden.", "warning")
                log_message("Personensuche hat keine Ergebnisse zurückgegeben")
        elif search_mode == 'advanced':
            # Advanced database search mode
            search_query = request.form.get('search_query', '')
            advanced_selected_person_ids = request.form.get('advanced_selected_person_ids', '')
            
            databases_str = ", ".join(selected_databases)
            log_message(f"Starting advanced database search for '{search_query}' in {databases_str}")
            
            # Apply database-specific filters
            original_additional_terms = additional_terms
            
            # In multi-database mode, we need to manage filters per database
            # but we'll only apply database-specific filters if there's just one database selected
            if len(selected_databases) == 1:
                selected_database = selected_databases[0]
                if selected_database == 'PubMed':
                    # Add PubMed-specific filters
                    full_text_only = request.form.get('full_text_only') == 'on'
                    free_access_only = request.form.get('free_access_only') == 'on'
                    
                    if full_text_only:
                        additional_terms += " AND full text[sb]"
                    if free_access_only:
                        additional_terms += " AND free full text[sb]"
                        
                elif selected_database == 'Deutsche Nationalbibliothek':
                    # Add DNB-specific filters
                    online_only = request.form.get('online_only') == 'on'
                    academic_only = request.form.get('academic_only') == 'on'
                    
                    if online_only:
                        additional_terms += " AND elektronische Ressource"
                    if academic_only:
                        additional_terms += " AND Hochschulschrift"
                
                # Add language and publication type filters if specified
                if language:
                    if selected_database == 'PubMed':
                        additional_terms += f" AND {language}[lang]"
                    else:
                        additional_terms += f" AND sprache={language}"
                        
                if publication_type:
                    if selected_database == 'PubMed':
                        additional_terms += f" AND {publication_type}[pt]"
                    else:
                        additional_terms += f" AND {publication_type}"
            else:
                # Wenn mehrere Datenbanken ausgewählt sind, können wir keine datenbankspezifischen Filter anwenden
                log_message("Multiple databases selected, database-specific filters won't be applied")
            
            # Check if we have persons selected
            persons_list = []
            try:
                if advanced_selected_person_ids:
                    person_ids = json.loads(advanced_selected_person_ids)
                    
                    for person_id in person_ids:
                        person = db.session.query(Person).get(int(person_id))
                        if person:
                            persons_list.append(person)
                    
                    log_message(f"Advanced search includes {len(persons_list)} persons")
            except Exception as e:
                log_message(f"Error retrieving persons for advanced search: {str(e)}", level="ERROR")
                flash(f"Fehler beim Abrufen der Personen: {str(e)}", "danger")
                return redirect(url_for('search'))
            
            # If we have a query or persons selected
            if search_query or persons_list:
                # If we only have a direct query with no persons
                if search_query and not persons_list:
                    log_message(f"Performing advanced search with direct query only")
                    return perform_multi_database_search(search_query, selected_databases, "", additional_terms, date_range, start_date, end_date)
                
                # If we have persons (with or without a direct query)
                if persons_list:
                    # Perform search for each person and combine results
                    all_results = []
                    
                    for person in persons_list:
                        person_query = f"{person.first_name} {person.last_name}"
                        if search_query:
                            # If we have a direct query, combine it with the person
                            combined_query = f"({search_query}) AND ({person_query})"
                            log_message(f"Searching for: {combined_query}")
                        else:
                            # Otherwise just search for the person
                            combined_query = person_query
                            log_message(f"Searching for person: {person.name} ({person_query})")
                        
                        # Search in all selected databases for this person
                        for db_name in selected_databases:
                            try:
                                log_message(f"Searching {db_name} for combined query: {combined_query}")
                                
                                # Get connector for the current database
                                connector = get_connector_for_database(db_name, api_key=session['settings'].get('pubmed_api_key', ''))
                                
                                # Execute search
                                results = search_database(
                                    connector, 
                                    combined_query, 
                                    person_name=person.name,
                                    additional_terms=additional_terms,
                                    date_range=date_range
                                )
                                
                                # Add database name to each result
                                for result in results:
                                    result['Database'] = db_name
                                
                                if results:
                                    all_results.extend(results)
                                    log_message(f"Found {len(results)} results for query with {person.name} in {db_name}")
                                else:
                                    log_message(f"No results found for query with {person.name} in {db_name}")
                            except Exception as e:
                                log_message(f"Error searching for {person.name} in {db_name}: {str(e)}", level="ERROR")
                    
                    # Remove duplicates (based on identifier)
                    seen_identifiers = set()
                    unique_results = []
                    for result in all_results:
                        identifier = result.get('Identifier', '')
                        if identifier and identifier not in seen_identifiers:
                            seen_identifiers.add(identifier)
                            unique_results.append(result)
                            
                    # Store results in session and database
                    if unique_results:
                        # Save to database
                        try:
                            # First save the search query to reference results
                            person_names = ", ".join([p.name for p in persons_list])
                            databases_str = ", ".join(selected_databases)
                            search_name = f"Erweiterte Suche: {search_query or person_names} in {databases_str}"
                            search_query_obj = SearchQuery()
                            search_query_obj.name = search_name
                            search_query_obj.query = search_query
                            search_query_obj.database = databases_str  # Store multiple databases
                            search_query_obj.additional_terms = original_additional_terms  # Save original before filters
                            search_query_obj.start_date = start_date
                            search_query_obj.end_date = end_date
                            search_query_obj.person_name = person_names
                            search_query_obj.search_mode = 'advanced'
                            db.session.add(search_query_obj)
                            db.session.flush()  # Get ID without committing
                            
                            # Speichere nur die Query-ID in der Session, nicht die kompletten Ergebnisse
                            session['current_query_id'] = search_query_obj.id
                            session['results_count'] = len(unique_results)
                            session.modified = True
                            
                            # Now save each result
                            for result in unique_results:
                                # Extract database from result if available, or use the first selected database
                                result_database = result.get('Database', selected_databases[0])
                                
                                result_obj = SearchResult()
                                result_obj.query_id = search_query_obj.id
                                result_obj.database = result_database
                                result_obj.result_data = result
                                db.session.add(result_obj)
                            
                            db.session.commit()
                            log_message(f"Advanced search results saved to database. Query ID: {search_query_obj.id}")
                            
                        except Exception as e:
                            db.session.rollback()
                            log_message(f"Failed to save advanced search results to database: {str(e)}", level="ERROR")
                            # Continue since we at least have the results in the session
                        
                        log_message(f"Advanced search complete. Found {len(unique_results)} unique results.")
                        flash(f"{len(unique_results)} Ergebnisse gefunden.", "success")
                        return redirect(url_for('results'))
                    else:
                        flash("Keine Ergebnisse für die erweiterte Suche gefunden.", "warning")
                        log_message("Advanced search returned no results")
                        return redirect(url_for('search'))
            else:
                flash("Bitte geben Sie einen Suchbegriff ein oder wählen Sie mindestens eine Person aus.", "warning")
                log_message("Advanced search attempted with no query and no persons")
                return redirect(url_for('search'))
        else:
            # Invalid search mode
            flash("Ungültiger Suchmodus ausgewählt.", "danger")
            log_message(f"Invalid search mode: {search_mode}", level="ERROR")
    
    # Get persons list from database for dropdowns and person search
    try:
        persons_list = db.session.query(Person).all()
        persons = [person.to_dict() for person in persons_list]
        session['persons'] = persons  # Update session with latest from database
    except Exception as e:
        log_message(f"Error retrieving persons from database: {str(e)}", level="ERROR")
        persons = session.get('persons', [])
    
    # At this point we've already fetched saved queries at the beginning of the function
    # But add a safety check before rendering the template
    if saved_queries is None:
        saved_queries = []
    if persons is None:
        persons = []
    
    # Return the search page template with our safely fetched data
    return render_template(
        'search.html', 
        databases=databases, 
        persons=persons,
        saved_queries=saved_queries
    )

def perform_single_search(search_query, selected_database, person_name, additional_terms, date_range, start_date, end_date):
    """
    Abwärtskompatible Funktion für Aufrufe des alten Codes.
    Leitet einfach an die neue multi-datenbank Funktion weiter.
    """
    return perform_multi_database_search(search_query, [selected_database], person_name, additional_terms, date_range, start_date, end_date)

def perform_multi_database_search(search_query, selected_databases, person_name, additional_terms, date_range, start_date, end_date):
    """Helper function to perform a search across multiple databases"""
    try:
        if not selected_databases:
            flash("Bitte wählen Sie mindestens eine Datenbank aus.", "warning")
            log_message("Search attempted with no databases selected")
            return redirect(url_for('search'))
            
        all_results = []
        search_summary = {}
        total_results = 0
        
        # Iterate through each selected database
        for selected_database in selected_databases:
            try:
                log_message(f"Searching {selected_database} for: '{search_query}'")
                
                # Get appropriate connector for this database
                api_key = session.get('settings', {}).get('pubmed_api_key', '')
                connector = get_connector_for_database(selected_database, api_key=api_key)
                
                # Fehler abfangen, wenn kein Connector für diese Datenbank existiert
                if connector is None:
                    log_message(f"Kein Connector für Datenbank '{selected_database}' gefunden", level="ERROR")
                    search_summary[selected_database] = 0
                    flash(f"Fehler: Die Datenbank '{selected_database}' wird nicht unterstützt.", "danger")
                    continue
                
                # Execute search
                db_results = search_database(
                    connector, 
                    search_query, 
                    person_name=person_name,
                    additional_terms=additional_terms,
                    date_range=date_range
                )
                
                # Track results count for this database
                if db_results:
                    num_results = len(db_results)
                    search_summary[selected_database] = num_results
                    total_results += num_results
                    all_results.extend(db_results)
                    log_message(f"Found {num_results} results in {selected_database}")
                else:
                    search_summary[selected_database] = 0
                    log_message(f"No results found in {selected_database}")
                
            except Exception as e:
                search_summary[selected_database] = 0
                error_msg = str(e)
                log_message(f"Error searching {selected_database}: {error_msg}", level="ERROR")
                flash(f"Fehler bei der Suche in {selected_database}: {error_msg}", "danger")
                search_summary[selected_database] = f"Error: {str(e)}"
                # Continue with other databases
        
        # Store combined results in session and database
        if all_results:
            # Remove duplicate results based on title and identifier
            unique_results = []
            identifiers_seen = set()
            titles_seen = set()
            
            for result in all_results:
                identifier = result.get('Identifier', '')
                title = result.get('Titel', '')
                
                # Use identifier if available, otherwise use title
                if identifier and identifier not in identifiers_seen:
                    identifiers_seen.add(identifier)
                    unique_results.append(result)
                elif title and title not in titles_seen and not identifier:
                    titles_seen.add(title)
                    unique_results.append(result)
            
            # Save to database
            try:
                # Store databases as comma-separated string
                databases_str = ", ".join(selected_databases)
                
                # First save the search query
                search_query_obj = SearchQuery()
                search_query_obj.name = f"Search in {databases_str}: {search_query[:30]}{'...' if len(search_query) > 30 else ''}"
                search_query_obj.query = search_query
                search_query_obj.database = databases_str  # Store multiple databases
                search_query_obj.additional_terms = additional_terms
                search_query_obj.start_date = start_date
                search_query_obj.end_date = end_date
                search_query_obj.person_name = person_name
                search_query_obj.search_mode = 'multi'  # Marker for multi-database search
                db.session.add(search_query_obj)
                db.session.flush()  # Get ID without committing
                
                # Now save each result
                for result in unique_results:
                    # Extract database from result if available, otherwise use the first one
                    result_database = result.get('Database', selected_databases[0])
                    
                    result_obj = SearchResult()
                    result_obj.query_id = search_query_obj.id
                    result_obj.database = result_database
                    result_obj.result_data = result
                    db.session.add(result_obj)
                
                db.session.commit()
                
                # Speichere nur die Query-ID in der Session, nicht die kompletten Ergebnisse
                session['current_query_id'] = search_query_obj.id
                session['results_count'] = len(unique_results)
                session.modified = True
                
                log_message(f"Search results saved to database. Query ID: {search_query_obj.id}")
            except Exception as e:
                db.session.rollback()
                log_message(f"Failed to save search results to database: {str(e)}", level="ERROR")
                # Continue since we at least have results to display
            
            # Format search summary for display
            summary_text = ", ".join([f"{db}: {count}" for db, count in search_summary.items() if isinstance(count, int)])
            unique_count = len(unique_results)
            
            log_message(f"Multi-database search complete. Found {unique_count} unique results across {len(selected_databases)} databases.")
            
            if unique_count < total_results:
                flash(f"{unique_count} einzigartige Ergebnisse gefunden (insgesamt {total_results} Treffer - {summary_text}).", "success")
            else:
                flash(f"{unique_count} Ergebnisse gefunden ({summary_text}).", "success")
                
            return redirect(url_for('results'))
        else:
            flash("Keine Ergebnisse für Ihre Suchanfrage gefunden.", "warning")
            log_message("Multi-database search returned no results")
            return redirect(url_for('search'))
            
    except Exception as e:
        flash(f"Fehler während der Suche: {str(e)}", "danger")
        log_message(f"Search error: {str(e)}", level="ERROR")
        return redirect(url_for('search'))

@app.route('/results')
def results():
    """Display search results"""
    # Lade Ergebnisse aus der Datenbank anhand der in der Session gespeicherten Query-ID
    if 'current_query_id' in session:
        query_id = session.get('current_query_id')
        try:
            # Lade alle Ergebnisse für diese Query aus der Datenbank
            results_from_db = db.session.query(SearchResult).filter_by(query_id=query_id).all()
            
            # Extrahiere die tatsächlichen Ergebnisdaten
            results = [result.result_data for result in results_from_db]
            
            # WICHTIG: Wir speichern die Ergebnisse NICHT mehr in der Session, 
            # sondern laden sie bei Bedarf aus der DB
            # Das vermeidet die Session-Cookie-Größenbeschränkung
            
            log_message(f"Loaded {len(results)} results from database for query ID: {query_id}")
            return render_template('results.html', results=results, query_id=query_id)
        except Exception as e:
            log_message(f"Error loading results from database: {str(e)}", level="ERROR")
            flash(f"Fehler beim Laden der Ergebnisse aus der Datenbank: {str(e)}", "danger")
            return redirect(url_for('search'))
    else:
        # Wenn keine aktuelle Query ID vorhanden ist
        flash("Keine Suchergebnisse gefunden. Bitte führen Sie eine neue Suche durch.", "warning")
        return redirect(url_for('search'))

@app.route('/analysis')
def analysis():
    """Display analysis of search results"""
    # Direkt aus der Datenbank laden, um Session-Größe zu reduzieren
    if 'current_query_id' in session:
        query_id = session.get('current_query_id')
        try:
            # Lade alle Ergebnisse für diese Query aus der Datenbank
            results_from_db = db.session.query(SearchResult).filter_by(query_id=query_id).all()
            
            # Extrahiere die tatsächlichen Ergebnisdaten
            results = [result.result_data for result in results_from_db]
            log_message(f"Loaded {len(results)} results from database for analysis (query ID: {query_id})")
        except Exception as e:
            log_message(f"Error loading results from database for analysis: {str(e)}", level="ERROR")
            flash(f"Fehler beim Laden der Ergebnisse aus der Datenbank: {str(e)}", "danger")
            return redirect(url_for('search'))
    else:
        # Wenn keine aktuelle Query ID vorhanden ist
        flash("Keine Suchergebnisse für die Analyse gefunden. Bitte führen Sie eine neue Suche durch.", "warning")
        return redirect(url_for('search'))
    
    # Prepare data for analysis if results exist
    analysis_data = {}
    if results:
        # Count publications by year
        if 'Veröffentlichungsjahr' in results[0]:
            years = [result.get('Veröffentlichungsjahr', 'Unknown') for result in results]
            year_counts = {}
            for year in years:
                if year in year_counts:
                    year_counts[year] += 1
                else:
                    year_counts[year] = 1
            analysis_data['year_counts'] = year_counts
        
        # Count publications by author
        if 'Autoren' in results[0]:
            all_authors = []
            for result in results:
                authors = result.get('Autoren', '').split(', ')
                all_authors.extend(authors)
            
            author_counts = {}
            for author in all_authors:
                if author in author_counts:
                    author_counts[author] += 1
                else:
                    author_counts[author] = 1
            
            # Get top 10 authors
            top_authors = dict(sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10])
            analysis_data['top_authors'] = top_authors
    
    return render_template('analysis.html', results=results, analysis_data=analysis_data)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Manage application settings"""
    if request.method == 'POST':
        # Update settings
        updated_settings = {
            'output_path': request.form.get('output_path', './output'),
            'person_list_path': request.form.get('person_list_path', './person_lists'),
            'pubmed_api_key': request.form.get('pubmed_api_key', ''),
            'unique_filenames': request.form.get('unique_filenames') == 'on',
            'output_columns': request.form.getlist('output_columns'),
            'default_database': request.form.get('default_database', 'PubMed')
        }
        
        # Save settings to session and database
        session['settings'] = updated_settings
        
        try:
            # Save to database
            Setting.save_settings_dict(updated_settings)
            
            flash("Einstellungen erfolgreich aktualisiert!", "success")
            log_message("Einstellungen in Session und Datenbank aktualisiert")
        except Exception as e:
            db.session.rollback()
            flash(f"Einstellungen wurden in der Session gespeichert, konnten aber nicht in der Datenbank gespeichert werden: {str(e)}", "warning")
            log_message(f"Fehler beim Speichern der Einstellungen in der Datenbank: {str(e)}", level="ERROR")
        
    return render_template('settings.html', settings=session.get('settings', {}))

@app.route('/log')
def log():
    """Display application log"""
    logs = get_log_messages()
    return render_template('log.html', logs=logs)

@app.route('/api/clear_log', methods=['POST'])
def api_clear_log():
    """API endpoint to clear the log"""
    clear_log_messages()
    # Also clear logs in database
    with app.app_context():
        LogEntry.clear_logs()
    return jsonify({"success": True})

@app.route('/api/export_log', methods=['POST'])
def api_export_log():
    """API endpoint to export the log"""
    logs = get_log_messages()
    logs_text = "\n".join(logs)
    
    # Create in-memory text file
    output = BytesIO()
    output.write(logs_text.encode('utf-8'))
    output.seek(0)
    
    return send_file(
        output,
        mimetype="text/plain",
        as_attachment=True,
        download_name=f"medicalspy_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )

@app.route('/api/export_results', methods=['POST'])
def api_export_results():
    """API endpoint to export search results"""
    format_type = request.form.get('format', 'csv')
    
    results = []
    # Lade Ergebnisse aus der Datenbank anhand der in der Session gespeicherten Query-ID
    if 'current_query_id' in session:
        query_id = session.get('current_query_id')
        try:
            # Lade alle Ergebnisse für diese Query aus der Datenbank
            results_from_db = db.session.query(SearchResult).filter_by(query_id=query_id).all()
            
            # Extrahiere die tatsächlichen Ergebnisdaten
            results = [result.result_data for result in results_from_db]
            log_message(f"Loaded {len(results)} results from database for export (query ID: {query_id})")
        except Exception as e:
            log_message(f"Error loading results from database for export: {str(e)}", level="ERROR")
            return jsonify({"success": False, "message": f"Fehler beim Laden der Ergebnisse: {str(e)}"}), 500
    else:
        # Wenn keine aktuelle Query ID vorhanden ist
        return jsonify({"success": False, "message": "Keine Suchergebnisse zum Exportieren gefunden."}), 400
    
    if not results:
        return jsonify({"success": False, "message": "Keine Ergebnisse zum Exportieren gefunden."}), 400
    
    # Select columns to export based on settings
    output_columns = session['settings'].get('output_columns', [])
    if not output_columns:
        output_columns = list(results[0].keys())
    
    # Filter results to only include selected columns
    filtered_results = []
    for result in results:
        filtered_result = {}
        for col in output_columns:
            if col in result:
                filtered_result[col] = result[col]
        filtered_results.append(filtered_result)
    
    # Create filename
    filename = generate_filename(
        session['settings'].get('unique_filenames', False),
        extension=format_type
    )
    
    # Create in-memory file for export
    output = BytesIO()
    
    if format_type == 'csv':
        export_to_csv(filtered_results, output)
        mimetype = 'text/csv'
    else:  # Excel format
        export_to_excel(filtered_results, output)
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    output.seek(0)
    
    log_message(f"Exported {len(filtered_results)} results to {filename}")
    
    return send_file(
        output,
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/save_query', methods=['POST'])
def api_save_query():
    """API endpoint to save a search query"""
    data = request.json
    
    # Get search mode
    search_mode = data.get('search_mode', 'simple')
    
    # Validate required fields based on search mode
    if not data or 'query_name' not in data or 'database' not in data:
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    
    # For person search mode, the query field might be empty
    if search_mode != 'person' and ('search_query' not in data or not data['search_query']):
        return jsonify({"success": False, "message": "Search query is required for this search mode"}), 400
    
    # Create new query object
    new_query = {
        'name': data['query_name'],
        'query': data.get('search_query', ''),
        'database': data['database'],
        'additional_terms': data.get('additional_terms', ''),
        'start_date': data.get('start_date', ''),
        'end_date': data.get('end_date', ''),
        'person_name': data.get('person_name', ''),
        'search_mode': search_mode,
        'saved_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Save to database
    try:
        # Create database entry
        db_query = SearchQuery(
            name=new_query['name'],
            query=new_query['query'],
            database=new_query['database'],
            additional_terms=new_query['additional_terms'],
            start_date=new_query['start_date'],
            end_date=new_query['end_date'],
            person_name=new_query['person_name'],
            search_mode=search_mode
        )
        db.session.add(db_query)
        db.session.commit()
        
        # Update the new query with the database ID
        new_query['id'] = db_query.id
        
        # Update the session
        saved_queries = session.get('saved_queries', [])
        saved_queries.append(new_query)
        session['saved_queries'] = saved_queries
        session.modified = True
        
        log_message(f"Saved query: {data['query_name']} (mode: {search_mode})")
        return jsonify({"success": True, "query": new_query})
    except Exception as e:
        db.session.rollback()
        log_message(f"Failed to save query: {str(e)}", level="ERROR")
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route('/api/query/<int:query_id>', methods=['GET'])
def api_get_query(query_id):
    """API endpoint to get a single saved query"""
    try:
        # Find query in database
        query = db.session.query(SearchQuery).get(query_id)
        if query:
            # Convert to dictionary
            query_dict = query.to_dict()
            
            log_message(f"Retrieved query: {query.name}")
            return jsonify({"success": True, "query": query_dict})
        
        return jsonify({"success": False, "message": "Query not found in database"}), 404
    except Exception as e:
        log_message(f"Failed to retrieve query: {str(e)}", level="ERROR")
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route('/api/delete_query/<int:query_id>', methods=['DELETE'])
def api_delete_query(query_id):
    """API endpoint to delete a saved query"""
    try:
        # First delete associated results
        db.session.query(SearchResult).filter_by(query_id=query_id).delete()
        
        # Then find and delete the query
        query = db.session.query(SearchQuery).get(query_id)
        if query:
            query_name = query.name
            db.session.delete(query)
            
            # Commit all changes
            db.session.commit()
            
            # Update session
            saved_queries = session.get('saved_queries', [])
            saved_queries = [q for q in saved_queries if q.get('id') != query_id]
            session['saved_queries'] = saved_queries
            session.modified = True
            
            log_message(f"Deleted query: {query_name}")
            return jsonify({"success": True})
        
        return jsonify({"success": False, "message": "Query not found in database"}), 404
    except Exception as e:
        db.session.rollback()
        log_message(f"Failed to delete query: {str(e)}", level="ERROR")
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route('/api/manage_persons', methods=['POST'])
def api_manage_persons():
    """API endpoint to add, update, or remove a person"""
    action = request.form.get('action', '')
    
    if action == 'add':
        # Add a new person
        name = request.form.get('name', '')
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        
        if not name or not first_name or not last_name:
            return jsonify({"success": False, "message": "Missing required fields"}), 400
        
        try:
            # Create new person in database
            person = Person(
                name=name,
                first_name=first_name,
                last_name=last_name
            )
            db.session.add(person)
            db.session.commit()
            
            # Add to session
            new_person = {
                'id': person.id,
                'name': name,
                'first_name': first_name,
                'last_name': last_name
            }
            
            persons = session.get('persons', [])
            persons.append(new_person)
            session['persons'] = persons
            session.modified = True
            
            log_message(f"Added person: {name}")
            return jsonify({"success": True, "person": new_person})
            
        except Exception as e:
            db.session.rollback()
            log_message(f"Failed to add person: {str(e)}", level="ERROR")
            return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
        
    elif action == 'update':
        # Update an existing person
        person_id = int(request.form.get('id', -1))
        name = request.form.get('name', '')
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        
        if person_id < 0 or not name or not first_name or not last_name:
            return jsonify({"success": False, "message": "Missing required fields"}), 400
        
        try:
            # Update person in database
            person = db.session.query(Person).get(person_id)
            if not person:
                return jsonify({"success": False, "message": "Person not found in database"}), 404
                
            person.name = name
            person.first_name = first_name
            person.last_name = last_name
            db.session.commit()
            
            # Update in session
            updated_person = {
                'id': person.id,
                'name': name,
                'first_name': first_name,
                'last_name': last_name
            }
            
            persons = session.get('persons', [])
            # Replace the person with matching ID
            persons = [p for p in persons if p.get('id') != person_id]
            persons.append(updated_person)
            session['persons'] = persons
            session.modified = True
            
            log_message(f"Updated person: {name}")
            return jsonify({"success": True, "person": updated_person})
            
        except Exception as e:
            db.session.rollback()
            log_message(f"Failed to update person: {str(e)}", level="ERROR")
            return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
        
    elif action == 'delete':
        # Delete a person
        person_id = int(request.form.get('id', -1))
        
        if person_id < 0:
            return jsonify({"success": False, "message": "Missing person ID"}), 400
        
        try:
            # Delete from database
            person = db.session.query(Person).get(person_id)
            if not person:
                return jsonify({"success": False, "message": "Person not found in database"}), 404
                
            person_name = person.name
            db.session.delete(person)
            db.session.commit()
            
            # Update session
            persons = session.get('persons', [])
            # Remove the person with matching ID
            persons = [p for p in persons if p.get('id') != person_id]
            session['persons'] = persons
            session.modified = True
            
            log_message(f"Deleted person: {person_name}")
            return jsonify({"success": True})
            
        except Exception as e:
            db.session.rollback()
            log_message(f"Failed to delete person: {str(e)}", level="ERROR")
            return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    
    return jsonify({"success": False, "message": "Invalid action"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
