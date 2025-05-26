#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Connector Utilities
This module provides the connector factory function.
"""
import logging
from flask import current_app

# Import connector classes from backend/connectors_module.py
# utils.py is in backend/connectors/
# connectors_module.py is in backend/
try:
    from ..connectors_module import DatabaseConnector, PubMedConnector, DNBConnector
except ImportError as e:
    # This block is for diagnostics if the import fails.
    # In a correctly structured environment, this import should succeed.
    logger = logging.getLogger(__name__)
    logger.error(
        f"UTILS.PY CRITICAL IMPORT ERROR: Could not import connector classes "
        f"from ..connectors_module (expected at backend/connectors_module.py). Error: {e}. "
        f"Using placeholders. This will likely break functionality."
    )
    # Define placeholder classes if the primary import fails, to allow the module to load for inspection.
    class DatabaseConnector: 
        def __init__(self, api_key=None): self.name = "DatabaseConnector (Placeholder - utils.py)"
        def search(self, query, params=None): logging.getLogger(__name__).error(f"Placeholder {self.name} search called"); return []
        def construct_query(self, base_query, **kwargs): return base_query
    class PubMedConnector(DatabaseConnector):
        def __init__(self, api_key=None): super().__init__(api_key); self.name = "PubMed (Placeholder - utils.py)"
    class DNBConnector(DatabaseConnector):
        def __init__(self, api_key=None): super().__init__(api_key); self.name = "DNB (Placeholder - utils.py)"

logger = logging.getLogger(__name__)

# This dictionary maps database names to their respective connector classes.
# It relies on PubMedConnector and DNBConnector being correctly imported above.
SUPPORTED_DATABASES_CONNECTORS = {
    "PubMed": PubMedConnector,
    "Deutsche Nationalbibliothek": DNBConnector,
    # Other connectors (e.g., ArxivConnector) would be added here
    # after being imported from ..connectors_module
}

def get_connector_for_database(database_name, api_key_override=None):
    """
    Factory function to get a connector instance for the specified database.
    Retrieves API keys from Flask app config if available, but can be overridden by api_key_override.
    """
    # Ensure logger is configured if this module is used early or in isolation
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)
        logger.debug("Logger basicConfig called in get_connector_for_database as no handlers were found.")

    logger.debug(f"get_connector_for_database called for: '{database_name}'")
    
    connector_class = SUPPORTED_DATABASES_CONNECTORS.get(database_name)
    
    if not connector_class:
        logger.error(f"No connector class registered for database: '{database_name}'. Check SUPPORTED_DATABASES_CONNECTORS.")
        raise ValueError(f"Unsupported database: {database_name}")
    
    # Check if the resolved class is one of the placeholders due to import error
    if "Placeholder" in getattr(connector_class, '__name__', ''):
         logger.critical(
             f"CRITICAL: Attempting to use a PLACEHOLDER connector for '{database_name}' because "
             f"the real connector class could not be imported into utils.py. "
             f"Functionality for this database will be impaired. "
             f"Check logs for 'UTILS.PY CRITICAL IMPORT ERROR'."
         )
         # Depending on desired behavior, could raise an error here.
         # For now, allowing placeholder use to proceed and reveal further issues if any.

    api_key = api_key_override 
    if api_key is None: 
        try:
            if current_app: 
                if database_name == "PubMed":
                    api_key = current_app.config.get("PUBMED_API_KEY")
                elif database_name == "Deutsche Nationalbibliothek":
                    api_key = current_app.config.get("DNB_ACCESS_TOKEN") 
                logger.debug(f"API key for '{database_name}' from app.config: {'SET' if api_key else 'NOT SET'}")
        except RuntimeError: 
            logger.warning(f"Not in Flask application context for API key retrieval for '{database_name}'.")
    else:
        logger.debug(f"API key for '{database_name}' was provided by override.")
    
    try:
        connector_instance = connector_class(api_key=api_key)
        instance_name = getattr(connector_instance, 'name', 'Unknown Connector Name')
        logger.info(f"Successfully created connector instance for '{database_name}' (Connector name: {instance_name}, API key {'provided/set' if api_key else 'not provided/not set'})")
        return connector_instance
    except Exception as e:
        # Log the actual class that failed to instantiate, if it's a placeholder
        actual_class_name = getattr(connector_class, '__name__', 'UnknownClass')
        logger.error(f"Failed to instantiate connector '{actual_class_name}' for database '{database_name}': {e}", exc_info=True)
        raise ValueError(f"Could not create connector for {database_name}: {e}")

if __name__ == '__main__':
    # This block is for direct execution testing of this utils.py file.
    logging.basicConfig(level=logging.DEBUG) 
    logger.info("connectors/utils.py executed directly for testing purposes.")
    logger.warning("Direct execution of utils.py: Relative imports like 'from ..connectors_module import ...' are expected to fail if run as a top-level script without the package context correctly set up.")
