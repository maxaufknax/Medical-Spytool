@search_bp.route("/", methods=["GET", "POST"])
def index():
    """Handle search form display and search execution"""
    if request.method == "POST":
        errors = []
        
        # CSRF validation
        csrf_token = request.form.get('csrf_token')
        if not csrf_token:
            flash('Sicherheitstoken fehlt. Bitte laden Sie die Seite neu.', 'error')
            return redirect(url_for('search.index'))
        
        try:
            validate_csrf(csrf_token)
        except ValidationError:
            flash('Ungültiges oder abgelaufenes Sicherheitstoken. Bitte laden Sie die Seite neu.', 'error')
            return redirect(url_for('search.index'))
        
        # Get and validate search parameters
        search_mode = request.form.get('search_mode', 'simple')
        selected_databases = request.form.getlist('databases') # Ensure this is getlist
        
        # Determine query based on search mode
        if search_mode == 'simple':
            query = request.form.get('simple_query_content', '').strip()
        elif search_mode == 'person':
            # For person search, construct query from selected persons and optional keywords
            selected_person_ids_str = request.form.get('selected_person_ids', '')
            additional_keywords = request.form.get('person_search_keywords', '').strip()
            
            if not selected_person_ids_str:
                flash('Bitte wählen Sie mindestens eine Person für die personenbezogene Suche aus.', 'warning')
                return redirect(url_for('search.index'))

            selected_person_ids = [int(pid) for pid in selected_person_ids_str.split(',') if pid.isdigit()]
            persons = Person.query.filter(Person.id.in_(selected_person_ids)).all()
            
            if not persons:
                flash('Ausgewählte Personen nicht gefunden. Bitte versuchen Sie es erneut.', 'warning')
                return redirect(url_for('search.index'))

            # Construct a query string, e.g., "John Doe OR Jane Smith"
            person_names = [f"{p.first_name} {p.last_name}" for p in persons]
            query_parts = [f"({name})" for name in person_names] # Group names for OR logic
            
            if additional_keywords:
                query = f"({' OR '.join(query_parts)}) AND ({additional_keywords})"
            else:
                query = ' OR '.join(query_parts)
        
        elif search_mode == 'advanced':
            # Placeholder for advanced search query construction
            query = request.form.get('advanced_query_content', '').strip() # Assuming a field for advanced query
        else:
            flash('Unbekannter Suchmodus.', 'error')
            return redirect(url_for('search.index'))

        if not query:
            flash('Bitte geben Sie einen Suchbegriff ein.', 'warning')
            return redirect(url_for('search.index'))
            
        if not selected_databases:
            flash('Bitte wählen Sie mindestens eine Datenbank aus.', 'warning')
            return redirect(url_for('search.index'))
        
        try:
            # Set search status
            session['search_status'] = 'searching'
            session['search_start_time'] = get_utc_now().isoformat()
            
            # Execute enhanced search
            results, search_errors, search_summary = enhanced_search_database(
                query=query,
                databases=selected_databases,
                search_mode=search_mode
            )
            
            # Create and save search query
            search_query = SearchQuery(
                search_text=query,
                database=','.join(selected_databases),
                search_mode=search_mode,
                timestamp=get_utc_now()
            )
            db.session.add(search_query)
            db.session.commit()
            
            # Save results
            saved_count = save_search_results(search_query, results)
            
            # Store search information in session
            session['current_query_id'] = search_query.id
            session['search_summary'] = search_summary
            if search_errors:
                session['search_errors'] = [{'database': db, 'error': err} for db, err in search_errors.items()]
            
            # Update search status to completed - this is important for the AJAX status check
            session['search_status'] = 'completed'
            session.pop('search_start_time', None)
            
            # Redirect to results
            if saved_count > 0:
                flash(f'{saved_count} Ergebnisse gefunden.', 'success')
                logger.info(f"Search completed with {saved_count} results for query '{query}'")
                return redirect(url_for('search.results'))
            else:
                logger.info(f"Search completed with NO results for query '{query}'")
                flash('Keine Ergebnisse gefunden.', 'info')
                # Even with no results, make sure search status is properly updated
                session['search_status'] = 'no_results'
                return redirect(url_for('search.index'))
                
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            # Critical: Update search status to error to prevent UI from being stuck
            session['search_status'] = 'error'
            session.pop('search_start_time', None)
            # Store error in session for status API to report
            session['search_error_message'] = str(e)
            flash(f'Fehler bei der Suche: {str(e)}', 'error')
            return redirect(url_for('search.index'))
    
    # GET request - show search form
    return render_template('search.html', databases=['PubMed', 'Deutsche Nationalbibliothek'])
