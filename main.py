#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Main WSGI Application Entry Point

This module provides the Flask application instance for WSGI servers like Gunicorn.
For local development, debugging, and management tasks, use `python manage.py` instead.
"""

import os
import sys

# Add the project root to sys.path to ensure imports work correctly
# This assumes main.py is in the project root directory.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Try to load environment variables from .env file
# WSGI servers might have their own ways of managing environment variables,
# but this provides a fallback for some deployment scenarios.
try:
    from dotenv import load_dotenv

    # Load .env from the project root (where manage.py and this main.py are)
    dotenv_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
except ImportError:
    # python-dotenv package not installed, or not needed if env vars are set externally
    pass

# Import the Flask app factory from backend.app and create the app instance
# This ensures the app is created using the same mechanism as `flask run`
from backend.app import create_app

app = create_app()

# The 'app' object created above is what WSGI servers like Gunicorn will look for.
# Example Gunicorn command: gunicorn main:app

# The `if __name__ == "__main__":` block has been removed.
# To run the development server, please use the command:
# python manage.py run
