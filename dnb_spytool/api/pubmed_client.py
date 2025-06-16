"""
PubMed API Client for searching biomedical publications.

This module provides a client for searching PubMed using the NCBI E-utilities API.
"""

import requests
import time
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
import threading
from urllib.parse import urlencode
import re

# Enhanced imports for connection pooling
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import concurrent.futures

from .database_interface import DatabaseInterface, PublicationSchema
# Phase 2 Step 4 - Cache integration
from ..core.cache_manager import QueryCacheManager


class PubMedClient(DatabaseInterface):
    """Client for interacting with the PubMed database via NCBI E-utilities API."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    ESEARCH_URL = BASE_URL + "esearch.fcgi"
    EFETCH_URL = BASE_URL + "efetch.fcgi"
    
    def __init__(self, api_key: str = "fd409653aa8c7f336421d20a0e862459b507", 
                 email: str = "dnbspytool@example.com", timeout: int = 30):
        """
        Initialize the PubMed client with enhanced connection pooling.
        
        Args:
            api_key: NCBI API key for increased rate limits
            email: Email address (required by NCBI guidelines)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.email = email
        self.timeout = timeout
        
        # Enhanced session with connection pooling and retry strategy
        self.session = self._create_optimized_session()
        
        # Rate limiting: 10 requests/second with API key, 3/second without
        self.rate_limit_delay = 0.1 if api_key else 0.34
        self.last_request_time = 0
        self._rate_limit_lock = threading.Lock()
        
        # Connection stats for monitoring
        self._request_count = 0
        self._total_request_time = 0.0

        # Initialize cache manager
        self.cache_manager = QueryCacheManager()
    
    def _create_optimized_session(self) -> requests.Session:
        """Create an optimized session with connection pooling and retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],  # Updated parameter name
            backoff_factor=1,
            respect_retry_after_header=True
        )
        
        # Configure HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=10,  # Number of connection pools
            pool_maxsize=20,      # Max connections per pool
            max_retries=retry_strategy,
            pool_block=False      # Don't block when pool is full
        )
        
        # Mount adapters for both HTTP and HTTPS
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set optimized headers
        session.headers.update({
            'User-Agent': 'Medical-Spytool/1.4-beta (Python; Connection-Pooled)',
            'Accept': 'application/xml,text/xml',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        })
        
        return session
    
    def configure_api(self, api_key: str = "", email: str = "", tool_name: str = ""):
        """
        Configure API settings with enhanced session management.
        
        Args:
            api_key: NCBI API key for increased rate limits
            email: Email address (required by NCBI guidelines)
            tool_name: Tool name for identification
        """
        self.api_key = api_key.strip() if api_key else ""
        self.email = email.strip() if email else "dnbspytool@example.com"
        
        # Update rate limiting based on API key
        self.rate_limit_delay = 0.1 if self.api_key else 0.34
        
        # Update User-Agent header with enhanced identification
        user_agent = f"{tool_name or 'Medical-Spytool'}/1.4-beta (Python; {self.email}; Connection-Pooled)"
        self.session.headers.update({'User-Agent': user_agent})
        
        # Reset performance counters
        self._request_count = 0
        self._total_request_time = 0.0
        
        print(f"✓ PubMed API configured - Rate limit: {10 if self.api_key else 3} req/sec")
        print(f"✓ Connection pooling enabled: {self.session.adapters}")
    
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
                'pool_connections': 10,
                'pool_maxsize': 20,
                'retry_attempts': 3
            },
            'cache_stats': cache_stats
        }
    
    def test_connection(self) -> bool:
        """
        Test if the PubMed API is accessible with current configuration.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            params = {
                'db': 'pubmed',
                'term': 'test[Title]',
                'retmax': 1,
                'retmode': 'xml',
                'email': self.email
            }
            
            if self.api_key:
                params['api_key'] = self.api_key
            
            response = self.session.get(self.ESEARCH_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                # Check if the response contains valid XML with results
                try:
                    root = ET.fromstring(response.content)
                    # Look for either results or error messages
                    if root.tag == 'eSearchResult':
                        return True
                    else:
                        return False
                except ET.ParseError:
                    return False
            else:
                return False
                
        except Exception as e:
            print(f"PubMed connection test failed: {e}")
            return False
    
    @property
    def database_name(self) -> str:
        """Return the name of the database."""
        return "PubMed"
    
    @property
    def max_results_per_request(self) -> int:
        """Return the maximum results per single request."""
        return 10000  # PubMed allows large result sets
    
    def get_database_info(self) -> Dict[str, str]:
        """Get information about the PubMed database."""
        return {
            'name': 'PubMed',
            'description': 'Biomedical literature database maintained by NCBI',
            'base_url': self.BASE_URL,
            'coverage': 'Biomedical and life science literature',
            'provider': 'National Center for Biotechnology Information (NCBI)',
            'api_version': 'E-utilities'
        }
    
    def validate_query(self, query: str) -> Dict[str, any]:
        """
        Validate a PubMed search query.
        
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
        
        # Basic validation - PubMed is quite flexible with queries
        return {
            'is_valid': True,
            'error': None,
            'cleaned_query': cleaned_query
        }
    
    def _rate_limit(self):
        """Implement thread-safe rate limiting for API requests."""
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
            print(f"Optimized request failed: {e}")
            return None
    
    def _build_search_params(self, query: str, max_results: int = 100, 
                           start_record: int = 0) -> Dict:
        """
        Build parameters for esearch request.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            start_record: Starting record number (0-based)
            
        Returns:
            Dictionary of request parameters
        """
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': min(max_results, 10000),
            'retstart': start_record,
            'retmode': 'xml',
            'sort': 'pub_date',
            'email': self.email
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
            
        return params
    
    def _build_fetch_params(self, pmids: List[str]) -> Dict:
        """
        Build parameters for efetch request.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            Dictionary of request parameters
        """
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml',
            'rettype': 'medline',
            'email': self.email
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
            
        return params
    
    def _search_pmids(self, query: str, max_results: int = 100, 
                      start_record: int = 0) -> Dict:
        """
        Search for PubMed IDs using esearch with optimized requests and caching.
        
        Args:
            query: Search query
            max_results: Maximum results
            start_record: Starting record
            
        Returns:
            Dict with PMIDs and metadata
        """
        # Create cache key for PMID search
        pmid_cache_key = f"pubmed_pmids_{hash(query)}_{max_results}_{start_record}"
        
        # Check cache first
        cached_pmids = self.cache_manager.get(pmid_cache_key, "pubmed")
        if cached_pmids is not None:
            return cached_pmids
        
        params = self._build_search_params(query, max_results, start_record)
        
        try:
            response = self._make_optimized_request(self.ESEARCH_URL, params)
            if not response:
                return {'pmids': [], 'total_count': 0, 'start_record': start_record}
            
            # Parse XML response
            root = ET.fromstring(response.text)
            
            # Extract PMIDs
            pmids = []
            for id_elem in root.findall('.//Id'):
                if id_elem.text:
                    pmids.append(id_elem.text)
            
            # Extract total count
            count_elem = root.find('.//Count')
            total_count = int(count_elem.text) if count_elem is not None else len(pmids)
            
            result = {
                'pmids': pmids,
                'total_count': total_count,
                'start_record': start_record
            }
            
            # Cache the result            self.cache_manager.put(pmid_cache_key, "pubmed", result)
            
            return result
            
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return {'pmids': [], 'total_count': 0, 'start_record': start_record}
    
    def _fetch_publications(self, pmids: List[str]) -> List[Dict]:
        """
        Fetch publication details using efetch with optimized request handling.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            List of publication dictionaries
        """
        if not pmids:
            return []
        
        params = self._build_fetch_params(pmids)
        
        try:
            response = self._make_optimized_request(self.EFETCH_URL, params)
            if not response:
                return []
            
            return self._parse_medline_xml(response.text)
            
        except Exception as e:
            print(f"Error fetching PubMed publications: {e}")
            return []
    
    def _parse_medline_xml(self, xml_content: str) -> List[Dict]:
        """
        Parse MEDLINE XML format to extract publication data.
        
        Args:
            xml_content: XML response from efetch
            
        Returns:
            List of normalized publication dictionaries
        """
        publications = []
        
        try:
            root = ET.fromstring(xml_content)
            
            for article in root.findall('.//PubmedArticle'):
                pub = self._extract_publication_data(article)
                if pub:
                    # Enhance with URLs before normalization
                    pub = self._enhance_publication_with_urls(pub)
                    # Normalize to standard schema
                    normalized_pub = PublicationSchema.normalize_publication(pub)
                    publications.append(normalized_pub)
                    
        except Exception as e:
            print(f"Error parsing MEDLINE XML: {e}")
        
        return publications
    
    def _extract_publication_data(self, article_elem: ET.Element) -> Optional[Dict]:
        """
        Extract comprehensive publication data from a single PubmedArticle element with v1.4 enhancements.
        
        Args:
            article_elem: XML element containing article data
            
        Returns:
            Dictionary with enhanced publication data including new v1.4 fields
        """
        try:
            pub = {'database_source': 'PubMed'}
            
            # PMID
            pmid_elem = article_elem.find('.//PMID')
            pub['pmid'] = pmid_elem.text if pmid_elem is not None else None
            
            # Title
            title_elem = article_elem.find('.//ArticleTitle')
            pub['title'] = title_elem.text if title_elem is not None else 'No title available'
            
            # Authors (Enhanced with affiliations)
            authors = []
            for author in article_elem.findall('.//Author'):
                last_name = author.find('./LastName')
                first_name = author.find('./ForeName')
                initials = author.find('./Initials')
                
                if last_name is not None:
                    author_name = last_name.text
                    if first_name is not None:
                        author_name += f", {first_name.text}"
                    elif initials is not None:
                        author_name += f", {initials.text}"
                    authors.append(author_name)
            
            pub['authors'] = ', '.join(authors) if authors else 'No authors listed'
            
            # ENHANCED: Comprehensive affiliation data
            affiliation_data = self._extract_enhanced_affiliations(article_elem)
            pub.update({
                'affiliations': '; '.join(affiliation_data['all_affiliations']),
                'institutions': ', '.join(affiliation_data['institutions']),
                'countries': ', '.join(affiliation_data['countries']),
                'departments': ', '.join(affiliation_data['departments']),
                'author_emails': ', '.join(affiliation_data['emails'])
            })
            
            # Abstract (Enhanced with word count)
            abstract_elem = article_elem.find('.//AbstractText')
            abstract_text = abstract_elem.text if abstract_elem is not None else None
            pub['abstract'] = abstract_text
            pub['abstract_word_count'] = len(abstract_text.split()) if abstract_text else 0            
            # ENHANCED: Comprehensive journal metadata
            journal_data = self._extract_journal_metadata(article_elem)
            pub.update({
                'journal': journal_data['journal_title'] or journal_data['journal_abbreviation'],
                'journal_abbreviation': journal_data['journal_abbreviation'],
                'journal_issn': journal_data['issn_print'] or journal_data['issn_electronic'],
                'issn_print': journal_data['issn_print'],
                'issn_electronic': journal_data['issn_electronic'],
                'journal_volume': journal_data['journal_volume'],
                'journal_issue': journal_data['journal_issue'],
                'journal_pages': journal_data['journal_pages'],
                'journal_country': journal_data['journal_country'],
                'nlm_unique_id': journal_data['nlm_unique_id']
            })
            
            # Publication year
            year_elem = article_elem.find('.//PubDate/Year')
            if year_elem is not None:
                pub['publication_year'] = int(year_elem.text)
            else:
                # Try to extract from MedlineDate
                medline_date = article_elem.find('.//PubDate/MedlineDate')
                if medline_date is not None:
                    year_match = re.search(r'(\d{4})', medline_date.text)
                    if year_match:
                        pub['publication_year'] = int(year_match.group(1))
            
            # DOI and other IDs
            pub['article_ids'] = {}
            for id_elem in article_elem.findall('.//ArticleId'):
                id_type = id_elem.get('IdType')
                if id_type and id_elem.text:
                    pub['article_ids'][id_type] = id_elem.text
                    if id_type == 'doi':
                        pub['doi'] = id_elem.text
                    elif id_type == 'pmc':
                        pub['pmc'] = id_elem.text
            
            # ENHANCED: Comprehensive publication types
            pub_types_data = self._extract_comprehensive_publication_types(article_elem)
            pub.update({
                'publication_types': pub_types_data['publication_types'],
                'publication_type': pub_types_data['primary_type'],
                'is_research_article': pub_types_data['is_research_article'],
                'is_review': pub_types_data['is_review'],
                'is_case_report': pub_types_data['is_case_report'],
                'is_clinical_trial': pub_types_data['is_clinical_trial'],
                'is_meta_analysis': pub_types_data['is_meta_analysis']
            })
            
            # ENHANCED: Comprehensive MeSH data
            mesh_data = self._extract_comprehensive_mesh_data(article_elem)
            pub.update({
                'mesh_headings': mesh_data['mesh_headings'],
                'mesh_qualifiers': mesh_data['mesh_qualifiers'],
                'major_topics': mesh_data['major_topics'],
                'mesh_categories': mesh_data['mesh_categories'],
                'subject_headings': ', '.join(mesh_data['mesh_headings']) if mesh_data['mesh_headings'] else None
            })
            
            # Keywords (Enhanced extraction including both MeSH and author keywords)
            keywords = []
            for keyword in article_elem.findall('.//Keyword'):
                if keyword.text:
                    keywords.append(keyword.text)
            # Add MeSH terms as keywords
            keywords.extend(mesh_data['mesh_headings'])
            pub['keywords'] = list(set(keywords))  # Remove duplicates
            
            # Language
            lang_elem = article_elem.find('.//Language')
            pub['language'] = lang_elem.text if lang_elem is not None else None
            
            # ENHANCED: Comprehensive funding data
            funding_data = self._extract_enhanced_funding_data(article_elem)
            pub.update({
                'grants': funding_data['grants'],
                'funding_agencies': funding_data['funding_agencies'],
                'grant_numbers': funding_data['grant_numbers'],
                'funding_countries': funding_data['funding_countries'],
                'has_funding': funding_data['has_funding'],
                'funding': '; '.join([f"{g.get('agency', '')}: {g.get('grant_id', '')}" 
                                    for g in funding_data['grants']]) if funding_data['grants'] else None
            })
            
            # ENHANCED: Citation metrics and indexing status
            metrics_data = self._extract_citation_metrics(article_elem)
            pub.update({
                'pubmed_indexed': metrics_data['pubmed_indexed'],
                'medline_indexed': metrics_data['medline_indexed'],
                'pmc_available': metrics_data['pmc_available'],
                'free_full_text': metrics_data['free_full_text'],
                'citation_subset': metrics_data['citation_subset']
            })
            
            # Conflict of interest statement
            conflict_elem = article_elem.find('.//CoiStatement')
            pub['conflict_statement'] = conflict_elem.text if conflict_elem is not None else None
              # ENHANCED: Journal category classification
            pub['journal_category'] = self._derive_journal_category(pub.get('journal', ''))
            
            return pub
            
        except Exception as e:
            print(f"Error extracting publication data: {e}")
            return None
    
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
        
        # Check for PubMed URL
        if publication.get('pmid'):
            urls.append(f"https://pubmed.ncbi.nlm.nih.gov/{publication['pmid']}/")
        
        # Check for PMC URL (if available)
        if publication.get('pmc_id'):
            urls.append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{publication['pmc_id']}/")
        
        # Check for direct URL
        if publication.get('url'):
            urls.append(publication['url'])
        
        # Generate PubMed search URL based on title as fallback
        if publication.get('title'):
            title_query = publication['title'].replace(' ', '+')
            urls.append(f"https://pubmed.ncbi.nlm.nih.gov/?term={title_query}")
        
        return urls
    
    def get_primary_url(self, publication: Dict) -> Optional[str]:
        """
        Get the primary/preferred URL for a publication.
        
        Args:
            publication: Publication dictionary
            
        Returns:
            Primary URL or None
        """
        # Priority order: DOI, PubMed, PMC, direct URL
        if publication.get('doi'):
            return f"https://doi.org/{publication['doi']}"
        
        if publication.get('pmid'):
            return f"https://pubmed.ncbi.nlm.nih.gov/{publication['pmid']}/"
        
        if publication.get('pmc_id'):
            return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{publication['pmc_id']}/"
        
        if publication.get('url'):
            return publication['url']
        
        return None

    def search_publications(self, query: str, max_results: int = 100, **kwargs) -> List[Dict]:
        """
        Search for publications in PubMed with caching support.
        
        Args:
            query: Search query (author name or other terms)
            max_results: Maximum number of results to return
            **kwargs: Additional parameters (start_record, etc.)
            
        Returns:
            List of publication dictionaries
        """
        # Validate query
        validation = self.validate_query(query)
        if not validation['is_valid']:
            raise ValueError(f"Invalid query: {validation['error']}")
        
        query = validation['cleaned_query']
        start_record = kwargs.get('start_record', 0)
        
        # Create cache key from query parameters
        cache_key = f"pubmed_search_{hash(query)}_{max_results}_{start_record}"
        
        # Check cache first
        cached_result = self.cache_manager.get(cache_key, "pubmed")
        if cached_result is not None:
            print(f"Cache hit for PubMed query: {query[:50]}...")
            return cached_result
        
        all_publications = []
        current_start = start_record
        
        # Handle pagination
        while len(all_publications) < max_results:
            remaining = max_results - len(all_publications)
            batch_size = min(remaining, 200)  # Reasonable batch size
            
            # Search for PMIDs
            search_result = self._search_pmids(query, batch_size, current_start)
            pmids = search_result['pmids']
            
            if not pmids:
                break
            
            # Fetch publication details
            publications = self._fetch_publications(pmids)
            all_publications.extend(publications)
            
            # Check if we've got all available results
            if len(pmids) < batch_size:
                break
                
            current_start += len(pmids)
            
            # Rate limiting between batches
            time.sleep(0.5)
        
        # Limit results and cache the final result
        final_publications = all_publications[:max_results]
        
        # Store result in cache
        self.cache_manager.put(cache_key, "pubmed", final_publications)
        print(f"Cached PubMed search result: {len(final_publications)} publications")
        
        return final_publications
    
    def search_by_author(self, author_name: str, max_results: int = 100) -> Dict:
        """
        Search for publications by a specific author with caching support.
        
        Args:
            author_name: Name of the author
            max_results: Maximum results to return
            
        Returns:
            Dict with publications and metadata
        """
        # Create cache key for author search
        author_cache_key = f"pubmed_author_{hash(author_name)}_{max_results}"
        
        # Check cache first
        cached_author_result = self.cache_manager.get(author_cache_key, "pubmed")
        if cached_author_result is not None:
            print(f"Cache hit for PubMed author: {author_name}")
            return cached_author_result
        
        # Format author query for PubMed with intelligent name handling
        formatted_name = self._format_author_name_for_pubmed(author_name)
        author_query = f'"{formatted_name}"[Author]'
        
        print(f"🔍 PubMed search: '{author_name}' -> formatted as: '{formatted_name}'")
        
        publications = self.search_publications(author_query, max_results)
        
        result = {
            'publications': publications,
            'total_records': len(publications),
            'author': author_name,
            'database': 'PubMed'
        }
        
        # Cache the result
        self.cache_manager.put(author_cache_key, "pubmed", result)
        print(f"Cached PubMed author search: {author_name}")
        
        return result
    
    def extract_urls_from_publication(self, publication: Dict) -> Dict:
        """
        Extract all available URLs from a PubMed publication record.
        
        Args:
            publication: Publication dictionary from PubMed
            
        Returns:
            Dictionary with URL types and their values
        """
        urls = {}
        
        try:
            # PubMed URL based on PMID
            if publication.get('pmid'):
                urls['pubmed'] = f"https://pubmed.ncbi.nlm.nih.gov/{publication['pmid']}/"
                urls['pubmed_abstract'] = f"https://pubmed.ncbi.nlm.nih.gov/{publication['pmid']}/?format=abstract"
            
            # PMC (PubMed Central) URL if available
            if publication.get('pmc'):
                urls['pmc'] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{publication['pmc']}/"
                urls['pmc_pdf'] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{publication['pmc']}/pdf/"
            
            # DOI URL
            if publication.get('doi'):
                urls['doi'] = f"https://doi.org/{publication['doi']}"
            
            # Journal-specific URLs
            journal = publication.get('journal', '').lower()
            if journal and publication.get('pmid'):
                if 'nature' in journal:
                    urls['nature'] = f"https://www.nature.com/articles/pmid{publication['pmid']}"
                elif 'science' in journal:
                    urls['science'] = f"https://science.sciencemag.org/lookup/pmid/{publication['pmid']}"
                elif 'cell' in journal:
                    urls['cell'] = f"https://www.cell.com/action/showCitFormats?pii=S0092-8674&doi={publication.get('doi', '')}"
            
            # PubMed LinkOut URLs (external publisher links)
            if publication.get('pmid'):
                urls['linkout'] = f"https://www.ncbi.nlm.nih.gov/sites/linkout?pmid={publication['pmid']}"
            
            # ClinicalTrials.gov if mentioned
            abstract = publication.get('abstract', '').lower()
            if 'clinicaltrials.gov' in abstract:
                # Try to extract clinical trial number
                import re
                ct_match = re.search(r'nct\d{8}', abstract, re.IGNORECASE)
                if ct_match:
                    ct_number = ct_match.group().upper()
                    urls['clinicaltrials'] = f"https://clinicaltrials.gov/study/{ct_number}"
            
            # Add the primary URL to the publication record
            if urls:
                publication['url'] = self._get_primary_url(urls)
                publication['all_urls'] = urls
            
        except Exception as e:
            print(f"Warning: URL extraction failed for PubMed publication: {e}")
        
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
            'pmc',
            'pubmed',
            'nature',
            'science', 
            'cell',
            'linkout',
            'clinicaltrials',
            'pubmed_abstract'
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
    
    def _format_author_name_for_pubmed(self, author_name: str) -> str:
        """
        Format author name for optimal PubMed searching.
        
        PubMed typically works better with "Last, First" format.
        
        Args:
            author_name: Original author name
            
        Returns:
            Formatted author name for PubMed search
        """
        # Clean the name
        clean_name = author_name.strip()
        
        # If it already contains a comma, assume it's properly formatted
        if ',' in clean_name:
            return clean_name
        
        # Split by spaces and try to detect first/last name pattern
        parts = clean_name.split()
        
        if len(parts) == 2:
            # Assume "First Last" format, convert to "Last, First"
            first_name, last_name = parts
            return f"{last_name}, {first_name}"
        elif len(parts) == 3:
            # Assume "First Middle Last" format, convert to "Last, First Middle"
            first_name, middle_name, last_name = parts
            return f"{last_name}, {first_name} {middle_name}"
        elif len(parts) > 3:
            # More complex case: assume last part is surname
            last_name = parts[-1]
            first_parts = ' '.join(parts[:-1])
            return f"{last_name}, {first_parts}"
        else:
            # Single name or unclear format, return as-is
            return clean_name
    
    def _get_author_name_variations(self, author_name: str) -> List[str]:
        """
        Generate multiple name format variations for comprehensive searching.
        
        Args:
            author_name: Original author name
            
        Returns:
            List of name variations to try
        """
        variations = [author_name.strip()]  # Always include original
        
        clean_name = author_name.strip()
        
        # If it doesn't contain comma, try different formats
        if ',' not in clean_name:
            parts = clean_name.split()
            
            if len(parts) == 2:
                first, last = parts
                variations.extend([
                    f"{last}, {first}",  # Last, First
                    f"{last} {first[0]}",  # Last FirstInitial
                    f"{last}, {first[0]}",  # Last, FirstInitial
                    f"{first[0]} {last}",  # FirstInitial Last
                ])
            elif len(parts) >= 3:
                first = parts[0]
                last = parts[-1]
                middle_parts = ' '.join(parts[1:-1])
                variations.extend([
                    f"{last}, {first} {middle_parts}",  # Last, First Middle
                    f"{last}, {first}",  # Last, First (without middle)
                    f"{last} {first[0]}",  # Last FirstInitial
                ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for var in variations:
            if var not in seen:
                unique_variations.append(var)
                seen.add(var)
                
        return unique_variations

    # =====================================================================================
    # ENHANCED v1.4 METHODS FOR COMPREHENSIVE PUBMED DATA EXTRACTION
    # =====================================================================================
    
    def _extract_enhanced_affiliations(self, article_elem: ET.Element) -> Dict[str, any]:
        """Extract comprehensive affiliation data including institutions and countries."""
        affiliations_data = {
            'all_affiliations': [],
            'institutions': [],
            'countries': [],
            'departments': [],
            'emails': []
        }
        
        try:
            for author in article_elem.findall('.//Author'):
                affiliation_info = author.find('./AffiliationInfo')
                if affiliation_info is not None:
                    affiliation = affiliation_info.find('./Affiliation')
                    if affiliation is not None and affiliation.text:
                        aff_text = affiliation.text
                        affiliations_data['all_affiliations'].append(aff_text)
                        
                        # Extract institution names (usually first part before comma)
                        institution = self._extract_institution_from_affiliation(aff_text)
                        if institution:
                            affiliations_data['institutions'].append(institution)
                        
                        # Extract country
                        country = self._extract_country_from_affiliation(aff_text)
                        if country:
                            affiliations_data['countries'].append(country)
                        
                        # Extract department/faculty
                        department = self._extract_department_from_affiliation(aff_text)
                        if department:
                            affiliations_data['departments'].append(department)
                        
                        # Extract email if present
                        email = self._extract_email_from_affiliation(aff_text)
                        if email:
                            affiliations_data['emails'].append(email)
            
            # Remove duplicates and join
            for key in affiliations_data:
                if isinstance(affiliations_data[key], list):
                    affiliations_data[key] = list(set(affiliations_data[key]))
            
            return affiliations_data
            
        except Exception as e:
            print(f"Error extracting enhanced affiliations: {e}")
            return affiliations_data
    
    def _extract_institution_from_affiliation(self, affiliation: str) -> Optional[str]:
        """Extract institution name from affiliation string."""
        if not affiliation:
            return None
        
        # Common institution patterns
        import re
        
        # Look for university, hospital, institute patterns
        institution_patterns = [
            r'(.*?(?:University|Universität|Universidad|Université)[^,]*)',
            r'(.*?(?:Hospital|Klinik|Clinic|Medical Center)[^,]*)',
            r'(.*?(?:Institute|Institut|Centro)[^,]*)',
            r'(.*?(?:School of|Faculty of|Department of)[^,]*)',
            r'^([^,]+)'  # Fallback: first part before comma
        ]
        
        for pattern in institution_patterns:
            match = re.search(pattern, affiliation, re.IGNORECASE)
            if match:
                institution = match.group(1).strip()
                if len(institution) > 5:  # Minimum reasonable length
                    return institution
        
        return None
    
    def _extract_country_from_affiliation(self, affiliation: str) -> Optional[str]:
        """Extract country from affiliation string."""
        if not affiliation:
            return None
        
        import re
        
        # Common country patterns at the end of affiliations
        country_patterns = [
            r',\s*([A-Z][a-z\s]+)\.?\s*$',  # Country at end after comma
            r'\b(United States|USA|US)\b',
            r'\b(United Kingdom|UK)\b',
            r'\b(Germany|Deutschland)\b',
            r'\b(France|Frankreich)\b',
            r'\b(Italy|Italien)\b',
            r'\b(Spain|Spanien)\b',
            r'\b(Netherlands|Niederlande)\b',
            r'\b(Belgium|Belgien)\b',
            r'\b(Switzerland|Schweiz)\b',
            r'\b(Austria|Österreich)\b',
            r'\b(Sweden|Schweden)\b',
            r'\b(Norway|Norwegen)\b',
            r'\b(Denmark|Dänemark)\b',
            r'\b(Finland|Finnland)\b',
            r'\b(Canada|Kanada)\b',
            r'\b(Australia|Australien)\b',
            r'\b(Japan|Japan)\b',
            r'\b(China|China)\b',
            r'\b(India|Indien)\b',
            r'\b(Brazil|Brasilien)\b',
            r'\b(Russia|Russland)\b'
        ]
        
        for pattern in country_patterns:
            match = re.search(pattern, affiliation, re.IGNORECASE)
            if match:
                country = match.group(1).strip()
                if len(country) > 2:
                    return country
        
        return None
    
    def _extract_department_from_affiliation(self, affiliation: str) -> Optional[str]:
        """Extract department/faculty from affiliation string."""
        if not affiliation:
            return None
        
        import re
        
        # Look for department patterns
        dept_patterns = [
            r'(Department of [^,]+)',
            r'(Faculty of [^,]+)',
            r'(Division of [^,]+)',
            r'(Institute of [^,]+)',
            r'(Center for [^,]+)',
            r'(Abteilung für [^,]+)',
            r'(Klinik für [^,]+)'
        ]
        
        for pattern in dept_patterns:
            match = re.search(pattern, affiliation, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_email_from_affiliation(self, affiliation: str) -> Optional[str]:
        """Extract email address from affiliation string."""
        if not affiliation:
            return None
        
        import re
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, affiliation)
        
        if match:
            return match.group(0)
        
        return None
    
    def _extract_comprehensive_publication_types(self, article_elem: ET.Element) -> Dict[str, any]:
        """Extract comprehensive publication type information."""
        pub_types_data = {
            'publication_types': [],
            'primary_type': None,
            'is_research_article': False,
            'is_review': False,
            'is_case_report': False,
            'is_clinical_trial': False,
            'is_meta_analysis': False
        }
        
        try:
            # Extract all publication types
            for pt_elem in article_elem.findall('.//PublicationType'):
                if pt_elem.text:
                    pub_type = pt_elem.text.strip()
                    pub_types_data['publication_types'].append(pub_type)
            
            # Determine primary type and set flags
            if pub_types_data['publication_types']:
                # Priority order for primary type
                type_priorities = [
                    'Journal Article',
                    'Research Article', 
                    'Review',
                    'Case Reports',
                    'Clinical Trial',
                    'Meta-Analysis',
                    'Systematic Review'
                ]
                
                for priority_type in type_priorities:
                    for pub_type in pub_types_data['publication_types']:
                        if priority_type.lower() in pub_type.lower():
                            pub_types_data['primary_type'] = pub_type
                            break
                    if pub_types_data['primary_type']:
                        break
                
                # If no priority match, use first type
                if not pub_types_data['primary_type']:
                    pub_types_data['primary_type'] = pub_types_data['publication_types'][0]
                
                # Set boolean flags
                types_lower = [pt.lower() for pt in pub_types_data['publication_types']]
                pub_types_data['is_research_article'] = any('research' in t or 'journal article' in t for t in types_lower)
                pub_types_data['is_review'] = any('review' in t for t in types_lower)
                pub_types_data['is_case_report'] = any('case' in t for t in types_lower)
                pub_types_data['is_clinical_trial'] = any('trial' in t for t in types_lower)
                pub_types_data['is_meta_analysis'] = any('meta' in t for t in types_lower)
            
            return pub_types_data
            
        except Exception as e:
            print(f"Error extracting publication types: {e}")
            return pub_types_data
    
    def _extract_comprehensive_mesh_data(self, article_elem: ET.Element) -> Dict[str, any]:
        """Extract comprehensive MeSH data with hierarchical information."""
        mesh_data = {
            'mesh_headings': [],
            'mesh_qualifiers': [],
            'major_topics': [],
            'mesh_categories': [],
            'mesh_tree_numbers': []
        }
        
        try:
            for mesh_heading in article_elem.findall('.//MeshHeading'):
                descriptor = mesh_heading.find('./DescriptorName')
                if descriptor is not None and descriptor.text:
                    mesh_term = descriptor.text
                    mesh_data['mesh_headings'].append(mesh_term)
                    
                    # Check if this is a major topic
                    major_topic = descriptor.get('MajorTopicYN', 'N')
                    if major_topic == 'Y':
                        mesh_data['major_topics'].append(mesh_term)
                    
                    # Extract UI attribute (unique identifier)
                    ui = descriptor.get('UI')
                    if ui:
                        mesh_data['mesh_tree_numbers'].append(ui)
                
                # Extract qualifiers
                for qualifier in mesh_heading.findall('./QualifierName'):
                    if qualifier.text:
                        mesh_data['mesh_qualifiers'].append(qualifier.text)
            
            # Derive categories from MeSH terms (simplified categorization)
            mesh_data['mesh_categories'] = self._categorize_mesh_terms(mesh_data['mesh_headings'])
            
            return mesh_data
            
        except Exception as e:
            print(f"Error extracting MeSH data: {e}")
            return mesh_data
    
    def _categorize_mesh_terms(self, mesh_terms: List[str]) -> List[str]:
        """Categorize MeSH terms into broader medical categories."""
        categories = set()
        
        category_keywords = {
            'Anatomy': ['anatomy', 'organ', 'tissue', 'cell', 'muscle', 'bone', 'blood'],
            'Diseases': ['disease', 'syndrome', 'disorder', 'cancer', 'tumor', 'infection'],
            'Drugs': ['drug', 'medication', 'therapy', 'treatment', 'pharmaceutical'],
            'Procedures': ['surgery', 'procedure', 'technique', 'method', 'intervention'],
            'Diagnostics': ['diagnosis', 'test', 'imaging', 'biomarker', 'screening'],
            'Physiology': ['physiology', 'function', 'metabolism', 'pathway', 'process'],
            'Genetics': ['gene', 'genetic', 'dna', 'rna', 'chromosome', 'mutation'],
            'Immunology': ['immune', 'antibody', 'antigen', 'lymphocyte', 'cytokine']
        }
        
        for mesh_term in mesh_terms:
            mesh_lower = mesh_term.lower()
            for category, keywords in category_keywords.items():
                if any(keyword in mesh_lower for keyword in keywords):
                    categories.add(category)
                    break
        
        return list(categories)
    
    def _extract_journal_metadata(self, article_elem: ET.Element) -> Dict[str, any]:
        """Extract comprehensive journal metadata."""
        journal_data = {
            'journal_title': None,
            'journal_abbreviation': None,
            'issn_print': None,
            'issn_electronic': None,
            'journal_volume': None,
            'journal_issue': None,
            'journal_pages': None,
            'journal_country': None,
            'nlm_unique_id': None
        }
        
        try:
            # Journal title
            journal_elem = article_elem.find('.//Journal/Title')
            if journal_elem is not None:
                journal_data['journal_title'] = journal_elem.text
            
            # Journal abbreviation
            abbrev_elem = article_elem.find('.//MedlineTA')
            if abbrev_elem is not None:
                journal_data['journal_abbreviation'] = abbrev_elem.text
            
            # ISSNs
            for issn_elem in article_elem.findall('.//ISSN'):
                issn_type = issn_elem.get('IssnType', 'Print')
                if issn_type == 'Print':
                    journal_data['issn_print'] = issn_elem.text
                elif issn_type == 'Electronic':
                    journal_data['issn_electronic'] = issn_elem.text
            
            # Volume, Issue, Pages
            volume_elem = article_elem.find('.//JournalIssue/Volume')
            if volume_elem is not None:
                journal_data['journal_volume'] = volume_elem.text
            
            issue_elem = article_elem.find('.//JournalIssue/Issue')
            if issue_elem is not None:
                journal_data['journal_issue'] = issue_elem.text
            
            pages_elem = article_elem.find('.//Pagination/MedlinePgn')
            if pages_elem is not None:
                journal_data['journal_pages'] = pages_elem.text
            
            # Country
            country_elem = article_elem.find('.//MedlineJournalInfo/Country')
            if country_elem is not None:
                journal_data['journal_country'] = country_elem.text
            
            # NLM Unique ID
            nlm_id_elem = article_elem.find('.//MedlineJournalInfo/NlmUniqueID')
            if nlm_id_elem is not None:
                journal_data['nlm_unique_id'] = nlm_id_elem.text
            
            return journal_data
            
        except Exception as e:
            print(f"Error extracting journal metadata: {e}")
            return journal_data
    
    def _extract_enhanced_funding_data(self, article_elem: ET.Element) -> Dict[str, any]:
        """Extract comprehensive funding and grant information."""
        funding_data = {
            'grants': [],
            'funding_agencies': [],
            'grant_numbers': [],
            'funding_countries': [],
            'has_funding': False
        }
        
        try:
            for grant in article_elem.findall('.//Grant'):
                grant_info = {}
                
                grant_id = grant.find('./GrantID')
                if grant_id is not None and grant_id.text:
                    grant_info['grant_id'] = grant_id.text
                    funding_data['grant_numbers'].append(grant_id.text)
                
                agency = grant.find('./Agency')
                if agency is not None and agency.text:
                    grant_info['agency'] = agency.text
                    funding_data['funding_agencies'].append(agency.text)
                
                acronym = grant.find('./Acronym')
                if acronym is not None and acronym.text:
                    grant_info['acronym'] = acronym.text
                
                country = grant.find('./Country')
                if country is not None and country.text:
                    grant_info['country'] = country.text
                    funding_data['funding_countries'].append(country.text)
                
                if grant_info:
                    funding_data['grants'].append(grant_info)
            
            # Remove duplicates
            funding_data['funding_agencies'] = list(set(funding_data['funding_agencies']))
            funding_data['grant_numbers'] = list(set(funding_data['grant_numbers']))
            funding_data['funding_countries'] = list(set(funding_data['funding_countries']))
            
            # Set funding flag
            funding_data['has_funding'] = len(funding_data['grants']) > 0
            
            return funding_data
            
        except Exception as e:
            print(f"Error extracting funding data: {e}")
            return funding_data
    
    def _extract_citation_metrics(self, article_elem: ET.Element) -> Dict[str, any]:
        """Extract available citation and impact metrics."""
        metrics_data = {
            'pubmed_indexed': False,
            'medline_indexed': False,
            'pmc_available': False,
            'free_full_text': False,
            'article_ids': {},
            'citation_subset': None
        }
        
        try:
            # Check indexing status
            status_elem = article_elem.find('.//PublicationStatus')
            if status_elem is not None:
                if status_elem.text in ['medline', 'pubmed']:
                    metrics_data['pubmed_indexed'] = True
                if status_elem.text == 'medline':
                    metrics_data['medline_indexed'] = True
            
            # Extract all article IDs
            for id_elem in article_elem.findall('.//ArticleId'):
                id_type = id_elem.get('IdType')
                if id_type and id_elem.text:
                    metrics_data['article_ids'][id_type] = id_elem.text
                    
                    # Check for PMC availability
                    if id_type == 'pmc':
                        metrics_data['pmc_available'] = True
            
            # Check for free full text indicators
            if 'pmc' in metrics_data['article_ids'] or 'doi' in metrics_data['article_ids']:
                metrics_data['free_full_text'] = True
            
            # Citation subset
            subset_elem = article_elem.find('.//CitationSubset')
            if subset_elem is not None:
                metrics_data['citation_subset'] = subset_elem.text
            
            return metrics_data
            
        except Exception as e:
            print(f"Error extracting citation metrics: {e}")
            return metrics_data
    
    def _derive_journal_category(self, journal_name: str) -> str:
        """Derive journal category from journal name (NEW v1.4 field)."""
        if not journal_name:
            return None
        
        journal_lower = journal_name.lower()
        
        # Medical categories mapping
        category_keywords = {
            'Medical': ['medicine', 'medical', 'clinical', 'patient', 'therapy', 'treatment'],
            'Biomedical': ['biomedical', 'biomedicine', 'molecular', 'cellular', 'biochemistry'],
            'Pharmacology': ['pharmacology', 'drug', 'pharmaceutical', 'medication'],
            'Surgery': ['surgery', 'surgical', 'operative'],
            'Cardiology': ['cardiology', 'heart', 'cardiac', 'cardiovascular'],
            'Neurology': ['neurology', 'brain', 'neural', 'neuroscience'],
            'Oncology': ['oncology', 'cancer', 'tumor', 'carcinoma'],
            'Pediatrics': ['pediatric', 'children', 'child', 'infant'],
            'Public Health': ['public health', 'epidemiology', 'prevention'],
            'Nursing': ['nursing', 'nurse'],
            'Dentistry': ['dental', 'dentistry', 'oral'],
            'Research': ['research', 'science', 'scientific', 'journal']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in journal_lower for keyword in keywords):
                return category
        
        return 'General Medical'
