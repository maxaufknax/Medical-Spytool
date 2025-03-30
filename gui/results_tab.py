"""
Results Tab

This module defines the results tab for displaying search results.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import logging
from datetime import datetime

from utils.export_manager import export_to_excel, export_to_csv, get_unique_filename

logger = logging.getLogger(__name__)

class ResultsTab:
    """
    Tab for displaying search results.
    """
    
    def __init__(self, notebook, main_window):
        """
        Initialize the results tab.
        
        Args:
            notebook (ttk.Notebook): Parent notebook.
            main_window (MainWindow): Main application window.
        """
        self.notebook = notebook
        self.main_window = main_window
        self.settings = main_window.settings
        self.results = []
        
        # Create frame
        self.frame = ttk.Frame(notebook, padding=10)
        
        # Create widgets
        self.create_widgets()
        
        logger.info("Results tab initialized")
    
    def create_widgets(self):
        """Create results tab widgets."""
        # Top controls frame
        self.controls_frame = ttk.Frame(self.frame)
        self.controls_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Search info label
        self.results_info_var = tk.StringVar(value="No results")
        results_info_label = ttk.Label(self.controls_frame, textvariable=self.results_info_var)
        results_info_label.pack(side=tk.LEFT, padx=5)
        
        # Export buttons
        ttk.Button(self.controls_frame, text="Export to Excel", command=self.export_to_excel).pack(side=tk.RIGHT, padx=2)
        ttk.Button(self.controls_frame, text="Export to CSV", command=self.export_to_csv).pack(side=tk.RIGHT, padx=2)
        
        # Filter and sort frame
        self.filter_frame = ttk.LabelFrame(self.frame, text="Filter & Sort", padding=5)
        self.filter_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Database filter
        ttk.Label(self.filter_frame, text="Database:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.db_filter_var = tk.StringVar(value="All")
        self.db_filter_combo = ttk.Combobox(self.filter_frame, textvariable=self.db_filter_var, width=15)
        self.db_filter_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        self.db_filter_combo['values'] = ['All', 'PubMed', 'DNB']
        self.db_filter_combo.bind("<<ComboboxSelected>>", self.apply_filters)
        
        # Person filter
        ttk.Label(self.filter_frame, text="Person:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.person_filter_var = tk.StringVar(value="All")
        self.person_filter_combo = ttk.Combobox(self.filter_frame, textvariable=self.person_filter_var, width=20)
        self.person_filter_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        self.person_filter_combo.bind("<<ComboboxSelected>>", self.apply_filters)
        
        # Year range filter
        ttk.Label(self.filter_frame, text="Year from:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=2)
        self.year_from_var = tk.StringVar()
        self.year_from_entry = ttk.Spinbox(self.filter_frame, from_=1900, to=2100, textvariable=self.year_from_var, width=6)
        self.year_from_entry.grid(row=0, column=5, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(self.filter_frame, text="to:").grid(row=0, column=6, sticky=tk.W, padx=5, pady=2)
        self.year_to_var = tk.StringVar()
        self.year_to_entry = ttk.Spinbox(self.filter_frame, from_=1900, to=2100, textvariable=self.year_to_var, width=6)
        self.year_to_entry.grid(row=0, column=7, sticky=tk.W, padx=5, pady=2)
        
        # Apply filters button
        ttk.Button(self.filter_frame, text="Apply Filters", command=self.apply_filters).grid(
            row=0, column=8, sticky=tk.W, padx=5, pady=2)
        
        # Reset filters button
        ttk.Button(self.filter_frame, text="Reset Filters", command=self.reset_filters).grid(
            row=0, column=9, sticky=tk.W, padx=5, pady=2)
        
        # Results treeview
        self.create_results_treeview()
    
    def create_results_treeview(self):
        """Create the results treeview."""
        # Treeview frame with scrollbars
        tree_frame = ttk.Frame(self.frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview columns
        columns = [
            "Database", "Name", "Title", "Publication Year", 
            "Authors", "Identifier", "URL", "Citation Count"
        ]
        
        # Create treeview
        self.tree = ttk.Treeview(
            tree_frame, 
            columns=columns, 
            show="headings",
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        
        # Configure scrollbars
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
        
        # Setup columns
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            width = 150  # Default width
            
            # Adjust width based on column content
            if col in ["Title", "Authors"]:
                width = 300
            elif col in ["Database", "Name", "Citation Count"]:
                width = 100
            elif col in ["Publication Year"]:
                width = 120
            
            self.tree.column(col, width=width, minwidth=50)
        
        # Pack treeview
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind double-click event
        self.tree.bind("<Double-1>", self.on_result_double_click)
    
    def update_results(self, results):
        """
        Update the displayed results.
        
        Args:
            results (list): List of result dictionaries.
        """
        self.results = results
        
        # Update info text
        if results:
            self.results_info_var.set(f"{len(results)} results found")
        else:
            self.results_info_var.set("No results")
        
        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Update filter options
        self.update_filter_options(results)
        
        # Display results
        self.display_results(results)
    
    def update_filter_options(self, results):
        """
        Update filter options based on results.
        
        Args:
            results (list): List of result dictionaries.
        """
        if not results:
            return
        
        # Extract unique databases and persons
        databases = sorted(set(r.get("Database", "") for r in results if r.get("Database")))
        persons = sorted(set(r.get("Name", "") for r in results if r.get("Name")))
        
        # Update combobox values
        self.db_filter_combo['values'] = ["All"] + databases
        self.person_filter_combo['values'] = ["All"] + persons
        
        # Set default values
        self.db_filter_var.set("All")
        self.person_filter_var.set("All")
        
        # Extract year range
        years = [int(r.get("Publication Year", "0")) for r in results 
                 if r.get("Publication Year", "").isdigit()]
        
        if years:
            min_year = min(years)
            max_year = max(years)
            
            self.year_from_var.set(str(min_year))
            self.year_to_var.set(str(max_year))
    
    def display_results(self, results):
        """
        Display results in the treeview.
        
        Args:
            results (list): List of result dictionaries.
        """
        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not results:
            return
        
        # Get visible columns
        columns = self.tree["columns"]
        
        # Insert results
        for i, result in enumerate(results):
            # Prepare row values
            row_values = []
            for col in columns:
                value = result.get(col, "")
                row_values.append(value)
            
            # Insert row
            item_id = self.tree.insert("", "end", values=row_values)
            
            # Alternate row colors
            if i % 2 == 0:
                self.tree.item(item_id, tags=("evenrow",))
            else:
                self.tree.item(item_id, tags=("oddrow",))
        
        # Configure row tags
        self.tree.tag_configure("evenrow", background="#f0f0f0")
        self.tree.tag_configure("oddrow", background="#ffffff")
    
    def apply_filters(self, event=None):
        """
        Apply filters to the results.
        
        Args:
            event: ComboboxSelected event (optional).
        """
        if not self.results:
            return
        
        # Get filter values
        db_filter = self.db_filter_var.get()
        person_filter = self.person_filter_var.get()
        
        try:
            year_from = int(self.year_from_var.get()) if self.year_from_var.get() else None
        except ValueError:
            year_from = None
        
        try:
            year_to = int(self.year_to_var.get()) if self.year_to_var.get() else None
        except ValueError:
            year_to = None
        
        # Apply filters
        filtered_results = self.results.copy()
        
        # Database filter
        if db_filter != "All":
            filtered_results = [r for r in filtered_results if r.get("Database") == db_filter]
        
        # Person filter
        if person_filter != "All":
            filtered_results = [r for r in filtered_results if r.get("Name") == person_filter]
        
        # Year range filter
        if year_from is not None:
            filtered_results = [r for r in filtered_results 
                               if r.get("Publication Year", "").isdigit() and 
                               int(r.get("Publication Year")) >= year_from]
        
        if year_to is not None:
            filtered_results = [r for r in filtered_results 
                               if r.get("Publication Year", "").isdigit() and 
                               int(r.get("Publication Year")) <= year_to]
        
        # Update info text
        self.results_info_var.set(f"{len(filtered_results)} of {len(self.results)} results displayed")
        
        # Display filtered results
        self.display_results(filtered_results)
    
    def reset_filters(self):
        """Reset all filters to default values."""
        self.db_filter_var.set("All")
        self.person_filter_var.set("All")
        
        # Reset year range
        years = [int(r.get("Publication Year", "0")) for r in self.results 
                if r.get("Publication Year", "").isdigit()]
        
        if years:
            self.year_from_var.set(str(min(years)))
            self.year_to_var.set(str(max(years)))
        else:
            self.year_from_var.set("")
            self.year_to_var.set("")
        
        # Show all results
        self.display_results(self.results)
        self.results_info_var.set(f"{len(self.results)} results displayed")
    
    def sort_by_column(self, column):
        """
        Sort results by the specified column.
        
        Args:
            column (str): Column name to sort by.
        """
        if not self.results:
            return
        
        # Get current sorting
        sorted_id = self.tree.heading(column, "text")
        
        # Determine sort order
        reverse = False
        if sorted_id.startswith("▲ "):
            # Currently sorted ascending, switch to descending
            self.tree.heading(column, text=f"▼ {column}")
            reverse = True
        elif sorted_id.startswith("▼ "):
            # Currently sorted descending, switch to ascending
            self.tree.heading(column, text=f"▲ {column}")
        else:
            # Not sorted by this column yet, default to ascending
            self.tree.heading(column, text=f"▲ {column}")
        
        # Reset other column headings
        for col in self.tree["columns"]:
            if col != column:
                if self.tree.heading(col, "text").startswith("▲ ") or self.tree.heading(col, "text").startswith("▼ "):
                    self.tree.heading(col, text=col)
        
        # Sort the results
        try:
            # Try numeric sort for year and citation count
            if column in ["Publication Year", "Citation Count"]:
                def convert_to_int(val):
                    try:
                        return int(val)
                    except (ValueError, TypeError):
                        return 0
                
                sorted_results = sorted(
                    self.results, 
                    key=lambda r: convert_to_int(r.get(column, 0)), 
                    reverse=reverse
                )
            else:
                # Default to string sort
                sorted_results = sorted(
                    self.results, 
                    key=lambda r: str(r.get(column, "")).lower(), 
                    reverse=reverse
                )
            
            # Display sorted results
            self.display_results(sorted_results)
        
        except Exception as e:
            logger.error(f"Error sorting by {column}: {e}", exc_info=True)
            messagebox.showerror("Sort Error", f"Error sorting by {column}:\n{str(e)}")
    
    def on_result_double_click(self, event):
        """
        Handle double-click on a result.
        
        Args:
            event: Double-click event.
        """
        # Get selected item
        selection = self.tree.selection()
        if not selection:
            return
        
        # Get item values
        values = self.tree.item(selection[0], "values")
        if not values:
            return
        
        # Get URL column index
        url_index = self.tree["columns"].index("URL")
        
        # Open URL if available
        url = values[url_index]
        if url and url not in ["No URL", "N/A"]:
            import webbrowser
            try:
                webbrowser.open(url)
            except Exception as e:
                logger.error(f"Error opening URL {url}: {e}", exc_info=True)
                messagebox.showerror("URL Error", f"Error opening URL:\n{str(e)}")
    
    def get_displayed_results(self):
        """
        Get currently displayed results.
        
        Returns:
            list: Currently displayed results.
        """
        # Get all item IDs in the treeview
        item_ids = self.tree.get_children()
        
        if not item_ids:
            return []
        
        # Get results based on displayed order
        displayed_results = []
        columns = self.tree["columns"]
        
        for item_id in item_ids:
            values = self.tree.item(item_id, "values")
            
            # Create result dictionary
            result = {}
            for i, col in enumerate(columns):
                if i < len(values):
                    result[col] = values[i]
            
            displayed_results.append(result)
        
        return displayed_results
    
    def export_results(self):
        """Export results (called from main menu)."""
        self.export_to_excel()
    
    def export_to_excel(self):
        """Export results to Excel file."""
        # Get currently displayed results
        results = self.get_displayed_results()
        
        if not results:
            messagebox.showinfo("No Results", "There are no results to export.")
            return
        
        # Ask for file path
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
            initialdir=self.settings.get("output_path", "./output")
        )
        
        if not file_path:
            return
        
        # Export to Excel
        if export_to_excel(results, file_path):
            messagebox.showinfo("Export Successful", f"Results exported to {file_path}")
        else:
            messagebox.showerror("Export Error", "An error occurred while exporting to Excel.")
    
    def export_to_csv(self):
        """Export results to CSV file."""
        # Get currently displayed results
        results = self.get_displayed_results()
        
        if not results:
            messagebox.showinfo("No Results", "There are no results to export.")
            return
        
        # Ask for file path
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialdir=self.settings.get("output_path", "./output")
        )
        
        if not file_path:
            return
        
        # Export to CSV
        if export_to_csv(results, file_path):
            messagebox.showinfo("Export Successful", f"Results exported to {file_path}")
        else:
            messagebox.showerror("Export Error", "An error occurred while exporting to CSV.")
