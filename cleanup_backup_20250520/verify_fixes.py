#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Final Verification

This script verifies that all the fixes were applied successfully
and the application can run properly.
"""

import os
import sys
import logging
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("verification.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("Verification")


def check_environment():
    """Check if the environment is properly set up"""
    try:
        from dotenv import load_dotenv

        load_dotenv()
        logger.info("Environment variables loaded from .env file")
    except ImportError:
        logger.warning("dotenv package not installed")

    # Check environment variables
    env_vars = {
        "DATABASE_URL": os.environ.get("DATABASE_URL", "Not set"),
        "FLASK_ENV": os.environ.get("FLASK_ENV", "Not set"),
        "FLASK_APP": os.environ.get("FLASK_APP", "Not set"),
        "SECRET_KEY": os.environ.get("SECRET_KEY", "Not set"),
    }

    for var, value in env_vars.items():
        logger.info(f"Environment variable {var}: {value}")

    return True


def check_models_file():
    """Check if the models.py file has been fixed"""
    models_path = Path("backend/models.py")

    if not models_path.exists():
        logger.error(f"Models file not found: {models_path}")
        return False

    try:
        with open(models_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for duplicate JSONType class
        json_type_count = content.count("class JSONType")

        if json_type_count > 1:
            logger.error(f"Found {json_type_count} JSONType class declarations in models.py")
            return False
        else:
            logger.info("models.py has been fixed (no duplicate JSONType class)")
            return True

    except Exception as e:
        logger.error(f"Error checking models.py: {e}")
        return False


def check_database():
    """Check if the database is accessible and has the correct structure"""
    # Get database path
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable is not set")
        return False

    logger.info(f"Database URL: {database_url}")

    # Extract file path
    if database_url.startswith("sqlite:///"):
        db_path = database_url[10:]
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)

        logger.info(f"Database path: {db_path}")

        # Check if file exists
        if not os.path.exists(db_path):
            logger.error(f"Database file does not exist: {db_path}")
            return False

        # Check file permissions
        try:
            logger.info(f"File size: {os.path.getsize(db_path)} bytes")
            logger.info(f"File permissions: {oct(os.stat(db_path).st_mode)}")
        except Exception as e:
            logger.error(f"Error getting file information: {e}")

        # Try to connect to the database
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            logger.info("Successfully connected to database")

            # Check integrity
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            logger.info(f"Integrity check result: {result[0]}")

            # List tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            logger.info(f"Tables in database: {table_names}")

            # Check required tables
            required_tables = [
                "user",
                "person",
                "search_query",
                "search_result",
                "setting",
                "log_entry",
            ]
            missing_tables = [table for table in required_tables if table not in table_names]

            if missing_tables:
                logger.error(f"Missing required tables: {missing_tables}")
                return False

            # Check user table
            cursor.execute("SELECT COUNT(*) FROM user")
            user_count = cursor.fetchone()[0]
            logger.info(f"User count: {user_count}")

            conn.close()
            logger.info("Database check completed successfully")
            return True

        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False

    else:
        logger.error(f"Unsupported database type: {database_url}")
        return False


def check_flask_app():
    """Check if the Flask application can be created and initialized"""
    try:
        # Import Flask app
        from backend.app import create_app
        from backend.models import db

        logger.info("Successfully imported Flask application")

        # Create app
        app = create_app()
        logger.info("Successfully created Flask application")

        # Test application context
        with app.app_context():
            logger.info("Successfully created application context")

            try:
                # Test database connection within context
                from backend.models import User

                user_count = User.query.count()
                logger.info(f"Successfully queried database. User count: {user_count}")
                return True

            except Exception as e:
                logger.error(f"Error querying database: {e}")
                return False

    except ImportError as e:
        logger.error(f"Error importing Flask application: {e}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


def main():
    """Main function to verify all fixes"""
    print("\n" + "=" * 80)
    print("{:^80}".format("MEDICAL SPYTOOL - VERIFICATION"))
    print("=" * 80 + "\n")

    checks = [
        ("Environment", check_environment),
        ("Models File", check_models_file),
        ("Database", check_database),
        ("Flask Application", check_flask_app),
    ]

    all_passed = True

    for name, check_func in checks:
        print(f"\nVerifying: {name}")
        try:
            if check_func():
                print(f"✅ {name} check PASSED")
            else:
                print(f"❌ {name} check FAILED")
                all_passed = False
        except Exception as e:
            print(f"❌ {name} check ERROR: {e}")
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("{:^80}".format("VERIFICATION COMPLETED: ALL CHECKS PASSED"))
        print("{:^80}".format("The application should now run correctly!"))
    else:
        print("{:^80}".format("VERIFICATION COMPLETED: SOME CHECKS FAILED"))
        print("{:^80}".format("Please run fix_all.py again to resolve remaining issues"))
    print("=" * 80 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
