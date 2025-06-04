import requests
import logging
from typing import List, Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

class DNBClient:
    def __init__(self, base_url: str = "https://services.dnb.de/sru/dnb"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DNB-Spytool/1.0'
        })

    def search_by_author(self, author_name: str, start_record: int = 1, 
                        max_records: int = 100) -> Dict[str, Any]:
        """
        Search for publications by author name using DNB SRU API.
        
        Args:
            author_name: The author's name to search for
            start_record: Starting record number (1-based)
            max_records: Maximum number of records to retrieve per request
            
        Returns:
            Dict containing search results and metadata
        """
        # Clean and format author name for search
        author_query = author_name.strip().replace(' ', ' AND ')
        
        params = {
            'version': '1.1',
            'operation': 'searchRetrieve',
            'query': f'per="{author_query}"',
            'recordSchema': 'oai_dc',
            'startRecord': start_record,
            'maximumRecords': min(max_records, 100)  # DNB limit is typically 100
        }
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse XML response
            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.content)
            
            # Extract namespace information
            ns = {
                'srw': 'http://www.loc.gov/zing/srw/',
                'dc': 'http://purl.org/dc/elements/1.1/',
                'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/'
            }
            
            # Get total number of records
            total_records_elem = root.find('.//srw:numberOfRecords', ns)
            total_records = int(total_records_elem.text) if total_records_elem is not None else 0
            
            # Extract records
            records = []
            for record in root.findall('.//srw:record', ns):
                dc_elem = record.find('.//oai_dc:dc', ns)
                if dc_elem is not None:
                    publication = self._parse_dc_record(dc_elem, ns)
                    if publication:
                        records.append(publication)
            
            return {
                'records': records,
                'total_records': total_records,
                'start_record': start_record,
                'records_returned': len(records)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"DNB API request failed: {e}")
            raise
        except ET.ParseError as e:
            logger.error(f"Failed to parse DNB response: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in DNB search: {e}")
            raise

    def _parse_dc_record(self, dc_elem, namespaces: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse a Dublin Core record into a standardized publication format."""
        try:
            publication = {
                'source': 'DNB',
                'title': '',
                'authors': [],
                'year': '',
                'journal': '',
                'doi': '',
                'abstract': '',
                'keywords': [],
                'language': '',
                'publisher': '',
                'isbn': '',
                'issn': ''
            }
            
            # Title
            title_elem = dc_elem.find('dc:title', namespaces)
            if title_elem is not None:
                publication['title'] = title_elem.text or ''
            
            # Authors
            for creator in dc_elem.findall('dc:creator', namespaces):
                if creator.text:
                    publication['authors'].append(creator.text.strip())
            
            # Publication year
            date_elem = dc_elem.find('dc:date', namespaces)
            if date_elem is not None and date_elem.text:
                # Extract year from date string
                import re
                year_match = re.search(r'\b(19|20)\d{2}\b', date_elem.text)
                if year_match:
                    publication['year'] = year_match.group()
            
            # Publisher
            publisher_elem = dc_elem.find('dc:publisher', namespaces)
            if publisher_elem is not None:
                publication['publisher'] = publisher_elem.text or ''
            
            # Language
            language_elem = dc_elem.find('dc:language', namespaces)
            if language_elem is not None:
                publication['language'] = language_elem.text or ''
            
            # Subject/Keywords
            for subject in dc_elem.findall('dc:subject', namespaces):
                if subject.text:
                    publication['keywords'].append(subject.text.strip())
            
            # Description/Abstract
            description_elem = dc_elem.find('dc:description', namespaces)
            if description_elem is not None:
                publication['abstract'] = description_elem.text or ''
            
            # Identifier (may contain ISBN, ISSN, DOI)
            for identifier in dc_elem.findall('dc:identifier', namespaces):
                if identifier.text:
                    id_text = identifier.text.upper()
                    if 'ISBN' in id_text:
                        publication['isbn'] = identifier.text
                    elif 'ISSN' in id_text:
                        publication['issn'] = identifier.text
                    elif 'DOI' in id_text or id_text.startswith('10.'):
                        publication['doi'] = identifier.text
            
            return publication if publication['title'] else None
            
        except Exception as e:
            logger.warning(f"Failed to parse DNB record: {e}")
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
        all_publications = []
        start_record = 1
        page_size = 100  # Maximum allowed by DNB
        
        logger.info(f"Starting DNB search for author: {author_name}")
        
        try:
            # First request to get total count
            first_response = self.search_by_author(author_name, start_record, page_size)
            total_records = first_response['total_records']
            
            if total_records == 0:
                logger.info("No publications found")
                return []
            
            # Determine how many records we actually need
            target_records = min(total_records, max_results) if max_results else total_records
            logger.info(f"Found {total_records} total records, retrieving {target_records}")
            
            # Add records from first response
            all_publications.extend(first_response['records'])
            
            # Calculate remaining pages needed
            records_retrieved = len(first_response['records'])
            
            while records_retrieved < target_records and records_retrieved < total_records:
                start_record += page_size
                records_needed = target_records - records_retrieved
                current_page_size = min(page_size, records_needed)
                
                logger.debug(f"Fetching page starting at record {start_record}")
                
                # Add delay to be respectful to the API
                time.sleep(0.5)
                
                try:
                    response = self.search_by_author(author_name, start_record, current_page_size)
                    new_records = response['records']
                    
                    if not new_records:
                        logger.info("No more records available")
                        break
                    
                    all_publications.extend(new_records)
                    records_retrieved += len(new_records)
                    
                    logger.debug(f"Retrieved {len(new_records)} records, total: {records_retrieved}")
                    
                except Exception as e:
                    logger.error(f"Error fetching page starting at {start_record}: {e}")
                    break
            
            logger.info(f"DNB search completed: {len(all_publications)} publications retrieved")
            return all_publications[:target_records] if max_results else all_publications
            
        except Exception as e:
            logger.error(f"DNB search failed: {e}")
            raise

    def test_connection(self) -> bool:
        """Test if the DNB API is accessible."""
        try:
            response = self.session.get(self.base_url, timeout=10)
            return response.status_code == 200
        except:
            return False
