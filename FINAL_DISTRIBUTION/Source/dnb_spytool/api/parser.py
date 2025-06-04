"""
MARCXML Parser for processing DNB SRU API responses.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from datetime import datetime
import re


class MARCXMLParser:
    """Parser for MARCXML format responses from DNB SRU API."""
    
    def __init__(self):
        """Initialize the parser with namespace mappings."""
        self.namespaces = {
            'srw': 'http://www.loc.gov/zing/srw/',
            'marc': 'http://www.loc.gov/MARC21/slim',
            'diag': 'http://www.loc.gov/zing/srw/diagnostic/'
        }
    
    def parse_response(self, xml_content: bytes) -> Optional[Dict]:
        """
        Parse SRU response XML content.
        
        Args:
            xml_content: Raw XML response content
            
        Returns:
            Parsed response data with publications and metadata
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Check for errors/diagnostics
            diagnostics = root.findall('.//diag:diagnostic', self.namespaces)
            if diagnostics:
                error_msg = self._extract_diagnostic_message(diagnostics[0])
                print(f"API Error: {error_msg}")
                return None
            
            # Extract metadata
            total_records = self._get_total_records(root)
            
            # Extract publications
            publications = self._extract_publications(root)
            
            return {
                'publications': publications,
                'total_records': total_records,
                'records_returned': len(publications)
            }
            
        except ET.ParseError as e:
            print(f"XML parsing error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error parsing response: {e}")
            return None

    def parse_publications(self, xml_content: bytes) -> List[Dict]:
        """
        Parse publications from XML content (expected by tests).
        
        Args:
            xml_content: Raw XML response content
            
        Returns:
            List of publication dictionaries
        """
        # First check if xml_content is valid XML by parsing it directly
        try:
            ET.fromstring(xml_content)
        except ET.ParseError:
            # Re-raise ParseError for tests to catch
            raise
        
        try:
            result = self.parse_response(xml_content)
            if result and 'publications' in result:
                return result['publications']
            return []
        except Exception as e:
            print(f"Error parsing publications: {e}")
            return []
    
    def _get_total_records(self, root: ET.Element) -> int:
        """Extract total number of records from response."""
        total_elem = root.find('.//srw:numberOfRecords', self.namespaces)
        if total_elem is not None and total_elem.text:
            return int(total_elem.text)
        return 0
    
    def _extract_diagnostic_message(self, diagnostic: ET.Element) -> str:
        """Extract error message from diagnostic element."""
        message_elem = diagnostic.find('.//diag:message', self.namespaces)
        if message_elem is not None and message_elem.text:
            return message_elem.text
        return "Unknown API error"
    
    def _extract_publications(self, root: ET.Element) -> List[Dict]:
        """Extract publication records from MARCXML."""
        publications = []
        
        records = root.findall('.//marc:record', self.namespaces)
        
        for record in records:
            publication = self._parse_marc_record(record)
            if publication:
                publications.append(publication)
        
        return publications
    
    def _parse_marc_record(self, record: ET.Element) -> Optional[Dict]:
        """
        Parse a single MARC record into a publication dictionary.
        
        Args:
            record: MARC record XML element
            
        Returns:
            Publication data dictionary
        """
        try:
            publication = {
                'id': self._get_record_id(record),
                'title': self._extract_title(record),
                'authors': self._extract_authors(record),
                'publication_year': self._extract_publication_year(record),
                'publisher': self._extract_publisher(record),
                'isbn': self._extract_isbn(record),
                'issn': self._extract_issn(record),
                'doi': self._extract_doi(record),
                'subjects': self._extract_subjects(record),
                'subject_headings': self._extract_subjects(record),  # Consistent field name
                'language': self._extract_language(record),
                'description': self._extract_description(record),
                'abstract': self._extract_abstract(record),
                'notes': self._extract_notes(record),
                'publication_type': self._extract_publication_type(record),
                'physical_description': self._extract_physical_description(record),
                'series': self._extract_series(record),
                'url': self._extract_primary_url(record),
                'all_urls': self._extract_all_urls(record),
                'raw_data': self._extract_raw_marc_data(record)
            }
            
            return publication
            
        except Exception as e:
            print(f"Error parsing MARC record: {e}")
            return None

    def _get_record_id(self, record: ET.Element) -> str:
        """Extract record ID from control field 001."""
        control_001 = record.find('.//marc:controlfield[@tag="001"]', self.namespaces)
        if control_001 is not None and control_001.text:
            return control_001.text.strip()
        return ""

    def _extract_title(self, record: ET.Element) -> str:
        """
        Extract title from MARC record (expected by tests).
        
        Args:
            record: MARC record XML element
            
        Returns:
            Title string
        """
        field_245 = record.find('.//marc:datafield[@tag="245"]', self.namespaces)
        if field_245 is not None:
            title_parts = []
            for subfield in field_245.findall('.//marc:subfield', self.namespaces):
                if subfield.get('code') in ['a', 'b'] and subfield.text:
                    # Clean up whitespace and remove trailing colons
                    clean_text = subfield.text.strip().rstrip(':').strip()
                    if clean_text:
                        title_parts.append(clean_text)
            if title_parts:
                return ' : '.join(title_parts)
        return "Unknown Title"
    
    def _extract_authors(self, record: ET.Element) -> List[str]:
        """
        Extract authors from MARC record (expected by tests).
        
        Args:
            record: MARC record XML element
            
        Returns:
            List of author names
        """
        authors = []
        
        # Main author (100)
        field_100 = record.find('.//marc:datafield[@tag="100"]', self.namespaces)
        if field_100 is not None:
            author = self._extract_clean_author_name(field_100)
            if author:
                authors.append(author)
        
        # Additional authors (700)
        for field_700 in record.findall('.//marc:datafield[@tag="700"]', self.namespaces):
            author = self._extract_clean_author_name(field_700)
            if author:
                authors.append(author)
        
        # Return default if no authors found
        if not authors:
            return ["Unknown Author"]
        
        return authors
    
    def _extract_clean_author_name(self, author_field: ET.Element) -> str:
        """Extract clean author name without dates."""
        name_parts = []
        for subfield in author_field.findall('.//marc:subfield', self.namespaces):
            code = subfield.get('code')
            if code == 'a' and subfield.text:  # Only use 'a' subfield for name
                name_parts.append(subfield.text.strip())
        return ' '.join(name_parts)
    
    def _extract_isbn(self, record: ET.Element) -> str:
        """
        Extract ISBN from MARC record (expected by tests).
        
        Args:
            record: MARC record XML element
            
        Returns:
            ISBN string
        """
        field_020 = record.find('.//marc:datafield[@tag="020"]', self.namespaces)
        if field_020 is not None:
            isbn_subfield = field_020.find('.//marc:subfield[@code="a"]', self.namespaces)
            if isbn_subfield is not None and isbn_subfield.text:
                # Clean the ISBN (remove qualifiers in parentheses)
                isbn = isbn_subfield.text.strip()
                if '(' in isbn:
                    isbn = isbn.split('(')[0].strip()
                return isbn
        return ""
    
    def _extract_publication_year(self, record: ET.Element) -> Optional[int]:
        """
        Extract publication year from MARC record (expected by tests).
        
        Args:
            record: MARC record XML element
            
        Returns:
            Publication year as integer or None
        """
        # Try field 008 (fixed-length data elements)
        field_008 = record.find('.//marc:controlfield[@tag="008"]', self.namespaces)
        if field_008 is not None and field_008.text:
            field_008_text = field_008.text
            if len(field_008_text) >= 11:
                year_str = field_008_text[7:11]
                if year_str.isdigit():
                    return int(year_str)
        
        # Try field 260/264 (publication info)
        for tag in ['260', '264']:
            field = record.find(f'.//marc:datafield[@tag="{tag}"]', self.namespaces)
            if field is not None:
                for subfield in field.findall('.//marc:subfield[@code="c"]', self.namespaces):
                    if subfield.text:
                        # Extract year from publication date string
                        year_match = re.search(r'\b(\d{4})\b', subfield.text)
                        if year_match:
                            return int(year_match.group(1))
        
        return None
    
    def _extract_language(self, record: ET.Element) -> str:
        """
        Extract language from MARC record (expected by tests).
        
        Args:
            record: MARC record XML element
            
        Returns:
            Language code string
        """
        # Try field 041 first (language code)
        field_041 = record.find('.//marc:datafield[@tag="041"]', self.namespaces)
        if field_041 is not None:
            subfield_a = field_041.find('.//marc:subfield[@code="a"]', self.namespaces)
            if subfield_a is not None and subfield_a.text:
                return subfield_a.text.strip()
        
        # Try field 008 (fixed-length data elements)
        field_008 = record.find('.//marc:controlfield[@tag="008"]', self.namespaces)
        if field_008 is not None and field_008.text:
            field_008_text = field_008.text
            if len(field_008_text) >= 38:
                lang_code = field_008_text[35:38].strip()
                if lang_code and lang_code != '|||':
                    return lang_code
        
        return "unknown"
    
    def _extract_publisher(self, record: ET.Element) -> str:
        """
        Extract publisher from MARC record (expected by tests).
        
        Args:
            record: MARC record XML element
            
        Returns:
            Publisher string
        """
        # Try field 260 (publication, distribution, etc.)
        field_260 = record.find('.//marc:datafield[@tag="260"]', self.namespaces)
        if field_260 is not None:
            subfield_b = field_260.find('.//marc:subfield[@code="b"]', self.namespaces)
            if subfield_b is not None and subfield_b.text:
                publisher = subfield_b.text.strip()
                # Remove trailing comma or colon
                publisher = publisher.rstrip(',: ')
                return publisher
        
        # Try field 264 (production, publication, distribution, manufacture, and copyright notice)
        field_264 = record.find('.//marc:datafield[@tag="264"]', self.namespaces)
        if field_264 is not None:
            subfield_b = field_264.find('.//marc:subfield[@code="b"]', self.namespaces)
            if subfield_b is not None and subfield_b.text:
                publisher = subfield_b.text.strip()
                # Remove trailing comma or colon
                publisher = publisher.rstrip(',: ')
                return publisher
        
        return ""
    
    def _extract_subjects(self, record: ET.Element) -> List[str]:
        """
        Extract subjects from MARC record (expected by tests).
        
        Args:
            record: MARC record XML element
            
        Returns:
            List of subject strings
        """
        subjects = []
        
        # Field 650 - Subject added entry--topical term
        for field_650 in record.findall('.//marc:datafield[@tag="650"]', self.namespaces):
            subfield_a = field_650.find('.//marc:subfield[@code="a"]', self.namespaces)
            if subfield_a is not None and subfield_a.text:
                subjects.append(subfield_a.text.strip())
        
        # Field 655 - Index term--genre/form
        for field_655 in record.findall('.//marc:datafield[@tag="655"]', self.namespaces):
            subfield_a = field_655.find('.//marc:subfield[@code="a"]', self.namespaces)
            if subfield_a is not None and subfield_a.text:
                subjects.append(subfield_a.text.strip())
        
        return subjects
    
    def _extract_issn(self, record: ET.Element) -> str:
        """Extract ISSN from MARC record (field 022)."""
        field_022 = record.find('.//marc:datafield[@tag="022"]', self.namespaces)
        if field_022 is not None:
            issn_subfield = field_022.find('.//marc:subfield[@code="a"]', self.namespaces)
            if issn_subfield is not None and issn_subfield.text:
                return issn_subfield.text.strip()
        return ""
    
    def _extract_doi(self, record: ET.Element) -> str:
        """Extract DOI from MARC record (field 024 with $2=doi)."""
        for field_024 in record.findall('.//marc:datafield[@tag="024"]', self.namespaces):
            # Check if this is a DOI field
            subfield_2 = field_024.find('.//marc:subfield[@code="2"]', self.namespaces)
            if subfield_2 is not None and subfield_2.text and 'doi' in subfield_2.text.lower():
                doi_subfield = field_024.find('.//marc:subfield[@code="a"]', self.namespaces)
                if doi_subfield is not None and doi_subfield.text:
                    doi = doi_subfield.text.strip()
                    # Clean DOI - remove URL prefix if present
                    if doi.startswith('http'):
                        doi = doi.split('doi.org/')[-1]
                    return doi
        return ""
    
    def _extract_description(self, record: ET.Element) -> str:
        """Extract description/summary from MARC record (field 520)."""
        descriptions = []
        for field_520 in record.findall('.//marc:datafield[@tag="520"]', self.namespaces):
            subfield_a = field_520.find('.//marc:subfield[@code="a"]', self.namespaces)
            if subfield_a is not None and subfield_a.text:
                descriptions.append(subfield_a.text.strip())
        return ' '.join(descriptions) if descriptions else ""
    
    def _extract_abstract(self, record: ET.Element) -> str:
        """Extract abstract from MARC record (same as description for DNB)."""
        return self._extract_description(record)
    
    def _extract_notes(self, record: ET.Element) -> str:
        """Extract notes from MARC record (fields 500, 502, etc.)."""
        notes = []
        
        # General notes (500)
        for field_500 in record.findall('.//marc:datafield[@tag="500"]', self.namespaces):
            subfield_a = field_500.find('.//marc:subfield[@code="a"]', self.namespaces)
            if subfield_a is not None and subfield_a.text:
                notes.append(subfield_a.text.strip())
        
        # Dissertation notes (502)
        for field_502 in record.findall('.//marc:datafield[@tag="502"]', self.namespaces):
            subfield_a = field_502.find('.//marc:subfield[@code="a"]', self.namespaces)
            if subfield_a is not None and subfield_a.text:
                notes.append(f"Dissertation: {subfield_a.text.strip()}")
        
        # Bibliography notes (504)
        for field_504 in record.findall('.//marc:datafield[@tag="504"]', self.namespaces):
            subfield_a = field_504.find('.//marc:subfield[@code="a"]', self.namespaces)
            if subfield_a is not None and subfield_a.text:
                notes.append(f"Bibliography: {subfield_a.text.strip()}")
        
        return ' | '.join(notes) if notes else ""
    
    def _extract_publication_type(self, record: ET.Element) -> str:
        """Extract publication type from leader and control fields."""
        leader = record.find('.//marc:leader', self.namespaces)
        if leader is not None and leader.text and len(leader.text) >= 7:
            type_code = leader.text[6]
            
            type_mapping = {
                'a': 'Text',
                'm': 'Monograph',
                's': 'Serial',
                'c': 'Musical score',
                'd': 'Manuscript music',
                'e': 'Cartographic material',
                'f': 'Manuscript cartographic material',
                'g': 'Projected medium',
                'i': 'Nonmusical sound recording',
                'j': 'Musical sound recording',
                'k': 'Two-dimensional nonprojectable graphic',
                'o': 'Kit',
                'p': 'Mixed materials',
                'r': 'Three-dimensional artifact',
                't': 'Manuscript language material'
            }
            
            return type_mapping.get(type_code, 'Unknown')
        
        return ""
    
    def _extract_physical_description(self, record: ET.Element) -> str:
        """Extract physical description from MARC record (field 300)."""
        descriptions = []
        for field_300 in record.findall('.//marc:datafield[@tag="300"]', self.namespaces):
            parts = []
            for subfield in field_300.findall('.//marc:subfield', self.namespaces):
                code = subfield.get('code')
                if code in ['a', 'b', 'c'] and subfield.text:  # extent, other details, dimensions
                    parts.append(subfield.text.strip())
            if parts:
                descriptions.append(' : '.join(parts))
        
        return ' ; '.join(descriptions) if descriptions else ""
    
    def _extract_series(self, record: ET.Element) -> str:
        """Extract series information from MARC record (fields 440, 490, 830)."""
        series_info = []
        
        # Series statement (490)
        for field_490 in record.findall('.//marc:datafield[@tag="490"]', self.namespaces):
            subfield_a = field_490.find('.//marc:subfield[@code="a"]', self.namespaces)
            if subfield_a is not None and subfield_a.text:
                series_title = subfield_a.text.strip()
                subfield_v = field_490.find('.//marc:subfield[@code="v"]', self.namespaces)
                if subfield_v is not None and subfield_v.text:
                    series_title += f" ; {subfield_v.text.strip()}"
                series_info.append(series_title)
        
        # Series added entry (830)
        for field_830 in record.findall('.//marc:datafield[@tag="830"]', self.namespaces):
            subfield_a = field_830.find('.//marc:subfield[@code="a"]', self.namespaces)
            if subfield_a is not None and subfield_a.text:
                series_title = subfield_a.text.strip()
                subfield_v = field_830.find('.//marc:subfield[@code="v"]', self.namespaces)
                if subfield_v is not None and subfield_v.text:
                    series_title += f" ; {subfield_v.text.strip()}"
                series_info.append(series_title)
        
        return ' | '.join(series_info) if series_info else ""
    
    def _extract_primary_url(self, record: ET.Element) -> str:
        """Extract primary URL from MARC record (field 856)."""
        for field_856 in record.findall('.//marc:datafield[@tag="856"]', self.namespaces):
            # Prefer direct links (indicator 4 = HTTP)
            ind1 = field_856.get('ind1', '')
            ind2 = field_856.get('ind2', '')
            
            subfield_u = field_856.find('.//marc:subfield[@code="u"]', self.namespaces)
            if subfield_u is not None and subfield_u.text:
                url = subfield_u.text.strip()
                if url.startswith(('http://', 'https://')):
                    return url
        
        return ""
    
    def _extract_all_urls(self, record: ET.Element) -> dict:
        """Extract all URLs from MARC record with categorization."""
        urls = {}
        
        for field_856 in record.findall('.//marc:datafield[@tag="856"]', self.namespaces):
            subfield_u = field_856.find('.//marc:subfield[@code="u"]', self.namespaces)
            subfield_3 = field_856.find('.//marc:subfield[@code="3"]', self.namespaces)
            subfield_z = field_856.find('.//marc:subfield[@code="z"]', self.namespaces)
            
            if subfield_u is not None and subfield_u.text:
                url = subfield_u.text.strip()
                if url.startswith(('http://', 'https://')):
                    # Categorize URL based on domain or description
                    url_type = self._categorize_url(url, subfield_3, subfield_z)
                    urls[url_type] = url
        
        return urls
    
    def _categorize_url(self, url: str, subfield_3: ET.Element = None, subfield_z: ET.Element = None) -> str:
        """Categorize URL based on domain and description."""
        url_lower = url.lower()
        
        # Check description first
        if subfield_3 is not None and subfield_3.text:
            desc = subfield_3.text.lower()
            if 'inhaltsverzeichnis' in desc or 'table of contents' in desc:
                return 'table_of_contents'
            elif 'volltext' in desc or 'full text' in desc:
                return 'full_text'
        
        # Check by domain
        if 'doi.org' in url_lower:
            return 'doi'
        elif 'dnb.de' in url_lower:
            if 'opac' in url_lower:
                return 'dnb_record'
            else:
                return 'dnb_direct'
        elif 'worldcat.org' in url_lower:
            return 'worldcat'
        elif 'google.com/books' in url_lower or 'books.google' in url_lower:
            return 'google_books'
        elif 'springer' in url_lower:
            return 'springer'
        elif 'sciencedirect' in url_lower:
            return 'sciencedirect'
        elif 'issn.org' in url_lower:
            return 'issn_portal'
        else:
            return 'other'
    
    def _extract_raw_marc_data(self, record: ET.Element) -> dict:
        """Extract all MARC fields for advanced users."""
        raw_data = {}
        
        # Control fields
        for field in record.findall('.//marc:controlfield', self.namespaces):
            tag = field.get('tag')
            if tag and field.text:
                raw_data[f'control_{tag}'] = field.text.strip()
        
        # Data fields
        for field in record.findall('.//marc:datafield', self.namespaces):
            tag = field.get('tag')
            if tag:
                if tag not in raw_data:
                    raw_data[tag] = []
                
                field_data = {
                    'ind1': field.get('ind1', ''),
                    'ind2': field.get('ind2', ''),
                    'subfields': {}
                }
                
                for subfield in field.findall('.//marc:subfield', self.namespaces):
                    code = subfield.get('code')
                    if code and subfield.text:
                        if code not in field_data['subfields']:
                            field_data['subfields'][code] = []
                        field_data['subfields'][code].append(subfield.text.strip())
                
                if field_data['subfields']:
                    raw_data[tag].append(field_data)
        
        return raw_data
