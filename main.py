"""
Integrated Publication Search Tool

This application provides a unified interface for searching multiple academic databases
including PubMed and the German National Library (DNB). It supports person management,
advanced search options, result visualization, and export functionality.

Usage:
    flask run
    or
    gunicorn -b 0.0.0:5000 main:app
"""

import os
import sys
import logging
import json
import atexit
import tempfile
import webbrowser
import threading
import time
import glob
import ctypes
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, flash, session
from flask_bootstrap import Bootstrap

# Import database connectors
from database_connectors import (
    PubMedConnector, DNBConnector, ScopusConnector, 
    WoSConnector, GeprisConnector
)

# Import utilities
from utils.search_profiles import (
    save_search_profile, load_search_profile, delete_search_profile, 
    get_all_search_profiles
)
from utils.path_manager import get_resource_path, get_writeable_path
from utils.config_manager import load_settings, save_settings, ensure_directories
from utils.logging_manager import log_message
from utils.export_manager import export_to_excel, export_to_csv, get_unique_filename


# Setup logging
def setup_logging():
    """
    Configures the application's logging.

    Sets up logging to file (`medicalspytool.log` in a writable path) and
    to the console. If file logging setup fails, it falls back to console-only
    logging.

    Returns:
        logging.Logger: The configured logger instance for the application.
    """
    try:
        log_file_path = get_writeable_path("medicalspytool.log")
        # Ensure the directory for the log file exists
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path, encoding='utf-8'),
                logging.StreamHandler(sys.stdout) # Ensure console output goes to stdout
            ]
        )
        logger = logging.getLogger(__name__)
        logger.info("Logging configured to file and console.")
        return logger
    except Exception as e:
        # Emergency fallback if logging setup fails (e.g., permission issues)
        print(f"CRITICAL: Error setting up file logging: {e}. Falling back to console-only logging.")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        logger = logging.getLogger(__name__)
        logger.warning("File logging setup failed. Using console-only logging.")
        return logger

logger = setup_logging()
logger.info(f"Medical Spytool starting up. Python version: {sys.version}")
logger.info(f"Running in frozen mode: {getattr(sys, 'frozen', False)}")

# Initialize Flask app with proper paths for template and static folders
app = Flask(__name__,
            template_folder=get_resource_path('templates'),
            static_folder=get_resource_path('static'))
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")
Bootstrap(app)

# Load configuration
try:
    app_config = load_settings()
    ensure_directories(app_config)
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Error loading configuration: {e}", exc_info=True)
    app_config = {
        "output_path": get_writeable_path("output"),
        "person_list_path": get_writeable_path("person_lists"),
        "unique_filenames": True,
        "default_database": "PubMed",
        "search_timeout": 30
    }
    logger.info("Using fallback configuration")

# Global variables
search_results = []
GLOBAL_LOG = []
loaded_profile = None
loaded_profile_name = None

# Timeout für API-Validierungsanfragen (in Sekunden)
API_VALIDATION_TIMEOUT = 5  # seconds


@atexit.register # Ensures this function is called on program exit
def cleanup_temp_files():
    """
    Cleans up temporary files created by the application upon exiting.

    This function searches for and removes files matching specific patterns
    (e.g., '*.tmp', '*.bak') in the system's temporary directory and
    the application's configured output directory. This helps prevent
    accumulation of temporary data.
    """
    logger.info("Starting cleanup of temporary files...")
    # Define patterns for files to be cleaned up
    patterns = [
        'medicalspytool*.tmp',
        'medicalspytool*.bak',
        'search_results_*.tmp',
        'export_*.tmp'
    ]

    # Get standard temporary directory
    temp_dir = tempfile.gettempdir()
    paths_to_check = [temp_dir]

    # Also check application's output directory if defined in config
    if app_config and 'output_path' in app_config:
        output_dir = app_config.get('output_path')
        if os.path.exists(output_dir) and os.path.isdir(output_dir): # Check if path is valid directory
            paths_to_check.append(output_dir)
        else:
            logger.warning(f"Output directory '{output_dir}' not found or not a directory. Skipping cleanup there.")

    files_deleted_count = 0
    for path_to_check in paths_to_check:
        for pattern in patterns:
            try:
                for filename in glob.glob(os.path.join(path_to_check, pattern)):
                    try:
                        if os.path.exists(filename): # Check if file still exists before attempting removal
                            os.remove(filename)
                            logger.debug(f"Temporary file deleted: {filename}")
                            files_deleted_count += 1
                    except (PermissionError, OSError) as e:
                        # Log specific error but continue cleanup
                        logger.warning(f"Could not delete temporary file '{filename}': {e}")
                        continue # to the next file
            except Exception as e:
                # Log error related to glob or path joining but continue
                logger.error(f"Error during globbing for pattern '{pattern}' in '{path_to_check}': {e}")
                continue # to the next pattern

    if files_deleted_count > 0:
        logger.info(f"Temporary file cleanup finished. Deleted {files_deleted_count} file(s).")
    else:
        logger.info("Temporary file cleanup finished. No relevant files found to delete.")

