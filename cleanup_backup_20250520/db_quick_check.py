#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Database Quick Fix

This script checks and fixes common database issues.
"""

import os
import sys
import sqlite3
import shutil
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("db_quick_fix.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("DB-QuickFix")


def check_database():
    """Check if the database file exists, is accessible, and has the correct schema"""
    print("Checking database connection...")

    # Try to get database path from environment
    try:
        from dotenv import load_dotenv

        load_dotenv()
        print("Loaded environment variables from .env file")
    except ImportError:
        print("Warning: dotenv package not installed")

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set")
        return False

    print(f"Database URL: {database_url}")

    # Extract file path from database URL
    if database_url.startswith("sqlite:///"):
        db_path = database_url[10:]
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)
    else:
        print(f"ERROR: Unsupported database type: {database_url}")
        return False

    print(f"Database path: {db_path}")

    # Check if file exists
    if not os.path.exists(db_path):
        print(f"ERROR: Database file does not exist: {db_path}")

        # Check instance directory
        instance_dir = os.path.dirname(db_path)
        if os.path.exists(instance_dir):
            print(f"Directory exists: {instance_dir}")
            print(f"Contents: {os.listdir(instance_dir)}")
        else:
            print(f"Directory does not exist: {instance_dir}")
            os.makedirs(instance_dir, exist_ok=True)
            print(f"Created directory: {instance_dir}")

        return False

    # Check file permissions
    try:
        print(f"File size: {os.path.getsize(db_path)} bytes")
        print(f"File permissions: {oct(os.stat(db_path).st_mode)}")
        print(f"Current user: {os.getlogin()}")
    except Exception as e:
        print(f"Error getting file information: {e}")

    # Try to connect to the database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("Successfully connected to database")

        # Check integrity
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        print(f"Integrity check result: {result[0]}")

        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables in database: {[table[0] for table in tables]}")

        conn.close()
        print("Connection closed successfully")
        return True
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def backup_database(db_path):
    """Create a backup of the existing database"""
    if not os.path.exists(db_path):
        print("No database to backup")
        return True

    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"medicalspy_quickfix_{timestamp}.db"

    try:
        shutil.copy2(db_path, backup_path)
        print(f"Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False


def create_fresh_database(db_path):
    """Create a fresh database with the correct schema"""
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Remove existing file if it exists
    if os.path.exists(db_path):
        try:
            os.chmod(db_path, 0o666)  # Try to ensure we have write permissions
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")
        except Exception as e:
            print(f"Error removing existing database: {e}")
            return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.executescript(
            """
        -- User table
        CREATE TABLE user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Person table
        CREATE TABLE person (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            affiliation TEXT,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(id)
        );
        
        -- Search query table
        CREATE TABLE search_query (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            terms TEXT NOT NULL,
            database TEXT NOT NULL,
            filters TEXT,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(id)
        );
        
        -- Search result table
        CREATE TABLE search_result (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            authors TEXT,
            year INTEGER,
            journal TEXT,
            abstract TEXT,
            url TEXT,
            citation_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            result_data TEXT,
            FOREIGN KEY (query_id) REFERENCES search_query(id)
        );
        
        -- Setting table
        CREATE TABLE setting (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT NOT NULL,
            metadata TEXT
        );
        
        -- Log entry table
        CREATE TABLE log_entry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            source TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        )

        # Create admin user
        admin_password_hash = "pbkdf2:sha256:150000$E9Kbmeat$d110510c6f339c31cce1ec789aaea5fc3fa6e42e5c5e1e8512e367ce4e32205c"  # Hash for 'admin'
        cursor.execute(
            "INSERT INTO user (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
            ("admin", "admin@example.com", admin_password_hash, True),
        )

        # Create default settings
        default_settings = [
            ("default_database", "PubMed", '{"description": "Default database for searches"}'),
            ("max_results", "50", '{"description": "Maximum number of results per search query"}'),
            ("enable_export", "true", '{"description": "Enable export functionality"}'),
        ]

        for key, value, metadata in default_settings:
            cursor.execute(
                "INSERT INTO setting (key, value, metadata) VALUES (?, ?, ?)",
                (key, value, metadata),
            )

        # Commit and close
        conn.commit()
        conn.close()

        print(f"Created fresh database: {db_path}")
        return True
    except Exception as e:
        print(f"Error creating fresh database: {e}")
        return False


def fix_database_permissions(db_path):
    """Fix permissions on the database file"""
    if not os.path.exists(db_path):
        print(f"Database file does not exist: {db_path}")
        return False

    try:
        # Make sure the file is readable and writable
        os.chmod(db_path, 0o666)
        print(f"Fixed permissions on database file: {db_path}")

        # Make sure the directory is accessible
        dir_path = os.path.dirname(db_path)
        os.chmod(dir_path, 0o777)
        print(f"Fixed permissions on directory: {dir_path}")

        return True
    except Exception as e:
        print(f"Error fixing permissions: {e}")
        return False


def main():
    """Main function to check and fix database issues"""
    print("\n========== MEDICAL SPYTOOL - DATABASE QUICK FIX ==========\n")

    # Try to get database path from environment
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set")
        # Set a default value
        database_url = "sqlite:///instance/medicalspy.db"
        os.environ["DATABASE_URL"] = database_url
        print(f"Set default DATABASE_URL: {database_url}")

    # Extract file path from database URL
    if database_url.startswith("sqlite:///"):
        db_path = database_url[10:]
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)
    else:
        print(f"ERROR: Unsupported database type: {database_url}")
        return 1

    # Check database
    db_ok = check_database()

    if not db_ok:
        print("\nDatabase issues detected. Attempting to fix...\n")

        # Create backup
        backup_database(db_path)

        # Fix permissions
        fix_database_permissions(db_path)

        # Create fresh database
        if not create_fresh_database(db_path):
            print("ERROR: Failed to create fresh database")
            return 1

        # Check database again
        db_ok = check_database()
        if not db_ok:
            print("ERROR: Database issues persist after fix attempts")
            return 1

    print("\n========== FIX COMPLETED ==========")
    print("Result: SUCCESS")
    print("You can now run the application with one of the following commands:")
    print("1. python run_fixed.py")
    print("2. python run.py")
    print("3. activate_and_run.bat")

    return 0


if __name__ == "__main__":
    sys.exit(main())
