#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple database creation script to test SQLite access
"""

import os
import sqlite3
from pathlib import Path

# Create instance directory
instance_dir = Path("instance")
if not instance_dir.exists():
    print(f"Creating directory: {instance_dir}")
    instance_dir.mkdir(exist_ok=True)

# Database path
db_path = instance_dir / "medicalspy.db"

# Try to create a basic database
try:
    # Connect to the database
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(str(db_path))

    # Create a cursor
    cursor = conn.cursor()

    # Create a simple test table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS test_table (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    # Insert a test row
    cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("Test Entry",))

    # Commit the changes
    conn.commit()

    # Count rows
    cursor.execute("SELECT COUNT(*) FROM test_table")
    count = cursor.fetchone()[0]

    # Close the connection
    conn.close()

    print(f"✅ Database created successfully with {count} test entries.")
    print(f"Database path: {db_path.absolute()}")

except Exception as e:
    print(f"❌ Error creating database: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Absolute path to database: {db_path.absolute()}")
