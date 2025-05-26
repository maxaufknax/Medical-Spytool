#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Connectors Package
This package initializes and exports the database connectors and the factory function.
"""
import logging

logger = logging.getLogger(__name__)

# Import the factory function from utils.py within this package (backend/connectors/utils.py)
try:
    from .utils import get_connector_for_database
except ImportError as e:
    logger.error(f"CONNECTORS INIT ERROR: Failed to import get_connector_for_database from .utils. Error: {e}. Defining placeholder.")
    # This placeholder helps in allowing the application to start for further debugging if utils.py has issues.
    def get_connector_for_database(database_name, api_key_override=None): # pragma: no cover
        logger.critical(f"Placeholder get_connector_for_database called for {database_name} due to import error in backend.connectors.__init__.")
        raise ImportError(f"get_connector_for_database could not be imported from .utils: {e}")

# Import the connector classes themselves from backend/connectors_module.py (the file)
# Since __init__.py is in backend/connectors/ (package) and connectors_module.py (file) is in backend/,
# the relative import is `from ..connectors_module import ...`
try:
    from ..connectors_module import DatabaseConnector, PubMedConnector, DNBConnector
    # If there are other connectors in backend/connectors_module.py, import them here too.
    logger.info("Successfully imported DatabaseConnector, PubMedConnector, DNBConnector from ..connectors_module.")
except ImportError as e:
    logger.error(f"CONNECTORS INIT CRITICAL ERROR: Failed to import connector classes from ..connectors_module (backend/connectors_module.py). Error: {e}. Defining placeholders. Functionality will be impaired.")
    # Define placeholders if import fails, to allow the package to load for inspection.
    class DatabaseConnector: # pragma: no cover
        def __init__(self, api_key=None): self.name = "DatabaseConnector (Placeholder - __init__.py)"
    class PubMedConnector(DatabaseConnector): # pragma: no cover
        def __init__(self, api_key=None): super().__init__(api_key); self.name = "PubMed (Placeholder - __init__.py)"
    class DNBConnector(DatabaseConnector): # pragma: no cover
        def __init__(self, api_key=None): super().__init__(api_key); self.name = "DNB (Placeholder - __init__.py)"
    logger.warning("Using placeholder connector classes in backend.connectors.__init__ due to import error from ..connectors_module.")


__all__ = [
    'get_connector_for_database',
    'DatabaseConnector',
    'PubMedConnector',
    'DNBConnector',
    # Add other exported connector class names here if they are imported above
]

logger.info(f"backend.connectors package initialized. Available exports: {__all__}")
