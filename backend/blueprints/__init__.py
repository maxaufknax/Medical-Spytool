#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Blueprints Package
This module imports and configures all blueprints for the application.
"""

# Import all blueprints
try:
    from backend.blueprints.main import main_bp
    from backend.blueprints.search import search_bp
    from backend.blueprints.persons import persons_bp
    from backend.blueprints.settings import settings_bp
    from backend.blueprints.analysis import analysis_bp
    from backend.blueprints.export import export_bp
    from backend.blueprints.logs import logs_bp
    from backend.blueprints.auth import auth_bp
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Error importing blueprints: {e}")
    raise

# Define the order of blueprint registration
# Main blueprint should be registered first
all_blueprints = [
    main_bp,      # No prefix (/)
    auth_bp,      # /auth
    search_bp,    # /search
    persons_bp,   # /persons
    settings_bp,  # /settings
    analysis_bp,  # /analysis
    export_bp,    # /export
    logs_bp,      # /logs
]
