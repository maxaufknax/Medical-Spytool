"""
Settings Tab

This module defines the settings tab for application configuration.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import logging

from utils.config_manager import save_settings, ensure_directories

logger = logging.getLogger(__name__)

class SettingsTab:
    """
    Tab for application settings.
    """
    
    def __init__(self, notebook, main_window):
        """
        Initialize the settings tab.
        
        Args:
            notebook (ttk.Notebook): Parent notebook.
            main_window (MainWindow): Main application window.
        """
        self.notebook = notebook
        self.main_window = main_window
        self.settings = main_window.settings
        
        # Create frame
        self.frame = ttk.Frame(notebook, padding=10)
        
        # Create widgets
        self.create_widgets()
        
        logger.info("Settings tab initialized")
    
    def create_widgets(self):
        """Create settings tab widgets."""
        # Create a notebook for settings categories
        self.settings_notebook = ttk.Notebook(self.frame)
        self.settings_notebook.pack(fill=tk.BOTH, expand=True)
        
        # General settings tab
        self.general_frame = ttk.Frame(self.settings_notebook, padding=10)
        self.settings_notebook.add(self.general_frame, text="General")
        self.create_general_settings()
        
        # API keys tab
        self.api_keys_frame = ttk.Frame(self.settings_notebook, padding=10)
        self.settings_notebook.add(self.api_keys_frame, text="API Keys")
        self.create_api_keys_settings()
        
        # Output settings tab
        self.output_frame = ttk.Frame(self.settings_notebook, padding=10)
        self.settings_notebook.add(self.output_frame, text="Output")
        self.create_output_settings()
        
        # Button frame at the bottom
        self.button_frame = ttk.Frame(self.frame)
        self.button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Save button
        self.save_button = ttk.Button(self.button_frame, text="Save Settings", command=self.save_all_settings)
        self.save_button.pack(side=tk.RIGHT, padx=5)
    
    def create_general_settings(self):
        """Create general settings section."""
        # Path settings
        paths_frame = ttk.LabelFrame(self.general_frame, text="File Paths", padding=10)
        paths_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Output path
        ttk.Label(paths_frame, text="Output Directory:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.output_path_var = tk.StringVar(value=self.settings.get("output_path", "./output"))
        output_path_entry = ttk.Entry(paths_frame, textvariable=self.output_path_var, width=40)
        output_path_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        output_path_button = ttk.Button(paths_frame, text="Browse...", command=self.browse_output_path)
        output_path_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Person list path
        ttk.Label(paths_frame, text="Person Lists Directory:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.person_list_path_var = tk.StringVar(value=self.settings.get("person_list_path", "./person_lists"))
        person_list_path_entry = ttk.Entry(paths_frame, textvariable=self.person_list_path_var, width=40)
        person_list_path_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        person_list_path_button = ttk.Button(paths_frame, text="Browse...", command=self.browse_person_list_path)
        person_list_path_button.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # General options
        options_frame = ttk.LabelFrame(self.general_frame, text="Options", padding=10)
        options_frame.pack(fill=tk.X)
        
        # Default database
        ttk.Label(options_frame, text="Default Database:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.default_db_var = tk.StringVar(value=self.settings.get("default_database", "PubMed"))
        default_db_combo = ttk.Combobox(options_frame, textvariable=self.default_db_var, width=15)
        default_db_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        default_db_combo['values'] = ["PubMed", "DNB", "Combined"]
        
        # Unique filenames option
        self.unique_filenames_var = tk.BooleanVar(value=self.settings.get("unique_filenames", False))
        unique_filenames_check = ttk.Checkbutton(
            options_frame, 
            text="Generate unique filenames with timestamps", 
            variable=self.unique_filenames_var
        )
        unique_filenames_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
    
    def create_api_keys_settings(self):
        """Create API keys settings section."""
        # API keys frame
        keys_frame = ttk.Frame(self.api_keys_frame, padding=10)
        keys_frame.pack(fill=tk.BOTH, expand=True)
        
        # Info text
        info_text = (
            "Enter your API keys for each database below. API keys are required for "
            "accessing some database features and may increase request limits.\n\n"
            "You can leave fields blank if you don't have an API key for a particular database."
        )
        info_label = ttk.Label(keys_frame, text=info_text, wraplength=500, justify=tk.LEFT)
        info_label.pack(fill=tk.X, pady=(0, 10))
        
        # PubMed API key
        ttk.Label(keys_frame, text="PubMed API Key:").pack(fill=tk.X, anchor=tk.W)
        
        self.pubmed_api_key_var = tk.StringVar(value=self.settings.get("pubmed_api_key", ""))
        pubmed_api_key_entry = ttk.Entry(keys_frame, textvariable=self.pubmed_api_key_var, width=50)
        pubmed_api_key_entry.pack(fill=tk.X, pady=(0, 10))
        
        # DNB API key
        ttk.Label(keys_frame, text="DNB API Key:").pack(fill=tk.X, anchor=tk.W)
        
        self.dnb_api_key_var = tk.StringVar(value=self.settings.get("dnb_api_key", ""))
        dnb_api_key_entry = ttk.Entry(keys_frame, textvariable=self.dnb_api_key_var, width=50)
        dnb_api_key_entry.pack(fill=tk.X, pady=(0, 10))
        
        # API key info
        api_info_frame = ttk.LabelFrame(keys_frame, text="API Key Information", padding=10)
        api_info_frame.pack(fill=tk.X, pady=(10, 0))
        
        api_info_text = (
            "PubMed API Key: To get a PubMed API key, visit https://www.ncbi.nlm.nih.gov/account/ \n"
            "and register for an account. Then go to the 'API Keys' tab under your account settings.\n\n"
            "DNB API Key: The DNB search is currently available without an API key, but usage \n"
            "may be rate-limited. For access with higher rate limits, contact the DNB."
        )
        api_info_label = ttk.Label(api_info_frame, text=api_info_text, justify=tk.LEFT)
        api_info_label.pack(fill=tk.X)
    
    def create_output_settings(self):
        """Create output settings section."""
        # Output options frame
        output_options_frame = ttk.LabelFrame(self.output_frame, text="Output Options", padding=10)
        output_options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Output columns
        ttk.Label(output_options_frame, text="Select columns to include in exports:").pack(anchor=tk.W, pady=(0, 5))
        
        # Create a frame for checkboxes with scrolling capability
        columns_frame = ttk.Frame(output_options_frame)
        columns_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for scrolling
        canvas = tk.Canvas(columns_frame, borderwidth=0)
        scrollbar = ttk.Scrollbar(columns_frame, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        
        # Configure scrolling
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrolling components
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # All available columns
        all_columns = [
            "Database", "Name", "Title", "Publication Year", "Publication Month",
            "Authors", "Publication Types", "Affiliations", "Publisher", "Subjects",
            "Language", "PubMed URL", "DOI URL", "PubMed ID", "PMCID", "DOI", 
            "ISBN", "Identifier", "URL", "Citation Count"
        ]
        
        # Current selected columns
        selected_columns = self.settings.get("output_columns", [
            "Database", "Name", "Title", "Publication Year", "Authors", 
            "Identifier", "URL", "Citation Count"
        ])
        
        # Create column checkboxes
        self.column_vars = {}
        for i, column in enumerate(all_columns):
            var = tk.BooleanVar(value=column in selected_columns)
            self.column_vars[column] = var
            
            checkbox = ttk.Checkbutton(scroll_frame, text=column, variable=var)
            checkbox.grid(row=i // 2, column=i % 2, sticky=tk.W, padx=10, pady=2)
        
        # Select/Deselect all buttons
        select_buttons_frame = ttk.Frame(output_options_frame)
        select_buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(select_buttons_frame, text="Select All", command=self.select_all_columns).pack(side=tk.LEFT, padx=5)
        ttk.Button(select_buttons_frame, text="Deselect All", command=self.deselect_all_columns).pack(side=tk.LEFT, padx=5)
    
    def browse_output_path(self):
        """Browse for output directory."""
        dir_path = filedialog.askdirectory(initialdir=self.output_path_var.get())
        if dir_path:
            self.output_path_var.set(dir_path)
    
    def browse_person_list_path(self):
        """Browse for person list directory."""
        dir_path = filedialog.askdirectory(initialdir=self.person_list_path_var.get())
        if dir_path:
            self.person_list_path_var.set(dir_path)
    
    def select_all_columns(self):
        """Select all output columns."""
        for var in self.column_vars.values():
            var.set(True)
    
    def deselect_all_columns(self):
        """Deselect all output columns."""
        for var in self.column_vars.values():
            var.set(False)
    
    def save_all_settings(self):
        """Save all settings."""
        try:
            # General settings
            self.settings["output_path"] = self.output_path_var.get()
            self.settings["person_list_path"] = self.person_list_path_var.get()
            self.settings["default_database"] = self.default_db_var.get()
            self.settings["unique_filenames"] = self.unique_filenames_var.get()
            
            # API keys
            self.settings["pubmed_api_key"] = self.pubmed_api_key_var.get()
            self.settings["dnb_api_key"] = self.dnb_api_key_var.get()
            
            # Output columns
            selected_columns = [col for col, var in self.column_vars.items() if var.get()]
            
            # Ensure at least some columns are selected
            if not selected_columns:
                messagebox.showwarning("Warning", "Please select at least one output column.")
                return
            
            self.settings["output_columns"] = selected_columns
            
            # Save settings to file
            save_settings(self.settings)
            
            # Ensure directories exist
            ensure_directories(self.settings)
            
            messagebox.showinfo("Settings Saved", "Settings have been saved successfully.")
            
            logger.info("Settings saved")
        
        except Exception as e:
            logger.error(f"Error saving settings: {e}", exc_info=True)
            messagebox.showerror("Error", f"Error saving settings:\n{str(e)}")
