#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Database Backup Script
This script creates backups of the MedicalSpy database.
"""

import os
import sys
import time
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def backup_sqlite_database(source_path, backup_dir, keep_days=30):
    """
    Create a backup of the SQLite database

    Args:
        source_path (str): Path to the SQLite database file
        backup_dir (str): Directory to store backups in
        keep_days (int): Number of days to keep backups for
    """
    # Create backup directory if it doesn't exist
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    # Get source path
    source = Path(source_path)

    if not source.exists():
        print(f"Error: Source database not found at {source}")
        return False

    # Create timestamped backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_path / f"medicalspy_backup_{timestamp}.db"

    # Copy the database file
    try:
        shutil.copy2(source, backup_file)
        print(f"Database backup created: {backup_file}")

        # Cleanup old backups
        cleanup_old_backups(backup_path, keep_days)
        return True
    except Exception as e:
        print(f"Backup failed: {e}")
        return False


def backup_postgres_database(db_url, backup_dir, keep_days=30):
    """
    Create a backup of a PostgreSQL database using pg_dump

    Args:
        db_url (str): Database URL (postgresql://user:pass@host:port/dbname)
        backup_dir (str): Directory to store backups in
        keep_days (int): Number of days to keep backups for
    """
    # Create backup directory if it doesn't exist
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)

    # Parse the database URL
    try:
        from urllib.parse import urlparse

        parsed = urlparse(db_url)
        username = parsed.username
        password = parsed.password
        hostname = parsed.hostname
        port = parsed.port or 5432
        database = parsed.path.lstrip("/")
    except Exception as e:
        print(f"Failed to parse database URL: {e}")
        return False

    # Create timestamped backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_path / f"medicalspy_backup_{timestamp}.sql"

    # Set up the pg_dump command
    env = os.environ.copy()
    env["PGPASSWORD"] = password

    # Use pg_dump to create backup
    try:
        import subprocess

        cmd = [
            "pg_dump",
            "--host",
            hostname,
            "--port",
            str(port),
            "--username",
            username,
            "--format",
            "c",
            "--file",
            str(backup_file),
            database,
        ]
        subprocess.run(cmd, check=True, env=env)
        print(f"PostgreSQL backup created: {backup_file}")

        # Cleanup old backups
        cleanup_old_backups(backup_path, keep_days)
        return True
    except Exception as e:
        print(f"PostgreSQL backup failed: {e}")
        print("Make sure pg_dump is installed and available in your PATH")
        return False


def cleanup_old_backups(backup_dir, keep_days):
    """
    Remove backups older than the specified number of days

    Args:
        backup_dir (Path): Directory containing backups
        keep_days (int): Number of days to keep backups for
    """
    if keep_days <= 0:
        print("Not cleaning up old backups (keep_days <= 0)")
        return

    now = time.time()
    max_age = keep_days * 86400  # days to seconds

    for backup_file in backup_dir.glob("medicalspy_backup_*.db"):
        file_age = now - backup_file.stat().st_mtime
        if file_age > max_age:
            try:
                backup_file.unlink()
                print(f"Removed old backup: {backup_file}")
            except Exception as e:
                print(f"Failed to remove old backup {backup_file}: {e}")

    for backup_file in backup_dir.glob("medicalspy_backup_*.sql"):
        file_age = now - backup_file.stat().st_mtime
        if file_age > max_age:
            try:
                backup_file.unlink()
                print(f"Removed old backup: {backup_file}")
            except Exception as e:
                print(f"Failed to remove old backup {backup_file}: {e}")


if __name__ == "__main__":
    # Configure argument parser
    parser = argparse.ArgumentParser(description="MedicalSpy Database Backup Tool")
    parser.add_argument("--db-url", help="Database URL (overrides environment variable)")
    parser.add_argument("--backup-dir", default="backups", help="Directory to store backups in")
    parser.add_argument(
        "--keep-days", type=int, default=30, help="Number of days to keep backups for"
    )
    args = parser.parse_args()

    # Get database URL from environment or command line
    database_url = args.db_url or os.environ.get("DATABASE_URL", "sqlite:///instance/medicalspy.db")

    print(f"Backing up database: {database_url}")

    # Determine database type and back up accordingly
    if database_url.startswith("sqlite:///"):
        # Extract the path from the SQLite connection string
        db_path = database_url.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            # Convert relative path to absolute based on project root
            db_path = os.path.join(os.path.dirname(__file__), "..", db_path)
        success = backup_sqlite_database(db_path, args.backup_dir, args.keep_days)
    elif database_url.startswith("postgresql://"):
        success = backup_postgres_database(database_url, args.backup_dir, args.keep_days)
    else:
        print(f"Unsupported database type: {database_url.split(':')[0]}")
        success = False

    # Exit with appropriate code
    sys.exit(0 if success else 1)
