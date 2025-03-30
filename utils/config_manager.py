"""
Configuration Manager

This module handles loading, saving, and managing application configuration.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

# Configuration file path
CONFIG_FILE = "medicalspytool_config.json"
DEFAULT_CONFIG_FILE = os.path.join("assets", "default_config.json")

def load_settings():
    """
    Load application settings from configuration file.
    
    Returns:
        dict: Application settings.
    """
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
            logger.info("Settings loaded from configuration file.")
            return settings
        elif os.path.exists(DEFAULT_CONFIG_FILE):
            with open(DEFAULT_CONFIG_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
            logger.info("Settings loaded from default configuration file.")
            save_settings(settings)  # Save the default settings to the main config file
            return settings
        else:
            # Create default settings
            settings = create_default_settings()
            save_settings(settings)
            logger.info("Default settings created.")
            return settings
    except Exception as e:
        logger.error(f"Error loading settings: {e}", exc_info=True)
        return create_default_settings()

def save_settings(settings):
    """
    Save application settings to configuration file.
    
    Args:
        settings (dict): Application settings to save.
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
        logger.info("Settings saved.")
    except Exception as e:
        logger.error(f"Error saving settings: {e}", exc_info=True)

def create_default_settings():
    """
    Create default application settings.
    
    Returns:
        dict: Default settings.
    """
    return {
        "output_path": "./output",
        "person_list_path": "./person_lists",
        "unique_filenames": False,
        "pubmed_api_key": "",
        "dnb_api_key": "",
        "output_columns": [
            "Database", "Name", "Title", "Publication Year", "Authors", 
            "Identifier", "URL", "Citation Count"
        ],
        "default_database": "PubMed"
    }

def ensure_directories(settings):
    """
    Ensure that necessary directories exist.
    
    Args:
        settings (dict): Application settings containing directory paths.
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(settings["output_path"], exist_ok=True)
        
        # Create person list directory if it doesn't exist
        os.makedirs(settings["person_list_path"], exist_ok=True)
        
        logger.info("Directories created.")
    except Exception as e:
        logger.error(f"Error creating directories: {e}", exc_info=True)

def get_api_key(database_name, settings):
    """
    Get the API key for the specified database.
    
    Args:
        database_name (str): Name of the database.
        settings (dict): Application settings.
        
    Returns:
        str: API key or empty string if not found.
    """
    key_name = f"{database_name.lower()}_api_key"
    return settings.get(key_name, "")
