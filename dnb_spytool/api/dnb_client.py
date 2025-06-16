"""
DNB SRU API Client for searching publications by author.
"""

import requests
from requests.adapters import HTTPAdapter, Retry
import time
import re
import hashlib
from typing import List, Dict, Optional, Generator
from urllib.parse import urlencode
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from .parser import MARCXMLParser
from .database_interface import DatabaseInterface, PublicationSchema
from ..core.cache_manager import QueryCacheManager


class DNBClient(DatabaseInterface):
    """Client for interacting with the German National Library SRU API."""
    
    BASE_URL = "https://services.dnb.de/sru/dnb"
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize the DNB client with enhanced connection pooling.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.parser = MARCXMLParser()
        
        # Enhanced session with connection pooling and retry strategy
        self.session = self._create_optimized_session()
        
        # Performance monitoring
        self._request_count = 0
        self._total_request_time = 0.0
        self._rate_limit_lock = threading.Lock()
        
        # Rate limiting for DNB (conservative approach)
        self.rate_limit_delay = 0.5  # 2 requests per second max
        self.last_request_time = 0
        
        # Initialize cache manager
        self.cache_manager = QueryCacheManager()
    
    def _create_optimized_session(self) -> requests.Session:
        """Create an optimized session with connection pooling and retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy for DNB
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1,
            respect_retry_after_header=True
        )
        
        # Configure HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=5,   # Lower than PubMed since DNB is less frequent
            pool_maxsize=10,      # Conservative pool size
            max_retries=retry_strategy,
            pool_block=False
        )
        
        # Mount adapters for both HTTP and HTTPS
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set optimized headers
        session.headers.update({
            'User-Agent': 'Medical-Spytool/1.4-beta (Python; DNB-Optimized)',
            'Accept': 'application/xml,text/xml',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        })
        
        return session
    
    def get_connection_stats(self) -> Dict[str, any]:
        """Get connection performance statistics including cache metrics."""
        avg_time = self._total_request_time / self._request_count if self._request_count > 0 else 0
        
        # Get cache statistics safely
        cache_stats = {}
        try:
            if hasattr(self, 'cache_manager') and self.cache_manager:
                # Get basic cache stats without triggering threading issues
                memory_stats = self.cache_manager.memory_cache.stats.get_stats()
                cache_stats = {
                    'memory_cache': memory_stats,
                    'cache_enabled': True
                }
        except Exception as e:
            cache_stats = {'error': str(e), 'cache_enabled': False}
        
        return {
            'total_requests': self._request_count,
            'total_time': self._total_request_time,
            'average_request_time': avg_time,
            'rate_limit_delay': self.rate_limit_delay,
            'pool_config': {
                'pool_connections': 5,
                'pool_maxsize': 10,
                'retry_attempts': 3
            },
            'cache_stats': cache_stats
        }
    
    def _rate_limit(self):
        """Implement thread-safe rate limiting for DNB API requests."""
        with self._rate_limit_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
    
    def _make_optimized_request(self, url: str, params: Dict) -> Optional[requests.Response]:
        """Make an optimized request with performance tracking."""
        start_time = time.time()
        
        try:
            self._rate_limit()
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Track performance
            request_time = time.time() - start_time
            self._request_count += 1
            self._total_request_time += request_time
            
            return response
            
        except Exception as e:
            print(f"DNB optimized request failed: {e}")
            return None
    
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
    
    def test_connection(self) -> bool:
        """
        Test if the DNB API is accessible.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Test with a simple query that should always return results
            test_query = self._build_query("test")
            params = {
                'query': test_query,
                'recordSchema': 'oai_dc',
                'maximumRecords': 1,
                'startRecord': 1
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                # Check if the response contains valid XML
                try:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.content)
                    # Look for either results or a valid SRU response structure
                    if root.tag.endswith('searchRetrieveResponse'):
                        return True
                    else:
                        return False
                except ET.ParseError:
                    return False
            else:
                return False
                
        except Exception as e:
            print(f"DNB connection test failed: {e}")
            return False
    
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
        # Generate cache key for this search
        start_record = kwargs.get('start_record', 1)
        cache_key_data = f"dnb_search_{query}_{max_results}_{start_record}"
        cache_key = hashlib.md5(cache_key_data.encode()).hexdigest()
        
        # Check cache first
        cached_result = self.cache_manager.get(cache_key, "dnb")
        if cached_result is not None:
            print(f"✓ Cache hit for DNB search: {query[:50]}...")
            return cached_result
        
        print(f"⟳ Cache miss for DNB search: {query[:50]}... (fetching from DNB)")
        
        # Validate query
        validation = self.validate_query(query)
        if not validation['is_valid']:
            raise ValueError(f"Invalid query: {validation['error']}")
        
        author_name = validation['cleaned_query']
        
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

        # Cache the result
        self.cache_manager.put(cache_key, "dnb", all_publications)
        print(f"💾 Cached DNB search result: {len(all_publications)} publications")
        
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
        # Generate cache key for this author search
        author_cache_key_data = f"dnb_author_{author_name}_{max_records}_{start_record}"
        author_cache_key = hashlib.md5(author_cache_key_data.encode()).hexdigest()
        
        # Check cache for author search
        cached_author_result = self.cache_manager.get(author_cache_key, "dnb")
        if cached_author_result is not None:
            print(f"✓ Cache hit for DNB author search: {author_name}")
            return cached_author_result
        
        print(f"⟳ Cache miss for DNB author search: {author_name} (fetching from DNB)")
        
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
            result = {
                'publications': publications,
                'total_records': total_records if total_records > 0 else len(publications)
            }
            
            # Cache the author search result
            self.cache_manager.put(author_cache_key, "dnb", result)
            print(f"💾 Cached DNB author result: {len(publications)} publications for {author_name}")
            
            return result
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
        Make a request to the DNB SRU API using optimized session with retry logic.
        
        Args:
            params: Query parameters for the API request
            
        Returns:
            Raw response text or None if failed
        """
        try:
            # Use optimized request method with connection pooling and performance tracking
            response = self._make_optimized_request(self.BASE_URL, params)
            if response:
                return response.text
            return None
            
        except Exception as e:
            print(f"DNB request failed: {e}")
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
    
    def get_connection_stats(self) -> Dict[str, any]:
        """Get connection performance statistics."""
        avg_time = self._total_request_time / self._request_count if self._request_count > 0 else 0
        return {
            'total_requests': self._request_count,
            'total_time': self._total_request_time,
            'average_request_time': avg_time,
            'rate_limit_delay': self.rate_limit_delay,
            'pool_config': {
                'pool_connections': 5,
                'pool_maxsize': 10,
                'retry_attempts': 3
            }
        }
    
    def _rate_limit(self):
        """Implement thread-safe rate limiting for DNB API requests."""
        with self._rate_limit_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
    
    def _make_optimized_request(self, url: str, params: Dict) -> Optional[requests.Response]:
        """Make an optimized request with performance tracking."""
        start_time = time.time()
        
        try:
            self._rate_limit()
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Track performance
            request_time = time.time() - start_time
            self._request_count += 1
            self._total_request_time += request_time
            
            return response
            
        except Exception as e:
            print(f"DNB optimized request failed: {e}")
            return None
