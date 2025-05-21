#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reset Database Script - Fixed Version
Resets the database for Medical Spytool
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Set BASE_DIR to the directory containing this script
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

def reset_db():
    """Reset the database by creating a new app context and using db.create_all()"""
    # Import locally to avoid circular imports
    try:
        logging.info("Importing app components...")
        from backend.app import create_app
        from backend.models import db

        logging.info("Creating app context...")
        app = create_app()
        
        with app.app_context():
            logging.info("Dropping all tables...")
            db.drop_all()
            logging.info("Creating all tables...")
            db.create_all()
            logging.info("Database reset completed successfully!")
        
        return True
    except Exception as e:
        logging.error(f"Error resetting database: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logging.info("Starting database reset...")
    success = reset_db()
    if success:
        logging.info("Database successfully reset.")
        sys.exit(0)
    else:
        logging.error("Database reset failed.")
        sys.exit(1)
