#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Management Script
This script provides a centralized command-line interface for managing
the MedicalSpy application, including setup, database initialization,
and running the development server.
"""

import os
import sys
import subprocess
import logging
import argparse
import platform
import webbrowser
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import random
import shutil  # Added for backup_database_command
import sqlite3  # Added for check_db_integrity_command

# Add the project root to sys.path to ensure imports work correctly
# Define BASE_DIR as the directory containing manage.py (project root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


# --- Global Configuration ---
VENV_DIR = "venv"
INSTANCE_DIR = "instance"
LOG_DIR = "logs"
OUTPUT_DIR = "output"
PERSON_LISTS_DIR = "person_lists"
DEFAULT_DB_FILENAME = "medicalspy.db"
DATABASE_URL_ENV_VAR = "DATABASE_URL"
DEFAULT_ENV_FILE_CONTENT = """FLASK_APP=backend.app:create_app()
FLASK_ENV=development
DEBUG=True
SECRET_KEY=a_very_secret_key_please_change_me
SESSION_SECRET=another_very_secret_key_please_change_me
LOG_LEVEL=INFO
OUTPUT_PATH=./output
PERSON_LIST_PATH=./person_lists
DEFAULT_DATABASE=PubMed
FLASK_DEBUG=True
# API keys for external services - replace with your own credentials
PUBMED_API_KEY=
DNB_API_KEY=
"""


# --- Logging Setup ---
def setup_logging(log_level_str="INFO", log_to_file=True, logger_name="MedicalSpyManager"):
    """Configures the logging system."""
    numeric_level = getattr(logging, log_level_str.upper(), logging.INFO)
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_to_file:
        Path(LOG_DIR).mkdir(exist_ok=True)
        log_file = Path(LOG_DIR) / f"{logger_name.lower()}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        handlers.append(file_handler)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )
    return logging.getLogger(logger_name)


logger = setup_logging()

# --- Helper Functions ---


def get_configured_db_path(ensure_parent_dir_exists=True):
    """
    Determines the SQLite database file path from the DATABASE_URL environment variable.
    Returns a Path object if a SQLite path is found, otherwise None.
    """
    logger.debug("Attempting to get configured SQLite DB path from environment variables...")

    env_file_path_check = Path(BASE_DIR) / ".env"
    if env_file_path_check.exists():
        load_dotenv(dotenv_path=env_file_path_check, override=True)
        logger.debug(f"Loaded .env file from {env_file_path_check}")
    else:
        logger.debug(".env file not found, relying on existing environment variables or defaults.")

    db_url = os.environ.get(DATABASE_URL_ENV_VAR)

    if not db_url:
        logger.warning(f"{DATABASE_URL_ENV_VAR} not found in environment.")
        default_path = Path(BASE_DIR) / INSTANCE_DIR / DEFAULT_DB_FILENAME
        logger.info(
            f"Assuming default SQLite path: {default_path} due to missing {DATABASE_URL_ENV_VAR}."
        )
        if ensure_parent_dir_exists:
            default_path.parent.mkdir(parents=True, exist_ok=True)
        return default_path

    if db_url.startswith("sqlite:///"):
        db_path_str = db_url[len("sqlite:///") :]

        if os.path.isabs(db_path_str):
            db_file_path = Path(db_path_str)
        else:
            # Resolve relative paths against BASE_DIR
            db_file_path = (Path(BASE_DIR) / db_path_str).resolve()

        if ensure_parent_dir_exists:
            db_file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Determined SQLite DB path: {db_file_path}")
        return db_file_path
    else:
        logger.info(
            f"The configured database ({db_url}) is not SQLite. Path-based operations may not apply."
        )
        return None


def get_python_executable():
    """Returns the path to the Python executable, preferring venv."""
    if platform.system() == "Windows":
        venv_python = Path(BASE_DIR) / VENV_DIR / "Scripts" / "python.exe"
    else:
        venv_python = Path(BASE_DIR) / VENV_DIR / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def get_pip_executable():
    """Returns the path to the pip executable, preferring venv."""
    if platform.system() == "Windows":
        venv_pip = Path(BASE_DIR) / VENV_DIR / "Scripts" / "pip.exe"
    else:
        venv_pip = Path(BASE_DIR) / VENV_DIR / "bin" / "pip"
    if venv_pip.exists():
        return str(venv_pip)

    # Fallback: construct pip command for current python interpreter
    current_python = get_python_executable()
    # Check if current_python itself is a venv python that might not have pip directly on PATH
    # but can call it via "-m pip"
    if VENV_DIR in current_python:  # Heuristic: if "venv" is in the python path
        return f"{current_python} -m pip"

    # If not in venv, try to find a global pip or assume it's on PATH
    # This part might need adjustment based on how global pip is typically invoked
    # For simplicity, we'll assume "pip" command works or python -m pip
    try:
        subprocess.run(
            ["pip", "--version"],
            check=True,
            capture_output=True,
            shell=platform.system() == "Windows",
        )
        return "pip"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return f"{sys.executable} -m pip"  # Default to system python's pip module


def run_command(command, check=True, shell=False, capture_output=False, text=False):
    """Executes a shell command."""
    logger.info(f"Running command: {' '.join(command) if isinstance(command, list) else command}")
    try:
        # For pip executable, if it's a string like "python -m pip", shell must be True
        if isinstance(command, str) and " -m pip" in command:
            shell = True
        result = subprocess.run(
            command,
            check=check,
            shell=shell,
            capture_output=capture_output,
            text=text,
            encoding="utf-8",
        )
        if capture_output:
            logger.debug(f"Command stdout: {result.stdout}")
            if result.stderr:
                logger.error(f"Command stderr: {result.stderr}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if capture_output:
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
        raise
    except FileNotFoundError:
        logger.error(
            f"Command not found: {command[0] if isinstance(command, list) else command.split()[0]}"
        )
        raise


def check_python_version():
    """Checks if the Python version is 3.8 or higher."""
    logger.info("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error("Python 3.8 or higher is required. Please upgrade your Python installation.")
        sys.exit(1)
    logger.info(f"Python version {version.major}.{version.minor}.{version.micro} is suitable.")
    return True


def create_directories():
    """Creates necessary application directories."""
    logger.info("Creating necessary directories...")
    # VENV_DIR is created by setup_virtualenv, no need to include here
    dirs_to_create = [INSTANCE_DIR, LOG_DIR, OUTPUT_DIR, PERSON_LISTS_DIR]
    for app_dir_name in dirs_to_create:
        app_dir_path = Path(BASE_DIR) / app_dir_name
        app_dir_path.mkdir(exist_ok=True)
        logger.info(f"Directory '{app_dir_path}' ensured.")


# --- Setup Functions ---
def setup_virtualenv():
    """Creates a virtual environment if it doesn't exist."""
    venv_path = Path(BASE_DIR) / VENV_DIR
    python_in_venv_scripts = (
        venv_path
        / ("Scripts" if platform.system() == "Windows" else "bin")
        / ("python.exe" if platform.system() == "Windows" else "python")
    )

    if not python_in_venv_scripts.exists():
        logger.info(f"Creating virtual environment in '{venv_path}'...")
        run_command([sys.executable, "-m", "venv", str(venv_path)])
        logger.info("Virtual environment created successfully.")
    else:
        logger.info(f"Virtual environment already exists at '{venv_path}'.")


