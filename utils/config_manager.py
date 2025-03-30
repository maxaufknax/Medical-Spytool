"""
Configuration Manager

This module provides functions for loading and saving configuration settings.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    'output_path': './output',
    'person_list_path': './person_lists',
    'unique_filenames': True,
    'pubmed_api_key': '',
    'dnb_api_key': '',
    'default_database': 'PubMed',
    'output_columns': [
        "Database", "Name", "Title", "Publication Year", "Authors", 
        "Identifier", "URL", "Citation Count"
    ]
}

def load_settings():
    """
    Load application settings from file.
    
    Returns:
        dict: Application settings.
    """
    config_file = 'medicalspytool_config.json'
    
    # If config file doesn't exist, create a default one
    if not os.path.exists(config_file):
        logger.info(f"Creating default configuration file: {config_file}")
        return save_settings(DEFAULT_CONFIG)
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logger.info(f"Loaded configuration from {config_file}")
            
            # Update with any missing default settings
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
                    
            return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}", exc_info=True)
        return DEFAULT_CONFIG

def save_settings(config):
    """
    Save application settings to file.
    
    Args:
        config (dict): Application settings.
        
    Returns:
        dict: The config that was saved.
    """
    config_file = 'medicalspytool_config.json'
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
            logger.info(f"Saved configuration to {config_file}")
        return config
    except Exception as e:
        logger.error(f"Error saving configuration: {e}", exc_info=True)
        return config

def ensure_directories(config):
    """
    Ensure that necessary directories exist.
    
    Args:
        config (dict): Application settings.
    """
    try:
        # Ensure output directory exists
        output_path = config.get('output_path', './output')
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            logger.info(f"Created output directory: {output_path}")
            
        # Ensure person list directory exists
        person_list_path = config.get('person_list_path', './person_lists')
        if not os.path.exists(person_list_path):
            os.makedirs(person_list_path)
            logger.info(f"Created person list directory: {person_list_path}")
            
    except Exception as e:
        logger.error(f"Error ensuring directories: {e}", exc_info=True)