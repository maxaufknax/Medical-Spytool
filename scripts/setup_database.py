#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Database Setup and Check
This script handles database initialization and verification
"""

import os
import sys
import logging
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DB-Setup")


def ensure_env_file_with_sqlite():
    """Ensure .env file exists with SQLite configuration"""
    env_file_path = Path(".env")

    if env_file_path.exists():
        # Read current content
        with open(env_file_path, "r", encoding="utf-8") as f:
            content = f.readlines()

        # Check if DATABASE_URL is set correctly
        db_url_set = False
        new_content = []
        for line in content:
            if line.strip().startswith("DATABASE_URL="):
                if "sqlite:///instance/medicalspy.db" not in line:
                    new_content.append("DATABASE_URL=sqlite:///instance/medicalspy.db\n")
                    db_url_set = True
                else:
                    new_content.append(line)
                    db_url_set = True
            else:
                new_content.append(line)

        # Add DATABASE_URL if not found
        if not db_url_set:
            new_content.append("DATABASE_URL=sqlite:///instance/medicalspy.db\n")

        # Write updated content
        with open(env_file_path, "w", encoding="utf-8") as f:
            f.writelines(new_content)

        logger.info(f"Updated .env file with SQLite database configuration")
    else:
        # Create new .env file
        with open(env_file_path, "w", encoding="utf-8") as f:
            f.write("# MedicalSpy Environment Variables\n")
            f.write("DATABASE_URL=sqlite:///instance/medicalspy.db\n")
            f.write("PORT=5000\n")
            f.write("HOST=127.0.0.1\n")
            f.write("SESSION_SECRET=dev_secret_key\n")
            f.write("LOG_LEVEL=DEBUG\n")
            f.write("LOG_TO_FILE=TRUE\n")

        logger.info(f"Created new .env file with SQLite database configuration")


def check_and_create_db():
    """Check if the database exists and create it if not"""
    # Ensure instance directory exists
    instance_dir = Path("instance")
    instance_dir.mkdir(exist_ok=True)

    db_path = instance_dir / "medicalspy.db"

    # Check if database already exists
    if db_path.exists():
        try:
            # Try to connect to the database to verify it's valid
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check if we can query the sqlite_master table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            if tables:
                logger.info(f"Database exists and contains {len(tables)} tables")
                conn.close()
                return True
            else:
                logger.warning(f"Database exists but contains no tables")
                conn.close()
        except sqlite3.Error as e:
            logger.warning(f"Error connecting to existing database: {e}")
            logger.info(f"Will attempt to recreate the database")

            # Rename the old database file as backup
            backup_path = db_path.with_name(f"{db_path.name}.bak")
            try:
                db_path.rename(backup_path)
                logger.info(f"Created backup of existing database at {backup_path}")
            except:
                logger.warning(f"Could not create backup of existing database")

    # Create a new database file
    try:
        conn = sqlite3.connect(db_path)
        logger.info(f"Created new database file at {db_path}")
        conn.close()
        return True
    except sqlite3.Error as e:
        logger.error(f"Failed to create database file: {e}")
        return False


def initialize_db():
    """Initialize the database tables"""
    # Set DATABASE_URL environment variable for this script
    os.environ["DATABASE_URL"] = "sqlite:///instance/medicalspy.db"

    try:
        # Import models and initialize the database
        from backend.models import db
        from flask import Flask

        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)

        with app.app_context():
            db.create_all()

        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


def main():
    """Main function"""
    print("=== Medical Spytool Database Setup ===")

    print("\nStep 1: Checking .env file")
    ensure_env_file_with_sqlite()

    print("\nStep 2: Checking database file")
    if not check_and_create_db():
        print("Failed to create database file. Check permissions on the instance directory.")
        return 1

    print("\nStep 3: Initializing database tables")
    if not initialize_db():
        print("Failed to initialize database tables. Check the error messages above.")
        return 1

    print("\n✅ Database setup complete! You can now run the application.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
