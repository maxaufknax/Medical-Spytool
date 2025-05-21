#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - App Tests
This module contains tests for the main Flask application.
"""

import pytest
from backend.app import create_app


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SERVER_NAME": "test.local",
        }
    )

    # Create tables in the test database
    with app.app_context():
        from backend.models import db

        db.create_all()

    yield app

    # Clean up / reset resources
    with app.app_context():
        from backend.models import db

        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "ok"
    assert json_data["database"] == "connected"


def test_home_page(client):
    """Test that the home page loads."""
    response = client.get("/")
    assert response.status_code == 200


def test_search_page(client):
    """Test that the search page loads."""
    response = client.get("/search")
    assert response.status_code == 200