def install_requirements(requirements_file_name="project_requirements.txt"):
    """Installs Python packages from a requirements file into the venv."""
    requirements_file_path = Path(BASE_DIR) / requirements_file_name
    if not requirements_file_path.exists():
        logger.error(
            f"Requirements file '{requirements_file_path}' not found. Cannot install dependencies."
        )
        logger.info("Please ensure it exists in the project root.")
        logger.info(
            "If using pyproject.toml, you might want to run 'pip install .[dev]' or similar."
        )
        return

    logger.info(f"Installing requirements from '{requirements_file_path}'...")
    pip_exec = get_pip_executable()

    cmd_list = []
    shell_needed = False
    if isinstance(pip_exec, str) and " -m pip" in pip_exec:  # e.g. "path/to/python -m pip"
        cmd_list = pip_exec.split() + ["install", "-r", str(requirements_file_path)]
        # On Windows, python.exe might need shell=True if path contains spaces and not quoted
        # However, subprocess.run with a list of args is generally safer.
    elif isinstance(pip_exec, str) and pip_exec == "pip":  # global pip
        cmd_list = [pip_exec, "install", "-r", str(requirements_file_path)]
        shell_needed = platform.system() == "Windows"  # 'pip' might be a bat file on Windows
    else:  # path to pip executable
        cmd_list = [pip_exec, "install", "-r", str(requirements_file_path)]

    run_command(cmd_list, shell=shell_needed)

    # Verify some key packages
    try:
        verify_pip_exec = get_pip_executable()
        verify_cmd_list = []
        verify_shell_needed = False
        if isinstance(verify_pip_exec, str) and " -m pip" in verify_pip_exec:
            verify_cmd_list = verify_pip_exec.split() + ["show", "flask"]
        elif isinstance(verify_pip_exec, str) and verify_pip_exec == "pip":
            verify_cmd_list = [verify_pip_exec, "show", "flask"]
            verify_shell_needed = platform.system() == "Windows"
        else:
            verify_cmd_list = [verify_pip_exec, "show", "flask"]

        run_command(verify_cmd_list, capture_output=True, shell=verify_shell_needed)
        logger.info("Flask installation verified.")
    except subprocess.CalledProcessError:
        logger.warning("Flask verification failed. Requirements might not be fully installed.")
    logger.info("Requirements installation process completed.")


