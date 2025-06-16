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
from ..core.search_manager import EnhancedSearchManager
from ..core.cache_manager import QueryCacheManager
from ..utils.result_processor import EnhancedResultProcessor
from .enhanced_components import RealTimeProgressDialog, show_enhanced_error


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
        
        # Initialize enhanced components
        self.cache_manager = QueryCacheManager()
        self.search_manager = EnhancedSearchManager(self.cache_manager)
        self.result_processor = EnhancedResultProcessor()
        
        # Setup callbacks for enhanced search manager
        self.search_manager.add_progress_callback(self.on_search_progress)
        self.search_manager.add_result_callback(self.on_search_results)
        self.search_manager.add_error_callback(self.on_search_error)
        
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
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 10))
        style.configure('Search.TButton', background='#007acc')

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
            self.progress_var.set(100)
            
            # Validate results structure
            if not isinstance(results, dict):
                self.handle_search_error("Invalid results format received")
                return
            
            publications = results.get('publications', [])
            if not isinstance(publications, list):
                self.handle_search_error("Invalid publications data received")
                return
            
            # Store current publications
            self.current_publications = publications
            
            # Update results count
            self.results_count_label.config(text=f"{len(publications)} results")
            
            # Populate results tree
            self.populate_results_tree(publications)
            
            # Update status with detailed info
            if publications:
                # Get database breakdown
                db_breakdown = {}
                for pub in publications:
                    source = pub.get('source', 'Unknown')
                    db_breakdown[source] = db_breakdown.get(source, 0) + 1
                
                status_parts = [f"Found {len(publications)} publications"]
                if len(db_breakdown) > 1:
                    breakdown_str = ", ".join([f"{k}: {v}" for k, v in db_breakdown.items()])
                    status_parts.append(f"({breakdown_str})")
                
                # Add deduplication info if available
                dedup_stats = results.get('deduplication_stats', {})
                if dedup_stats.get('duplicates_removed', 0) > 0:
                    status_parts.append(f"({dedup_stats['duplicates_removed']} duplicates removed)")
                
                self.update_status(" ".join(status_parts))
            else:
                self.update_status("No publications found")
                
            # Switch to results tab
            self.notebook.select(1)  # Results tab
            
        except Exception as e:
            self.handle_search_error(f"Error processing results: {str(e)}")

    def handle_search_error(self, error_message):
        """Handle search errors with user-friendly messages."""
        try:
            # Reset UI state
            self.search_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.progress_var.set(0)
            
            # Show error message
            self.update_status(f"Search failed: {error_message}")
            messagebox.showerror("Search Error", f"Search failed:\n\n{error_message}")
            
        except Exception as e:
            print(f"Error handling search error: {e}")

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
        """Create the enhanced results tab with v1.4 column management."""
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="Results")
        
        # Results header with enhanced controls
        header_frame = ttk.Frame(results_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        ttk.Label(header_frame, text="Search Results", style='Title.TLabel').pack(side=tk.LEFT)
        
        # Column view selector
        view_frame = ttk.Frame(header_frame)
        view_frame.pack(side=tk.LEFT, padx=(20, 0))
        
        ttk.Label(view_frame, text="View:").pack(side=tk.LEFT)
        self.column_view_var = tk.StringVar(value="standard")
        view_combo = ttk.Combobox(view_frame, textvariable=self.column_view_var, width=12,
                                 values=["standard", "extended", "pubmed", "dnb", "all"], state="readonly")
        view_combo.pack(side=tk.LEFT, padx=(5, 0))
        view_combo.bind('<<ComboboxSelected>>', self.on_column_view_change)
        
        self.results_count_label = ttk.Label(header_frame, text="No results", style='Subtitle.TLabel')
        self.results_count_label.pack(side=tk.RIGHT)
        
        # Results tree with dynamic column configuration
        tree_frame = ttk.Frame(results_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Initialize with standard columns
        self.setup_results_tree(tree_frame)
        
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
        
        # Column visibility controls
        column_controls_frame = ttk.Frame(url_frame)
        column_controls_frame.pack(side=tk.RIGHT)
        
        ttk.Button(column_controls_frame, text="📊 Customize Columns", 
                  command=self.show_column_customization).pack(side=tk.LEFT, padx=(10, 0))
        
        # Details frame
        details_frame = ttk.LabelFrame(results_frame, text="Publication Details", padding=10)
        details_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.details_text = scrolledtext.ScrolledText(details_frame, height=6, 
                                                    font=('Arial', 9), wrap=tk.WORD)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection and double-click
        self.setup_results_tree_events()
    
    def setup_results_tree(self, parent_frame):
        """Setup the results tree with configurable columns."""
        # Define all available columns with metadata
        self.all_columns = {
            # Standard columns
            'Title': {'width': 250, 'category': 'standard'},
            'Authors': {'width': 150, 'category': 'standard'},
            'Year': {'width': 60, 'category': 'standard'},
            'Database': {'width': 70, 'category': 'standard'},
            'Primary URL': {'width': 120, 'category': 'standard'},
            
            # Extended basic columns
            'Publisher': {'width': 140, 'category': 'extended'},
            'Publication Type': {'width': 120, 'category': 'extended'},
            'DOI': {'width': 100, 'category': 'extended'},
            'ISBN/ISSN': {'width': 100, 'category': 'extended'},
            'Language': {'width': 80, 'category': 'extended'},
            
            # PubMed specific columns
            'Journal': {'width': 150, 'category': 'pubmed'},
            'PMID': {'width': 80, 'category': 'pubmed'},
            'PMC': {'width': 80, 'category': 'pubmed'},
            'MeSH Terms': {'width': 200, 'category': 'pubmed'},
            'Publication Types': {'width': 120, 'category': 'pubmed'},
            'Funding': {'width': 150, 'category': 'pubmed'},
            'Institution': {'width': 150, 'category': 'pubmed'},
            'Country': {'width': 100, 'category': 'pubmed'},
            'Journal Category': {'width': 120, 'category': 'pubmed'},
            'Abstract Word Count': {'width': 80, 'category': 'pubmed'},
            'Is Review': {'width': 60, 'category': 'pubmed'},
            'Is Clinical Trial': {'width': 80, 'category': 'pubmed'},
            'Free Full Text': {'width': 80, 'category': 'pubmed'},
            
            # DNB specific columns
            'DNB Classification': {'width': 120, 'category': 'dnb'},
            'Document Type': {'width': 100, 'category': 'dnb'},
            'Thesis Type': {'width': 100, 'category': 'dnb'},
            'University': {'width': 150, 'category': 'dnb'},
            'Supervisor': {'width': 120, 'category': 'dnb'},
            'Academic Degree': {'width': 100, 'category': 'dnb'},
            'Series Title': {'width': 150, 'category': 'dnb'},
            'Physical Description': {'width': 120, 'category': 'dnb'},
            'Availability': {'width': 100, 'category': 'dnb'},
            'Place of Publication': {'width': 120, 'category': 'dnb'},
            'DNB ID': {'width': 100, 'category': 'dnb'},
            'GND Terms': {'width': 150, 'category': 'dnb'},
            
            # All view additional columns
            'Abstract': {'width': 300, 'category': 'all'},
            'Keywords': {'width': 200, 'category': 'all'},
            'Notes': {'width': 200, 'category': 'all'},
            'Raw Data': {'width': 100, 'category': 'all'},
        }
        
        # Column view configurations
        self.column_views = {
            'standard': ['Title', 'Authors', 'Year', 'Database', 'Primary URL'],
            'extended': ['Title', 'Authors', 'Year', 'Publisher', 'Publication Type', 'DOI', 'ISBN/ISSN', 'Language', 'Database', 'Primary URL'],
            'pubmed': ['Title', 'Authors', 'Year', 'Journal', 'PMID', 'MeSH Terms', 'Publication Types', 'Institution', 'Country', 'Journal Category', 'Funding', 'Primary URL'],
            'dnb': ['Title', 'Authors', 'Year', 'Document Type', 'University', 'DNB Classification', 'Thesis Type', 'Supervisor', 'Academic Degree', 'Availability', 'Primary URL'],
            'all': list(self.all_columns.keys())
        }
        
        # Get current view columns
        current_view = self.column_view_var.get()
        current_columns = self.column_views.get(current_view, self.column_views['standard'])
        
        # Create the treeview
        if hasattr(self, 'results_tree'):
            self.results_tree.destroy()
        
        self.results_tree = ttk.Treeview(parent_frame, columns=current_columns, show="headings", height=15)
        
        # Initialize sorting state
        self.sort_column = None
        self.sort_reverse = False
        
        # Configure column headings and widths
        for col in current_columns:
            self.results_tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            width = self.all_columns.get(col, {}).get('width', 100)
            self.results_tree.column(col, width=width)
        
        # Setup scrollbars
        if hasattr(self, 'v_scrollbar'):
            self.v_scrollbar.destroy()
        if hasattr(self, 'h_scrollbar'):
            self.h_scrollbar.destroy()
            
        self.v_scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.h_scrollbar = ttk.Scrollbar(parent_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        # Pack tree and scrollbars
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)
    
    def setup_results_tree_events(self):
        """Setup event bindings for the results tree."""
        self.results_tree.bind('<<TreeviewSelect>>', self.on_result_select)
        self.results_tree.bind('<Double-1>', self.on_publication_double_click)
    
    def on_column_view_change(self, event=None):
        """Handle column view change."""
        if hasattr(self, 'results_tree') and hasattr(self, 'current_publications'):
            # Get the parent frame
            tree_parent = self.results_tree.master
            
            # Recreate the tree with new columns
            self.setup_results_tree(tree_parent)
            
            # Repopulate with current data if available
            if self.current_publications:
                self.populate_results_tree()
    
    def show_column_customization(self):
        """Show column customization dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Customize Columns")
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (200)
        y = (dialog.winfo_screenheight() // 2) - (250)
        dialog.geometry(f"400x500+{x}+{y}")
        
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Select Columns to Display:", 
                 font=('Arial', 10, 'bold')).pack(pady=(0, 10))
        
        # Column checkboxes
        self.column_vars = {}
        for col_id, col_text in [
            ("title", "Title"),
            ("authors", "Authors"),
            ("year", "Year"),
            ("source", "Source"),
            ("type", "Type"),
            ("url", "Primary URL"),
            ("dnb_direct", "DNB Direct"),
            ("dnb_record", "DNB Record")
        ]:
            var = tk.BooleanVar(value=True)  # Default all to True
            self.column_vars[col_id] = var
            ttk.Checkbutton(main_frame, text=col_text, variable=var).pack(anchor=tk.W, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Apply", 
                  command=lambda: [self.apply_column_customization(), dialog.destroy()]).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", 
                  command=dialog.destroy).pack(side=tk.RIGHT)
    
    def apply_column_customization(self):
        """Apply column customization (placeholder for now)."""
        # This would modify the tree columns based on selected checkboxes
        # For now, just show a message
        messagebox.showinfo("Column Customization", "Column customization applied!")

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
        
        # Create scrollable frame for settings
        canvas = tk.Canvas(settings_frame)
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        ttk.Label(scrollable_frame, text="Settings", style='Title.TLabel').pack(pady=(20, 30))
        
        # Main settings frame
        main_settings_frame = ttk.Frame(scrollable_frame)
        main_settings_frame.pack(expand=True, padx=50, pady=20)
        
        # PubMed API Configuration
        self.create_pubmed_api_frame(main_settings_frame)
        
        # General API settings
        api_frame = ttk.LabelFrame(main_settings_frame, text="General API Settings", padding=20)
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
        
        about_text = """Medical Spytool v1.4-beta
        
A comprehensive tool for searching and analyzing publications from multiple medical and academic databases including the German National Library (DNB) and PubMed.

Features:
• Multi-database search (DNB + PubMed)
• PubMed API key integration for enhanced performance
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
    
    def create_pubmed_api_frame(self, parent):
        """Create PubMed API configuration frame."""
        pubmed_frame = ttk.LabelFrame(parent, text="PubMed API Configuration", padding=20)
        pubmed_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Status indicator
        status_frame = ttk.Frame(pubmed_frame)
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(status_frame, text="API Status:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.pubmed_status_label = ttk.Label(status_frame, text="Not Configured", foreground="red")
        self.pubmed_status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        self.rate_limit_label = ttk.Label(status_frame, text="Rate Limit: 3 requests/second (Public)", 
                                         font=('Arial', 9, 'italic'))
        self.rate_limit_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Information section
        info_frame = ttk.Frame(pubmed_frame)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        info_text = ("Configure your NCBI API key to increase your PubMed search rate limit from 3 to 10 requests per second.\n"
            except Exception as e:
                self.root.after(0, self._handle_api_test_error, str(e))
        
        threading.Thread(target=test_api, daemon=True).start()
    
    def _handle_api_test_result(self, result, api_key):
        """Handle API test result in main thread."""
        self.test_api_button.config(state='normal')
        
        if result:
            if api_key:
                self.pubmed_status_label.config(text="✓ API Key Valid", foreground="green")
                self.rate_limit_label.config(text="Rate Limit: 10 requests/second (Authenticated)")
                messagebox.showinfo("Success", "API key is valid! You now have increased rate limits (10 req/sec).")
            else:
                self.pubmed_status_label.config(text="✓ Public Access", foreground="blue")
                self.rate_limit_label.config(text="Rate Limit: 3 requests/second (Public)")
                messagebox.showinfo("Success", "PubMed is accessible without API key (3 req/sec limit).")
        else:
            self.pubmed_status_label.config(text="✗ Connection Failed", foreground="red")
            messagebox.showerror("Error", "Failed to connect to PubMed API. Please check your settings.")
    
    def _handle_api_test_error(self, error_msg):
        """Handle API test error in main thread."""
        self.test_api_button.config(state='normal')
        self.pubmed_status_label.config(text="✗ Test Failed", foreground="red")
        messagebox.showerror("Error", f"API test failed: {error_msg}")
    
    def save_pubmed_config(self):
        """Save PubMed API configuration."""
        try:
            config = {
                'api_key': self.api_key_var.get().strip(),
                'email': self.email_var.get().strip(),
                'tool_name': self.tool_name_var.get().strip()
            }
            
            # Validate configuration
            if not config['email']:
                messagebox.showerror("Error", "Email address is required.")
                return
            
            # Save through database manager
            success = self.db_manager.save_pubmed_config(config)
            
            if success:
                messagebox.showinfo("Success", "PubMed configuration saved successfully.")
                # Apply the configuration immediately
                self.db_manager.configure_pubmed_api(
                    config['api_key'], 
                    config['email'], 
                    config['tool_name']
                )
            else:
                messagebox.showerror("Error", "Failed to save configuration.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def load_pubmed_config(self):
        """Load PubMed API configuration."""
        try:
            config = self.db_manager.load_pubmed_config()
            
            if config:
                self.api_key_var.set(config.get('api_key', ''))
                self.email_var.set(config.get('email', 'dnbspytool@example.com'))
                self.tool_name_var.set(config.get('tool_name', 'Medical-Spytool'))
                
                # Apply configuration to database manager
                self.db_manager.configure_pubmed_api(
                    config.get('api_key', ''),
                    config.get('email', 'dnbspytool@example.com'),
                    config.get('tool_name', 'Medical-Spytool')
                )
                
                # Update status display
                if config.get('api_key'):
                    self.pubmed_status_label.config(text="✓ API Key Configured", foreground="green")
                    self.rate_limit_label.config(text="Rate Limit: 10 requests/second (Authenticated)")
                else:
                    self.pubmed_status_label.config(text="✓ Public Access", foreground="blue")
                    self.rate_limit_label.config(text="Rate Limit: 3 requests/second (Public)")
                    
        except Exception as e:
            print(f"Failed to load PubMed configuration: {e}")
            # Set defaults
            self.email_var.set('dnbspytool@example.com')
            self.tool_name_var.set('Medical-Spytool')
    
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
        """Start the enhanced search with real-time progress."""
        # Validate inputs
        if not self.validate_search_inputs():
            return
        
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
        
        # Create progress dialog
        self.progress_dialog = RealTimeProgressDialog(self.root, "Medical Spytool - Search Progress")
        self.progress_dialog.set_cancel_callback(self.cancel_enhanced_search)
        
        # Disable search button
        self.search_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Clear previous results
        self.clear_results()
        
        # Start enhanced search in separate thread
        self.search_thread = threading.Thread(
            target=self.perform_enhanced_search,
            args=(authors, databases, max_results),
            daemon=True
        )
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

    def perform_enhanced_search(self, authors: List[str], databases: List[DatabaseType], max_results: int):
        """Perform enhanced search with robust error handling and progress tracking."""
        try:
            # Use enhanced search manager for better error handling and progress tracking
            results = self.search_manager.search_with_fallback(
                queries=authors,
                databases=databases,
                max_results=max_results,
                enable_parallel=True
            )
            
            # Process results with enhanced processor
            if results:
                processed_results = self.result_processor.process_results(
                    raw_results=results,
                    search_query=" ".join(authors),
                    source_databases=[db.value for db in databases]
                )
                
                # Convert processed results back to legacy format
                legacy_results = {
                    'publications': [pub.original_data for pub in processed_results],
                    'deduplication_stats': self.result_processor.get_duplicate_summary(processed_results),
                    'search_time': 0.0,  # Will be calculated by search manager
                    'processing_stats': self.result_processor.get_processing_statistics()
                }
                
                # Send results to main thread
                self.result_queue.put(('results', legacy_results))
            else:
                self.result_queue.put(('results', {'publications': []}))
                
        except Exception as e:
            self.result_queue.put(('error', str(e)))
        finally:
            # Close progress dialog
            self.root.after(0, self.close_progress_dialog)
    
    def cancel_enhanced_search(self):
        """Cancel the enhanced search operation."""
        if hasattr(self, 'search_manager'):
            self.search_manager.cancel_search()
        
        # Update UI
        self.root.after(0, self.reset_search_ui)
    
    def close_progress_dialog(self):
        """Close the progress dialog."""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # Reset UI
        self.reset_search_ui()
    
    def reset_search_ui(self):
        """Reset search UI to initial state."""
        self.search_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_var.set(0)
    
    def on_search_progress(self, progress):
        """Handle search progress updates."""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.root.after(0, lambda: self.progress_dialog.update_progress(progress))
    
    def on_search_results(self, results):
        """Handle search results from enhanced search manager."""
        # This will be called by the search manager when results are available
        # We handle results in perform_enhanced_search instead
        pass
    
    def on_search_error(self, error_message):
        """Handle search errors with enhanced error dialog."""
        self.root.after(0, lambda: self.show_enhanced_error(error_message))
    
    def show_enhanced_error(self, error_message: str):
        """Show enhanced error dialog with solutions."""
        # Common solutions for search errors
        solutions = [
            "Check your internet connection and try again",
            "Verify that the author names are spelled correctly",
            "Try searching with fewer authors or reduced result limits",
            "Check if the selected databases are currently available",
            "Clear the cache and restart the application if problems persist"
        ]
        
        # Get detailed error info if available
        error_details = ""
        if hasattr(self, 'search_manager'):
            stats = self.search_manager.get_search_statistics()
            error_details = f"Search Statistics:\n{json.dumps(stats, indent=2)}"
        
        show_enhanced_error(
            self.root,
            "Search Error",
            error_message,
            error_details,
            solutions
        )
        
        # Reset UI
        self.reset_search_ui()
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.complete(success=False)
    
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

    # Add missing helper functions that populate_results_tree() calls
    def safe_join(self, value, default=''):
        """
        Safely join values that might be lists, strings, or None.
        
        Args:
            value: Value to join (can be list, string, or None)
            default: Default value to return if input is empty/None
            
        Returns:
            Joined string or default value
        """
        if value is None:
            return default
        elif isinstance(value, list):
            # Filter out empty values and join
            filtered_items = [str(item) for item in value if item]
            return ', '.join(filtered_items) if filtered_items else default
        elif isinstance(value, str):
            return value if value.strip() else default
        else:
            return str(value) if value else default

    def _get_primary_url_for_display(self, publication: Dict) -> str:
        """
        Get the primary URL for display in the results tree.
        
        Args:
            publication: Publication dictionary
            
        Returns:
            Primary URL for display (truncated if too long)
        """
        try:
            # Check for direct URL field first
            if publication.get('url'):
                url = str(publication['url'])
                return url[:30] + "..." if len(url) > 30 else url
            
            # Check for DOI
            if publication.get('doi'):
                doi = str(publication['doi'])
                if doi.startswith('http'):
                    return doi[:30] + "..." if len(doi) > 30 else doi
                else:
                    url = f"https://doi.org/{doi}"
                    return url[:30] + "..." if len(url) > 30 else url
            
            # Check other URL fields
            url_fields = ['dnb_direct', 'pmid', 'pmc']
            for field in url_fields:
                if publication.get(field):
                    url = str(publication[field])
                    if url.startswith('http'):
                        return url[:30] + "..." if len(url) > 30 else url
            
            return ""
        except Exception:
            return ""

    def _get_dnb_direct_url(self, publication: Dict) -> str:
        """
        Get DNB direct URL for display.
        
        Args:
            publication: Publication dictionary
            
        Returns:
            DNB direct URL (shortened for display)
        """
        try:
            dnb_direct = publication.get('dnb_direct', '')
            if dnb_direct:
                return "✓" if dnb_direct.startswith('http') else ""
            return ""
        except Exception:
            return ""

    def _get_dnb_record_url(self, publication: Dict) -> str:
        """
        Get DNB record URL for display.
        
        Args:
            publication: Publication dictionary
            
        Returns:
            DNB record URL indicator for display
        """
        try:
            # Check for DNB record URL
            dnb_record = publication.get('dnb_record', '')
            if dnb_record:
                return "✓" if dnb_record.startswith('http') else ""
            
            # Fallback: generate from record ID if available
            record_id = publication.get('id') or publication.get('record_id')
            if record_id:
                return "✓"
            
            return ""
        except Exception:
            return ""

    def open_selected_publication_url(self):
        """Open the URL of the selected publication in the web browser."""
        try:
            selection = self.results_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a publication first.")
                return
            
            # Get selected publication
            item = selection[0]
            index = self.results_tree.index(item)
            
            if 0 <= index < len(self.current_publications):
                pub = self.current_publications[index]
                
                # Get all available URLs for this publication
                urls = self._get_publication_urls(pub)
                
                if not urls:
                    messagebox.showinfo("No URL", "No accessible URL found for this publication.")
                    return
                
                if len(urls) == 1:
                    # Single URL - open directly
                    url = urls[0]['url']
                    webbrowser.open(url)
                    self.update_status(f"Opened URL: {url[:50]}...")
                else:
                    # Multiple URLs - show selection dialog
                    selected_url = self._select_url_dialog(urls)
                    if selected_url:
                        webbrowser.open(selected_url)
                        self.update_status(f"Opened URL: {selected_url[:50]}...")
            else:
                messagebox.showwarning("Invalid Selection", "Selected publication is not valid.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open URL: {str(e)}")
            print(f"Error opening URL: {e}")
    
    def copy_selected_publication_url(self):
        """Copy the URL of the selected publication to the clipboard."""
        try:
            selection = self.results_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a publication first.")
                return
            
            # Get selected publication
            item = selection[0]
            index = self.results_tree.index(item)
            
            if 0 <= index < len(self.current_publications):
                pub = self.current_publications[index]
                
                # Get all available URLs for this publication
                urls = self._get_publication_urls(pub)
                
                if not urls:
                    messagebox.showinfo("No URL", "No accessible URL found for this publication.")
                    return
                
                if len(urls) == 1:
                    # Single URL - copy directly
                    url = urls[0]['url']
                    self.root.clipboard_clear()
                    self.root.clipboard_append(url)
                    self.root.update()  # Update clipboard
                    messagebox.showinfo("Copied", f"URL copied to clipboard:\n{url}")
                    self.update_status(f"Copied URL: {url[:50]}...")
                else:
                    # Multiple URLs - show selection dialog
                    selected_url = self._select_url_dialog(urls)
                    if selected_url:
                        self.root.clipboard_clear()
                        self.root.clipboard_append(selected_url)
                        self.root.update()  # Update clipboard
                        messagebox.showinfo("Copied", f"URL copied to clipboard:\n{selected_url}")
                        self.update_status(f"Copied URL: {selected_url[:50]}...")
            else:
                messagebox.showwarning("Invalid Selection", "Selected publication is not valid.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy URL: {str(e)}")
            print(f"Error copying URL: {e}")
    
    def _get_publication_urls(self, publication: Dict) -> List[Dict[str, str]]:
        """
        Extract all available URLs from a publication.
        
        Args:
            publication: Publication dictionary
            
        Returns:
            List of URL dictionaries with 'url' and 'label' keys
        """
        urls = []
        
        try:
            # Primary URL (highest priority)
            if publication.get('url'):
                urls.append({
                    'url': str(publication['url']),
                    'label': 'Primary URL'
                })
            
            # DOI URL
            if publication.get('doi'):
                doi = str(publication['doi'])
                if doi.startswith('http'):
                    urls.append({
                        'url': doi,
                        'label': 'DOI Link'
                    })
                else:
                    urls.append({
                        'url': f"https://doi.org/{doi}",
                        'label': 'DOI Link'
                    })
            
            # DNB Direct URL
            if publication.get('dnb_direct'):
                dnb_direct = str(publication['dnb_direct'])
                if dnb_direct.startswith('http'):
                    urls.append({
                        'url': dnb_direct,
                        'label': 'DNB Direct Link'
                    })
            
            # PubMed URL
            if publication.get('pmid'):
                pmid = str(publication['pmid'])
                urls.append({
                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    'label': 'PubMed'
                })
            
            # PMC URL
            if publication.get('pmc'):
                pmc = str(publication['pmc'])
                if pmc.startswith('PMC'):
                    urls.append({
                        'url': f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/",
                        'label': 'PMC Full Text'
                    })
                else:
                    urls.append({
                        'url': f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc}/",
                        'label': 'PMC Full Text'
                    })
            
            # DNB Record URL
            if publication.get('dnb_record'):
                dnb_record = str(publication['dnb_record'])
                if dnb_record.startswith('http'):
                    urls.append({
                        'url': dnb_record,
                        'label': 'DNB Record'
                    })
            
            # Additional URLs from all_urls field if available
            if publication.get('all_urls') and isinstance(publication['all_urls'], list):
                for url_entry in publication['all_urls']:
                    if isinstance(url_entry, dict) and url_entry.get('url'):
                        # Check if this URL is not already in our list
                        url_str = str(url_entry['url'])
                        if not any(existing['url'] == url_str for existing in urls):
                            urls.append({
                                'url': url_str,
                                'label': url_entry.get('label', 'Additional URL')
                            })
            
        except Exception as e:
            print(f"Error extracting URLs from publication: {e}")
        
        return urls
    
    def _select_url_dialog(self, urls: List[Dict[str, str]]) -> Optional[str]:
        """
        Show a dialog to select from multiple URLs.
        
        Args:
            urls: List of URL dictionaries with 'url' and 'label' keys
            
        Returns:
            Selected URL string or None if cancelled
        """
        try:
            dialog = tk.Toplevel(self.root)
            dialog.title("Select URL")
            dialog.geometry("500x300")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
            y = (dialog.winfo_screenheight() // 2) - (300 // 2)
            dialog.geometry(f"500x300+{x}+{y}")
            
            selected_url = [None]  # Use list to allow modification in nested function
            
            # Main frame
            main_frame = ttk.Frame(dialog, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            ttk.Label(main_frame, text="Multiple URLs available. Please select one:", 
                     font=('Arial', 10, 'bold')).pack(pady=(0, 10))
            
            # URL list frame
            list_frame = ttk.Frame(main_frame)
            list_frame.pack(fill=tk.BOTH, expand=True)
            
            # Listbox with scrollbar
            listbox_frame = ttk.Frame(list_frame)
            listbox_frame.pack(fill=tk.BOTH, expand=True)
            
            listbox = tk.Listbox(listbox_frame, font=('Arial', 9))
            scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
            listbox.configure(yscrollcommand=scrollbar.set)
            
            # Populate listbox
            for i, url_info in enumerate(urls):
                label = url_info['label']
                url = url_info['url']
                # Truncate long URLs for display
                display_url = url if len(url) <= 60 else url[:57] + "..."
                listbox.insert(tk.END, f"{label}: {display_url}")
            
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Select first item by default
            if urls:
                listbox.selection_set(0)
            
            # Button frame
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(10, 0))
            
            def on_ok():
                selection = listbox.curselection()
                if selection:
                    selected_url[0] = urls[selection[0]]['url']
                dialog.destroy()
            
            def on_cancel():
                dialog.destroy()
            
            def on_double_click(event):
                on_ok()
            
            # Bind double-click
            listbox.bind('<Double-Button-1>', on_double_click)
            
            # Buttons
            ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=(5, 0))
            ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT)
            
            # Wait for dialog to close
            dialog.wait_window()
            
            return selected_url[0]
            
        except Exception as e:
            print(f"Error in URL selection dialog: {e}")
            return None
    
    def on_result_select(self, event):
        """Handle result selection in tree to enable/disable URL buttons."""
        try:
            selection = self.results_tree.selection()
            if not selection:
                # No selection - disable URL buttons
                if hasattr(self, 'open_url_button'):
                    self.open_url_button.config(state=tk.DISABLED)
                if hasattr(self, 'copy_url_button'):
                    self.copy_url_button.config(state=tk.DISABLED)
                return
            
            # Get selected publication
            item = selection[0]
            index = self.results_tree.index(item)
            
            if 0 <= index < len(self.current_publications):
                pub = self.current_publications[index]
                
                # Show publication details
                self.show_publication_details(pub)
                
                # Check if URLs are available to enable/disable buttons
                urls = self._get_publication_urls(pub)
                button_state = tk.NORMAL if urls else tk.DISABLED
                
                if hasattr(self, 'open_url_button'):
                    self.open_url_button.config(state=button_state)
                if hasattr(self, 'copy_url_button'):
                    self.copy_url_button.config(state=button_state)
            else:
                # Invalid selection - disable URL buttons
                if hasattr(self, 'open_url_button'):
                    self.open_url_button.config(state=tk.DISABLED)
                if hasattr(self, 'copy_url_button'):
                    self.copy_url_button.config(state=tk.DISABLED)
                    
        except Exception as e:
            print(f"Error in result selection handler: {e}")
            # On error, disable URL buttons
            if hasattr(self, 'open_url_button'):
                self.open_url_button.config(state=tk.DISABLED)
            if hasattr(self, 'copy_url_button'):
                self.copy_url_button.config(state=tk.DISABLED)

    def on_publication_double_click(self, event):
        """Handle double-click on publication to open URL."""
        try:
            # Call the open URL method
            self.open_selected_publication_url()
        except Exception as e:
            print(f"Error in double-click handler: {e}")

    def browse_export_file(self):
        """Browse for export file location."""
        try:
            format_type = self.export_format_var.get()
            extensions = {
                'csv': [('CSV files', '*.csv'), ('All files', '*.*')],
                'json': [('JSON files', '*.json'), ('All files', '*.*')],
                'excel': [('Excel files', '*.xlsx'), ('All files', '*.*')]
            }
            
            filename = filedialog.asksaveasfilename(
                title="Save export file as...",
                filetypes=extensions.get(format_type, [('All files', '*.*')]),
                defaultextension=f".{format_type}"
            )
            
            if filename:
                self.export_file_var.set(filename)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to browse for export file: {str(e)}")
    
    def browse_report_file(self):
        """Browse for report file location."""
        try:
            format_type = self.report_format_var.get()
            extensions = {
                'pdf': [('PDF files', '*.pdf'), ('All files', '*.*')],
                'html': [('HTML files', '*.html'), ('All files', '*.*')]
            }
            
            filename = filedialog.asksaveasfilename(
                title="Save report file as...",
                filetypes=extensions.get(format_type, [('All files', '*.*')]),
                defaultextension=f".{format_type}"
            )
            
           
            
            if filename:
                self.report_file_var.set(filename)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to browse for report file: {str(e)}")
    
    def export_data(self):
        """Export current search results."""
        try:
            if not self.current_publications:
                messagebox.showwarning("No Data", "No publication data to export. Please perform a search first.")
                return
            
            export_file = self.export_file_var.get().strip()
            if not export_file:
                messagebox.showerror("Error", "Please specify an export file location.")
                return
            
            format_type = self.export_format_var.get()
            
            # Show progress
            self.update_status(f"Exporting data to {format_type.upper()} format...")
            
            # DEBUG: Check publication data structure before export
            print(f"[DEBUG] Exporting {len(self.current_publications)} publications")
            if self.current_publications:
                sample_pub = self.current_publications[0]
                print(f"[DEBUG] Sample publication keys: {list(sample_pub.keys())}")
                print(f"[DEBUG] Sample publication abstract: {sample_pub.get('abstract', 'NOT_FOUND')}")
                print(f"[DEBUG] Sample publication description: {sample_pub.get('description', 'NOT_FOUND')}")
                print(f"[DEBUG] Sample publication content: {sample_pub.get('content', 'NOT_FOUND')}")
            
            # Export using the DataExporter
            success = self.exporter.export_publications(
                self.current_publications, 
                format_type,
                export_file
            )
            
            if success:
                self.update_status(f"Data exported successfully to {export_file}")
                messagebox.showinfo("Export Complete", 
                                  f"Data successfully exported to:\n{export_file}")
            else:
                messagebox.showerror("Export Error", "Failed to export data.")
                
        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            self.update_status("Export failed")
            messagebox.showerror("Export Error", error_msg)
    
    def export_report(self):
        """Export analytics report."""
        try:
            if not self.current_analyzer:
                messagebox.showwarning("No Analytics", 
                                     "No analytics data available. Please generate analytics first.")
                return
            
            report_file = self.report_file_var.get().strip()
            if not report_file:
                messagebox.showerror("Error", "Please specify a report file location.")
                return
            
            format_type = self.report_format_var.get()
            
            # Show progress
            self.update_status(f"Exporting report to {format_type.upper()} format...")
            
            # Export report using the DataExporter
            success = self.exporter.export_analytics_report(
                self.current_analyzer,
                self.current_visualizer, 
                report_file, 
                format_type
            )
            
            if success:
                self.update_status(f"Report exported successfully to {report_file}")
                messagebox.showinfo("Export Complete", 
                                  f"Report successfully exported to:\n{report_file}")
            else:
                messagebox.showerror("Export Error", "Failed to export report.")
                
        except Exception as e:
            error_msg = f"Report export failed: {str(e)}"
            self.update_status("Report export failed")
            messagebox.showerror("Export Error", error_msg)

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
            else:
                # Default to timeline
                self.current_figure = self.current_visualizer.create_publication_timeline()
            
            # Display the chart
            if self.current_figure:
                self.canvas = FigureCanvasTkAgg(self.current_figure, self.chart_frame)
                self.canvas.draw()
                self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
        except Exception as e:
            print(f"Error updating chart: {e}")
            # Show error message in chart area
            if hasattr(self, 'chart_frame'):
                error_label = ttk.Label(self.chart_frame, text=f"Chart Error: {str(e)}")
                error_label.pack(pady=20)

    def on_closing(self):
        """Handle application closing with proper cleanup of enhanced components."""
        try:
            # Stop the timer loop
            self.is_running = False
            
            # Cancel any pending after calls
            if hasattr(self, 'after_id') and self.after_id:
                try:
                    self.root.after_cancel(self.after_id)
                except tk.TclError:
                    pass  # Already cancelled or window destroyed
            
            # Cancel any running enhanced search
            if hasattr(self, 'search_manager') and self.search_manager:
                try:
                    self.search_manager.cancel_search()
                    self.search_manager.cleanup()
                except Exception as e:
                    print(f"Error cleaning up search manager: {e}")
            
            # Close progress dialog if open
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                try:
                    self.progress_dialog.close()
                except Exception as e:
                    print(f"Error closing progress dialog: {e}")
            
            # Cleanup enhanced components
            if hasattr(self, 'result_processor') and self.result_processor:
                try:
                    # Optional: save processing statistics
                    stats = self.result_processor.get_processing_statistics()
                    print(f"Final processing stats: {stats.get('total_processed', 0)} publications processed")
                except Exception as e:
                    print(f"Error getting final stats: {e}")
            
            # Cleanup cache manager
            if hasattr(self, 'cache_manager') and self.cache_manager:
                try:
                    self.cache_manager.cleanup_expired()
                    print(f"Cache cleanup completed. Hit rate: {self.cache_manager.get_hit_rate():.1%}")
                except Exception as e:
                    print(f"Error cleaning up cache: {e}")
            
            # Stop any running search threads (legacy support)
            if hasattr(self, 'search_thread') and self.search_thread and self.search_thread.is_alive():
                try:
                    self.search_thread.join(timeout=2.0)
                except Exception as e:
                    print(f"Error stopping search thread: {e}")
            
            # Close matplotlib figures to prevent memory leaks
            try:
                plt.close('all')
            except Exception as e:
                print(f"Error closing matplotlib figures: {e}")
            
            # Finally destroy the root window
            try:
                self.root.destroy()
            except tk.TclError:
                pass  # Window already destroyed
        
        except Exception as e:
            print(f"Error during cleanup: {e}")
            # Force window destruction as last resort
            try:
                self.root.destroy()
            except:
                pass


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
