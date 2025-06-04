"""
DNB SRU API Client for searching publications by author.
"""

import requests
import time
from typing import List, Dict, Optional, Generator
from urllib.parse import urlencode
from .parser import MARCXMLParser
from .database_interface import DatabaseInterface, PublicationSchema


class DNBClient(DatabaseInterface):
    """Client for interacting with the German National Library SRU API."""
    
    BASE_URL = "https://services.dnb.de/sru/dnb"
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize the DNB client.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.parser = MARCXMLParser()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DNB-Spytool/1.0.0 (Python)'
        })
    
    # Properties expected by tests
    @property
    def base_url(self) -> str:
        """Get the base URL for the DNB API."""
        return self.BASE_URL
    
    @property
    def max_records(self) -> int:
        """Get the maximum records per request."""
        return 100
    
    @property
    def database_name(self) -> str:
        """Return the name of the database."""
        return "DNB"
    
    @property 
    def max_results_per_request(self) -> int:
        """Return the maximum results per single request."""
        return 100
    
    def _build_query(self, author_name: str) -> str:
        """
        Build CQL query for author search.
        
        Args:
            author_name: Name of the author
            
        Returns:
            CQL query string
        """
        return f'per="{author_name}"'
    
    def _build_params(self, query: str, start_record: int = 1, max_records: int = 100) -> Dict:
        """
        Build parameters for API request.
        
        Args:
            query: CQL query string
            start_record: Starting record number
            max_records: Maximum records to retrieve
            
        Returns:
            Dictionary of API parameters
        """
        return {
            'version': '1.1',
            'operation': 'searchRetrieve',
            'query': query,
            'recordSchema': 'MARC21-xml',
            'startRecord': start_record,
            'maximumRecords': max_records
        }
    
    def _parse_total_records(self, xml_content: str) -> int:
        """
        Parse total number of records from XML response.
        
        Args:
            xml_content: XML response content
            
        Returns:
            Total number of records
        """
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            
            # Find numberOfRecords element
            namespaces = {
                'srw': 'http://www.loc.gov/zing/srw/',            }
            
            total_elem = root.find('.//srw:numberOfRecords', namespaces)
            if total_elem is not None and total_elem.text:
                return int(total_elem.text)
            return 0
        except Exception:
            return 0
    
    def search_publications(self, query: str, max_results: int = 100, **kwargs) -> List[Dict]:
        """
        Search for publications in DNB (interface implementation).
        
        Args:
            query: Search query (typically author name)
            max_results: Maximum results to return
            **kwargs: Additional parameters (start_record, etc.)
            
        Returns:
            List of publication dictionaries
        """
        # Validate query
        validation = self.validate_query(query)
        if not validation['is_valid']:
            raise ValueError(f"Invalid query: {validation['error']}")
        
        author_name = validation['cleaned_query']
        start_record = kwargs.get('start_record', 1)
        
        # Validate author name
        if not author_name or not author_name.strip():
            raise ValueError("Author name cannot be empty")
            
        # Handle pagination for larger result sets
        all_publications = []
        current_start = start_record
        total_records = None

        while len(all_publications) < max_results:
            # Calculate remaining records needed
            remaining_needed = max_results - len(all_publications)
            page_size = min(remaining_needed, 100)  # API limit is 100
            
            # Stop if no more records needed
            if page_size <= 0:
                break

            result = self.search_by_author(author_name, page_size, current_start)
            if not result or 'publications' not in result:
                break

            publications = result['publications']
            if not publications:
                break

            # Update total_records if not already set
            if total_records is None:
                total_records = result.get('total_records', 0)

            # Add publications to our collection
            all_publications.extend(publications)

            # Check stopping conditions
            
            # 1. We have all records we want
            if len(all_publications) >= max_results:
                break

            # 2. We have all available records
            if total_records > 0 and len(all_publications) >= total_records:
                break

            # 3. Last page was empty or had fewer records than requested
            # BUT only stop if we've also reached the total records count
            if len(publications) < page_size and total_records > 0 and len(all_publications) >= total_records:
                break

            # Continue to next page
            # Note: DNB uses 1-based indexing for startRecord
            if page_size > len(publications):
                break  # We got fewer records than requested, so we're done
            current_start = current_start + page_size

        return all_publications
    
    def search_by_author(self, author_name: str, max_records: int = 100, 
                        start_record: int = 1) -> Dict:
        """
        Search for publications by author name.
        
        Args:
            author_name: Name of the author to search for
            max_records: Maximum number of records to retrieve
            start_record: Starting record number for pagination
            
        Returns:
            Dict containing search results and metadata
        """
        # Construct CQL query for author search
        query = f'per="{author_name}"'
        
        params = {
            'version': '1.1',
            'operation': 'searchRetrieve',
            'query': query,
            'recordSchema': 'MARC21-xml',
            'maximumRecords': min(max_records, 100),  # API limit is 100 per request
            'startRecord': start_record,
            'recordPacking': 'xml'
        }
        response_text = self._make_request(params)
        if response_text:
            # Parse the response and return publications directly
            raw_publications = self.parser.parse_publications(response_text.encode('utf-8'))
            
            # Normalize publications to standard schema and extract URLs
            publications = []
            for pub in raw_publications:
                pub['database_source'] = 'DNB'  # Mark source
                normalized_pub = PublicationSchema.normalize_publication(pub)
                # Extract URLs from the publication
                self._enhance_publication_with_urls(normalized_pub)
                publications.append(normalized_pub)
            
            # Parse total records count for pagination
            total_records = self._parse_total_records(response_text)
            return {
                'publications': publications,
                'total_records': total_records if total_records > 0 else len(publications)
            }
        return {'publications': [], 'total_records': 0}
    
    def search_multiple_authors(self, authors: List[str], max_records: int = 100) -> Dict:
        """
        Search for publications by multiple authors.
        
        Args:
            authors: List of author names
            max_records: Maximum number of records per author
            
        Returns:
            Dict containing combined search results
        """
        all_results = {
            'publications': [],
            'total_records': 0,
            'authors_searched': authors,
            'search_metadata': {}
        }
        
        for author in authors:
            print(f"Searching for author: {author}")
            author_results = self.get_all_publications(author, max_records)
            
            all_results['publications'].extend(author_results['publications'])
            all_results['total_records'] += author_results['total_records']
            all_results['search_metadata'][author] = {
                'records_found': author_results['total_records'],
                'records_retrieved': len(author_results['publications'])
            }
            
            # Add small delay between requests to be respectful
            time.sleep(0.5)
        
        return all_results
    
    def get_all_publications(self, author_name: str, max_records: int = 1000) -> Dict:
        """
        Retrieve all publications for an author using pagination.
        
        Args:
            author_name: Name of the author
            max_records: Maximum total records to retrieve
            
        Returns:
            Dict containing all publications and metadata
        """
        all_publications = []
        start_record = 1
        records_per_request = 100
        total_records = 0
        
        while len(all_publications) < max_records:
            remaining_records = max_records - len(all_publications)
            current_max = min(records_per_request, remaining_records)
            
            result = self.search_by_author(author_name, current_max, start_record)
            
            if not result or 'publications' not in result:
                break
            
            publications = result['publications']
            if not publications:
                break
            
            all_publications.extend(publications)
            total_records = result.get('total_records', len(all_publications))
            
            print(f"Retrieved {len(all_publications)} of {total_records} records for {author_name}")
            # Check if we've retrieved all available records
            if len(publications) < current_max or len(all_publications) >= total_records:
                break
            
            start_record += len(publications)
            time.sleep(0.3)  # Rate limiting
        
        return {
            'publications': all_publications,
            'total_records': total_records,
            'author': author_name
        }

    def _make_request(self, params: Dict) -> Optional[str]:
        """
        Make a request to the DNB SRU API with retry logic.
        
        Args:
            params: Query parameters for the API request
            
        Returns:
            Raw response text or None if failed
        """
        url = f"{self.BASE_URL}?{urlencode(params)}"
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, timeout=self.timeout, headers=self.session.headers)
                response.raise_for_status()
                
                # Return raw response text
                return response.text
                
            except requests.exceptions.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"All retry attempts failed for URL: {url}")
                    if attempt == self.max_retries - 1:
                        raise  # Re-raise the exception on final attempt
            except Exception as e:
                print(f"Error making request: {e}")
                return None
        
        return None
    
    def validate_author_name(self, author_name: str) -> bool:
        """
        Validate author name format.
        
        Args:
            author_name: Author name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not author_name or not isinstance(author_name, str):
            return False
        
        # Basic validation: at least 2 characters, contains letters
        return len(author_name.strip()) >= 2 and any(c.isalpha() for c in author_name)
    
    def get_search_suggestions(self, partial_name: str) -> List[str]:
        """
        Get search suggestions for partial author names.
        
        Args:
            partial_name: Partial author name
            
        Returns:
            List of suggested complete names
        """
        # This would ideally use a suggest API endpoint
        # For now, return the input as a basic suggestion
        if self.validate_author_name(partial_name):
            return [partial_name.strip()]
        return []
    
    def get_database_info(self) -> Dict[str, str]:
        """Get information about the DNB database."""
        return {
            'name': 'Deutsche Nationalbibliothek (DNB)',
            'description': 'German National Library bibliographic database',
            'base_url': self.BASE_URL,
            'coverage': 'German and German-language publications',
            'provider': 'Deutsche Nationalbibliothek',
            'api_version': 'SRU 1.1'
        }
    
    def validate_query(self, query: str) -> Dict[str, any]:
        """
        Validate a DNB search query.
        
        Args:
            query: Query string to validate
            
        Returns:
            Dict with validation results
        """
        if not query or not isinstance(query, str):
            return {
                'is_valid': False,
                'error': 'Query cannot be empty',
                'cleaned_query': None
            }
        
        cleaned_query = query.strip()
        if len(cleaned_query) < 2:
            return {
                'is_valid': False,
                'error': 'Query must be at least 2 characters long',
                'cleaned_query': cleaned_query
            }
        
        # DNB-specific validation
        if not any(c.isalpha() for c in cleaned_query):
            return {
                'is_valid': False,
                'error': 'Query must contain at least one letter',
                'cleaned_query': cleaned_query
            }
        
        return {
            'is_valid': True,
            'error': None,
            'cleaned_query': cleaned_query
        }
    
    def extract_publication_urls(self, publication: Dict) -> List[str]:
        """
        Extract all available URLs for a publication.
        
        Args:
            publication: Publication dictionary
            
        Returns:
            List of URLs
        """
        urls = []
        
        # Check for DOI URL
        if publication.get('doi'):
            urls.append(f"https://doi.org/{publication['doi']}")
        
        # Check for DNB permalink/URL
        if publication.get('url'):
            urls.append(publication['url'])
        
        # Check for ISBN-based URLs (for books)
        if publication.get('isbn'):
            # DNB catalog URL based on ISBN
            isbn = publication['isbn'].replace('-', '').replace(' ', '')
            urls.append(f"https://portal.dnb.de/opac.htm?method=simpleSearch&query={isbn}")
        
        # Check for ISSN-based URLs (for serials)
        if publication.get('issn'):
            issn = publication['issn'].replace('-', '').replace(' ', '')
            urls.append(f"https://portal.dnb.de/opac.htm?method=simpleSearch&query={issn}")
        
        # Generate DNB catalog search URL based on title
        if publication.get('title'):
            title_query = publication['title'].replace(' ', '+')
            urls.append(f"https://portal.dnb.de/opac.htm?method=simpleSearch&query={title_query}")
        
        return urls
    
    def get_primary_url(self, publication: Dict) -> Optional[str]:
        """
        Get the primary/preferred URL for a publication.
        
        Args:
            publication: Publication dictionary
            
        Returns:
            Primary URL or None
        """
        # Priority order: DOI, direct URL, DNB catalog search
        if publication.get('doi'):
            return f"https://doi.org/{publication['doi']}"
        
        if publication.get('url'):
            return publication['url']
        
        # Generate DNB catalog search URL as fallback
        if publication.get('isbn'):
            isbn = publication['isbn'].replace('-', '').replace(' ', '')
            return f"https://portal.dnb.de/opac.htm?method=simpleSearch&query={isbn}"
        
        if publication.get('title'):
            title_query = publication['title'].replace(' ', '+')
            return f"https://portal.dnb.de/opac.htm?method=simpleSearch&query={title_query}"
        
        return None

    def extract_urls_from_publication(self, publication: Dict) -> Dict:
        """
        Extract all available URLs from a DNB publication record.
        
        Args:
            publication: Publication dictionary from DNB
            
        Returns:
            Dictionary with URL types and their values
        """
        urls = {}
        
        try:
            # Direct URL from MARC field 856 (highest priority)
            if publication.get('url') and publication['url'].startswith('http'):
                urls['dnb_direct'] = publication['url']
            
            # DNB URL based on record ID (could be 'id' or 'record_id')
            record_id = publication.get('id') or publication.get('record_id')
            if record_id:
                urls['dnb_record'] = f"https://portal.dnb.de/opac.htm?method=simpleSearch&cqlMode=true&query=idn%3D{record_id}"
            
            # ISBN-based URLs
            if publication.get('isbn'):
                isbn = publication['isbn'].replace('-', '').replace(' ', '')
                urls['worldcat'] = f"https://www.worldcat.org/isbn/{isbn}"
                urls['google_books'] = f"https://books.google.com/books?vid=ISBN{isbn}"
            
            # DOI URL
            if publication.get('doi'):
                urls['doi'] = f"https://doi.org/{publication['doi']}"
            
            # ISSN-based URL for journals
            if publication.get('issn'):
                issn = publication['issn'].replace('-', '')
                urls['issn_portal'] = f"https://portal.issn.org/resource/ISSN/{issn}"
            
            # Publisher-specific URLs
            publisher = publication.get('publisher', '').lower()
            title = publication.get('title', '')
            
            if 'springer' in publisher and publication.get('isbn'):
                urls['springer'] = f"https://link.springer.com/book/{publication['isbn']}"
            elif 'elsevier' in publisher and publication.get('doi'):
                urls['sciencedirect'] = f"https://www.sciencedirect.com/science/article/pii/{publication['doi']}"
            
            # Add the primary URL to the publication record
            if urls:
                publication['url'] = self._get_primary_url(urls)
                publication['all_urls'] = urls
                
                # Also expose URLs as individual fields for GUI compatibility
                for url_type, url_value in urls.items():
                    publication[url_type] = url_value
            
        except Exception as e:
            print(f"Warning: URL extraction failed for DNB publication: {e}")
        
        return urls
    
    def _get_primary_url(self, urls: Dict) -> str:
        """
        Get the primary URL from available URLs with priority order.
        
        Args:
            urls: Dictionary of URL types and values
            
        Returns:
            Primary URL string
        """
        priority_order = [
            'doi',
            'dnb_direct',    # Direct DNB URLs from MARC field 856
            'dnb_record',    # DNB record search URLs
            'springer',
            'sciencedirect',
            'worldcat',
            'google_books',
            'issn_portal'
        ]
        
        for url_type in priority_order:
            if url_type in urls:
                return urls[url_type]
        
        # Return any available URL if no priority match
        return next(iter(urls.values())) if urls else None
    
    def _enhance_publication_with_urls(self, publication: Dict) -> Dict:
        """
        Enhance publication record with extracted URLs.
        
        Args:
            publication: Publication dictionary
            
        Returns:
            Enhanced publication dictionary with URLs
        """
        try:
            self.extract_urls_from_publication(publication)
        except Exception as e:
            print(f"Warning: Failed to enhance publication with URLs: {e}")
        
        return publication
