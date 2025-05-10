#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Configuration module
This module handles loading and saving application settings.

Settings are loaded from:
1. Environment variables (top priority)
2. .env file (if python-dotenv is installed)
3. Database (via Setting model)
4. Default values
"""

import os
import json
import logging
from pathlib import Path

# Try to import dotenv for .env file loading
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Configuration file (used as fallback and for saving non-sensitive settings)
CONFIG_FILE = "medicalspy_config.json"

logger = logging.getLogger("MedicalSpy")

# Load environment variables from .env file if available
if DOTENV_AVAILABLE:
    env_path = Path('.') / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.info("Environment variables loaded from .env file")

def get_env_setting(key, default=None, allow_sensitive=False):
    """
    Get a setting from environment variables with fallback to default.
    
    Args:
        key (str): The environment variable name
        default (any, optional): Default value if not found
        allow_sensitive (bool): Whether to allow sensitive values in logs
        
    Returns:
        The value of the environment variable or default
    """
    # Standardize key for environment variables (uppercase, with prefix)
    env_key = key.upper()
    
    # Check if environment variable exists
    value = os.environ.get(env_key, default)
    
    # Log the retrieval (but not the value for sensitive data)
    if value is not None and value != default:
        if allow_sensitive:
            logger.debug(f"Retrieved setting from environment: {key}={value}")
        else:
            logger.debug(f"Retrieved setting from environment: {key}=<value hidden>")
            
    return value

def load_settings():
    """
    Load settings from multiple sources in priority order:
    1. Environment variables
    2. Config file
    3. Default values
    
    Returns:
        dict: Settings dictionary
    """
    try:
        # Start with default settings
        settings = {
            "output_path": "./output",
            "person_list_path": "./person_lists",
            "unique_filenames": False,
            "pubmed_api_key": "",
            "output_columns": [
                "Name", "Title", "Creator", "Publication Year", "Identifier",
                "URL", "Authors", "Citation Count"
            ],
            "default_database": "PubMed"
        }
        
        # Try to load from config file
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    file_settings = json.load(f)
                    # Update settings with file values
                    settings.update(file_settings)
                logger.info("Settings loaded from configuration file")
            except Exception as e:
                logger.error(f"Error loading settings from config file: {e}")
        
        # Override with environment variables
        env_settings = {
            "output_path": get_env_setting("OUTPUT_PATH", settings["output_path"], True),
            "person_list_path": get_env_setting("PERSON_LIST_PATH", settings["person_list_path"], True),
            "pubmed_api_key": get_env_setting("PUBMED_API_KEY", settings["pubmed_api_key"]),
            "default_database": get_env_setting("DEFAULT_DATABASE", settings["default_database"], True)
        }
        
        # Update settings with environment values
        settings.update(env_settings)
        
        # Save non-sensitive settings to config file for persistence
        save_non_sensitive_settings(settings)
        
        return settings
        
    except Exception as e:
        logger.error(f"Error in load_settings: {e}")
        # Return basic default settings in case of error
        return {
            "output_path": "./output",
            "person_list_path": "./person_lists",
            "unique_filenames": False,
            "pubmed_api_key": "",
            "output_columns": [
                "Name", "Title", "Creator", "Publication Year", "Identifier",
                "URL", "Authors", "Citation Count"
            ],
            "default_database": "PubMed"
        }

def save_non_sensitive_settings(settings):
    """
    Save non-sensitive settings to the configuration file.
    Sensitive settings like API keys are not saved.
    
    Args:
        settings (dict): Settings to save
    """
    try:
        # Create a copy without sensitive data
        safe_settings = settings.copy()
        
        # Remove sensitive keys
        if "pubmed_api_key" in safe_settings:
            safe_settings["pubmed_api_key"] = ""
        
        # Save to file
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(safe_settings, f, indent=4)
        logger.info("Non-sensitive settings saved to configuration file")
    except Exception as e:
        logger.error(f"Error saving settings: {e}")

def save_settings(settings):
    """
    Save settings to the configuration file.
    This function is maintained for backward compatibility.
    
    Args:
        settings (dict): Settings to save
    """
    save_non_sensitive_settings(settings)

def ensure_directories(settings):
    """
    Ensure that required directories exist.
    
    Args:
        settings (dict): Application settings
    """
    try:
        os.makedirs(settings["output_path"], exist_ok=True)
        os.makedirs(settings["person_list_path"], exist_ok=True)
        logger.info("Required directories have been created")
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
