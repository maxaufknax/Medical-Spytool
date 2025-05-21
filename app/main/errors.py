from flask import render_template, request, jsonify
from . import main

@main.app_errorhandler(404)
def page_not_found(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404

@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response
    return render_template('500.html'), 500

# Add custom error logging
@main.app_errorhandler(Exception)
def unhandled_exception(e):
    from flask import current_app
    current_app.logger.error('Unhandled exception: %s', e, exc_info=True)
    return internal_server_error(e)
