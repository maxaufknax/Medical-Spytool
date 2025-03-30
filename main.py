#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integrated Publication Search Tool

This application provides a unified interface for searching multiple academic databases
including PubMed and the German National Library (DNB). It supports person management,
advanced search options, result visualization, and export functionality.

Usage:
    python main.py
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
import logging

# Setup proper path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Application imports
from gui.main_window import MainWindow
from utils.logging_manager import setup_logging

def main():
    """
    Entry point for the application.
    Initializes logging and starts the main application window.
    """
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Integrated Publication Search Tool")
    
    try:
        # Create the root window
        root = tk.Tk()
        root.title("Integrated Publication Search Tool")
        
        # Set minimum size
        root.minsize(1000, 700)
        
        # Create the main application window
        app = MainWindow(root)
        
        # Start the main event loop
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        messagebox.showerror("Application Error", 
                            f"An unexpected error occurred:\n{str(e)}\n\nPlease check the log file for details.")
    finally:
        logger.info("Application terminated")

if __name__ == "__main__":
    main()