def create_env_file(force_overwrite=False):
    """Creates the .env file with default settings if it doesn't exist or if forced."""
    # .env file should ideally be in BASE_DIR for Flask to pick it up automatically with python-dotenv
    env_file_path = Path(BASE_DIR) / ".env"

    if not env_file_path.exists() or force_overwrite:
        if force_overwrite and env_file_path.exists():
            logger.info(f"Force overwriting existing .env file at {env_file_path}")
        else:
            logger.info(f"Creating .env file at {env_file_path}")

        # Construct DATABASE_URL using an absolute path for the SQLite DB
        # Place the SQLite DB inside the INSTANCE_DIR within BASE_DIR
        db_file_path = Path(BASE_DIR) / INSTANCE_DIR / DEFAULT_DB_FILENAME
        # Ensure the instance directory exists before creating the .env file that might reference it
        (Path(BASE_DIR) / INSTANCE_DIR).mkdir(exist_ok=True)

        db_url = f"sqlite:///{db_file_path.as_posix()}"  # as_posix() ensures forward slashes

        env_content = DEFAULT_ENV_FILE_CONTENT + f"\n{DATABASE_URL_ENV_VAR}={db_url}\n"

        # Ensure SECRET_KEY and SESSION_SECRET are present
        # (They are in DEFAULT_ENV_FILE_CONTENT, but this is a good practice check)
        if "SECRET_KEY=" not in env_content:
            env_content += "SECRET_KEY=your_very_secret_flask_key_fallback\n"
        if "SESSION_SECRET=" not in env_content:
            env_content += "SESSION_SECRET=your_very_secret_session_key_fallback\n"

        with open(env_file_path, "w", encoding="utf-8") as f:
            f.write(env_content)
        logger.info(".env file created/updated successfully.")
    else:
        logger.info(
            f".env file at {env_file_path} already exists. Skipping creation. Use --force-env to overwrite."
        )


