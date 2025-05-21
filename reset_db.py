#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reset Database Script
Resets the database for Medical Spytool
"""

from backend.models import db
from backend.app import create_app

def reset_db():
    """Drop and recreate all database tables"""
    print("Initializing app context...")
    app = create_app()
    
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        print("Database reset completed successfully")

if __name__ == "__main__":
    reset_db()