@app.route('/')
def index():
    """Render the main page."""
    from datetime import datetime
    return render_template('index.html', config=app_config, now=datetime.now())

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Handle search requests."""
    from datetime import datetime
    import json
    
    # Globale Variablen für Suchstatus
    global search_results
    global loaded_profile
    global loaded_profile_name
    
    try:
        if request.method == 'POST':
            # Formularvalidierung
            form_data = {}
            required_fields = ['database']
            
            # Sammle alle Formularfelder
            for field in request.form:
                form_data[field] = request.form.get(field)
            
            # Validiere Pflichtfelder
            missing_fields = [field for field in required_fields if not form_data.get(field)]
            if missing_fields:
                raise ValueError(f"Fehlende Pflichtfelder: {', '.join(missing_fields)}")
            
            database = form_data['database']
            
            # Validiere Person oder Suchbegriff
            search_term = form_data.get('search_term', '').strip()
            person_names = form_data.get('person_names', '').strip()
            
            if not search_term and not person_names:
                raise ValueError("Bitte geben Sie mindestens einen Suchbegriff oder eine Person ein")
            
            # Validiere maximale Ergebnisse
            try:
                max_results = int(form_data.get('max_results', 100))
                if max_results < 1 or max_results > 10000:
                    raise ValueError
            except ValueError:
                raise ValueError("Ungültige Anzahl maximaler Ergebnisse (1-10000)")
            
            # Initialisiere Suchvorgang
            log_message(None, f"Starting search in {database}")
            
            try:
                # Führe Suche basierend auf Datenbankauswahl durch
                results = []
                
                if database == 'Combined':
                    # Kombinierte Suche über alle Datenbanken
                    database_connectors = {
                        'PubMed': PubMedConnector(),
                        'DNB': DNBConnector(),
                        'Scopus': ScopusConnector(),
                        'WoS': WoSConnector(),
                        'GEPRIS': GeprisConnector()
                    }
                    
                    # Validiere API-Keys vor der Suche
                    for db_name, connector in database_connectors.items():
                        api_key = app_config.get(f'{db_name.lower()}_api_key')
                        if not connector.validate_api_key(api_key):
                            log_message(None, f"Warning: Invalid API key for {db_name}")
                            flash(f"Warnung: Ungültiger API-Schlüssel für {db_name}", "warning")
                    
                    # Führe parallele Suchen durch
                    search_tasks = []
                    for db_name, connector in database_connectors.items():
                        try:
                            search_results = connector.search(
                                search_term=search_term,
                                person_names=person_names.split(',') if person_names else None,
                                max_results=max_results,
                                **form_data
                            )
                            results.extend(search_results)
                        except Exception as db_error:
                            log_message(None, f"Error in {db_name}: {str(db_error)}")
                            flash(f"Fehler bei {db_name}: {str(db_error)}", "warning")
                
                else:
                    # Einzeldatenbanksuche
                    connector_class = {
                        'PubMed': PubMedConnector,
                        'DNB': DNBConnector,
                        'Scopus': ScopusConnector,
                        'WoS': WoSConnector,
                        'GEPRIS': GeprisConnector
                    }.get(database)
                    
                    if not connector_class:
                        raise ValueError(f"Unbekannte Datenbank: {database}")
                    
                    connector = connector_class()
                    api_key = app_config.get(f'{database.lower()}_api_key')
                    
                    if not connector.validate_api_key(api_key):
                        raise ValueError(f"Ungültiger API-Schlüssel für {database}")
                    
                    results = connector.search(
                        search_term=search_term,
                        person_names=person_names.split(',') if person_names else None,
                        max_results=max_results,
                        **form_data
                    )
                
                # Aktualisiere globale Ergebnisse
                search_results = results
                
                # Erfolgs- oder Warnmeldung
                if len(results) > 0:
                    flash(f"{len(results)} Ergebnisse gefunden.", "success")
                else:
                    flash("Keine Ergebnisse gefunden. Versuchen Sie andere Suchbegriffe oder Datenbanken.", "warning")
                
                return render_template('results.html', 
                                    results=results, 
                                    count=len(results),
                                    search_term=search_term,
                                    database=database,
                                    config=app_config,
                                    now=datetime.now())
                
            except Exception as search_error:
                error_msg = str(search_error)
                logger.error(f"Search error: {error_msg}", exc_info=True)
                log_message(None, f"Error during search: {error_msg}")
                return render_template('search.html', 
                                    error=error_msg,
                                    config=app_config,
                                    form_data=form_data,
                                    profile=loaded_profile,
                                    now=datetime.now())
        
        # GET request oder Form-Validierungsfehler
        profile_data = None
        if loaded_profile:
            profile_data = loaded_profile
            # Profile nach Verwendung zurücksetzen
            loaded_profile = None
            loaded_profile_name = None
        
        return render_template('search.html',
                            config=app_config,
                            profile=profile_data,
                            now=datetime.now())
                            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Unexpected error in search route: {error_msg}", exc_info=True)
        flash(error_msg, "danger")
        return render_template('search.html',
                            error=error_msg,
                            config=app_config,
                            profile=loaded_profile,
                            now=datetime.now())

@app.route('/cancel_search', methods=['POST'])
def cancel_search():
    """Cancel an ongoing search operation."""
    global search_results
    try:
        # Setze globale Suchergebnisse zurück
        search_results = []
        
        # Logge den Abbruch
        log_message(None, "Search cancelled by user")
        
        return jsonify({'status': 'success', 'message': 'Search cancelled'})
    except Exception as e:
        logger.error(f"Error cancelling search: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

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

@app.route('/api/get_visualization', methods=['GET'])
def get_visualization():
    """Generate and return chart visualizations for analysis."""
    import matplotlib
    matplotlib.use('Agg') # Use non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    import io
    import base64
    from collections import Counter

    global search_results
    if not search_results:
        return jsonify({'error': 'No search results available for visualization.'}), 400

    chart_type = request.args.get('type', 'year') # Default to year chart
    plt.style.use('seaborn-v0_8-darkgrid') # Using a seaborn style available in newer versions

    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        img = io.BytesIO()
        title = ""

        if chart_type == 'year':
            title = 'Publikationen nach Jahr'
            years = [str(r.get('Publication Year', 'N/A')) for r in search_results if r.get('Publication Year')]
            year_counts = Counter(sorted(years))
            if not year_counts:
                 return jsonify({'error': 'Keine gültigen Publikationsjahre für die Visualisierung gefunden.'}), 400

            sns.barplot(x=list(year_counts.keys()), y=list(year_counts.values()), ax=ax, palette="viridis")
            ax.set_ylabel('Anzahl Publikationen')
            ax.set_xlabel('Jahr')
            plt.xticks(rotation=45, ha="right")

        elif chart_type == 'database':
            title = 'Publikationen nach Datenbank'
            databases = [r.get('Database', 'N/A') for r in search_results]
            db_counts = Counter(databases)
            if not db_counts:
                return jsonify({'error': 'Keine Datenbankinformationen für die Visualisierung gefunden.'}), 400

            sns.barplot(x=list(db_counts.keys()), y=list(db_counts.values()), ax=ax, palette="crest")
            ax.set_ylabel('Anzahl Publikationen')
            ax.set_xlabel('Datenbank')
            plt.xticks(rotation=45, ha="right")

        elif chart_type == 'person':
            # This assumes 'Name' field in results refers to the person searched for,
            # or some other relevant person identifier from the search context.
            # This might need refinement based on how person-specific results are tagged.
            title = 'Publikationen nach Person (Suchkontext)'
            # 'Name' field in each result dict is assumed to hold the context of the search (e.g. searched person)
            # This is a simplification. A more robust solution would require results to be explicitly tagged with person IDs.
            persons_in_results = [r.get('Name', 'Unbekannt') for r in search_results if r.get('Name')]
            if not persons_in_results: # Check if list is empty
                 return jsonify({'error': 'Keine Personeninformationen in den Ergebnissen für die Visualisierung gefunden.'}), 400

            person_counts = Counter(persons_in_results)
            if not person_counts: # Check if Counter is empty
                 return jsonify({'error': 'Keine zählbaren Personeninformationen für die Visualisierung gefunden.'}), 400

            sns.barplot(x=list(person_counts.keys()), y=list(person_counts.values()), ax=ax, palette="magma")
            ax.set_ylabel('Anzahl Publikationen')
            ax.set_xlabel('Person (Suchkontext)')
            plt.xticks(rotation=45, ha="right")

        else:
            return jsonify({'error': 'Invalid chart type specified.'}), 400

        ax.set_title(title, fontsize=16)
        plt.tight_layout()
        fig.savefig(img, format='png', bbox_inches='tight')
        plt.close(fig) # Close the figure to free memory
        img.seek(0)

        img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
        return jsonify({'image': img_base64})

    except Exception as e:
        logger.error(f"Error generating visualization (type: {chart_type}): {e}", exc_info=True)
        # Ensure figure is closed on error too
        if 'fig' in locals() and plt.fignum_exists(fig.number): plt.close(fig)
        return jsonify({'error': f'Fehler beim Erstellen der Visualisierung: {str(e)}'}), 500


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
        app_config['scopus_api_key'] = request.form.get('scopus_api_key', '')
        app_config['wos_api_key'] = request.form.get('wos_api_key', '')
        app_config['gepris_api_key'] = request.form.get('gepris_api_key', '')
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
    
    dynamic_available_columns = []
    if search_results:
        # Collect all unique keys from all result dictionaries
        all_keys = set()
        for result in search_results:
            if isinstance(result, dict):
                all_keys.update(result.keys())
        # Sort for consistent order, can be customized further
        # Standard fields first, then others alphabetically
        standard_fields_ordered = [
            'Title', 'Authors', 'Publication Year', 'Publication Month', 'Journal',
            'Database', 'DOI', 'URL', 'Abstract', 'Keywords', 'Publication Type',
            'Language', 'Citation Count', 'PMID', 'ISBN', 'Identifier', 'Name',
            'Project ID', 'Investigators', 'Institution', 'Period', 'Subject Area', 'Publisher'
        ]

        # Prioritize standard fields that are present, then add others
        present_standard_fields = [field for field in standard_fields_ordered if field in all_keys]
        other_fields = sorted(list(all_keys - set(present_standard_fields)))
        dynamic_available_columns = present_standard_fields + other_fields
    
    if not dynamic_available_columns: # Fallback if no results or no keys
        dynamic_available_columns = [
            "Title", "Authors", "Publication Year", "Journal", "Database", "DOI", "URL"
        ]

    return render_template('export.html', 
                          results=search_results,
                          count=len(search_results) if search_results else 0,
                          available_columns=dynamic_available_columns, # Use dynamically generated columns
                          config=app_config,
                          now=datetime.now())
                          
@app.route('/export/update_settings', methods=['POST'])
def update_export_settings():
    """Update export settings."""
    global app_config
    
    if request.method == 'POST':
        # Spalten für den Export
        output_columns = request.form.getlist('output_columns')
        
        # Dateioptionen
        output_path = request.form.get('output_path', './output')
        unique_filenames = 'unique_filenames' in request.form
        filename_prefix = request.form.get('filename_prefix', 'medical_spytool_export')
        
        # Excel-Optionen
        excel_formatting = 'excel_formatting' in request.form
        excel_autofilter = 'excel_autofilter' in request.form
        excel_freeze_header = 'excel_freeze_header' in request.form
        
        # CSV-Optionen
        csv_delimiter = request.form.get('csv_delimiter', ',')
        csv_encoding = request.form.get('csv_encoding', 'utf-8')
        
        # Aktualisiere die Konfiguration
        app_config.update({
            'output_columns': output_columns,
            'output_path': output_path,
            'unique_filenames': unique_filenames,
            'filename_prefix': filename_prefix,
            'excel_formatting': excel_formatting,
            'excel_autofilter': excel_autofilter,
            'excel_freeze_header': excel_freeze_header,
            'csv_delimiter': csv_delimiter,
            'csv_encoding': csv_encoding
        })
        
        # Speichern der aktualisierten Konfiguration
        save_settings(app_config)
        
        # Stelle sicher, dass der Ausgabeordner existiert
        os.makedirs(output_path, exist_ok=True)
        
        flash('Export-Einstellungen wurden erfolgreich gespeichert.', 'success')
        
    return redirect(url_for('export_page'))

@app.route('/export/<format>')
def export(format):
    """Export results to file."""
    global search_results, app_config
    
    if not search_results:
        flash('Keine Ergebnisse zum Exportieren vorhanden. Bitte führen Sie zuerst eine Suche durch.', 'warning')
        return redirect(url_for('export_page'))
    
    # Create output directory if it doesn't exist
    output_path = app_config.get('output_path', './output')
    try:
        os.makedirs(output_path, exist_ok=True)
    except PermissionError as e:
        logger.error(f"Keine Berechtigung zum Erstellen des Ausgabeverzeichnisses: {str(e)}")
        flash(f"Keine Berechtigung zum Erstellen des Ausgabeverzeichnisses: {str(e)}", "danger")
        return redirect(url_for('export_page'))
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Ausgabeverzeichnisses: {str(e)}", exc_info=True)
        flash(f"Fehler beim Erstellen des Ausgabeverzeichnisses: {str(e)}", "danger")
        return redirect(url_for('export_page'))
    
    # Get file path
    filename_prefix = app_config.get('filename_prefix', 'medical_spytool_export')
    
    # Add timestamp if unique filenames are enabled
    if app_config.get('unique_filenames', True):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"{filename_prefix}_{timestamp}"
    else:
        base_name = filename_prefix
    
    file_path = os.path.join(output_path, base_name)
    
    try:
        if format == 'excel':
            file_path = f"{file_path}.xlsx"
            
            # Excel-spezifische Optionen
            excel_options = {
                'formatting': app_config.get('excel_formatting', True),
                'autofilter': app_config.get('excel_autofilter', True),
                'freeze_header': app_config.get('excel_freeze_header', True),
                'output_columns': app_config.get('output_columns', [])
            }
            
            # Export durchführen mit Optionen
            success = export_to_excel(search_results, file_path, options=excel_options)
            if not success:
                flash("Fehler beim Excel-Export. Versuche CSV als Alternative.", "warning")
                # Fallback zu CSV
                file_path = f"{os.path.splitext(file_path)[0]}.csv"
                csv_options = {
                    'delimiter': app_config.get('csv_delimiter', ','),
                    'encoding': app_config.get('csv_encoding', 'utf-8'),
                    'output_columns': app_config.get('output_columns', [])
                }
                success = export_to_csv(search_results, file_path, options=csv_options)
                if not success:
                    flash("Auch der CSV-Export ist fehlgeschlagen. Bitte überprüfen Sie die Logs.", "danger")
                    return redirect(url_for('export_page'))
            
            # Datei zum Download anbieten
            try:
                return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))
            except Exception as download_e:
                logger.error(f"Fehler beim Bereitstellen der Datei zum Download: {str(download_e)}", exc_info=True)
                flash(f"Die Datei wurde erstellt, kann aber nicht heruntergeladen werden: {str(download_e)}", "warning")
                flash(f"Sie finden die exportierte Datei hier: {file_path}", "info")
                return redirect(url_for('export_page'))
            
        elif format == 'csv':
            file_path = f"{file_path}.csv"
            
            # CSV-spezifische Optionen
            csv_options = {
                'delimiter': app_config.get('csv_delimiter', ','),
                'encoding': app_config.get('csv_encoding', 'utf-8'),
                'output_columns': app_config.get('output_columns', [])
            }
            
            # Export durchführen mit Optionen
            success = export_to_csv(search_results, file_path, options=csv_options)
            if not success:
                flash("Fehler beim CSV-Export. Bitte überprüfen Sie die Logs.", "danger")
                return redirect(url_for('export_page'))
            
            # Datei zum Download anbieten
            try:
                return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))
            except Exception as download_e:
                logger.error(f"Fehler beim Bereitstellen der Datei zum Download: {str(download_e)}", exc_info=True)
                flash(f"Die Datei wurde erstellt, kann aber nicht heruntergeladen werden: {str(download_e)}", "warning")
                flash(f"Sie finden die exportierte Datei hier: {file_path}", "info")
                return redirect(url_for('export_page'))
            
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
    
    # Personenlistendatei definieren
    persons_file = os.path.join(app_config.get('person_list_path', './person_lists'), 'persons.json')
    
    # Stelle sicher, dass das Verzeichnis existiert
    try:
        os.makedirs(os.path.dirname(persons_file), exist_ok=True)
        logger.info(f"Personenverzeichnis sichergestellt: {os.path.dirname(persons_file)}")
    except PermissionError as e:
        error_msg = f"Keine Berechtigung zum Erstellen des Personenverzeichnisses: {str(e)}"
        logger.error(error_msg)
        return render_template('persons.html', 
                               persons=[], 
                               error=error_msg,
                               config=app_config,
                               now=datetime.now())
    except OSError as e:
        error_msg = f"Betriebssystemfehler beim Erstellen des Personenverzeichnisses: {str(e)}"
        logger.error(error_msg)
        return render_template('persons.html', 
                               persons=[], 
                               error=error_msg,
                               config=app_config,
                               now=datetime.now())
    
    # Personenliste initialisieren
    person_list = []
    
    # Lade existierende Personen, falls Datei existiert
    if os.path.exists(persons_file):
        try:
            # Sichere Dateioperationen mit Fehlerbehandlung
            with open(persons_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
                if not file_content.strip():
                    # Leere Datei behandeln
                    logger.warning(f"Personenliste {persons_file} ist leer, initialisiere neue Liste")
                    person_list = []
                else:
                    person_list = json.loads(file_content)
            
            # Validiere, dass person_list tatsächlich eine Liste ist
            if not isinstance(person_list, list):
                logger.warning(f"Personenliste hat falsches Format (kein Array), initialisiere neue Liste")
                person_list = []
                
            logger.info(f"Personenliste aus {persons_file} geladen: {len(person_list)} Einträge")
        except json.JSONDecodeError as e:
            error_msg = f"Fehler beim Parsen der Personenliste: {str(e)}"
            logger.error(error_msg)
            
            # Erstelle Backup der defekten Datei
            try:
                backup_path = f"{persons_file}.backup-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                with open(persons_file, 'r', encoding='utf-8') as src, open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
                logger.info(f"Backup der defekten Personenliste erstellt: {backup_path}")
            except Exception as backup_e:
                logger.error(f"Fehler beim Erstellen des Backups der defekten Personenliste: {str(backup_e)}")
                
            return render_template('persons.html', 
                                  persons=person_list, 
                                  error=error_msg,
                                  config=app_config,
                                  now=datetime.now())
        except PermissionError as e:
            error_msg = f"Keine Berechtigung zum Lesen der Personenliste: {str(e)}"
            logger.error(error_msg)
            return render_template('persons.html', 
                                  persons=person_list, 
                                  error=error_msg,
                                  config=app_config,
                                  now=datetime.now())
        except FileNotFoundError as e:
            error_msg = f"Personenliste nicht gefunden: {str(e)}"
            logger.error(error_msg)
            # Kein Fehler dem Benutzer anzeigen, da wir dann einfach eine leere Liste verwenden
        except Exception as e:
            error_msg = f"Unerwarteter Fehler beim Laden der Personenliste: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return render_template('persons.html', 
                                  persons=person_list, 
                                  error=error_msg,
                                  config=app_config,
                                  now=datetime.now())
    
    # Verarbeite POST-Anfragen für Aktionen
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            # Füge eine neue Person hinzu
            firstname = request.form.get('firstname', '').strip()
            lastname = request.form.get('lastname', '').strip()
            search_term = request.form.get('search_term', '').strip()
            additional_terms = request.form.get('additional_terms', '').strip()
            
            # Vollständiger Name
            full_name = f"{firstname} {lastname}".strip()
            
            if firstname and lastname:
                # Wenn kein Suchbegriff angegeben wurde, Nachname als Suchbegriff verwenden
                if not search_term:
                    search_term = lastname
                
                person = {
                    'Name': full_name,
                    'Firstname': firstname,
                    'Lastname': lastname,
                    'Search Term': search_term if search_term else None,
                    'Additional Terms': additional_terms if additional_terms else None
                }
                
                # Auf Duplikate prüfen
                if not any(p.get('Name') == full_name for p in person_list):
                    person_list.append(person)
                    
                    # Speichere die aktualisierte Liste mit sicheren Dateioperationen
                    try:
                        # Sichere Dateioperationen mit temporärer Datei
                        temp_file = f"{persons_file}.tmp"
                        with open(temp_file, 'w', encoding='utf-8') as f:
                            json.dump(person_list, f, indent=2, ensure_ascii=False)
                        
                        # Überprüfe, ob die temporäre Datei korrekt geschrieben wurde
                        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                            # Erstelle Backup der alten Datei, falls vorhanden
                            if os.path.exists(persons_file):
                                backup_path = f"{persons_file}.bak"
                                try:
                                    with open(persons_file, 'r', encoding='utf-8') as src, open(backup_path, 'w', encoding='utf-8') as dst:
                                        dst.write(src.read())
                                except Exception as e:
                                    logger.warning(f"Konnte kein Backup der alten Personenliste erstellen: {str(e)}")
                            
                            # Ersetze die alte Datei durch die neue
                            if os.path.exists(persons_file):
                                os.replace(temp_file, persons_file)
                            else:
                                os.rename(temp_file, persons_file)
                                
                            logger.info(f"Person '{full_name}' hinzugefügt und Liste gespeichert")
                            flash(f"Person '{full_name}' erfolgreich hinzugefügt.", "success")
                        else:
                            # Temporäre Datei wurde nicht korrekt geschrieben
                            error_msg = "Fehler beim Speichern: Temporäre Datei konnte nicht erstellt werden"
                            logger.error(error_msg)
                            if os.path.exists(temp_file):
                                os.remove(temp_file)  # Entferne fehlerhafte temporäre Datei
                            return render_template('persons.html', 
                                                  persons=person_list, 
                                                  error=error_msg,
                                                  config=app_config,
                                                  now=datetime.now())
                    except PermissionError as e:
                        error_msg = f"Keine Berechtigung zum Speichern der Personenliste: {str(e)}"
                        logger.error(error_msg)
                        return render_template('persons.html', 
                                              persons=person_list, 
                                              error=error_msg,
                                              config=app_config,
                                              now=datetime.now())
                    except OSError as e:
                        error_msg = f"Betriebssystemfehler beim Speichern der Personenliste: {str(e)}"
                        logger.error(error_msg)
                        return render_template('persons.html', 
                                              persons=person_list, 
                                              error=error_msg,
                                              config=app_config,
                                              now=datetime.now())
                    except Exception as e:
                        error_msg = f"Unerwarteter Fehler beim Speichern der Personenliste: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        return render_template('persons.html', 
                                              persons=person_list, 
                                              error=error_msg,
                                              config=app_config,
                                              now=datetime.now())
                else:
                    # Person existiert bereits
                    flash(f"Person '{full_name}' existiert bereits.", "warning")
            else:
                # Vorname oder Nachname fehlt
                flash("Bitte geben Sie Vor- und Nachnamen ein.", "warning")
        
        elif action == 'delete':
            # Lösche eine Person
            try:
                index = int(request.form.get('index', -1))
                if 0 <= index < len(person_list):
                    deleted_name = person_list[index].get('Name', 'Unbekannt')
                    del person_list[index]
                    
                    # Speichere die aktualisierte Liste mit sicheren Dateioperationen
                    try:
                        # Sichere Dateioperationen mit temporärer Datei
                        temp_file = f"{persons_file}.tmp"
                        with open(temp_file, 'w', encoding='utf-8') as f:
                            json.dump(person_list, f, indent=2, ensure_ascii=False)
                        
                        # Überprüfe, ob die temporäre Datei korrekt geschrieben wurde
                        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                            # Erstelle Backup der alten Datei
                            if os.path.exists(persons_file):
                                backup_path = f"{persons_file}.bak"
                                try:
                                    with open(persons_file, 'r', encoding='utf-8') as src, open(backup_path, 'w', encoding='utf-8') as dst:
                                        dst.write(src.read())
                                except Exception as e:
                                    logger.warning(f"Konnte kein Backup der alten Personenliste erstellen: {str(e)}")
                            
                            # Ersetze die alte Datei durch die neue
                            if os.path.exists(persons_file):
                                os.replace(temp_file, persons_file)
                            else:
                                os.rename(temp_file, persons_file)
                                
                            logger.info(f"Person '{deleted_name}' gelöscht und Liste gespeichert")
                            flash(f"Person '{deleted_name}' erfolgreich gelöscht.", "success")
                        else:
                            # Temporäre Datei wurde nicht korrekt geschrieben
                            error_msg = "Fehler beim Speichern: Temporäre Datei konnte nicht erstellt werden"
                            logger.error(error_msg)
                            if os.path.exists(temp_file):
                                os.remove(temp_file)  # Entferne fehlerhafte temporäre Datei
                            return render_template('persons.html', 
                                                  persons=person_list, 
                                                  error=error_msg,
                                                  config=app_config,
                                                  now=datetime.now())
                    except PermissionError as e:
                        error_msg = f"Keine Berechtigung zum Speichern der Personenliste: {str(e)}"
                        logger.error(error_msg)
                        return render_template('persons.html', 
                                              persons=person_list, 
                                              error=error_msg,
                                              config=app_config,
                                              now=datetime.now())
                    except OSError as e:
                        error_msg = f"Betriebssystemfehler beim Speichern der Personenliste: {str(e)}"
                        logger.error(error_msg)
                        return render_template('persons.html', 
                                              persons=person_list, 
                                              error=error_msg,
                                              config=app_config,
                                              now=datetime.now())
                    except Exception as e:
                        error_msg = f"Unerwarteter Fehler beim Speichern der Personenliste: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        return render_template('persons.html', 
                                              persons=person_list, 
                                              error=error_msg,
                                              config=app_config,
                                              now=datetime.now())
                else:
                    flash("Ungültiger Index für Löschvorgang.", "danger")
            except ValueError:
                flash("Ungültiger Index-Wert.", "danger")
    
    return render_template('persons.html', persons=person_list, config=app_config, now=datetime.now())

@app.route('/api/persons')
def api_persons_list():
    """API endpoint for person selection with autocomplete.
    
    Returns:
        JSON response with filtered persons or error message
    """
    try:
        # Get query parameter
        query = request.args.get('query', '').lower()
        
        # Try to get persons from session cache first
        persons = session.get('cached_persons')
        
        if persons is None:
            # Load from file if not in cache
            persons_path = os.path.join(app_config.get('person_list_path', 'person_lists'), 'persons.json')
            
            if not os.path.exists(persons_path):
                # Return empty list if file doesn't exist
                session['cached_persons'] = []
                return jsonify([])
            
            try:
                with open(persons_path, 'r', encoding='utf-8') as f:
                    persons = json.load(f)
                    
                # Validate data structure
                if not isinstance(persons, list):
                    logger.error("Invalid persons data structure: not a list")
                    return jsonify([]), 500
                    
                # Cache the results
                session['cached_persons'] = persons
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error in persons file: {e}")
                return jsonify({'error': 'Invalid persons data format'}), 500
            except Exception as e:
                logger.error(f"Error reading persons file: {e}", exc_info=True)
                return jsonify({'error': 'Internal server error'}), 500
        
        # Filter persons if query is provided
        if query:
            filtered_persons = []
            for person in persons:
                name = person.get('Name', '').lower()
                firstname = person.get('Firstname', '').lower()
                lastname = person.get('Lastname', '').lower()
                
                if (query in name or 
                    query in firstname or 
                    query in lastname):
                    filtered_persons.append(person)
            
            # Sort results: exact matches first, then by alphabet
            filtered_persons.sort(
                key=lambda p: (
                    0 if p.get('Name', '').lower().startswith(query) else 1,
                    p.get('Name', '')
                )
            )
            
            # Limit results
            persons = filtered_persons[:10]
        
        return jsonify(persons)
        
    except Exception as e:
        logger.error(f"Unexpected error in api_persons_list: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

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

@app.route('/search_profiles', methods=['GET'])
def search_profiles():
    """Handle search profiles page."""
    from datetime import datetime
    
    profiles = get_all_search_profiles()
    return render_template('search_profiles.html', 
                         profiles=profiles,
                         config=app_config,
                         now=datetime.now())

@app.route('/save_search_profile', methods=['POST'])
def save_search_profile():
    """Save a search profile."""
    profile_name = request.form.get('profile_name')
    profile_data = request.form.get('profile_data')
    
    if not profile_name or not profile_data:
        flash('Profilname und Daten sind erforderlich.', 'danger')
        return redirect(url_for('search'))
    
    try:
        # Konvertiere Profildaten zu JSON
        profile_data = json.loads(profile_data)
        
        # Speichere das Profil
        success = save_search_profile(profile_name, profile_data)
        
        if success:
            flash(f'Suchprofil "{profile_name}" erfolgreich gespeichert.', 'success')
        else:
            flash('Fehler beim Speichern des Suchprofils.', 'danger')
    except Exception as e:
        logger.error(f"Error saving search profile: {e}", exc_info=True)
        flash(f'Fehler beim Speichern des Suchprofils: {str(e)}', 'danger')
    
    return redirect(url_for('search'))

@app.route('/load_search_profile/<profile_name>', methods=['GET'])
def load_search_profile_endpoint(profile_name):
    """Load a search profile."""
    global loaded_profile
    global loaded_profile_name
    
    try:
        profile_data = load_search_profile(profile_name)
        
        if profile_data:
            loaded_profile = profile_data
            loaded_profile_name = profile_name
            flash(f'Suchprofil "{profile_name}" geladen.', 'success')
        else:
            flash(f'Suchprofil "{profile_name}" nicht gefunden.', 'warning')
    except Exception as e:
        logger.error(f"Error loading search profile: {e}", exc_info=True)
        flash(f'Fehler beim Laden des Suchprofils: {str(e)}', 'danger')
    
    return redirect(url_for('search'))

@app.route('/delete_search_profile/<profile_name>', methods=['POST'])
def delete_search_profile_endpoint(profile_name):
    """Delete a search profile."""
    try:
        success = delete_search_profile(profile_name)
        
        if success:
            flash(f'Suchprofil "{profile_name}" erfolgreich gelöscht.', 'success')
        else:
            flash(f'Suchprofil "{profile_name}" nicht gefunden.', 'warning')
    except Exception as e:
        logger.error(f"Error deleting search profile: {e}", exc_info=True)
        flash(f'Fehler beim Löschen des Suchprofils: {str(e)}', 'danger')
    
    return redirect(url_for('search_profiles'))

@app.route('/logs')
def logs():
    """Show application logs."""
    global GLOBAL_LOG
    from datetime import datetime
    
    log_file = get_writeable_path("medicalspytool.log")
    log_content = []
    
    # Try to read log file content
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.readlines()
                # Beschränke auf die letzten 1000 Zeilen
                log_content = log_content[-1000:]
    except Exception as e:
        logger.error(f"Error reading log file: {e}", exc_info=True)
        flash(f"Fehler beim Lesen der Logdatei: {str(e)}", "danger")
    
    # Kombiniere Datei-Logs mit In-Memory-Logs
    all_logs = GLOBAL_LOG + log_content
    
    # Get detailed system info for advanced log
    system_info = {
        "os": sys.platform,
        "python_version": sys.version,
        "app_version": "2.0.0",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "config": app_config
    }
    
    try:
        import platform
        system_info["platform"] = platform.platform()
        system_info["processor"] = platform.processor()
        system_info["machine"] = platform.machine()
    except:
        pass
    
    return render_template('logs.html',
                          logs=all_logs,
                          system_info=system_info,
                          config=app_config,
                          now=datetime.now())

@app.route('/api/check_dependencies')
def check_dependencies():
    """API endpoint to check dependencies and their versions."""
    try:
        import pkg_resources
        import platform
        import sys
        
        # Get installed packages and their versions
        installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
        
        # Check required packages (based on the imports in this application)
        required_packages = [
            'flask', 'flask-bootstrap', 'requests', 'pandas', 
            'numpy', 'lxml', 'beautifulsoup4', 'openpyxl', 
            'matplotlib', 'seaborn'
        ]
        
        dependencies_status = {}
        for package in required_packages:
            if package in installed_packages:
                dependencies_status[package] = {
                    'installed': True,
                    'version': installed_packages.get(package, 'Unknown'),
                    'status': 'OK'
                }
            else:
                dependencies_status[package] = {
                    'installed': False,
                    'version': None,
                    'status': 'Missing'
                }
        
        # Add system information
        system_info = {
            'python_version': platform.python_version(),
            'system': platform.system(),
            'platform': platform.platform(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }
        
        log_message(None, f"Dependencies check completed successfully")
        return jsonify({
            'success': True,
            'dependencies': dependencies_status,
            'system_info': system_info,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        log_message(None, f"Error checking dependencies: {str(e)}", level=logging.ERROR)
        return jsonify({
            'success': False,
            'message': f"Error checking dependencies: {str(e)}",
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

@app.route('/api/test_connections')
def test_connections():
    """API endpoint to test database connections."""
    try:
        results = {}
        
        # Test PubMed connection
        pubmed = PubMedConnector()
        pubmed_result = pubmed.test_connection()
        results['PubMed'] = pubmed_result
        
        # Test DNB connection
        dnb = DNBConnector()
        dnb_result = dnb.test_connection()
        results['DNB'] = dnb_result
        
        # Test Scopus connection if API key is available
        scopus_api_key = app_config.get('scopus_api_key')
        if scopus_api_key:
            scopus = ScopusConnector()
            scopus_result = scopus.test_connection()
            results['Scopus'] = scopus_result
        else:
            results['Scopus'] = {
                'status': 'Not Tested',
                'message': 'API key not configured',
                'response_time': None
            }
        
        # Test Web of Science connection if API key is available
        wos_api_key = app_config.get('wos_api_key')
        if wos_api_key:
            wos = WoSConnector()
            wos_result = wos.test_connection()
            results['Web of Science'] = wos_result
        else:
            results['Web of Science'] = {
                'status': 'Not Tested',
                'message': 'API key not configured',
                'response_time': None
            }
        
        # Test GEPRIS connection
        gepris = GeprisConnector()
        gepris_result = gepris.test_connection()
        results['GEPRIS'] = gepris_result
        
        log_message(None, f"Database connection tests completed")
        return jsonify({
            'success': True,
            'connections': results,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        log_message(None, f"Error testing database connections: {str(e)}", level=logging.ERROR)
        return jsonify({
            'success': False,
            'message': f"Error testing database connections: {str(e)}",
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

@app.route('/api/check_storage_paths')
def check_storage_paths():
    """API endpoint to check storage paths and their write permissions."""
    try:
        paths_to_check = {
            'output_directory': get_writeable_path(app_config.get('output_path', 'output')),
            'person_list_directory': get_writeable_path(app_config.get('person_list_path', 'person_lists')),
            'logs_directory': os.path.dirname(get_writeable_path('medicalspytool.log')),
            'temp_directory': tempfile.gettempdir()
        }
        
        path_status = {}
        for name, path in paths_to_check.items():
            try:
                # Check if path exists
                exists = os.path.exists(path)
                
                # Check if directory
                is_dir = os.path.isdir(path) if exists else False
                
                # Check write permissions by attempting to create a test file
                writable = False
                if exists and is_dir:
                    test_file = os.path.join(path, f"write_test_{int(time.time())}.tmp")
                    try:
                        with open(test_file, 'w') as f:
                            f.write('test')
                        writable = True
                        # Clean up test file
                        if os.path.exists(test_file):
                            os.remove(test_file)
                    except (IOError, PermissionError):
                        writable = False
                
                # Get free space in MB
                free_space_mb = None
                if exists:
                    try:
                        if sys.platform == 'win32':
                            free_bytes = ctypes.c_ulonglong(0)
                            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(path), None, None, ctypes.pointer(free_bytes))
                            free_space_mb = free_bytes.value / (1024 * 1024)
                        else:
                            st = os.statvfs(path)
                            free_space_mb = (st.f_bavail * st.f_frsize) / (1024 * 1024)
                    except Exception:
                        free_space_mb = "Unknown"
                
                path_status[name] = {
                    'path': path,
                    'exists': exists,
                    'is_directory': is_dir,
                    'writable': writable,
                    'free_space_mb': free_space_mb,
                    'status': 'OK' if (exists and is_dir and writable) else 'Problem'
                }
                
            except Exception as path_error:
                path_status[name] = {
                    'path': path,
                    'error': str(path_error),
                    'status': 'Error'
                }
        
        log_message(None, f"Storage paths check completed")
        return jsonify({
            'success': True,
            'paths': path_status,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        log_message(None, f"Error checking storage paths: {str(e)}", level=logging.ERROR)
        return jsonify({
            'success': False,
            'message': f"Error checking storage paths: {str(e)}",
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

@app.route('/api/check_can_iterate')
def check_can_iterate():
    """API endpoint to check if the system can continue to iterate.
    
    This diagnostic tool checks:
    1. If there are more search results to process
    2. If any background tasks are running
    3. If system resources are available for continued processing
    4. If there are any errors or warnings that would prevent iteration
    """
    try:
        global search_results
        
        # Check for search results
        has_search_results = len(search_results) > 0
        processed_results = getattr(search_results, 'processed_count', 0)
        total_results = len(search_results)
        
        # Check system resources
        import psutil
        memory_available = True
        cpu_available = True
        
        try:
            memory = psutil.virtual_memory()
            memory_available = memory.percent < 90  # Consider memory available if usage is below 90%
            
            cpu = psutil.cpu_percent(interval=0.5)
            cpu_available = cpu < 80  # Consider CPU available if usage is below 80%
        except:
            # If psutil fails, assume resources are available
            pass
        
        # Check for any errors in log that might prevent iteration
        error_count = 0
        warning_count = 0
        
        try:
            log_path = get_writeable_path("medicalspytool.log")
            if os.path.exists(log_path):
                with open(log_path, 'r') as log_file:
                    log_contents = log_file.read()
                    error_count = log_contents.count('ERROR')
                    warning_count = log_contents.count('WARNING')
        except:
            # If log file can't be read, assume no errors
            pass
        
        # Check database connectors status
        connectors_available = {
            'PubMed': True,
            'DNB': True,
            'Scopus': True,
            'WoS': True,
            'GEPRIS': True
        }
        
        # Quick API key validation (without making external calls)
        for db_name in connectors_available.keys():
            api_key = app_config.get(f'{db_name.lower()}_api_key', '')
            connectors_available[db_name] = bool(api_key)
        
        # Determine if iteration can continue
        can_iterate = has_search_results and memory_available and cpu_available
        
        # Identify any blocking issues
        blocking_issues = []
        
        if not has_search_results:
            blocking_issues.append("No search results available to process")
        
        if not memory_available:
            blocking_issues.append("System memory usage is too high (>90%)")
        
        if not cpu_available:
            blocking_issues.append("CPU usage is too high (>80%)")
        
        if error_count > 10:
            blocking_issues.append(f"High number of errors detected in logs ({error_count})")
        
        # Return comprehensive status information
        return jsonify({
            'status': 'success',
            'can_iterate': can_iterate,
            'search_results': {
                'available': has_search_results,
                'count': total_results,
                'processed': processed_results,
                'remaining': total_results - processed_results if hasattr(search_results, 'processed_count') else 'unknown'
            },
            'system_resources': {
                'memory_available': memory_available,
                'cpu_available': cpu_available
            },
            'log_status': {
                'error_count': error_count,
                'warning_count': warning_count
            },
            'connectors_available': connectors_available,
            'blocking_issues': blocking_issues
        })
        
    except Exception as e:
        logger.error(f"Error checking iteration status: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e),
            'can_iterate': False
        }), 500

@app.route('/api/clear_logs', methods=['POST'])
def clear_logs():
    """API endpoint to clear all logs."""
    try:
        log_path = get_writeable_path("medicalspytool.log")
        
        # First, log the operation before clearing
        log_message(None, "Log file cleared by user request", level=logging.WARNING)
        
        # Clear the log file
        with open(log_path, 'w') as f:
            f.write(f"Log file cleared on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Reset the global log array
        global GLOBAL_LOG
        GLOBAL_LOG = [f"Log file cleared on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
        
        return jsonify({
            'success': True,
            'message': 'Logs successfully cleared',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        log_message(None, f"Error clearing logs: {str(e)}", level=logging.ERROR)
        return jsonify({
            'success': False,
            'message': f"Error clearing logs: {str(e)}",
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

@app.route('/info')
def info():
    """Show information about the application."""
    from datetime import datetime
    return render_template('info.html', 
                         config=app_config,
                         now=datetime.now(),
                         version="2.0.0")  # Add version information

# API Key Validation Routes
@app.route('/validate_api_key/<database_name>', methods=['POST'])
def validate_api_key_route(database_name):
    """Validate API key for a given database."""
    from utils.api_key_manager import validate_api_key as validate_key_util

    try:
        data = request.get_json()
        if not data or 'api_key' not in data:
            return jsonify({'valid': False, 'message': 'API key not provided in request.'}), 400

        api_key_to_validate = data['api_key']

        connector_map = {
            'pubmed': PubMedConnector,
            'dnb': DNBConnector,
            'scopus': ScopusConnector,
            'wos': WoSConnector,
            'gepris': GeprisConnector # Gepris doesn't use API keys, but manager handles it.
        }

        connector_class = connector_map.get(database_name.lower())
        if not connector_class:
            return jsonify({'valid': False, 'message': 'Invalid database specified.'}), 404

        # Instantiate connector (API key here is for the instance, validation will use key_to_validate)
        # For connectors that don't strictly need a key for instantiation, this is fine.
        # For those that do, they usually fetch from config if not provided.
        # The api_key_manager's validate_api_key will use the one passed to it.
        connector_instance = connector_class(api_key=app_config.get(f'{database_name.lower()}_api_key', ''), settings=app_config)

        # Use the validation utility which includes timeout and caching
        is_valid, message = validate_key_util(connector_instance, api_key_to_validate)

        return jsonify({'valid': is_valid, 'message': message})

    except Exception as e:
        logger.error(f"Error validating API key for {database_name}: {e}", exc_info=True)
        return jsonify({'valid': False, 'message': f'Error during validation: {str(e)}'}), 500

# API endpoint for dynamic search options
@app.route('/api/database_options/<database_name>')
def get_database_options(database_name):
    """Return dynamic options for a given database (search fields, pub types, languages)."""
    options = {
        'search_fields': [],
        'pub_types': [],
        'languages': [] # Common languages, can be expanded
    }

    # Default common languages, can be overridden by specific connectors if needed
    common_languages = ["English", "German", "French", "Spanish", "Chinese", "Japanese", "Russian"]

    if database_name.lower() == 'pubmed':
        options['search_fields'] = ['All Fields', 'Title', 'Author', 'Journal', 'Abstract', 'MeSH Terms', 'Affiliation']
        options['pub_types'] = [
            'Journal Article', 'Review', 'Clinical Trial', 'Letter', 'Editorial',
            'Meta-Analysis', 'Systematic Review', 'Case Reports'
        ] # These are common PubMed types, actual list is vast.
        options['languages'] = common_languages
    elif database_name.lower() == 'dnb':
        options['search_fields'] = ['Alle Felder', 'Titel', 'Autor', 'Schlagwort', 'Verlag', 'ISBN']
        options['pub_types'] = [ # DNB uses specific material types
            'Monographie', 'Zeitschrift', 'Online-Ressource', 'Karte', 'Hochschulschrift', 'Tonträger'
        ]
        options['languages'] = common_languages
    elif database_name.lower() == 'scopus':
        options['search_fields'] = ['All Fields', 'Title', 'Author', 'Abstract', 'Keywords', 'Affiliation', 'Source Title']
        options['pub_types'] = ['Article', 'Review', 'Conference Paper', 'Book', 'Book Chapter', 'Editorial', 'Letter']
        options['languages'] = common_languages # Scopus supports many, these are examples
    elif database_name.lower() == 'wos':
        # WoSConnector has get_available_fields, but it's not static.
        # For simplicity here, providing a common list. A better way would be to instantiate connector.
        options['search_fields'] = ["All Fields", "Author", "Title", "Abstract", "Keywords", "Address", "DOI", "ISSN", "Journal", "Conference"]
        options['pub_types'] = ["Article", "Review", "Proceedings Paper", "Book Chapter", "Editorial", "Letter"]
        options['languages'] = ["English", "German", "French", "Spanish", "Portuguese", "Russian", "Japanese", "Chinese"]
    elif database_name.lower() == 'gepris':
        options['search_fields'] = ['All Fields', 'Project Title', 'Person', 'Institution'] # Gepris is project/person focused
        options['pub_types'] = ['Project', 'Person', 'Institution'] # Conceptual types for Gepris
        options['languages'] = ["German", "English"] # Gepris is primarily German/English
    else:
        return jsonify({'error': 'Unknown database name'}), 404

    return jsonify(options)

# Globale Fehlerbehandlung
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html',
                          error="404 - Seite nicht gefunden",
                          message="Die angeforderte Seite wurde nicht gefunden.",
                          config=app_config,
                          now=datetime.now()), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html',
                          error="500 - Interner Serverfehler",
                          message="Ein interner Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.",
                          config=app_config,
                          now=datetime.now()), 500

@app.errorhandler(Exception)
def unhandled_exception(e):
    logger.error(f"Unbehandelter Fehler: {str(e)}", exc_info=True)
    return render_template('error.html',
                          error="Unerwarteter Fehler",
                          message=f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}",
                          config=app_config,
                          now=datetime.now()), 500

if __name__ == '__main__':
    try:
        ensure_directories(app_config) # Ensure writable directories like logs, output, person_lists exist

        is_frozen = getattr(sys, 'frozen', False)
        
        if is_frozen:
            # Running as a PyInstaller bundle
            logger.info("Application is running as a frozen executable.")
            # Optionally, prevent webbrowser.open if it's a background process or not desired
            # if app_config.get("auto_open_browser", True): # Make it configurable
            #    webbrowser.open('http://127.0.0.1:5000/') # Or the configured host/port

            from waitress import serve
            # Use a configured host and port, or defaults
            # Ensure host is 0.0.0.0 or specific IP if network access is needed,
            # 127.0.0.1 for local access only.
            host = app_config.get("server_host", "127.0.0.1") # Default to local access for bundled app
            port = app_config.get("server_port", 5000)
            logger.info(f"Starting Waitress WSGI server on {host}:{port}")
            serve(app, host=host, port=port)
        else:
            # Running as a script (development mode)
            logger.info("Application is running in development mode.")
            if os.environ.get("WERKZEUG_RUN_MAIN") != "true": # Avoid opening browser twice with reloader
                 webbrowser.open('http://127.0.0.1:5000/')
            app.run(debug=True, host="127.0.0.1", port=5000) # Standard Flask dev server
            
    except Exception as e:
        logger.error(f"Application startup error: {e}", exc_info=True)
        # Zeige Fehlermeldung für 10 Sekunden an
        print(f"\nFehler beim Starten der Anwendung: {e}")
        print("\nDie Anwendung wird in 10 Sekunden beendet...")
        time.sleep(10)