#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Fix models.py
This script fixes the duplicate JSONType class in models.py
"""

import os
import sys
from pathlib import Path


def fix_duplicate_jsontype():
    models_path = Path("backend/models.py")

    if not models_path.exists():
        print(f"Error: {models_path} not found")
        return False

    try:
        with open(models_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Count JSONType class declarations
        jsontype_count = content.count("class JSONType")
        print(f"Found {jsontype_count} JSONType class declarations")

        if jsontype_count <= 1:
            print("No duplicate JSONType class found. Nothing to fix.")
            return True

        # Find the duplicate declaration pattern
        duplicate_pattern = """from sqlalchemy.dialects import postgresql
from sqlalchemy.types import TypeDecorator, TEXT
import json

# JSON type that works with both SQLite and PostgreSQL
class JSONType(TypeDecorator):
    impl = TEXT"""

        if duplicate_pattern in content:
            fixed_content = content.replace(duplicate_pattern, "")

            with open(models_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)

            print("Successfully removed duplicate JSONType class")
            return True
        else:
            print("Could not find the exact duplicate pattern. Manual inspection needed.")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    print("\n=== MedicalSpy Model Fixer ===\n")

    success = fix_duplicate_jsontype()

    if success:
        print("\n✅ Fix completed successfully")
    else:
        print("\n❌ Fix failed")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from sqlalchemy.dialects import postgresql
from sqlalchemy.types import TypeDecorator, TEXT


# JSON type that works with both SQLite and PostgreSQL
class JSONType(TypeDecorator):
    impl = TEXT

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSON

            return dialect.type_descriptor(JSON())
        else:
            return dialect.type_descriptor(self.impl)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, str):
            return json.loads(value)
        return value


# Initialize SQLAlchemy
db = SQLAlchemy()


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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
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
    name = db.Column(db.String(255), nullable=False, index=True)
    query = db.Column(db.Text)
    database = db.Column(db.String(255), index=True)
    additional_terms = db.Column(db.Text)
    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))
    person_name = db.Column(db.String(255), index=True)
    search_mode = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    results = db.relationship("SearchResult", backref="query", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "query": self.query,
            "database": self.database,
            "additional_terms": self.additional_terms,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "person_name": self.person_name,
            "search_mode": self.search_mode,
            "saved_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


class SearchResult(db.Model):
    """Model for search results"""

    __tablename__ = "search_results"

    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey("search_queries.id"), nullable=False, index=True)
    database = db.Column(db.String(100), nullable=False, index=True)
    result_data = db.Column(
        JSONType, nullable=False
    )  # Store as JSON - works with SQLite and PostgreSQL
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        """Convert model to dictionary"""
        result_data = (
            json.loads(self.result_data) if isinstance(self.result_data, str) else self.result_data
        )

        # Process the result data to standardize field names to English
        standardized_data = {}

        # Map of German field names to English equivalents
        field_name_map = {
            "Titel": "Title",
            "Autoren": "Authors",
            "Erscheinungsjahr": "Publication Year",
            "Veröffentlichungsjahr": "Publication Year",
            "Creator": "Creator",
            "Name": "Name",
            "Identifier": "Identifier",
            "URL": "URL",
            "Zitationsanzahl": "Citation Count",
            "Datenbank": "Database",
        }

        # Transfer result data with standardized field names
        for key, value in result_data.items():
            # Use English name if mapping exists, otherwise keep original
            english_key = field_name_map.get(key, key)
            standardized_data[english_key] = value

        return {
            "id": self.id,
            "query_id": self.query_id,
            "database": self.database,
            **standardized_data,
            "saved_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

    @property
    def data(self):
        """Get the JSON data as a dictionary"""
        return (
            json.loads(self.result_data) if isinstance(self.result_data, str) else self.result_data
        )

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
        settings = {}
        for setting in db.session.query(cls).all():
            # Handle special cases for non-string values
            if setting.key == "unique_filenames":
                settings[setting.key] = setting.value.lower() == "true"
            elif setting.key == "output_columns":
                if setting.value:
                    settings[setting.key] = json.loads(setting.value)
                else:
                    settings[setting.key] = []
            else:
                settings[setting.key] = setting.value

        # Add default values if not present
        if "output_path" not in settings:
            settings["output_path"] = "./output"
        if "person_list_path" not in settings:
            settings["person_list_path"] = "./person_lists"
        if "unique_filenames" not in settings:
            settings["unique_filenames"] = True
        if "output_columns" not in settings:
            settings["output_columns"] = []
        if "default_database" not in settings:
            settings["default_database"] = "PubMed"

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
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
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
