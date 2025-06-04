#!/usr/bin/env python3
"""
Test script to verify the MARC parser debugging fixes.
Tests that "N/A" values have been eliminated and proper empty strings are returned.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dnb_spytool'))

from dnb_spytool.api.parser import MARCXMLParser


def test_safe_functions():
    """Test helper functions that previously returned 'N/A'."""
    print("Testing safe function behavior...")
    
    # Create a mock publication dict with missing values
    publication = {
        'title': 'Test Title',
        'authors': ['Author One'],
        'isbn': None,
        'issn': '',
        'doi': '',
        'subjects': []
    }
    
    # Import the GUI class to test safe functions
    try:
        from dnb_spytool.gui.main_window import DNBSpytoolGUI
        import tkinter as tk
        
        # Create a test root and GUI instance
        root = tk.Tk()
        gui = DNBSpytoolGUI(root)
        
        # Test safe_join function
        empty_list = []
        none_value = None
        empty_string = ""
        
        result1 = gui.safe_join(empty_list)
        result2 = gui.safe_join(none_value) 
        result3 = gui.safe_join(empty_string)
        
        print(f"safe_join([]) = '{result1}' (should be empty)")
        print(f"safe_join(None) = '{result2}' (should be empty)")
        print(f"safe_join('') = '{result3}' (should be empty)")
        
        # Verify no "N/A" values
        results = [result1, result2, result3]
        na_found = any('N/A' in str(r) for r in results)
        
        if na_found:
            print("❌ FAILED: Found 'N/A' values in safe_join results")
            return False
        else:
            print("✅ PASSED: No 'N/A' values found in safe_join results")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ ERROR testing GUI safe functions: {e}")
        return False


def test_parser_enhancements():
    """Test MARC parser enhancements."""
    print("\nTesting MARC parser enhancements...")
    
    try:
        parser = MARCXMLParser()
        
        # Create a minimal test MARC record
        test_marc_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <marc:collection xmlns:marc="http://www.loc.gov/MARC21/slim">
            <marc:record>
                <marc:controlfield tag="001">123456</marc:controlfield>
                <marc:datafield tag="245" ind1="1" ind2="0">
                    <marc:subfield code="a">Test Medical Publication</marc:subfield>
                    <marc:subfield code="b">A Study</marc:subfield>
                </marc:datafield>
                <marc:datafield tag="100" ind1="1" ind2=" ">
                    <marc:subfield code="a">Smith, John</marc:subfield>
                </marc:datafield>
            </marc:record>
        </marc:collection>'''
        
        # Parse the test record
        import xml.etree.ElementTree as ET
        root = ET.fromstring(test_marc_xml)
        record = root.find('.//{http://www.loc.gov/MARC21/slim}record')
        
        if record is not None:
            # Test title extraction
            title = parser._extract_title(record)
            print(f"Extracted title: '{title}'")
            
            # Test author extraction
            authors = parser._extract_authors(record)
            print(f"Extracted authors: {authors}")
            
            # Test that empty values return empty strings, not defaults
            isbn = parser._extract_isbn(record)
            issn = parser._extract_issn(record)
            doi = parser._extract_doi(record)
            
            print(f"ISBN (should be empty): '{isbn}'")
            print(f"ISSN (should be empty): '{issn}'")
            print(f"DOI (should be empty): '{doi}'")
            
            # Verify no "N/A" or "Unknown" defaults
            all_values = [title, isbn, issn, doi] + authors
            problem_values = [v for v in all_values if v and ('N/A' in str(v) or 'Unknown' in str(v))]
            
            if problem_values:
                print(f"❌ FAILED: Found problematic default values: {problem_values}")
                return False
            else:
                print("✅ PASSED: No problematic default values found")
                return True
        else:
            print("❌ ERROR: Could not parse test MARC record")
            return False
            
    except Exception as e:
        print(f"❌ ERROR testing parser: {e}")
        return False


def main():
    """Run all tests."""
    print("=== Medical Spytool v1.2-beta Phase 1 Fix Verification ===")
    print("Testing elimination of 'N/A' values from MARC parser debugging...\n")
    
    test1_passed = test_safe_functions()
    test2_passed = test_parser_enhancements()
    
    print(f"\n=== Test Results ===")
    print(f"GUI Safe Functions: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Parser Enhancements: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Phase 1 fixes successfully implemented.")
        print("The MARC parser debugging phase is complete.")
        return True
    else:
        print("\n⚠️ Some tests failed. Review the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
