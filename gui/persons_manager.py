"""
Persons Manager

This module defines a class for managing persons and their search terms.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import logging
from utils.export_manager import save_person_list, load_person_list

logger = logging.getLogger(__name__)

class PersonsManager:
    """
    Component for managing persons and their search terms.
    """
    
    def __init__(self, parent, settings=None, database_options=None):
        """
        Initialize the persons manager.
        
        Args:
            parent (ttk.Frame): Parent frame.
            settings (dict, optional): Application settings.
            database_options (tk.StringVar, optional): Database selection variable.
        """
        self.parent = parent
        self.settings = settings or {}
        self.database_options = database_options
        self.persons = []
        self.editing_person_index = None
        
        # Create person management frame
        self.persons_frame = ttk.LabelFrame(parent, text="Person Management", padding=5)
        self.persons_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Create widgets
        self.create_widgets()
        
        # Load persons from default file if it exists
        self.load_persons()
        
        logger.info("Persons manager initialized")
    
    def create_widgets(self):
        """Create person management widgets."""
        # Create top part for person entry
        self.create_person_entry()
        
        # Create bottom part for person list
        self.create_person_list()
    
    def create_person_entry(self):
        """Create widgets for entering person details."""
        # Frame for person input
        person_input_frame = ttk.Frame(self.persons_frame)
        person_input_frame.pack(fill=tk.X, pady=5)
        
        # Name
        ttk.Label(person_input_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(person_input_frame, textvariable=self.name_var, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Search term
        ttk.Label(person_input_frame, text="Search Term:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.search_term_var = tk.StringVar()
        search_term_entry = ttk.Entry(person_input_frame, textvariable=self.search_term_var, width=30)
        search_term_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Additional terms
        ttk.Label(person_input_frame, text="Additional Terms:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.additional_terms_var = tk.StringVar()
        additional_terms_entry = ttk.Entry(person_input_frame, textvariable=self.additional_terms_var, width=70)
        additional_terms_entry.grid(row=1, column=1, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=2)
        
        # Buttons frame
        buttons_frame = ttk.Frame(person_input_frame)
        buttons_frame.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=5)
        
        # Add/Update button
        self.add_button = ttk.Button(buttons_frame, text="Add Person", command=self.add_person, width=15)
        self.add_button.pack(side=tk.LEFT, padx=2)
        
        # Clear button
        clear_button = ttk.Button(buttons_frame, text="Clear", command=self.clear_person_form, width=15)
        clear_button.pack(side=tk.LEFT, padx=2)
        
        # Load/Save buttons
        load_button = ttk.Button(buttons_frame, text="Load List", command=self.load_persons, width=15)
        load_button.pack(side=tk.LEFT, padx=2)
        
        save_button = ttk.Button(buttons_frame, text="Save List", command=self.save_persons, width=15)
        save_button.pack(side=tk.LEFT, padx=2)
    
    def create_person_list(self):
        """Create widgets for displaying person list."""
        # Frame for person list with scrollbar
        list_frame = ttk.Frame(self.persons_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a frame for the Treeview and scrollbar
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create Treeview for persons
        self.persons_tree = ttk.Treeview(
            tree_frame,
            columns=("Name", "Search Term", "Additional Terms"),
            show="headings",
            selectmode="browse",
            height=5
        )
        self.persons_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbar
        scrollbar.config(command=self.persons_tree.yview)
        self.persons_tree.config(yscrollcommand=scrollbar.set)
        
        # Configure columns
        self.persons_tree.heading("Name", text="Name", anchor=tk.W)
        self.persons_tree.heading("Search Term", text="Search Term", anchor=tk.W)
        self.persons_tree.heading("Additional Terms", text="Additional Terms", anchor=tk.W)
        
        self.persons_tree.column("Name", width=150, minwidth=100)
        self.persons_tree.column("Search Term", width=200, minwidth=150)
        self.persons_tree.column("Additional Terms", width=300, minwidth=200)
        
        # Bind select event
        self.persons_tree.bind("<<TreeviewSelect>>", self.on_person_select)
        
        # Selection and action buttons
        selection_frame = ttk.Frame(list_frame)
        selection_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        
        # Selection buttons
        select_all_button = ttk.Button(selection_frame, text="Select All", command=self.select_all_persons, width=12)
        select_all_button.pack(pady=2)
        
        deselect_all_button = ttk.Button(selection_frame, text="Deselect All", command=self.deselect_all_persons, width=12)
        deselect_all_button.pack(pady=2)
        
        # Action buttons
        edit_button = ttk.Button(selection_frame, text="Edit", command=self.edit_person, width=12)
        edit_button.pack(pady=2)
        
        delete_button = ttk.Button(selection_frame, text="Delete", command=self.delete_person, width=12)
        delete_button.pack(pady=2)
        
        # Checkboxes for selection
        self.selection_vars = {}
        self.selection_frame = ttk.Frame(self.persons_frame)
        self.selection_frame.pack(fill=tk.X, pady=5)
    
    def refresh_person_list(self):
        """Refresh the person list display."""
        # Clear the tree
        for item in self.persons_tree.get_children():
            self.persons_tree.delete(item)
        
        # Clear selection checkboxes
        for widget in self.selection_frame.winfo_children():
            widget.destroy()
        
        self.selection_vars = {}
        
        # Add persons to tree
        for i, person in enumerate(self.persons):
            self.persons_tree.insert(
                "", 
                "end", 
                values=(
                    person.get("Name", ""), 
                    person.get("Search Term", ""), 
                    person.get("Additional Terms", "")
                )
            )
            
            # Add selection checkbox
            var = tk.BooleanVar(value=False)
            self.selection_vars[i] = var
            
            # Arrange checkboxes in rows of 5
            row = i // 5
            col = i % 5
            
            cb = ttk.Checkbutton(
                self.selection_frame, 
                text=person.get("Name", f"Person {i+1}"),
                variable=var
            )
            cb.grid(row=row, column=col, sticky=tk.W, padx=5)
    
    def add_person(self):
        """Add or update a person in the list."""
        name = self.name_var.get().strip()
        search_term = self.search_term_var.get().strip()
        additional_terms = self.additional_terms_var.get().strip()
        
        if not name:
            messagebox.showwarning("Missing Name", "Please enter a name for the person.")
            return
        
        if not search_term:
            messagebox.showwarning("Missing Search Term", "Please enter a search term for the person.")
            return
        
        person = {
            "Name": name,
            "Search Term": search_term,
            "Additional Terms": additional_terms
        }
        
        if self.editing_person_index is not None:
            # Update existing person
            self.persons[self.editing_person_index] = person
            self.editing_person_index = None
            self.add_button.config(text="Add Person")
        else:
            # Add new person
            self.persons.append(person)
        
        # Clear form and refresh list
        self.clear_person_form()
        self.refresh_person_list()
        
        logger.info(f"Person added/updated: {name}")
    
    def clear_person_form(self):
        """Clear the person entry form."""
        self.name_var.set("")
        self.search_term_var.set("")
        self.additional_terms_var.set("")
        self.editing_person_index = None
        self.add_button.config(text="Add Person")
    
    def on_person_select(self, event):
        """
        Handle person selection in the tree.
        
        Args:
            event: TreeviewSelect event.
        """
        selection = self.persons_tree.selection()
        if not selection:
            return
        
        # Get selected item index
        item = selection[0]
        item_index = self.persons_tree.index(item)
        
        # Get person data
        if 0 <= item_index < len(self.persons):
            person = self.persons[item_index]
            
            # Fill form with selected person data
            self.name_var.set(person.get("Name", ""))
            self.search_term_var.set(person.get("Search Term", ""))
            self.additional_terms_var.set(person.get("Additional Terms", ""))
            
            # Set editing index
            self.editing_person_index = item_index
            self.add_button.config(text="Update Person")
    
    def edit_person(self):
        """Edit the selected person."""
        selection = self.persons_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a person to edit.")
            return
        
        # Trigger the selection event
        self.on_person_select(None)
    
    def delete_person(self):
        """Delete the selected person."""
        selection = self.persons_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a person to delete.")
            return
        
        # Get selected item index
        item = selection[0]
        item_index = self.persons_tree.index(item)
        
        # Confirm deletion
        if 0 <= item_index < len(self.persons):
            person = self.persons[item_index]
            name = person.get("Name", f"Person {item_index+1}")
            
            if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete {name}?"):
                # Delete person
                del self.persons[item_index]
                
                # Clear form if editing the deleted person
                if self.editing_person_index == item_index:
                    self.clear_person_form()
                elif self.editing_person_index is not None and self.editing_person_index > item_index:
                    # Adjust editing index if needed
                    self.editing_person_index -= 1
                
                # Refresh list
                self.refresh_person_list()
                
                logger.info(f"Person deleted: {name}")
    
    def select_all_persons(self):
        """Select all persons."""
        for var in self.selection_vars.values():
            var.set(True)
    
    def deselect_all_persons(self):
        """Deselect all persons."""
        for var in self.selection_vars.values():
            var.set(False)
    
    def get_selected_persons(self):
        """
        Get list of selected persons.
        
        Returns:
            list: Selected person dictionaries.
        """
        selected = []
        for i, var in self.selection_vars.items():
            if var.get() and i < len(self.persons):
                selected.append(self.persons[i])
        return selected
    
    def save_persons(self):
        """Save the person list to a file."""
        if not self.persons:
            messagebox.showinfo("No Persons", "There are no persons to save.")
            return
        
        # Get file path
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialdir=self.settings.get("person_list_path", "./person_lists")
        )
        
        if not file_path:
            return
        
        # Save person list
        if save_person_list(self.persons, file_path):
            messagebox.showinfo("Saved", f"Person list saved to {file_path}")
            logger.info(f"Person list saved to {file_path}")
        else:
            messagebox.showerror("Error", "An error occurred while saving the person list.")
    
    def load_persons(self, file_path=None):
        """
        Load person list from a file.
        
        Args:
            file_path (str, optional): Path to the file to load from.
        """
        if file_path is None:
            # Ask for file path
            file_path = filedialog.askopenfilename(
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
                initialdir=self.settings.get("person_list_path", "./person_lists")
            )
        
        if not file_path or not os.path.exists(file_path):
            return
        
        # Load person list
        loaded_persons = load_person_list(file_path)
        
        if loaded_persons:
            # Ask whether to replace or append
            if self.persons:
                if messagebox.askyesno("Load Persons", "Do you want to replace the existing persons?"):
                    self.persons = loaded_persons
                else:
                    # Append, avoiding duplicates
                    existing_names = {p.get("Name", "") for p in self.persons}
                    for person in loaded_persons:
                        name = person.get("Name", "")
                        if name and name not in existing_names:
                            self.persons.append(person)
                            existing_names.add(name)
            else:
                self.persons = loaded_persons
            
            # Refresh list
            self.refresh_person_list()
            
            messagebox.showinfo("Loaded", f"Person list loaded from {file_path}")
            logger.info(f"Person list loaded from {file_path}")
        else:
            messagebox.showwarning("Empty File", "No persons found in the selected file.")

