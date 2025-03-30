"""
Base Database Connector

This module defines the base class for all database connectors.
Each database connector class should inherit from this base class
and implement the required methods.
"""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class DatabaseConnector(ABC):
    """
    Abstract base class for database connectors.
    
    This class defines the interface that all database connectors must implement.
    """
    
    def __init__(self, api_key=None, settings=None):
        """
        Initialize the database connector.
        
        Args:
            api_key (str, optional): API key for the database.
            settings (dict, optional): Additional settings for the connector.
        """
        self.api_key = api_key
        self.settings = settings or {}
        self.name = "Generic Database"
        self.max_results_per_page = 100
        self.search_fields = []
        
    @abstractmethod
    def search(self, query, params=None, log_widget=None):
        """
        Search the database with the given query.
        
        Args:
            query (str): The search query.
            params (dict, optional): Additional search parameters.
            log_widget (tkinter.Text, optional): Widget for logging messages.
            
        Returns:
            list: List of search results.
        """
        raise NotImplementedError("This method must be implemented in subclasses")
        
    @abstractmethod
    def parse_results(self, response, name=None, log_widget=None):
        """
        Parse the search results from the database response.
        
        Args:
            response: The response from the database.
            name (str, optional): Name associated with the search.
            log_widget (tkinter.Text, optional): Widget for logging messages.
            
        Returns:
            list: List of parsed results.
        """
        raise NotImplementedError("This method must be implemented in subclasses")
        
    def get_citation_count(self, identifier):
        """
        Get the citation count for a publication.
        
        Args:
            identifier (str): The publication identifier.
            
        Returns:
            str or int: The citation count or "N/A" if not available.
        """
        return "N/A"
    
    def get_available_fields(self):
        """
        Get the list of available search fields.
        
        Returns:
            list: List of search field names.
        """
        return self.search_fields
        
    def construct_query(self, base_query, additional_terms="", date_range=None, 
                        language=None, pub_type=None, field=None):
        """
        Construct a query with the given parameters.
        
        Args:
            base_query (str): The base search query.
            additional_terms (str, optional): Additional search terms.
            date_range (dict, optional): Date range with 'start' and 'end' keys.
            language (str, optional): Language filter.
            pub_type (str, optional): Publication type filter.
            field (str, optional): Field to search in.
            
        Returns:
            str: The constructed query.
        """
        query = base_query
        if additional_terms:
            query = f"({query}) AND ({additional_terms})"
        return query
