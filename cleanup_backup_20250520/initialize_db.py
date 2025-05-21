#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database initialization script for Medical Spytool
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database with proper error handling"""
    # Import Flask app and database
    from backend.app import app, db
    
    # Ensure instance directory exists
    instance_dir = Path(app.instance_path)
    try:
        instance_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"Instance directory ensured at: {instance_dir}")
    except Exception as e:
        logger.error(f"Failed to create instance directory: {e}")
        return False
    
    # Set database path
    db_path = instance_dir / "medicalspy.db"
    
    # Remove existing database if it exists
    if db_path.exists():
        try:
            db_path.unlink()
            logger.info("Removed existing database file")
        except Exception as e:
            logger.error(f"Failed to remove existing database: {e}")
            return False
    
    # Create new database
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database initialized and tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
