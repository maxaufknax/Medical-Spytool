"""
PubMed API Client for searching biomedical publications.

This module provides a client for searching PubMed using the NCBI E-utilities API.
"""

import requests
import xml.etree.ElementTree as ET
import time
import logging
from typing import List, Dict, Optional, Any
from urllib.parse import urlencode, quote
import re

logger = logging.getLogger(__name__)

class PubMedClient:
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
    
    def test_connection(self) -> bool:
        """Test if the PubMed API is accessible."""
        try:
            params = {
                'db': 'pubmed',
                'term': 'test',
                'retmax': 1,
                'retmode': 'xml',
                'email': self.email
            }
            
            if self.api_key:
                params['api_key'] = self.api_key
            
            response = self.session.get(self.ESEARCH_URL, params=params, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"PubMed connection test failed: {e}")
            return False
    
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
        """Build parameters for esearch request."""
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
        """Build parameters for efetch request."""
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
        """Search for PubMed IDs using esearch."""
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
            logger.error(f"Error searching PubMed: {e}")
            return {'pmids': [], 'total_count': 0, 'start_record': start_record}
    
    def _fetch_publications(self, pmids: List[str]) -> List[Dict]:
        """Fetch publication details using efetch."""
        if not pmids:
            return []
        
        self._rate_limit()
        
        params = self._build_fetch_params(pmids)
        
        try:
            response = self.session.get(self.EFETCH_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            return self._parse_medline_xml(response.text)
            
        except Exception as e:
            logger.error(f"Error fetching PubMed publications: {e}")
            return []
    
    def _parse_medline_xml(self, xml_content: str) -> List[Dict]:
        """Parse MEDLINE XML format to extract publication data."""
        publications = []
        
        try:
            root = ET.fromstring(xml_content)
            
            for article in root.findall('.//PubmedArticle'):
                pub = self._extract_publication_data(article)
                if pub:
                    publications.append(pub)
                    
        except Exception as e:
            logger.error(f"Error parsing MEDLINE XML: {e}")
        
        return publications
    
    def _extract_publication_data(self, article_elem: ET.Element) -> Optional[Dict]:
        """Extract publication data from a single PubmedArticle element."""
        try:
            pub = {'database_source': 'PubMed'}
            
            # PMID
            pmid_elem = article_elem.find('.//PMID')
            pub['pmid'] = pmid_elem.text if pmid_elem is not None else None
            pub['id'] = pub['pmid']  # Use PMID as primary ID
            
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
            pub['description'] = pub['abstract']  # Alias for consistency
            
            # Journal
            journal_elem = article_elem.find('.//Journal/Title')
            if journal_elem is None:
                journal_elem = article_elem.find('.//MedlineTA')
            pub['journal'] = journal_elem.text if journal_elem is not None else None
            pub['publisher'] = pub['journal']  # Alias for consistency
              # Publication year
            year_elem = article_elem.find('.//PubDate/Year')
            if year_elem is not None:
                pub['publication_year'] = int(year_elem.text)
                pub['year'] = pub['publication_year']  # Alias for consistency
            else:
                # Try to extract from MedlineDate
                medline_date = article_elem.find('.//PubDate/MedlineDate')
                if medline_date is not None:
                    year_match = re.search(r'(\d{4})', medline_date.text)
                    if year_match:
                        pub['publication_year'] = int(year_match.group(1))
                        pub['year'] = pub['publication_year']
                else:
                    pub['publication_year'] = None
                    pub['year'] = 'Unknown'
            
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
            pub['type'] = pub['publication_type']  # Alias for consistency
            
            # MeSH terms (subject headings)
            mesh_terms = []
            for mesh in article_elem.findall('.//MeshHeading/DescriptorName'):
                if mesh.text:
                    mesh_terms.append(mesh.text)
            pub['subject_headings'] = ', '.join(mesh_terms) if mesh_terms else None
            pub['subjects'] = mesh_terms  # Keep as list for consistency
            
            # Language
            lang_elem = article_elem.find('.//Language')
            pub['language'] = lang_elem.text if lang_elem is not None else None
            pub['languages'] = [pub['language']] if pub['language'] else []
            
            # ISSN
            issn_elem = article_elem.find('.//ISSN')
            pub['issn'] = issn_elem.text if issn_elem is not None else None
            
            # ISBN (not typically available in PubMed, but add for consistency)
            pub['isbn'] = []
              # URLs (construct from PMID)
            if pub['pmid']:
                pub['url'] = f"https://pubmed.ncbi.nlm.nih.gov/{pub['pmid']}/"
                pub['urls'] = [pub['url']]
            else:
                pub['urls'] = []
            
            # Set source for analytics
            pub['source'] = 'PubMed'
            
            return pub
            
        except Exception as e:
            logger.error(f"Error extracting publication data: {e}")
            return None
    
    def search_publications(self, author_name: str, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for publications by author with automatic pagination.
        
        Args:
            author_name: The author's name to search for
            max_results: Maximum number of results to return (None for all)
            
        Returns:
            List of publication dictionaries
        """
        # Format author query for PubMed
        author_query = f'"{author_name}"[Author]'
        
        all_publications = []
        start_record = 0
        batch_size = 200  # Reasonable batch size for PubMed
        
        logger.info(f"Starting PubMed search for author: {author_name}")
        
        try:
            # Continue searching until we have enough results
            while max_results is None or len(all_publications) < max_results:
                remaining = (max_results - len(all_publications)) if max_results else batch_size
                current_batch_size = min(remaining, batch_size)
                
                # Search for PMIDs
                search_result = self._search_pmids(author_query, current_batch_size, start_record)
                pmids = search_result['pmids']
                
                if not pmids:
                    logger.info("No more PMIDs found")
                    break
                
                logger.debug(f"Found {len(pmids)} PMIDs, fetching details...")
                
                # Fetch publication details
                publications = self._fetch_publications(pmids)
                all_publications.extend(publications)
                
                logger.debug(f"Retrieved {len(publications)} publications, total: {len(all_publications)}")
                
                # Check if we've got all available results
                if len(pmids) < current_batch_size:
                    logger.info("Reached end of available results")
                    break
                    
                start_record += len(pmids)
                
                # Rate limiting between batches
                time.sleep(0.5)
            
            final_results = all_publications[:max_results] if max_results else all_publications
            logger.info(f"PubMed search completed: {len(final_results)} publications retrieved")
            return final_results
            
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            raise

    def search_by_author(self, author_name: str, max_results: int = 100) -> Dict[str, Any]:
        """
        Search for publications by a specific author.
        
        Args:
            author_name: Name of the author
            max_results: Maximum results to return
            
        Returns:
            Dict with publications and metadata
        """
        publications = self.search_publications(author_name, max_results)
        
        return {
            'records': publications,
            'total_records': len(publications),
            'author': author_name,
            'database': 'PubMed'
        }
