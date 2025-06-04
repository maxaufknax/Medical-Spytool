"""
Scopus Connector Module

This module provides functionality to search the Scopus database
using their API.
"""

from typing import List, Dict, Any, Optional, Union
import requests
import json
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from .base_connector import BaseConnector

logger = logging.getLogger(__name__)

class ScopusConnector(BaseConnector):
    """
    Connector for searching the Scopus database.
    """
    requires_api_key = True # Scopus API requires an API key
    
    def __init__(self, api_key: str = None, settings: dict = None):
        """Initialize the Scopus connector."""
        super().__init__(api_key, settings)
        self.base_url = "https://api.elsevier.com/content/search/scopus"
        self.max_results = 100
        self.name = "Scopus" # Added for api_key_manager
        
    def construct_query(self, search_term: str, **kwargs) -> str:
        """
        Construct a Scopus API query string.
        
        Args:
            search_term (str): The main search term
            **kwargs: Additional search parameters
                - additional_terms (str): Additional search terms
                - date_range (dict): Date range with 'start' and 'end' keys
                - language (str): Language filter
                - pub_type (str): Publication type filter
                - field (str): Specific field to search in
                - person_names (list): List of person names to include in search
                
        Returns:
            str: The constructed query string
        """
        query_parts = []
        
        # Add main search term if provided
        if search_term:
            # Check if field-specific search is requested
            field = kwargs.get('field', '').lower()
            search_field = kwargs.get('search_field', '').lower()
            
            if field and field != 'all fields' and field != 'alle felder':
                # Map common fields to Scopus field codes
                field_map = {
                    'titel': 'TITLE',
                    'title': 'TITLE',
                    'autor': 'AUTH',
                    'author': 'AUTH',
                    'abstract': 'ABS',
                    'keywords': 'KEY',
                    'schlagwort': 'KEY',
                    'affiliation': 'AFFIL'
                }
                if field in field_map:
                    query_parts.append(f"{field_map[field]}({search_term})")
                else:
                    query_parts.append(f"ALL({search_term})")
            elif search_field and search_field != 'all fields' and search_field != 'alle felder':
                # Map common fields to Scopus field codes
                field_map = {
                    'titel': 'TITLE',
                    'title': 'TITLE',
                    'autor': 'AUTH',
                    'author': 'AUTH',
                    'abstract': 'ABS',
                    'keywords': 'KEY',
                    'schlagwort': 'KEY',
                    'affiliation': 'AFFIL'
                }
                if search_field in field_map:
                    query_parts.append(f"{field_map[search_field]}({search_term})")
                else:
                    query_parts.append(f"ALL({search_term})")
            else:
                query_parts.append(f"ALL({search_term})")
        
        # Add person names if provided
        person_names = kwargs.get('person_names', [])
        if person_names and isinstance(person_names, list):
            author_queries = []
            for person in person_names:
                if isinstance(person, str) and person.strip():
                    # Format author query for Scopus
                    author_queries.append(f"AUTH({person.strip()})")
            
            if author_queries:
                query_parts.append(" OR ".join(author_queries))
        
        # Add additional terms if provided
        additional_terms = kwargs.get('additional_terms')
        if additional_terms:
            query_parts.append(f"ALL({additional_terms})")
            
        # Add date range if provided
        date_range = kwargs.get('date_range')
        if date_range:
            start_date = date_range.get('start')
            end_date = date_range.get('end')
            if start_date and end_date:
                query_parts.append(f"PUBYEAR BET {start_date} {end_date}")
        
        # Alternative: check for start_date and end_date directly (from form submission)
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        if start_date and end_date:
            query_parts.append(f"PUBYEAR BET {start_date} {end_date}")
                
        # Add language filter if provided
        language = kwargs.get('language')
        if language:
            query_parts.append(f"LANGUAGE({language})")
            
        # Add publication type filter if provided
        pub_type = kwargs.get('pub_type')
        if pub_type:
            query_parts.append(f"DOCTYPE({pub_type})")
            
        # Combine all parts with AND
        return " AND ".join(query_parts) if query_parts else "*"
        
    def search(self, search_term: str = None, query: str = None, params: Dict[str, Any] = None, 
               person_names: List[str] = None, max_results: int = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Perform a search using the Scopus API.
        
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
        """
        try:
            # Set the maximum number of results if provided
            if max_results:
                self.max_results = max_results
            
            # Get the API key from kwargs, app_config, or self
            # Ensure self.api_key is used if available and validated
            current_api_key = self.api_key or kwargs.get('api_key') or kwargs.get('scopus_api_key')

            if not current_api_key:
                logger.error("Scopus API key is missing.")
                raise ValueError("Scopus API key is required for searching.")
            
            # If a query is not provided directly, construct it from search_term and other parameters
            if not query:
                # Combine all search parameters into kwargs
                combined_kwargs = kwargs.copy()
                if person_names:
                    combined_kwargs['person_names'] = person_names
                
                # Construct the query
                query = self.construct_query(search_term, **combined_kwargs)
            
            logger.info(f"Scopus search query: {query}")
            
            headers = {
                'X-ELS-APIKey': current_api_key,
                'Accept': 'application/json'
            }
            
            search_params = {
                'query': query,
                'count': str(self.max_results),
                'view': 'COMPLETE'  # Get complete record information
            }
            
            # Update with any additional parameters
            if params:
                search_params.update(params)
                
            response = requests.get(self.base_url, headers=headers, params=search_params)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if 'service-error' in data:
                error = data['service-error']
                error_msg = error.get('statusText', 'Unknown API error')
                logger.error(f"Scopus API error: {error_msg}")
                raise Exception(f"Scopus API error: {error_msg}")
            
            # Extract search results
            entries = data.get('search-results', {}).get('entry', [])
            results = []
            
            for entry in entries:
                try:
                    # Extract authors
                    authors = []
                    for author in entry.get('author', []):
                        auth_name = author.get('authname', '')
                        if auth_name:
                            authors.append(auth_name)
                    authors_text = "; ".join(authors) if authors else "Unknown"
                    
                    # Extract publication date
                    pub_date = entry.get('prism:coverDate', '')
                    pub_year = pub_date.split('-')[0] if pub_date and '-' in pub_date else None
                    pub_month = pub_date.split('-')[1] if pub_date and '-' in pub_date and len(pub_date.split('-')) > 1 else None
                    
                    # Extract affiliations
                    affiliations = []
                    for aff in entry.get('affiliation', []):
                        aff_name = aff.get('affilname', '')
                        if aff_name:
                            affiliations.append(aff_name)
                    affiliations_text = "; ".join(affiliations) if affiliations else None
                    
                    # Extract keywords
                    keywords_text = None
                    if entry.get('authkeywords'):
                        keywords = entry.get('authkeywords').split('|')
                        keywords_text = "; ".join(keywords) if keywords else None
                    
                    # Build result dictionary
                    result = {
                        'Title': entry.get('dc:title'),
                        'Authors': authors_text,
                        'Journal': entry.get('prism:publicationName'),
                        'Publication Year': pub_year,
                        'Publication Month': pub_month,
                        'DOI': entry.get('prism:doi'),
                        'Abstract': entry.get('dc:description'),
                        'Citation Count': entry.get('citedby-count'),
                        'Institute': affiliations_text,
                        'Keywords': keywords_text,
                        'Database': 'Scopus',
                        'URL': entry.get('prism:url'),
                        'Publication Type': entry.get('subtypeDescription'),
                        'Language': entry.get('language'),
                        'ISSN': entry.get('prism:issn'),
                        'Source ID': entry.get('source-id')
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error parsing Scopus entry: {e}", exc_info=True)
                    continue
            
            logger.info(f"Found {len(results)} Scopus results")
            return self.format_results(results)
            
        except requests.RequestException as e:
            logger.error(f"Scopus API request error: {e}", exc_info=True)
            raise Exception(f"Scopus API request error: {str(e)}")
        except Exception as e:
            logger.error(f"Scopus search error: {e}", exc_info=True)
            raise Exception(f"Scopus search error: {str(e)}")
            
    def validate_api_key(self, api_key: str = None) -> bool:
        """
        Validate the Scopus API key by making a test request.
        
        Args:
            api_key (str, optional): The API key to validate. If None, use the one from the instance.
            
        Returns:
            bool: True if the API key is valid, False otherwise
        """
        # Use provided API key or fall back to instance API key
        key_to_validate = api_key if api_key else self.api_key
        
        if not key_to_validate:
            return False
            
        try:
            headers = {
                'X-ELS-APIKey': key_to_validate,
                'Accept': 'application/json'
            }
            
            # Make a minimal test query
            test_params = {
                'query': 'test',
                'count': '1'
            }
            
            response = requests.get(self.base_url, headers=headers, params=test_params)
            
            # API key is valid if we get a successful response
            return response.ok and 'service-error' not in response.json()
            
        except Exception as e:
            logger.error(f"API key validation error: {e}", exc_info=True)
            return False
            
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the Scopus API.
        
        Returns:
            dict: A dictionary containing the test results
        """
        import time
        
        try:
            start_time = time.time()
            
            # Check if API key is available
            if not self.api_key:
                return {
                    'status': 'Error',
                    'message': 'No Scopus API key provided',
                    'response_time': None
                }
            
            # Make a simple test query
            test_query = "medicine"
            headers = {
                "X-ELS-APIKey": self.api_key,
                "Accept": "application/json"
            }
            params = {
                "query": test_query,
                "count": "1"
            }
            
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            
            response_time = time.time() - start_time
            
            if response.ok:
                try:
                    data = response.json()
                    total_results = data.get('search-results', {}).get('opensearch:totalResults', 0)
                    
                    return {
                        'status': 'OK',
                        'message': f'Successfully connected to Scopus. Found {total_results} results for "medicine"',
                        'response_time': round(response_time, 2)
                    }
                except json.JSONDecodeError:
                    return {
                        'status': 'Warning',
                        'message': 'Connected to Scopus, but received invalid JSON response',
                        'response_time': round(response_time, 2)
                    }
            else:
                error_msg = response.text
                try:
                    error_json = response.json()
                    if 'error-response' in error_json:
                        error_msg = error_json['error-response'].get('error-message', response.text)
                except:
                    pass
                
                return {
                    'status': 'Error',
                    'message': f'Error connecting to Scopus: {response.status_code} - {error_msg}',
                    'response_time': round(response_time, 2)
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'Error',
                'message': 'Connection to Scopus timed out',
                'response_time': None
            }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'Error',
                'message': 'Network error: Unable to connect to Scopus',
                'response_time': None
            }
        except Exception as e:
            logger.error(f"Scopus connection test error: {e}", exc_info=True)
            return {
                'status': 'Error',
                'message': f'Error testing Scopus connection: {str(e)}',
                'response_time': None
            }