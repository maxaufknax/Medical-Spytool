#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Configuration module
This module handles loading and saving application settings.
"""

import os
import json
import logging
from pathlib import Path
from datetime import timedelta # Ensure timedelta is imported for PERMANENT_SESSION_LIFETIME

# Initialize logger early
logger = logging.getLogger(__name__)
# BasicConfig should ideally be set up in app.py, but for standalone config use:
if not logger.hasHandlers(): # Avoid adding multiple handlers if already configured
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s : %(message)s')

# --- Define Paths and Create Directories at Module Level ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INSTANCE_PATH = PROJECT_ROOT / 'instance'
SESSION_FILE_DIR_PATH = INSTANCE_PATH / 'flask_session'
LOG_DIR_PATH = PROJECT_ROOT / 'logs' # Changed from 'log' to 'logs' to match app.py
DEFAULT_SQLITE_DB_PATH = INSTANCE_PATH / 'medicalspy.db'
TEST_SQLITE_DB_PATH = INSTANCE_PATH / 'test_medicalspy.db'
APP_CONFIG_JSON_PATH = INSTANCE_PATH / "medicalspy_config.json"

# Ensure critical directories exist immediately
INSTANCE_PATH.mkdir(parents=True, exist_ok=True)
SESSION_FILE_DIR_PATH.mkdir(parents=True, exist_ok=True)
LOG_DIR_PATH.mkdir(parents=True, exist_ok=True)

# Ensure output and person_list directories (app-specific, potentially configurable)
# Default locations relative to PROJECT_ROOT
DEFAULT_OUTPUT_PATH_STR = "./output"
DEFAULT_PERSON_LIST_PATH_STR = "./person_lists"

OUTPUT_PATH_ENV = os.environ.get("OUTPUT_PATH", DEFAULT_OUTPUT_PATH_STR)
PERSON_LIST_PATH_ENV = os.environ.get("PERSON_LIST_PATH", DEFAULT_PERSON_LIST_PATH_STR)

APP_OUTPUT_PATH = Path(OUTPUT_PATH_ENV) if Path(OUTPUT_PATH_ENV).is_absolute() else PROJECT_ROOT / OUTPUT_PATH_ENV
APP_PERSON_LIST_PATH = Path(PERSON_LIST_PATH_ENV) if Path(PERSON_LIST_PATH_ENV).is_absolute() else PROJECT_ROOT / PERSON_LIST_PATH_ENV

APP_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
APP_PERSON_LIST_PATH.mkdir(parents=True, exist_ok=True)

logger.info(f"PROJECT_ROOT: {PROJECT_ROOT}")
logger.info(f"Instance path ensured at {INSTANCE_PATH}")
logger.info(f"Session file directory ensured at {SESSION_FILE_DIR_PATH}")
logger.info(f"Logs directory ensured at {LOG_DIR_PATH}")
logger.info(f"Default DB path: {DEFAULT_SQLITE_DB_PATH}")
logger.info(f"App output path ensured at {APP_OUTPUT_PATH}")
logger.info(f"App person list path ensured at {APP_PERSON_LIST_PATH}")

# Load environment variables from .env file if available at the project root
try:
    from dotenv import load_dotenv
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.info(f"Environment variables loaded from {env_path}")
    else:
        logger.info(f".env file not found at {env_path}.")
except ImportError:
    logger.info("python-dotenv not installed, .env file will not be loaded.")


# --- Flask Configuration Classes ---
class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_secret_key_that_should_be_changed_in_production_environment'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LANGUAGES = ['en', 'de']
    BABEL_DEFAULT_LOCALE = 'de'
    SESSION_TYPE = 'filesystem' 
    SESSION_FILE_DIR = str(SESSION_FILE_DIR_PATH) 
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    LOG_FILE = os.environ.get('LOG_FILE', str(LOG_DIR_PATH / 'medicalspy.log'))

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DEFAULT_SQLITE_DB_PATH}'
    
    # Application-specific settings (can be further customized by load_app_settings)
    OUTPUT_PATH = str(APP_OUTPUT_PATH)
    PERSON_LIST_PATH = str(APP_PERSON_LIST_PATH)
    UNIQUE_FILENAMES = os.environ.get("UNIQUE_FILENAMES", "False").lower() == "true"
    DEFAULT_DATABASE = os.environ.get("DEFAULT_DATABASE", "PubMed")
    PUBMED_API_KEY = os.environ.get("PUBMED_API_KEY")
    DNB_ACCESS_TOKEN = os.environ.get("DNB_ACCESS_TOKEN")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = False 
    # SQLALCHEMY_DATABASE_URI = f'sqlite:///{DEFAULT_SQLITE_DB_PATH}' # Keep it simple for dev


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    if Config.SECRET_KEY == 'a_very_secret_key_that_should_be_changed_in_production_environment':
        logger.warning("PRODUCTION WARNING: Default SECRET_KEY is used. Set a strong SECRET_KEY environment variable for production.")
    # SQLALCHEMY_DATABASE_URI = os.environ.get('PROD_DATABASE_URL') # Should be set in environment


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False 
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or f'sqlite:///{TEST_SQLITE_DB_PATH}'
    WTF_CSRF_ENABLED = False  # Often disabled for testing forms directly
    SESSION_TYPE = 'filesystem' 
    SESSION_FILE_DIR = str(SESSION_FILE_DIR_PATH) # Ensure it's a string
    # For testing, could also use 'sqlite:///:memory:' for SQLALCHEMY_DATABASE_URI if preferred and no persistence needed.


# --- Functions for managing dynamic application settings (e.g., from JSON file) ---
# These are distinct from Flask's core config and are more for user-level preferences.

def get_env_setting(key, default=None, sensitive=False):
    # This helper is mostly for the load_app_settings function below.
    env_key = key.upper()
    value = os.environ.get(env_key, default)
    # logger.debug(f"Env setting: {key} -> {'******' if sensitive else value}") # Can be noisy
    return value

DEFAULT_APP_SETTINGS_VALUES = {
    "output_path": Config.OUTPUT_PATH, # Use resolved path from Config
    "person_list_path": Config.PERSON_LIST_PATH, # Use resolved path from Config
    "unique_filenames": Config.UNIQUE_FILENAMES,
    "output_columns": [
        "Name", "Title", "Creator", "Publication Year", 
        "Identifier", "URL", "Authors", "Citation Count",
    ],
    "default_database": Config.DEFAULT_DATABASE,
    "pubmed_api_key": Config.PUBMED_API_KEY, # Will be None if not in env
    "dnb_access_token": Config.DNB_ACCESS_TOKEN, # Will be None if not in env
}

def get_default_app_settings():
    return DEFAULT_APP_SETTINGS_VALUES.copy()

def load_app_settings():
    """
    Loads application-specific settings.
    Priority: Environment Variables > JSON Config File > Class Defaults (from Config).
    """
    settings = get_default_app_settings() # Start with defaults from Config class

    if APP_CONFIG_JSON_PATH.exists():
        try:
            with open(APP_CONFIG_JSON_PATH, "r", encoding="utf-8") as f:
                file_settings = json.load(f)
                # Update settings: file settings override class defaults if not set by env
                for key, value in file_settings.items():
                    if os.environ.get(key.upper()) is None: # Only use if not set by env
                        settings[key] = value
            logger.info(f"App settings updated from {APP_CONFIG_JSON_PATH}")
        except Exception as e:
            logger.error(f"Error loading app settings from {APP_CONFIG_JSON_PATH}: {e}")

    # Environment variables override file and class defaults for these specific settings
    settings["output_path"] = os.environ.get("OUTPUT_PATH", settings["output_path"])
    settings["person_list_path"] = os.environ.get("PERSON_LIST_PATH", settings["person_list_path"])
    settings["default_database"] = os.environ.get("DEFAULT_DATABASE", settings["default_database"])
    settings["pubmed_api_key"] = os.environ.get("PUBMED_API_KEY", settings["pubmed_api_key"])
    settings["dnb_access_token"] = os.environ.get("DNB_ACCESS_TOKEN", settings["dnb_access_token"])
    
    unique_filenames_env = os.environ.get("UNIQUE_FILENAMES")
    if unique_filenames_env is not None:
        settings["unique_filenames"] = unique_filenames_env.lower() == 'true'
    elif isinstance(settings.get("unique_filenames"), str): # from JSON file
         settings["unique_filenames"] = settings["unique_filenames"].lower() == "true"
    
    # Ensure paths are absolute after loading from all sources
    if not Path(settings["output_path"]).is_absolute():
        settings["output_path"] = str(PROJECT_ROOT / settings["output_path"])
    if not Path(settings["person_list_path"]).is_absolute():
        settings["person_list_path"] = str(PROJECT_ROOT / settings["person_list_path"])

    # Ensure directories exist based on the final settings
    Path(settings["output_path"]).mkdir(parents=True, exist_ok=True)
    Path(settings["person_list_path"]).mkdir(parents=True, exist_ok=True)
    
    return settings

def save_app_settings(app_settings):
    """Saves non-sensitive application-specific settings to JSON file."""
    safe_settings_to_save = {}
    sensitive_keys = ["pubmed_api_key", "dnb_access_token", "SECRET_KEY"] # SECRET_KEY should not be here
    
    # Only save settings that are part of the "default app settings" structure and non-sensitive
    for key, value in app_settings.items():
        if key in DEFAULT_APP_SETTINGS_VALUES and key not in sensitive_keys:
            safe_settings_to_save[key] = value
            
    try:
        APP_CONFIG_JSON_PATH.parent.mkdir(parents=True, exist_ok=True) # Ensure instance dir exists
        with open(APP_CONFIG_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(safe_settings_to_save, f, indent=4)
        logger.info(f"Non-sensitive app settings saved to {APP_CONFIG_JSON_PATH}")
    except Exception as e:
        logger.error(f"Error saving app settings to {APP_CONFIG_JSON_PATH}: {e}")

logger.info("backend.config module loaded and processed.")
# To be used by app.py for loading these app-specific settings if needed:
# current_app_settings = load_app_settings()
