#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Configuration module
This module handles loading and saving application settings.
"""

import os
import json
import logging

# Configuration file
CONFIG_FILE = "medicalspy_config.json"

logger = logging.getLogger("MedicalSpy")

def load_settings():
    """
    Load settings from the configuration file.
    
    Returns:
        dict: Settings dictionary
    """
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
            logger.info("Settings loaded from configuration file.")
            return settings
        else:
            # Default settings
            settings = {
                "output_path": "./output",
                "person_list_path": "./person_lists",
                "unique_filenames": False,
                "pubmed_api_key": "",
                "output_columns": [
                    "Name", "Titel", "Creator", "Erscheinungsjahr", "Identifier",
                    "URL", "Autoren", "Veröffentlichungsjahr", "Zitationsanzahl"
                ],
                "default_database": "PubMed"
            }
            save_settings(settings)
            logger.info("Default settings created.")
            return settings
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        # Return default settings in case of error
        return {
            "output_path": "./output",
            "person_list_path": "./person_lists",
            "unique_filenames": False,
            "pubmed_api_key": "",
            "output_columns": [
                "Name", "Titel", "Creator", "Erscheinungsjahr", "Identifier",
                "URL", "Autoren", "Veröffentlichungsjahr", "Zitationsanzahl"
            ],
            "default_database": "PubMed"
        }

def save_settings(settings):
    """
    Save settings to the configuration file.
    
    Args:
        settings (dict): Settings to save
    """
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
        logger.info("Settings saved to configuration file.")
    except Exception as e:
        logger.error(f"Error saving settings: {e}")

def ensure_directories(settings):
    """
    Ensure that required directories exist.
    
    Args:
        settings (dict): Application settings
    """
    try:
        os.makedirs(settings["output_path"], exist_ok=True)
        os.makedirs(settings["person_list_path"], exist_ok=True)
        logger.info("Required directories have been created.")
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
