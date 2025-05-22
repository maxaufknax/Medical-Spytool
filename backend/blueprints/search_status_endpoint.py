@search_bp.route("/status", methods=["GET"])
def check_search_status():
    """
    AJAX endpoint to check the current search status
    Returns JSON with search status information
    """
    search_status = session.get('search_status', 'idle')
    start_time_str = session.get('search_start_time')
    
    response_data = {
        'status': search_status,
        'message': 'Suche läuft...' if search_status == 'searching' else 'Bereit'
    }
    
    # Add specific messages based on status
    if search_status == 'completed':
        response_data['message'] = 'Suche abgeschlossen.'
    elif search_status == 'no_results':
        response_data['message'] = 'Keine Ergebnisse gefunden.'
    elif search_status == 'error':
        error_msg = session.get('search_error_message', 'Unbekannter Fehler')
        response_data['message'] = f'Fehler: {error_msg}'
        response_data['error'] = error_msg
    
    # Check if search has been running too long
    if start_time_str and search_status == 'searching':
        try:
            start_time = datetime.fromisoformat(start_time_str)
            current_time = get_utc_now()
            duration = (current_time - start_time).total_seconds()
            
            # Add duration to response
            response_data['duration'] = round(duration)
            
            # If search has been running for more than 45 seconds, consider it stuck
            if duration > 45:
                logger.warning(f"Search appears to be stuck, running for {duration:.2f}s")
                response_data['status'] = 'timeout'
                response_data['message'] = 'Suche dauert länger als erwartet'
                # Reset the search status to allow new searches
                session['search_status'] = 'timeout'
                session.pop('search_start_time', None)
        except Exception as e:
            logger.error(f"Error calculating search duration: {str(e)}")
    
    # Check if we have errors saved from a search attempt
    errors = session.get('search_errors', [])
    if errors:
        response_data['errors'] = errors
    
    # Check if we have a search summary to return
    summary = session.get('search_summary', {})
    if summary:
        response_data['summary'] = summary
    
    return jsonify(response_data)
