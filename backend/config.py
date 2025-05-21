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
    load_dotenv = None

# Configuration file (used as fallback and for saving non-sensitive settings)
CONFIG_FILE = "medicalspy_config.json"

# Application secret key - secure but stored only in environment or .env
SECRET_KEY = os.environ.get("SECRET_KEY", "a_secure_randomized_key_for_development_only_please_change_in_production")

logger = logging.getLogger("MedicalSpy")

# Load environment variables from .env file if available
if DOTENV_AVAILABLE:
    env_path = Path(".") / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.info("Environment variables loaded from .env file")


def get_env_setting(key, default=None, sensitive=False):
    """
    Get a setting from environment variables with fallback to default.

    Args:
        key (str): The environment variable name
        default (any, optional): Default value if not found
        sensitive (bool): Whether this is a sensitive setting like an API key

    Returns:
        The value of the environment variable or default
    """
    # Standardize key for environment variables (uppercase, with prefix)
    env_key = key.upper()

    # Check if environment variable exists
    value = os.environ.get(env_key, default)

    # Log the retrieval (but not the value for sensitive data)
    if value is not None and value != default:
        if sensitive:
            logger.debug(f"Retrieved sensitive setting from environment: {key}=******")
        else:
            logger.debug(f"Retrieved setting from environment: {key}={value}")

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
        default_settings = {
            "output_path": "./output",
            "person_list_path": "./person_lists",
            "unique_filenames": False,  # Boolean default
            "output_columns": [
                "Name",
                "Title",
                "Creator",
                "Publication Year",
                "Identifier",
                "URL",
                "Authors",
                "Citation Count",
            ],
            "default_database": "PubMed",
            # Add other non-sensitive defaults here
            "pubmed_api_key": None,  # Placeholder for API key
            "dnb_access_token": None,  # Placeholder for API key
        }
        settings = default_settings.copy()

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
            "output_path": get_env_setting("OUTPUT_PATH", settings["output_path"], sensitive=False),
            "person_list_path": get_env_setting(
                "PERSON_LIST_PATH", settings["person_list_path"], sensitive=False
            ),
            "default_database": get_env_setting(
                "DEFAULT_DATABASE", settings["default_database"], sensitive=False
            ),
        }

        # Update settings with environment values
        settings.update(env_settings)

        # Ensure boolean conversion for unique_filenames if from env or file
        if isinstance(settings.get("unique_filenames"), str):
            settings["unique_filenames"] = settings["unique_filenames"].lower() == "true"

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
            "output_columns": [
                "Name",
                "Title",
                "Creator",
                "Publication Year",
                "Identifier",
                "URL",
                "Authors",
                "Citation Count",
            ],
            "default_database": "PubMed",
            "pubmed_api_key": None,
            "dnb_access_token": None,
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
            del safe_settings["pubmed_api_key"]

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


# Add DEFAULT_SETTINGS to be accessible by models.py
DEFAULT_SETTINGS = {
    "output_path": "./output",
    "person_list_path": "./person_lists",
    "unique_filenames": False,
    "output_columns": [
        "Name",
        "Title",
        "Creator",
        "Publication Year",
        "Identifier",
        "URL",
        "Authors",
        "Citation Count",
    ],
    "default_database": "PubMed",
}


def get_default_settings():
    return DEFAULT_SETTINGS.copy()
