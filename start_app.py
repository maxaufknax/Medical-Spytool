#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medical Spytool Starter Script
This script starts the Medical Spytool application with proper configuration.
"""

import os
import sys
import webbrowser
import logging
from pathlib import Path

# Add the project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "logs", "app.log")),
        logging.StreamHandler(sys.stdout)
    ]
)

from backend.app import create_app

def run_app():
    """Run the Medical Spytool Flask application"""
    print("Starting Medical Spytool application...")
    
    # Ensure required directories exist
    for directory in ['instance', 'logs', 'output', 'person_lists']:
        os.makedirs(os.path.join(BASE_DIR, directory), exist_ok=True)
    
    # Create and configure the app
    app = create_app()
    
    host = '127.0.0.1'
    port = 5000
    
    # Register an after_request handler to debug response headers
    @app.after_request
    def debug_headers(response):
        # Log headers for debugging
        logging.debug(f"Response headers: {dict(response.headers)}")
        return response
    
    # Initialize search debug logger when app is available
    with app.app_context():
        try:
            from backend.search_debug import init_search_debug_logger
            init_search_debug_logger()
            logging.info("Search debug logger initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing search debug logger: {e}")
    
    # Open browser with the application URL
    url = f"http://{host}:{port}"
    print(f"Opening browser at: {url}")
    webbrowser.open(url)
    
    # Start the Flask development server
    print("Medical Spytool is running. Press Ctrl+C to stop.")
    app.run(host=host, port=port, debug=True)

if __name__ == "__main__":
    run_app()
