#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Utility functions module
This module provides utility functions for MedicalSpy.
"""

import os
import csv
import pandas as pd
import logging
from datetime import datetime
from io import StringIO

logger = logging.getLogger("MedicalSpy")

# Global log storage
_log_messages = []

def log_message(message, level="INFO", save_to_db=True):
    """
    Log a message to the global log.
    
    Args:
        message (str): The message to log
        level (str, optional): The log level (INFO, WARNING, ERROR)
        save_to_db (bool, optional): Whether to save the log message to the database
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {level}: {message}"
    _log_messages.append(full_msg)
    
    if level == "INFO":
        logger.info(message)
    elif level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)
        
    # Save to database if requested
    if save_to_db:
        try:
            # Import here to avoid circular imports
            from backend.models import LogEntry, db
            from flask import current_app
            
            # Only save to DB if within app context
            if current_app:
                with current_app.app_context():
                    LogEntry.add_log(message, level)
        except Exception as e:
            logger.error(f"Failed to save log to database: {e}")

def get_log_messages(include_db_logs=True):
    """
    Get all log messages.
    
    Args:
        include_db_logs (bool, optional): Whether to include logs from the database
        
    Returns:
        list: List of log messages
    """
    logs = _log_messages.copy()
    
    if include_db_logs:
        try:
            # Import here to avoid circular imports
            from backend.models import LogEntry
            from flask import current_app
            
            # Only get DB logs if within app context
            if current_app:
                with current_app.app_context():
                    db_logs = LogEntry.get_logs()
                    logs.extend(db_logs)
        except:
            # If there's an error, just return in-memory logs
            pass
    
    return logs

def clear_log_messages():
    """Clear all log messages."""
    global _log_messages
    _log_messages = []

def generate_filename(unique=False, base_name="medicalspy_export", extension="csv"):
    """
    Generate a filename for exporting results.
    
    Args:
        unique (bool, optional): Whether to include timestamp for uniqueness
        base_name (str, optional): Base name for the file
        extension (str, optional): File extension
        
    Returns:
        str: The generated filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if unique:
        return f"{base_name}_{timestamp}.{extension}"
    else:
        return f"{base_name}.{extension}"

def export_to_csv(data, output_file):
    """
    Export data to a CSV file.
    
    Args:
        data (list): List of dictionaries to export
        output_file: File-like object to write to
    """
    if not data:
        return
        
    # Get field names from the first item
    fieldnames = list(data[0].keys())
    
    # Write CSV
    writer = csv.DictWriter(output_file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)

def export_to_excel(data, output_file):
    """
    Export data to an Excel file.
    
    Args:
        data (list): List of dictionaries to export
        output_file: File-like object to write to
    """
    if not data:
        return
        
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Write Excel
    df.to_excel(output_file, index=False)

def safe_get(dictionary, key, default=""):
    """
    Safely get a value from a dictionary.
    
    Args:
        dictionary (dict): The dictionary to get the value from
        key (str): The key to get
        default (any, optional): Default value if key doesn't exist
        
    Returns:
        any: The value or default
    """
    if key in dictionary:
        return dictionary[key]
    return default

def flatten_nested_dict(nested_dict, prefix=""):
    """
    Flatten a nested dictionary.
    
    Args:
        nested_dict (dict): The nested dictionary to flatten
        prefix (str, optional): Prefix for keys
        
    Returns:
        dict: Flattened dictionary
    """
    flattened = {}
    
    for key, value in nested_dict.items():
        new_key = f"{prefix}{key}" if prefix else key
        
        if isinstance(value, dict):
            flattened.update(flatten_nested_dict(value, f"{new_key}_"))
        else:
            flattened[new_key] = value
            
    return flattened
