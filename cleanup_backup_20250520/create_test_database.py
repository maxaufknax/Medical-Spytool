#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Enhanced Test Database Setup

This script creates and populates a test database with sample data
for testing the MedicalSpy application. It helps ensure proper database
initialization with all required tables and sample data.
"""

import os
import sys
import json
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_database_setup")


def setup_python_path():
    """Set up the Python path to include the current directory"""
    current_dir = Path(__file__).parent.absolute()
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    return current_dir


def create_test_database():
    """Create a test database with sample data"""
    # Import Flask components
    from backend.app import create_app
    from backend.models import db, User, SearchQuery, SearchResult, Person, Setting, LogEntry

    # Use an in-memory SQLite database for testing
    app = create_app("testing")
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///instance/medicalspy.db",
            "WTF_CSRF_ENABLED": False,
        }
    )

    logger.info("Creating test database with sample data...")

    with app.app_context():
        # Create all tables
        db.create_all()

        # Create test user
        test_user = User(username="testuser", email="test@example.com", name="Test User")
        test_user.set_password("password123")
        db.session.add(test_user)

        # Create admin user
        admin_user = User(
            username="admin", email="admin@example.com", name="Admin User", is_admin=True
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)

        # Add some test persons
        persons = [
            Person(
                name="Einstein, Albert",
                aliases=["A. Einstein"],
                metadata={"field": "Physics", "notable_work": "Theory of Relativity"},
            ),
            Person(
                name="Curie, Marie",
                aliases=["M. Curie", "Marie Skłodowska Curie"],
                metadata={"field": "Chemistry", "notable_work": "Radioactivity"},
            ),
            Person(
                name="Pasteur, Louis",
                aliases=["L. Pasteur"],
                metadata={"field": "Microbiology", "notable_work": "Vaccination"},
            ),
        ]
        db.session.add_all(persons)

        # Add sample search queries
        for i in range(5):
            query = SearchQuery(
                query_text=f"Test Query {i+1}",
                database_name="PubMed",
                parameters={"max_results": 10, "year_from": 2000, "year_to": 2023},
                user_id=test_user.id if i % 2 == 0 else admin_user.id,
                created_at=datetime.now() - timedelta(days=i),
            )
            db.session.add(query)

            # Add sample results for each query
            for j in range(3):
                result = SearchResult(
                    query_id=i + 1,  # Will be set after the query is added
                    title=f"Test Publication {i+1}-{j+1}",
                    authors=["Author One", "Author Two"],
                    year=2020 + j,
                    journal="Test Journal",
                    abstract="This is a test abstract for the publication.",
                    url=f"https://example.com/publication/{i+1}/{j+1}",
                    citation_count=random.randint(0, 100),
                    result_data={
                        "keywords": ["test", "medical", "research"],
                        "doi": f"10.1234/test-{i+1}-{j+1}",
                    },
                )
                db.session.add(result)

        # Add settings
        settings = [
            Setting(
                key="default_database",
                value="PubMed",
                metadata={"description": "Default database for searches"},
            ),
            Setting(
                key="max_results_per_page",
                value="20",
                metadata={"description": "Maximum results per page"},
            ),
            Setting(
                key="enable_export",
                value="true",
                metadata={"description": "Enable export functionality"},
            ),
        ]
        db.session.add_all(settings)

        # Add log entries
        logs = [
            LogEntry(
                level="INFO",
                message=f"Test log entry {i+1}",
                source="test_database_setup",
                timestamp=datetime.now() - timedelta(hours=i),
            )
            for i in range(10)
        ]
        db.session.add_all(logs)

        # Commit all changes
        db.session.commit()

        logger.info(f"Database initialized with:")
        logger.info(f"- {User.query.count()} users")
        logger.info(f"- {Person.query.count()} persons")
        logger.info(f"- {SearchQuery.query.count()} search queries")
        logger.info(f"- {SearchResult.query.count()} search results")
        logger.info(f"- {Setting.query.count()} settings")
        logger.info(f"- {LogEntry.query.count()} log entries")

    return app


def main():
    """Main function"""
    setup_python_path()
    app = create_test_database()

    print("\n" + "=" * 80)
    print("Test database successfully created and populated!")
    print("This database exists only in memory and is for testing purposes.")
    print("=" * 80)

    # Display app config for debugging
    print("\nApplication Configuration:")
    for key in sorted(app.config.keys()):
        if not key.startswith("_") and key in ["SQLALCHEMY_DATABASE_URI", "ENV", "TESTING"]:
            print(f"{key}: {app.config[key]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
