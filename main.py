#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Main Module
This is the main entry point for the MedicalSpy web application.
"""

from backend.app import app

# This imports the Flask app from backend/app.py
# The app is then used by gunicorn when starting the server

if __name__ == "__main__":
    # This block won't be executed when running with gunicorn
    # It's here for development convenience when running directly
    app.run(host='0.0.0.0', port=5000, debug=True)