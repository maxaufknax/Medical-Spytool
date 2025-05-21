#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Database Reset Utility
This script drops and recreates all tables in the database.
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("db_reset")

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import application context and models
try:
    from backend.app import app
    from backend.models import db
    from backend.utils import log_message
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

def reset_database():
    """Drop all tables and recreate them"""
    try:
        logger.info("Starting database reset process")
        
        with app.app_context():
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"medicalspy_{timestamp}.db"
            db_path = os.path.join(app.instance_path, "medicalspy.db")
            backup_path = os.path.join("backups", backup_name)
            
            # Ensure backup directory exists
            os.makedirs("backups", exist_ok=True)
            
            # Backup current database if it exists
            if os.path.exists(db_path):
                try:
                    import shutil
                    shutil.copy2(db_path, backup_path)
                    logger.info(f"Created database backup at: {backup_path}")
                except Exception as backup_err:
                    logger.warning(f"Failed to create backup: {backup_err}")
            
            # Drop all tables
            logger.info("Dropping all database tables")
            db.drop_all()
            
            # Create tables
            logger.info("Creating database tables")
            db.create_all()
            
            # Commit changes
            db.session.commit()
            
            logger.info("Database reset complete")
            return True
            
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False

if __name__ == "__main__":
    print("This script will reset the MedicalSpy database.")
    print("WARNING: All data will be lost!")
    
    confirm = input("Are you sure you want to continue? (y/N): ")
    
    if confirm.lower() == "y":
        if reset_database():
            print("Database has been successfully reset.")
        else:
            print("Failed to reset database. See logs for details.")
    else:
        print("Database reset canceled.")