def initialize_database(force_recreate=False):
    """Initializes the database by creating tables. Optionally drops existing tables first."""
    logger.info("Initializing database...")

    # Ensure .env is loaded for create_app()
    env_path = Path(BASE_DIR) / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)  # Override to ensure our .env is used
        logger.info(f".env loaded from {env_path} for database initialization.")
    else:
        logger.warning(
            f".env file not found at {env_path}. Database initialization might use default app config or fail if critical env vars are missing."
        )
        logger.warning("Consider running 'python manage.py setup --env' first.")

    try:
        # Dynamically import create_app and db to ensure .env changes are reflected
        from backend.app import create_app, db
        from backend.models import Setting  # Import Setting to initialize default settings

        app = create_app()  # create_app should now use the loaded .env variables

        with app.app_context():
            # Determine DB path from app config to ensure consistency
            raw_db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
            if not raw_db_uri:
                logger.error(
                    "SQLALCHEMY_DATABASE_URI not configured in the Flask app. Cannot initialize database."
                )
                return

            logger.info(f"Database URI from app config: {raw_db_uri}")

            is_sqlite = raw_db_uri.startswith("sqlite:///")
            db_file_for_init = (
                None  # Use a different variable name to avoid conflict with outer scope variables
            )
            if is_sqlite:
                db_path_str = raw_db_uri.replace("sqlite:///", "")
                if not os.path.isabs(db_path_str):
                    # Resolve relative paths against app.instance_path or BASE_DIR
                    # Flask's instance_path is often preferred for instance-local files
                    # However, to align with get_configured_db_path, let's use BASE_DIR for consistency if not absolute
                    db_file_for_init = (Path(BASE_DIR) / db_path_str).resolve()
                else:
                    db_file_for_init = Path(db_path_str)

                db_file_for_init.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Target SQLite database file for initialization: {db_file_for_init}")

            if force_recreate and is_sqlite and db_file_for_init and db_file_for_init.exists():
                logger.info(
                    f"Force recreate: Deleting existing database file at {db_file_for_init}..."
                )
                db_file_for_init.unlink()
            elif force_recreate and not is_sqlite:
                logger.info("Force recreate: Dropping all tables for non-SQLite DB...")
                db.drop_all()  # For non-SQLite, drop tables

            logger.info("Creating database tables...")
            db.create_all()
            logger.info("Database tables created successfully.")

            # Initialize default settings in the database
            logger.info("Initializing default settings in the database...")
            default_db_settings = {
                "output_path": "./output",
                "person_list_path": "./person_lists",
                "unique_filenames": "false",  # Stored as string, converted by model
                "output_columns": '["Name", "Title", "Creator", "Publication Year", "Identifier", "URL", "Authors", "Citation Count", "Database"]',  # Stored as JSON string
                "default_database": "PubMed",
                # Add API keys as placeholders - user should fill these in .env or UI
                "pubmed_api_key": "YOUR_PUBMED_API_KEY_HERE",
                "ieee_api_key": "YOUR_IEEE_API_KEY_HERE",
                "springer_api_key": "YOUR_SPRINGER_API_KEY_HERE",
                "elsevier_api_key": "YOUR_ELSEVIER_API_KEY_HERE",
            }
            for key, value in default_db_settings.items():
                existing_setting = Setting.query.filter_by(key=key).first()
                if not existing_setting:
                    setting = Setting(key=key, value=value)
                    db.session.add(setting)
                    logger.info(f"Added default setting: {key} = {value}")
                elif existing_setting.value != value and key in [
                    "output_path",
                    "person_list_path",
                    "default_database",
                ]:  # Overwrite some non-sensitive defaults if they differ
                    logger.info(
                        f"Updating default setting: {key} from '{existing_setting.value}' to '{value}'"
                    )
                    existing_setting.value = value
            db.session.commit()
            logger.info("Default settings initialized/verified in the database.")

    except ImportError as e:
        logger.error(
            f"Failed to import Flask app or extensions: {e}. Ensure backend.app and backend.models are correct and all dependencies are installed."
        )
        logger.error("Try running 'python manage.py setup --install' first.")
    except Exception as e:
        logger.error(f"An error occurred during database initialization: {e}", exc_info=True)


