"""
DNB (Deutsche Nationalbibliothek) Connector
This module provides functionality to search the DNB catalog.
"""
from typing import List, Dict, Any, Optional, Union
import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from .base_connector import BaseConnector

logger = logging.getLogger(__name__)

class DNBConnector(BaseConnector):
    """
    Connector for searching the Deutsche Nationalbibliothek (DNB) catalog.
    """
    requires_api_key = True # DNB SRU requires an access token (API key)
    
    def __init__(self, api_key: str = None, settings: dict = None):
        """Initialize the DNB connector."""
        super().__init__(api_key, settings)
        self.base_url = "https://services.dnb.de/sru/dnb"
        self.max_results = 100
        self.name = "DNB" # Added for api_key_manager
        
    def construct_query(self, search_term: str, **kwargs) -> str:
        """
        Construct a DNB SRU query string.
        
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
            # Check if there's a specific field to search in
            field = kwargs.get('field', '').lower()
            search_field = kwargs.get('search_field', '').lower()
            
            if field and field != 'alle felder':
                # Map common fields to DNB field codes
                field_map = {
                    'titel': 'tit',
                    'autor': 'per',
                    'schlagwort': 'sub',
                    'verlag': 'pub',
                    'isbn': 'num'
                }
                if field in field_map:
                    query_parts.append(f'{field_map[field]} all "{search_term}"')
                else:
                    query_parts.append(f'dnb.any all "{search_term}"')
            elif search_field and search_field != 'alle felder':
                # Map common fields to DNB field codes  
                field_map = {
                    'titel': 'tit',
                    'autor': 'per',
                    'schlagwort': 'sub',
                    'verlag': 'pub',
                    'isbn': 'num'
                }
                if search_field in field_map:
                    query_parts.append(f'{field_map[search_field]} all "{search_term}"')
                else:
                    query_parts.append(f'dnb.any all "{search_term}"')
            else:
                query_parts.append(f'dnb.any all "{search_term}"')
        
        # Add person names if provided
        person_names = kwargs.get('person_names', [])
        if person_names and isinstance(person_names, list):
            for person in person_names:
                if isinstance(person, str) and person.strip():
                    query_parts.append(f'per all "{person.strip()}"')
        
        # Add additional terms if provided
        additional_terms = kwargs.get('additional_terms')
        if additional_terms:
            query_parts.append(f'dnb.any all "{additional_terms}"')
            
        # Add date range if provided
        date_range = kwargs.get('date_range')
        if date_range:
            start_date = date_range.get('start')
            end_date = date_range.get('end')
            if start_date and end_date:
                date_query = f'jhr >= "{start_date}" and jhr <= "{end_date}"'
                query_parts.append(date_query)
        
        # Alternative: check for start_date and end_date directly (from form submission)
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        if start_date and end_date:
            date_query = f'jhr >= "{start_date}" and jhr <= "{end_date}"'
            query_parts.append(date_query)
                
        # Add language filter if provided
        language = kwargs.get('language')
        if language:
            query_parts.append(f'language="{language}"')
            
        # Add publication type filter if provided
        pub_type = kwargs.get('pub_type')
        if pub_type:
            query_parts.append(f'materialType="{pub_type}"')
            
        # Combine all parts with AND
        final_query = " AND ".join(query_parts) if query_parts else "*"
        
        return final_query
        
    def search(self, search_term: str = None, query: str = None, params: Dict[str, Any] = None, 
               person_names: List[str] = None, max_results: int = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Perform a search using the DNB SRU API.
        
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
            
            # If a query is not provided directly, construct it from search_term and other parameters
            if not query:
                # Combine all search parameters into kwargs
                combined_kwargs = kwargs.copy()
                if person_names:
                    combined_kwargs['person_names'] = person_names
                
                # Construct the query
                query = self.construct_query(search_term, **combined_kwargs)
            
            logger.info(f"DNB search query: {query}")
            
            search_params = {
                'operation': 'searchRetrieve',
                'version': '1.1',
                'recordSchema': 'MARC21-xml',
                'maximumRecords': str(self.max_results),
                'query': query,
                'accessToken': self.api_key # Add API key for DNB
            }
            
            # Update with any additional parameters
            if params:
                search_params.update(params)

            if not self.api_key:
                logger.error("DNB API key is missing.")
                raise ValueError("DNB API key is required for searching.")
            
            response = requests.get(self.base_url, params=search_params)
            response.raise_for_status()
            
            # Parse XML response
            soup = BeautifulSoup(response.content, 'xml')
            
            # Check for errors
            error = soup.find('diagnostics')
            if error:
                error_msg = error.get_text()
                logger.error(f"DNB API error: {error_msg}")
                raise Exception(f"DNB API error: {error_msg}")
            
            # Parse results
            records = soup.find_all('record')
            results = []
            
            for record in records:
                try:
                    # Extract basic metadata
                    title = self._get_marc_field(record, '245', 'a')
                    authors_list = self._get_marc_field_multiple(record, '100', 'a')
                    authors_list.extend(self._get_marc_field_multiple(record, '700', 'a') or [])
                    authors = "; ".join(authors_list) if authors_list else "Unknown"
                    
                    year = self._get_marc_field(record, '260', 'c')
                    if year:
                        # Clean up year format (remove brackets, copyright symbols, etc.)
                        year = year.strip('[]©c')
                        # Extract just the year (4 digits)
                        import re
                        year_match = re.search(r'\d{4}', year)
                        if year_match:
                            year = year_match.group(0)
                    
                    publisher = self._get_marc_field(record, '260', 'b')
                    isbn = self._get_marc_field(record, '020', 'a')
                    language = self._get_marc_field(record, '041', 'a')
                    
                    # Get subjects/keywords
                    subjects_list = self._get_marc_field_multiple(record, '650', 'a')
                    subjects = "; ".join(subjects_list) if subjects_list else None
                    
                    # Get publication type
                    pub_type = self._get_marc_field(record, '655', 'a')
                    
                    # Get abstract
                    abstract = self._get_marc_field(record, '520', 'a')
                    
                    # Build result dictionary
                    result = {
                        'Title': title,
                        'Authors': authors,
                        'Publication Year': year,
                        'Publisher': publisher,
                        'ISBN': isbn,
                        'Language': language,
                        'Database': 'DNB',
                        'Keywords': subjects,
                        'Publication Type': pub_type,
                        'Abstract': abstract,
                        'Citation Count': None  # DNB doesn't provide citation counts
                    }
                    
                    # Add URL if ISBN is available
                    if isbn:
                        result['URL'] = f"https://d-nb.info/{isbn}"
                    else:
                        # Try to get the DNB identifier
                        identifier = self._get_record_identifier(record)
                        if identifier:
                            result['URL'] = f"https://d-nb.info/{identifier}"
                            result['Identifier'] = identifier
                        else:
                            result['URL'] = "No URL"
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error parsing DNB record: {e}", exc_info=True)
                    continue
            
            logger.info(f"Found {len(results)} DNB results")
            return self.format_results(results)
            
        except requests.RequestException as e:
            logger.error(f"DNB API request error: {e}", exc_info=True)
            raise Exception(f"DNB API request error: {str(e)}")
        except Exception as e:
            logger.error(f"DNB search error: {e}", exc_info=True)
            raise Exception(f"DNB search error: {str(e)}")
            
    def _get_marc_field(self, record, field, subfield):
        """Helper method to get a single MARC field value."""
        field_elem = record.find(tag=field)
        if field_elem:
            subfield_elem = field_elem.find(code=subfield)
            if subfield_elem:
                return subfield_elem.get_text().strip()
        return None
        
    def _get_marc_field_multiple(self, record, field, subfield):
        """Helper method to get multiple values from a MARC field."""
        values = []
        fields = record.find_all(tag=field)
        for field_elem in fields:
            subfield_elem = field_elem.find(code=subfield)
            if subfield_elem:
                values.append(subfield_elem.get_text().strip())
        return values if values else []
        
    def _get_record_identifier(self, record):
        """Helper method to extract the DNB record identifier."""
        try:
            # Try to get control number
            control_field = record.find(tag='001')
            if control_field:
                return control_field.get_text().strip()
                
            # Alternatively, look in recordIdentifier
            record_id = record.find('recordIdentifier')
            if record_id:
                return record_id.get_text().strip()
                
            return None
        except Exception:
            return None
            
    def validate_api_key(self, api_key: str = None) -> bool:
        """
        Validate the API key by making a test request.
        
        Args:
            api_key (str, optional): The API key to validate. If None, use the one from the instance.
            
        Returns:
            bool: True if the API key is valid, False otherwise
        """
        try:
            # DNB generally doesn't require an API key for basic SRU searches,
            # but for real usage, an access token is often needed.
            # This validation checks if the key is provided and if a basic query works.
            key_to_validate = api_key if api_key else self.api_key
            if not key_to_validate:
                return False # API key is required
            
            # Make a simple test query
            test_query = "*"
            search_params = {
                'operation': 'searchRetrieve',
                'version': '1.1',
                'recordSchema': 'MARC21-xml',
                'maximumRecords': '1',
                'query': test_query,
                'accessToken': key_to_validate
            }
            
            response = requests.get(self.base_url, params=search_params)
            response.raise_for_status()
            
            # Check if response contains valid XML
            soup = BeautifulSoup(response.content, 'xml')
            error = soup.find('diagnostics')
            
            return not error
            
        except Exception as e:
            logger.error(f"API key validation error: {e}", exc_info=True)
            return False
            
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the DNB API.
        
        Returns:
            dict: A dictionary containing the test results
        """
        import time
        
        try:
            start_time = time.time()
            
            # Make a simple test query
            test_query = "medizin"  # Simple German medical term
            search_params = {
                'operation': 'searchRetrieve',
                'version': '1.1',
                'recordSchema': 'MARC21-xml',
                'maximumRecords': '1',
                'query': test_query
            }
            
            response = requests.get(self.base_url, params=search_params, timeout=10)
            
            response_time = time.time() - start_time
            
            if response.ok:
                # Parse XML response
                soup = BeautifulSoup(response.content, 'xml')
                
                # Check for errors
                error = soup.find('diagnostics')
                if error:
                    error_msg = error.get_text()
                    return {
                        'status': 'Error',
                        'message': f'DNB API returned an error: {error_msg}',
                        'response_time': round(response_time, 2)
                    }
                
                # Get number of results
                num_records_elem = soup.find('numberOfRecords')
                if num_records_elem:
                    num_records = int(num_records_elem.get_text())
                    return {
                        'status': 'OK',
                        'message': f'Successfully connected to DNB. Found {num_records} results for "medizin"',
                        'response_time': round(response_time, 2)
                    }
                else:
                    return {
                        'status': 'Warning',
                        'message': 'Connected to DNB, but could not determine number of results',
                        'response_time': round(response_time, 2)
                    }
            else:
                return {
                    'status': 'Error',
                    'message': f'Error connecting to DNB: {response.status_code} - {response.reason}',
                    'response_time': round(response_time, 2)
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'Error',
                'message': 'Connection to DNB timed out',
                'response_time': None
            }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'Error',
                'message': 'Network error: Unable to connect to DNB',
                'response_time': None
            }
        except Exception as e:
            logger.error(f"DNB connection test error: {e}", exc_info=True)
            return {
                'status': 'Error',
                'message': f'Error testing DNB connection: {str(e)}',
                'response_time': None
            }
