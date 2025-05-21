import pytest
from flask import url_for
from backend.app import create_app
import json

def create_test_app():
    """Helper function to create a test Flask application."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing
        "SESSION_TYPE": "filesystem",
        "SERVER_NAME": "localhost"  # Required for url_for to work in tests
    })
    return app

@pytest.fixture
def app():
    """Create and configure the test application."""
    app = create_test_app()
    app_context = app.app_context()
    app_context.push()
    
    # Setup database
    from backend.models import db
    db.create_all()
    
    yield app
    
    db.session.remove()
    db.drop_all()
    app_context.pop()

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

def test_search_form(client):
    """Test if the search page is accessible."""
    response = client.get('/search/')
    assert response.status_code == 200

def test_simple_search(client, app):
    """Test simple search."""
    with app.test_request_context():
        data = {
            'search_mode': 'simple',
            'search_type': 'quick',
            'query': 'test',
            'databases[]': 'PubMed',  # Wird als Form-Parameter gesendet
            'csrf_token': 'dummy_token'
        }
        print(f"\nSending data: {json.dumps(data, indent=2)}")
        response = client.post('/search/', data=data)
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data.decode()}")
        assert response.status_code in [200, 302]

def test_person_search(client, app):
    """Test person search."""
    with app.test_request_context():
        data = {
            'search_mode': 'person',
            'search_type': 'person',
            'query': 'John Doe',
            'databases[]': 'PubMed',  # Wird als Form-Parameter gesendet
            'csrf_token': 'dummy_token'
        }
        print(f"\nSending data: {json.dumps(data, indent=2)}")
        response = client.post('/search/', data=data)
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data.decode()}")
        assert response.status_code in [200, 302]

def test_advanced_search(client, app):
    """Test advanced search."""
    with app.test_request_context():
        data = {
            'search_mode': 'advanced',
            'search_type': 'advanced',
            'query': 'cancer treatment',
            'year_from': '2020',
            'year_to': '2025',
            'databases[]': 'PubMed',  # Wird als Form-Parameter gesendet
            'csrf_token': 'dummy_token'
        }
        print(f"\nSending data: {json.dumps(data, indent=2)}")
        response = client.post('/search/', data=data)
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data.decode()}")
        assert response.status_code in [200, 302]

def test_invalid_search(client):
    """Test search with invalid parameters."""
    # Test mit leeren Daten
    response = client.post('/search/', data={})
    assert response.status_code == 302  # Erwarte Umleitung bei leeren Daten
    
    # Test mit ungültigem Suchmodus
    data = {'search_mode': 'invalid', 'databases[]': 'PubMed', 'query': 'test'}
    response = client.post('/search/', data=data)
    assert response.status_code == 302  # Erwarte Umleitung bei ungültigem Modus
    
def test_search_validation(client):
    """Test search parameter validation."""
    # Test ohne Datenbanken
    data = {
        'search_mode': 'simple',
        'search_type': 'quick',
        'query': 'test'
    }
    response = client.post('/search/', data=data)
    assert response.status_code == 302  # Erwarte Umleitung bei fehlenden Datenbanken

    # Test ohne Query
    data = {
        'search_mode': 'simple',
        'search_type': 'quick',
        'databases[]': 'PubMed'
    }
    response = client.post('/search/', data=data)
    assert response.status_code == 302  # Erwarte Umleitung bei fehlender Query
