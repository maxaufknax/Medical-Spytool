"""
Integrated Publication Search Tool

This application provides a unified interface for searching multiple academic databases
including PubMed and the German National Library (DNB). It supports person management,
advanced search options, result visualization, and export functionality.

Usage:
    flask run
    or
    gunicorn -b 0.0.0.0:5000 main:app
"""

import os
import logging
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, flash, session
from flask_bootstrap import Bootstrap
from utils.search_profiles import (
    save_search_profile, load_search_profile, delete_search_profile, 
    get_all_search_profiles
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("medicalspytool.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")
Bootstrap(app)

# Import database connectors
from database_connectors import DATABASE_CONNECTORS
from utils.config_manager import load_settings, save_settings, ensure_directories
from utils.logging_manager import log_message
from utils.export_manager import export_to_excel, export_to_csv, get_unique_filename

# Load configuration
app_config = load_settings()
ensure_directories(app_config)

# Global variables
search_results = []
GLOBAL_LOG = []

@app.route('/')
def index():
    """Render the main page."""
    from datetime import datetime
    return render_template('index.html', config=app_config, now=datetime.now())

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Handle search requests."""
    global search_results, GLOBAL_LOG
    from datetime import datetime
    
    # Geladenes Profil aus Session abrufen, falls vorhanden
    loaded_profile = session.get('loaded_profile', None)
    loaded_profile_name = session.get('loaded_profile_name', None)
    
    # Wenn wir in einem POST sind und ein Profil geladen hatten, dieses aus der Session entfernen
    if request.method == 'POST' and loaded_profile:
        session.pop('loaded_profile', None)
        session.pop('loaded_profile_name', None)
    
    if request.method == 'POST':
        # Get form data
        database = request.form.get('database', 'PubMed')
        search_term = request.form.get('search_term', '')
        additional_terms = request.form.get('additional_terms', '')
        person_name = request.form.get('person_name', 'General Search')
        max_results = int(request.form.get('max_results', 100))
        
        # Optional parameters
        search_field = request.form.get('search_field', 'Alle Felder')
        language = request.form.get('language', '')
        pub_type = request.form.get('pub_type', '')
        use_date_filter = request.form.get('use_date_filter') == 'on'
        
        date_range = None
        if use_date_filter:
            start_date = request.form.get('start_date', '')
            end_date = request.form.get('end_date', '')
            if start_date and end_date:
                date_range = {
                    'start': datetime.strptime(start_date, '%Y-%m-%d'),
                    'end': datetime.strptime(end_date, '%Y-%m-%d')
                }
        
        # Prepare search parameters
        search_params = {
            'name': person_name,
            'max_results': max_results,
            'field': search_field if search_field != 'Alle Felder' else None
        }
        
        if language:
            search_params['language'] = language
        
        if pub_type:
            search_params['pub_type'] = pub_type
            
        if date_range:
            search_params['date_range'] = date_range
        
        # Get API key
        api_key = app_config.get(f"{database.lower()}_api_key", "")
        
        # Search based on selected database
        results = []
        log_message(None, f"Starting search in {database}")
        
        try:
            if database == 'Combined':
                # Search in all databases
                for db_name, connector_class in DATABASE_CONNECTORS.items():
                    db_api_key = app_config.get(f"{db_name.lower()}_api_key", "")
                    connector = connector_class(api_key=db_api_key, settings=app_config)
                    
                    # Construct query
                    query = connector.construct_query(
                        search_term, 
                        additional_terms=additional_terms,
                        date_range=date_range,
                        language=language,
                        pub_type=pub_type,
                        field=search_field
                    )
                    
                    db_results = connector.search(query, params=search_params)
                    results.extend(db_results)
                    log_message(None, f"Found {len(db_results)} results in {db_name}")
            else:
                # Search in specific database
                connector_class = DATABASE_CONNECTORS.get(database)
                if connector_class:
                    connector = connector_class(api_key=api_key, settings=app_config)
                    
                    # Construct query
                    query = connector.construct_query(
                        search_term, 
                        additional_terms=additional_terms,
                        date_range=date_range,
                        language=language,
                        pub_type=pub_type,
                        field=search_field
                    )
                    
                    results = connector.search(query, params=search_params)
                    log_message(None, f"Found {len(results)} results in {database}")
            
            # Update global results
            search_results = results
            
            return render_template('results.html', 
                                   results=results, 
                                   count=len(results),
                                   search_term=search_term,
                                   database=database,
                                   config=app_config,
                                   now=datetime.now())
            
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            log_message(None, f"Error during search: {str(e)}")
            return render_template('search.html', 
                                   error=str(e), 
                                   database=database,
                                   config=app_config,
                                   now=datetime.now())
    
    # GET request, show search form
    profile_data = None
    profile_name = None
    
    # Verwende das aus der Session geladene Profil, falls vorhanden
    if loaded_profile:
        profile_data = loaded_profile
        profile_name = loaded_profile_name
        flash(f'Suchprofil "{profile_name}" geladen. Sie können jetzt die Suche starten.', 'success')
    
    return render_template('search.html', 
                          config=app_config, 
                          now=datetime.now(),
                          profile=profile_data,
                          profile_name=profile_name)

@app.route('/results')
def results():
    """Display search results."""
    global search_results
    from datetime import datetime
    return render_template('results.html', 
                          results=search_results, 
                          count=len(search_results),
                          config=app_config,
                          now=datetime.now())

@app.route('/analysis')
def analysis():
    """Show data analysis and visualization."""
    global search_results
    from datetime import datetime
    return render_template('analysis.html', 
                          results=search_results,
                          count=len(search_results),
                          config=app_config,
                          now=datetime.now())

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Handle settings page."""
    global app_config
    from datetime import datetime
    
    if request.method == 'POST':
        # Update settings from form
        app_config['output_path'] = request.form.get('output_path', './output')
        app_config['person_list_path'] = request.form.get('person_list_path', './person_lists')
        app_config['unique_filenames'] = request.form.get('unique_filenames') == 'on'
        app_config['pubmed_api_key'] = request.form.get('pubmed_api_key', '')
        app_config['dnb_api_key'] = request.form.get('dnb_api_key', '')
        app_config['default_database'] = request.form.get('default_database', 'PubMed')
        
        # Get selected columns
        all_columns = [
            "Database", "Name", "Title", "Publication Year", "Publication Month",
            "Authors", "Publication Types", "Affiliations", "Publisher", "Subjects",
            "Language", "PubMed URL", "DOI URL", "PubMed ID", "PMCID", "DOI", 
            "ISBN", "Identifier", "URL", "Citation Count"
        ]
        
        output_columns = []
        for column in all_columns:
            if request.form.get(f"column_{column.replace(' ', '_')}") == 'on':
                output_columns.append(column)
        
        if not output_columns:
            # Default columns if none selected
            output_columns = ["Database", "Name", "Title", "Publication Year", "Authors", 
                             "Identifier", "URL", "Citation Count"]
        
        app_config['output_columns'] = output_columns
        
        # Save settings
        save_settings(app_config)
        ensure_directories(app_config)
        
        return redirect(url_for('settings', saved=True))
    
    return render_template('settings.html', config=app_config, saved=request.args.get('saved'), now=datetime.now())

@app.route('/export', methods=['GET'])
def export_page():
    """Show export page."""
    global search_results, app_config
    from datetime import datetime
    
    return render_template('export.html', 
                          results=search_results,
                          count=len(search_results) if search_results else 0,
                          config=app_config,
                          now=datetime.now())

@app.route('/export/<format>')
def export(format):
    """Export results to file."""
    global search_results, app_config
    
    if not search_results:
        flash('Keine Ergebnisse zum Exportieren vorhanden. Bitte führen Sie zuerst eine Suche durch.', 'warning')
        return redirect(url_for('export_page'))
    
    # Create output directory if it doesn't exist
    os.makedirs(app_config.get('output_path', './output'), exist_ok=True)
    
    # Get file path
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = f"search_results_{timestamp}"
    file_path = os.path.join(app_config.get('output_path', './output'), base_name)
    
    try:
        if format == 'excel':
            file_path = f"{file_path}.xlsx"
            export_to_excel(search_results, file_path)
            return send_file(file_path, as_attachment=True)
            
        elif format == 'csv':
            file_path = f"{file_path}.csv"
            export_to_csv(search_results, file_path)
            return send_file(file_path, as_attachment=True)
            
        else:
            flash('Ungültiges Exportformat. Bitte wählen Sie Excel oder CSV.', 'danger')
            return redirect(url_for('export_page'))
            
    except Exception as e:
        logger.error(f"Export error: {e}", exc_info=True)
        flash(f'Fehler beim Export: {str(e)}', 'danger')
        return redirect(url_for('export_page'))

@app.route('/persons', methods=['GET', 'POST'])
def persons():
    """Handle person management."""
    from datetime import datetime
    persons_file = os.path.join(app_config.get('person_list_path', './person_lists'), 'persons.json')
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(persons_file), exist_ok=True)
    
    # Initialize persons list
    person_list = []
    
    # Load existing persons if file exists
    if os.path.exists(persons_file):
        try:
            with open(persons_file, 'r', encoding='utf-8') as f:
                person_list = json.load(f)
        except Exception as e:
            logger.error(f"Error loading persons: {e}", exc_info=True)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            # Add a new person
            name = request.form.get('name', '').strip()
            search_term = request.form.get('search_term', '').strip()
            additional_terms = request.form.get('additional_terms', '').strip()
            
            if name and search_term:
                person = {
                    'Name': name,
                    'Search Term': search_term,
                    'Additional Terms': additional_terms
                }
                
                # Check for duplicates
                if not any(p.get('Name') == name for p in person_list):
                    person_list.append(person)
                    
                    # Save updated list
                    try:
                        with open(persons_file, 'w', encoding='utf-8') as f:
                            json.dump(person_list, f, indent=2)
                    except Exception as e:
                        logger.error(f"Error saving persons: {e}", exc_info=True)
                        return render_template('persons.html', 
                                              persons=person_list, 
                                              error=f"Error saving: {str(e)}",
                                              config=app_config,
                                              now=datetime.now())
        
        elif action == 'delete':
            # Delete a person
            index = int(request.form.get('index', -1))
            if 0 <= index < len(person_list):
                del person_list[index]
                
                # Save updated list
                try:
                    with open(persons_file, 'w', encoding='utf-8') as f:
                        json.dump(person_list, f, indent=2)
                except Exception as e:
                    logger.error(f"Error saving persons: {e}", exc_info=True)
                    return render_template('persons.html', 
                                          persons=person_list, 
                                          error=f"Error saving: {str(e)}",
                                          config=app_config,
                                          now=datetime.now())
    
    return render_template('persons.html', persons=person_list, config=app_config, now=datetime.now())

