#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import PyInstaller.__main__

def build_executable():
    """Build the executable with PyInstaller"""
    # Determine the root directory of the application
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define the PyInstaller command line arguments
    args = [
        'medical_spytool.py',                # Script to package
        '--name=MedicalSpytool',             # Name of the executable
        '--onefile',                         # Create a single file
        '--windowed',                        # Windows specific - don't open console window
        '--icon=static/favicon.ico',         # Application icon
        '--add-data=static;static',          # Include static files
        '--add-data=templates;templates',    # Include templates
        '--add-data=translations;translations', # Include translations
        '--hidden-import=sqlalchemy.sql.default_comparator', # Hidden imports
        '--hidden-import=pymysql',
        '--hidden-import=pandas',
        '--hidden-import=openpyxl',
        '--log-level=INFO',                  # Logging level
        '--clean',                           # Clean build directories before build
    ]
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    print("Build completed successfully!")

if __name__ == '__main__':
    build_executable()
