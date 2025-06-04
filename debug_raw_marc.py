#!/usr/bin/env python3
"""
Debug script to examine raw MARC XML data.
"""

import sys
import os
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dnb_spytool'))

from dnb_spytool.api.dnb_client import DNBClient

def debug_raw_marc():
    """Debug raw MARC XML data to see available fields."""
    try:
        client = DNBClient()
        print("Examining raw MARC XML data...")
        print("=" * 60)
        
        # Make a raw API call 
        author_name = "Koch"
        params = {
            'version': '1.1',
            'operation': 'searchRetrieve',
            'query': f'per="{author_name}"',
            'recordSchema': 'MARC21-xml',
            'maximumRecords': 1,
            'startRecord': 1
        }
        
        response = client.session.get(client.base_url, params=params, timeout=30)
        response.raise_for_status()
        
        # Parse the XML to examine structure
        root = ET.fromstring(response.content)
        
        namespaces = {
            'srw': 'http://www.loc.gov/zing/srw/',
            'marc': 'http://www.loc.gov/MARC21/slim'
        }
        
        # Find first record
        first_record = root.find('.//srw:record', namespaces)
        if first_record is not None:
            record_data = first_record.find('.//srw:recordData', namespaces)
            if record_data is not None:
                marc_record = record_data.find('.//marc:record', namespaces)
                if marc_record is not None:
                    print("Full MARC Record Analysis:")
                    print("-" * 40)
                    
                    # Show ALL data fields
                    data_fields = marc_record.findall('.//marc:datafield', namespaces)
                    print(f"\nAll Data Fields ({len(data_fields)}):")
                    
                    for df in data_fields:
                        tag = df.get('tag')
                        ind1 = df.get('ind1', '')
                        ind2 = df.get('ind2', '')
                        
                        subfields = []
                        for sf in df.findall('.//marc:subfield', namespaces):
                            code = sf.get('code')
                            text = sf.text or ""
                            subfields.append(f"${code} {text}")
                        
                        print(f"  {tag} {ind1}{ind2}: {' | '.join(subfields)}")
                    
                    # Look for specific fields that should contain descriptions, subjects, etc.
                    print("\n\nSpecific Field Search:")
                    print("-" * 40)
                    
                    # Fields that often contain the data we're missing
                    interesting_fields = {
                        '520': 'Summary/Abstract',
                        '505': 'Contents note',
                        '650': 'Subject heading - topical term',
                        '651': 'Subject heading - geographic name', 
                        '655': 'Index term - genre/form',
                        '600': 'Subject heading - personal name',
                        '610': 'Subject heading - corporate name',
                        '022': 'ISSN',
                        '024': 'Other standard identifier',
                        '856': 'Electronic location and access',
                        '500': 'General note',
                        '504': 'Bibliography note',
                        '502': 'Dissertation note'
                    }
                    
                    for field_tag, description in interesting_fields.items():
                        fields = marc_record.findall(f'.//marc:datafield[@tag="{field_tag}"]', namespaces)
                        if fields:
                            print(f"\n{field_tag} ({description}):")
                            for field in fields:
                                subfields = []
                                for sf in field.findall('.//marc:subfield', namespaces):
                                    code = sf.get('code')
                                    text = sf.text or ""
                                    subfields.append(f"${code} {text}")
                                print(f"    {' | '.join(subfields)}")
                        else:
                            print(f"\n{field_tag} ({description}): NOT FOUND")
                            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_raw_marc()
