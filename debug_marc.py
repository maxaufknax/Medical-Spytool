#!/usr/bin/env python3
"""Debug MARC field extraction for DNB client."""

from dnb_spytool.api.dnb_client import DNBClient
import xml.etree.ElementTree as ET

def debug_marc_fields():
    """Debug MARC field extraction."""
    try:
        client = DNBClient()
        print("Debugging MARC field extraction...")
        
        # Make a raw API call to see the XML structure
        author_name = "Einstein"
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
        
        # Look for the MARC record structure
        print("\nXML Structure Analysis:")
        print("=" * 50)
        
        # Find namespaces
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
                    print("\nMARC Record found! Analyzing fields:")
                    print("-" * 40)
                    
                    # Check control fields
                    control_fields = marc_record.findall('.//marc:controlfield', namespaces)
                    print(f"\nControl Fields ({len(control_fields)}):")
                    for cf in control_fields:
                        tag = cf.get('tag')
                        text = cf.text or ""
                        print(f"  {tag}: {text}")
                    
                    # Check data fields
                    data_fields = marc_record.findall('.//marc:datafield', namespaces)
                    print(f"\nData Fields ({len(data_fields)}):")
                    for df in data_fields[:10]:  # Show first 10
                        tag = df.get('tag')
                        ind1 = df.get('ind1', '')
                        ind2 = df.get('ind2', '')
                        
                        subfields = []
                        for sf in df.findall('.//marc:subfield', namespaces):
                            code = sf.get('code')
                            text = sf.text or ""
                            subfields.append(f"${code} {text}")
                        
                        print(f"  {tag} {ind1}{ind2}: {' | '.join(subfields)}")
                    
                    if len(data_fields) > 10:
                        print(f"  ... and {len(data_fields) - 10} more fields")
                    
                    # Look specifically for fields we're interested in
                    print("\nSpecific Field Analysis:")
                    print("-" * 40)
                    
                    interesting_fields = ['020', '022', '024', '245', '520', '856']
                    for field_tag in interesting_fields:
                        field = marc_record.find(f'.//marc:datafield[@tag="{field_tag}"]', namespaces)
                        if field is not None:
                            subfields = []
                            for sf in field.findall('.//marc:subfield', namespaces):
                                code = sf.get('code')
                                text = sf.text or ""
                                subfields.append(f"${code} {text}")
                            print(f"  {field_tag}: {' | '.join(subfields)}")
                        else:
                            print(f"  {field_tag}: NOT FOUND")
                else:
                    print("No MARC record found in recordData")
            else:
                print("No recordData found")
        else:
            print("No records found in response")
            
        # Also test our parser
        print("\n\nTesting Our Parser:")
        print("=" * 50)
        results = client.search_by_author('Einstein', max_records=1, start_record=1)
        if results['publications']:
            pub = results['publications'][0]
            print("Extracted fields:")
            for key, value in pub.items():
                if value:  # Only show non-empty fields
                    print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_marc_fields()
