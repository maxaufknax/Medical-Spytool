"""
Database management module for SciPub Explorer

This module handles database initialization, connection management,
and provides helper functions for database operations.
"""
import os
import sqlite3
import logging
import json
import datetime
import hashlib
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

# Global connection variable
_connection = None
_db_path = None

# Default database location
DEFAULT_DB_LOCATION = os.path.join(os.path.expanduser("~"), ".scipub_explorer", "scipub_explorer.db")

# Server connection information
_server_mode = False
_server_config = {
    "host": None,
    "port": None,
    "database": None,
    "user": None,
    "password": None
}

def init_db(db_path=None, server_config=None):
    """
    Initialize the database with required tables

    Args:
        db_path (str, optional): Path to the SQLite database file. If None, uses default location.
        server_config (dict, optional): PostgreSQL server configuration for multi-user mode.
            Format: {"host": str, "port": int, "database": str, "user": str, "password": str}
    """
    global _connection, _db_path, _server_mode, _server_config

    # If no path is provided, use the default
    if db_path is None:
        db_path = DEFAULT_DB_LOCATION

    _db_path = db_path

    # Check if we're in server mode
    if server_config:
        try:
            # Import required modules for PostgreSQL
            import psycopg2

            # Store server configuration
            _server_mode = True
            _server_config = server_config

            # Create a connection to the PostgreSQL database
            conn_string = f"host={server_config['host']} port={server_config['port']} dbname={server_config['database']} user={server_config['user']} password={server_config['password']}"
            _connection = psycopg2.connect(conn_string)
            logger.info(f"Connected to PostgreSQL database at {server_config['host']}:{server_config['port']}")

            # Create tables for PostgreSQL - modified syntax
            with _connection:
                cursor = _connection.cursor()

                # Users table for multi-user support
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(255) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        full_name VARCHAR(255),
                        email VARCHAR(255),
                        is_admin BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # User profiles table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        profile_name VARCHAR(255) NOT NULL,
                        default_search_settings JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)

                # API Keys table with user association
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS api_keys (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        database_name VARCHAR(255) NOT NULL,
                        api_key VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (user_id, database_name),
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)

                # Persons table for author profiles
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS persons (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        affiliation VARCHAR(255),
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)

                # Person aliases table for search aliases
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS person_aliases (
                        id SERIAL PRIMARY KEY,
                        person_id INTEGER NOT NULL,
                        alias VARCHAR(255) NOT NULL,
                        FOREIGN KEY (person_id) REFERENCES persons (id) ON DELETE CASCADE
                    )
                """)

                # Search history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS search_history (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        search_terms TEXT NOT NULL,
                        databases TEXT NOT NULL,
                        filters TEXT,
                        result_count INTEGER,
                        search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)

                # Application logs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS app_logs (
                        id SERIAL PRIMARY KEY,
                        level VARCHAR(50) NOT NULL,
                        message TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Settings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        setting_key VARCHAR(255) NOT NULL,
                        setting_value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (user_id, setting_key),
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)

                # Commit the changes
                _connection.commit()

                logger.info("PostgreSQL database tables created successfully")

        except ImportError:
            logger.error("PostgreSQL support requires the psycopg2 module. Falling back to SQLite.")
            _server_mode = False

        except Exception as e:
            logger.error(f"PostgreSQL database initialization error: {e}")
            logger.info("Falling back to SQLite database...")
            _server_mode = False

    # If not in server mode or server connection failed, use SQLite
    if not _server_mode:
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            # Create a connection to the SQLite database
            _connection = sqlite3.connect(db_path)
            logger.info(f"Connected to SQLite database at {db_path}")

            # Enable foreign keys
            _connection.execute("PRAGMA foreign_keys = ON")

            # Create tables for SQLite
            with _connection:
                cursor = _connection.cursor()

                # Users table for multi-user support
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        full_name TEXT,
                        email TEXT,
                        is_admin INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # User profiles table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        profile_name TEXT NOT NULL,
                        default_search_settings TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)

                # API Keys table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS api_keys (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        database_name TEXT NOT NULL,
                        api_key TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (user_id, database_name),
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)

                # Persons table for author profiles
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS persons (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        affiliation TEXT,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)

                # Person aliases table for search aliases
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS person_aliases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        person_id INTEGER NOT NULL,
                        alias TEXT NOT NULL,
                        FOREIGN KEY (person_id) REFERENCES persons (id) ON DELETE CASCADE
                    )
                """)

                # Search history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS search_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        search_terms TEXT NOT NULL,
                        databases TEXT NOT NULL,
                        filters TEXT,
                        result_count INTEGER,
                        search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)

                # Application logs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS app_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        level TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Settings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        setting_key TEXT NOT NULL,
                        setting_value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (user_id, setting_key),
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)

                # Create default admin user if no users exist
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]

                if user_count == 0:
                    # Create a default admin user
                    default_password_hash = hashlib.sha256("admin".encode()).hexdigest()
                    cursor.execute("""
                        INSERT INTO users (username, password_hash, full_name, is_admin)
                        VALUES (?, ?, ?, ?)
                    """, ("admin", default_password_hash, "Administrator", 1))

                    logger.info("Created default admin user (username: admin, password: admin)")

                logger.info("SQLite database tables created successfully")

                # Add new columns to existing tables if they don't exist
                cursor = _connection.cursor()

                # Add user_id column to tables that need it
                try:
                    cursor.execute("ALTER TABLE persons ADD COLUMN user_id INTEGER REFERENCES users(id)")
                except Exception as e:
                    logger.warning(f"Error adding user_id column to persons table: {e}")

                try:
                    cursor.execute("ALTER TABLE api_keys ADD COLUMN user_id INTEGER REFERENCES users(id)")
                except Exception as e:
                    logger.warning(f"Error adding user_id column to api_keys table: {e}")

                try:
                    cursor.execute("ALTER TABLE settings ADD COLUMN setting_value TEXT")
                except Exception as e:
                    logger.warning(f"Error adding setting_value column to settings table: {e}")


        except sqlite3.Error as e:
            logger.error(f"SQLite database initialization error: {e}")
            raise