def populate_test_data_command(args):
    """Populates the database with sample data for testing and demonstration."""
    logger.info("Populating database with test data...")

    env_path = Path(BASE_DIR) / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        logger.info(f".env loaded from {env_path} for populating test data.")
    else:
        logger.warning(
            f".env file not found at {env_path}. Test data population might use default app config or fail."
        )
        logger.warning("Consider running 'python manage.py setup --env' first.")
        # Optionally, exit if .env is critical, but for now, proceed.

    try:
        from backend.app import create_app, db
        from backend.models import User, Person, SearchQuery, SearchResult, Setting, LogEntry

        app = create_app()
        with app.app_context():
            logger.info("Creating sample data...")

            # Check if data already exists to avoid duplicates, or if forced
            if args.force_clear:
                logger.info(
                    "Force clear enabled: Deleting existing test-related data (Users (except admin), Persons, SearchQueries, SearchResults, LogEntries)..."
                )
                # Be careful with what you delete. This is a simple approach.
                # Keep admin user if exists, or handle its recreation.
                admin_user = User.query.filter_by(username="admin").first()

                SearchResult.query.delete()
                SearchQuery.query.delete()
                Person.query.delete()
                LogEntry.query.delete()
                # Delete non-admin users
                User.query.filter(User.username != "admin").delete()
                db.session.commit()
                logger.info("Existing test-related data cleared.")
                # Re-add admin if it was deleted and we want a default admin
                if not admin_user and not User.query.filter_by(username="admin").first():
                    admin = User(
                        username="admin",
                        email="admin@example.com",
                        name="Administrator",
                        role="admin",
                    )
                    admin.set_password("admin123")  # Standard test password
                    db.session.add(admin)
                    logger.info("Default admin user re-created as it was cleared.")

            # Sample Users
            users_data = [
                {
                    "username": "testuser1",
                    "email": "testuser1@example.com",
                    "name": "Test User One",
                    "password": "password123",
                    "role": "user",
                },
                {
                    "username": "testuser2",
                    "email": "testuser2@example.com",
                    "name": "Test User Two",
                    "password": "password456",
                    "role": "user",
                },
            ]
            created_users = []
            # Ensure admin user exists
            admin = User.query.filter_by(username="admin").first()
            if not admin:
                admin = User(
                    username="admin", email="admin@example.com", name="Administrator", role="admin"
                )
                admin.set_password("admin123")  # Standard test password
                db.session.add(admin)
                created_users.append(admin)
                logger.info("Created default admin user.")
            else:
                created_users.append(admin)  # Add existing admin to list for query association

            for u_data in users_data:
                if not User.query.filter_by(username=u_data["username"]).first():
                    user = User(
                        username=u_data["username"],
                        email=u_data["email"],
                        name=u_data["name"],
                        role=u_data["role"],
                    )
                    user.set_password(u_data["password"])
                    db.session.add(user)
                    created_users.append(user)
            db.session.commit()  # Commit users to get IDs

            # Sample Persons
            persons_data = [
                {
                    "name": "Doe, John",
                    "aliases": ["J. Doe"],
                    "metadata": {"field": "General Medicine", "country": "USA"},
                },
                {
                    "name": "Smith, Jane",
                    "aliases": ["J. Smith"],
                    "metadata": {"field": "Pediatrics", "country": "Canada"},
                },
                {
                    "name": "Garcia, Carlos",
                    "aliases": ["C. Garcia"],
                    "metadata": {"field": "Cardiology", "notes": "Leading researcher"},
                },
            ]
            created_persons = []
            for p_data in persons_data:
                if not Person.query.filter_by(name=p_data["name"]).first():  # Simple check
                    person = Person(
                        name=p_data["name"],
                        aliases=p_data["aliases"],
                        metadata=p_data["metadata"],
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                    )
                    db.session.add(person)
                    created_persons.append(person)
            db.session.commit()

            # Sample Search Queries and Results
            if created_users:  # Ensure users exist to associate queries
                for i in range(1, 4):
                    user_for_query = random.choice(created_users)
                    sq_text = f"Sample COVID-19 Research {i}"
                    if not SearchQuery.query.filter_by(
                        query_text=sq_text, user_id=user_for_query.id
                    ).first():  # Simple check
                        search_query = SearchQuery(
                            query_text=sq_text,
                            database_name="PubMed",
                            parameters={"year_from": 2020, "year_to": 2023, "max_results": 5},
                            created_at=datetime.utcnow() - timedelta(days=i * 2),
                            user_id=user_for_query.id,
                        )
                        db.session.add(search_query)
                        db.session.flush()  # Get search_query.id

                        for j in range(1, 3):
                            result = SearchResult(
                                query_id=search_query.id,
                                title=f"Study on COVID-19 Variant {i}-{j}",
                                authors=["Author X", "Author Y"],
                                year=2021 + j,
                                journal="Journal of Virology",
                                abstract=f"This is a sample abstract for study {i}-{j} on new COVID-19 variants and their impact.",
                                url=f"https://example.com/study/{i}{j}",
                                citation_count=random.randint(10, 150),
                                created_at=datetime.utcnow() - timedelta(days=i * 2, hours=j),
                                result_data={
                                    "doi": f"10.xxxx/virology.{i}{j}",
                                    "pmid": f"{30000000 + i*10 + j}",
                                },
                            )
                            db.session.add(result)
            db.session.commit()

            # Sample Log Entries
            log_levels = ["INFO", "WARNING", "DEBUG"]
            for i in range(1, 6):
                log_entry = LogEntry(
                    level=random.choice(log_levels),
                    message=f"Sample log entry number {i} for testing purposes.",
                    source="test_data_population",
                    timestamp=datetime.utcnow() - timedelta(hours=i),
                )
                db.session.add(log_entry)
            db.session.commit()

            # Default settings are handled by initialize_database, but we can add more here if needed
            # For example, a setting specific to test data
            test_setting_key = "test_data_populated_on"
            existing_test_setting = Setting.query.filter_by(key=test_setting_key).first()
            if not existing_test_setting:
                setting = Setting(
                    key=test_setting_key, value=datetime.utcnow().isoformat(), section="debug"
                )
                db.session.add(setting)
            else:
                existing_test_setting.value = datetime.utcnow().isoformat()
            db.session.commit()

            logger.info("Sample data populated successfully.")
            logger.info(f"  Users: {User.query.count()} (includes admin)")
            logger.info(f"  Persons: {Person.query.count()}")
            logger.info(f"  SearchQueries: {SearchQuery.query.count()}")
            logger.info(f"  SearchResults: {SearchResult.query.count()}")
            logger.info(f"  LogEntries: {LogEntry.query.count()}")
            logger.info(f"  Settings: {Setting.query.count()}")

    except ImportError as e:
        logger.error(
            f"Failed to import Flask app or models: {e}. Ensure backend.app and backend.models are correct and dependencies installed."
        )
        logger.error("Try running 'python manage.py setup --install'.")
    except Exception as e:
        logger.error(f"An error occurred during test data population: {e}", exc_info=True)
        db.session.rollback()


