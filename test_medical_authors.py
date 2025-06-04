#!/usr/bin/env python3
"""Test URL extraction for medical publications."""

from dnb_spytool.api.dnb_client import DNBClient

def test_medical_publications():
    """Test URL extraction for medical authors."""
    try:
        client = DNBClient()
        
        # Test with medical authors
        medical_authors = ["Müller", "Schmidt", "Weber"]
        
        for author in medical_authors:
            print(f"\n{'='*60}")
            print(f"Testing author: {author}")
            print('='*60)
            
            results = client.search_by_author(author, max_records=3, start_record=1)
            print(f"Found {len(results['publications'])} publications")
            
            for i, pub in enumerate(results['publications'][:2]):  # Show first 2
                print(f"\nPublication {i+1}:")
                print(f"Title: {pub.get('title', 'N/A')[:80]}...")
                print(f"Authors: {pub.get('authors', 'N/A')}")
                print(f"Year: {pub.get('publication_year', 'N/A')}")
                print(f"Publisher: {pub.get('publisher', 'N/A')}")
                print(f"Type: {pub.get('publication_type', 'N/A')}")
                print(f"Language: {pub.get('language', 'N/A')}")
                print(f"ISBN: {pub.get('isbn', 'N/A')}")
                print(f"ISSN: {pub.get('issn', 'N/A')}")
                print(f"DOI: {pub.get('doi', 'N/A')}")
                print(f"Record ID: {pub.get('id', 'N/A')}")
                
                # URL information
                print(f"\nURL Information:")
                print(f"Primary URL: {pub.get('url', 'No URL')}")
                
                all_urls = pub.get('all_urls', {})
                if all_urls:
                    print("Available URLs:")
                    for url_type, url in all_urls.items():
                        print(f"  {url_type}: {url}")
                else:
                    print("No URLs available")
                
                # Check for additional metadata
                desc = pub.get('description', '')
                if desc and len(desc) > 10:
                    print(f"Description: {desc[:100]}...")
                
                phys_desc = pub.get('physical_description', '')
                if phys_desc:
                    print(f"Physical: {phys_desc}")
                
                series = pub.get('series', '')
                if series:
                    print(f"Series: {series}")
                
                notes = pub.get('notes', '')
                if notes:
                    print(f"Notes: {notes}")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_medical_publications()
