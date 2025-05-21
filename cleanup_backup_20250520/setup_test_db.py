#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Test Database Setup

Dieses Skript bereitet die Testdatenbank für die Unit-Tests vor.
Es erstellt eine separate Test-Datenbank und füllt sie mit minimalen Testdaten.
"""

import os
import sys
import logging
import tempfile
from pathlib import Path

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("test_setup.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("TestSetup")


def setup_test_environment():
    """
    Richtet die Testumgebung ein und erstellt eine temporäre Testdatenbank.
    """
    # Setze das aktuelle Verzeichnis in sys.path
    base_dir = Path(__file__).resolve().parent
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))

    # Erstelle temporäre Datenbank für Tests
    _, db_path = tempfile.mkstemp(suffix=".db", prefix="test_medicalspy_")
    temp_db_uri = f"sqlite:///{db_path}"

    # Setze Umgebungsvariablen für Tests
    os.environ["TESTING"] = "True"
    os.environ["DATABASE_URL"] = temp_db_uri
    os.environ["FLASK_ENV"] = "testing"
    os.environ["DEBUG"] = "True"

    logger.info(f"Temporäre Test-Datenbank erstellt: {db_path}")
    logger.info(f"Test-Datenbank-URI: {temp_db_uri}")

    return temp_db_uri, db_path


def create_test_database(db_uri):
    """
    Erstellt die Testdatenbank-Struktur und füllt sie mit minimalen Testdaten.
    """
    try:
        # Importiere Flask-App und DB mit der neuen Testkonfiguration
        from backend.app import create_app
        from backend.models import db, User, SearchQuery, SearchResult, Person, Setting, LogEntry
        from datetime import datetime, timedelta

        # Erstelle App mit Testkonfiguration
        app = create_app(testing=True)

        # Überschreibe die Datenbank-URI
        app.config["SQLALCHEMY_DATABASE_URI"] = db_uri

        # Erstelle die Datenbanktabellen
        with app.app_context():
            # Erstelle Tabellen
            db.create_all()
            logger.info("Testdatenbank-Tabellen erstellt.")

            # Erstelle Testdaten

            # Admin-User erstellen
            admin = User(username="admin", email="admin@example.com", is_admin=True)
            admin.set_password("admin123")
            db.session.add(admin)

            # Test-User erstellen
            test_user = User(username="testuser", email="test@example.com")
            test_user.set_password("password")
            db.session.add(test_user)

            # Beispiel-Person erstellen
            person = Person(
                name="Dr. Test Person",
                email="test.person@example.com",
                affiliation="Test University",
                user_id=admin.id,
                created_at=datetime.now(),
            )
            db.session.add(person)

            # Beispiel-Suchanfrage erstellen
            query = SearchQuery(
                terms="test query",
                database="PubMed",
                filters={"year": "2020-2023"},
                user_id=admin.id,
                created_at=datetime.now() - timedelta(days=1),
            )
            db.session.add(query)
            db.session.flush()

            # Beispiel-Suchergebnis erstellen
            result = SearchResult(
                query_id=query.id,
                title="Test Publication Title",
                authors=["Author A", "Author B"],
                year=2022,
                journal="Test Journal",
                abstract="This is a test abstract for unit testing purposes.",
                url="https://example.org/test",
                citation_count=10,
                created_at=datetime.now() - timedelta(hours=1),
                result_data={
                    "keywords": ["test", "medical", "example"],
                    "doi": "10.1234/test.123",
                    "pmid": "12345678",
                },
            )
            db.session.add(result)

            # Beispieleinstellungen
            settings = [
                Setting(key="default_database", value="PubMed"),
                Setting(key="max_results", value="50"),
                Setting(key="enable_export", value="true"),
            ]
            db.session.add_all(settings)

            # Beispiel-Logeintrag
            log = LogEntry(
                level="INFO",
                message="Test log entry",
                source="test_setup",
                timestamp=datetime.now(),
            )
            db.session.add(log)

            # Alle Änderungen speichern
            db.session.commit()
            logger.info("Testdaten erfolgreich in die Datenbank eingefügt.")

            # Überprüfen der Daten
            user_count = User.query.count()
            result_count = SearchResult.query.count()
            logger.info(
                f"Erstellte Test-Datensätze: {user_count} Benutzer, {result_count} Suchergebnisse"
            )

            return True

    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Testdatenbank: {e}", exc_info=True)
        return False


def write_pytest_config():
    """
    Erstellt eine konftest.py-Datei für pytest, um die Testdatenbank einzurichten.
    """
    try:
        conftest_path = Path("tests/conftest.py")
        conftest_dir = conftest_path.parent

        # Stelle sicher, dass das tests-Verzeichnis existiert
        if not conftest_dir.exists():
            conftest_dir.mkdir(parents=True, exist_ok=True)

        # Conftest-Inhalt
        conftest_content = """
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
    app.config.update({
        "SQLALCHEMY_DATABASE_URI": test_db_uri,
        "TESTING": True,
        "WTF_CSRF_ENABLED": False  # Disable CSRF protection for testing
    })
    
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
"""

        # Schreibe die Conftest-Datei
        with open(conftest_path, "w", encoding="utf-8") as f:
            f.write(conftest_content.strip())

        logger.info(f"pytest Konfiguration erstellt: {conftest_path}")
        return True

    except Exception as e:
        logger.error(f"Fehler beim Erstellen der pytest-Konfiguration: {e}", exc_info=True)
        return False


def main():
    """Hauptfunktion"""
    print("\n" + "=" * 80)
    print("{:^80}".format("MEDICAL SPYTOOL - TEST DATABASE SETUP"))
    print("=" * 80 + "\n")

    # Richtet die Testumgebung ein
    db_uri, db_path = setup_test_environment()

    # Erstellt die Testdatenbank
    success = create_test_database(db_uri)

    # Erstellt die pytest-Konfiguration
    config_success = write_pytest_config()

    if success and config_success:
        print("\n✅ Testdatenbank und Konfiguration erfolgreich erstellt!")
        print(f"Temporäre Testdatenbank: {db_path}")
        print("Führen Sie 'python run_tests.py' aus, um die Tests zu starten.")
        return 0
    else:
        print("\n❌ Fehler beim Einrichten der Testumgebung.")
        print("Überprüfen Sie die Logs für Details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
