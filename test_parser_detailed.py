#!/usr/bin/env python3
"""
Test script to analyze MARC field extraction in detail.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dnb_spytool'))

from dnb_spytool.api.dnb_client import DNBClient

def test_detailed_parsing():
    """Test detailed MARC field parsing."""
    try:
        client = DNBClient()
        print("Testing detailed MARC field parsing...")
        print("=" * 60)
        
        # Test with a medical author
        results = client.search_by_author('Koch', max_records=3, start_record=1)
        
        if results['publications']:
            for i, pub in enumerate(results['publications'][:2]):  # Only show first 2
                print(f"\nPublication {i+1}:")
                print("-" * 40)
                
                # Show all available fields
                for key, value in pub.items():
                    if value:  # Only show non-empty fields
                        if isinstance(value, list):
                            if value:  # Only if list is not empty
                                print(f"  {key}: {value}")
                        else:
                            print(f"  {key}: {value}")
                    else:
                        print(f"  {key}: [EMPTY/N/A]")
                
                print("\n" + "=" * 60)
        else:
            print("No publications found!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_detailed_parsing()
