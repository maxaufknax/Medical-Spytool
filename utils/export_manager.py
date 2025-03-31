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

def export_to_excel(results, filepath, options=None):
    """
    Export search results to Excel file with advanced formatting options.
    
    Args:
        results (list): List of dictionaries containing search results.
        filepath (str): Path to save the Excel file.
        options (dict, optional): Export options including:
            - formatting (bool): Whether to apply fancy formatting
            - autofilter (bool): Whether to add autofilters to column headers
            - freeze_header (bool): Whether to freeze the header row
            - output_columns (list): List of columns to include in export
        
    Returns:
        bool: Success status.
    """
    if not results:
        logger.warning("No results to export to Excel.")
        return False
    
    # Set default options if not provided
    if options is None:
        options = {}
    
    formatting = options.get('formatting', True)
    autofilter = options.get('autofilter', True)
    freeze_header = options.get('freeze_header', True)
    output_columns = options.get('output_columns', [])
    
    try:
        if PANDAS_AVAILABLE:
            # Use pandas for better Excel formatting
            df = pd.DataFrame(results)
            
            # Filter columns if specified
            if output_columns:
                # Keep only columns that exist in the dataframe
                columns_to_keep = [col for col in output_columns if col in df.columns]
                if columns_to_keep:
                    df = df[columns_to_keep]
            
            # Create a writer with options
            writer = pd.ExcelWriter(filepath, engine='openpyxl')
            
            # Write the data
            df.to_excel(writer, index=False, sheet_name='Search Results')
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Search Results']
            
            if formatting:
                # Define some styles
                header_font = workbook.add_format({'bold': True, 'bg_color': '#0D6EFD', 'font_color': '#FFFFFF'})
                alt_row_color = workbook.add_format({'bg_color': '#F8F9FA'})
                
                # Apply header style
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_font)
                
                # Add zebra striping to rows
                for row_num in range(1, len(df) + 1, 2):
                    worksheet.set_row(row_num, None, alt_row_color)
            
            # Auto-adjust columns' width
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
                col_idx = df.columns.get_loc(column) + 1
                if hasattr(worksheet, 'column_dimensions'):
                    # Openpyxl style
                    worksheet.column_dimensions[chr(64 + col_idx)].width = min(column_width, 60)
                else:
                    # XlsxWriter style
                    worksheet.set_column(col_idx - 1, col_idx - 1, min(column_width, 60))
            
            # Add autofilter if requested
            if autofilter and hasattr(worksheet, 'auto_filter'):
                worksheet.auto_filter.ref = f"A1:{chr(64 + len(df.columns))}{len(df) + 1}"
            
            # Freeze header row if requested
            if freeze_header and hasattr(worksheet, 'freeze_panes'):
                worksheet.freeze_panes = 'A2'
            
            writer.close()
            logger.info(f"Exported {len(results)} results to Excel: {filepath}")
            return True
        else:
            # Fallback to CSV if pandas is not available
            logger.warning("Pandas not available. Exporting to CSV instead.")
            return export_to_csv(results, filepath.replace('.xlsx', '.csv'), options)
            
    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}", exc_info=True)
        return False

def export_to_csv(results, filepath, options=None):
    """
    Export search results to CSV file.
    
    Args:
        results (list): List of dictionaries containing search results.
        filepath (str): Path to save the CSV file.
        options (dict, optional): Export options including:
            - delimiter (str): CSV delimiter character (default: ',')
            - encoding (str): File encoding (default: 'utf-8')
            - output_columns (list): List of columns to include in export
        
    Returns:
        bool: Success status.
    """
    if not results:
        logger.warning("No results to export to CSV.")
        return False
    
    # Set default options if not provided
    if options is None:
        options = {}
    
    delimiter = options.get('delimiter', ',')
    encoding = options.get('encoding', 'utf-8')
    output_columns = options.get('output_columns', [])
    
    try:
        # Process results based on output_columns
        processed_results = []
        
        if output_columns:
            # Filter results to include only specified columns
            for result in results:
                filtered_result = {}
                for column in output_columns:
                    if column in result:
                        filtered_result[column] = result[column]
                processed_results.append(filtered_result)
            
            # Get fieldnames from the columns that actually exist
            if processed_results:
                fieldnames = list(processed_results[0].keys())
            else:
                # If no columns matched, use original results
                processed_results = results
                fieldnames = list(results[0].keys())
        else:
            # Use all columns
            processed_results = results
            fieldnames = list(results[0].keys())
        
        with open(filepath, 'w', newline='', encoding=encoding) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(processed_results)
            
        logger.info(f"Exported {len(results)} results to CSV: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}", exc_info=True)
        return False