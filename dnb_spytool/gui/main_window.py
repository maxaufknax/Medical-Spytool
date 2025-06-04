"""
Main GUI window for the DNB Spytool application using tkinter.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import webbrowser
from typing import List, Optional, Dict, Any
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import queue
import json

from ..api.database_manager import DatabaseManager, DatabaseType
from ..analytics.analyzer import PublicationAnalyzer
from ..analytics.visualizer import PublicationVisualizer
from ..utils.exporters import DataExporter
from ..utils.validators import InputValidator


class DNBSpytoolGUI:
    """Main GUI application class."""
    
    def __init__(self, root):
        """Initialize the GUI application."""
        self.root = root
        self.root.title("Medical Spytool")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Initialize components
        self.db_manager = DatabaseManager()
        self.validator = InputValidator()
        self.exporter = DataExporter()
        
        # Data storage
        self.current_publications = []
        self.current_analyzer = None
        self.current_visualizer = None
        
        # Threading
        self.search_thread = None
        self.result_queue = queue.Queue()
        
        # Timer management
        self.after_id = None
        self.is_running = True
        
        # Create GUI elements
        self.create_styles()
        self.create_widgets()
        self.setup_bindings()
        
        # Bind close event to cleanup timer
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start result checker
        self.check_results()
    
    def create_styles(self):
        """Create and configure GUI styles."""
        style = ttk.Style()
        
        # Configure notebook tabs
        style.configure('TNotebook.Tab', padding=[12, 8])
        
        # Configure buttons
        style.configure('Search.TButton', font=('Arial', 10, 'bold'))
        style.configure('Export.TButton', font=('Arial', 9))
        
        # Configure labels
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 10, 'italic'))
    
    def create_widgets(self):
        """Create and layout all GUI widgets."""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_search_tab()
        self.create_results_tab()
        self.create_analytics_tab()
        self.create_export_tab()
        self.create_settings_tab()
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_search_tab(self):
        """Create the search tab."""
        search_frame = ttk.Frame(self.notebook)
        self.notebook.add(search_frame, text="Search")
        
        # Title
        title_label = ttk.Label(search_frame, text="Medical Spytool", style='Title.TLabel')
        title_label.pack(pady=(20, 10))
        
        subtitle_label = ttk.Label(search_frame, 
                                 text="Search DNB and PubMed databases for publications by author", 
                                 style='Subtitle.TLabel')
        subtitle_label.pack(pady=(0, 30))
        
        # Main search frame
        main_frame = ttk.Frame(search_frame)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=20)
        
        # Author input section
        author_frame = ttk.LabelFrame(main_frame, text="Author Information", padding=20)
        author_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Single author option
        self.search_mode = tk.StringVar(value="single")
        
        single_radio = ttk.Radiobutton(author_frame, text="Single Author", 
                                     variable=self.search_mode, value="single",
                                     command=self.on_search_mode_change)
        single_radio.pack(anchor=tk.W, pady=(0, 5))
        
        self.single_author_frame = ttk.Frame(author_frame)
        self.single_author_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.single_author_frame, text="Author Name:").pack(anchor=tk.W)
        self.author_entry = ttk.Entry(self.single_author_frame, font=('Arial', 11))
        self.author_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Multiple authors option
        multi_radio = ttk.Radiobutton(author_frame, text="Multiple Authors", 
                                    variable=self.search_mode, value="multiple",
                                    command=self.on_search_mode_change)
        multi_radio.pack(anchor=tk.W, pady=(10, 5))
        
        self.multi_author_frame = ttk.Frame(author_frame)
        self.multi_author_frame.pack(fill=tk.X)
        
        ttk.Label(self.multi_author_frame, text="Author Names (one per line):").pack(anchor=tk.W)
        self.authors_text = scrolledtext.ScrolledText(self.multi_author_frame, height=4, font=('Arial', 10))
        self.authors_text.pack(fill=tk.X, pady=(5, 0))
        
        # Database selection section
        database_frame = ttk.LabelFrame(main_frame, text="Database Selection", padding=20)
        database_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.database_selection = tk.StringVar(value="both")
        
        dnb_radio = ttk.Radiobutton(database_frame, text="DNB (German National Library)", 
                                   variable=self.database_selection, value="dnb")
        dnb_radio.pack(anchor=tk.W, pady=(0, 5))
        
        pubmed_radio = ttk.Radiobutton(database_frame, text="PubMed (NCBI)", 
                                      variable=self.database_selection, value="pubmed")
        pubmed_radio.pack(anchor=tk.W, pady=(0, 5))
        
        both_radio = ttk.Radiobutton(database_frame, text="Both databases (with deduplication)", 
                                    variable=self.database_selection, value="both")
        both_radio.pack(anchor=tk.W)
        
        # Database status
        database_status_frame = ttk.Frame(database_frame)
        database_status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.database_status_label = ttk.Label(database_status_frame, text="", font=('Arial', 9), foreground="green")
        self.database_status_label.pack(anchor=tk.W)
        
        # Update database status
        self.update_database_status()
        
        # Search options
        options_frame = ttk.LabelFrame(main_frame, text="Search Options", padding=20)
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Max results
        max_results_frame = ttk.Frame(options_frame)
        max_results_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(max_results_frame, text="Maximum Results per Author:").pack(side=tk.LEFT)
        self.max_results_var = tk.StringVar(value="100")
        max_results_spinbox = ttk.Spinbox(max_results_frame, from_=1, to=1000, 
                                        textvariable=self.max_results_var, width=10)
        max_results_spinbox.pack(side=tk.RIGHT)
        
        # Date range filter
        self.create_date_filter_section(options_frame)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(options_frame, variable=self.progress_var, 
                                          mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Search button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        self.search_button = ttk.Button(button_frame, text="Search Publications", 
                                      style='Search.TButton', command=self.start_search)
        self.search_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Stop Search", 
                                    command=self.stop_search, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        # Initialize mode
        self.on_search_mode_change()
    
    def create_results_tab(self):
        """Create the results tab."""
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="Results")
        
        # Results header
        header_frame = ttk.Frame(results_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        ttk.Label(header_frame, text="Search Results", style='Title.TLabel').pack(side=tk.LEFT)
        self.results_count_label = ttk.Label(header_frame, text="No results", style='Subtitle.TLabel')
        self.results_count_label.pack(side=tk.RIGHT)
        
        # Results tree
        tree_frame = ttk.Frame(results_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("Title", "Authors", "Year", "Publisher", "Type", "Database")
        self.results_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        self.results_tree.heading("Title", text="Title")
        self.results_tree.heading("Authors", text="Authors")
        self.results_tree.heading("Year", text="Year")
        self.results_tree.heading("Publisher", text="Publisher")
        self.results_tree.heading("Type", text="Type")
        self.results_tree.heading("Database", text="Database")
        
        self.results_tree.column("Title", width=280)
        self.results_tree.column("Authors", width=180)
        self.results_tree.column("Year", width=80)
        self.results_tree.column("Publisher", width=180)
        self.results_tree.column("Type", width=100)
        self.results_tree.column("Database", width=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack tree and scrollbars
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # URL Action buttons frame
        url_frame = ttk.Frame(results_frame)
        url_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        self.open_url_button = ttk.Button(url_frame, text="🔗 Open Publication", 
                                         command=self.open_selected_publication_url,
                                         state=tk.DISABLED)
        self.open_url_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.copy_url_button = ttk.Button(url_frame, text="📋 Copy URL", 
                                         command=self.copy_selected_publication_url,
                                         state=tk.DISABLED)
        self.copy_url_button.pack(side=tk.LEFT)
        
        # Details frame
        details_frame = ttk.LabelFrame(results_frame, text="Publication Details", padding=10)
        details_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.details_text = scrolledtext.ScrolledText(details_frame, height=6, 
                                                    font=('Arial', 9), wrap=tk.WORD)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection and double-click
        self.results_tree.bind('<<TreeviewSelect>>', self.on_result_select)
        self.results_tree.bind('<Double-1>', self.on_publication_double_click)
    
    def create_analytics_tab(self):
        """Create the analytics tab."""
        analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(analytics_frame, text="Analytics")
        
        # Analytics header
        header_frame = ttk.Frame(analytics_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text="Publication Analytics", style='Title.TLabel').pack(side=tk.LEFT)
        
        self.analytics_button = ttk.Button(header_frame, text="Generate Analytics", 
                                         command=self.generate_analytics)
        self.analytics_button.pack(side=tk.RIGHT)
        
        # Create paned window for analytics
        paned = ttk.PanedWindow(analytics_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Left panel - Summary statistics
        left_frame = ttk.LabelFrame(paned, text="Summary Statistics", padding=10)
        paned.add(left_frame, weight=1)
        
        self.stats_text = scrolledtext.ScrolledText(left_frame, font=('Courier', 9), wrap=tk.WORD)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Right panel - Visualization
        right_frame = ttk.LabelFrame(paned, text="Visualization", padding=10)
        paned.add(right_frame, weight=2)
        
        # Chart selection
        chart_frame = ttk.Frame(right_frame)
        chart_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(chart_frame, text="Chart Type:").pack(side=tk.LEFT)
        self.chart_type_var = tk.StringVar(value="timeline")
        chart_combo = ttk.Combobox(chart_frame, textvariable=self.chart_type_var, width=20,
                                 values=["timeline", "authors", "subjects", "types", "collaboration", "database_sources"])
        chart_combo.pack(side=tk.LEFT, padx=(10, 0))
        chart_combo.bind('<<ComboboxSelected>>', self.update_chart)
        
        # Chart canvas frame
        self.chart_frame = ttk.Frame(right_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # Initially empty
        self.canvas = None
        self.current_figure = None
    
    def create_export_tab(self):
        """Create the export tab."""
        export_frame = ttk.Frame(self.notebook)
        self.notebook.add(export_frame, text="Export")
        
        # Export header
        ttk.Label(export_frame, text="Export Data", style='Title.TLabel').pack(pady=(20, 30))
        
        # Main export frame
        main_export_frame = ttk.Frame(export_frame)
        main_export_frame.pack(expand=True, padx=50, pady=20)
        
        # Data export section
        data_frame = ttk.LabelFrame(main_export_frame, text="Data Export", padding=20)
        data_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Format selection
        format_frame = ttk.Frame(data_frame)
        format_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(format_frame, text="Export Format:").pack(side=tk.LEFT)
        self.export_format_var = tk.StringVar(value="csv")
        format_combo = ttk.Combobox(format_frame, textvariable=self.export_format_var, width=15,
                                  values=["csv", "json", "excel"], state="readonly")
        format_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # File selection
        file_frame = ttk.Frame(data_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(file_frame, text="Output File:").pack(anchor=tk.W)
        
        file_entry_frame = ttk.Frame(file_frame)
        file_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.export_file_var = tk.StringVar()
        self.export_file_entry = ttk.Entry(file_entry_frame, textvariable=self.export_file_var)
        self.export_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_button = ttk.Button(file_entry_frame, text="Browse...", command=self.browse_export_file)
        browse_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Export button
        export_data_button = ttk.Button(data_frame, text="Export Data", 
                                      style='Export.TButton', command=self.export_data)
        export_data_button.pack(pady=10)
        
        # Report export section
        report_frame = ttk.LabelFrame(main_export_frame, text="Analytics Report Export", padding=20)
        report_frame.pack(fill=tk.X)
        
        # Report format
        report_format_frame = ttk.Frame(report_frame)
        report_format_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(report_format_frame, text="Report Format:").pack(side=tk.LEFT)
        self.report_format_var = tk.StringVar(value="pdf")
        report_combo = ttk.Combobox(report_format_frame, textvariable=self.report_format_var, width=15,
                                  values=["pdf", "html"], state="readonly")
        report_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Report file selection
        report_file_frame = ttk.Frame(report_frame)
        report_file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(report_file_frame, text="Report File:").pack(anchor=tk.W)
        
        report_entry_frame = ttk.Frame(report_file_frame)
        report_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.report_file_var = tk.StringVar()
        self.report_file_entry = ttk.Entry(report_entry_frame, textvariable=self.report_file_var)
        self.report_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        report_browse_button = ttk.Button(report_entry_frame, text="Browse...", 
                                        command=self.browse_report_file)
        report_browse_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Export report button
        export_report_button = ttk.Button(report_frame, text="Export Report", 
                                        style='Export.TButton', command=self.export_report)
        export_report_button.pack(pady=10)
    
    def create_settings_tab(self):
        """Create the settings tab."""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        ttk.Label(settings_frame, text="Settings", style='Title.TLabel').pack(pady=(20, 30))
        
        # Main settings frame
        main_settings_frame = ttk.Frame(settings_frame)
        main_settings_frame.pack(expand=True, padx=50, pady=20)
        
        # API settings
        api_frame = ttk.LabelFrame(main_settings_frame, text="API Settings", padding=20)
        api_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Timeout setting
        timeout_frame = ttk.Frame(api_frame)
        timeout_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(timeout_frame, text="Request Timeout (seconds):").pack(side=tk.LEFT)
        self.timeout_var = tk.StringVar(value="30")
        timeout_spinbox = ttk.Spinbox(timeout_frame, from_=5, to=120, 
                                    textvariable=self.timeout_var, width=10)
        timeout_spinbox.pack(side=tk.RIGHT)
        
        # Max retries setting
        retries_frame = ttk.Frame(api_frame)
        retries_frame.pack(fill=tk.X)
        
        ttk.Label(retries_frame, text="Maximum Retries:").pack(side=tk.LEFT)
        self.retries_var = tk.StringVar(value="3")
        retries_spinbox = ttk.Spinbox(retries_frame, from_=1, to=10, 
                                    textvariable=self.retries_var, width=10)
        retries_spinbox.pack(side=tk.RIGHT)
        
        # About section
        about_frame = ttk.LabelFrame(main_settings_frame, text="About", padding=20)
        about_frame.pack(fill=tk.X)
        
        about_text = """Medical Spytool v1
        
