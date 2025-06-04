"""
PubMed API Client for searching biomedical publications.

This module provides a client for searching PubMed using the NCBI E-utilities API.
"""

import requests
import xml.etree.ElementTree as ET
import time
from typing import List, Dict, Optional
from urllib.parse import urlencode, quote
import re

from .database_interface import DatabaseInterface, PublicationSchema


class PubMedClient(DatabaseInterface):
    """Client for interacting with the PubMed database via NCBI E-utilities API."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    ESEARCH_URL = BASE_URL + "esearch.fcgi"
    EFETCH_URL = BASE_URL + "efetch.fcgi"
    
    def __init__(self, api_key: str = "fd409653aa8c7f336421d20a0e862459b507", 
                 email: str = "dnbspytool@example.com", timeout: int = 30):
        """
        Initialize the PubMed client.
        
        Args:
            api_key: NCBI API key for increased rate limits
            email: Email address (required by NCBI guidelines)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.email = email
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DNB-Spytool-PubMed/1.0.0 (Python)'
        })
        
        # Rate limiting: 10 requests/second with API key, 3/second without
        self.rate_limit_delay = 0.1 if api_key else 0.34
        self.last_request_time = 0
    
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
        """Implement rate limiting for API requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
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
        Search for PubMed IDs using esearch.
        
        Args:
            query: Search query
            max_results: Maximum results
            start_record: Starting record
            
        Returns:
            Dict with PMIDs and metadata
        """
        self._rate_limit()
        
        params = self._build_search_params(query, max_results, start_record)
        
        try:
            response = self.session.get(self.ESEARCH_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            
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
            
            return {
                'pmids': pmids,
                'total_count': total_count,
                'start_record': start_record
            }
            
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return {'pmids': [], 'total_count': 0, 'start_record': start_record}
    
    def _fetch_publications(self, pmids: List[str]) -> List[Dict]:
        """
        Fetch publication details using efetch.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            List of publication dictionaries
        """
        if not pmids:
            return []
        
        self._rate_limit()
        
        params = self._build_fetch_params(pmids)
        
        try:
            response = self.session.get(self.EFETCH_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            
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
                    # Normalize to standard schema
                    normalized_pub = PublicationSchema.normalize_publication(pub)
                    publications.append(normalized_pub)
                    
        except Exception as e:
            print(f"Error parsing MEDLINE XML: {e}")
        
        return publications
    
    def _extract_publication_data(self, article_elem: ET.Element) -> Optional[Dict]:
        """
        Extract publication data from a single PubmedArticle element.
        
        Args:
            article_elem: XML element containing article data
            
        Returns:
            Dictionary with publication data
        """
        try:
            pub = {'database_source': 'PubMed'}
            
            # PMID
            pmid_elem = article_elem.find('.//PMID')
            pub['pmid'] = pmid_elem.text if pmid_elem is not None else None
            
            # Title
            title_elem = article_elem.find('.//ArticleTitle')
            pub['title'] = title_elem.text if title_elem is not None else 'No title available'
            
            # Authors
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
            
            # Abstract
            abstract_elem = article_elem.find('.//AbstractText')
            pub['abstract'] = abstract_elem.text if abstract_elem is not None else None
            
            # Journal
            journal_elem = article_elem.find('.//Journal/Title')
            if journal_elem is None:
                journal_elem = article_elem.find('.//MedlineTA')
            pub['journal'] = journal_elem.text if journal_elem is not None else None
            
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
            
            # DOI
            for id_elem in article_elem.findall('.//ArticleId'):
                if id_elem.get('IdType') == 'doi':
                    pub['doi'] = id_elem.text
                    break
            
            # Publication type
            pub_types = []
            for pt_elem in article_elem.findall('.//PublicationType'):
                if pt_elem.text:
                    pub_types.append(pt_elem.text)
            pub['publication_type'] = ', '.join(pub_types) if pub_types else None
            
            # MeSH terms (subject headings)
            mesh_terms = []
            for mesh in article_elem.findall('.//MeshHeading/DescriptorName'):
                if mesh.text:
                    mesh_terms.append(mesh.text)
            pub['subject_headings'] = ', '.join(mesh_terms) if mesh_terms else None
            
            # Language
            lang_elem = article_elem.find('.//Language')
            pub['language'] = lang_elem.text if lang_elem is not None else None
            
            # ISSN
            issn_elem = article_elem.find('.//ISSN')
            pub['issn'] = issn_elem.text if issn_elem is not None else None
            
            return pub
            
        except Exception as e:
            print(f"Error extracting publication data: {e}")
            return None
    
    def search_publications(self, query: str, max_results: int = 100, **kwargs) -> List[Dict]:
        """
        Search for publications in PubMed.
        
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
        
        return all_publications[:max_results]
    
    def search_by_author(self, author_name: str, max_results: int = 100) -> Dict:
        """
        Search for publications by a specific author.
        
        Args:
            author_name: Name of the author
            max_results: Maximum results to return
            
        Returns:
            Dict with publications and metadata
        """
        # Format author query for PubMed
        author_query = f'"{author_name}"[Author]'
        
        publications = self.search_publications(author_query, max_results)
        
        return {
            'publications': publications,
            'total_records': len(publications),
            'author': author_name,
            'database': 'PubMed'
        }
