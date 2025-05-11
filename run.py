#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Run Script
This script starts the MedicalSpy web application with additional setup for development.

It provides a more comprehensive setup process than main.py, including:
- Environment variable loading
- Directory validation and creation
- Database verification
- Connector initialization
- Detailed logging configuration
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add the current directory to the path to ensure imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables must be set manually.")
    
# Configure logging
def setup_logging(log_level, log_to_file=True):
    """
    Configure the logging system.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR)
        log_to_file (bool): Whether to log to a file
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_to_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create a daily log file
        log_file = log_dir / f"medicalspy_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        handlers.append(file_handler)
        
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    return logging.getLogger("MedicalSpy")

def check_database():
    """
    Check if the database connection is properly configured.
    
    Returns:
        bool: True if database connection is working, False otherwise
    """
    logger.info("Checking database connection...")
    
    try:
        from backend.app import db
        from flask import current_app
        
        with current_app.app_context():
            # Try a simple query to check connection
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        logger.error(f"Please check your DATABASE_URL environment variable.")
        return False

def check_api_connectors(settings):
    """
    Check if API connectors are properly configured.
    
    Args:
        settings (dict): Application settings
        
    Returns:
        dict: Status of each connector
    """
    logger.info("Checking API connectors...")
    
    from backend.connectors import PubMedConnector, DNBConnector
    
    connector_status = {}
    
    # Check PubMed connector
    pubmed_key = settings.get("pubmed_api_key", "")
    pubmed = PubMedConnector(pubmed_key)
    connector_status["PubMed"] = {
        "api_key_configured": bool(pubmed_key),
        "status": "Ready" if pubmed_key else "API key missing"
    }
    
    # Check DNB connector (doesn't require API key)
    dnb = DNBConnector()
    connector_status["DNB"] = {
        "api_key_configured": True,  # DNB doesn't need an API key
        "status": "Ready"
    }
    
    return connector_status

def main():
    """
    Main function to start the application.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the MedicalSpy web application')
    parser.add_argument('--port', type=int, default=int(os.environ.get("PORT", 5000)),
                        help='Port to run the server on (default: 5000 or PORT env var)')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Host to run the server on (default: 0.0.0.0)')
    parser.add_argument('--log-level', type=str, default=os.environ.get("LOG_LEVEL", "INFO"),
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO or LOG_LEVEL env var)')
    parser.add_argument('--no-log-file', action='store_true',
                        help='Disable logging to file')
    parser.add_argument('--check-only', action='store_true',
                        help='Only check configuration without starting the server')
    args = parser.parse_args()
    
    # Set up logging
    global logger
    logger = setup_logging(args.log_level, not args.no_log_file)
    
    try:
        # Import application modules after logging is set up
        from backend.app import app
        from backend.config import ensure_directories, load_settings
        
        # Load settings
        settings = load_settings()
        logger.info("Settings loaded successfully")
        
        # Ensure required directories exist
        ensure_directories(settings)
        logger.info("Required directories verified")
        
        # Perform system checks
        db_status = check_database()
        api_status = check_api_connectors(settings)
        
        # Log startup information
        logger.info("=== MedicalSpy Web Application ===")
        logger.info(f"Database connection: {'OK' if db_status else 'FAILED'}")
        for name, status in api_status.items():
            logger.info(f"{name} connector: {status['status']}")
        
        if args.check_only:
            logger.info("Configuration check completed - exiting")
            sys.exit(0 if db_status else 1)
        
        # Check if DB connection is working before starting
        if not db_status:
            logger.error("Cannot start application due to database connection error")
            sys.exit(1)
        
        # Run the Flask application
        logger.info(f"Starting web server on {args.host}:{args.port}")
        app.run(host=args.host, port=args.port, debug=(args.log_level.upper() == 'DEBUG'))
        
    except KeyboardInterrupt:
        logger.info("Application shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
