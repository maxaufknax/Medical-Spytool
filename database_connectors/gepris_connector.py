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
    requires_api_key = False # GEPRIS does not use an API key
    
    def __init__(self, api_key: str = None, settings: dict = None):
        """Initialize the GEPRIS connector."""
        super().__init__(api_key, settings)
        # GEPRIS uses different URLs for different types of searches.
        # For projects by term:
        self.base_search_url = "https://gepris.dfg.de/gepris/OCTOPUS/search/project"
        # For persons by name:
        self.base_person_search_url = "https://gepris.dfg.de/gepris/OCTOPUS/search/person"
        self.name = "Gepris"
        self.max_results = 50 # GEPRIS shows 10-20 results per page, be mindful of scraping load.
        
    def construct_query(self, search_term: str, **kwargs) -> str:
        """
        Construct a GEPRIS query string. For GEPRIS, this is typically a single string
        as it doesn't support complex boolean queries via simple URL params.
        Person names will be handled by a different search URL path if provided.

        Args:
            search_term (str): The main search term for projects.
            **kwargs: Additional search parameters.
                - person_names (list): List of person names. If provided, this might change search behavior.
                - additional_terms (str): Additional terms to append to search_term.
        Returns:
            str: The constructed query string.
        """
        query_parts = []
        if search_term:
            query_parts.append(search_term)

        additional_terms = kwargs.get('additional_terms')
        if additional_terms:
            query_parts.append(additional_terms)
        
        # For GEPRIS, complex field searches or date ranges are not easily done via simple URL.
        # The main search string is usually a combination of terms.
        # If person_names are primary, the search term might be secondary or ignored for person search.

        # If person_names are provided and no other search_term, we might want to use the person name as the query.
        person_names = kwargs.get('person_names', [])
        if not search_term and person_names and isinstance(person_names, list) and person_names[0]:
            # Use the first person name as the primary query if no other search term
            return person_names[0].strip()

        return " ".join(query_parts) if query_parts else "" # Return empty if no terms, search will handle.

    def search(self, search_term: str = None, query: str = None, params: Dict[str, Any] = None,
               person_names: List[str] = None, max_results: int = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Perform a search using the GEPRIS database (via web scraping).
        
        Args:
            search_term (str, optional): The main search term for projects.
            query (str, optional): A pre-constructed query string.
            params (dict, optional): Additional request parameters (not typically used here).
            person_names (list, optional): List of person names to search for.
            max_results (int, optional): Maximum number of results to return.
            **kwargs: Additional keyword arguments passed to construct_query if query is not set.
            
        Returns:
            list: List of search results as dictionaries.
        """
        effective_max_results = max_results if max_results is not None else self.max_results

        if not query:
            # If person_names are provided, prioritize person search
            if person_names and isinstance(person_names, list) and person_names[0]:
                # Use the first person name for the search. GEPRIS person search is by name.
                # Other search_term or additional_terms might be ignored or used as filter if supported.
                search_string = person_names[0].strip()
                search_url = self.base_person_search_url
                search_type_log = f"person '{search_string}'"
            elif search_term: # Standard project search
                search_string = self.construct_query(search_term, person_names=person_names, **kwargs)
                search_url = self.base_search_url
                search_type_log = f"project term '{search_string}'"
            else: # No valid terms
                logger.info("GEPRIS search attempted with no search term or person name.")
                return []
        else: # Query is pre-constructed
            search_string = query
            # Determine if it's a person or project search based on context or a heuristic (e.g. if person_names is also passed)
            if person_names and person_names[0] and person_names[0] in search_string : # Basic heuristic
                 search_url = self.base_person_search_url
                 search_type_log = f"pre-constructed person query '{search_string}'"
            else:
                 search_url = self.base_search_url
                 search_type_log = f"pre-constructed project query '{search_string}'"

        if not search_string.strip():
            logger.info("GEPRIS search string is empty.")
            return []

        logger.info(f"GEPRIS searching for {search_type_log} using URL: {search_url}")

        request_params = {
            'findButton': 'Finden', # This might be specific to project search
            'text': search_string, # For person search, the param is often 'text'
            'lookuptype': 'modules', # For person search
            'searchType': 'person', # For person search
            # For project search, it's 'task': 'doSearchSimple', 'searchString': search_string
        }
        # Adjust params based on URL
        if search_url == self.base_search_url: # Project search
            request_params = {'task': 'doSearchSimple', 'searchString': search_string, 'findButton': 'Finden'}
        else: # Person search
            request_params = {'lookuptype':'modules', 'searchType': 'person', 'text': search_string, 'findButton': 'Finden'}


        try:
            response = requests.get(search_url, params=request_params, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []

            if search_url == self.base_search_url: # Parsing project results
                project_elements = soup.find_all('div', class_='projekt') # Class name might be 'projekt'
                if not project_elements: project_elements = soup.find_all('div', class_='project') # Fallback
                if not project_elements: project_elements = soup.find_all('div', class_='item') # Fallback

                for project_div in project_elements[:effective_max_results]:
                    title_tag = project_div.find('h2')
                    title = title_tag.get_text(strip=True) if title_tag else "N/A"
                    link_tag = title_tag.find('a', href=True) if title_tag else None
                    project_url = f"https://gepris.dfg.de{link_tag['href']}" if link_tag else "N/A"
                    project_id = link_tag['href'].split('/')[-1] if link_tag and '/' in link_tag['href'] else "N/A"

                    details_text = project_div.get_text(" | ", strip=True)
                    
                    # Crude extraction, GEPRIS HTML is complex and varies.
                    investigators_str = "N/A"
                    institution_str = "N/A"
                    period_str = "N/A"

                    # Example of trying to find specific details - this needs refinement based on actual HTML
                    term_tag = project_div.find('div', class_='term')
                    if term_tag: period_str = term_tag.get_text(strip=True)
                    
                    leader_tags = project_div.find_all('span', class_='person')
                    if leader_tags:
                        investigators_str = "; ".join([leader.get_text(strip=True) for leader in leader_tags])

                    inst_tag = project_div.find('span', class_='institution')
                    if inst_tag : institution_str = inst_tag.get_text(strip=True)


                    results.append({
                        'Title': title,
                        'Authors': investigators_str, # Using 'Authors' for consistency with other connectors
                        'Journal': institution_str, # Using 'Journal' for institution for consistency
                        'Publication Year': period_str.split('-')[-1].strip() if '-' in period_str else period_str, # Attempt to get end year
                        'Abstract': details_text, # Using full details as abstract
                        'DOI': None,
                        'URL': project_url,
                        'Database': 'Gepris',
                        'Publication Type': 'Project Funding',
                        'Identifier': project_id,
                        'Keywords': None, # Gepris doesn't have keywords in the same way
                        'Citation Count': None
                    })
            elif search_url == self.base_person_search_url: # Parsing person results
                person_elements = soup.find_all('div', class_='person') # Assuming this class for person items
                if not person_elements: person_elements = soup.find_all('div', class_='item')

                for person_div in person_elements[:effective_max_results]:
                    name_tag = person_div.find('a', class_='name') # Or similar selector
                    name = name_tag.get_text(strip=True) if name_tag else "N/A"
                    person_url = f"https://gepris.dfg.de{name_tag['href']}" if name_tag and name_tag.has_attr('href') else "N/A"
                    person_id = name_tag['href'].split('/')[-1] if name_tag and name_tag.has_attr('href') and '/' in name_tag['href'] else "N/A"
                    
                    institution_tags = person_div.find_all('span', class_='institution') # Example selector
                    institutions = "; ".join([inst.get_text(strip=True) for inst in institution_tags]) or "N/A"

                    results.append({
                        'Title': f"Profile of {name}", # Create a title for person result
                        'Authors': name,
                        'Journal': institutions, # Affiliated institutions
                        'Publication Year': None,
                        'Abstract': f"GEPRIS profile for {name}, affiliated with {institutions}.",
                        'DOI': None,
                        'URL': person_url,
                        'Database': 'Gepris',
                        'Publication Type': 'Person Profile',
                        'Identifier': person_id,
                        'Keywords': None,
                        'Citation Count': None
                    })
            
            logger.info(f"Found {len(results)} Gepris results for {search_type_log}")
            return self.format_results(results)
            
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
        Test the connection to GEPRIS by attempting a simple project search.
        
        Returns:
            dict: A dictionary containing the test results.
        """
        import time
        start_time = time.time()
        test_query = "medizin" # A common German term for testing

        # Use the project search URL and params
        request_params = {'task': 'doSearchSimple', 'searchString': test_query, 'findButton': 'Finden'}
        
        try:
            response = requests.get(self.base_search_url, params=request_params, timeout=15)
            response_time = time.time() - start_time
            response.raise_for_status() # Will raise an HTTPError for bad responses (4xx or 5xx)

            # Check if the page content seems valid (e.g., contains search results area)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for a known element that indicates a results page or no results page
            # For example, the header of the results list or the "no results" message div.
            # <div class="bla">Ihre Suche nach "medizin" ergab x Treffer</div> or similar
            results_count_element = soup.find('div', class_='itemcount') # Common way to show item count
            if results_count_element and results_count_element.find('strong'):
                 num_results_text = results_count_element.find('strong').get_text(strip=True)
                 message = f'Successfully connected to GEPRIS. Test search for "{test_query}" returned {num_results_text} results.'
            elif soup.find('div', id='main'): # Check if main content area loads
                 message = f'Successfully connected to GEPRIS. Test search for "{test_query}" loaded page, but result count not identified.'
            else: # Fallback if specific elements are not found but page loaded
                 message = f'Successfully connected to GEPRIS. Test search for "{test_query}" loaded page.'


            return {
                'status': 'OK',
                'message': message,
                'response_time': round(response_time, 2)
            }

        except requests.exceptions.Timeout:
            return {
                'status': 'Error',
                'message': f'Connection to GEPRIS timed out after 15 seconds for query "{test_query}".',
                'response_time': None
            }
        except requests.exceptions.HTTPError as http_err:
            return {
                'status': 'Error',
                'message': f'HTTP error connecting to GEPRIS for query "{test_query}": {http_err.response.status_code} - {http_err.response.reason}',
                'response_time': round(time.time() - start_time, 2) if 'start_time' in locals() else None
            }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'Error',
                'message': f'Network error: Unable to connect to GEPRIS for query "{test_query}".',
                'response_time': None
            }
        except Exception as e:
            logger.error(f"GEPRIS connection test error for query '{test_query}': {e}", exc_info=True)
            return {
                'status': 'Error',
                'message': f'Error testing GEPRIS connection with query "{test_query}": {str(e)}',
                'response_time': None
            }