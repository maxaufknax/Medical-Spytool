#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from app import create_app

def main():
    """Main entry point for the application"""
    # Set environment variables for configuration
    os.environ.setdefault('FLASK_ENV', 'production')
    
    # Create the Flask application instance
    app = create_app()
    
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        # Use a production server instead of Flask's development server
        from waitress import serve
        serve(app, host='127.0.0.1', port=5000)
    else:
        # Running as script
        app.run(host='127.0.0.1', port=5000, debug=False)

if __name__ == '__main__':
    main()
