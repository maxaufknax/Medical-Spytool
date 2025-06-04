#!/usr/bin/env python3
"""Test URL extraction for DNB client."""

from dnb_spytool.api.dnb_client import DNBClient

def test_url_extraction():
    """Test URL extraction for DNB publications."""
    try:
        client = DNBClient()
        print("Testing DNB URL extraction...")
        
        # Search for a test author
        results = client.search_by_author('Einstein', max_records=2, start_record=1)
        print(f"Found {len(results['publications'])} publications")
        
        for i, pub in enumerate(results['publications'][:2]):
            print(f"\nPublication {i+1}:")
            print(f"Title: {pub.get('title', 'N/A')[:100]}...")
            print(f"URL: {pub.get('url', 'No URL')}")
            print(f"DOI: {pub.get('doi', 'No DOI')}")
            print(f"All URLs: {pub.get('all_urls', 'No URLs')}")
            print(f"ISBN: {pub.get('isbn', 'No ISBN')}")
            print(f"ISSN: {pub.get('issn', 'No ISSN')}")
            print(f"Record ID: {pub.get('id', 'No ID')}")
            print(f"Description: {pub.get('description', 'No Description')[:100]}...")
            print(f"Type: {pub.get('publication_type', 'No Type')}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_url_extraction()
