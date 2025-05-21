#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Search Debug Logger
This script adds enhanced logging for the search functionality.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Ensure we're in the correct directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configure logging
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'search_debug.log')
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

# Create a logger specifically for search operations
search_logger = logging.getLogger('medical_spytool.search')
search_logger.setLevel(logging.DEBUG)

def log_csrf_status():
    """Log CSRF token configuration and status"""
    from flask import current_app
    
    search_logger.info("=== CSRF Configuration Status ===")
    search_logger.info(f"WTF_CSRF_ENABLED: {current_app.config.get('WTF_CSRF_ENABLED')}")
    search_logger.info(f"WTF_CSRF_CHECK_DEFAULT: {current_app.config.get('WTF_CSRF_CHECK_DEFAULT')}")
    search_logger.info(f"WTF_CSRF_TIME_LIMIT: {current_app.config.get('WTF_CSRF_TIME_LIMIT')}")
    search_logger.info(f"WTF_CSRF_SSL_STRICT: {current_app.config.get('WTF_CSRF_SSL_STRICT')}")
    search_logger.info("================================")

def patch_search_blueprint():
    """Patch the search blueprint to add enhanced logging"""
    from flask import request, session
    from backend.blueprints.search import search_bp
    
    # Save the original route handler
    original_index = search_bp.view_functions['index']
    
    def enhanced_index(*args, **kwargs):
        """Enhanced index function with additional logging"""
        search_logger.info("=== New Search Request ===")
        search_logger.info(f"Method: {request.method}")
        
        if request.method == 'POST':
            search_logger.info("Search form submitted")
            search_logger.info(f"Form data: {list(request.form.keys())}")
            search_logger.info(f"CSRF token in form: {'csrf_token' in request.form}")
            search_logger.info(f"CSRF token in session: {'csrf_token' in session}")
            
            if 'csrf_token' in request.form:
                token_value = request.form['csrf_token']
                search_logger.info(f"CSRF token value (first 5 chars): {token_value[:5]}...")
            
            search_logger.info(f"Search mode: {request.form.get('search_mode')}")
            search_logger.info(f"Selected databases: {request.form.getlist('databases')}")
        
        # Call the original handler
        return original_index(*args, **kwargs)
    
    # Replace the route handler
    search_bp.view_functions['index'] = enhanced_index
    search_logger.info("Search blueprint patched with enhanced logging")

def init_search_debug_logger():
    """Initialize the search debug logger"""
    search_logger.info(f"Search debug logger initialized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    search_logger.info(f"Logging to {LOG_FILE}")
    
    # Patch the search blueprint when the application is available
    from flask import current_app
    with current_app.app_context():
        log_csrf_status()
        patch_search_blueprint()
    
    search_logger.info("Search debugging initialized successfully")

# This will be imported and used in the main application
