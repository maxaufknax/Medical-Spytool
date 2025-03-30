"""
Export Manager

This module provides functions for exporting search results to various formats.
"""

import os
import csv
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("Pandas not available. Excel export will be limited.")

def get_unique_filename(base_path, extension, use_unique=True):
    """
    Generate a unique filename by appending a timestamp.
    
    Args:
        base_path (str): Base file path.
        extension (str): File extension (without dot).
        use_unique (bool): Whether to add timestamp to ensure uniqueness.
        
    Returns:
        str: Unique file path.
    """
    # Strip extension if included
    if base_path.lower().endswith(f".{extension.lower()}"):
        base_path = base_path[:-len(extension)-1]
    
    if use_unique:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{base_path}_{timestamp}.{extension}"
    else:
        return f"{base_path}.{extension}"

def export_to_excel(results, filepath):
    """
    Export search results to Excel file.
    
    Args:
        results (list): List of dictionaries containing search results.
        filepath (str): Path to save the Excel file.
        
    Returns:
        bool: Success status.
    """
    if not results:
        logger.warning("No results to export to Excel.")
        return False
    
    try:
        if PANDAS_AVAILABLE:
            # Use pandas for better Excel formatting
            df = pd.DataFrame(results)
            
            # Create a writer with options
            writer = pd.ExcelWriter(filepath, engine='openpyxl')
            
            # Write the data
            df.to_excel(writer, index=False, sheet_name='Search Results')
            
            # Auto-adjust columns' width
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
                col_idx = df.columns.get_loc(column) + 1
                writer.sheets['Search Results'].column_dimensions[chr(64 + col_idx)].width = min(column_width, 60)
            
            writer.close()
            logger.info(f"Exported {len(results)} results to Excel: {filepath}")
            return True
        else:
            # Fallback to CSV if pandas is not available
            logger.warning("Pandas not available. Exporting to CSV instead.")
            return export_to_csv(results, filepath.replace('.xlsx', '.csv'))
            
    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}", exc_info=True)
        return False

def export_to_csv(results, filepath):
    """
    Export search results to CSV file.
    
    Args:
        results (list): List of dictionaries containing search results.
        filepath (str): Path to save the CSV file.
        
    Returns:
        bool: Success status.
    """
    if not results:
        logger.warning("No results to export to CSV.")
        return False
    
    try:
        # Get fieldnames from the first result
        fieldnames = list(results[0].keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
            
        logger.info(f"Exported {len(results)} results to CSV: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}", exc_info=True)
        return False