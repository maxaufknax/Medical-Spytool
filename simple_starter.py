#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Medical Spytool Starter
This script starts the Medical Spytool application and prints the URL.
"""

import os
import sys
import logging
import webbrowser
from pathlib import Path

# Set BASE_DIR to the directory containing this script
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def main():
    """Main function to start the application"""
    try:
        logging.info("Starting Medical Spytool application...")

        # Ensure required directories exist
        for directory in ['instance', 'logs', 'output', 'person_lists']:
            os.makedirs(os.path.join(BASE_DIR, directory), exist_ok=True)
            logging.info(f"Directory {directory} is ready.")

        # Import Flask application
        logging.info("Creating Flask application...")
        from backend.app import create_app
        app = create_app()
          # Define URL and port
        host = '127.0.0.1'
        port = 5000
        url = f"http://{host}:{port}"
        
        # Print URL for Simple Browser
        print(f"BROWSER_URL:{url}")
        logging.info(f"Application will be available at {url}")
        
        # Open browser automatically
        try:
            webbrowser.open(url)
            logging.info(f"Opening browser at {url}")
        except Exception as browser_err:
            logging.warning(f"Could not open browser: {browser_err}")
        
        # Start Flask development server
        logging.info("Starting Flask server...")
        app.run(host=host, port=port, debug=False)
        
    except Exception as e:
        logging.error(f"Error starting application: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