@app.route('/persons/list')
def persons_list():
    """Return the list of persons as JSON for API usage."""
    persons_file = os.path.join(app_config.get('person_list_path', './person_lists'), 'persons.json')
    
    # Initialize persons list
    person_list = []
    
    # Load existing persons if file exists
    if os.path.exists(persons_file):
        try:
            with open(persons_file, 'r', encoding='utf-8') as f:
                person_list = json.load(f)
        except Exception as e:
            logger.error(f"Error loading persons: {e}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    return jsonify(person_list)

@app.route('/logs')
def logs():
    """Show application logs."""
    global GLOBAL_LOG
    from datetime import datetime
    
    # Try to read log file content
    try:
        with open('medicalspytool.log', 'r', encoding='utf-8') as f:
            log_content = f.read()
    except Exception as e:
        logger.error(f"Error reading log file: {e}", exc_info=True)
        log_content = "Error loading log file."
    
    return render_template('logs.html', log_content=log_content, config=app_config, now=datetime.now())

@app.route('/api/get_database_fields')
def get_database_fields():
    """API endpoint to get available fields for a database."""
    database = request.args.get('database', 'PubMed')
    
    if database == 'Combined':
        # For combined search, use common fields
        fields = ["Alle Felder", "Autor", "Titel"]
    else:
        # Get fields from the selected database connector
        connector_class = DATABASE_CONNECTORS.get(database)
        if connector_class:
            connector = connector_class()
            fields = connector.get_available_fields()
        else:
            fields = ["Alle Felder"]
    
    return jsonify(fields)

@app.route('/search_profiles', methods=['GET', 'POST', 'DELETE'])
def search_profiles():
    """Handle search profile management."""
    from datetime import datetime
    
    if request.method == 'GET':
        # Alle Suchprofile abrufen
        profiles = get_all_search_profiles()
        return render_template('search_profiles.html', 
                              profiles=profiles,
                              config=app_config,
                              now=datetime.now())
    
    elif request.method == 'POST':
        # Entweder ein Profil speichern oder laden
        action = request.form.get('action', '')
        
        if action == 'save':
            # Aktuelles Suchformular als Profil speichern
            profile_name = request.form.get('profile_name', '')
            
            if not profile_name.strip():
                flash('Bitte geben Sie einen Namen für das Suchprofil ein.', 'danger')
                return redirect(url_for('search_profiles'))
            
            # Suchparameter sammeln
            search_params = {
                'database': request.form.get('database', 'PubMed'),
                'search_term': request.form.get('search_term', ''),
                'additional_terms': request.form.get('additional_terms', ''),
                'person_name': request.form.get('person_name', ''),
                'max_results': request.form.get('max_results', '100'),
                'search_field': request.form.get('search_field', 'Alle Felder'),
                'language': request.form.get('language', ''),
                'pub_type': request.form.get('pub_type', ''),
                'use_date_filter': request.form.get('use_date_filter') == 'on'
            }
            
            # Datum-Filter hinzufügen, wenn aktiviert
            if search_params['use_date_filter']:
                start_date = request.form.get('start_date', '')
                end_date = request.form.get('end_date', '')
                if start_date and end_date:
                    search_params['date_range'] = {
                        'start': start_date,
                        'end': end_date
                    }
            
            # Profil speichern
            success = save_search_profile(profile_name, search_params)
            
            if success:
                flash(f'Suchprofil "{profile_name}" erfolgreich gespeichert.', 'success')
            else:
                flash(f'Fehler beim Speichern des Suchprofils "{profile_name}".', 'danger')
            
            return redirect(url_for('search_profiles'))
            
        elif action == 'load':
            # Ausgewähltes Profil laden
            profile_name = request.form.get('profile_name', '')
            
            if not profile_name:
                flash('Bitte wählen Sie ein Suchprofil aus.', 'danger')
                return redirect(url_for('search_profiles'))
            
            # Profil laden
            profile_data = load_search_profile(profile_name)
            
            if not profile_data:
                flash(f'Suchprofil "{profile_name}" konnte nicht geladen werden.', 'danger')
                return redirect(url_for('search_profiles'))
            
            # Profildaten in der Session speichern für die Suche-Seite
            session['loaded_profile'] = profile_data
            session['loaded_profile_name'] = profile_name
            
            flash(f'Suchprofil "{profile_name}" geladen. Sie können jetzt die Suche starten.', 'success')
            return redirect(url_for('search'))
            
    elif request.method == 'DELETE' or (request.method == 'POST' and request.form.get('action') == 'delete'):
        # Profil löschen
        if request.method == 'DELETE':
            # API-Aufruf
            data = request.get_json()
            profile_name = data.get('profile_name', '')
        else:
            # Formular-Aufruf
            profile_name = request.form.get('profile_name', '')
        
        if not profile_name:
            if request.method == 'DELETE':
                return jsonify({'error': 'No profile name provided'}), 400
            else:
                flash('Bitte wählen Sie ein Suchprofil zum Löschen aus.', 'danger')
                return redirect(url_for('search_profiles'))
        
        # Profil löschen
        success = delete_search_profile(profile_name)
        
        if request.method == 'DELETE':
            if success:
                return jsonify({'success': True, 'message': f'Profil "{profile_name}" gelöscht'})
            else:
                return jsonify({'error': f'Fehler beim Löschen des Profils "{profile_name}"'}), 500
        else:
            if success:
                flash(f'Suchprofil "{profile_name}" erfolgreich gelöscht.', 'success')
            else:
                flash(f'Fehler beim Löschen des Suchprofils "{profile_name}".', 'danger')
            return redirect(url_for('search_profiles'))
    
    # Fallback
    return redirect(url_for('search_profiles'))

@app.route('/api/search_profiles', methods=['GET'])
def api_search_profiles():
    """API endpoint to get all search profiles."""
    profiles = get_all_search_profiles()
    return jsonify(profiles)

@app.route('/api/search_profiles/<profile_name>', methods=['GET'])
def api_search_profile(profile_name):
    """API endpoint to get a specific search profile."""
    profile = load_search_profile(profile_name)
    if profile:
        return jsonify(profile)
    else:
        return jsonify({'error': f'Profil "{profile_name}" nicht gefunden'}), 404

@app.route('/api/get_visualization')
def get_visualization():
    """API endpoint to generate visualizations."""
    global search_results
    
    chart_type = request.args.get('type', 'year')
    
    if not search_results:
        return jsonify({'error': 'No data available'})
    
    try:
        import matplotlib.pyplot as plt
        import io
        import base64
        from collections import Counter
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        if chart_type == 'year':
            # Extract publication years
            years = [int(r.get("Publication Year")) for r in search_results 
                    if r.get("Publication Year", "").isdigit()]
            
            if not years:
                return jsonify({'error': 'No year data available'})
            
            # Count publications by year
            year_counter = Counter(years)
            
            # Sort by year
            sorted_years = sorted(year_counter.items())
            x, y = zip(*sorted_years)
            
            # Create bar chart
            plt.bar(x, y, color='navy')
            plt.xlabel('Publication Year')
            plt.ylabel('Number of Publications')
            plt.title('Publications by Year')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
        elif chart_type == 'database':
            # Extract databases
            databases = [r.get("Database", "Unknown") for r in search_results]
            
            if not databases:
                return jsonify({'error': 'No database data available'})
            
            # Count publications by database
            db_counter = Counter(databases)
            
            # Sort by count (descending)
            sorted_dbs = sorted(db_counter.items(), key=lambda x: x[1], reverse=True)
            x, y = zip(*sorted_dbs)
            
            # Create bar chart
            plt.bar(x, y, color='lightseagreen')
            plt.xlabel('Database')
            plt.ylabel('Number of Publications')
            plt.title('Publications by Database')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
        elif chart_type == 'person':
            # Extract persons
            persons = [r.get("Name", "Unknown") for r in search_results]
            
            if not persons:
                return jsonify({'error': 'No person data available'})
            
            # Count publications by person
            person_counter = Counter(persons)
            
            # Sort by count (descending) and take top 15
            sorted_persons = sorted(person_counter.items(), key=lambda x: x[1], reverse=True)[:15]
            x, y = zip(*sorted_persons)
            
            # Create horizontal bar chart
            plt.barh(x, y, color='darkgreen')
            plt.xlabel('Number of Publications')
            plt.ylabel('Person')
            plt.title('Top 15 Persons by Number of Publications')
            plt.grid(axis='x', linestyle='--', alpha=0.7)
            
        else:
            return jsonify({'error': 'Invalid chart type'})
        
        # Save plot to a buffer
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        buf.seek(0)
        
        # Convert to base64 string
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        return jsonify({'image': image_base64})
        
    except Exception as e:
        logger.error(f"Visualization error: {e}", exc_info=True)
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    """
    Entry point for the application.
    """
    try:
        logger.info("Starting application")
        # Check if needed directories exist, create if they don't
        ensure_directories(app_config)
        # Run the application
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)