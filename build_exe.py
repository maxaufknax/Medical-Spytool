#!/usr/bin/env python
"""
Build script for creating a standalone executable with PyInstaller.

This script configures PyInstaller to create a single executable file
for the Medical Spytool application, including all necessary resources.

Usage:
    python build_exe.py
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime

# PyInstaller configuration
PYINSTALLER_ARGS = [
    '--name=MedicalSpyTool',
    '--onefile',  # Create a single executable file
    '--windowed',  # Don't show console window on Windows
    '--icon=assets/icon.ico',  # Application icon
    '--add-data=templates;templates',  # Include templates
    '--add-data=static;static',  # Include static files
    '--add-data=assets;assets',  # Include assets
    # Core dependencies often needing hidden imports
    '--hidden-import=pandas',
    '--hidden-import=openpyxl',
    # '--hidden-import=xlsxwriter', # Commented out as it was removed from requirements.txt
    '--hidden-import=bootstrap_flask', # Changed from flask_bootstrap
    '--hidden-import=waitress',
    '--hidden-import=matplotlib',
    '--hidden-import=matplotlib.backends.backend_agg', # Common backend for charts
    '--hidden-import=seaborn',
    '--hidden-import=psutil',
    '--hidden-import=pkg_resources.py2_warn', # Sometimes needed by various packages

    # Application modules (ensure PyInstaller finds them)
    '--hidden-import=database_connectors',
    '--hidden-import=utils',
    '--hidden-import=utils.api_key_manager',
    '--hidden-import=utils.config_manager',
    '--hidden-import=utils.export_manager',
    '--hidden-import=utils.logging_manager',
    '--hidden-import=utils.path_manager',
    '--hidden-import=utils.search_profiles',

    # Explicitly list all connectors
    '--hidden-import=database_connectors.base_connector',
    '--hidden-import=database_connectors.dnb_connector',
    '--hidden-import=database_connectors.gepris_connector',
    '--hidden-import=database_connectors.pubmed_connector',
    '--hidden-import=database_connectors.scopus_connector',
    '--hidden-import=database_connectors.wos_connector',

    # Other potential hidden imports that might arise from libraries
    '--hidden-import=sklearn.utils._cython_blas', # Seaborn might pull this
    '--hidden-import=scipy.sparse.csgraph._validation', # Scipy is often a dep of stats/data libs
    '--hidden-import=scipy.integrate',
    '--hidden-import=PIL._imagingtk', # Pillow (PIL) often used by matplotlib or other image libs
    '--hidden-import=PIL._tkinter_finder',
    '--clean',  # Clean PyInstaller cache
    'main.py'  # Main script
]

# Ensure the dist directory exists
if not os.path.exists('dist'):
    os.makedirs('dist')

# Create a build info file
def create_build_info():
    """Create a build info file with version and build date."""
    build_info = {
        'version': '2.0.0',
        'build_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'python_version': sys.version,
    }
    
    with open('assets/build_info.txt', 'w') as f:
        for key, value in build_info.items():
            f.write(f"{key}: {value}\n")

# Copy necessary files to the dist directory
def copy_additional_files():
    """Copy additional files to the dist directory."""
    # Create directories
    os.makedirs('dist/person_lists', exist_ok=True)
    os.makedirs('dist/output', exist_ok=True)
    os.makedirs('dist/logs', exist_ok=True)
    
    # Copy README and license
    if os.path.exists('README.md'):
        shutil.copy('README.md', 'dist/README.md')
    
    # Create an empty persons.json file
    with open('dist/person_lists/persons.json', 'w') as f:
        f.write('[]')

# Main build function
def build_executable():
    """Build the executable using PyInstaller."""
    print("Building Medical Spytool executable...")
    
    # Create build info
    create_build_info()
    
    # Run PyInstaller
    pyinstaller_cmd = ['pyinstaller'] + PYINSTALLER_ARGS
    
    try:
        subprocess.run(pyinstaller_cmd, check=True)
        print("PyInstaller completed successfully.")
        
        # Copy additional files
        copy_additional_files()
        print("Additional files copied.")
        
        print("\nBuild completed successfully!")
        print(f"Executable is located at: {os.path.abspath('dist/MedicalSpyTool.exe')}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running PyInstaller: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error during build process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()