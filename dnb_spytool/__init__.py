"""
DNB Spytool - German National Library Search Tool

A comprehensive Python application for searching, retrieving, saving, and analyzing 
publications from the German National Library (Deutsche Nationalbibliothek - DNB).
"""

__version__ = "1.9.0"
__author__ = "DNB Spytool Contributors"
__email__ = "support@dnbspytool.com"
__description__ = "German National Library search and analysis tool"

from .api.dnb_client import DNBClient
from .api.parser import MARCXMLParser
from .analytics.analyzer import PublicationAnalyzer
from .analytics.visualizer import PublicationVisualizer
from .utils.exporters import DataExporter
from .utils.validators import InputValidator

__all__ = [
    'DNBClient', 
    'MARCXMLParser',
    'PublicationAnalyzer', 
    'PublicationVisualizer',
    'DataExporter',
    'InputValidator'
]
