#!/usr/bin/env python3
"""
Test script to verify that the Tkinter timer issue is fixed.
This script tests the DNBSpytoolGUI timer management without requiring GUI display.
"""

import tkinter as tk
import time
import sys
import os

# Add the dnb_spytool package to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_timer_cleanup():
    """Test that the timer cleanup works correctly."""
    print("Testing DNBSpytoolGUI timer management...")
    
    try:
        # Create root window
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Import after setting up Tkinter
        from dnb_spytool.gui.main_window import DNBSpytoolGUI
        
        # Create GUI instance
        app = DNBSpytoolGUI(root)
        
        # Verify timer management attributes exist
        assert hasattr(app, 'after_id'), "after_id attribute missing"
        assert hasattr(app, 'is_running'), "is_running attribute missing" 
        assert hasattr(app, 'on_closing'), "on_closing method missing"
        assert hasattr(app, 'check_results'), "check_results method missing"
        
        print("✅ Timer management attributes found")
        
        # Test initial state
        assert app.is_running == True, "is_running should be True initially"
        print("✅ Initial state correct")
        
        # Test cleanup
        app.on_closing()
        assert app.is_running == False, "is_running should be False after cleanup"
        print("✅ Cleanup works correctly")
        
        # Test safe_join function in show_publication_details
        test_pub = {
            'title': 'Test Publication',
            'author': ['Author 1', 'Author 2'],  # List
            'isbn': 'single_isbn',  # String
            'language': None,  # None value
            'subject': [],  # Empty list
        }
        
        # This should not raise TypeError anymore
        try:
            app.show_publication_details(test_pub)
            print("✅ safe_join function works correctly - no TypeError")
        except Exception as e:
            print(f"❌ Error in show_publication_details: {e}")
            return False
        
        print("🎉 All timer and TypeError fixes verified successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        try:
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    success = test_timer_cleanup()
    sys.exit(0 if success else 1)
