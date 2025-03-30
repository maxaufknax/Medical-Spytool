"""
Main Window

This module defines the main application window and its components.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

from gui.search_tab import SearchTab
from gui.results_tab import ResultsTab
from gui.analysis_tab import AnalysisTab
from gui.settings_tab import SettingsTab
from utils.config_manager import load_settings, ensure_directories

logger = logging.getLogger(__name__)

class MainWindow:
    """
    Main application window class.
    """
    
    def __init__(self, master):
        """
        Initialize the main window.
        
        Args:
            master (tk.Tk): Root Tkinter window.
        """
        self.master = master
        self.settings = load_settings()
        ensure_directories(self.settings)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initialize search results
        self.search_results = []
        
        # Create tabs
        self.create_tabs()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.create_status_bar()
        
        logger.info("Main window initialized")
    
    def create_tabs(self):
        """Create application tabs."""
        # Search Tab
        self.search_tab = SearchTab(self.notebook, self)
        self.notebook.add(self.search_tab.frame, text="Search")
        
        # Results Tab
        self.results_tab = ResultsTab(self.notebook, self)
        self.notebook.add(self.results_tab.frame, text="Results")
        
        # Analysis Tab
        self.analysis_tab = AnalysisTab(self.notebook, self)
        self.notebook.add(self.analysis_tab.frame, text="Analysis")
        
        # Settings Tab
        self.settings_tab = SettingsTab(self.notebook, self)
        self.notebook.add(self.settings_tab.frame, text="Settings")
        
        # Set up tab change events
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def create_menu_bar(self):
        """Create the application menu bar."""
        self.menu_bar = tk.Menu(self.master)
        self.master.config(menu=self.menu_bar)
        
        # File Menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Results...", command=self.results_tab.export_results)
        file_menu.add_command(label="Export Log...", command=self.search_tab.export_log)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)
        
        # Edit Menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Clear Results", command=self.clear_results)
        edit_menu.add_command(label="Clear Log", command=self.search_tab.clear_log)
        
        # Help Menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_status_bar(self):
        """Create the application status bar."""
        self.status_bar = ttk.Frame(self.master)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        
        # Status message
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_label = ttk.Label(self.status_bar, textvariable=self.status_var, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_var.set(0)
        self.progress_bar = ttk.Progressbar(
            self.status_bar, 
            variable=self.progress_var, 
            mode='determinate',
            length=200
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
    
    def update_status(self, message, progress=None):
        """
        Update the status bar.
        
        Args:
            message (str): Status message to display.
            progress (float, optional): Progress value (0-100).
        """
        self.status_var.set(message)
        if progress is not None:
            self.progress_var.set(progress)
        self.master.update_idletasks()
    
    def on_tab_changed(self, event):
        """
        Handle tab change events.
        
        Args:
            event: Tab change event.
        """
        tab_id = self.notebook.select()
        tab_name = self.notebook.tab(tab_id, "text")
        
        # Update results if switching to Results or Analysis tab
        if tab_name == "Results":
            self.results_tab.update_results(self.search_results)
        elif tab_name == "Analysis":
            self.analysis_tab.update_data(self.search_results)
    
    def update_results(self, results):
        """
        Update search results.
        
        Args:
            results (list): New search results.
        """
        self.search_results = results
        self.results_tab.update_results(results)
        self.analysis_tab.update_data(results)
    
    def clear_results(self):
        """Clear all search results."""
        if messagebox.askyesno("Clear Results", "Are you sure you want to clear all search results?"):
            self.search_results = []
            self.results_tab.update_results([])
            self.analysis_tab.update_data([])
            self.search_tab.log_message("Results cleared")
    
    def show_about(self):
        """Show the about dialog."""
        messagebox.showinfo(
            "About Integrated Publication Search Tool",
            "Integrated Publication Search Tool\n\n"
            "Version 1.0\n\n"
            "This application provides a unified interface for searching multiple academic databases "
            "including PubMed and the German National Library (DNB).\n\n"
            "Features include person management, advanced search options, "
            "result visualization, and export functionality."
        )