def full_setup(force_env_overwrite=False, force_db_recreate=False):
    """Runs the complete setup process."""
    logger.info("Starting full application setup...")
    if not check_python_version():
        return
    create_directories()  # Create LOG_DIR, OUTPUT_DIR etc.
    setup_virtualenv()  # Create VENV_DIR
    install_requirements()
    create_env_file(force_overwrite=force_env_overwrite)  # Creates .env in BASE_DIR
    initialize_database(force_recreate=force_db_recreate)
    logger.info("Full application setup completed successfully!")
    logger.info(f"You can now try to run the application using: python manage.py run")


# --- Run Application Functions ---
def run_dev_server(host="127.0.0.1", port=5000, debug=True, no_browser=False):
    """Run the development server"""
    logger.info("Starting development server...")
    
    from backend.app import create_app
    app = create_app()
    
    # Ensure all directories exist
    for directory in [INSTANCE_DIR, LOG_DIR, OUTPUT_DIR, PERSON_LISTS_DIR]:
        os.makedirs(directory, exist_ok=True)
    
    # Start the development server
    server_url = f"http://{host}:{port}"
    logger.info(f"Server starting on {server_url}")
    
    if not no_browser:
        webbrowser.open(server_url)
    
    app.run(host=host, port=port, debug=debug)


