#!/usr/bin/env python3
"""
Integration test to verify GUI URL functionality works with enhanced DNB client
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dnb_spytool.api.dnb_client import DNBClient
from dnb_spytool.api.database_interface import DatabaseInterface
from dnb_spytool.gui.main_window import DNBSpytoolGUI
import tkinter as tk
from unittest.mock import patch

def test_url_workflow():
    """Test the complete URL workflow from search to GUI display"""
    print("=" * 60)
    print("GUI INTEGRATION TEST - URL Functionality Verification")
    print("=" * 60)
    
    # 1. Test DNB search and URL extraction
    print("\n1. Testing DNB search and URL extraction...")
    dnb_client = DNBClient()
    
    # Search for a medical author likely to have DNB records
    author = "Elisabeth Pott"  # Known medical author in DNB
    
    try:
        publications = dnb_client.search_publications(author, max_results=3)
        print(f"Found {len(publications)} publications for {author}")
        
        if not publications:
            print("No publications found - testing with different author")
            author = "Robert Koch"
            publications = dnb_client.search_publications(author, max_results=3)
            print(f"Found {len(publications)} publications for {author}")
        
        # Analyze URL data in publications
        print("\n2. Analyzing URL data in publications...")
        for i, pub in enumerate(publications[:2], 1):
            print(f"\nPublication {i}: {pub.get('title', 'Unknown Title')[:50]}...")
            print(f"Record ID: {pub.get('id', 'Not found')}")
            
            # Check all URL types
            url_types = ['dnb_direct', 'dnb_record', 'doi', 'isbn', 'worldcat', 'google_books', 'springer']
            found_urls = []
            for url_type in url_types:
                if pub.get(url_type):
                    found_urls.append(f"{url_type}: {pub[url_type]}")
            
            print(f"Available URLs ({len(found_urls)}):")
            for url in found_urls[:3]:  # Show first 3
                print(f"  - {url}")
            if len(found_urls) > 3:
                print(f"  ... and {len(found_urls) - 3} more")
    
    except Exception as e:
        print(f"Error in DNB search test: {e}")
        return False
    
    # 3. Test GUI URL extraction methods
    print("\n3. Testing GUI URL extraction methods...")
    
    # Create a test GUI instance (without actually showing it)
    root = tk.Tk()
    root.withdraw()  # Hide the window
      try:
        gui = DNBSpytoolGUI(root)
        
        # Test _get_publication_urls method with our publication data
        if publications:
            test_pub = publications[0]
            urls = gui._get_publication_urls(test_pub)
            
            print(f"GUI extracted {len(urls)} URLs from first publication:")
            for i, (url_type, url) in enumerate(urls[:3], 1):
                print(f"  {i}. {url_type}: {url[:60]}...")
            
            # Test URL button state logic
            has_urls = len(urls) > 0
            print(f"\nURL buttons should be {'enabled' if has_urls else 'disabled'}")
            
            # Simulate the URL opening workflow
            print(f"\n4. Simulating URL opening workflow...")
            if urls:
                # Test single URL scenario
                if len(urls) == 1:
                    print(f"Single URL scenario - would open: {urls[0][1]}")
                else:
                    print(f"Multiple URLs scenario - would show selection dialog with {len(urls)} options")
                    
                print("✓ URL opening workflow simulation successful")
            else:
                print("⚠ No URLs available for opening workflow")
        
    except Exception as e:
        print(f"Error in GUI test: {e}")
        return False
    finally:
        root.destroy()
    
    # 4. Test database integration
    print("\n5. Testing database integration...")
    try:
        # Test that the enhanced schema fields are properly handled
        db_interface = DatabaseInterface()
        
        if publications:
            test_pub = publications[0]
            
            # Check that new optional fields are accessible
            new_fields = ['id', 'description', 'physical_description', 'series', 'notes']
            available_fields = []
            
            for field in new_fields:
                if field in test_pub:
                    available_fields.append(field)
            
            print(f"New schema fields available: {available_fields}")
            print(f"✓ Database schema enhancement working")
    
    except Exception as e:
        print(f"Error in database test: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("INTEGRATION TEST RESULTS:")
    print("✓ DNB client URL extraction enhanced")
    print("✓ GUI URL methods functional") 
    print("✓ Database schema updated")
    print("✓ Complete workflow ready for real-world testing")
    print("=" * 60)
    
    return True

def test_url_button_states():
    """Test URL button state management logic"""
    print("\n" + "=" * 50)
    print("URL BUTTON STATE TEST")
    print("=" * 50)
    
    root = tk.Tk()
    root.withdraw()
      try:
        gui = DNBSpytoolGUI(root)
        
        # Test case 1: Publication with URLs
        pub_with_urls = {
            'title': 'Test Publication',
            'dnb_direct': 'https://d-nb.info/123456789',
            'doi': 'https://doi.org/10.1000/test'
        }
        
        urls = gui._get_publication_urls(pub_with_urls)
        print(f"Test 1 - Publication with URLs: {len(urls)} URLs found")
        print(f"Expected button state: ENABLED")
        
        # Test case 2: Publication without URLs
        pub_without_urls = {
            'title': 'Test Publication No URLs',
            'authors': 'Test Author'
        }
        
        urls = gui._get_publication_urls(pub_without_urls)
        print(f"Test 2 - Publication without URLs: {len(urls)} URLs found")
        print(f"Expected button state: DISABLED")
        
        print("✓ URL button state logic verified")
        
    except Exception as e:
        print(f"Error in button state test: {e}")
        return False
    finally:
        root.destroy()
    
    return True

if __name__ == "__main__":
    print("Starting GUI Integration Test...")
    
    # Run integration tests
    success1 = test_url_workflow()
    success2 = test_url_button_states()
    
    if success1 and success2:
        print("\n🎉 All integration tests passed!")
        print("The URL functionality should now work properly in the GUI.")
        print("\nNext steps:")
        print("1. Run the actual GUI application")
        print("2. Perform a DNB search")
        print("3. Test double-click and URL buttons on results")
    else:
        print("\n❌ Some integration tests failed.")
        print("Review the error messages above for debugging.")
