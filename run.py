#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Run Script
This script starts the MedicalSpy web application.
"""

import os
import sys
import logging
from backend.app import app
from backend.config import ensure_directories, load_settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("medicalspy.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("MedicalSpy")

def main():
    """
    Main function to start the application.
    """
    try:
        # Load settings
        settings = load_settings()
        
        # Ensure required directories exist
        ensure_directories(settings)
        
        # Log startup information
        logger.info("Starting MedicalSpy Web Application")
        
        # Determine port (use 5000 by default, but allow override through PORT env var)
        port = int(os.environ.get("PORT", 5000))
        
        # Run the Flask application
        app.run(host='0.0.0.0', port=port, debug=True)
        
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
