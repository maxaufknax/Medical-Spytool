"""
Analysis Tab

This module defines the analysis tab for visualizing search results.
"""

import tkinter as tk
from tkinter import ttk
import logging
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import Counter

logger = logging.getLogger(__name__)

class AnalysisTab:
    """
    Tab for analyzing and visualizing search results.
    """
    
    def __init__(self, notebook, main_window):
        """
        Initialize the analysis tab.
        
        Args:
            notebook (ttk.Notebook): Parent notebook.
            main_window (MainWindow): Main application window.
        """
        self.notebook = notebook
        self.main_window = main_window
        self.settings = main_window.settings
        self.data = []
        
        # Create frame
        self.frame = ttk.Frame(notebook, padding=10)
        
        # Create widgets
        self.create_widgets()
        
        logger.info("Analysis tab initialized")
    
    def create_widgets(self):
        """Create analysis tab widgets."""
        # Top controls frame
        self.controls_frame = ttk.Frame(self.frame)
        self.controls_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Analysis selection
        ttk.Label(self.controls_frame, text="Analysis Type:").pack(side=tk.LEFT, padx=5)
        
        self.analysis_var = tk.StringVar(value="Publications by Year")
        analysis_combo = ttk.Combobox(self.controls_frame, textvariable=self.analysis_var, width=25)
        analysis_combo.pack(side=tk.LEFT, padx=5)
        analysis_combo['values'] = [
            "Publications by Year",
            "Publications by Database",
            "Publications by Person",
            "Citation Analysis"
        ]
        analysis_combo.bind("<<ComboboxSelected>>", self.on_analysis_change)
        
        # Generate button
        ttk.Button(self.controls_frame, text="Generate", command=self.generate_analysis).pack(side=tk.LEFT, padx=5)
        
        # Results info
        self.results_info_var = tk.StringVar(value="No data to analyze")
        results_info_label = ttk.Label(self.controls_frame, textvariable=self.results_info_var)
        results_info_label.pack(side=tk.RIGHT, padx=5)
        
        # Create visualization frame
        self.viz_frame = ttk.LabelFrame(self.frame, text="Visualization", padding=10)
        self.viz_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure and canvas
        self.create_plot_area()
    
    def create_plot_area(self):
        """Create the matplotlib plot area."""
        # Create initial figure and plot
        self.fig, self.ax = plt.subplots(figsize=(10, 6), dpi=80)
        self.fig.tight_layout(pad=3)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.viz_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)
    
    def update_data(self, data):
        """
        Update the data for analysis.
        
        Args:
            data (list): Search results data.
        """
        self.data = data
        
        if data:
            self.results_info_var.set(f"{len(data)} results available for analysis")
        else:
            self.results_info_var.set("No data to analyze")
        
        # Generate analysis with default view
        self.generate_analysis()
    
    def on_analysis_change(self, event):
        """
        Handle analysis type change.
        
        Args:
            event: ComboboxSelected event.
        """
        self.generate_analysis()
    
    def generate_analysis(self):
        """Generate the selected analysis visualization."""
        if not self.data:
            # Show a message in the plot area
            self.ax.clear()
            self.ax.text(0.5, 0.5, "No data available for analysis", 
                        fontsize=14, ha='center', va='center')
            self.ax.axis('off')
            self.canvas.draw()
            return
        
        # Get selected analysis type
        analysis_type = self.analysis_var.get()
        
        # Generate selected visualization
        if analysis_type == "Publications by Year":
            self.publications_by_year()
        elif analysis_type == "Publications by Database":
            self.publications_by_database()
        elif analysis_type == "Publications by Person":
            self.publications_by_person()
        elif analysis_type == "Citation Analysis":
            self.citation_analysis()
    
    def publications_by_year(self):
        """Generate publications by year visualization."""
        # Extract publication years
        years = []
        for result in self.data:
            year = result.get("Publication Year", "")
            if year and year.isdigit():
                years.append(int(year))
        
        if not years:
            self.show_no_data_message("No publication year data available")
            return
        
        # Count publications by year
        year_counter = Counter(years)
        
        # Sort by year
        sorted_years = sorted(year_counter.items())
        years, counts = zip(*sorted_years)
        
        # Create bar chart
        self.ax.clear()
        self.ax.bar(years, counts, color='navy')
        self.ax.set_xlabel('Publication Year')
        self.ax.set_ylabel('Number of Publications')
        self.ax.set_title('Publications by Year')
        
        # Set ticks
        if len(years) > 20:
            # Show only some year labels to avoid overcrowding
            step = max(1, len(years) // 10)
            self.ax.set_xticks(years[::step])
        else:
            self.ax.set_xticks(years)
        
        self.ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Draw the figure
        self.fig.tight_layout()
        self.canvas.draw()
    
    def publications_by_database(self):
        """Generate publications by database visualization."""
        # Extract databases
        databases = [result.get("Database", "Unknown") for result in self.data]
        
        if not databases:
            self.show_no_data_message("No database data available")
            return
        
        # Count publications by database
        db_counter = Counter(databases)
        
        # Sort by count (descending)
        sorted_dbs = sorted(db_counter.items(), key=lambda x: x[1], reverse=True)
        dbs, counts = zip(*sorted_dbs)
        
        # Create bar chart
        self.ax.clear()
        bars = self.ax.bar(dbs, counts, color='lightseagreen')
        self.ax.set_xlabel('Database')
        self.ax.set_ylabel('Number of Publications')
        self.ax.set_title('Publications by Database')
        
        # Add count labels on top of bars
        for bar in bars:
            height = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width()/2., height,
                         f'{height}', ha='center', va='bottom')
        
        self.ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Draw the figure
        self.fig.tight_layout()
        self.canvas.draw()
    
    def publications_by_person(self):
        """Generate publications by person visualization."""
        # Extract persons
        persons = [result.get("Name", "Unknown") for result in self.data]
        
        if not persons:
            self.show_no_data_message("No person data available")
            return
        
        # Count publications by person
        person_counter = Counter(persons)
        
        # Sort by count (descending)
        sorted_persons = sorted(person_counter.items(), key=lambda x: x[1], reverse=True)
        persons, counts = zip(*sorted_persons)
        
        # Create bar chart
        self.ax.clear()
        
        # Handle large number of persons
        if len(persons) > 15:
            # Show only top 15 persons
            persons = persons[:15]
            counts = counts[:15]
            self.ax.set_title('Top 15 Persons by Number of Publications')
        else:
            self.ax.set_title('Publications by Person')
        
        # Create horizontal bar chart for better readability with many persons
        bars = self.ax.barh(persons, counts, color='darkgreen')
        self.ax.set_xlabel('Number of Publications')
        self.ax.set_ylabel('Person')
        
        # Add count labels
        for bar in bars:
            width = bar.get_width()
            self.ax.text(width, bar.get_y() + bar.get_height()/2.,
                         f'{width}', ha='left', va='center')
        
        self.ax.grid(axis='x', linestyle='--', alpha=0.7)
        
        # Draw the figure
        self.fig.tight_layout()
        self.canvas.draw()
    
    def citation_analysis(self):
        """Generate citation analysis visualization."""
        # Extract citation data
        citation_data = []
        for result in self.data:
            name = result.get("Name", "Unknown")
            citation_count = result.get("Citation Count", "")
            
            # Convert citation count to int
            try:
                if citation_count and citation_count not in ["N/A", "Error"]:
                    citation_count = int(citation_count)
                    citation_data.append((name, citation_count))
            except (ValueError, TypeError):
                continue
        
        if not citation_data:
            self.show_no_data_message("No citation data available")
            return
        
        # Group by person and sum citations
        person_citations = {}
        for name, count in citation_data:
            person_citations[name] = person_citations.get(name, 0) + count
        
        # Sort by citation count (descending)
        sorted_citations = sorted(person_citations.items(), key=lambda x: x[1], reverse=True)
        persons, counts = zip(*sorted_citations)
        
        # Create visualization
        self.ax.clear()
        
        # Handle large number of persons
        if len(persons) > 10:
            # Show only top 10 persons
            persons = persons[:10]
            counts = counts[:10]
            self.ax.set_title('Top 10 Persons by Citation Count')
        else:
            self.ax.set_title('Citation Analysis by Person')
        
        # Create horizontal bar chart
        bars = self.ax.barh(persons, counts, color='darkred')
        self.ax.set_xlabel('Number of Citations')
        self.ax.set_ylabel('Person')
        
        # Add count labels
        for bar in bars:
            width = bar.get_width()
            self.ax.text(width, bar.get_y() + bar.get_height()/2.,
                         f'{width}', ha='left', va='center')
        
        self.ax.grid(axis='x', linestyle='--', alpha=0.7)
        
        # Draw the figure
        self.fig.tight_layout()
        self.canvas.draw()
    
    def show_no_data_message(self, message):
        """
        Show a message in the plot area when no data is available.
        
        Args:
            message (str): Message to display.
        """
        self.ax.clear()
        self.ax.text(0.5, 0.5, message, fontsize=14, ha='center', va='center')
        self.ax.axis('off')
        self.canvas.draw()