# --- Main CLI Parser ---
def main():
    parser = argparse.ArgumentParser(
        description="MedicalSpy Management Script",
        formatter_class=argparse.RawTextHelpFormatter,  # For better help text formatting
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # --- Setup command ---
    setup_parser = subparsers.add_parser(
        "setup", help="Manages application setup end-to-end or in parts."
    )
    setup_parser.add_argument(
        "--venv", action="store_true", help="Only create/ensure virtual environment."
    )
    setup_parser.add_argument(
        "--install",
        action="store_true",
        help="Only install/update requirements from project_requirements.txt.",
    )
    setup_parser.add_argument("--env", action="store_true", help="Only create/update .env file.")
    setup_parser.add_argument(
        "--force-env",
        dest="force_env_overwrite",
        action="store_true",
        help="Force overwrite .env file if it exists. Use with --env or --full.",
    )
    setup_parser.add_argument(
        "--db",
        action="store_true",
        help="Only initialize database (create tables and default settings).",
    )
    setup_parser.add_argument(
        "--force-db",
        dest="force_db_recreate",
        action="store_true",
        help="Force recreate database (drops existing tables/SQLite file). Use with --db or --full.",
    )
    setup_parser.add_argument(
        "--full",
        action="store_true",
        help="Run full setup: Python version check, create directories, venv, install requirements, create .env, initialize DB.\nUse --force-env and --force-db with --full to control overwriting.",
    )
    setup_parser.set_defaults(func=handle_setup_command)

    # --- Run command ---
    run_parser = subparsers.add_parser("run", help="Runs the Flask development server.")
    run_parser.add_argument(
        "--port",
        type=int,
        default=os.environ.get("FLASK_RUN_PORT", 5000),
        help="Port to run on (default: 5000 or FLASK_RUN_PORT).",
    )
    run_parser.add_argument(
        "--host",
        default=os.environ.get("FLASK_RUN_HOST", "127.0.0.1"),
        help="Host to bind to (default: 127.0.0.1 or FLASK_RUN_HOST).",
    )
    run_parser.add_argument(
        "--no-browser", action="store_true", help="Don't open browser automatically."
    )
    run_parser.add_argument(
        "--debug",
        dest="debug_mode",
        action="store_true",
        default=True,
        help="Run server in debug mode (default: True, uses FLASK_ENV=development).",
    )
    run_parser.add_argument(
        "--no-debug",
        dest="debug_mode",
        action="store_false",
        help="Run server without debug mode (uses FLASK_ENV=production).",
    )
    run_parser.set_defaults(func=handle_run_command)

    # --- DB command ---
    db_parser = subparsers.add_parser("db", help="Database operations.")
    db_subparsers = db_parser.add_subparsers(
        dest="db_command", required=True, help="DB sub-commands"
    )

    db_init_parser = db_subparsers.add_parser(
        "init", help="Initialize database (creates tables, populates default settings)."
    )
    db_init_parser.add_argument(
        "--force",
        dest="force_db_recreate",
        action="store_true",
        help="Force recreate database (drops existing tables/SQLite file).",
    )
    db_init_parser.set_defaults(
        func=lambda args_lambda: initialize_database(force_recreate=args_lambda.force_db_recreate)
    )  # Corrected args access

    db_populate_parser = db_subparsers.add_parser(
        "populate-test-data", help="Populates the database with sample data."
    )
    db_populate_parser.add_argument(
        "--force-clear",
        action="store_true",
        help="Clear existing test-related data before populating. Use with caution.",
    )
    db_populate_parser.set_defaults(func=populate_test_data_command)

    # New: DB backup command
    db_backup_parser = db_subparsers.add_parser("backup", help="Backup the SQLite database.")
    db_backup_parser.set_defaults(func=backup_database_command)

    # New: DB integrity-check command
    db_integrity_parser = db_subparsers.add_parser(
        "integrity-check", help="Check SQLite database integrity."
    )
    db_integrity_parser.set_defaults(func=check_db_integrity_command)

    args = parser.parse_args()

    # Re-initialize logger with potentially new log level from args
    global logger
    logger = setup_logging(log_level_str=args.log_level)

    args.func(args)


def handle_setup_command(args):
    if args.full:
        full_setup(
            force_env_overwrite=args.force_env_overwrite, force_db_recreate=args.force_db_recreate
        )
    else:
        # Individual setup steps
        if args.venv:
            setup_virtualenv()
        if args.install:
            # Always ensure venv is there before installing
            setup_virtualenv()
            install_requirements()
        if args.env or args.force_env_overwrite:
            # Ensure instance dir exists for .env which might define DB path inside instance
            (Path(BASE_DIR) / INSTANCE_DIR).mkdir(exist_ok=True)
            create_env_file(force_overwrite=args.force_env_overwrite)
        if args.db or args.force_db_recreate:
            # DB initialization might need .env and venv packages
            setup_virtualenv()
            install_requirements()  # Ensure SQLAlchemy etc. are available
            create_env_file()  # Ensure .env with DB_URL is available
            initialize_database(force_recreate=args.force_db_recreate)

        if not any(
            [
                args.venv,
                args.install,
                args.env,
                args.force_env_overwrite,
                args.db,
                args.force_db_recreate,
            ]
        ):
            logger.info(
                "No specific setup option chosen. Use 'python manage.py setup --help' for options."
            )
            logger.info("To run full setup: 'python manage.py setup --full'")


def handle_run_command(args):
    # Before running, ensure basic setup like .env and venv with packages might be useful
    # However, 'run' should primarily just run if the environment is assumed to be ready.
    # For a better UX, we can add quick checks or rely on errors from Flask itself.
    logger.info("Preparing to run server...")
    # Quick check for .env, guide if missing
    if not (Path(BASE_DIR) / ".env").exists():
        logger.warning(
            f".env file not found at {Path(BASE_DIR) / '.env'}. The application might not configure correctly."
        )
        logger.warning(
            "Consider running 'python manage.py setup --env' or 'python manage.py setup --full'."
        )

    # Quick check for venv, guide if missing (by checking for a common venv file)
    venv_indicator = Path(BASE_DIR) / VENV_DIR / ("pyvenv.cfg")  # Common file in venv
    if not venv_indicator.exists():
        logger.warning(
            f"Virtual environment at '{Path(BASE_DIR) / VENV_DIR}' might be missing or incomplete."
        )
        logger.warning(
            "Consider running 'python manage.py setup --venv --install' or 'python manage.py setup --full'."
        )

    run_dev_server(
        port=args.port, host=args.host, no_browser=args.no_browser, debug=args.debug_mode
    )


# --- Custom DB Commands ---
def backup_database_command(args):
    """Creates a backup of the SQLite database."""
    logger.info("Starting database backup...")

    db_path = get_configured_db_path()  # Uses the new helper
    if not db_path:
        logger.error("Could not determine SQLite database path from DATABASE_URL. Backup aborted.")
        return

    if not db_path.exists():
        logger.warning(f"Database file {db_path} not found. Nothing to back up.")
        return

    backup_dir_name = "backups"
    backup_dir_path = Path(BASE_DIR) / backup_dir_name
    backup_dir_path.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Ensure the backup file has a .db extension if the original does, or similar logic
    original_suffix = db_path.suffix if db_path.suffix else ".db"  # Default to .db if no suffix
    backup_filename = f"{db_path.stem}_{timestamp}{original_suffix}"
    backup_file_path = backup_dir_path / backup_filename

    try:
        shutil.copy2(db_path, backup_file_path)
        logger.info(f"Database backup successful: {backup_file_path}")
        print(f"Database backup created at: {backup_file_path}")
    except Exception as e:
        logger.error(f"Error creating database backup: {e}", exc_info=True)
        print(f"Error creating database backup: {e}")


def check_db_integrity_command(args):
    """Checks the integrity of the SQLite database."""
    logger.info("Checking database integrity...")

    db_path = get_configured_db_path()  # Uses the new helper
    if not db_path:
        logger.error(
            "Could not determine SQLite database path from DATABASE_URL. Integrity check aborted."
        )
        return

    if not db_path.exists():
        logger.warning(f"Database file {db_path} not found. Cannot check integrity.")
        print(f"Database file {db_path} not found.")
        return

    # Check if it's likely an SQLite file by checking the db_url again or file extension
    # get_configured_db_path already logs if it's not SQLite, but this is an extra check
    db_url_for_check = os.environ.get(DATABASE_URL_ENV_VAR)
    if not (db_url_for_check and db_url_for_check.startswith("sqlite:///")):
        logger.info(
            f"Database {db_path} (from URL: {db_url_for_check}) does not appear to be an SQLite file. Skipping PRAGMA integrity_check."
        )
        print(
            f"Integrity check is for SQLite databases. Configured DB does not seem to be SQLite: {db_url_for_check}"
        )
        return

    try:
        # Connect in read-only mode if possible, to avoid issues with locked db
        conn_str = f"file:{db_path}?mode=ro"
        logger.info(f"Connecting to {conn_str} for integrity check.")
        conn = sqlite3.connect(conn_str, uri=True)
        cursor = conn.cursor()
        logger.info(f"Running PRAGMA integrity_check on {db_path}...")
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchall()
        conn.close()

        if len(result) == 1 and result[0][0] == "ok":
            logger.info("Database integrity check: OK")
            print("Database integrity: OK")
        else:
            logger.error("Database integrity check: FAILED")
            print("Database integrity: FAILED")
            for row in result:
                logger.error(f"Integrity issue: {row[0]}")
                print(f"  Issue: {row[0]}")
    except sqlite3.OperationalError as e:
        # If read-only fails (e.g. "attempt to write a readonly database"), try read-write
        if (
            "readonly database" in str(e).lower()
            or "attempt to write a readonly database" in str(e).lower()
        ):
            logger.warning(
                f"Read-only connection failed ({e}), trying read-write mode for integrity check."
            )
            try:
                conn = sqlite3.connect(str(db_path))  # Default read-write
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                result = cursor.fetchall()
                conn.close()
                if len(result) == 1 and result[0][0] == "ok":
                    logger.info("Database integrity check (RW mode): OK")
                    print("Database integrity: OK")
                else:
                    logger.error("Database integrity check (RW mode): FAILED")
                    print("Database integrity: FAILED")
                    for row in result:
                        logger.error(f"Integrity issue: {row[0]}")
                        print(f"  Issue: {row[0]}")
            except Exception as e_rw:
                logger.error(
                    f"SQLite error during integrity check (RW mode): {e_rw}", exc_info=True
                )
                print(f"Error during integrity check (RW mode): {e_rw}")
        else:
            logger.error(f"SQLite operational error during integrity check: {e}", exc_info=True)
            print(f"Operational error during integrity check: {e}")

    except sqlite3.Error as e:  # Catch other sqlite3 errors
        logger.error(f"SQLite error during integrity check: {e}", exc_info=True)
        print(f"Error during integrity check: {e}")
    except Exception as e:  # Catch any other unexpected errors
        logger.error(f"Unexpected error during integrity check: {e}", exc_info=True)
        print(f"Unexpected error during integrity check: {e}")


if __name__ == "__main__":
    main()
