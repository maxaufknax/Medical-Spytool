#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Main Module
This is the main entry point for the MedicalSpy web application.

This module serves as the entry point for Gunicorn or other WSGI servers.
For local development, use `run.py` instead, which provides additional 
setup and configuration options.
"""

import os
import sys

# Add the project root to sys.path to ensure imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv package not installed
    pass

# Import the Flask app from backend/app.py
from backend.app import app

# This app object is used by gunicorn when starting the server

if __name__ == "__main__":
    # This block won't be executed when running with gunicorn
    # It's here for development convenience when running directly
    # For full development setup, use run.py instead
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)