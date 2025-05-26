#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Blueprints Package
This module imports and configures all blueprints for the application.
"""

import logging

# Import all blueprints
try:
    from .main import main_bp
    from .search import search_bp
    from .persons import persons_bp
    from .settings import settings_bp
    from .analysis import analysis_bp
    from .export import export_bp
    from .logs import logs_bp
    from .auth import auth_bp
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Error importing blueprints: {e}")
    # If a blueprint fails to import, it's a critical error, so re-raise
    raise

# Define the blueprints and their URL prefixes
# Format: (blueprint_name_str, blueprint_instance, url_prefix_str)
all_blueprints = [
    ("main", main_bp, "/"),
    ("auth", auth_bp, "/auth"),
    ("search", search_bp, "/search"),
    ("persons", persons_bp, "/persons"),
    ("settings", settings_bp, "/settings"),
    ("analysis", analysis_bp, "/analysis"),
    ("export", export_bp, "/export"),
    ("logs", logs_bp, "/logs"),
]

# Example of how you might dynamically discover blueprints if needed,
# but for now, explicit listing is clearer and less error-prone.
# all_blueprints = []
# for name, obj in inspect.getmembers(__import__(__name__, fromlist=['*']))):
#     if isinstance(obj, Blueprint):
#         prefix = f"/{name.replace('_bp', '')}" if name != 'main_bp' else '/'
#         all_blueprints.append((name.replace('_bp', ''), obj, prefix))

logger = logging.getLogger(__name__)
logger.info("Blueprints initialized and collected.")
