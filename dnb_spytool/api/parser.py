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
            
            # Enhanced extraction for DNB v1.4
            dnb_classification = self._extract_enhanced_dnb_classification(record)
            publication.update(dnb_classification)
            
            document_type = self._extract_enhanced_document_type(record)
            publication.update(document_type)
            
            institution_data = self._extract_enhanced_institution_data(record)
            publication.update(institution_data)
            
            identifiers = self._extract_enhanced_identifiers(record)
            publication.update(identifiers)
            
            series_data = self._extract_enhanced_series_data(record)
            publication.update(series_data)
            
            availability_data = self._extract_enhanced_availability_data(record)
            publication.update(availability_data)
            
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

    # =====================================================================================
    # ENHANCED v1.4 METHODS FOR COMPREHENSIVE DNB DATA EXTRACTION
    # =====================================================================================
    
    def _extract_enhanced_dnb_classification(self, record: ET.Element) -> Dict[str, any]:
        """Extract comprehensive DNB classification and subject data."""
        classification_data = {
            'dnb_classification': [],
            'ddc_numbers': [],
            'subject_headings': [],
            'gnd_terms': [],
            'local_classification': [],
            'keywords': []
        }
        
        try:
            # DDC (Dewey Decimal Classification) - Field 082
            for field in record.findall('.//marc:datafield[@tag="082"]', self.namespaces):
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                if subfield_a is not None and subfield_a.text:
                    classification_data['ddc_numbers'].append(subfield_a.text.strip())
            
            # DNB Sachgruppe - Field 084 with indicator 2="sdnb"
            for field in record.findall('.//marc:datafield[@tag="084"]', self.namespaces):
                ind2 = field.get('ind2', '')
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                subfield_2 = field.find('.//marc:subfield[@code="2"]', self.namespaces)
                
                if subfield_a is not None and subfield_a.text:
                    if subfield_2 is not None and 'sdnb' in subfield_2.text.lower():
                        classification_data['dnb_classification'].append(subfield_a.text.strip())
                    else:
                        classification_data['local_classification'].append(subfield_a.text.strip())
            
            # Subject headings - Field 650 (Subject headings)
            for field in record.findall('.//marc:datafield[@tag="650"]', self.namespaces):
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                if subfield_a is not None and subfield_a.text:
                    classification_data['subject_headings'].append(subfield_a.text.strip())
            
            # GND Terms - Field 689 (Subject access fields - GND)
            for field in record.findall('.//marc:datafield[@tag="689"]', self.namespaces):
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                if subfield_a is not None and subfield_a.text:
                    classification_data['gnd_terms'].append(subfield_a.text.strip())
            
            # Keywords - Field 653 (Index terms)
            for field in record.findall('.//marc:datafield[@tag="653"]', self.namespaces):
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                if subfield_a is not None and subfield_a.text:
                    classification_data['keywords'].append(subfield_a.text.strip())
            
            return classification_data
            
        except Exception as e:
            print(f"Error extracting DNB classification: {e}")
            return classification_data
    
    def _extract_enhanced_document_type(self, record: ET.Element) -> Dict[str, any]:
        """Extract comprehensive document type information."""
        doc_type_data = {
            'document_type': None,
            'thesis_type': None,
            'is_dissertation': False,
            'is_habilitation': False,
            'is_master_thesis': False,
            'is_bachelor_thesis': False,
            'publication_format': None,
            'content_type': []
        }
        
        try:
            # Leader position 06 (Type of record)
            leader = record.find('.//marc:leader', self.namespaces)
            if leader is not None and leader.text and len(leader.text) > 6:
                type_code = leader.text[6]
                doc_type_data['content_type'].append(self._decode_leader_type(type_code))
            
            # Field 502 - Dissertation note
            for field in record.findall('.//marc:datafield[@tag="502"]', self.namespaces):
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                subfield_b = field.find('.//marc:subfield[@code="b"]', self.namespaces)
                
                if subfield_a is not None and subfield_a.text:
                    thesis_note = subfield_a.text.lower()
                    if 'dissertation' in thesis_note or 'diss' in thesis_note:
                        doc_type_data['is_dissertation'] = True
                        doc_type_data['thesis_type'] = 'Dissertation'
                    elif 'habilitation' in thesis_note:
                        doc_type_data['is_habilitation'] = True
                        doc_type_data['thesis_type'] = 'Habilitation'
                    elif 'master' in thesis_note:
                        doc_type_data['is_master_thesis'] = True
                        doc_type_data['thesis_type'] = 'Master Thesis'
                    elif 'bachelor' in thesis_note:
                        doc_type_data['is_bachelor_thesis'] = True
                        doc_type_data['thesis_type'] = 'Bachelor Thesis'
                
                # Academic degree
                if subfield_b is not None and subfield_b.text:
                    doc_type_data['degree_type'] = subfield_b.text.strip()
            
            # Field 655 - Genre/form heading
            for field in record.findall('.//marc:datafield[@tag="655"]', self.namespaces):
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                if subfield_a is not None and subfield_a.text:
                    doc_type_data['document_type'] = subfield_a.text.strip()
            
            # Determine primary document type
            if doc_type_data['is_dissertation']:
                doc_type_data['document_type'] = 'Dissertation'
            elif doc_type_data['is_habilitation']:
                doc_type_data['document_type'] = 'Habilitation'
            elif doc_type_data['is_master_thesis']:
                doc_type_data['document_type'] = 'Master Thesis'
            elif doc_type_data['is_bachelor_thesis']:
                doc_type_data['document_type'] = 'Bachelor Thesis'
            elif not doc_type_data['document_type']:
                doc_type_data['document_type'] = 'Monograph'
            
            return doc_type_data
            
        except Exception as e:
            print(f"Error extracting document type: {e}")
            return doc_type_data
    
    def _decode_leader_type(self, type_code: str) -> str:
        """Decode MARC leader type code."""
        type_mapping = {
            'a': 'Language material',
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
        return type_mapping.get(type_code, f'Unknown ({type_code})')
    
    def _extract_enhanced_institution_data(self, record: ET.Element) -> Dict[str, any]:
        """Extract comprehensive institution and academic data."""
        institution_data = {
            'institution': None,
            'university': None,
            'department': None,
            'faculty': None,
            'supervisor': None,
            'advisor': None,
            'institution_gnd': None,
            'place_of_publication': None,
            'academic_degree': None
        }
        
        try:
            # Field 502 - Dissertation note (institution information)
            for field in record.findall('.//marc:datafield[@tag="502"]', self.namespaces):
                subfield_c = field.find('.//marc:subfield[@code="c"]', self.namespaces)
                if subfield_c is not None and subfield_c.text:
                    institution_data['institution'] = subfield_c.text.strip()
                    if 'universität' in subfield_c.text.lower() or 'university' in subfield_c.text.lower():
                        institution_data['university'] = subfield_c.text.strip()
                
                # Degree type
                subfield_b = field.find('.//marc:subfield[@code="b"]', self.namespaces)
                if subfield_b is not None and subfield_b.text:
                    institution_data['academic_degree'] = subfield_b.text.strip()
                
                # Year
                subfield_d = field.find('.//marc:subfield[@code="d"]', self.namespaces)
                if subfield_d is not None and subfield_d.text:
                    institution_data['thesis_year'] = subfield_d.text.strip()
            
            # Field 700 - Added entry personal name (often supervisor/advisor)
            for field in record.findall('.//marc:datafield[@tag="700"]', self.namespaces):
                ind2 = field.get('ind2', '')
                subfield_4 = field.find('.//marc:subfield[@code="4"]', self.namespaces)
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                
                if subfield_a is not None and subfield_a.text:
                    if subfield_4 is not None and subfield_4.text:
                        role = subfield_4.text.lower()
                        if 'dgs' in role or 'ths' in role:  # Degree supervisor
                            institution_data['supervisor'] = subfield_a.text.strip()
                        elif 'sad' in role:  # Scientific advisor
                            institution_data['advisor'] = subfield_a.text.strip()
            
            # Field 710 - Added entry corporate name (institution)
            for field in record.findall('.//marc:datafield[@tag="710"]', self.namespaces):
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                subfield_b = field.find('.//marc:subfield[@code="b"]', self.namespaces)
                
                if subfield_a is not None and subfield_a.text:
                    if not institution_data['institution']:
                        institution_data['institution'] = subfield_a.text.strip()
                    
                    if subfield_b is not None and subfield_b.text:
                        institution_data['department'] = subfield_b.text.strip()
            
            # Field 264 - Publication, Distribution, etc. (Place of publication)
            for field in record.findall('.//marc:datafield[@tag="264"]', self.namespaces):
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                if subfield_a is not None and subfield_a.text:
                    institution_data['place_of_publication'] = subfield_a.text.strip()
            
            return institution_data
            
        except Exception as e:
            print(f"Error extracting institution data: {e}")
            return institution_data
    
    def _extract_enhanced_identifiers(self, record: ET.Element) -> Dict[str, any]:
        """Extract comprehensive identifier information."""
        identifier_data = {
            'isbn': None,
            'isbn_13': None,
            'isbn_10': None,
            'issn': None,
            'urn': None,
            'doi': None,
            'gnd_id': None,
            'oclc_number': None,
            'dnb_id': None,
            'other_ids': []
        }
        
        try:
            # Field 020 - ISBN
            for field in record.findall('.//marc:datafield[@tag="020"]', self.namespaces):
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                if subfield_a is not None and subfield_a.text:
                    isbn = subfield_a.text.strip()
                    identifier_data['isbn'] = isbn
                    
                    # Determine ISBN type
                    if len(isbn.replace('-', '').replace(' ', '')) == 13:
                        identifier_data['isbn_13'] = isbn
                    elif len(isbn.replace('-', '').replace(' ', '')) == 10:
                        identifier_data['isbn_10'] = isbn
            
            # Field 022 - ISSN
            for field in record.findall('.//marc:datafield[@tag="022"]', self.namespaces):
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                if subfield_a is not None and subfield_a.text:
                    identifier_data['issn'] = subfield_a.text.strip()
            
            # Field 024 - Other standard identifier
            for field in record.findall('.//marc:datafield[@tag="024"]', self.namespaces):
                ind1 = field.get('ind1', '')
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                subfield_2 = field.find('.//marc:subfield[@code="2"]', self.namespaces)
                
                if subfield_a is not None and subfield_a.text:
                    if ind1 == '7' and subfield_2 is not None:  # Source specified in subfield 2
                        source = subfield_2.text.lower()
                        if 'urn' in source:
                            identifier_data['urn'] = subfield_a.text.strip()
                        elif 'doi' in source:
                            identifier_data['doi'] = subfield_a.text.strip()
                        elif 'gnd' in source:
                            identifier_data['gnd_id'] = subfield_a.text.strip()
                        else:
                            identifier_data['other_ids'].append(f"{source}: {subfield_a.text.strip()}")
            
            # Field 035 - System control number (OCLC, etc.)
            for field in record.findall('.//marc:datafield[@tag="035"]', self.namespaces):
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                if subfield_a is not None and subfield_a.text:
                    control_num = subfield_a.text.strip()
                    if 'oclc' in control_num.lower():
                        identifier_data['oclc_number'] = control_num
                    elif control_num.startswith('(DE-'):
                        identifier_data['dnb_id'] = control_num
                    else:
                        identifier_data['other_ids'].append(control_num)
            
            return identifier_data
            
        except Exception as e:
            print(f"Error extracting identifiers: {e}")
            return identifier_data
    
    def _extract_enhanced_series_data(self, record: ET.Element) -> Dict[str, any]:
        """Extract comprehensive series and publication information."""
        series_data = {
            'series_title': None,
            'series_volume': None,
            'series_issn': None,
            'collection_title': None,
            'physical_description': None,
            'pagination': None,
            'dimensions': None,
            'material_type': None
        }
        
        try:
            # Field 490 - Series statement
            for field in record.findall('.//marc:datafield[@tag="490"]', self.namespaces):
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                subfield_v = field.find('.//marc:subfield[@code="v"]', self.namespaces)
                subfield_x = field.find('.//marc:subfield[@code="x"]', self.namespaces)
                
                if subfield_a is not None and subfield_a.text:
                    series_data['series_title'] = subfield_a.text.strip()
                
                if subfield_v is not None and subfield_v.text:
                    series_data['series_volume'] = subfield_v.text.strip()
                
                if subfield_x is not None and subfield_x.text:
                    series_data['series_issn'] = subfield_x.text.strip()
            
            # Field 300 - Physical description
            for field in record.findall('.//marc:datafield[@tag="300"]', self.namespaces):
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                subfield_b = field.find('.//marc:subfield[@code="b"]', self.namespaces)
                subfield_c = field.find('.//marc:subfield[@code="c"]', self.namespaces)
                
                if subfield_a is not None and subfield_a.text:
                    series_data['pagination'] = subfield_a.text.strip()
                
                if subfield_b is not None and subfield_b.text:
                    series_data['material_type'] = subfield_b.text.strip()
                
                if subfield_c is not None and subfield_c.text:
                    series_data['dimensions'] = subfield_c.text.strip()
                
                # Combine for physical description
                desc_parts = []
                for sf in [subfield_a, subfield_b, subfield_c]:
                    if sf is not None and sf.text:
                        desc_parts.append(sf.text.strip())
                series_data['physical_description'] = ' ; '.join(desc_parts)
            
            return series_data
            
        except Exception as e:
            print(f"Error extracting series data: {e}")
            return series_data
    
    def _extract_enhanced_availability_data(self, record: ET.Element) -> Dict[str, any]:
        """Extract availability and access information."""
        availability_data = {
            'availability_status': None,
            'access_conditions': None,
            'electronic_access': [],
            'holding_institutions': [],
            'loan_restrictions': None,
            'digital_availability': False
        }
        
        try:
            # Field 506 - Restrictions on access
            for field in record.findall('.//marc:datafield[@tag="506"]', self.namespaces):
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                if subfield_a is not None and subfield_a.text:
                    availability_data['access_conditions'] = subfield_a.text.strip()
            
            # Field 540 - Terms governing use and reproduction
            for field in record.findall('.//marc:datafield[@tag="540"]', self.namespaces):
                subfield_a = field.find('.//marc:subfield[@code="a"]', self.namespaces)
                if subfield_a is not None and subfield_a.text:
                    availability_data['loan_restrictions'] = subfield_a.text.strip()
            
            # Field 856 - Electronic location and access
            for field in record.findall('.//marc:datafield[@tag="856"]', self.namespaces):
                subfield_u = field.find('.//marc:subfield[@code="u"]', self.namespaces)
                subfield_z = field.find('.//marc:subfield[@code="z"]', self.namespaces)
                
                if subfield_u is not None and subfield_u.text:
                    url = subfield_u.text.strip()
                    note = subfield_z.text.strip() if subfield_z is not None and subfield_z.text else ""
                    
                    availability_data['electronic_access'].append({
                        'url': url,
                        'note': note
                    })
                    
                    # Check for digital availability
                    if 'digital' in note.lower() or 'volltext' in note.lower() or 'pdf' in url.lower():
                        availability_data['digital_availability'] = True
            
            # Determine general availability status
            if availability_data['digital_availability']:
                availability_data['availability_status'] = 'Digital Available'
            elif availability_data['access_conditions']:
                availability_data['availability_status'] = 'Restricted Access'
            else:
                availability_data['availability_status'] = 'Standard Loan'
            
            return availability_data
            
        except Exception as e:
            print(f"Error extracting availability data: {e}")
            return availability_data
