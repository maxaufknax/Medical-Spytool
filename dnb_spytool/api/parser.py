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
                'total_records': total_records,            'records_returned': len(publications)
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
                'subjects': self._extract_subjects(record),
                'language': self._extract_language(record),
                'url': self._extract_urls(record)
            }
            
            return publication
            
        except Exception as e:
            print(f"Error parsing MARC record: {e}")
            return None

    def _extract_urls(self, record: ET.Element) -> List[str]:
        """Extract various URLs from MARC record."""
        urls = []

        # DNB Portal URL from control field 001
        dnb_id_elem = record.find('.//marc:controlfield[@tag="001"]', self.namespaces)
        if dnb_id_elem is not None and dnb_id_elem.text:
            dnb_id = dnb_id_elem.text.strip()
            if dnb_id:
                urls.append(f"https://portal.dnb.de/opac/showRecord?cqlQuery=nid%3D{dnb_id}")

        # URLs and URNs from datafield 856
        for field_856 in record.findall('.//marc:datafield[@tag="856"]', self.namespaces):
            url_subfield_u = field_856.find('.//marc:subfield[@code="u"]', self.namespaces)
            if url_subfield_u is not None and url_subfield_u.text:
                urls.append(url_subfield_u.text.strip())

            # Check for URNs in subfield 'a' if subfield 'q' indicates URN
            # This is a basic check; DNB's URN representation might be more complex.
            subfield_q = field_856.find('.//marc:subfield[@code="q"]', self.namespaces)
            if subfield_q is not None and subfield_q.text and "urn" in subfield_q.text.lower():
                subfield_a = field_856.find('.//marc:subfield[@code="a"]', self.namespaces)
                if subfield_a is not None and subfield_a.text:
                    urn_value = subfield_a.text.strip()
                    if urn_value.startswith("urn:nbn:"):
                        urls.append(f"https://nbn-resolving.org/{urn_value}")

        # DOI URLs from datafield 024
        for field_024 in record.findall('.//marc:datafield[@tag="024"]', self.namespaces):
            subfield_2 = field_024.find('.//marc:subfield[@code="2"]', self.namespaces)
            if subfield_2 is not None and subfield_2.text and subfield_2.text.strip().lower() == "doi":
                subfield_a = field_024.find('.//marc:subfield[@code="a"]', self.namespaces)
                if subfield_a is not None and subfield_a.text:
                    doi_value = subfield_a.text.strip()
                    if doi_value: # Ensure DOI value is not empty
                        urls.append(f"https://doi.org/{doi_value}")

        # Return unique, stripped URLs
        return list(set([url.strip() for url in urls if url]))

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
