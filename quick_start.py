#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medical Spytool Quick Start
This script provides a simple way to start the application for testing.
"""

import os
import sys
import logging
import webbrowser
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Add the project directory to the path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Ensure required directories exist
for directory in ['instance', 'logs', 'output', 'person_lists']:
    os.makedirs(os.path.join(BASE_DIR, directory), exist_ok=True)
    logging.info(f"Directory {directory} is ready")

# Import the Flask application
try:
    from backend.app import create_app

    # Create and configure the app
    app = create_app()
    
    # Configure the app to run with simplified settings
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    app.config['SERVER_NAME'] = None
    
    # Define the URL
    host = '127.0.0.1'
    port = 5000
    url = f"http://{host}:{port}"
    
    # Print information
    print(f"\n{'='*50}")
    print("Medical Spytool Quick Start")
    print(f"{'='*50}")
    print(f"\nApplication will be available at: {url}")
    print("\nPress Ctrl+C to stop the server")
    print(f"\n{'='*50}\n")
    
    # Open the browser
    webbrowser.open(url)
    
    # Run the application
    app.run(host=host, port=port, threaded=True)

except Exception as e:
    logging.error(f"Error starting application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
