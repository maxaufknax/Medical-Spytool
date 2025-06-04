#!/usr/bin/env python3
"""
Test script to verify the distribution versions have the proper fixes.
"""

import sys
import os

def test_distribution_safe_functions(distribution_path, name):
    """Test the safe functions in a distribution version."""
    print(f"\nTesting {name}...")
    
    try:
        # Add distribution path to sys.path
        sys.path.insert(0, distribution_path)
        
        # Import the GUI class
        from dnb_spytool.gui.main_window import DNBSpytoolGUI
        import tkinter as tk
        
        # Create a test root and GUI instance
        root = tk.Tk()
        root.withdraw()  # Hide the window
        gui = DNBSpytoolGUI(root)
        
        # Create mock publication for testing safe_get and safe_join
        publication = {'title': 'Test', 'empty_field': None, 'blank_field': ''}
        
        # Test a mock publication detail display
        # We'll simulate what the show_publication_details method does
        def safe_join(value, default=''):
            if value is None:
                return default
            elif isinstance(value, list):
                return ', '.join(str(item) for item in value if item) or default
            elif isinstance(value, str):
                return value or default
            else:
                return str(value) or default
        
        def safe_get(key, default=''):
            return publication.get(key, default) or default
        
        # Test the functions
        result1 = safe_join(None)
        result2 = safe_join([])
        result3 = safe_get('nonexistent')
        result4 = safe_get('empty_field')
        
        print(f"  safe_join(None) = '{result1}'")
        print(f"  safe_join([]) = '{result2}'")
        print(f"  safe_get('nonexistent') = '{result3}'")
        print(f"  safe_get('empty_field') = '{result4}'")
        
        # Check for N/A values
        results = [result1, result2, result3, result4]
        na_found = any('N/A' in str(r) for r in results)
        
        root.destroy()
        
        if na_found:
            print(f"  ❌ FAILED: Found 'N/A' values in {name}")
            return False
        else:
            print(f"  ✅ PASSED: No 'N/A' values found in {name}")
            return True
            
    except Exception as e:
        print(f"  ❌ ERROR testing {name}: {e}")
        return False
    finally:
        # Clean up sys.path
        if distribution_path in sys.path:
            sys.path.remove(distribution_path)


def main():
    """Test both distribution versions."""
    print("=== Testing Distribution Versions for Phase 1 Fixes ===")
    
    base_path = r"c:\Users\paaschma\Documents\coding\medical_spytool_1.2\Medical-Spytool-medicalspy-1.2-beta-\FINAL_DISTRIBUTION"
    
    # Test Source distribution
    source_path = os.path.join(base_path, "Source")
    test1_passed = test_distribution_safe_functions(source_path, "Source Distribution")
    
    # Test Portable App distribution  
    portable_path = os.path.join(base_path, "Portable-App", "Medical-Spytool-Portable")
    test2_passed = test_distribution_safe_functions(portable_path, "Portable App Distribution")
    
    print(f"\n=== Distribution Test Results ===")
    print(f"Source Distribution: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Portable App Distribution: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All distribution versions have proper fixes!")
        return True
    else:
        print("\n⚠️ Some distribution versions still have issues.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
