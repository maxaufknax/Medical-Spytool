import os
import sys
import pytest
from pathlib import Path

# Füge das Projektverzeichnis zum Pfad hinzu
base_dir = Path(__file__).resolve().parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

# Importiere App und DB
from backend.app import create_app
from backend.models import db as _db


@pytest.fixture(scope="session")
def app():
    # Set environment variables for testing
    os.environ["TESTING"] = "True"
    os.environ["FLASK_ENV"] = "testing"

    # Use in-memory SQLite database for testing
    test_db_uri = "sqlite:///:memory:"

    # Create the Flask app
    app = create_app(testing=True)
    app.config.update(
        {
            "SQLALCHEMY_DATABASE_URI": test_db_uri,
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,  # Disable CSRF protection for testing
        }
    )

    # Create an application context
    with app.app_context():
        # Create the database tables
        _db.create_all()

        # Here you could add test data if needed

        yield app

        # Clean up after tests
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    # Return a database session for testing
    with app.app_context():
        yield _db
        # Clean up after each test
        _db.session.rollback()


@pytest.fixture(scope="function")
def client(app):
    # Return a test client for the Flask app
    return app.test_client()
