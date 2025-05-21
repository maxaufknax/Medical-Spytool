#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Health Check Script
This script checks the health status of the MedicalSpy application.
"""

import os
import sys
import time
import argparse
import logging
import requests
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("health_check")


def check_database_connection():
    """Check if the database is accessible"""
    try:
        # Import models
        from backend.models import db, User

        # Try to query the database
        result = User.query.first()
        return True, "Database connection successful"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"


def check_web_server(url="http://localhost:5000", max_retries=5, retry_delay=2):
    """
    Check if the web server is responding

    Args:
        url (str): URL to check
        max_retries (int): Maximum number of retries
        retry_delay (int): Delay between retries in seconds

    Returns:
        tuple: (success, message)
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                return True, f"Web server is responding at {url}"
            else:
                logger.warning(f"Web server responded with status code {response.status_code}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    return False, f"Web server returned status code {response.status_code}"
        except requests.exceptions.ConnectionError:
            logger.warning("Connection error when connecting to web server")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                return False, "Could not connect to web server"
        except requests.exceptions.Timeout:
            logger.warning("Timeout when connecting to web server")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                return False, "Web server connection timed out"
        except Exception as e:
            return False, f"Error connecting to web server: {str(e)}"

    return False, "Web server check failed after retries"


def check_file_permissions():
    """Check if key directories are writable"""
    directories = ["logs", "output", "person_lists", "instance"]

    results = []
    all_success = True

    for directory in directories:
        dir_path = Path(directory)

        # Check if directory exists
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True)
                results.append(f"Created directory {directory}")
            except Exception as e:
                all_success = False
                results.append(f"Error creating directory {directory}: {str(e)}")
                continue

        # Check if directory is writable
        try:
            test_file = dir_path / ".write_test"
            with open(test_file, "w") as f:
                f.write("test")
            test_file.unlink()
            results.append(f"Directory {directory} is writable")
        except Exception as e:
            all_success = False
            results.append(f"Directory {directory} is not writable: {str(e)}")

    return all_success, "\n".join(results)


def run_health_check(
    check_web=True, check_db=True, check_files=True, server_url="http://localhost:5000"
):
    """
    Run all health checks

    Args:
        check_web (bool): Whether to check web server
        check_db (bool): Whether to check database
        check_files (bool): Whether to check file permissions
        server_url (str): URL of the web server

    Returns:
        bool: True if all checks pass, False otherwise
    """
    all_checks_pass = True

    print("=" * 50)
    print("Medical Spytool Health Check")
    print("=" * 50)

    # Check web server
    if check_web:
        print("\nChecking web server...")
        success, message = check_web_server(server_url)
        all_checks_pass = all_checks_pass and success
        print(f"{'✓' if success else '✗'} {message}")

    # Check database
    if check_db:
        print("\nChecking database connection...")
        success, message = check_database_connection()
        all_checks_pass = all_checks_pass and success
        print(f"{'✓' if success else '✗'} {message}")

    # Check file permissions
    if check_files:
        print("\nChecking file permissions...")
        success, message = check_file_permissions()
        all_checks_pass = all_checks_pass and success
        print(f"{'✓' if success else '✗'} {message}")

    # Summary
    print("\n" + "=" * 50)
    if all_checks_pass:
        print("✓ All health checks passed!")
    else:
        print("✗ Some health checks failed.")
    print("=" * 50)

    return all_checks_pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MedicalSpy Health Check Tool")
    parser.add_argument("--no-web", action="store_true", help="Skip web server check")
    parser.add_argument("--no-db", action="store_true", help="Skip database check")
    parser.add_argument("--no-files", action="store_true", help="Skip file permission check")
    parser.add_argument("--url", default="http://localhost:5000", help="Web server URL to check")

    args = parser.parse_args()

    success = run_health_check(
        check_web=not args.no_web,
        check_db=not args.no_db,
        check_files=not args.no_files,
        server_url=args.url,
    )

    # Exit with appropriate code
    sys.exit(0 if success else 1)
