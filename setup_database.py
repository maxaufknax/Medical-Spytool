#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Setup Script for Medical Spytool
Ensures database exists in the correct location for the running Flask app
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Change to backend directory to match Flask app environment
os.chdir(backend_dir)

def create_database_structure():
    """Create database and basic table structure"""
    print("=== Medical Spytool Database Setup ===")
    
    # The Flask app is looking for instance/medicalspy.db relative to backend directory
    db_path = Path("instance/medicalspy.db")
    instance_dir = db_path.parent
    
    # Ensure instance directory exists
    instance_dir.mkdir(exist_ok=True)
    print(f"✅ Instance directory ensured: {instance_dir.absolute()}")
    
    # Create/verify database file
    try:
        # Create database connection
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create basic tables that Flask-SQLAlchemy expects
        print("📋 Creating basic database structure...")
        
        # Settings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS setting (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key VARCHAR(100) NOT NULL UNIQUE,
            value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Search queries table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_query (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_content TEXT NOT NULL,
            search_mode VARCHAR(20) DEFAULT 'simple',
            databases TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Search results table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_result (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_id INTEGER,
            title TEXT,
            authors TEXT,
            abstract TEXT,
            publication_date TEXT,
            database_source VARCHAR(50),
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (query_id) REFERENCES search_query (id)
        )
        ''')
        
        # Persons table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS person (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200) NOT NULL,
            affiliation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Log entries table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS log_entry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level VARCHAR(20),
            message TEXT,
            module VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Users table for authentication
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE,
            password_hash VARCHAR(255),
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Commit changes
        conn.commit()
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"✅ Database created successfully: {db_path.absolute()}")
        print(f"📊 Tables created: {', '.join(tables)}")
        
        # Insert default settings
        default_settings = [
            ('app_initialized', 'true'),
            ('default_databases', 'PubMed'),
            ('max_results_per_query', '100'),
            ('search_timeout', '30')
        ]
        
        for key, value in default_settings:
            cursor.execute('INSERT OR IGNORE INTO setting (key, value) VALUES (?, ?)', (key, value))
        
        conn.commit()
        print("✅ Default settings inserted")
        
        # Test database access
        cursor.execute('SELECT COUNT(*) FROM setting')
        setting_count = cursor.fetchone()[0]
        print(f"🔍 Database test: {setting_count} settings found")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

if __name__ == "__main__":
    success = create_database_structure()
    if success:
        print("\n🎉 Database setup completed successfully!")
        print("   The Flask application should now be able to access the database.")
    else:
        print("\n💥 Database setup failed!")
    
    sys.exit(0 if success else 1)
