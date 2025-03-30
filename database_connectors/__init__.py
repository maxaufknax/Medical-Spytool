"""
Database Connectors Package

This package provides connectors for various publication databases.
"""

from database_connectors.base_connector import DatabaseConnector
from database_connectors.pubmed_connector import PubMedConnector
from database_connectors.dnb_connector import DNBConnector

# Register available database connectors
DATABASE_CONNECTORS = {
    "PubMed": PubMedConnector,
    "DNB": DNBConnector
}

__all__ = [
    "DATABASE_CONNECTORS",
    "DatabaseConnector",
    "PubMedConnector",
    "DNBConnector"
]