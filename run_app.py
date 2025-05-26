#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Application Startup Script
This script ensures the proper Python path and starts the Flask application.
"""

import sys
import os
from pathlib import Path

# Get the project root directory (where this script is located)
project_root = Path(__file__).parent.absolute()
backend_dir = project_root / "backend"

# Add both project root and backend directory to Python path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Change to backend directory for proper file resolution
os.chdir(backend_dir)

# Now import and run the Flask application
if __name__ == "__main__":
    from app import create_app
    
    app = create_app()
    # Disable reloader to avoid path issues during development
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
