"""
Enhanced GUI Components for Medical Spytool v1.4-beta

This module provides advanced GUI components with real-time updates,
progress tracking, and enhanced user interaction features.

Features:
- Real-time Progress Updates with estimated time remaining
- Cancellable Searches with proper cleanup
- Result Streaming (results appear during search)
- Enhanced Error Messages with solutions
- Cache Statistics Display
- Performance Monitoring
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import time
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RealTimeProgressDialog:
    """Advanced progress dialog with real-time updates."""
    
    def __init__(self, parent, title="Search Progress"):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x300")
        self.dialog.resizable(False, False)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.center_dialog()
        
        # Progress tracking
        self.start_time = time.time()
        self.is_cancelled = False
        self.cancel_callback: Optional[Callable] = None
        
        self.create_widgets()
    
    def center_dialog(self):
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """Create dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Initializing search...", 
                                     font=('Arial', 11, 'bold'))
        self.status_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var,
                                          mode='determinate', length=400)
        self.progress_bar.pack(pady=(0, 10))
        
        # Progress percentage
        self.percentage_label = ttk.Label(main_frame, text="0%")
        self.percentage_label.pack()
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding=10)
        stats_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Create statistics grid
        self.stats_labels = {}
        stats_info = [
            ("Completed Queries:", "completed"),
            ("Successful Queries:", "successful"),
            ("Failed Queries:", "failed"),
            ("Cache Hits:", "cache_hits"),
            ("Success Rate:", "success_rate"),
            ("Time Remaining:", "time_remaining")
        ]
        
        for i, (label_text, key) in enumerate(stats_info):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(stats_frame, text=label_text).grid(row=row, column=col, 
                                                        sticky=tk.W, padx=(0, 5))
            
            self.stats_labels[key] = ttk.Label(stats_frame, text="0", 
                                             font=('Arial', 9, 'bold'))
            self.stats_labels[key].grid(row=row, column=col+1, sticky=tk.W, padx=(0, 20))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(20, 0))
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel Search",
                                       command=self.cancel_search)
        self.cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.details_button = ttk.Button(button_frame, text="Show Details",
                                        command=self.show_details)
        self.details_button.pack(side=tk.LEFT)
        
        # Details text (initially hidden)
        self.details_frame = ttk.Frame(main_frame)
        
        self.details_text = tk.Text(self.details_frame, height=8, width=60,
                                   font=('Consolas', 9))
        details_scrollbar = ttk.Scrollbar(self.details_frame, orient=tk.VERTICAL,
                                         command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.details_visible = False
    
    def update_progress(self, progress_info):
        """Update progress display."""
        try:
            # Handle different progress info formats
            if hasattr(progress_info, 'current_operation'):
                # SearchProgress object
                self.status_label.config(text=progress_info.current_operation)
                self.progress_var.set(progress_info.progress_percentage)
                self.percentage_label.config(text=f"{progress_info.progress_percentage:.1f}%")
                
                self.stats_labels["completed"].config(text=str(progress_info.completed_queries))
                self.stats_labels["successful"].config(text=str(progress_info.successful_queries))
                self.stats_labels["failed"].config(text=str(progress_info.failed_queries))
                self.stats_labels["cache_hits"].config(text=str(progress_info.cached_hits))
                self.stats_labels["success_rate"].config(text=f"{progress_info.success_rate:.1f}%")
                
                if progress_info.estimated_time_remaining > 0:
                    time_str = self.format_time(progress_info.estimated_time_remaining)
                else:
                    time_str = "Calculating..."
                self.stats_labels["time_remaining"].config(text=time_str)
            else:
                # Simple dict format
                self.status_label.config(text=progress_info.get('message', 'Processing...'))
                if 'percentage' in progress_info:
                    self.progress_var.set(progress_info['percentage'])
                    self.percentage_label.config(text=f"{progress_info['percentage']:.1f}%")
            
            # Add to details log
            if self.details_visible:
                timestamp = datetime.now().strftime("%H:%M:%S")
                message = getattr(progress_info, 'current_operation', progress_info.get('message', 'Processing...'))
                self.details_text.insert(tk.END, f"[{timestamp}] {message}\n")
                self.details_text.see(tk.END)
            
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
    
    def format_time(self, seconds: float) -> str:
        """Format time in a human-readable way."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes:.0f}m {secs:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h {minutes:.0f}m"
    
    def cancel_search(self):
        """Cancel the search operation."""
        if not self.is_cancelled and self.cancel_callback:
            self.is_cancelled = True
            self.cancel_callback()
            self.cancel_button.config(text="Cancelling...", state=tk.DISABLED)
            self.status_label.config(text="Cancelling search...")
    
    def show_details(self):
        """Toggle details view."""
        if self.details_visible:
            self.details_frame.pack_forget()
            self.details_button.config(text="Show Details")
            self.dialog.geometry("500x300")
        else:
            self.details_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
            self.details_button.config(text="Hide Details")
            self.dialog.geometry("500x500")
        
        self.details_visible = not self.details_visible
    
    def complete(self, success: bool = True):
        """Mark operation as complete."""
        if success:
            self.status_label.config(text="Search completed successfully!")
            self.cancel_button.config(text="Close", state=tk.NORMAL)
            self.cancel_button.config(command=self.close)
        else:
            self.status_label.config(text="Search failed or was cancelled.")
            self.cancel_button.config(text="Close", state=tk.NORMAL)
            self.cancel_button.config(command=self.close)
    
    def close(self):
        """Close the dialog."""
        self.dialog.destroy()
    
    def set_cancel_callback(self, callback: Callable):
        """Set the callback for cancellation."""
        self.cancel_callback = callback


class EnhancedErrorDialog:
    """Enhanced error dialog with solutions and details."""
    
    def __init__(self, parent, title: str, error_message: str, 
                 error_details: str = None, suggested_solutions: List[str] = None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x400")
        self.dialog.resizable(True, True)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.error_message = error_message
        self.error_details = error_details or ""
        self.suggested_solutions = suggested_solutions or []
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create error dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Error icon and message
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Error message
        error_label = ttk.Label(header_frame, text=self.error_message,
                               font=('Arial', 11, 'bold'), foreground='red')
        error_label.pack(anchor=tk.W)
        
        # Notebook for details and solutions
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Solutions tab
        if self.suggested_solutions:
            solutions_frame = ttk.Frame(notebook)
            notebook.add(solutions_frame, text="Suggested Solutions")
            
            solutions_text = tk.Text(solutions_frame, wrap=tk.WORD, 
                                   font=('Arial', 10))
            solutions_scrollbar = ttk.Scrollbar(solutions_frame, orient=tk.VERTICAL,
                                              command=solutions_text.yview)
            solutions_text.configure(yscrollcommand=solutions_scrollbar.set)
            
            solutions_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            solutions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Add solutions
            for i, solution in enumerate(self.suggested_solutions, 1):
                solutions_text.insert(tk.END, f"{i}. {solution}\n\n")
            
            solutions_text.config(state=tk.DISABLED)
        
        # Details tab
        if self.error_details:
            details_frame = ttk.Frame(notebook)
            notebook.add(details_frame, text="Technical Details")
            
            details_text = tk.Text(details_frame, wrap=tk.WORD, 
                                 font=('Consolas', 9))
            details_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL,
                                            command=details_text.yview)
            details_text.configure(yscrollcommand=details_scrollbar.set)
            
            details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            details_text.insert(tk.END, self.error_details)
            details_text.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="OK", 
                  command=self.dialog.destroy).pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="Copy Error", 
                  command=self.copy_error).pack(side=tk.RIGHT, padx=(0, 10))
    
    def copy_error(self):
        """Copy error information to clipboard."""
        error_info = f"Error: {self.error_message}\n\n"
        
        if self.suggested_solutions:
            error_info += "Suggested Solutions:\n"
            for i, solution in enumerate(self.suggested_solutions, 1):
                error_info += f"{i}. {solution}\n"
            error_info += "\n"
        
        if self.error_details:
            error_info += f"Technical Details:\n{self.error_details}"
        
        self.dialog.clipboard_clear()
        self.dialog.clipboard_append(error_info)
        
        messagebox.showinfo("Copied", "Error information copied to clipboard.")


def show_enhanced_error(parent, title: str, error_message: str, 
                       error_details: str = None, suggested_solutions: List[str] = None):
    """Show enhanced error dialog."""
    EnhancedErrorDialog(parent, title, error_message, error_details, suggested_solutions)