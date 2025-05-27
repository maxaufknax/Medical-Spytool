"""
Base Connector Module

This module provides the base class for all database connectors.
Each specific database connector should inherit from this class
and implement the required methods.
"""

from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class BaseConnector:
    """Base class for database connectors."""
    
    def __init__(self, api_key: str = None, settings: dict = None):
        """
        Initialize the connector.
        
        Args:
            api_key (str, optional): API key for the database service
            settings (dict, optional): Additional settings for the connector
        """
        self.api_key = api_key
        self.settings = settings or {}
        self.max_results = 100
        
    def construct_query(self, search_term: str, **kwargs) -> str:
        """
        Construct a query string for the database.
        
        Args:
            search_term (str): The main search term
            **kwargs: Additional search parameters
                - person_names (list): List of person names to include in search
                - additional_terms (str): Additional search terms
                - date_range (dict): Date range with 'start' and 'end' keys
                - language (str): Language filter
                - pub_type (str): Publication type filter
            
        Returns:
            str: The constructed query string
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement construct_query()")
        
    def search(self, search_term: str = None, query: str = None, params: Dict[str, Any] = None, 
               person_names: List[str] = None, max_results: int = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Perform a search in the database.
        
        This method supports two calling conventions:
        1. search(query, params) - Traditional interface
        2. search(search_term, person_names, max_results, **kwargs) - Interface used in main.py
        
        Args:
            search_term (str, optional): The main search term
            query (str, optional): A pre-constructed query string
            params (dict, optional): Additional search parameters
            person_names (list, optional): List of person names to include in search
            max_results (int, optional): Maximum number of results to return
            **kwargs: Any additional parameters for the search
            
        Returns:
            list: List of search results as dictionaries
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement search()")
        
    def validate_api_key(self, api_key: str = None) -> bool:
        """
        Validate the API key.
        
        Args:
            api_key (str, optional): The API key to validate. If None, use the one from the instance.
            
        Returns:
            bool: True if the API key is valid, False otherwise
            
        Note:
            This is an optional method that subclasses can implement
            if they support API key validation.
        """
        return True  # Default implementation assumes no API key is needed
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the database.
        
        Returns:
            dict: A dictionary containing the test results including:
                - status: 'OK', 'Error', or 'Not Available'
                - message: A message describing the test result
                - response_time: The time it took to get a response (in seconds)
                
        Note:
            This method should be implemented by subclasses to provide
            more specific connection testing. The base implementation
            returns a generic "Not Implemented" status.
        """
        return {
            'status': 'Not Implemented',
            'message': 'Connection test not implemented for this database connector',
            'response_time': None
        }
        
    def format_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format and standardize search results.
        
        This method ensures all results have a consistent structure
        and all required fields are present.
        
        Args:
            results (list): The raw search results from the database
            
        Returns:
            list: Formatted and standardized results
            
        Note:
            This is a helper method that subclasses can override if needed.
            The base implementation returns the results as is.
        """
        standard_fields = [
            'Title', 'Authors', 'Journal', 'Publication Year', 'Publication Month',
            'Abstract', 'DOI', 'URL', 'Database', 'Publication Type', 'Language',
            'Keywords', 'Citation Count'
        ]
        
        formatted_results = []
        for result in results:
            # Ensure all standard fields exist (with None as default)
            formatted_result = {field: result.get(field) for field in standard_fields}
            
            # Copy any additional fields that aren't in the standard set
            for key, value in result.items():
                if key not in standard_fields:
                    formatted_result[key] = value
                    
            formatted_results.append(formatted_result)
            
        return formatted_results