#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Model Tests
This module contains tests for the database models.
"""

import pytest
import json
from datetime import datetime
from backend.app import create_app
from backend.models import db, SearchQuery, SearchResult, Person, Setting, LogEntry


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    # Create tables in the test database
    with app.app_context():
        db.create_all()

    yield app

    # Clean up / reset resources
    with app.app_context():
        db.drop_all()


@pytest.fixture
def app_context(app):
    """Provide the application context for tests."""
    with app.app_context():
        yield


def test_search_query_model(app_context):
    """Test the SearchQuery model."""
    # Create a search query
    query = SearchQuery(
        name="Test Search",
        query="test",
        database="PubMed",
        additional_terms="additional",
        start_date="2020-01-01",
        end_date="2020-12-31",
        person_name="John Doe",
        search_mode="simple",
    )

    # Add to database
    db.session.add(query)
    db.session.commit()

    # Retrieve from database
    saved_query = SearchQuery.query.filter_by(name="Test Search").first()

    # Assert values
    assert saved_query is not None
    assert saved_query.name == "Test Search"
    assert saved_query.query == "test"
    assert saved_query.database == "PubMed"
    assert saved_query.additional_terms == "additional"
    assert saved_query.start_date == "2020-01-01"
    assert saved_query.end_date == "2020-12-31"
    assert saved_query.person_name == "John Doe"
    assert saved_query.search_mode == "simple"

    # Test to_dict method
    query_dict = saved_query.to_dict()
    assert query_dict["name"] == "Test Search"
    assert query_dict["query"] == "test"
    assert "id" in query_dict
    assert "created_at" in query_dict


def test_search_result_model(app_context):
    """Test the SearchResult model."""
    # Create a search query to associate with result
    query = SearchQuery(name="Test Search", query="test")
    db.session.add(query)
    db.session.commit()

    # Create result data
    result_data = {"Title": "Test Title", "Authors": ["Author 1", "Author 2"], "Year": "2020"}

    # Create a search result
    result = SearchResult(query_id=query.id, result_data=json.dumps(result_data))

    # Add to database
    db.session.add(result)
    db.session.commit()

    # Retrieve from database
    saved_result = SearchResult.query.filter_by(query_id=query.id).first()

    # Assert values
    assert saved_result is not None
    assert saved_result.query_id == query.id
    assert json.loads(saved_result.result_data) == result_data

    # Test data property
    assert saved_result.data == result_data

    # Test to_dict method
    result_dict = saved_result.to_dict()
    assert result_dict["Title"] == "Test Title"
    assert result_dict["Authors"] == ["Author 1", "Author 2"]
    assert result_dict["Year"] == "2020"


def test_person_model(app_context):
    """Test the Person model."""
    # Create a person
    person = Person(name="John Doe", first_name="John", last_name="Doe")

    # Add to database
    db.session.add(person)
    db.session.commit()

    # Retrieve from database
    saved_person = Person.query.filter_by(name="John Doe").first()

    # Assert values
    assert saved_person is not None
    assert saved_person.name == "John Doe"
    assert saved_person.first_name == "John"
    assert saved_person.last_name == "Doe"

    # Test to_dict method
    person_dict = saved_person.to_dict()
    assert person_dict["name"] == "John Doe"
    assert person_dict["first_name"] == "John"
    assert person_dict["last_name"] == "Doe"
    assert "id" in person_dict


def test_setting_model(app_context):
    """Test the Setting model."""
    # Create settings
    settings = [
        Setting(key="output_path", value="./output"),
        Setting(key="unique_filenames", value="true"),
        Setting(key="output_columns", value=json.dumps(["Title", "Authors"])),
    ]

    # Add to database
    db.session.add_all(settings)
    db.session.commit()

    # Test get_settings_dict method
    settings_dict = Setting.get_settings_dict()
    assert settings_dict["output_path"] == "./output"
    assert settings_dict["unique_filenames"] is True  # Should be converted to bool
    assert settings_dict["output_columns"] == ["Title", "Authors"]  # Should be parsed from JSON

    # Test save_settings_dict method
    new_settings = {
        "output_path": "./new_output",
        "unique_filenames": False,
        "new_setting": "value",
    }

    Setting.save_settings_dict(new_settings)

    # Verify updated settings
    updated_settings = Setting.get_settings_dict()
    assert updated_settings["output_path"] == "./new_output"
    assert updated_settings["unique_filenames"] is False
    assert updated_settings["new_setting"] == "value"
    assert updated_settings["output_columns"] == ["Title", "Authors"]  # Should be unchanged


def test_log_entry_model(app_context):
    """Test the LogEntry model."""
    # Create a log entry
    log = LogEntry(level="INFO", message="Test log message")

    # Add to database
    db.session.add(log)
    db.session.commit()

    # Retrieve from database
    saved_log = LogEntry.query.filter_by(message="Test log message").first()

    # Assert values
    assert saved_log is not None
    assert saved_log.level == "INFO"
    assert saved_log.message == "Test log message"

    # Test to_dict method
    log_dict = saved_log.to_dict()
    assert log_dict["level"] == "INFO"
    assert log_dict["message"] == "Test log message"
    assert "timestamp" in log_dict

    # Test get_logs method
    logs = LogEntry.get_logs()
    assert len(logs) == 1
    assert logs[0].message == "Test log message"

    # Test add_log method
    LogEntry.add_log("WARNING", "Another test message")
    logs = LogEntry.get_logs()
    assert len(logs) == 2
    assert logs[1].level == "WARNING"

    # Test clear_logs method
    LogEntry.clear_logs()
    logs = LogEntry.get_logs()
    assert len(logs) == 0
