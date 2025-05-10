#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database utility tools for MedicalSpy
Use this script to initialize, reset, or manage the database.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("MedicalSpy-DB")

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("python-dotenv package not installed. Environment variables must be set manually.")

def init_database():
    """Initialize the database tables"""
    from backend.app import app, db
    
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully")
            return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

def reset_database():
    """Reset the database by dropping and recreating all tables"""
    from backend.app import app, db
    
    try:
        with app.app_context():
            logger.warning("About to drop all database tables!")
            db.drop_all()
            logger.info("All tables dropped")
            
            db.create_all()
            logger.info("Database tables recreated successfully")
            return True
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False

def check_database_connection():
    """Check if database connection is working"""
    from backend.app import app, db
    
    try:
        with app.app_context():
            # Try to execute a simple query
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
            db.session.commit()
            
            # Get table names
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            logger.info(f"Database connection successful. Tables: {', '.join(tables)}")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.error(f"Please check your DATABASE_URL environment variable.")
        return False

def add_sample_person():
    """Add a sample person to the database for testing"""
    from backend.app import app, db
    from backend.models import Person
    
    try:
        with app.app_context():
            # Create a Person instance
            sample_person = Person()
            sample_person.name = "John Doe"
            sample_person.first_name = "John"
            sample_person.last_name = "Doe"
            db.session.add(sample_person)
            db.session.commit()
            logger.info(f"Sample person added with ID: {sample_person.id}")
            return True
    except Exception as e:
        logger.error(f"Error adding sample person: {e}")
        return False

def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description='MedicalSpy Database Tools')
    parser.add_argument('--init', action='store_true', help='Initialize database tables')
    parser.add_argument('--reset', action='store_true', help='Reset database (drop and recreate all tables)')
    parser.add_argument('--check', action='store_true', help='Check database connection')
    parser.add_argument('--add-sample', action='store_true', help='Add a sample person for testing')
    
    args = parser.parse_args()
    
    if args.check or (not args.init and not args.reset and not args.add_sample):
        check_database_connection()
    
    if args.init:
        init_database()
    
    if args.reset:
        reset_database()
    
    if args.add_sample:
        add_sample_person()

if __name__ == '__main__':
    main()