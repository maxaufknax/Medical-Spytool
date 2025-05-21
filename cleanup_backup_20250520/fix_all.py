#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Consolidated Solution

This script fixes the common issues with the MedicalSpy application:
1. Duplicate JSONType class in models.py
2. Database access permission issues
3. Application context problems

Usage:
    python fix_all.py
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
        logging.FileHandler("fix_all.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("FixAll")


def fix_models_file():
    """Fix duplicate JSONType class in models.py"""
    models_path = Path("backend/models.py")

    if not models_path.exists():
        logger.error(f"Models file not found: {models_path}")
        return False

    # Read the file
    try:
        with open(models_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for duplicate JSONType class
        json_type_count = content.count("class JSONType")

        if json_type_count > 1:
            logger.info(f"Found {json_type_count} JSONType class declarations. Fixing...")

            # Find the last import before the first JSONType class
            import_end = content.find("class JSONType")
            if import_end == -1:
                logger.error("Could not find JSONType class in models.py")
                return False

            # Find the end of the first JSONType class implementation
            class_start = content.find("class JSONType")
            next_class = content.find("class ", class_start + 10)

            if next_class == -1:
                # If there's no next class, find the next import
                next_import = content.find("import ", class_start + 10)
                if next_import == -1:
                    logger.error("Could not find the end of the JSONType class")
                    return False
                first_jsontype_end = next_import
            else:
                first_jsontype_end = next_class

            # Extract the first JSONType implementation
            first_jsontype = content[class_start:first_jsontype_end].strip()

            # Find all other JSONType implementations and remove them
            remaining_content = content[first_jsontype_end:]
            while "class JSONType" in remaining_content:
                next_jsontype_start = remaining_content.find("class JSONType")
                if next_jsontype_start == -1:
                    break

                next_class = remaining_content.find("class ", next_jsontype_start + 10)
                if next_class == -1:
                    next_import = remaining_content.find("import ", next_jsontype_start + 10)
                    if next_import == -1:
                        next_jsontype_end = len(remaining_content)
                    else:
                        next_jsontype_end = next_import
                else:
                    next_jsontype_end = next_class

                # Remove this JSONType implementation
                remaining_content = (
                    remaining_content[:next_jsontype_start] + remaining_content[next_jsontype_end:]
                )

            # Reconstruct the file
            fixed_content = content[:first_jsontype_end] + remaining_content

            # Write the fixed content back to the file
            with open(models_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)

            logger.info("Successfully fixed models.py file")
            return True
        else:
            logger.info("No duplicate JSONType class found in models.py")
            return True

    except Exception as e:
        logger.error(f"Error fixing models.py: {e}")
        return False


def fix_database():
    """Fix database issues"""
    # Try to load environment variables
    try:
        from dotenv import load_dotenv

        load_dotenv()
        logger.info("Environment variables loaded from .env file")
    except ImportError:
        logger.warning("dotenv package not installed, using default database path")

    # Get database path
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        database_url = "sqlite:///instance/medicalspy.db"
        os.environ["DATABASE_URL"] = database_url
        logger.info(f"Set default DATABASE_URL: {database_url}")

    # Extract file path
    if database_url.startswith("sqlite:///"):
        db_path = database_url[10:]
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)

        logger.info(f"Database path: {db_path}")

        # Create instance directory if it doesn't exist
        instance_dir = os.path.dirname(db_path)
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir, exist_ok=True)
            logger.info(f"Created instance directory: {instance_dir}")

        # Backup existing database
        if os.path.exists(db_path):
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"medicalspy_fixall_{timestamp}.db"

            try:
                shutil.copy2(db_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            except Exception as e:
                logger.error(f"Error creating backup: {e}")

            # Try to fix permissions on existing database
            try:
                os.chmod(db_path, 0o666)
                logger.info(f"Fixed permissions on database file: {db_path}")
            except Exception as e:
                logger.error(f"Error fixing permissions: {e}")

                # If we can't fix permissions, try to delete the file
                try:
                    os.remove(db_path)
                    logger.info(f"Removed existing database: {db_path}")
                except Exception as e:
                    logger.error(f"Error removing database: {e}")
                    return False

        # Create fresh database
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
                (
                    "max_results",
                    "50",
                    '{"description": "Maximum number of results per search query"}',
                ),
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

            logger.info(f"Created fresh database: {db_path}")
            return True

        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            return False

        except Exception as e:
            logger.error(f"Error creating database: {e}")
            return False

    else:
        logger.error(f"Unsupported database type: {database_url}")
        return False


def create_app_context_wrapper():
    """Create a proper application context wrapper"""
    run_fixed_path = Path("run_fixed.py")

    # Create a new fixed run script
    try:
        with open(run_fixed_path, "w", encoding="utf-8") as f:
            f.write(
                '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Improved Starter

This script starts the MedicalSpy application with proper error handling
and application context management.
"""

import os
import sys
import logging
from pathlib import Path
import webbrowser
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('run_improved.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("MedicalSpy")

def prepare_environment():
    """Prepare the execution environment"""
    # Try to load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Environment variables loaded from .env file")
    except ImportError:
        logger.warning("dotenv package not installed")
    
    # Ensure instance directory exists
    instance_dir = Path("instance")
    if not instance_dir.exists():
        logger.info(f"Creating instance directory: {instance_dir}")
        instance_dir.mkdir(parents=True, exist_ok=True)
    
    # Set DATABASE_URL if not already set
    if 'DATABASE_URL' not in os.environ:
        db_url = 'sqlite:///instance/medicalspy.db'
        os.environ['DATABASE_URL'] = db_url
        logger.info(f"Set DATABASE_URL to {db_url}")
    
    # Set FLASK_ENV if not already set
    if 'FLASK_ENV' not in os.environ:
        os.environ['FLASK_ENV'] = 'development'
        logger.info("Set FLASK_ENV to development")

def run_application(debug=True, host="127.0.0.1", port=5000):
    """Run the Flask application with proper context handling"""
    try:
        # Import Flask app
        from backend.app import create_app
        from backend.models import db
        
        logger.info("Initializing Flask application")
        app = create_app()
        
        # Initialize database within application context
        with app.app_context():
            try:
                logger.info("Establishing database connection to " + os.environ.get('DATABASE_URL', 'unknown'))
                db.create_all()
                logger.info("Database tables created successfully")
                
                # Verify database connection by making a simple query
                from backend.models import User
                try:
                    user_count = User.query.count()
                    logger.info(f"Database connection verified. Found {user_count} users.")
                except Exception as e:
                    logger.error(f"Error querying database: {e}")
            except Exception as e:
                logger.error(f"Error creating database tables: {e}")
                logger.error("Application will continue, but database operations might fail.")
        
        # Open browser (if running with GUI)
        url = f"http://{host}:{port}/"
        logger.info(f"Application URL: {url}")
        
        if sys.stdout.isatty():  # Only open browser if running in interactive mode
            try:
                webbrowser.open(url)
                logger.info("Browser opened automatically")
            except Exception as e:
                logger.error(f"Error opening browser: {e}")
        
        # Run the application
        logger.info(f"Starting Flask server on {host}:{port} (debug={debug})")
        app.run(host=host, port=port, debug=debug)
        
    except ImportError as e:
        logger.error(f"Error importing Flask application: {e}")
        logger.error("Make sure all required packages are installed")
        return False
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print(f"=== MedicalSpy Application Starter ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working directory: {os.getcwd()}")
    print("======================================")
    
    prepare_environment()
    run_application()
'''
            )
        logger.info("Created improved application starter (run_fixed.py)")
        return True

    except Exception as e:
        logger.error(f"Error creating improved starter: {e}")
        return False


def update_batch_file():
    """Update the batch file to use the improved starter"""
    batch_path = Path("activate_and_run.bat")

    if not batch_path.exists():
        logger.warning(f"Batch file not found: {batch_path}")
        return False

    try:
        with open(batch_path, "w", encoding="utf-8") as f:
            f.write(
                """@echo off
rem MedicalSpy Activation and Launch Script (UTF-8 support)
chcp 65001 > nul
echo.
echo ************************************************************
echo *                                                          *
echo *          MEDICALSPY ACTIVATION AND LAUNCHER              *
echo *                                                          *
echo ************************************************************
echo.

rem Activate virtual environment
echo Activating virtual environment...
call venv\\Scripts\\activate.bat

rem Create instance directory if it doesn't exist
if not exist instance (
    echo Creating instance directory...
    mkdir instance
)

rem Check if database exists
if not exist instance\\medicalspy.db (
    echo Database not found. Creating new database...
    python fix_all.py
) else (
    echo Database found.
)

rem Set environment variables
set DATABASE_URL=sqlite:///instance/medicalspy.db
set FLASK_ENV=development

rem Start the application
echo.
echo Starting Medical Spytool...
python run_fixed.py

pause
"""
            )
        logger.info("Updated batch file (activate_and_run.bat)")
        return True

    except Exception as e:
        logger.error(f"Error updating batch file: {e}")
        return False


def main():
    """Main function to fix all issues"""
    print("\n" + "=" * 80)
    print("{:^80}".format("MEDICAL SPYTOOL - ALL-IN-ONE FIX"))
    print("=" * 80 + "\n")

    # Fix models.py
    print("\n--- Fixing models.py ---")
    if fix_models_file():
        print("✅ models.py fixed successfully")
    else:
        print("❌ Error fixing models.py")

    # Fix database
    print("\n--- Fixing database ---")
    if fix_database():
        print("✅ Database fixed successfully")
    else:
        print("❌ Error fixing database")

    # Create application context wrapper
    print("\n--- Creating improved starter ---")
    if create_app_context_wrapper():
        print("✅ Improved application starter created")
    else:
        print("❌ Error creating improved starter")

    # Update batch file
    print("\n--- Updating batch file ---")
    if update_batch_file():
        print("✅ Batch file updated")
    else:
        print("❌ Error updating batch file")

    print("\n" + "=" * 80)
    print("{:^80}".format("FIX COMPLETED"))
    print("=" * 80 + "\n")

    print("You can now run the application using one of these methods:")
    print("1. python run_fixed.py")
    print("2. activate_and_run.bat (recommended)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
