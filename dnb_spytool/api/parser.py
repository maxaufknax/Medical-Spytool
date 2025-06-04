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
                'issn': self._extract_issn(record),
                'doi': self._extract_doi(record),
                'url': self._extract_url(record),
                'subjects': self._extract_subjects(record),
                'language': self._extract_language(record),
                'description': self._extract_description(record),
                'publication_type': self._extract_publication_type(record),
                'physical_description': self._extract_physical_description(record),
                'series': self._extract_series(record),
                'notes': self._extract_notes(record)
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
        # Try field 245 first (title statement)
        field_245 = record.find('.//marc:datafield[@tag="245"]', self.namespaces)
        if field_245 is not None:
            title_parts = []
            for subfield in field_245.findall('.//marc:subfield', self.namespaces):
                if subfield.get('code') in ['a', 'b'] and subfield.text:
                    # Clean up whitespace and remove trailing colons/slashes
                    clean_text = subfield.text.strip().rstrip(':/ ').strip()
                    if clean_text:
                        title_parts.append(clean_text)
            if title_parts:
                return ' : '.join(title_parts)
        
        # Try field 130 (uniform title)
        field_130 = record.find('.//marc:datafield[@tag="130"]', self.namespaces)
        if field_130 is not None:
            subfield_a = field_130.find('.//marc:subfield[@code="a"]', self.namespaces)
            if subfield_a is not None and subfield_a.text:
                return subfield_a.text.strip().rstrip(':/ ').strip()
        
        # Try field 240 (uniform title)
        field_240 = record.find('.//marc:datafield[@tag="240"]', self.namespaces)
        if field_240 is not None:
            subfield_a = field_240.find('.//marc:subfield[@code="a"]', self.namespaces)
            if subfield_a is not None and subfield_a.text:
                return subfield_a.text.strip().rstrip(':/ ').strip()
        
        return ""
    
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
        
        # Corporate author (110)
        field_110 = record.find('.//marc:datafield[@tag="110"]', self.namespaces)
        if field_110 is not None:
            author = self._extract_clean_author_name(field_110)
            if author:
                authors.append(author)
        
        # Additional authors (700)
        for field_700 in record.findall('.//marc:datafield[@tag="700"]', self.namespaces):
            author = self._extract_clean_author_name(field_700)
            if author and author not in authors:  # Avoid duplicates
                authors.append(author)
        
        # Additional corporate authors (710)
        for field_710 in record.findall('.//marc:datafield[@tag="710"]', self.namespaces):
            author = self._extract_clean_author_name(field_710)
            if author and author not in authors:  # Avoid duplicates
                authors.append(author)
        
        return authors
    
    def _extract_clean_author_name(self, author_field: ET.Element) -> str:
        """Extract clean author name without dates."""
        name_parts = []
        for subfield in author_field.findall('.//marc:subfield', self.namespaces):
            code = subfield.get('code')
            if code in ['a', 'b'] and subfield.text:  # Include both 'a' and 'b' subfields
                text = subfield.text.strip()
                # Remove dates in parentheses and other qualifiers
                text = re.sub(r'\([^)]*\)', '', text).strip()
                text = text.rstrip('.,;: ').strip()
                if text:
                    name_parts.append(text)
        return ' '.join(name_parts)
    
    def _extract_isbn(self, record: ET.Element) -> str:
        """
        Extract ISBN from MARC record (expected by tests).
        
        Args:
            record: MARC record XML element
            
        Returns:
            ISBN string (first valid ISBN found)
        """
        # Collect all ISBNs from all 020 fields
        isbns = []
        for field_020 in record.findall('.//marc:datafield[@tag="020"]', self.namespaces):
            isbn_subfield = field_020.find('.//marc:subfield[@code="a"]', self.namespaces)
            if isbn_subfield is not None and isbn_subfield.text:
                # Clean the ISBN (remove qualifiers in parentheses)
                isbn = isbn_subfield.text.strip()
                if '(' in isbn:
                    isbn = isbn.split('(')[0].strip()
                # Remove hyphens and spaces for validation
                clean_isbn = isbn.replace('-', '').replace(' ', '')
                if clean_isbn and (len(clean_isbn) == 10 or len(clean_isbn) == 13):
                    isbns.append(isbn)
        
        # Return the first valid ISBN
        return isbns[0] if isbns else ""
    
    def _extract_issn(self, record: ET.Element) -> str:
        """
        Extract ISSN from MARC record.
        
        Args:
            record: MARC record XML element
            
        Returns:
            ISSN string (first valid ISSN found)
        """
        # Collect all ISSNs from all 022 fields
        issns = []
        for field_022 in record.findall('.//marc:datafield[@tag="022"]', self.namespaces):
            issn_subfield = field_022.find('.//marc:subfield[@code="a"]', self.namespaces)
            if issn_subfield is not None and issn_subfield.text:
                issn = issn_subfield.text.strip()
                # Basic ISSN validation (should be 8 digits with hyphen)
                clean_issn = issn.replace('-', '')
                if clean_issn.isdigit() and len(clean_issn) == 8:
                    issns.append(issn)
        
        # Return the first valid ISSN
        return issns[0] if issns else ""
    
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
                lang_code = subfield_a.text.strip()
                if lang_code and len(lang_code) >= 2:
                    return lang_code
        
        # Try field 008 (fixed-length data elements)
        field_008 = record.find('.//marc:controlfield[@tag="008"]', self.namespaces)
        if field_008 is not None and field_008.text:
            field_008_text = field_008.text
            if len(field_008_text) >= 38:
                lang_code = field_008_text[35:38].strip()
                if lang_code and lang_code != '|||' and lang_code.isalpha():
                    return lang_code
        
        # Try field 546 (language note)
        field_546 = record.find('.//marc:datafield[@tag="546"]', self.namespaces)
        if field_546 is not None:
            subfield_a = field_546.find('.//marc:subfield[@code="a"]', self.namespaces)
            if subfield_a is not None and subfield_a.text:
                # Extract language name from text
                text = subfield_a.text.lower()
                common_languages = {
                    'english': 'eng', 'german': 'ger', 'french': 'fre', 
                    'spanish': 'spa', 'italian': 'ita', 'portuguese': 'por'
                }
                for lang_name, lang_code in common_languages.items():
                    if lang_name in text:
                        return lang_code
        
        return ""
    
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
    
    def _extract_description(self, record: ET.Element) -> str:
        """
        Extract description/summary from MARC record.
        
        Args:
            record: MARC record XML element
            
        Returns:
            Description string
        """
        # Field 520 - Summary, abstract, annotation, scope, etc.
        field_520 = record.find('.//marc:datafield[@tag="520"]', self.namespaces)
        if field_520 is not None:
            subfield_a = field_520.find('.//marc:subfield[@code="a"]', self.namespaces)
            if subfield_a is not None and subfield_a.text:
                return subfield_a.text.strip()
        
        # Field 505 - Contents note
        field_505 = record.find('.//marc:datafield[@tag="505"]', self.namespaces)
        if field_505 is not None:
            subfield_a = field_505.find('.//marc:subfield[@code="a"]', self.namespaces)
            if subfield_a is not None and subfield_a.text:
                return subfield_a.text.strip()
        
        return ""
    
    def _extract_publication_type(self, record: ET.Element) -> str:
        """
        Extract publication type from MARC record.
        
        Args:
            record: MARC record XML element
            
        Returns:
            Publication type string
        """
        # Field 655 - Index term--genre/form
        field_655 = record.find('.//marc:datafield[@tag="655"]', self.namespaces)
        if field_655 is not None:
            subfield_a = field_655.find('.//marc:subfield[@code="a"]', self.namespaces)
            if subfield_a is not None and subfield_a.text:
                return subfield_a.text.strip()
        
        # Leader position for type of record
        leader = record.find('.//marc:leader', self.namespaces)
        if leader is not None and leader.text and len(leader.text) > 6:
            type_of_record = leader.text[6]
            type_mapping = {
                'a': 'Language material',
                'b': 'Archival and manuscripts',
                'c': 'Notated music',
                'd': 'Manuscript notated music',
                'e': 'Cartographic material',
                'f': 'Manuscript cartographic material',
                'g': 'Projected medium',
                'i': 'Nonmusical sound recording',
                'j': 'Musical sound recording',
                'k': 'Two-dimensional nonprojectable graphic',
                'm': 'Computer file',
                'o': 'Kit',
                'p': 'Mixed materials',
                'r': 'Three-dimensional artifact or naturally occurring object',
                't': 'Manuscript language material'
            }
            return type_mapping.get(type_of_record, 'Unknown')
        
        return ""
    
    def _extract_doi(self, record: ET.Element) -> str:
        """
        Extract DOI from MARC record.
        
        Args:
            record: MARC record XML element
            
        Returns:
            DOI string
        """
        # Field 024 with indicator 7 for DOI
        for field_024 in record.findall('.//marc:datafield[@tag="024"]', self.namespaces):
            if field_024.get('ind1') == '7':
                subfield_2 = field_024.find('.//marc:subfield[@code="2"]', self.namespaces)
                if subfield_2 is not None and subfield_2.text and 'doi' in subfield_2.text.lower():
                    subfield_a = field_024.find('.//marc:subfield[@code="a"]', self.namespaces)
                    if subfield_a is not None and subfield_a.text:
                        doi = subfield_a.text.strip()
                        # Remove "doi:" prefix if present
                        if doi.lower().startswith('doi:'):
                            doi = doi[4:].strip()
                        return doi
        
        # Field 856 with DOI in URL
        for field_856 in record.findall('.//marc:datafield[@tag="856"]', self.namespaces):
            subfield_u = field_856.find('.//marc:subfield[@code="u"]', self.namespaces)
            if subfield_u is not None and subfield_u.text:
                url = subfield_u.text.strip()
                if 'doi.org/' in url:
                    # Extract DOI from URL
                    doi_match = re.search(r'doi\.org/(.+)', url)
                    if doi_match:
                        return doi_match.group(1)
        
        return ""
    
    def _extract_url(self, record: ET.Element) -> str:
        """
        Extract direct URL from MARC record.
        
        Args:
            record: MARC record XML element
            
        Returns:
            URL string
        """
        # Field 856 - Electronic location and access
        field_856 = record.find('.//marc:datafield[@tag="856"]', self.namespaces)
        if field_856 is not None:
            subfield_u = field_856.find('.//marc:subfield[@code="u"]', self.namespaces)
            if subfield_u is not None and subfield_u.text:
                return subfield_u.text.strip()
        
        return ""
    
    def _extract_physical_description(self, record: ET.Element) -> str:
        """
        Extract physical description from MARC record.
        
        Args:
            record: MARC record XML element
            
        Returns:
            Physical description string
        """
        # Field 300 - Physical description
        field_300 = record.find('.//marc:datafield[@tag="300"]', self.namespaces)
        if field_300 is not None:
            desc_parts = []
            for subfield in field_300.findall('.//marc:subfield', self.namespaces):
                if subfield.get('code') in ['a', 'b', 'c'] and subfield.text:
                    desc_parts.append(subfield.text.strip())
            if desc_parts:
                return ' ; '.join(desc_parts)
        
        return ""
    
    def _extract_series(self, record: ET.Element) -> str:
        """
        Extract series information from MARC record.
        
        Args:
            record: MARC record XML element
            
        Returns:
            Series string
        """
        # Field 490 - Series statement
        field_490 = record.find('.//marc:datafield[@tag="490"]', self.namespaces)
        if field_490 is not None:
            subfield_a = field_490.find('.//marc:subfield[@code="a"]', self.namespaces)
            if subfield_a is not None and subfield_a.text:
                series = subfield_a.text.strip()
                # Add volume number if available
                subfield_v = field_490.find('.//marc:subfield[@code="v"]', self.namespaces)
                if subfield_v is not None and subfield_v.text:
                    series += f" ; {subfield_v.text.strip()}"
                return series
        
        return ""
    
    def _extract_notes(self, record: ET.Element) -> List[str]:
        """
        Extract notes from MARC record.
        
        Args:
            record: MARC record XML element
            
        Returns:
            List of notes
        """
        notes = []
        
        # Various note fields
        note_fields = ['500', '501', '502', '504', '505', '506', '508', '511', '515', '518', '520', '521', '525', '530']
        
        for field_tag in note_fields:
            for field in record.findall(f'.//marc:datafield[@tag="{field_tag}"]', self.namespaces):
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                if subfield_a is not None and subfield_a.text:
                    notes.append(subfield_a.text.strip())
        
        return notes
