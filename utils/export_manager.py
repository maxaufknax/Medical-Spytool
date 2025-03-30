"""
Export Manager

This module handles exporting search results to various formats.
"""

import os
import csv
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

def export_to_excel(data, file_path, sheet_name="Search Results"):
    """
    Export data to Excel file.
    
    Args:
        data (list): List of dictionaries containing the data to export.
        file_path (str): Path to save the Excel file.
        sheet_name (str, optional): Name of the Excel sheet.
        
    Returns:
        bool: True if export was successful, False otherwise.
    """
    try:
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        
        # Make sure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write to Excel
        df.to_excel(file_path, sheet_name=sheet_name, index=False)
        
        logger.info(f"Data exported to Excel: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}", exc_info=True)
        return False

def export_to_csv(data, file_path, delimiter=','):
    """
    Export data to CSV file.
    
    Args:
        data (list): List of dictionaries containing the data to export.
        file_path (str): Path to save the CSV file.
        delimiter (str, optional): Delimiter to use in the CSV file.
        
    Returns:
        bool: True if export was successful, False otherwise.
    """
    try:
        # Make sure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Get all possible keys from all dictionaries
        fieldnames = set()
        for item in data:
            fieldnames.update(item.keys())
        fieldnames = sorted(list(fieldnames))
        
        # Write to CSV
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"Data exported to CSV: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}", exc_info=True)
        return False

def save_person_list(persons, file_path):
    """
    Save person list to a CSV file.
    
    Args:
        persons (list): List of person dictionaries.
        file_path (str): Path to save the CSV file.
        
    Returns:
        bool: True if save was successful, False otherwise.
    """
    try:
        # Make sure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Extract fieldnames from the first person
        if not persons:
            fieldnames = ["Name", "Search Term", "Additional Terms"]
        else:
            fieldnames = list(persons[0].keys())
        
        # Write to CSV
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(persons)
        
        logger.info(f"Person list saved to: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving person list: {e}", exc_info=True)
        return False

def load_person_list(file_path):
    """
    Load person list from a CSV file.
    
    Args:
        file_path (str): Path to the CSV file.
        
    Returns:
        list: List of person dictionaries or empty list if an error occurred.
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"Person list file does not exist: {file_path}")
            return []
        
        persons = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                persons.append(dict(row))
        
        logger.info(f"Person list loaded from: {file_path}")
        return persons
    except Exception as e:
        logger.error(f"Error loading person list: {e}", exc_info=True)
        return []

def get_unique_filename(base_path, base_name, extension):
    """
    Generate a unique filename by appending a timestamp.
    
    Args:
        base_path (str): Base directory path.
        base_name (str): Base filename.
        extension (str): File extension.
        
    Returns:
        str: Unique filepath.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(base_path, f"{base_name}_{timestamp}.{extension}")
