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
print(f"Database URL: {database_url}")
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create database tables if they don't exist
with app.app_context():
    db.create_all()
    logger.info("Database tables created (if they didn't exist)")

# Initialize session variables if not present
@app.before_request
def before_request():
    if 'search_results' not in session:
        session['search_results'] = []
    if 'saved_queries' not in session:
        # Load saved queries from database
        with app.app_context():
            queries = SearchQuery.query.all()
            session['saved_queries'] = [query.to_dict() for query in queries]
    if 'settings' not in session:
        # Load settings from database
        with app.app_context():
            session['settings'] = Setting.get_settings_dict()
    if 'persons' not in session:
        # Load persons from database
        with app.app_context():
            persons = Person.query.all()
            session['persons'] = [person.to_dict() for person in persons]

# Add context processor to provide current year to all templates
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Render the search page or perform a search"""
    databases = ["PubMed", "Deutsche Nationalbibliothek"]
    
    if request.method == 'POST':
        # Handle search form submission
        search_query = request.form.get('search_query', '')
        selected_database = request.form.get('database', 'PubMed')
        additional_terms = request.form.get('additional_terms', '')
        
        # Get date range (if provided)
        start_date = request.form.get('start_date', '')
        end_date = request.form.get('end_date', '')
        date_range = parse_date_range(start_date, end_date)
        
        # Get selected person (if any)
        person_name = request.form.get('person_name', '')
        
        # Perform the search
        try:
            log_message(f"Starting search for '{search_query}' in {selected_database}")
            
            # Get appropriate connector
            connector = get_connector_for_database(selected_database, api_key=session['settings'].get('pubmed_api_key', ''))
            
            # Execute search
            results = search_database(
                connector, 
                search_query, 
                person_name=person_name,
                additional_terms=additional_terms,
                date_range=date_range
            )
            
            # Store results in session and database
            if results:
                # Save to session
                session['search_results'] = results
                session.modified = True
                
                # Save to database
                try:
                    # First save the search query if not already saved
                    search_query_obj = SearchQuery.query.filter_by(
                        query=search_query,
                        database=selected_database,
                        additional_terms=additional_terms
                    ).first()
                    
                    if not search_query_obj:
                        search_query_obj = SearchQuery(
                            name=f"Search in {selected_database}: {search_query[:30]}{'...' if len(search_query) > 30 else ''}",
                            query=search_query,
                            database=selected_database,
                            additional_terms=additional_terms,
                            start_date=start_date,
                            end_date=end_date,
                            person_name=person_name
                        )
                        db.session.add(search_query_obj)
                        db.session.flush()  # Get ID without committing
                    
                    # Now save each result
                    for result in results:
                        result_obj = SearchResult(
                            query_id=search_query_obj.id,
                            database=selected_database,
                            result_data=result
                        )
                        db.session.add(result_obj)
                    
                    db.session.commit()
                    log_message(f"Search results saved to database. Query ID: {search_query_obj.id}")
                    
                except Exception as e:
                    db.session.rollback()
                    log_message(f"Failed to save search results to database: {str(e)}", level="ERROR")
                    # Continue since we at least have the results in the session
                
                log_message(f"Search complete. Found {len(results)} results.")
                return redirect(url_for('results'))
            else:
                flash("No results found for your search query.", "warning")
                log_message("Search returned no results")
                
        except Exception as e:
            flash(f"Error during search: {str(e)}", "danger")
            log_message(f"Search error: {str(e)}", level="ERROR")
    
    # Get persons list for the dropdown
    persons = session.get('persons', [])
    
    # Get saved queries
    saved_queries = session.get('saved_queries', [])
    
    return render_template(
        'search.html', 
        databases=databases, 
        persons=persons,
        saved_queries=saved_queries
    )

@app.route('/results')
def results():
    """Display search results"""
    results = session.get('search_results', [])
    return render_template('results.html', results=results)

@app.route('/analysis')
def analysis():
    """Display analysis of search results"""
    results = session.get('search_results', [])
    
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
            
            flash("Settings updated successfully!", "success")
            log_message("Settings updated in session and database")
        except Exception as e:
            db.session.rollback()
            flash(f"Settings saved to session but failed to save to database: {str(e)}", "warning")
            log_message(f"Failed to save settings to database: {str(e)}", level="ERROR")
        
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
    results = session.get('search_results', [])
    
    if not results:
        return jsonify({"success": False, "message": "No results to export"}), 400
    
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
    
    if not data or 'query_name' not in data or 'search_query' not in data or 'database' not in data:
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    
    # Create new query object
    new_query = {
        'name': data['query_name'],
        'query': data['search_query'],
        'database': data['database'],
        'additional_terms': data.get('additional_terms', ''),
        'start_date': data.get('start_date', ''),
        'end_date': data.get('end_date', ''),
        'person_name': data.get('person_name', ''),
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
            person_name=new_query['person_name']
        )
        db.session.add(db_query)
        db.session.commit()
        
        # Update the session
        saved_queries = session.get('saved_queries', [])
        saved_queries.append(new_query)
        session['saved_queries'] = saved_queries
        session.modified = True
        
        log_message(f"Saved query: {data['query_name']}")
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        log_message(f"Failed to save query: {str(e)}", level="ERROR")
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

@app.route('/api/delete_query/<int:query_id>', methods=['DELETE'])
def api_delete_query(query_id):
    """API endpoint to delete a saved query"""
    try:
        # Find query in database
        query = SearchQuery.query.get(query_id)
        if query:
            query_name = query.name
            
            # Delete from database
            db.session.delete(query)
            db.session.commit()
            
            # Update session
            saved_queries = session.get('saved_queries', [])
            # Filter out the deleted query
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
            person = Person.query.get(person_id)
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
            person = Person.query.get(person_id)
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
