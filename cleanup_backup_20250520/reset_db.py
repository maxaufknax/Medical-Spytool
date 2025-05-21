#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from backend.models import db
from backend.app import app
import sys

def reset_database():
    """Reset the database by dropping all tables and recreating them"""
    try:
        with app.app_context():
            print("Dropping all tables...")
            db.drop_all()
            print("Creating all tables...")
            db.create_all()
            db.session.commit()
            print("Database schema has been reset successfully.")
            return True
    except Exception as e:
        print(f"Error resetting database: {str(e)}", file=sys.stderr)
        return False

if __name__ == '__main__':
    success = reset_database()
    sys.exit(0 if success else 1)
