#!/usr/bin/env python3
"""
Debug script to trace URL enhancement process
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dnb_spytool.api.dnb_client import DNBClient
import xml.etree.ElementTree as ET

def debug_url_enhancement():
    """Debug the URL enhancement process step by step"""
    print("=" * 60)
    print("URL ENHANCEMENT DEBUG")
    print("=" * 60)
    
    dnb_client = DNBClient()
    
    # Get raw search results first
    print("1. Getting raw search results...")
    try:
        raw_query = "Elisabeth Pott"
        response = dnb_client._make_sru_request("any", raw_query, 1, 2)
        
        if response and 'records' in response:
            print(f"Found {len(response['records'])} raw records")
            
            for i, record in enumerate(response['records'][:1], 1):  # Debug first record
                print(f"\n--- Debugging Record {i} ---")
                
                # Parse the record
                parsed = dnb_client.parser.parse_marc_record(record)
                print(f"After parsing: {list(parsed.keys())}")
                print(f"Record ID: {parsed.get('id', 'NOT FOUND')}")
                
                # Check raw MARC for URLs
                if 'marcxml' in record:
                    print("\nChecking raw MARC XML for URLs...")
                    try:
                        root = ET.fromstring(record['marcxml'])
                        
                        # Look for field 856 (URLs)
                        url_fields = root.findall(".//ns:datafield[@tag='856']", 
                                                {'ns': 'http://www.loc.gov/MARC21/slim'})
                        print(f"Found {len(url_fields)} URL fields (856)")
                        
                        for j, field in enumerate(url_fields):
                            subfields = field.findall(".//ns:subfield", 
                                                    {'ns': 'http://www.loc.gov/MARC21/slim'})
                            print(f"  Field {j+1}:")
                            for subfield in subfields:
                                code = subfield.get('code')
                                text = subfield.text or ''
                                print(f"    {code}: {text}")
                        
                        # Look for control field 001 (Record ID)
                        id_field = root.find(".//ns:controlfield[@tag='001']", 
                                           {'ns': 'http://www.loc.gov/MARC21/slim'})
                        if id_field is not None:
                            print(f"Record ID from 001: {id_field.text}")
                        else:
                            print("No control field 001 found")
                    
                    except Exception as e:
                        print(f"Error parsing MARC XML: {e}")
                
                # Test URL enhancement
                print(f"\nTesting URL enhancement...")
                enhanced = dnb_client._enhance_publication_with_urls(parsed)
                
                print(f"Before enhancement URLs: {[k for k in parsed.keys() if 'url' in k.lower() or k in ['doi', 'isbn']]}")
                print(f"After enhancement URLs: {[k for k in enhanced.keys() if 'url' in k.lower() or k in ['doi', 'isbn', 'dnb_direct', 'dnb_record', 'worldcat', 'google_books', 'springer']]}")
                
                # Show all URL-related fields
                url_related = ['doi', 'isbn', 'dnb_direct', 'dnb_record', 'worldcat', 'google_books', 'springer', 'sciencedirect']
                print(f"\nURL-related fields in enhanced record:")
                for field in url_related:
                    if field in enhanced:
                        value = enhanced[field]
                        print(f"  {field}: {value}")
                
                if enhanced.get('id'):
                    expected_dnb_url = f"https://d-nb.info/{enhanced['id']}"
                    print(f"\nExpected DNB record URL: {expected_dnb_url}")
                    if enhanced.get('dnb_record') == expected_dnb_url:
                        print("✓ DNB record URL correctly generated")
                    else:
                        print(f"⚠ DNB record URL mismatch: {enhanced.get('dnb_record')}")
        else:
            print("No records found in response")
    
    except Exception as e:
        print(f"Error in debug: {e}")
        import traceback
        traceback.print_exc()

def test_url_generation():
    """Test URL generation methods"""
    print("\n" + "=" * 50)
    print("URL GENERATION TEST")
    print("=" * 50)
    
    # Test with sample data
    sample_publication = {
        'id': '1234567890',
        'isbn': '9783769213720',
        'title': 'Test Publication',
        'authors': 'Test Author'
    }
    
    dnb_client = DNBClient()
    enhanced = dnb_client._enhance_publication_with_urls(sample_publication)
    
    print(f"Sample publication: {sample_publication}")
    print(f"\nGenerated URLs:")
    
    url_fields = ['dnb_direct', 'dnb_record', 'worldcat', 'google_books', 'springer']
    for field in url_fields:
        if field in enhanced:
            print(f"  {field}: {enhanced[field]}")
    
    # Test the enhancement method step by step
    print(f"\nStep-by-step URL generation:")
    
    # Test DNB record URL generation
    if enhanced.get('id'):
        expected_dnb = f"https://d-nb.info/{enhanced['id']}"
        print(f"1. DNB record URL: {expected_dnb}")
    
    # Test ISBN-based URLs
    if enhanced.get('isbn'):
        isbn = enhanced['isbn']
        expected_worldcat = f"https://www.worldcat.org/isbn/{isbn}"
        expected_google = f"https://books.google.com/books?q=isbn:{isbn}"
        print(f"2. WorldCat URL: {expected_worldcat}")
        print(f"3. Google Books URL: {expected_google}")

if __name__ == "__main__":
    debug_url_enhancement()
    test_url_generation()
