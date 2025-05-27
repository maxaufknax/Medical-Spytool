"""
GEPRIS Connector Module

This module provides functionality to search the GEPRIS database.
"""

from typing import List, Dict, Any, Optional
import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from .base_connector import BaseConnector  # Changed from DatabaseConnector to BaseConnector

logger = logging.getLogger(__name__)

class GeprisConnector(BaseConnector):
    """
    Connector for searching the GEPRIS database.
    """
    
    def __init__(self, api_key: str = None, settings: dict = None):
        """Initialize the GEPRIS connector."""
        super().__init__(api_key, settings)
        self.base_url = "http://gepris.dfg.de/gepris/OCTOPUS"
        self.max_results = 100
        
    def construct_query(self, search_term: str, **kwargs) -> str:
        """
        Construct a GEPRIS query string.
        
        Args:
            search_term (str): The main search term
            **kwargs: Additional search parameters
                - additional_terms (str): Additional search terms
                - date_range (dict): Date range with 'start' and 'end' keys
                - language (str): Language filter
                - pub_type (str): Publication type filter
                - field (str): Specific field to search in
                
        Returns:
            str: The constructed query string
        """
        query_parts = []
        
        # Add main search term
        if search_term:
            query_parts.append(search_term)
            
        # Add additional terms if provided
        additional_terms = kwargs.get('additional_terms')
        if additional_terms:
            query_parts.append(additional_terms)
            
        # Combine all parts with AND
        return " AND ".join(query_parts) if query_parts else "*"
        
    def search(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Perform a search using the GEPRIS database.
        
        Args:
            query (str): The search query
            params (dict): Additional search parameters
            
        Returns:
            list: List of search results as dictionaries
        """
        try:
            # Since GEPRIS doesn't have a public API, we'll use web scraping
            search_url = f"{self.base_url}/search/project"
            params = {
                'findButton': 'Finden',
                'task': 'doSearchSimple',
                'searchString': query
            }
            
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            # Parse HTML response
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find project results
            results = []
            project_elements = soup.find_all('div', class_='project-item')
            
            for project in project_elements[:self.max_results]:
                try:
                    # Extract project details
                    title_elem = project.find('h2', class_='title')
                    title = title_elem.text.strip() if title_elem else None
                    
                    # Project ID
                    project_id = None
                    if title_elem and title_elem.find('a'):
                        project_link = title_elem.find('a').get('href', '')
                        project_id = project_link.split('/')[-1] if project_link else None
                    
                    # Principal investigators
                    investigators = []
                    pi_elem = project.find('div', class_='investigator')
                    if pi_elem:
                        for name in pi_elem.find_all('a'):
                            investigators.append(name.text.strip())
                    
                    # Institution
                    institution = None
                    inst_elem = project.find('div', class_='institution')
                    if inst_elem:
                        institution = inst_elem.text.strip()
                    
                    # Project period
                    period = None
                    period_elem = project.find('div', class_='period')
                    if period_elem:
                        period = period_elem.text.strip()
                    
                    # Subject area
                    subject = None
                    subject_elem = project.find('div', class_='subject-area')
                    if subject_elem:
                        subject = subject_elem.text.strip()
                    
                    result = {
                        'Title': title,
                        'Project ID': project_id,
                        'Investigators': investigators,
                        'Institution': institution,
                        'Period': period,
                        'Subject Area': subject,
                        'Database': 'GEPRIS',
                        'URL': f"http://gepris.dfg.de/gepris/projekt/{project_id}" if project_id else None
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error parsing GEPRIS project: {e}", exc_info=True)
                    continue
            
            return results
            
        except requests.RequestException as e:
            logger.error(f"GEPRIS request error: {e}", exc_info=True)
            raise Exception(f"GEPRIS request error: {str(e)}")
        except Exception as e:
            logger.error(f"GEPRIS search error: {e}", exc_info=True)
            raise Exception(f"GEPRIS search error: {str(e)}")
            
    def validate_api_key(self, api_key: str = None) -> bool:
        """
        Validate the API key (GEPRIS doesn't require an API key).
        
        Args:
            api_key (str, optional): API key (not used for GEPRIS)
        
        Returns:
            bool: Always returns True as GEPRIS doesn't use API keys
        """
        return True

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the GEPRIS API.
        
        Returns:
            dict: A dictionary containing the test results
        """
        import time
        
        try:
            start_time = time.time()
            
            # Make a simple test query
            test_query = "medizin"  # Simple German medical term
            url = f"{self.base_url}/projects"
            params = {
                "q": test_query,
                "rows": 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            response_time = time.time() - start_time
            
            if response.ok:
                try:
                    data = response.json()
                    total_results = data.get('numFound', 0)
                    
                    return {
                        'status': 'OK',
                        'message': f'Successfully connected to GEPRIS. Found {total_results} results for "medizin"',
                        'response_time': round(response_time, 2)
                    }
                except json.JSONDecodeError:
                    return {
                        'status': 'Warning',
                        'message': 'Connected to GEPRIS, but received invalid JSON response',
                        'response_time': round(response_time, 2)
                    }
            else:
                return {
                    'status': 'Error',
                    'message': f'Error connecting to GEPRIS: {response.status_code} - {response.reason}',
                    'response_time': round(response_time, 2)
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'Error',
                'message': 'Connection to GEPRIS timed out',
                'response_time': None
            }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'Error',
                'message': 'Network error: Unable to connect to GEPRIS',
                'response_time': None
            }
        except Exception as e:
            logger.error(f"GEPRIS connection test error: {e}", exc_info=True)
            return {
                'status': 'Error',
                'message': f'Error testing GEPRIS connection: {str(e)}',
                'response_time': None
            }