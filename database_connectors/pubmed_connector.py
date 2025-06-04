"""
PubMed Connector Module

This module provides functionality to search the PubMed database
using their E-utilities API.
"""

from typing import List, Dict, Any, Optional, Union
import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from .base_connector import BaseConnector

logger = logging.getLogger(__name__)

class PubMedConnector(BaseConnector):
    """
    Connector for searching the PubMed database.
    """
    requires_api_key = False  # PubMed can be used without an API key, but it's recommended for higher rate limits
    
    def __init__(self, api_key: str = None, settings: dict = None):
        """Initialize the PubMed connector."""
        super().__init__(api_key, settings)
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.max_results = 100
        self.name = "PubMed" # Added for api_key_manager
        
    def construct_query(self, search_term: str, **kwargs) -> str:
        """
        Construct a PubMed query string.
        
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
            query_parts.append(f"({search_term})")
        
        # Add person names if provided
        person_names = kwargs.get('person_names', [])
        if person_names and isinstance(person_names, list):
            # Convert each person name to a search term
            for person in person_names:
                if isinstance(person, str) and person.strip():
                    # Format: "Lastname, Firstname"[Author] OR "Lastname F"[Author]
                    # Split name if it contains a comma
                    if ',' in person:
                        lastname, firstname = person.split(',', 1)
                        author_query = f'"{lastname.strip()}, {firstname.strip()}"[Author]'
                    # Split name if it contains a space
                    elif ' ' in person:
                        name_parts = person.split()
                        lastname = name_parts[-1]  # Last part is likely the lastname
                        firstname_initial = name_parts[0][0] if len(name_parts) > 1 else ""
                        author_query = f'"{lastname} {firstname_initial}"[Author]'
                    else:
                        # Just use the name as is
                        author_query = f'"{person}"[Author]'
                    query_parts.append(author_query)
            
        # Add additional terms if provided
        additional_terms = kwargs.get('additional_terms')
        if additional_terms:
            query_parts.append(f"({additional_terms})")
            
        # Add date range if provided
        date_range = kwargs.get('date_range')
        if date_range:
            start_date = date_range.get('start')
            end_date = date_range.get('end')
            if start_date and end_date:
                date_query = f"{start_date}:{end_date}[dp]"
                query_parts.append(date_query)
        
        # Alternative: check for start_date and end_date directly (from form submission)
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        if start_date and end_date:
            date_query = f"{start_date}:{end_date}[dp]"
            query_parts.append(date_query)
                
        # Add language filter if provided
        language = kwargs.get('language')
        if language:
            query_parts.append(f"{language}[lang]")
            
        # Add publication type filter if provided
        pub_type = kwargs.get('pub_type')
        if pub_type:
            query_parts.append(f"{pub_type}[pt]")
            
        # Add field-specific search if provided
        field = kwargs.get('field')
        if field and field.lower() != 'all fields' and search_term:
            # Map common fields to PubMed field tags
            field_map = {
                'title': '[ti]',
                'author': '[au]',
                'journal': '[ta]',
                'abstract': '[ab]',
                'affiliation': '[ad]'
            }
            
            # Handle field in search_field parameter (from form)
            search_field = kwargs.get('search_field')
            if search_field and search_field.lower() in field_map and search_term:
                # Replace the first query part (search term) with field-specific query
                if query_parts and search_term in query_parts[0]:
                    query_parts[0] = f"({search_term}{field_map[search_field.lower()]})"
            
            # Direct field specification takes precedence
            elif field.lower() in field_map and search_term:
                # Replace the first query part (search term) with field-specific query
                if query_parts and search_term in query_parts[0]:
                    query_parts[0] = f"({search_term}{field_map[field.lower()]})"
        
        # Combine all parts with AND
        if not query_parts:
            # If no query parts, use a default query that returns recent publications
            return "recent[filter]"
        
        return " AND ".join(query_parts)
        
    def search(self, search_term: str = None, query: str = None, params: Dict[str, Any] = None, person_names: List[str] = None, max_results: int = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Perform a search using the PubMed E-utilities API.
        
        This method supports two calling conventions:
        1. search(query, params) - The traditional BaseConnector interface
        2. search(search_term, person_names, max_results, **kwargs) - The way it's called in main.py
        
        Args:
            search_term (str, optional): The main search term
            query (str, optional): A pre-constructed query string (alternative to search_term)
            params (dict, optional): Additional search parameters
            person_names (list, optional): List of person names to include in the search
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
            
            logger.info(f"PubMed search query: {query}")
            
            # First, search for matching PMIDs
            search_params = {
                'db': 'pubmed',
                'term': query,
                'retmax': str(self.max_results),
                'usehistory': 'y',
                'retmode': 'json'
            }
            
            # If params were provided, update search_params
            if params:
                search_params.update(params)
            
            # Add API key if available
            if self.api_key:
                search_params['api_key'] = self.api_key
            
            # Get the API key from app_config if it's in kwargs
            elif 'api_key' in kwargs:
                search_params['api_key'] = kwargs.get('api_key')
                
            search_url = f"{self.base_url}/esearch.fcgi"
            response = requests.get(search_url, params=search_params)
            response.raise_for_status()
            
            search_result = response.json()
            pmids = search_result['esearchresult'].get('idlist', [])
            
            if not pmids:
                logger.info("No results found for PubMed query")
                return []
                
            # Then, fetch details for those PMIDs
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(pmids),
                'retmode': 'xml'
            }
            
            if self.api_key:
                fetch_params['api_key'] = self.api_key
            elif 'api_key' in kwargs:
                fetch_params['api_key'] = kwargs.get('api_key')
                
            fetch_url = f"{self.base_url}/efetch.fcgi"
            response = requests.get(fetch_url, params=fetch_params)
            response.raise_for_status()
            
            # Parse XML response
            soup = BeautifulSoup(response.content, 'xml')
            articles = soup.find_all('PubmedArticle')
            
            results = []
            for article in articles:
                try:
                    # Extract article metadata
                    citation = article.MedlineCitation
                    
                    # Basic metadata
                    pmid = citation.PMID.text
                    article_info = citation.Article
                    
                    # Title
                    title = article_info.ArticleTitle.text if article_info.ArticleTitle else "No Title"
                    
                    # Authors
                    authors = []
                    author_list = article_info.AuthorList.find_all('Author') if article_info.AuthorList else []
                    for author in author_list:
                        try:
                            lastname = author.LastName.text if author.LastName else ''
                            forename = author.ForeName.text if author.ForeName else ''
                            authors.append(f"{lastname}, {forename}".strip(', '))
                        except Exception as author_error:
                            logger.debug(f"Error extracting author: {author_error}")
                            continue
                    
                    author_string = "; ".join(authors) if authors else "Unknown"
                            
                    # Journal info
                    journal = article_info.Journal
                    journal_title = journal.Title.text if journal and journal.Title else "No Journal"
                    
                    # Publication date
                    pub_date = None
                    pub_month = None
                    
                    # Try different paths for publication date
                    if hasattr(journal, 'JournalIssue') and hasattr(journal.JournalIssue, 'PubDate'):
                        pub_date_elem = journal.JournalIssue.PubDate
                        year = pub_date_elem.Year.text if hasattr(pub_date_elem, 'Year') else None
                        month = pub_date_elem.Month.text if hasattr(pub_date_elem, 'Month') else None
                        if year:
                            pub_date = year
                            pub_month = month
                    
                    # Try alternative publication date path
                    if not pub_date and hasattr(article_info, 'PubDate'):
                        pub_date_elem = article_info.PubDate
                        year = pub_date_elem.Year.text if hasattr(pub_date_elem, 'Year') else None
                        month = pub_date_elem.Month.text if hasattr(pub_date_elem, 'Month') else None
                        if year:
                            pub_date = year
                            pub_month = month
                            
                    # Abstract
                    abstract = None
                    if article_info.Abstract and article_info.Abstract.AbstractText:
                        if isinstance(article_info.Abstract.AbstractText, list):
                            abstract_parts = []
                            for part in article_info.Abstract.AbstractText:
                                if part.string:
                                    abstract_parts.append(part.string)
                                else:
                                    abstract_parts.append(part.text)
                            abstract = " ".join(abstract_parts)
                        else:
                            abstract = article_info.Abstract.AbstractText.text
                    
                    # Publication type
                    pub_types = []
                    pub_type_list = citation.find_all('PublicationType') if citation else []
                    for pub_type in pub_type_list:
                        if pub_type.text:
                            pub_types.append(pub_type.text)
                    pub_type_string = "; ".join(pub_types) if pub_types else None
                    
                    # MeSH terms (Keywords)
                    mesh_terms = []
                    mesh_heading_list = citation.find_all('MeshHeading') if citation else []
                    for mesh in mesh_heading_list:
                        descriptor = mesh.DescriptorName.text if mesh.DescriptorName else None
                        if descriptor:
                            mesh_terms.append(descriptor)
                    keywords = "; ".join(mesh_terms) if mesh_terms else None
                    
                    # Language
                    language = article_info.Language.text if hasattr(article_info, 'Language') else None
                    
                    # DOI and other identifiers
                    article_ids = article.PubmedData.ArticleIdList.find_all('ArticleId') if hasattr(article, 'PubmedData') and hasattr(article.PubmedData, 'ArticleIdList') else []
                    doi = next((aid.text for aid in article_ids if aid.get('IdType') == 'doi'), None)
                    
                    # Citation count (not directly available from PubMed, would need additional API calls)
                    citation_count = None
                    
                    # Build result dictionary
                    result = {
                        'Title': title,
                        'Authors': author_string,
                        'Journal': journal_title,
                        'Publication Year': pub_date,
                        'Publication Month': pub_month,
                        'Abstract': abstract,
                        'PMID': pmid,
                        'DOI': doi,
                        'Database': 'PubMed',
                        'URL': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        'Publication Type': pub_type_string,
                        'Language': language,
                        'Keywords': keywords,
                        'Citation Count': citation_count
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error parsing PubMed article (ID: {pmid if 'pmid' in locals() else 'unknown'}): {e}", exc_info=True)
                    continue
                    
            logger.info(f"Found {len(results)} PubMed results")
            return results
            
        except requests.RequestException as e:
            logger.error(f"PubMed API request error: {e}", exc_info=True)
            raise Exception(f"PubMed API request error: {str(e)}")
        except Exception as e:
            logger.error(f"PubMed search error: {e}", exc_info=True)
            raise Exception(f"PubMed search error: {str(e)}")
            
    def validate_api_key(self, api_key: str = None) -> bool:
        """
        Validate the PubMed API key by making a test request.
        
        Args:
            api_key (str, optional): The API key to validate. If None, use the one from the instance.
            
        Returns:
            bool: True if the API key is valid, False otherwise
        """
        try:
            # Use provided API key or fall back to instance API key
            key_to_validate = api_key if api_key else self.api_key
            
            # If no API key, return True as PubMed doesn't strictly require one
            if not key_to_validate:
                return True
            
            # Make a simple test query
            test_params = {
                'db': 'pubmed',
                'term': 'test',
                'retmax': '1',
                'api_key': key_to_validate
            }
            
            search_url = f"{self.base_url}/esearch.fcgi"
            response = requests.get(search_url, params=test_params)
            
            # Check if the request was successful and didn't return an API key error
            return response.ok and 'API key invalid' not in response.text
            
        except Exception as e:
            logger.error(f"API key validation error: {e}", exc_info=True)
            return False
            
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to PubMed.
        
        Returns:
            dict: A dictionary containing the test results
        """
        import time
        
        try:
            start_time = time.time()
            
            # Make a simple test query
            test_params = {
                'db': 'pubmed',
                'term': 'medical',
                'retmax': '1',
                'retmode': 'json'
            }
            
            if self.api_key:
                test_params['api_key'] = self.api_key
                
            search_url = f"{self.base_url}/esearch.fcgi"
            response = requests.get(search_url, params=test_params, timeout=10)
            
            response_time = time.time() - start_time
            
            if response.ok:
                search_result = response.json()
                count = int(search_result['esearchresult'].get('count', 0))
                
                if count > 0:
                    return {
                        'status': 'OK',
                        'message': f'Successfully connected to PubMed. Found {count} results for "medical"',
                        'response_time': round(response_time, 2)
                    }
                else:
                    return {
                        'status': 'Warning',
                        'message': 'Connected to PubMed, but received 0 results for test query',
                        'response_time': round(response_time, 2)
                    }
            else:
                return {
                    'status': 'Error',
                    'message': f'Error connecting to PubMed: {response.status_code} - {response.reason}',
                    'response_time': round(response_time, 2)
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'Error',
                'message': 'Connection to PubMed timed out',
                'response_time': None
            }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'Error',
                'message': 'Network error: Unable to connect to PubMed',
                'response_time': None
            }
        except Exception as e:
            logger.error(f"PubMed connection test error: {e}", exc_info=True)
            return {
                'status': 'Error',
                'message': f'Error testing PubMed connection: {str(e)}',
                'response_time': None
            }