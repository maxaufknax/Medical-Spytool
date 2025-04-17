#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Database Models
This module defines the database models for the MedicalSpy application.
"""

import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB

# Initialize SQLAlchemy
db = SQLAlchemy()

class SearchQuery(db.Model):
    """Model for saved search queries"""
    __tablename__ = 'search_queries'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    query = db.Column(db.Text)
    database = db.Column(db.String(255))
    additional_terms = db.Column(db.Text)
    start_date = db.Column(db.String(50))
    end_date = db.Column(db.String(50))
    person_name = db.Column(db.String(255))
    search_mode = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    results = db.relationship('SearchResult', backref='query', cascade='all, delete-orphan')

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'query': self.query,
            'database': self.database,
            'additional_terms': self.additional_terms,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'person_name': self.person_name,
            'search_mode': self.search_mode,
            'saved_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class SearchResult(db.Model):
    """Model for search results"""
    __tablename__ = 'search_results'

    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('search_queries.id'), nullable=False)
    database = db.Column(db.String(100), nullable=False)
    result_data = db.Column(JSONB, nullable=False)  # Store the full result as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'query_id': self.query_id,
            'database': self.database,
            **self.result_data,
            'saved_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Person(db.Model):
    """Model for persons"""
    __tablename__ = 'persons'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'first_name': self.first_name,
            'last_name': self.last_name
        }

class Setting(db.Model):
    """Model for application settings"""
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)

    @classmethod
    def get_settings_dict(cls):
        """Get all settings as a dictionary"""
        settings = {}
        for setting in db.session.query(cls).all():
            # Handle special cases for non-string values
            if setting.key == 'unique_filenames':
                settings[setting.key] = setting.value.lower() == 'true'
            elif setting.key == 'output_columns':
                if setting.value:
                    settings[setting.key] = json.loads(setting.value)
                else:
                    settings[setting.key] = []
            else:
                settings[setting.key] = setting.value

        # Add default values if not present
        if 'output_path' not in settings:
            settings['output_path'] = './output'
        if 'person_list_path' not in settings:
            settings['person_list_path'] = './person_lists'
        if 'unique_filenames' not in settings:
            settings['unique_filenames'] = True
        if 'output_columns' not in settings:
            settings['output_columns'] = []
        if 'default_database' not in settings:
            settings['default_database'] = 'PubMed'

        return settings

    @classmethod
    def save_settings_dict(cls, settings_dict):
        """Save a dictionary of settings"""
        for key, value in settings_dict.items():
            # Handle special cases for non-string values
            if key == 'unique_filenames':
                value_str = str(value).lower()
            elif key == 'output_columns':
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
    __tablename__ = 'log_entries'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    level = db.Column(db.String(20), default='INFO')
    message = db.Column(db.Text, nullable=False)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'level': self.level,
            'message': self.message
        }

    @classmethod
    def get_logs(cls, limit=100):
        """Get the latest log entries"""
        logs = db.session.query(cls).order_by(cls.timestamp.desc()).limit(limit).all()
        return [f"[{log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {log.level}: {log.message}" for log in logs]

    @classmethod
    def add_log(cls, message, level='INFO'):
        """Add a new log entry"""
        log = cls(message=message, level=level)
        db.session.add(log)
        db.session.commit()

    @classmethod
    def clear_logs(cls):
        """Clear all log entries"""
        db.session.query(cls).delete()
        db.session.commit()