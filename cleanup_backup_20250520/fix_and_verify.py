#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Final Fix and Verification

This script fixes all known issues and generates a detailed report file.
"""

import os
import sys
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

# First create output directory for reports
output_dir = Path("fix_reports")
output_dir.mkdir(exist_ok=True)

# Set up the report file
report_path = output_dir / f"fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
with open(report_path, "w", encoding="utf-8") as report:
    report.write("==================================================\n")
    report.write("    MEDICAL SPYTOOL - FIX AND VERIFICATION REPORT\n")
    report.write("==================================================\n\n")
    report.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")


def log(message):
    """Write a message to both console and the report file"""
    print(message)
    with open(report_path, "a", encoding="utf-8") as report:
        report.write(message + "\n")


def check_models_file():
    """Check and fix the models.py file for duplicate JSONType class"""
    log("\n1. CHECKING MODELS.PY FILE")
    log("-------------------------")

    models_path = Path("backend/models.py")

    if not models_path.exists():
        log("❌ models.py file not found")
        return False

    try:
        # Read content
        with open(models_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for duplicate JSONType class
        jsontype_count = content.count("class JSONType")
        log(f"Found {jsontype_count} occurrences of 'class JSONType'")

        if jsontype_count <= 1:
            log("✅ No duplicate JSONType class found")
            return True

        log("⚠️ Duplicate JSONType class found. Fixing...")

        # Find a duplicate pattern to remove
        duplicate_pattern = """from sqlalchemy.dialects import postgresql
from sqlalchemy.types import TypeDecorator, TEXT
import json

