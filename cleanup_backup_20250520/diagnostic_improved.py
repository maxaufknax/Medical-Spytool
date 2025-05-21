#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Improved Diagnostic Tool

This script helps diagnose common issues with the Medical Spytool application.
"""

import os
import sys
import sqlite3
import logging
import platform
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("diagnostic.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("MedicalSpy-Diagnose")


def check_python_environment():
    """Check Python environment and installed packages"""
    print("\n🐍 Checking Python environment...")

    python_version = platform.python_version()
    system_info = f"{platform.system()} {platform.release()}"

    print(f"Python version: {python_version}")
    print(f"Operating system: {system_info}")

    # Check for virtual environment
    in_venv = sys.prefix != sys.base_prefix
    print(f"Using virtual environment: {'Yes' if in_venv else 'No'}")

    # Required packages
    required_packages = [
        "flask",
        "flask-sqlalchemy",
        "flask-wtf",
        "flask-login",
        "python-dotenv",
        "werkzeug",
        "itsdangerous",
        "beautifulsoup4",
    ]

    missing_packages = []

    for package in required_packages:
        package_name = package.replace("-", "_").split(".")[0]
        try:
            importlib.import_module(package_name)
            print(f"✓ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} is missing")

    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install " + " ".join(missing_packages))
        return False
    else:
        print("\n✅ All required packages are installed.")
        return True


def check_directory_structure():
    """Check if all necessary directories exist"""
    print("\n📁 Checking directory structure...")

    base_dir = Path(__file__).resolve().parent
    required_dirs = ["instance", "logs", "output", "person_lists", "backend", "tests"]
    missing_dirs = []

    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
            print(f"✗ {dir_name} directory is missing")
        else:
            print(f"✓ {dir_name} directory exists")

    if missing_dirs:
        print(f"\n⚠️ Missing directories: {', '.join(missing_dirs)}")
        print("Creating missing directories...")
        for dir_name in missing_dirs:
            dir_path = base_dir / dir_name
            dir_path.mkdir(exist_ok=True, parents=True)
            print(f"  Created {dir_name} directory")
    else:
        print("\n✅ All required directories exist.")


def check_env_file():
    """Check if .env file exists and has required variables"""
    print("\n📄 Checking .env file...")

    base_dir = Path(__file__).resolve().parent
    env_file = base_dir / ".env"

    if not env_file.exists():
        print("✗ .env file is missing")

        # Create default .env file
        print("Creating default .env file...")
        default_env = """DATABASE_URL=sqlite:///instance/medicalspy.db
FLASK_ENV=development
DEBUG=True
FLASK_APP=backend.app
SECRET_KEY=dev_secret_key_123
SESSION_SECRET=dev_secret_key_123
LOG_LEVEL=DEBUG
OUTPUT_PATH=./output
PERSON_LIST_PATH=./person_lists
DEFAULT_DATABASE=PubMed
FLASK_DEBUG=True"""

        with open(env_file, "w", encoding="utf-8") as f:
            f.write(default_env)

        print("✓ Default .env file created")
    else:
        print("✓ .env file exists")

        # Check for required variables
        required_vars = ["DATABASE_URL", "FLASK_APP", "SECRET_KEY"]
        missing_vars = []

        with open(env_file, "r", encoding="utf-8") as f:
            content = f.read()

            for var in required_vars:
                if var not in content:
                    missing_vars.append(var)

        if missing_vars:
            print(f"⚠️ Missing required variables in .env: {', '.join(missing_vars)}")
        else:
            print("✓ All required environment variables are defined")


def check_database():
    """Check database connectivity and structure"""
    print("\n🗄️ Checking database...")

    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "instance" / "medicalspy.db"

    if not db_path.exists():
        print(f"✗ Database file not found: {db_path}")
        return False

    print(f"✓ Database file exists: {db_path}")

    # Check if file is readable
    if not os.access(db_path, os.R_OK):
        print("✗ Database file is not readable (permission issue)")
        return False

    # Check database structure
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = [
            "user",
            "person",
            "search_query",
            "search_result",
            "setting",
            "log_entry",
        ]
        missing_tables = [table for table in required_tables if table not in tables]

        if missing_tables:
            print(f"✗ Missing tables: {', '.join(missing_tables)}")
            print(f"  Existing tables: {', '.join(tables)}")
            conn.close()
            return False
        else:
            print(f"✓ All required tables exist: {', '.join(required_tables)}")

        # Count entries in tables
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} entries")

        conn.close()
        print("✅ Database structure is valid")
        return True

    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        return False


def check_application_files():
    """Check if key application files exist"""
    print("\n📋 Checking application files...")

    base_dir = Path(__file__).resolve().parent
    required_files = [
        "run.py",
        "backend/app.py",
        "backend/models.py",
        "backend/connectors.py",
        "initialize_db.py",
    ]

    missing_files = []

    for file_path in required_files:
        full_path = base_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
            print(f"✗ {file_path} is missing")
        else:
            print(f"✓ {file_path} exists")

    if missing_files:
        print(f"\n⚠️ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("\n✅ All required application files exist.")
        return True


def main():
    """Main diagnostic function"""
    print("\n" + "=" * 80)
    print("{:^80}".format("MEDICAL SPYTOOL - IMPROVED DIAGNOSTIC TOOL"))
    print("=" * 80 + "\n")

    # Run all checks
    env_ok = check_python_environment()
    check_directory_structure()
    check_env_file()
    db_ok = check_database()
    files_ok = check_application_files()

    # Summary
    print("\n" + "=" * 80)
    print("{:^80}".format("DIAGNOSTIC SUMMARY"))
    print("=" * 80 + "\n")

    if env_ok and db_ok and files_ok:
        print("✅ All checks passed. The application should be ready to run.")
        print("   You can start the application with: python run.py")
        return 0
    else:
        print("⚠️ Some issues were detected. Please fix them before running the application.")

        if not env_ok:
            print("   - Install missing Python packages")
        if not db_ok:
            print("   - Fix database issues (try running: python initialize_db.py --force)")
        if not files_ok:
            print("   - Ensure all required application files are present")

        return 1


if __name__ == "__main__":
    sys.exit(main())
