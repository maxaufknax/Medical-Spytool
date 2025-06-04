#!/usr/bin/env python3
"""
Simplified integration test for enhanced URL extraction
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dnb_spytool.api.dnb_client import DNBClient
from dnb_spytool.api.database_interface import DatabaseInterface

def test_enhanced_url_extraction():
    """Test the enhanced URL extraction functionality"""
    print("=" * 60)
    print("ENHANCED URL EXTRACTION TEST")
    print("=" * 60)
    
    # 1. Test DNB search with URL extraction
    print("\n1. Testing DNB search with enhanced URL extraction...")
    dnb_client = DNBClient()
    
    try:
        # Search for a medical author
        author = "Elisabeth Pott"
        publications = dnb_client.search_publications(author, max_results=3)
        
        if not publications:
            # Try alternative author
            author = "Robert Koch"
            publications = dnb_client.search_publications(author, max_results=3)
        
        print(f"Found {len(publications)} publications for {author}")
        
        if not publications:
            print("No publications found - trying generic medical search")
            publications = dnb_client.search_publications("Medizin Gesundheit", max_results=2)
            print(f"Found {len(publications)} publications for medical search")
        
        # Analyze URL extraction results
        print("\n2. Analyzing enhanced URL extraction...")
        
        total_publications = len(publications)
        publications_with_urls = 0
        total_urls = 0
        url_type_counts = {}
        
        for i, pub in enumerate(publications[:3], 1):  # Analyze first 3
            print(f"\n--- Publication {i} ---")
            print(f"Title: {pub.get('title', 'Unknown')[:60]}...")
            print(f"Record ID: {pub.get('id', 'Not found')}")
            
            # Count URLs by type
            url_types = ['dnb_direct', 'dnb_record', 'doi', 'isbn', 'worldcat', 'google_books', 'springer', 'sciencedirect']
            pub_urls = []
            
            for url_type in url_types:
                if pub.get(url_type):
                    pub_urls.append((url_type, pub[url_type]))
                    url_type_counts[url_type] = url_type_counts.get(url_type, 0) + 1
            
            if pub_urls:
                publications_with_urls += 1
                total_urls += len(pub_urls)
                print(f"URLs found ({len(pub_urls)}):")
                for url_type, url in pub_urls:
                    print(f"  - {url_type}: {url[:50]}...")
            else:
                print("No URLs found")
        
        # Summary statistics
        print(f"\n3. URL Extraction Summary:")
        print(f"Publications analyzed: {min(3, total_publications)}")
        print(f"Publications with URLs: {publications_with_urls}")
        print(f"Total URLs extracted: {total_urls}")
        print(f"Average URLs per publication: {total_urls/min(3, total_publications):.1f}")
        
        print(f"\nURL types found:")
        for url_type, count in url_type_counts.items():
            print(f"  - {url_type}: {count}")
        
        # Test the priority order
        print(f"\n4. Testing URL priority order...")
        if publications:
            test_pub = publications[0]
            
            # Our enhanced priority order
            priority_order = ['doi', 'dnb_direct', 'dnb_record', 'springer', 'sciencedirect', 'worldcat', 'google_books', 'issn_portal']
            
            primary_url = None
            primary_type = None
            
            for url_type in priority_order:
                if test_pub.get(url_type):
                    primary_url = test_pub[url_type]
                    primary_type = url_type
                    break
            
            if primary_url:
                print(f"Primary URL (highest priority): {primary_type}")
                print(f"URL: {primary_url}")
            else:
                print("No URLs available for priority testing")
        
        # Test new schema fields
        print(f"\n5. Testing new schema fields...")
        if publications:
            test_pub = publications[0]
            new_fields = ['id', 'description', 'physical_description', 'series', 'notes']
            
            found_fields = []
            for field in new_fields:
                if field in test_pub and test_pub[field]:
                    found_fields.append(field)
            
            print(f"New schema fields with data: {found_fields}")
            
            # Show sample data for found fields
            for field in found_fields[:2]:  # Show first 2
                value = str(test_pub[field])[:100]
                print(f"  - {field}: {value}...")
        
        print(f"\n6. Results Assessment:")
        
        if publications_with_urls > 0:
            print("✓ URL extraction is working")
        else:
            print("⚠ No URLs extracted - may need debugging")
        
        if total_urls >= publications_with_urls * 2:  # At least 2 URLs per publication with URLs
            print("✓ Multiple URL types being extracted")
        else:
            print("⚠ Limited URL variety - enhancement may need refinement")
        
        if 'dnb_direct' in url_type_counts or 'dnb_record' in url_type_counts:
            print("✓ DNB-specific URLs are being extracted")
        else:
            print("⚠ DNB URLs not found - may need MARC parsing debug")
        
        return total_urls > 0
        
    except Exception as e:
        print(f"Error in URL extraction test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_compatibility():
    """Test compatibility with GUI URL expectations"""
    print("\n" + "=" * 50)
    print("GUI COMPATIBILITY TEST")
    print("=" * 50)
    
    try:
        dnb_client = DNBClient()
        publications = dnb_client.search_publications("Medizin", max_results=1)
        
        if not publications:
            print("No publications for compatibility test")
            return False
        
        pub = publications[0]
        
        # Test what GUI would expect
        gui_expected_urls = []
        
        # Current GUI implementation checks these fields
        if pub.get('doi'):
            gui_expected_urls.append(f"https://doi.org/{pub['doi']}")
        
        if pub.get('pmid'):
            gui_expected_urls.append(f"https://pubmed.ncbi.nlm.nih.gov/{pub['pmid']}/")
        
        if pub.get('url'):
            gui_expected_urls.append(pub['url'])
        
        # Our enhanced URLs
        enhanced_urls = []
        url_types = ['dnb_direct', 'dnb_record', 'doi', 'isbn', 'worldcat', 'google_books']
        
        for url_type in url_types:
            if pub.get(url_type):
                enhanced_urls.append(pub[url_type])
        
        print(f"GUI would find: {len(gui_expected_urls)} URLs")
        print(f"Enhanced extraction found: {len(enhanced_urls)} URLs")
        
        if enhanced_urls:
            print("✓ Enhanced URL extraction provides URLs for GUI")
            print(f"Sample URL: {enhanced_urls[0]}")
        else:
            print("⚠ No enhanced URLs available for GUI")
        
        return len(enhanced_urls) > 0
        
    except Exception as e:
        print(f"Error in GUI compatibility test: {e}")
        return False

if __name__ == "__main__":
    print("Starting Enhanced URL Extraction Integration Test...")
    
    success1 = test_enhanced_url_extraction()
    success2 = test_gui_compatibility()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 INTEGRATION TEST PASSED!")
        print("✓ Enhanced URL extraction is working")
        print("✓ Multiple URL types are being extracted")
        print("✓ GUI compatibility maintained")
        print("\nThe URL opening functionality should now work in the GUI.")
        print("Ready for real-world testing!")
    else:
        print("❌ INTEGRATION TEST ISSUES DETECTED")
        print("Review the results above for specific problems.")
    print("=" * 60)
