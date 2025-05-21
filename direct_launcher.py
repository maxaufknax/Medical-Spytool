"""
Medical Spytool Direct Launcher
"""

import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
PERSON_LISTS_DIR = os.path.join(BASE_DIR, 'person_lists')

def ensure_directories():
    """Ensure required directories exist"""
    for directory in [INSTANCE_DIR, LOG_DIR, OUTPUT_DIR, PERSON_LISTS_DIR]:
        os.makedirs(directory, exist_ok=True)

def main():
    """Main function"""
    logging.info("Starting Medical Spytool directly...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Fix utils.py if it still has issues
    try:
        from backend.app import create_app
        app = create_app()
        
        # The URL to open in Simple Browser
        url = "http://127.0.0.1:5000"
        logging.info(f"Server will be available at: {url}")
        
        # Start the Flask application
        app.run(host='127.0.0.1', port=5000, debug=True)
        
        return url
    except Exception as e:
        logging.error(f"Error starting the application: {str(e)}")
        return None

if __name__ == "__main__":
    main()
