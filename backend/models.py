#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Database Models
"""

import json
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app
from backend.config import get_env_setting
from sqlalchemy.types import TypeDecorator, TEXT

# Initialize SQLAlchemy without binding to an app
db = SQLAlchemy()

# JSON type for SQLite compatibility
class JSONType(TypeDecorator):
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value) if isinstance(value, str) else value


def get_utc_now():
    """Helper function to get current UTC time"""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """Model for user accounts"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    last_login = db.Column(db.DateTime, default=get_utc_now)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        """Set password hash from plain text password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Convert model to dictionary (excluding sensitive data)"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_admin": self.is_admin,
            "created_at": (
                self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
            ),
            "last_login": (
                self.last_login.strftime("%Y-%m-%d %H:%M:%S") if self.last_login else None
            ),
        }

    @classmethod
    def get_by_username(cls, username):
        """Get user by username"""
        return cls.query.filter_by(username=username).first()

    @classmethod
    def get_by_email(cls, email):
        """Get user by email"""
        return cls.query.filter_by(email=email).first()

    def set_reset_token(self, token, expiry_datetime):
        """Set password reset token and expiry"""
        self.reset_token = token
        self.reset_token_expiry = expiry_datetime

    def clear_reset_token(self):
        """Clear password reset token and expiry"""
        self.reset_token = None
        self.reset_token_expiry = None

    @classmethod
    def get_by_reset_token(cls, token):
        """Get user by reset token"""
        return cls.query.filter_by(reset_token=token).first()


class SearchQuery(db.Model):
    """Model for saved search queries"""

    __tablename__ = "search_queries"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    search_text = db.Column(db.Text, nullable=True)  # Main search query text
    database = db.Column(db.String(255), nullable=False)  # Comma-separated list of databases
    additional_terms = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    person_name = db.Column(db.String(255), nullable=True)  # For person searches
    search_mode = db.Column(db.String(50), nullable=False)  # simple, person, advanced
    created_at = db.Column(db.DateTime, default=get_utc_now, index=True)
    
    # Alias for timestamp field used in templates
    @property
    def timestamp(self):
        return self.created_at
        
    # Convenience property for databases as a list
    @property
    def databases(self):
        return json.dumps(self.database.split(','))

    # Relationship to results
    results = db.relationship(
        "SearchResult",
        backref="search_query",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "query": self.search_text,  # Keep query in the dict for backwards compatibility
            "search_text": self.search_text,
            "database": self.database,
            "additional_terms": self.additional_terms,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "person_name": self.person_name,
            "search_mode": self.search_mode,
            "saved_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


class SearchResult(db.Model):
    """Model for search results"""

    __tablename__ = "search_results"

    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey("search_queries.id"), nullable=False, index=True)
    database = db.Column(db.String(100), nullable=False, index=True)
    result_data = db.Column(JSONType, nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now, index=True)

    def validate_result_data(self):
        """Validate that the result data has all required fields"""
        required_fields = ['Title', 'Authors', 'Publication Year', 'Database']
        result_dict = self.data
        
        missing_fields = [field for field in required_fields if field not in result_dict]
        if missing_fields:
            raise ValueError(f"Missing required fields in result data: {', '.join(missing_fields)}")
        
        return True

    @property
    def data(self):
        """Get the JSON data as a dictionary"""
        data = json.loads(self.result_data) if isinstance(self.result_data, str) else self.result_data
        
        # Standardize field names
        standardized = {}
        field_map = {
            'Titel': 'Title',
            'Autoren': 'Authors',
            'Jahr': 'Publication Year',
            'Erscheinungsjahr': 'Publication Year',
            'Datenbank': 'Database'
        }
        
        for key, value in data.items():
            standardized_key = field_map.get(key, key)
            standardized[standardized_key] = value
            
        return standardized

    @data.setter
    def data(self, value):
        """Set the JSON data from a dictionary"""
        self.result_data = json.dumps(value)


class Person(db.Model):
    """Model for persons"""

    __tablename__ = "persons"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
        }


class Setting(db.Model):
    """Model for application settings"""

    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)

    @classmethod
    def get_settings_dict(cls):
        """Get all settings as a dictionary"""
        # Start with defaults from config.py
        settings = {
            "unique_filenames": get_env_setting("UNIQUE_FILENAMES", False),
            "output_columns": get_env_setting("OUTPUT_COLUMNS", []),
            # Add other defaults here
        }

        # Override with database settings
        for setting in db.session.query(cls).all():
            if setting.key in settings:
                settings[setting.key] = setting.value
            else:
                settings[setting.key] = setting.value

        return settings

    @classmethod
    def save_settings_dict(cls, settings_dict):
        """Save a dictionary of settings"""
        for key, value in settings_dict.items():
            # Handle special cases for non-string values
            if key == "unique_filenames":
                value_str = str(value).lower()
            elif key == "output_columns":
                value_str = json.dumps(value)
            else:
                value_str = str(value)

            # Update or create
            setting = db.session.query(cls).filter_by(key=key).first()
            if setting:
                setting.value = value_str
            else:
                setting = cls(key=key, value=value_str)
                db.session.add(setting)

        db.session.commit()


class LogEntry(db.Model):
    """Model for logging messages"""

    __tablename__ = "log_entries"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=get_utc_now, index=True)
    level = db.Column(db.String(20), default="INFO", index=True)
    message = db.Column(db.Text, nullable=False)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "level": self.level,
            "message": self.message,
        }

    @classmethod
    def get_logs(cls, limit=100, level=None):
        """
        Get the latest log entries with optional filtering by level

        Args:
            limit (int): Maximum number of logs to return
            level (str): Filter by log level (INFO, WARNING, ERROR)

        Returns:
            list: List of LogEntry objects
        """
        query = cls.query

        if level:
            query = query.filter_by(level=level)

        return query.order_by(cls.timestamp.desc()).limit(limit).all()

    @classmethod
    def add_log(cls, message, level="INFO"):
        """
        Add a new log entry

        Args:
            message (str): Log message
            level (str): Log level (INFO, WARNING, ERROR)

        Returns:
            LogEntry: The created log entry
        """
        log = cls(message=message, level=level)
        db.session.add(log)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise
        return log

    @classmethod
    def clear_logs(cls, older_than=None):
        """
        Clear all logs or logs older than a specific date

        Args:
            older_than (datetime): Delete logs older than this date
        """
        try:
            if older_than:
                cls.query.filter(cls.timestamp < older_than).delete()
            else:
                cls.query.delete()
            db.session.commit()
        except:
            db.session.rollback()
            raise