A comprehensive tool for searching and analyzing publications from multiple medical and academic databases including the German National Library (DNB) and PubMed.

Features:
• Multi-database search (DNB + PubMed)
• Search by author name(s)
• Export data in multiple formats (CSV, JSON, Excel, PDF)
• Generate analytics and visualizations
• Real-time progress tracking
• Cross-platform compatibility

Data Sources: German National Library SRU API & PubMed API
License: MIT License
        """
        
        about_label = ttk.Label(about_frame, text=about_text, justify=tk.LEFT)
        about_label.pack(anchor=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(about_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Visit GitHub", 
                 command=lambda: webbrowser.open("https://github.com/maxaufknax/Medical-Spytool")).pack(side=tk.LEFT)
        
        ttk.Button(button_frame, text="DNB API Documentation", 
                 command=lambda: webbrowser.open("https://www.dnb.de/EN/Professionell/Services/WissenschaftundForschung/SRU/sru_node.html")).pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(button_frame, text="PubMed API Documentation", 
                 command=lambda: webbrowser.open("https://www.ncbi.nlm.nih.gov/books/NBK25501/")).pack(side=tk.LEFT, padx=(10, 0))
    
    def setup_bindings(self):
        """Setup event bindings."""
        self.root.bind('<Control-s>', lambda e: self.export_data())
        self.root.bind('<Control-o>', lambda e: self.browse_export_file())
        self.root.bind('<F5>', lambda e: self.start_search())
        self.root.bind('<Escape>', lambda e: self.stop_search())
        
        # Bind format changes to update file extensions
        self.export_format_var.trace('w', self.on_export_format_change)
        self.report_format_var.trace('w', self.on_report_format_change)
    
    def on_search_mode_change(self):
        """Handle search mode change."""
        if self.search_mode.get() == "single":
            self.single_author_frame.pack(fill=tk.X, pady=(0, 10))
            self.multi_author_frame.pack_forget()
        else:
            self.single_author_frame.pack_forget()
            self.multi_author_frame.pack(fill=tk.X)
    
    def update_database_status(self):
        """Update database availability status."""
        try:
            dnb_available = self.db_manager.is_database_available(DatabaseType.DNB)
            pubmed_available = self.db_manager.is_database_available(DatabaseType.PUBMED)
            
            if dnb_available and pubmed_available:
                status_text = "✓ Both DNB and PubMed are available"
                color = "green"
            elif dnb_available:
                status_text = "✓ DNB available, ⚠ PubMed unavailable"
                color = "orange"
            elif pubmed_available:
                status_text = "⚠ DNB unavailable, ✓ PubMed available"
                color = "orange"
            else:
                status_text = "⚠ Both databases unavailable"
                color = "red"
                
            self.database_status_label.config(text=status_text, foreground=color)
        except Exception as e:
            self.database_status_label.config(text=f"⚠ Error checking database status: {e}", foreground="red")
    
    def on_export_format_change(self, *args):
        """Handle export format change."""
        format_type = self.export_format_var.get()
        current_file = self.export_file_var.get()
        
        if current_file:
            base_name = os.path.splitext(current_file)[0]
            extensions = {'csv': '.csv', 'json': '.json', 'excel': '.xlsx'}
            new_file = base_name + extensions.get(format_type, '.csv')
            self.export_file_var.set(new_file)
    
    def on_report_format_change(self, *args):
        """Handle report format change."""
        format_type = self.report_format_var.get()
        current_file = self.report_file_var.get()
        
        if current_file:
            base_name = os.path.splitext(current_file)[0]
            extensions = {'pdf': '.pdf', 'html': '.html'}
            new_file = base_name + extensions.get(format_type, '.pdf')
            self.report_file_var.set(new_file)
    
    def update_status(self, message: str):
        """Update status bar."""
        self.status_bar.config(text=message)
        self.root.update_idletasks()
    
    def start_search(self):
        """Start the search in a separate thread."""
        # Validate inputs
        if not self.validate_search_inputs():
            return
        
        # Disable search button, enable stop button
        self.search_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Clear previous results
        self.clear_results()
        
        # Start search thread
        self.search_thread = threading.Thread(target=self.perform_search, daemon=True)
        self.search_thread.start()
    
    def validate_search_inputs(self) -> bool:
        """Validate search inputs."""
        if self.search_mode.get() == "single":
            author = self.author_entry.get().strip()
            if not author:
                messagebox.showerror("Validation Error", "Please enter an author name.")
                return False
            
            validation = self.validator.validate_author_name(author)
            if not validation['is_valid']:
                error_msg = "Invalid author name:\n" + self.safe_join(validation['errors'], '\n')
                messagebox.showerror("Validation Error", error_msg)
                return False
        else:
            authors_text = self.authors_text.get("1.0", tk.END).strip()
            if not authors_text:
                messagebox.showerror("Validation Error", "Please enter at least one author name.")
                return False
            
            authors = [line.strip() for line in authors_text.split('\n') if line.strip()]
            validation = self.validator.validate_author_list(authors)
            if not validation['is_valid']:
                error_msg = "Invalid author names:\n" + self.safe_join(validation['errors'], '\n')
                messagebox.showerror("Validation Error", error_msg)
                return False
        
        # Validate date range if enabled
        if self.date_filter_enabled.get():
            if not self.validate_date_range():
                return False
        
        return True
    
    def validate_date_range(self) -> bool:
        """Validate date range inputs."""
        try:
            start_year_str = self.start_year_var.get().strip()
            end_year_str = self.end_year_var.get().strip()
            
            start_year = None
            end_year = None
            
            if start_year_str:
                start_year = int(start_year_str)
                if start_year < 1450 or start_year > 2030:
                    messagebox.showerror("Validation Error", 
                                       "Start year must be between 1450 and 2030.")
                    return False
            
            if end_year_str:
                end_year = int(end_year_str)
                if end_year < 1450 or end_year > 2030:
                    messagebox.showerror("Validation Error", 
                                       "End year must be between 1450 and 2030.")
                    return False
            
            if start_year and end_year and start_year > end_year:
                messagebox.showerror("Validation Error", 
                                   "Start year must be less than or equal to end year.")
                return False
                
            return True
            
        except ValueError:
            messagebox.showerror("Validation Error", 
                               "Please enter valid years (numbers only).")
            return False
    
    def perform_search(self):
        """Perform the actual search (runs in separate thread)."""
        try:
            # Get search parameters
            if self.search_mode.get() == "single":
                authors = [self.author_entry.get().strip()]
            else:
                authors_text = self.authors_text.get("1.0", tk.END).strip()
                authors = [line.strip() for line in authors_text.split('\n') if line.strip()]
            
            max_results = int(self.max_results_var.get())
            
            # Get selected database(s)
            database_selection = self.database_selection.get()
            if database_selection == "dnb":
                databases = [DatabaseType.DNB]
            elif database_selection == "pubmed":
                databases = [DatabaseType.PUBMED]
            else:  # both
                databases = [DatabaseType.DNB, DatabaseType.PUBMED]
            
            # Perform search with detailed progress updates
            database_names = [db.value.upper() for db in databases]
            total_steps = len(authors) * len(databases)
            
            database_names_str = self.safe_join(database_names)
            self.result_queue.put(('status', f"🔍 Starting search across {database_names_str} for {len(authors)} author(s)..."))
            self.result_queue.put(('progress', 10))
            
            # Add timing information
            import time
            start_time = time.time()
            
            self.result_queue.put(('status', f"🌐 Connecting to databases..."))
            self.result_queue.put(('progress', 20))
            
            # Check database availability first
            available_databases = []
            for db in databases:
                try:
                    if self.db_manager.is_database_available(db):
                        available_databases.append(db)
                        self.result_queue.put(('status', f"✅ {db.value.upper()} connection established"))
                    else:
                        self.result_queue.put(('status', f"❌ {db.value.upper()} unavailable"))
                except Exception as e:
                    self.result_queue.put(('status', f"⚠️ Error checking {db.value.upper()}: {str(e)[:50]}..."))
            
            if not available_databases:
                raise Exception("No databases are currently available")
            
            self.result_queue.put(('progress', 40))
            
            # Use DatabaseManager's search_multiple_authors method
            self.result_queue.put(('status', f"📚 Searching publications..."))
            results = self.db_manager.search_multiple_authors(authors, available_databases, max_results)
            
            self.result_queue.put(('progress', 80))
            
            # Apply date range filter if enabled
            if self.date_filter_enabled.get() and results.get('publications'):
                original_count = len(results['publications'])
                start_year = None
                end_year = None
                
                start_year_str = self.start_year_var.get().strip()
                end_year_str = self.end_year_var.get().strip()
                
                if start_year_str:
                    start_year = int(start_year_str)
                if end_year_str:
                    end_year = int(end_year_str)
                
                if start_year or end_year:
                    filtered_publications = self.apply_date_filter(results['publications'], start_year, end_year)
                    results['publications'] = filtered_publications
                    filtered_count = len(filtered_publications)
                    
                    if filtered_count < original_count:
                        self.result_queue.put(('status', f"📅 Date filter applied: {original_count} → {filtered_count} publications"))
            
            self.result_queue.put(('progress', 90))
            
            # Calculate search time
            search_time = time.time() - start_time
            
            # Enhanced results with timing and database info
            if results.get('publications'):
                pub_count = len(results['publications'])
                db_breakdown = {}
                for pub in results['publications']:
                    db_source = pub.get('database_source', 'Unknown')
                    db_breakdown[db_source] = db_breakdown.get(db_source, 0) + 1
                
                status_msg = f"✅ Found {pub_count} publications in {search_time:.2f}s"
                if len(db_breakdown) > 1:
                    breakdown_items = [f"{db}: {count}" for db, count in db_breakdown.items()]
                    breakdown = self.safe_join(breakdown_items)
                    status_msg += f" ({breakdown})"
                
                # Add deduplication info if applicable
                if results.get('deduplication_stats', {}).get('duplicates_removed', 0) > 0:
                    dup_count = results['deduplication_stats']['duplicates_removed']
                    status_msg += f" | {dup_count} duplicates removed"
                
                self.result_queue.put(('status', status_msg))
            else:
                self.result_queue.put(('status', f"❌ No publications found in {search_time:.2f}s"))
            
            self.result_queue.put(('progress', 100))
            
            # Put results in queue
            self.result_queue.put(('results', results))
            
        except Exception as e:
            self.result_queue.put(('error', str(e)))
    
    def stop_search(self):
        """Stop the current search."""
        # Note: This is a simplified stop mechanism
        # In a more sophisticated implementation, you would use threading.Event
        self.search_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Search stopped by user")
    
    def check_results(self):
        """Check for results from the search thread."""
        if not self.is_running:
            return
            
        try:
            while True:
                msg_type, data = self.result_queue.get_nowait()
                
                if msg_type == 'status':
                    self.update_status(data)
                elif msg_type == 'progress':
                    self.progress_var.set(data)
                elif msg_type == 'results':
                    self.handle_search_results(data)
                elif msg_type == 'error':
                    self.handle_search_error(data)
                    
        except queue.Empty:
            pass
        except tk.TclError:
            # Widget has been destroyed, stop the timer
            self.is_running = False
            return
        
        # Schedule next check only if still running
        if self.is_running:
            try:
                self.after_id = self.root.after(100, self.check_results)
            except tk.TclError:
                # GUI has been destroyed
                self.is_running = False
    
    def handle_search_results(self, results):
        """Handle search results with enhanced validation and error handling."""
        try:
            # Reset UI state
            self.search_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.progress_var.set(0)
            
            # Validate results structure
            if not results or not isinstance(results, dict):
                self.update_status("Invalid search results received")
                messagebox.showwarning("Search Error", "Invalid search results received.")
                return
            
            publications = results.get('publications', [])
            
            if publications and isinstance(publications, list) and len(publications) > 0:
                # Filter out any None or invalid publications
                valid_publications = []
                for pub in publications:
                    if pub and isinstance(pub, dict) and pub.get('title'):
                        valid_publications.append(pub)
                
                if not valid_publications:
                    self.update_status("No valid publications found")
                    messagebox.showinfo("Search Results", "No valid publications found in search results.")
                    return
                
                self.current_publications = valid_publications
                
                # Populate results tree with progress indication for large datasets
                if len(valid_publications) > 100:
                    self.update_status(f"Loading {len(valid_publications)} publications...")
                
                self.populate_results_tree()
                
                # Create detailed status message with database breakdown
                total_count = len(self.current_publications)
                status_msg = f"Found {total_count} publications"
                
                # Show database breakdown if available
                database_counts = {}
                for pub in self.current_publications:
                    db_source = str(pub.get('database_source', 'Unknown') or 'Unknown').upper()
                    database_counts[db_source] = database_counts.get(db_source, 0) + 1
                
                if len(database_counts) > 1:
                    breakdown_parts = []
                    for db, count in sorted(database_counts.items()):
                        breakdown_parts.append(f"{db}: {count}")
                    if breakdown_parts:
                        breakdown_str = self.safe_join(breakdown_parts)
                        status_msg += f" ({breakdown_str})"
                        
                    # Show deduplication info if applicable
                    if results.get('deduplication_stats', {}).get('duplicates_removed', 0) > 0:
                        dup_count = results['deduplication_stats']['duplicates_removed']
                        status_msg += f", {dup_count} duplicates removed"
                elif len(database_counts) == 1:
                    # Single database search
                    db_name = list(database_counts.keys())[0]
                    status_msg += f" from {db_name}"
                
                # Add timing information if available
                search_time = results.get('search_time')
                if search_time:
                    status_msg += f" in {search_time:.2f}s"
                
                self.update_status(status_msg)
                
                # Update results count display
                count_text = f"{total_count} publications"
                if len(database_counts) > 1:
                    count_text += f" ({', '.join([f'{db}: {count}' for db, count in sorted(database_counts.items())])})"
                self.results_count_label.config(text=count_text)
                
                # Switch to results tab
                self.notebook.select(1)
                
                # Show success message for large datasets
                if len(valid_publications) > 50:
                    messagebox.showinfo("Search Complete", 
                                      f"Successfully loaded {len(valid_publications)} publications.\n"
                                      f"Use the scrollbar to navigate through all results.")
                
            else:
                self.current_publications = []
                self.results_count_label.config(text="No results")
                
                # Clear results tree
                for item in self.results_tree.get_children():
                    self.results_tree.delete(item)
                
                self.update_status("No publications found")
                messagebox.showinfo("Search Results", "No publications found for the specified author(s).")
                
        except Exception as e:
            error_msg = f"Error handling search results: {str(e)}"
            print(error_msg)
            self.update_status("Error processing search results")
            messagebox.showerror("Search Error", f"An error occurred while processing search results:\n{str(e)}")
    
    def handle_search_error(self, error_msg):
        """Handle search errors."""
        self.search_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_var.set(0)
        
        self.update_status("Search failed")
        messagebox.showerror("Search Error", f"An error occurred during search:\n{error_msg}")
    
    def clear_results(self):
        """Clear previous results."""
        self.current_publications = []
        self.current_analyzer = None
        self.current_visualizer = None
        
        # Clear results tree
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.results_count_label.config(text="No results")
        self.details_text.delete(1.0, tk.END)
        
        # Clear analytics
        self.stats_text.delete(1.0, tk.END)
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
    
    def populate_results_tree(self):
        """Populate the results tree with publications."""
        try:
            # Clear existing items
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            # Check if we have publications
            if not self.current_publications:
                self.results_count_label.config(text="No results")
                return
            
            # Add publications with progress for large datasets
            total_pubs = len(self.current_publications)
            for i, pub in enumerate(self.current_publications):
                # Handle potential None values and different data structures
                title = str(pub.get('title', 'No title') or 'No title')[:100]
                
                # Handle authors - can be list or string
                authors_raw = pub.get('author', []) or pub.get('authors', []) or []
                authors = self.safe_join(authors_raw)[:50]
                
                year = str(pub.get('publication_year', '') or pub.get('year', '') or '')
                publisher = str(pub.get('publisher', '') or '')[:50]
                pub_type = str(pub.get('type', '') or pub.get('publication_type', '') or '')
                database_source = str(pub.get('database_source', 'Unknown') or 'Unknown').upper()
                
                # Insert into tree with error handling
                try:
                    self.results_tree.insert('', 'end', values=(title, authors, year, publisher, pub_type, database_source))
                except Exception as e:
                    print(f"Warning: Could not insert publication {i+1}: {e}")
                    continue
                
                # Update progress for large datasets (every 50 items)
                if total_pubs > 100 and i % 50 == 0:
                    self.update_status(f"Loading results... {i+1}/{total_pubs}")
                    self.root.update_idletasks()
            
            # Enhanced results count with database breakdown
            database_counts = {}
            for pub in self.current_publications:
                db_source = str(pub.get('database_source', 'Unknown') or 'Unknown').upper()
                database_counts[db_source] = database_counts.get(db_source, 0) + 1
            
            count_text = f"{len(self.current_publications)} publications"
            if len(database_counts) > 1:
                breakdown_items = [f"{db}: {count}" for db, count in sorted(database_counts.items())]
                breakdown = self.safe_join(breakdown_items)
                count_text += f" ({breakdown})"
            
            self.results_count_label.config(text=count_text)
            
            # Ensure scrollbars are updated
            self.results_tree.update_idletasks()
            
            # Auto-scroll to top
            if self.results_tree.get_children():
                self.results_tree.selection_set(self.results_tree.get_children()[0])
                self.results_tree.focus(self.results_tree.get_children()[0])
                
        except Exception as e:
            error_msg = f"Error populating results tree: {str(e)}"
            print(error_msg)
            self.results_count_label.config(text="Error loading results")
            self.update_status("Error loading results")
    
    def on_result_select(self, event):
        """Handle result selection in tree."""
        selection = self.results_tree.selection()
        if not selection:
            # Disable URL buttons when no selection
            self.open_url_button.config(state=tk.DISABLED)
            self.copy_url_button.config(state=tk.DISABLED)
            return
        
        # Get selected index
        item = selection[0]
        index = self.results_tree.index(item)
        
        if 0 <= index < len(self.current_publications):
            pub = self.current_publications[index]
            self.show_publication_details(pub)
            
            # Enable URL buttons if publication has URLs
            has_urls = self._publication_has_urls(pub)
            state = tk.NORMAL if has_urls else tk.DISABLED
            self.open_url_button.config(state=state)
            self.copy_url_button.config(state=state)
        else:
            self.open_url_button.config(state=tk.DISABLED)
            self.copy_url_button.config(state=tk.DISABLED)
    
    def on_publication_double_click(self, event):
        """Handle double-click on publication to open URL."""
        selection = self.results_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        index = self.results_tree.index(item)
        
        if 0 <= index < len(self.current_publications):
            pub = self.current_publications[index]
            self._open_publication_url(pub)
    
    def open_selected_publication_url(self):
        """Open URL for currently selected publication."""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a publication first.")
            return
        
        item = selection[0]
        index = self.results_tree.index(item)
        
        if 0 <= index < len(self.current_publications):
            pub = self.current_publications[index]
            self._open_publication_url(pub)
    
    def copy_selected_publication_url(self):
        """Copy URL of currently selected publication to clipboard."""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a publication first.")
            return
        
        item = selection[0]
        index = self.results_tree.index(item)
        
        if 0 <= index < len(self.current_publications):
            pub = self.current_publications[index]
            urls = self._get_publication_urls(pub)
            
            if not urls:
                messagebox.showinfo("No URLs", "No URLs available for this publication.")
                return
            
            # If multiple URLs, let user choose
            if len(urls) > 1:
                selected = self._select_url_dialog(urls)
                if not selected:
                    return
                url = selected[1]  # Get URL from tuple
                label = selected[0]  # Get label from tuple
            else:
                label, url = urls[0]  # Unpack tuple
            
            # Copy to clipboard
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(url)
                self.root.update()  # Ensure clipboard is updated
                messagebox.showinfo("URL Copied", f"{label} copied to clipboard:\n{url}")
            except Exception as e:
                messagebox.showerror("Copy Error", f"Failed to copy URL to clipboard:\n{str(e)}")
    
    def _get_publication_urls(self, publication: Dict) -> List[tuple]:
        """Extract all available URLs from a publication with labels."""
        urls = []
        
        try:
            # Enhanced URL extraction with priority order and labels
            url_mapping = [
                ('doi', 'DOI Link'),
                ('dnb_direct', 'DNB Direct Link'),
                ('dnb_record', 'DNB Record'),
                ('springer', 'Springer Link'),
                ('sciencedirect', 'ScienceDirect'),
                ('worldcat', 'WorldCat'),
                ('google_books', 'Google Books'),
                ('pmid', 'PubMed'),
                ('pmc', 'PMC'),
                ('url', 'Primary URL'),
                ('issn_portal', 'ISSN Portal')
            ]
            
            # Process URLs in priority order
            for field_name, label in url_mapping:
                if publication.get(field_name):
                    url = publication[field_name]
                    
                    # Handle special cases for URL formatting
                    if field_name == 'doi' and not url.startswith('http'):
                        url = f"https://doi.org/{url}"
                    elif field_name == 'pmid' and not url.startswith('http'):
                        url = f"https://pubmed.ncbi.nlm.nih.gov/{url}/"
                    elif field_name == 'pmc' and not url.startswith('http'):
                        url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{url}/"
                    
                    # Avoid duplicates
                    if url not in [u[1] for u in urls]:
                        urls.append((label, url))
            
            # Fallback: check all_urls field for any missed URLs
            all_urls = publication.get('all_urls', {})
            if all_urls and isinstance(all_urls, dict):
                for url_type, url in all_urls.items():
                    if url and url not in [u[1] for u in urls]:
                        label = url_type.replace('_', ' ').title()
                        urls.append((label, url))
            
        except Exception as e:
            print(f"Error extracting URLs: {e}")
        
        return urls
    
    def _select_url_dialog(self, urls: List[tuple]) -> Optional[tuple]:
        """Allow user to select from multiple URLs."""
        try:
            import tkinter.simpledialog as simpledialog
            
            # Create a simple selection dialog
            choice_text = "Multiple URLs available. Select one:\n\n"
            for i, (label, url) in enumerate(urls, 1):
                # Truncate long URLs for display
                display_url = url[:60] + "..." if len(url) > 60 else url
                choice_text += f"{i}. {label}: {display_url}\n"
            
            choice_text += f"\nEnter number (1-{len(urls)}):"
            
            selection = simpledialog.askstring(
                "Select URL", 
                choice_text
            )
            
            if selection and selection.isdigit():
                index = int(selection) - 1
                if 0 <= index < len(urls):
                    return urls[index]
            
        except Exception as e:
            print(f"Error in URL selection dialog: {e}")
        
        return None
    
    def safe_join(self, items, separator=', '):
        """Safely join items with error handling for non-iterable items."""
        try:
            if items is None:
                return ""
            if isinstance(items, str):
                return items
            if hasattr(items, '__iter__'):
                return separator.join([str(item) for item in items if item])
            else:
                return str(items)
        except (TypeError, AttributeError):
            return str(items) if items else ""
    
    def show_publication_details(self, publication: Dict):
        """Display comprehensive detailed information about a selected publication with enhanced schema support."""
        try:
            if not self.details_text:
                return
                
            # Clear previous content
            self.details_text.delete('1.0', tk.END)
            
            # Format publication details with enhanced schema
            details = []
            
            # === BASIC INFORMATION ===
            details.append("=== PUBLICATION DETAILS ===\n\n")
            
            # Title (required field)
            title = publication.get('title', 'No title available')
            details.append(f"Title: {title}\n\n")
            
            # Authors (required field - use consistent field name)
            authors = publication.get('authors', [])
            authors_str = self.safe_join(authors)
            details.append(f"Authors: {authors_str}\n")
            
            # Publication Year (required field)
            year = publication.get('publication_year', '')
            details.append(f"Publication Year: {year}\n")
            
            # Database Source (required field)
            db_source = publication.get('database_source', 'Unknown')
            details.append(f"Database Source: {db_source.upper()}\n\n")
            
            # === PUBLICATION METADATA ===
            
            # Journal (enhanced field)
            journal = publication.get('journal', '')
            if journal:
                details.append(f"Journal: {journal}\n")
            
            # Publisher
            publisher = publication.get('publisher', '')
            if publisher:
                details.append(f"Publisher: {publisher}\n")
            
            # Publication Type (use consistent field name)
            pub_type = publication.get('publication_type', '')
            if pub_type:
                details.append(f"Publication Type: {pub_type}\n")
            
            # Language
            language = publication.get('language', '')
            if language:
                details.append(f"Language: {language}\n")
            
            # Physical Description (new enhanced field)
            physical_desc = publication.get('physical_description', '')
            if physical_desc:
                details.append(f"Physical Description: {physical_desc}\n")
            
            # Series (new enhanced field)
            series = publication.get('series', '')
            if series:
                details.append(f"Series: {series}\n")
            
            # === IDENTIFIERS & LINKS ===
            details.append("\n=== IDENTIFIERS & LINKS ===\n")
            
            # Record ID (new enhanced field)
            record_id = publication.get('id', '')
            if record_id:
                details.append(f"Record ID: {record_id}\n")
            
            # ISBN/ISSN
            identifiers = []
            if publication.get('isbn'):
                isbn_val = publication['isbn']
                isbn_str = self.safe_join(isbn_val) if isinstance(isbn_val, list) else str(isbn_val)
                identifiers.append(f"ISBN: {isbn_str}")
            if publication.get('issn'):
                issn_val = publication['issn'] 
                issn_str = self.safe_join(issn_val) if isinstance(issn_val, list) else str(issn_val)
                identifiers.append(f"ISSN: {issn_str}")
            
            if identifiers:
                details.append("\n".join(identifiers) + "\n")
            
            # Enhanced URL Display
            urls = []
            
            # Primary URL
            primary_url = publication.get('primary_url', '') or publication.get('url', '')
            if primary_url:
                urls.append(f"Primary URL: {primary_url}")
            
            # DOI with link
            doi = publication.get('doi', '')
            if doi:
                urls.append(f"DOI: https://doi.org/{doi}")
            
            # PubMed with link
            pmid = publication.get('pmid', '')
            if pmid:
                urls.append(f"PubMed: https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
            
            # PMC with link (new enhanced field)
            pmc = publication.get('pmc', '')
            if pmc:
                urls.append(f"PMC: https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/")
            
            # All URLs (enhanced URL collection)
            all_urls = publication.get('all_urls', {})
            if isinstance(all_urls, dict) and all_urls:
                for url_type, url_value in all_urls.items():
                    if url_value and url_type not in ['primary_url', 'doi', 'pmid', 'pmc']:
                        urls.append(f"{url_type.title()}: {url_value}")
            
            if urls:
                details.append(f"\nLinks:\n" + "\n".join(urls) + "\n")
            
            # === CONTENT ===
            details.append("\n=== CONTENT ===\n")
            
            # Abstract
            abstract = publication.get('abstract', '')
            if abstract:
                # Truncate very long abstracts for display
                if len(abstract) > 1000:
                    abstract = abstract[:1000] + "...\n[Abstract truncated for display]"
                details.append(f"Abstract:\n{abstract}\n\n")
            
            # Description (new enhanced field from MARC 520)
            description = publication.get('description', '')
            if description and description != abstract:  # Avoid duplication
                if len(description) > 500:
                    description = description[:500] + "...\n[Description truncated for display]"
                details.append(f"Description:\n{description}\n\n")
            
            # Subject Headings (use consistent field name)
            subjects = publication.get('subject_headings', [])
            if subjects:
                subjects_str = self.safe_join(subjects)
                details.append(f"Subject Headings: {subjects_str}\n\n")
            
            # Notes (new enhanced field)
            notes = publication.get('notes', '')
            if notes:
                if len(notes) > 300:
                    notes = notes[:300] + "...\n[Notes truncated for display]"
                details.append(f"Notes:\n{notes}\n")
            
            # === METADATA SUMMARY ===
            details.append("\n=== METADATA SUMMARY ===\n")
            
            # Count available fields
            available_fields = [k for k, v in publication.items() if v]
            details.append(f"Available Data Fields: {len(available_fields)}\n")
            
            # Enhanced features indicator
            enhanced_features = []
            if publication.get('all_urls'):
                enhanced_features.append("Enhanced URLs")
            if publication.get('pmc'):
                enhanced_features.append("PMC ID")
            if publication.get('physical_description'):
                enhanced_features.append("Physical Description")
            if publication.get('series'):
                enhanced_features.append("Series Info")
            if publication.get('notes'):
                enhanced_features.append("Additional Notes")
            
            if enhanced_features:
                details.append(f"Enhanced Features: {', '.join(enhanced_features)}\n")
            
            # Insert all details
            self.details_text.insert('1.0', ''.join(details))
            
        except Exception as e:
            error_text = f"Error displaying publication details: {str(e)}\n\nDebug Info:\nAvailable fields: {list(publication.keys()) if publication else 'No publication data'}"
            self.details_text.delete('1.0', tk.END)
            self.details_text.insert('1.0', error_text)
    
    def _publication_has_urls(self, publication: Dict) -> bool:
        """Check if publication has any accessible URLs."""
        try:
            urls = self._get_publication_urls(publication)
            return len(urls) > 0
        except (AttributeError, TypeError):
            return False
    
    def _open_publication_url(self, publication: Dict):
        """Open the most appropriate URL for a publication."""
        try:
            urls = self._get_publication_urls(publication)
            
            if not urls:
                messagebox.showinfo("No URL", "No accessible URL found for this publication.")
                return
            
            # If multiple URLs, let user choose, otherwise use the first (highest priority)
            if len(urls) > 1:
                selected = self._select_url_dialog(urls)
                if not selected:
                    return
                label, url = selected
            else:
                label, url = urls[0]
            
            # Open the URL
            import webbrowser
            webbrowser.open(url)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open URL: {str(e)}")

    def generate_analytics(self):
        """Generate analytics for current publications."""
        if not self.current_publications:
            messagebox.showwarning("No Data", "Please perform a search first to generate analytics.")
            return
        
        try:
            self.update_status("Generating analytics...")
            
            # Validate and clean publication data before analysis
            valid_publications = []
            for pub in self.current_publications:
                if pub is not None and isinstance(pub, dict):
                    valid_publications.append(pub)
            
            if not valid_publications:
                messagebox.showwarning("No Valid Data", "No valid publication data found for analytics.")
                return
            
            # Create analyzer and visualizer with error handling
            try:
                self.current_analyzer = PublicationAnalyzer(valid_publications)
                self.current_visualizer = PublicationVisualizer(self.current_analyzer)
            except Exception as e:
                messagebox.showerror("Analytics Error", f"Failed to initialize analytics engine:\n{str(e)}")
                self.update_status("Analytics initialization failed")
                return
            
            # Generate summary statistics with error handling
            try:
                summary = self.current_analyzer.generate_summary_report()
                self.stats_text.delete(1.0, tk.END)
                self.stats_text.insert(1.0, summary)
            except Exception as e:
                summary = f"Error generating summary report: {str(e)}\n\nBasic Info:\n- Total Publications: {len(valid_publications)}"
                self.stats_text.delete(1.0, tk.END)
                self.stats_text.insert(1.0, summary)
                print(f"Warning: Summary generation failed: {e}")
            
            # Generate initial chart with error handling
            try:
                self.update_chart()
            except Exception as e:
                print(f"Warning: Chart generation failed: {e}")
                # Continue without chart
            
            self.update_status("Analytics generated successfully")
            
        except Exception as e:
            error_msg = f"Failed to generate analytics: {str(e)}"
            print(error_msg)
            messagebox.showerror("Analytics Error", error_msg)
            self.update_status("Analytics generation failed")
    
    def update_chart(self, event=None):
        """Update the current chart."""
        if not self.current_visualizer:
            return
        
        try:
            # Clear previous chart
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
                self.canvas = None
            
            if self.current_figure:
                plt.close(self.current_figure)
            
            # Generate new chart
            chart_type = self.chart_type_var.get()
            
            if chart_type == "timeline":
                self.current_figure = self.current_visualizer.create_publication_timeline()
            elif chart_type == "authors":
                self.current_figure = self.current_visualizer.create_author_productivity_chart()
            elif chart_type == "subjects":
                self.current_figure = self.current_visualizer.create_subject_wordcloud_chart()
            elif chart_type == "types":
                self.current_figure = self.current_visualizer.create_publication_type_pie_chart()
            elif chart_type == "collaboration":
                self.current_figure = self.current_visualizer.create_collaboration_analysis()
            elif chart_type == "database_sources":
                self.current_figure = self.current_visualizer.create_database_source_chart()
            
            # Embed chart in tkinter
            if self.current_figure:
                self.canvas = FigureCanvasTkAgg(self.current_figure, master=self.chart_frame)
                self.canvas.draw()
                self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            messagebox.showerror("Chart Error", f"Failed to generate chart:\n{str(e)}")
    
    def browse_export_file(self):
        """Browse for export file."""
        format_type = self.export_format_var.get()
        extensions = {
            'csv': [('CSV files', '*.csv'), ('All files', '*.*')],
            'json': [('JSON files', '*.json'), ('All files', '*.*')],
            'excel': [('Excel files', '*.xlsx'), ('All files', '*.*')]
        }
        
        filetypes = extensions.get(format_type, [('All files', '*.*')])
        
        filename = filedialog.asksaveasfilename(
            title="Save Export File",
            filetypes=filetypes,
            defaultextension=f".{format_type}"
        )
        
        if filename:
            self.export_file_var.set(filename)
    
    def browse_report_file(self):
        """Browse for report file."""
        format_type = self.report_format_var.get()
        extensions = {
            'pdf': [('PDF files', '*.pdf'), ('All files', '*.*')],
            'html': [('HTML files', '*.html'), ('All files', '*.*')]
        }
        
        filetypes = extensions.get(format_type, [('All files', '*.*')])
        
        filename = filedialog.asksaveasfilename(
            title="Save Report File",
            filetypes=filetypes,
            defaultextension=f".{format_type}"
        )
        
        if filename:
            self.report_file_var.set(filename)
    
    def export_data(self):
        """Export publication data."""
        if not self.current_publications:
            messagebox.showwarning("No Data", "Please perform a search first to export data.")
            return
        
        export_file = self.export_file_var.get().strip()
        if not export_file:
            messagebox.showerror("Export Error", "Please specify an output file.")
            return
        
        try:
            format_type = self.export_format_var.get()
            success = self.exporter.export_publications(
                self.current_publications, format_type, export_file
            )
            
            if success:
                messagebox.showinfo("Export Success", f"Data exported successfully to:\n{export_file}")
                self.update_status(f"Data exported to {export_file}")
            else:
                messagebox.showerror("Export Error", "Failed to export data.")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Export failed:\n{str(e)}")
    
    def export_report(self):
        """Export analytics report."""
        if not self.current_analyzer:
            messagebox.showwarning("No Analytics", "Please generate analytics first.")
            return
        
        report_file = self.report_file_var.get().strip()
        if not report_file:
            messagebox.showerror("Export Error", "Please specify a report file.")
            return
        
        try:
            format_type = self.report_format_var.get()
            success = self.exporter.export_analysis_report(
                self.current_analyzer, self.current_visualizer, report_file, format_type
            )
            
            if success:
                messagebox.showinfo("Export Success", f"Report exported successfully to:\n{report_file}")
                self.update_status(f"Report exported to {report_file}")
                
                # Also export charts
                base_path = os.path.splitext(report_file)[0]
                charts_dir = f"{base_path}_charts"
                if self.current_visualizer:
                    chart_files = self.current_visualizer.save_all_charts(charts_dir)
                    if chart_files:
                        messagebox.showinfo("Charts Exported", 
                                          f"Charts also saved to:\n{charts_dir}")
            else:
                messagebox.showerror("Export Error", "Failed to export report.")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Report export failed:\n{str(e)}")
    
    def on_closing(self):
        """Handle application closing with proper cleanup."""
        # Stop the timer loop
        self.is_running = False
        
        # Cancel any pending after calls
        if self.after_id:
            try:
                self.root.after_cancel(self.after_id)
            except tk.TclError:
                pass  # Already cancelled or window destroyed
        
        # Stop any running search threads
        if self.search_thread and self.search_thread.is_alive():
            # Note: In a more sophisticated implementation, you would use threading.Event
            pass
        
        # Destroy the window
        self.root.destroy()
    
    def create_date_filter_section(self, parent_frame):
        """Create the date range filter section."""
        # Date filter frame
        date_filter_frame = ttk.Frame(parent_frame)
        date_filter_frame.pack(fill=tk.X, pady=(10, 10))
        
        # Checkbox to enable/disable date filter
        self.date_filter_enabled = tk.BooleanVar(value=False)
        date_checkbox = ttk.Checkbutton(date_filter_frame, 
                                       text="Enable Date Range Filter",
                                       variable=self.date_filter_enabled,
                                       command=self.on_date_filter_toggle)
        date_checkbox.pack(anchor=tk.W, pady=(0, 5))
        
        # Date inputs frame
        self.date_inputs_frame = ttk.Frame(date_filter_frame)
        self.date_inputs_frame.pack(fill=tk.X, padx=(20, 0))
        
        # Start year
        start_year_frame = ttk.Frame(self.date_inputs_frame)
        start_year_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(start_year_frame, text="Start Year:").pack(anchor=tk.W)
        self.start_year_var = tk.StringVar()
        self.start_year_spinbox = ttk.Spinbox(start_year_frame, from_=1450, to=2030,
                                             textvariable=self.start_year_var, width=8,
                                             state=tk.DISABLED)
        self.start_year_spinbox.pack(anchor=tk.W, pady=(2, 0))
        
        # End year  
        end_year_frame = ttk.Frame(self.date_inputs_frame)
        end_year_frame.pack(side=tk.LEFT)
        
        ttk.Label(end_year_frame, text="End Year:").pack(anchor=tk.W)
        self.end_year_var = tk.StringVar()
        self.end_year_spinbox = ttk.Spinbox(end_year_frame, from_=1450, to=2030,
                                           textvariable=self.end_year_var, width=8,
                                           state=tk.DISABLED)
        self.end_year_spinbox.pack(anchor=tk.W, pady=(2, 0))
        
        # Set default values
        current_year = 2025  # Based on current date
        self.start_year_var.set(str(current_year - 10))  # Default: last 10 years
        self.end_year_var.set(str(current_year))
        
        # Initially disable the date inputs
        self.on_date_filter_toggle()
    
    def on_date_filter_toggle(self):
        """Handle toggling of the date filter checkbox."""
        if self.date_filter_enabled.get():
            # Enable date inputs
            self.start_year_spinbox.config(state=tk.NORMAL)
            self.end_year_spinbox.config(state=tk.NORMAL)
        else:
            # Disable date inputs
            self.start_year_spinbox.config(state=tk.DISABLED)
            self.end_year_spinbox.config(state=tk.DISABLED)
    
    def apply_date_filter(self, publications: List[Dict], start_year: Optional[int], end_year: Optional[int]) -> List[Dict]:
        """Apply date range filter to publications."""
        if not start_year and not end_year:
            return publications
        
        filtered_publications = []
        
        for pub in publications:
            pub_year = self.extract_publication_year(pub)
            
            if pub_year is None:
                # If no year can be extracted, include it (let user decide)
                filtered_publications.append(pub)
                continue
            
            # Apply filters
            if start_year and pub_year < start_year:
                continue
            if end_year and pub_year > end_year:
                continue
                
            filtered_publications.append(pub)
        
        return filtered_publications
    
    def extract_publication_year(self, publication: Dict) -> Optional[int]:
        """Extract publication year from a publication record."""
        # Try multiple fields that might contain year information
        year_fields = ['publication_year', 'year', 'date', 'pub_date']
        
        for field in year_fields:
            if field in publication and publication[field]:
                year_value = publication[field]
                
                # Handle different year formats
                if isinstance(year_value, int):
                    return year_value
                elif isinstance(year_value, str):
                    # Try to extract 4-digit year from string
                    import re
                    year_match = re.search(r'\b(19|20)\d{2}\b', year_value)
                    if year_match:
                        return int(year_match.group())
        
        return None


def main():
    """Main function to run the GUI application."""
    try:
        root = tk.Tk()
        app = DNBSpytoolGUI(root)
        root.mainloop()
    except ImportError as e:
        print(f"Missing required dependency: {e}")
        print("Please install all requirements: pip install -r requirements.txt")
    except Exception as e:
        print(f"Error starting GUI: {e}")


if __name__ == '__main__':
    main()
