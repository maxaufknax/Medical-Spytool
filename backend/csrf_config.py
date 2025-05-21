#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - CSRF Configuration
This module handles CSRF protection configuration.
"""

import logging
from flask import request, jsonify, flash, redirect, url_for, session, current_app
from flask_wtf.csrf import CSRFError, generate_csrf

logger = logging.getLogger(__name__)

def init_csrf_protection(app, csrf):
    """
    Initialize CSRF protection for the application.
    
    Args:
        app: Flask application instance
        csrf: Flask-WTF CSRFProtect instance
    """
    # Ensure we have a strong secret key
    if not app.secret_key or len(app.secret_key) < 16:
        # Use the one from config or generate a random one
        from backend.config import SECRET_KEY
        app.secret_key = SECRET_KEY
        logger.info("Set application secret key from configuration")
    
    # Set CSRF settings with secure defaults
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
    app.config['WTF_CSRF_SSL_STRICT'] = True
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True    # Only exempt routes that are truly safe and don't need CSRF protection
    safe_endpoints = [
        'static',  # Static files
        'main.health_check',  # Health check endpoint
        'api.get_persons',  # Read-only API endpoint
        'logs.api_logs',  # Read-only logs endpoint
    ]
    
    for endpoint in safe_endpoints:
        view_func = app.view_functions.get(endpoint)
        if view_func:
            csrf.exempt(view_func)
            logger.info(f"CSRF protection exempted for {endpoint}")
        else:
            logger.warning(f"Could not find endpoint {endpoint} to exempt from CSRF")
    
    @app.before_request
    def ensure_csrf():
        """Ensure CSRF token is synchronized between session and cookie"""
        # Skip for exempt endpoints and GET/HEAD requests
        if request.endpoint in safe_endpoints or request.method in ('GET', 'HEAD', 'OPTIONS'):
            return
            
        # Ensure token exists in session
        if 'csrf_token' not in session:
            csrf_token = generate_csrf()
            session['csrf_token'] = csrf_token
            session.modified = True
            logger.debug("Generated new CSRF token for session")
        
        # For non-GET requests, validate token in headers or form
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            token = None
            
            # Check token in headers (for AJAX)
            if request.is_json:
                token = request.headers.get('X-CSRFToken')
                if not token:
                    logger.warning("Missing CSRF token in AJAX request headers")
                    return jsonify({
                        'error': 'Missing CSRF token',
                        'message': 'CSRF token must be included in X-CSRFToken header'
                    }), 400
            
            # For form submissions, the CSRFProtect extension will handle validation
            # This is just a backup check for debugging
            elif request.form and 'csrf_token' not in request.form:
                logger.warning("Form submitted without CSRF token in form data")
                # Don't return error here - let the CSRFProtect extension handle it
    
    @app.after_request
    def add_csrf_cookie(response):
        """Add or update CSRF token in cookie and headers"""
        # Skip for exempted endpoints
        if request.endpoint not in safe_endpoints:
            csrf_token = session.get('csrf_token', generate_csrf())
            
            # Set secure cookie
            response.set_cookie(
                'csrf_token',
                csrf_token,
                max_age=3600,  # 1 hour
                secure=not app.debug,  # Secure in production
                httponly=True,  # Prevent XSS access
                samesite='Strict'  # Prevent CSRF
            )            # Add CSRF token to response headers for AJAX requests
            response.headers['X-CSRF-Token'] = csrf_token
            
        return response
    
    # Note: CSRF error handling is now managed in app.py
    # We don't need a duplicate handler here
