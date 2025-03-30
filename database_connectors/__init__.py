"""
Database Connectors Package

This package contains database connector classes for various academic databases.
Each connector follows a common interface defined in the base_connector module.
"""

from database_connectors.base_connector import DatabaseConnector
from database_connectors.pubmed_connector import PubMedConnector
from database_connectors.dnb_connector import DNBConnector

# Dictionary to map database names to connector classes
DATABASE_CONNECTORS = {
    "PubMed": PubMedConnector,
    "DNB": DNBConnector,
}

__all__ = ['DatabaseConnector', 'PubMedConnector', 'DNBConnector', 'DATABASE_CONNECTORS']
