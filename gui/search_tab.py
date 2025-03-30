"""
Search Tab

This module defines the search tab for searching publications.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import logging
from datetime import datetime
from tkcalendar import DateEntry

from database_connectors import DATABASE_CONNECTORS
from utils.logging_manager import log_message, clear_log, export_log
from utils.config_manager import get_api_key
from gui.persons_manager import PersonsManager

logger = logging.getLogger(__name__)

class SearchTab:
    """
    Tab for searching publications.
    """
    
    def __init__(self, notebook, main_window):
        """
        Initialize the search tab.
        
        Args:
            notebook (ttk.Notebook): Parent notebook.
            main_window (MainWindow): Main application window.
        """
        self.notebook = notebook
        self.main_window = main_window
        self.settings = main_window.settings
        self.search_results = []
        self.search_thread = None
        self.stop_search = False
        self.pause_search = False
        
        # Create frame
        self.frame = ttk.Frame(notebook, padding=10)
        
        # Create widgets
        self.create_widgets()
        
        logger.info("Search tab initialized")
    
    def create_widgets(self):
        """Create search tab widgets."""
        # Create paned window (left: search options, right: log)
        self.paned_window = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left panel: Search options
        self.search_frame = ttk.Frame(self.paned_window, padding=(0, 0, 5, 0))
        self.paned_window.add(self.search_frame, weight=3)
        
        # Database selection
        self.create_database_selection()
        
        # Person management
        self.persons_manager = PersonsManager(
            self.search_frame, 
            settings=self.settings,
            database_options=self.database_var,
        )
        
        # Search options
        self.create_search_options()
        
        # Search controls
        self.create_search_controls()
        
        # Right panel: Log
        self.log_frame = ttk.LabelFrame(self.paned_window, text="Log", padding=5)
        self.paned_window.add(self.log_frame, weight=2)
        
        # Log text widget
        self.log_text = tk.Text(self.log_frame, wrap=tk.WORD, height=20, width=40)
        self.log_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.log_text.config(state="disabled")
        
        # Log scrollbar
        self.log_scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scrollbar.set)
        self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Log controls
        self.log_controls_frame = ttk.Frame(self.log_frame)
        self.log_controls_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        
        ttk.Button(self.log_controls_frame, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.log_controls_frame, text="Export Log", command=self.export_log).pack(side=tk.LEFT, padx=2)
        
        # Initialize with a welcome message
        self.log_message("Welcome to the Integrated Publication Search Tool")
        self.log_message("Please enter search terms and select options to begin")
    
    def create_database_selection(self):
        """Create database selection widgets."""
        # Database selection frame
        db_frame = ttk.LabelFrame(self.search_frame, text="Database", padding=5)
        db_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Database selection
        self.database_var = tk.StringVar(value="PubMed")
        
        # Radio buttons for databases
        self.db_radios = []
        
        # Add combined option
        combined_radio = ttk.Radiobutton(
            db_frame, 
            text="Combined Search", 
            variable=self.database_var, 
            value="Combined",
            command=self.on_database_change
        )
        combined_radio.grid(row=0, column=0, sticky=tk.W, padx=5)
        self.db_radios.append(combined_radio)
        
        # Add individual database options
        for i, db_name in enumerate(DATABASE_CONNECTORS.keys()):
            radio = ttk.Radiobutton(
                db_frame, 
                text=db_name, 
                variable=self.database_var, 
                value=db_name,
                command=self.on_database_change
            )
            radio.grid(row=0, column=i+1, sticky=tk.W, padx=5)
            self.db_radios.append(radio)
        
        # Set default from settings
        default_db = self.settings.get("default_database", "PubMed")
        if default_db in [r.cget("value") for r in self.db_radios]:
            self.database_var.set(default_db)
    
    def create_search_options(self):
        """Create search options widgets."""
        # Search options frame
        self.options_frame = ttk.LabelFrame(self.search_frame, text="Search Options", padding=5)
        self.options_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Create a notebook for advanced options
        options_notebook = ttk.Notebook(self.options_frame)
        options_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Date range tab
        date_frame = ttk.Frame(options_notebook, padding=5)
        options_notebook.add(date_frame, text="Date Range")
        
        # Date range widgets
        ttk.Label(date_frame, text="From:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.start_date = DateEntry(date_frame, width=12, background='darkblue',
                               foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.start_date.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(date_frame, text="To:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.end_date = DateEntry(date_frame, width=12, background='darkblue',
                             foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.end_date.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Date filter checkbox
        self.use_date_filter = tk.BooleanVar(value=False)
        ttk.Checkbutton(date_frame, text="Enable Date Filter", variable=self.use_date_filter).grid(
            row=0, column=4, sticky=tk.W, padx=5, pady=5)
        
        # Language tab
        language_frame = ttk.Frame(options_notebook, padding=5)
        options_notebook.add(language_frame, text="Language")
        
        # Language widgets
        ttk.Label(language_frame, text="Language:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.language_var = tk.StringVar()
        language_options = ["", "English", "German", "French", "Spanish", "Italian"]
        language_combo = ttk.Combobox(language_frame, textvariable=self.language_var, values=language_options)
        language_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Publication type tab
        pub_type_frame = ttk.Frame(options_notebook, padding=5)
        options_notebook.add(pub_type_frame, text="Publication Type")
        
        # Publication type widgets
        ttk.Label(pub_type_frame, text="Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.pub_type_var = tk.StringVar()
        pub_type_options = ["", "Journal Article", "Review", "Clinical Trial", "Book", "Thesis"]
        pub_type_combo = ttk.Combobox(pub_type_frame, textvariable=self.pub_type_var, values=pub_type_options)
        pub_type_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Search field tab
        field_frame = ttk.Frame(options_notebook, padding=5)
        options_notebook.add(field_frame, text="Search Field")
        
        # Search field widgets
        ttk.Label(field_frame, text="Field:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.field_var = tk.StringVar(value="Alle Felder")
        self.field_combo = ttk.Combobox(field_frame, textvariable=self.field_var)
        self.field_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Update field options based on selected database
        self.update_field_options()
    
    def create_search_controls(self):
        """Create search control widgets."""
        # Results limit frame
        limit_frame = ttk.Frame(self.search_frame, padding=5)
        limit_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(limit_frame, text="Max Results:").pack(side=tk.LEFT, padx=5)
        
        self.max_results_var = tk.StringVar(value="100")
        max_results_entry = ttk.Spinbox(limit_frame, from_=10, to=1000, increment=10, 
                                        textvariable=self.max_results_var, width=5)
        max_results_entry.pack(side=tk.LEFT, padx=5)
        
        # Search buttons frame
        buttons_frame = ttk.Frame(self.search_frame, padding=5)
        buttons_frame.pack(fill=tk.X)
        
        # Start search button
        self.start_button = ttk.Button(buttons_frame, text="Start Search", command=self.start_search, width=15)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Pause/resume button
        self.pause_button = ttk.Button(buttons_frame, text="Pause", command=self.toggle_pause, width=15)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        self.pause_button.config(state="disabled")
        
        # Stop button
        self.stop_button = ttk.Button(buttons_frame, text="Stop", command=self.stop_search_process, width=15)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.stop_button.config(state="disabled")
    
    def on_database_change(self):
        """Handle database selection change."""
        self.update_field_options()
    
    def update_field_options(self):
        """Update search field options based on selected database."""
        selected_db = self.database_var.get()
        
        if selected_db == "Combined":
            # For combined search, use common fields
            fields = ["Alle Felder", "Autor", "Titel"]
        else:
            # Get fields from the selected database connector
            db_class = DATABASE_CONNECTORS.get(selected_db)
            if db_class:
                connector = db_class()
                fields = connector.get_available_fields()
            else:
                fields = ["Alle Felder"]
        
        self.field_combo.config(values=fields)
        if self.field_var.get() not in fields:
            self.field_var.set(fields[0])
    
    def log_message(self, message):
        """
        Add a message to the log.
        
        Args:
            message (str): Message to log.
        """
        log_message(self.log_text, message)
    
    def clear_log(self):
        """Clear the log."""
        clear_log(self.log_text)
    
    def export_log(self):
        """Export the log to a file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            export_log(self.log_text, file_path)
    
    def get_search_params(self):
        """
        Get search parameters from the UI.
        
        Returns:
            dict: Search parameters.
        """
        params = {
            'database': self.database_var.get(),
            'max_results': int(self.max_results_var.get())
        }
        
        # Add date range if enabled
        if self.use_date_filter.get():
            params['date_range'] = {
                'start': self.start_date.get_date(),
                'end': self.end_date.get_date()
            }
        
        # Add language if specified
        if self.language_var.get():
            params['language'] = self.language_var.get()
        
        # Add publication type if specified
        if self.pub_type_var.get():
            params['pub_type'] = self.pub_type_var.get()
        
        # Add search field if specified
        if self.field_var.get() != "Alle Felder":
            params['field'] = self.field_var.get()
        
        return params
    
    def prepare_search(self):
        """
        Prepare for search.
        
        Returns:
            tuple: (selected_persons, search_params) or None if preparation failed.
        """
        # Get selected persons
        selected_persons = self.persons_manager.get_selected_persons()
        if not selected_persons:
            messagebox.showwarning("No Selection", "Please select at least one person to search for.")
            return None
        
        # Get search parameters
        search_params = self.get_search_params()
        
        return selected_persons, search_params
    
    def start_search(self):
        """Start the search process."""
        # Check if a search is already running
        if self.search_thread and self.search_thread.is_alive():
            messagebox.showinfo("Search in Progress", "A search is already running.")
            return
        
        preparation = self.prepare_search()
        if not preparation:
            return
        
        selected_persons, search_params = preparation
        
        # Reset control flags
        self.stop_search = False
        self.pause_search = False
        
        # Update button states
        self.start_button.config(state="disabled")
        self.pause_button.config(state="normal")
        self.stop_button.config(state="normal")
        
        # Start search in a separate thread
        self.search_thread = threading.Thread(
            target=self.search_process,
            args=(selected_persons, search_params),
            daemon=True
        )
        self.search_thread.start()
    
    def toggle_pause(self):
        """Toggle pause/resume search."""
        if self.pause_search:
            # Resume search
            self.pause_search = False
            self.pause_button.config(text="Pause")
            self.log_message("Search resumed")
        else:
            # Pause search
            self.pause_search = True
            self.pause_button.config(text="Resume")
            self.log_message("Search paused")
    
    def stop_search_process(self):
        """Stop the search process."""
        self.stop_search = True
        self.log_message("Stopping search...")
    
    def search_process(self, persons, params):
        """
        Execute the search process.
        
        Args:
            persons (list): List of person dictionaries.
            params (dict): Search parameters.
        """
        try:
            database = params.get('database')
            self.log_message(f"Starting search in {database} for {len(persons)} persons")
            
            # Update status
            self.main_window.update_status("Searching...", 0)
            
            all_results = []
            total_persons = len(persons)
            
            for i, person in enumerate(persons):
                # Check if search was stopped
                if self.stop_search:
                    self.log_message("Search stopped by user")
                    break
                
                name = person.get('Name', 'Unknown')
                search_term = person.get('Search Term', '')
                additional_terms = person.get('Additional Terms', '')
                
                if not search_term:
                    self.log_message(f"Skipping {name}: No search term provided")
                    continue
                
                # Update progress
                progress_pct = (i / total_persons) * 100
                self.main_window.update_status(f"Searching for {name}...", progress_pct)
                
                # Log search start
                self.log_message(f"Searching for {name}: {search_term}")
                
                # Handle pausing
                while self.pause_search and not self.stop_search:
                    time.sleep(0.5)
                    self.main_window.update_status(f"Search paused at {name}...", progress_pct)
                
                if self.stop_search:
                    self.log_message("Search stopped by user")
                    break
                
                # Perform the search
                person_results = self.perform_search(
                    database, 
                    search_term, 
                    name, 
                    additional_terms, 
                    params
                )
                
                # Add results
                if person_results:
                    all_results.extend(person_results)
                    self.log_message(f"Found {len(person_results)} results for {name}")
                else:
                    self.log_message(f"No results found for {name}")
            
            # Update main window with results
            self.main_window.update_results(all_results)
            
            # Update status
            self.main_window.update_status(
                f"Search completed: {len(all_results)} results found", 100)
            
            self.log_message(f"Search completed: {len(all_results)} total results found")
        
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            self.log_message(f"Error during search: {str(e)}")
            self.main_window.update_status("Search error", 0)
        
        finally:
            # Reset button states
            self.start_button.config(state="normal")
            self.pause_button.config(state="disabled")
            self.pause_button.config(text="Pause")
            self.stop_button.config(state="disabled")
    
    def perform_search(self, database, search_term, name, additional_terms, params):
        """
        Perform search in the specified database.
        
        Args:
            database (str): Database name.
            search_term (str): Main search term.
            name (str): Person name.
            additional_terms (str): Additional search terms.
            params (dict): Search parameters.
            
        Returns:
            list: Search results.
        """
        # Check if it's a combined search
        if database == "Combined":
            return self.perform_combined_search(search_term, name, additional_terms, params)
        
        # Get database connector
        db_connector_class = DATABASE_CONNECTORS.get(database)
        if not db_connector_class:
            self.log_message(f"Unknown database: {database}")
            return []
        
        # Initialize connector with API key
        api_key = get_api_key(database, self.settings)
        connector = db_connector_class(api_key=api_key, settings=self.settings)
        
        # Construct query
        query = connector.construct_query(
            base_query=search_term,
            additional_terms=additional_terms,
            date_range=params.get('date_range'),
            language=params.get('language'),
            pub_type=params.get('pub_type'),
            field=params.get('field')
        )
        
        # Perform search
        search_params = {
            'name': name,
            'max_results': params.get('max_results', 100)
        }
        results = connector.search(query, search_params, self.log_text)
        
        return results
    
    def perform_combined_search(self, search_term, name, additional_terms, params):
        """
        Perform search in all available databases.
        
        Args:
            search_term (str): Main search term.
            name (str): Person name.
            additional_terms (str): Additional search terms.
            params (dict): Search parameters.
            
        Returns:
            list: Combined search results.
        """
        combined_results = []
        
        for db_name, db_connector_class in DATABASE_CONNECTORS.items():
            # Check if search was stopped
            if self.stop_search:
                self.log_message("Search stopped by user")
                break
            
            # Handle pausing
            while self.pause_search and not self.stop_search:
                time.sleep(0.5)
            
            if self.stop_search:
                self.log_message("Search stopped by user")
                break
            
            self.log_message(f"Searching in {db_name} for {name}")
            
            # Initialize connector with API key
            api_key = get_api_key(db_name, self.settings)
            connector = db_connector_class(api_key=api_key, settings=self.settings)
            
            # Construct query
            query = connector.construct_query(
                base_query=search_term,
                additional_terms=additional_terms,
                date_range=params.get('date_range'),
                language=params.get('language'),
                pub_type=params.get('pub_type'),
                field=params.get('field')
            )
            
            # Perform search
            search_params = {
                'name': name,
                'max_results': params.get('max_results', 100)
            }
            
            try:
                results = connector.search(query, search_params, self.log_text)
                combined_results.extend(results)
                self.log_message(f"Found {len(results)} results in {db_name} for {name}")
            except Exception as e:
                logger.error(f"Error searching {db_name}: {e}", exc_info=True)
                self.log_message(f"Error searching {db_name}: {str(e)}")
        
        return combined_results
