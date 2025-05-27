"""
Database Connectors Package

This package provides connectors for various publication databases.
"""

from database_connectors.base_connector import BaseConnector
from database_connectors.dnb_connector import DNBConnector
from database_connectors.pubmed_connector import PubMedConnector
from database_connectors.scopus_connector import ScopusConnector
from database_connectors.wos_connector import WoSConnector
from database_connectors.gepris_connector import GeprisConnector

# Dictionary mapping database names to their connector classes
DATABASE_CONNECTORS = {
    'DNB': DNBConnector,
    'PubMed': PubMedConnector,
    'Scopus': ScopusConnector,
    'WoS': WoSConnector,
    'GEPRIS': GeprisConnector
}

__all__ = [
    "DATABASE_CONNECTORS",
    "BaseConnector",
    "DNBConnector",
    "PubMedConnector",
    "ScopusConnector",
    "WoSConnector",
    "GeprisConnector"
]