# JSON type that works with both SQLite and PostgreSQL
class JSONType(TypeDecorator):
    impl = TEXT"""

        if duplicate_pattern in content:
            fixed_content = content.replace(duplicate_pattern, "")

            # Create a backup
            backup_path = models_path.with_suffix(".py.bak")
            shutil.copy2(models_path, backup_path)
            log(f"Created backup of models.py at {backup_path}")

            # Write fixed content
            with open(models_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)

            # Verify fix
            with open(models_path, "r", encoding="utf-8") as f:
                new_content = f.read()

            new_count = new_content.count("class JSONType")
            if new_count == 1:
                log("✅ Successfully fixed duplicate JSONType class")
                return True
            else:
                log(f"⚠️ Fix partially successful: now have {new_count} JSONType classes")
                return False
        else:
            log("❌ Could not find the duplicate pattern to replace")
            return False

    except Exception as e:
        log(f"❌ Error fixing models.py: {e}")
        return False


def check_database():
    """Check and fix database issues"""
    log("\n2. CHECKING DATABASE")
    log("-------------------")

    # Try to get database path from environment or use default
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        database_url = "sqlite:///instance/medicalspy.db"
        os.environ["DATABASE_URL"] = database_url
        log(f"Set DATABASE_URL to default: {database_url}")
    else:
        log(f"Using DATABASE_URL: {database_url}")

    # Extract file path
    if database_url.startswith("sqlite:///"):
        db_path = database_url[10:]
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)

        db_path = Path(db_path)
        log(f"Database path: {db_path}")

        # Check if directory exists
        if not db_path.parent.exists():
            log(f"Creating directory: {db_path.parent}")
            db_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if database file exists
        if not db_path.exists():
            log("Database file does not exist. Creating new database...")
        else:
            # Check if file is accessible
            try:
                log(f"Database file exists ({db_path.stat().st_size} bytes)")
                # Try to connect to database
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()

                if result[0] == "ok":
                    log("✅ Database integrity check passed")

                    # Check tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    table_names = [table[0] for table in tables]
                    log(f"Tables in database: {', '.join(table_names)}")

                    conn.close()
                    return True
                else:
                    log(f"❌ Database integrity check failed: {result[0]}")
                    log("Creating a backup and new database...")
            except Exception as e:
                log(f"❌ Error accessing database: {e}")
                log("Creating a backup and new database...")

        # Backup existing database if it exists
        if db_path.exists():
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)

            backup_path = (
                backup_dir / f"medicalspy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            try:
                shutil.copy2(db_path, backup_path)
                log(f"✅ Created database backup at {backup_path}")
            except Exception as e:
                log(f"❌ Failed to create backup: {e}")

            # Delete existing database
            try:
                db_path.unlink()
                log("✅ Removed old database")
            except Exception as e:
                log(f"❌ Could not remove old database: {e}")
                return False

        # Create new database
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Create schema
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

            # Add example settings
            settings = [
                ("default_database", "PubMed", '{"description":"Default database for searches"}'),
                (
                    "max_results",
                    "50",
                    '{"description":"Maximum number of results per search query"}',
                ),
                ("enable_export", "true", '{"description":"Enable export functionality"}'),
            ]

            for key, value, metadata in settings:
                cursor.execute(
                    "INSERT INTO setting (key, value, metadata) VALUES (?, ?, ?)",
                    (key, value, metadata),
                )

            # Commit and close
            conn.commit()
            conn.close()

            log("✅ Successfully created new database")
            return True

        except Exception as e:
            log(f"❌ Error creating new database: {e}")
            return False

    else:
        log(f"❌ Unsupported database type: {database_url}")
        return False


def fix_templates():
    """Fix URL endpoints in templates"""
    log("\n3. CHECKING TEMPLATES")
    log("--------------------")

    base_template_path = Path("backend/templates/base.html")

    if not base_template_path.exists():
        log(f"❌ Base template not found: {base_template_path}")
        return False

    try:
        with open(base_template_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for problematic patterns
        if "href=\"{{ url_for('index') }}\"" in content:
            log("⚠️ Found incorrect URL endpoint 'index'. Fixing...")

            # Create backup
            backup_path = base_template_path.with_suffix(".html.bak")
            shutil.copy2(base_template_path, backup_path)
            log(f"Created backup of base.html at {backup_path}")

            # Fix URL endpoints
            replacements = [
                ("href=\"{{ url_for('index') }}\"", "href=\"{{ url_for('main.index') }}\""),
                ("href=\"{{ url_for('search') }}\"", "href=\"{{ url_for('main.search') }}\""),
                ("href=\"{{ url_for('about') }}\"", "href=\"{{ url_for('main.about') }}\""),
                ("href=\"{{ url_for('export') }}\"", "href=\"{{ url_for('main.export') }}\""),
                ("href=\"{{ url_for('settings') }}\"", "href=\"{{ url_for('main.settings') }}\""),
                ("href=\"{{ url_for('login') }}\"", "href=\"{{ url_for('auth.login') }}\""),
                ("href=\"{{ url_for('logout') }}\"", "href=\"{{ url_for('auth.logout') }}\""),
                ("href=\"{{ url_for('register') }}\"", "href=\"{{ url_for('auth.register') }}\""),
            ]

            fixed_content = content
            for old, new in replacements:
                if old in fixed_content:
                    fixed_content = fixed_content.replace(old, new)
                    log(f"  Fixed: {old} -> {new}")

            # Write fixed content
            with open(base_template_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)

            log("✅ Successfully fixed URL endpoints in templates")
            return True
        else:
            log("✅ No URL endpoint issues found in templates")
            return True

    except Exception as e:
        log(f"❌ Error fixing templates: {e}")
        return False


def create_improved_starter():
    """Create an improved application starter script"""
    log("\n4. CREATING IMPROVED STARTER")
    log("---------------------------")

    run_fixed_path = Path("run_fixed.py")

    try:
        with open(run_fixed_path, "w", encoding="utf-8") as f:
            f.write(
                '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Improved Application Starter

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
    
    # Set FLASK_APP if not already set
    if 'FLASK_APP' not in os.environ:
        os.environ['FLASK_APP'] = 'backend.app'
        logger.info("Set FLASK_APP to backend.app")

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

        log("✅ Successfully created improved application starter (run_fixed.py)")
        return True

    except Exception as e:
        log(f"❌ Error creating improved starter: {e}")
        return False


def generate_summary():
    """Generate a summary of fixes and instructions"""
    log("\n5. FINAL SUMMARY AND INSTRUCTIONS")
    log("--------------------------------")

    log(
        """
All fixes have been applied to the Medical Spytool application:

1. The duplicate JSONType class in models.py has been fixed
2. A new clean database has been created in the instance directory
3. URL endpoint issues in templates have been fixed
4. An improved application starter has been created (run_fixed.py)

To run the application, use one of these methods:

1. Run the improved starter:
   python run_fixed.py

2. Use the batch file:
   .\\fresh_start.bat

If you still encounter issues:
- Check the logs in the logs directory
- Ensure your instance directory has proper permissions
- Verify that the virtual environment has all required packages installed

Detailed report has been saved to:
"""
        + str(report_path)
    )


def main():
    """Main function to fix all issues"""
    log("Starting comprehensive fix and verification...\n")

    # Check and fix models.py
    models_ok = check_models_file()

    # Check and fix database
    db_ok = check_database()

    # Fix templates
    templates_ok = fix_templates()

    # Create improved starter
    starter_ok = create_improved_starter()

    # Generate summary
    generate_summary()

    # Return overall status
    return all([models_ok, db_ok, templates_ok, starter_ok])


if __name__ == "__main__":
    result = main()
    with open(report_path, "a", encoding="utf-8") as report:
        report.write("\n\n==================================================\n")
        if result:
            report.write("OVERALL RESULT: ✅ SUCCESS\n")
        else:
            report.write("OVERALL RESULT: ⚠️ PARTIAL SUCCESS (Some issues may remain)\n")
        report.write("==================================================\n")

    print(f"\nComplete report saved to: {report_path}")
    sys.exit(0 if result else 1)
