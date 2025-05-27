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
            # Normalisiere die Ergebnisse, um sicherzustellen, dass alle Eintru00e4ge die gleichen Schlu00fcssel haben
            all_keys = set()
            for result in results:
                all_keys.update(result.keys())
            
            normalized_results = []
            for result in results:
                normalized_result = {key: result.get(key, "") for key in all_keys}
                normalized_results.append(normalized_result)
            
            # Use pandas for better Excel formatting
            df = pd.DataFrame(normalized_results)
            
            # Filter columns if specified
            if output_columns:
                # Keep only columns that exist in the dataframe
                columns_to_keep = [col for col in output_columns if col in df.columns]
                if columns_to_keep:
                    df = df[columns_to_keep]
                else:
                    logger.warning("None of the specified output columns exist in the results. Using all columns.")
            
            # Create Excel file
            try:
                df.to_excel(filepath, index=False, sheet_name='Search Results', engine='openpyxl')
                logger.info(f"Exported {len(results)} results to Excel: {filepath}")
                return True
            except Exception as excel_e:
                logger.error(f"Error writing Excel file with pandas: {excel_e}", exc_info=True)
                # Fallback to CSV if Excel writing fails
                csv_path = filepath.replace('.xlsx', '.csv')
                logger.warning(f"Falling back to CSV export: {csv_path}")
                return export_to_csv(results, csv_path, options)
        else:
            # Fallback to CSV if pandas is not available
            logger.warning("Pandas not available. Exporting to CSV instead.")
            return export_to_csv(results, filepath.replace('.xlsx', '.csv'), options)
            
    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}", exc_info=True)
        # Try CSV as last resort
        try:
            csv_path = filepath.replace('.xlsx', '.csv')
            logger.warning(f"Attempting emergency CSV export: {csv_path}")
            return export_to_csv(results, csv_path, options)
        except Exception as csv_e:
            logger.error(f"Emergency CSV export also failed: {csv_e}", exc_info=True)
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
        # Sammle alle möglichen Schlüssel aus allen Ergebnissen
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())
        
        # Wenn output_columns angegeben sind, filtere die Schlüssel
        if output_columns:
            # Behalte nur die Spalten, die tatsächlich in den Ergebnissen existieren
            fieldnames = [col for col in output_columns if col in all_keys]
            if not fieldnames:
                logger.warning("None of the specified output columns exist in the results. Using all columns.")
                fieldnames = sorted(list(all_keys))
        else:
            # Verwende alle Schlüssel, sortiert für Konsistenz
            fieldnames = sorted(list(all_keys))
        
        # Normalisiere die Ergebnisse, damit alle die gleichen Schlüssel haben
        normalized_results = []
        for result in results:
            normalized_result = {}
            for key in fieldnames:
                normalized_result[key] = result.get(key, "")
            normalized_results.append(normalized_result)
        
        # Schreibe die CSV-Datei
        with open(filepath, 'w', newline='', encoding=encoding) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(normalized_results)
            
        logger.info(f"Exported {len(results)} results to CSV: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}", exc_info=True)
        
        # Versuche einen Fallback mit minimalen Daten
        try:
            fallback_path = f"{os.path.splitext(filepath)[0]}_fallback.csv"
            logger.warning(f"Attempting fallback CSV export with minimal data: {fallback_path}")
            
            # Extrahiere nur die wichtigsten Felder
            minimal_results = []
            for result in results:
                minimal_result = {
                    "Title": result.get("Title", ""),
                    "Authors": result.get("Authors", ""),
                    "Year": result.get("Publication Year", ""),
                    "Database": result.get("Database", "")
                }
                minimal_results.append(minimal_result)
            
            with open(fallback_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["Title", "Authors", "Year", "Database"], delimiter=',')
                writer.writeheader()
                writer.writerows(minimal_results)
                
            logger.info(f"Fallback export successful: {fallback_path}")
            return True
        except Exception as fallback_e:
            logger.error(f"Fallback CSV export also failed: {fallback_e}", exc_info=True)
            return False