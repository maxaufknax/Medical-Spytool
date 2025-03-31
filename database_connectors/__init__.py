"""
Database Connectors Package

This package provides connectors for various publication databases.
"""

from database_connectors.base_connector import DatabaseConnector
from database_connectors.pubmed_connector import PubMedConnector
from database_connectors.dnb_connector import DNBConnector
from database_connectors.scopus_connector import ScopusConnector
from database_connectors.wos_connector import WoSConnector
from database_connectors.gepris_connector import GEPRISConnector

# Register available database connectors
DATABASE_CONNECTORS = {
    "PubMed": PubMedConnector,
    "DNB": DNBConnector,
    "Scopus": ScopusConnector,
    "WoS": WoSConnector,
    "GEPRIS": GEPRISConnector
}

__all__ = [
    "DATABASE_CONNECTORS",
    "DatabaseConnector",
    "PubMedConnector",
    "DNBConnector",
    "ScopusConnector",
    "WoSConnector",
    "GEPRISConnector"
]