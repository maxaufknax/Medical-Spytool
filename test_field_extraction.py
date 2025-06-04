#!/usr/bin/env python3
"""Test specific field extraction."""

from dnb_spytool.api.parser import MARCXMLParser
import xml.etree.ElementTree as ET

def test_field_extraction():
    """Test specific field extraction methods."""
    try:
        # Create parser
        parser = MARCXMLParser()
        
        # Get sample MARC record from API
        from dnb_spytool.api.dnb_client import DNBClient
        client = DNBClient()
        
        # Make a raw API call
        params = {
            'version': '1.1',
            'operation': 'searchRetrieve',
            'query': 'per="Einstein"',
            'recordSchema': 'MARC21-xml',
            'maximumRecords': 1,
            'startRecord': 1
        }
        
        response = client.session.get(client.base_url, params=params, timeout=30)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.content)
        namespaces = {
            'srw': 'http://www.loc.gov/zing/srw/',
            'marc': 'http://www.loc.gov/MARC21/slim'
        }
        
        # Find MARC record
        marc_record = root.find('.//marc:record', namespaces)
        if marc_record is not None:
            print("Testing field extraction methods:")
            print("-" * 40)
            
            # Test record ID
            record_id = parser._get_record_id(marc_record)
            print(f"Record ID: '{record_id}'")
            
            # Test URL extraction
            url = parser._extract_url(marc_record)
            print(f"Direct URL: '{url}'")
            
            # Test DOI extraction
            doi = parser._extract_doi(marc_record)
            print(f"DOI: '{doi}'")
            
            # Test ISSN extraction
            issn = parser._extract_issn(marc_record)
            print(f"ISSN: '{issn}'")
            
            # Test description extraction
            description = parser._extract_description(marc_record)
            print(f"Description: '{description[:100]}...' ({len(description)} chars)")
            
            # Manual check of field 856
            print("\nManual Field 856 Check:")
            field_856 = marc_record.find('.//marc:datafield[@tag="856"]', parser.namespaces)
            if field_856 is not None:
                print("Field 856 found!")
                for subfield in field_856.findall('.//marc:subfield', parser.namespaces):
                    code = subfield.get('code')
                    text = subfield.text or ""
                    print(f"  Subfield {code}: {text}")
            else:
                print("Field 856 NOT found")
            
            # Manual check of control field 001
            print("\nManual Control Field 001 Check:")
            control_001 = marc_record.find('.//marc:controlfield[@tag="001"]', parser.namespaces)
            if control_001 is not None:
                print(f"Control field 001 found: '{control_001.text}'")
            else:
                print("Control field 001 NOT found")
        else:
            print("No MARC record found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_field_extraction()
