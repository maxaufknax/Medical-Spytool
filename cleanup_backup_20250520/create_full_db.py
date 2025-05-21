#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Improved database creation script for Medical Spytool
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add the project directory to the Python path
base_dir = Path(__file__).resolve().parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

# Create instance directory
instance_dir = base_dir / "instance"
if not instance_dir.exists():
    print(f"Creating directory: {instance_dir}")
    instance_dir.mkdir(exist_ok=True, parents=True)

# Database path
db_path = instance_dir / "medicalspy.db"

# Try to create the database schema
try:
    print(f"Connecting to database: {db_path}")

    # Remove existing database file if it exists
    if db_path.exists():
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)

    # Connect to the database
    conn = sqlite3.connect(str(db_path))

    # Create a cursor
    cursor = conn.cursor()

    # Create necessary tables
    print("Creating database tables...")

    # Users table
    cursor.execute(
        """
    CREATE TABLE user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        is_admin BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    # Person table
    cursor.execute(
        """
    CREATE TABLE person (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        affiliation TEXT,
        user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES user(id)
    )
    """
    )

    # Search query table
    cursor.execute(
        """
    CREATE TABLE search_query (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        terms TEXT NOT NULL,
        database TEXT NOT NULL,
        filters TEXT,
        user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES user(id)
    )
    """
    )

    # Search result table
    cursor.execute(
        """
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
    )
    """
    )

    # Settings table
    cursor.execute(
        """
    CREATE TABLE setting (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL,
        metadata TEXT
    )
    """
    )

    # Log entry table
    cursor.execute(
        """
    CREATE TABLE log_entry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT NOT NULL,
        message TEXT NOT NULL,
        source TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    # Create admin user
    print("Creating admin user...")
    # Using a hardcoded password hash for 'admin' for simplicity
    password_hash = "pbkdf2:sha256:150000$E9Kbmeat$d110510c6f339c31cce1ec789aaea5fc3fa6e42e5c5e1e8512e367ce4e32205c"
    cursor.execute(
        "INSERT INTO user (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
        ("admin", "admin@example.com", password_hash, True),
    )

    # Add default settings
    print("Adding default settings...")
    default_settings = [
        ("default_database", "PubMed", '{"description": "Standard-Datenbank für Suchen"}'),
        ("max_results", "50", '{"description": "Maximale Anzahl von Ergebnissen pro Suchanfrage"}'),
        ("enable_export", "true", '{"description": "Export-Funktionalität aktivieren"}'),
    ]

    for key, value, metadata in default_settings:
        cursor.execute(
            "INSERT INTO setting (key, value, metadata) VALUES (?, ?, ?)", (key, value, metadata)
        )

    # Commit the changes
    conn.commit()

    # Verify tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Created {len(tables)} tables: {', '.join([t[0] for t in tables])}")

    # Close the connection
    conn.close()

    print(f"✅ Database created successfully.")
    print(f"Database path: {db_path.absolute()}")

except Exception as e:
    print(f"❌ Error creating database: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Absolute path to database: {db_path.absolute()}")

    # Try to diagnose permission issues
    try:
        parent_writable = os.access(instance_dir, os.W_OK)
        print(f"Instance directory writable: {parent_writable}")

        if db_path.exists():
            file_writable = os.access(db_path, os.W_OK)
            print(f"Database file writable: {file_writable}")

            # Try to read database
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                print(f"Database integrity: {result[0]}")
                conn.close()
            except Exception as e2:
                print(f"Could not read database: {e2}")
    except Exception as e3:
        print(f"Error diagnosing permissions: {e3}")
