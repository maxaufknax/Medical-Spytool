#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Deep Debug Tool für Medical Spytool
Dieses Skript führt eine tiefgreifende Diagnose der Flask-Anwendung durch
und identifiziert Probleme bei der Blueprint-Registrierung und Template-Rendering.
"""

import os
import sys
import logging
from pathlib import Path
import importlib.util
import inspect
from flask import Flask, render_template, request, url_for
from werkzeug.routing import BuildError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("debug_flask_app.log", mode="w"),
    ],
)

logger = logging.getLogger("FlaskDebugger")

def import_module_from_file(file_path, module_name):
    """Import a Python module from a file path."""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            logger.error(f"Failed to import {module_name} from {file_path}: spec is None")
            return None
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Failed to import {module_name} from {file_path}: {e}")
        return None

def check_blueprint_routes(blueprint):
    """Check if a blueprint has routes."""
    routes = []
    for attr_name in dir(blueprint):
        attr = getattr(blueprint, attr_name)
        if callable(attr) and hasattr(attr, "view_class") or hasattr(attr, "__name__") and attr.__name__ == "view_functions":
            routes.append(attr_name)
    
    # Check if 'index' exists among routes
    has_index = 'index' in routes
    return routes, has_index

def check_template_file(template_path):
    """Check if a template file exists and is well-formed."""
    if not os.path.exists(template_path):
        return False, f"Template file does not exist: {template_path}"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Basic checks for template syntax
        errors = []
        if "{% extends" in content and not content.strip().startswith("{% extends"):
            errors.append("extends tag should be the first non-whitespace content")
        
        if content.count("{% block") != content.count("{% endblock"):
            errors.append("Mismatched block tags")
            
        if content.count("{{") != content.count("}}"):
            errors.append("Mismatched {{ }} delimiters")
            
        if content.count("{%") != content.count("%}"):
            errors.append("Mismatched {% %} delimiters")
            
        return len(errors) == 0, "\n".join(errors) if errors else "Template looks valid"
    except Exception as e:
        return False, f"Error reading template: {str(e)}"

def main():
    """Main function to diagnose the Flask application."""
    logger.info("=== Medical Spytool Flask App Diagnostics ===")
    
    # 1. Load application factory
    logger.info("Loading app factory...")
    app_module = import_module_from_file("backend/app.py", "backend.app")
    if not app_module or not hasattr(app_module, "create_app"):
        logger.error("Could not load app factory from backend/app.py")
        return False
    
    try:
        # 2. Create app with debug config
        logger.info("Creating Flask application...")
        app = app_module.create_app("development")
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        app.config['SERVER_NAME'] = 'localhost:5000'  # Required for url_for to work outside request context
    except Exception as e:
        logger.error(f"Error creating Flask app: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. Check registered blueprints and their routes
    logger.info("Checking registered blueprints...")
    with app.app_context():
        app_blueprints = {}
        for rule in app.url_map.iter_rules():
            endpoint = rule.endpoint
            blueprint_name = endpoint.split('.')[0] if '.' in endpoint else None
            
            if blueprint_name and blueprint_name not in app_blueprints:
                app_blueprints[blueprint_name] = []
            
            if blueprint_name:
                app_blueprints[blueprint_name].append((rule.rule, endpoint))
    
    # 4. Check blueprint files and their routes
    logger.info("Checking blueprint files...")
    blueprint_dir = Path("backend/blueprints")
    blueprint_files = list(blueprint_dir.glob("*.py"))
    blueprint_files = [f for f in blueprint_files if not f.name.startswith("__")]
    
    for bp_file in blueprint_files:
        bp_name = bp_file.stem
        logger.info(f"Checking blueprint: {bp_name}")
        
        # Check if blueprint is registered in app
        if bp_name not in app_blueprints:
            logger.warning(f"Blueprint {bp_name} exists but is not registered in the app")
        
        # Import module and check routes
        bp_module = import_module_from_file(bp_file, f"backend.blueprints.{bp_name}")
        if not bp_module:
            continue
        
        # Find the blueprint object
        bp_obj = None
        for attr_name in dir(bp_module):
            attr = getattr(bp_module, attr_name)
            if attr_name.endswith("_bp") or (attr_name == bp_name and hasattr(attr, "name")):
                bp_obj = attr
                break
        
        if not bp_obj:
            logger.warning(f"Could not find blueprint object in {bp_name}")
            continue
        
        # Check routes
        routes, has_index = check_blueprint_routes(bp_obj)
        if not has_index and f"{bp_name}.index" in [e.split('.')[-2:] for r, e in sum(app_blueprints.values(), [])]:
            logger.warning(f"Blueprint {bp_name} is expected to have 'index' route but none was found")
    
    # 5. Check template files
    logger.info("Checking template files...")
    template_dir = Path("backend/templates")
    template_files = list(template_dir.glob("**/*.html"))
    
    for template_file in template_files:
        rel_path = template_file.relative_to(template_dir)
        logger.info(f"Checking template: {rel_path}")
        
        is_valid, message = check_template_file(template_file)
        if not is_valid:
            logger.warning(f"Template {rel_path} has issues: {message}")
    
    # 6. Test URL building for each blueprint
    logger.info("Testing URL generation...")
    with app.app_context():
        for blueprint_name in app_blueprints:
            logger.info(f"Testing URLs for blueprint: {blueprint_name}")
            
            try:
                # Try to build URL for index endpoint
                url = url_for(f"{blueprint_name}.index")
                logger.info(f"URL for {blueprint_name}.index: {url}")
            except BuildError as e:
                logger.error(f"BuildError for {blueprint_name}.index: {e}")
    
    # 7. Check base.html template for navigation links
    logger.info("Checking base.html navigation links...")
    base_template = template_dir / "base.html"
    if base_template.exists():
        with open(base_template, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all url_for calls in the template
        import re
        url_for_pattern = r"url_for\(['\"]([^'\"]+)['\"]"
        endpoints = re.findall(url_for_pattern, content)
        
        with app.app_context():
            for endpoint in endpoints:
                try:
                    url = url_for(endpoint)
                    logger.info(f"URL for {endpoint}: {url}")
                except BuildError as e:
                    logger.error(f"BuildError for {endpoint}: {e}")
    
    logger.info("=== Diagnostic complete ===")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