@contextmanager
def get_db_connection():
    """
    Context manager for database connections

    Yields:
        Connection: Database connection (SQLite or PostgreSQL)
    """
    global _connection, _server_mode

    if _connection is None:
        raise RuntimeError("Database not initialized. Call init_db first.")

    try:
        # Return the existing connection
        yield _connection
    except Exception as e:
        if _server_mode:
            logger.error(f"PostgreSQL database operation error: {e}")
        else:
            logger.error(f"SQLite database operation error: {e}")
        raise

def get_user_by_username(username):
    """
    Get a user by username

    Args:
        username (str): The username to look up

    Returns:
        dict: User information or None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, username, password_hash, full_name, email, is_admin 
                FROM users 
                WHERE username = ?
            """, (username,))

            row = cursor.fetchone()

            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'password_hash': row[2],
                    'full_name': row[3],
                    'email': row[4],
                    'is_admin': bool(row[5]) if not _server_mode else row[5]
                }
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None

def authenticate_user(username, password):
    """
    Authenticate a user with username and password

    Args:
        username (str): The username
        password (str): The plaintext password

    Returns:
        dict: User information if authentication successful, None otherwise
    """
    user = get_user_by_username(username)

    if user:
        # Hash the provided password and compare with stored hash
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if password_hash == user['password_hash']:
            logger.info(f"User {username} authenticated successfully")
            return user

    logger.warning(f"Failed authentication attempt for user {username}")
    return None

def create_user(username, password, full_name=None, email=None, is_admin=False):
    """
    Create a new user

    Args:
        username (str): Unique username
        password (str): Password (will be hashed)
        full_name (str, optional): Full name of the user
        email (str, optional): Email address
        is_admin (bool, optional): Whether user has admin privileges

    Returns:
        int: User ID if successful, None if failed
    """
    # Hash the password
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        try:
            # Convert boolean to integer for SQLite if needed
            admin_value = is_admin
            if not _server_mode:
                admin_value = 1 if is_admin else 0

            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, email, is_admin)
                VALUES (?, ?, ?, ?, ?)
            """, (username, password_hash, full_name, email, admin_value))

            conn.commit()

            # Get the ID of the inserted user
            if _server_mode:
                cursor.execute("SELECT lastval()")
            else:
                cursor.execute("SELECT last_insert_rowid()")

            user_id = cursor.fetchone()[0]
            logger.info(f"User {username} created successfully with ID {user_id}")

            return user_id

        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating user: {e}")
            return None

def create_user_profile(user_id, profile_name, default_search_settings=None):
    """
    Create a user profile with default search settings

    Args:
        user_id (int): User ID
        profile_name (str): Name of the profile
        default_search_settings (dict, optional): Default search settings

    Returns:
        int: Profile ID if successful, None if failed
    """
    # Convert settings dict to JSON string if provided
    settings_json = None
    if default_search_settings:
        settings_json = json.dumps(default_search_settings)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO user_profiles (user_id, profile_name, default_search_settings)
                VALUES (?, ?, ?)
            """, (user_id, profile_name, settings_json))

            conn.commit()

            # Get the ID of the inserted profile
            if _server_mode:
                cursor.execute("SELECT lastval()")
            else:
                cursor.execute("SELECT last_insert_rowid()")

            profile_id = cursor.fetchone()[0]
            logger.info(f"Profile '{profile_name}' created for user {user_id}")

            return profile_id

        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating user profile: {e}")
            return None

def get_user_profiles(user_id):
    """
    Get all profiles for a user

    Args:
        user_id (int): User ID

    Returns:
        list: List of profile dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, profile_name, default_search_settings
                FROM user_profiles
                WHERE user_id = ?
            """, (user_id,))

            profiles = []
            for row in cursor.fetchall():
                # Parse the search settings JSON
                settings = None
                if row[2]:
                    try:
                        settings = json.loads(row[2])
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in default_search_settings for profile {row[0]}")

                profiles.append({
                    'id': row[0],
                    'profile_name': row[1],
                    'default_search_settings': settings
                })

            return profiles

        except Exception as e:
            logger.error(f"Error getting user profiles: {e}")
            return []

def close_db():
    """Close the database connection"""
    global _connection, _server_mode

    if _connection:
        _connection.close()
        _connection = None
        if _server_mode:
            logger.info("PostgreSQL database connection closed")
        else:
            logger.info("SQLite database connection closed")

# Add server-specific functions
def is_server_mode():
    """Check if we're in server mode (PostgreSQL)"""
    global _server_mode
    return _server_mode

def get_server_info():
    """Get server connection information"""
    global _server_config, _server_mode

    if _server_mode:
        return {
            'host': _server_config['host'],
            'port': _server_config['port'],
            'database': _server_config['database'],
            'user': _server_config['user']
        }
    else:
        return None