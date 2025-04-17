"""
Utility functions for the SciPub Explorer application

This module contains helper functions for export, data processing, and other utilities.
"""
import os
import csv
import json
import logging
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import QFileDialog, QMessageBox

logger = logging.getLogger(__name__)

def export_to_csv(parent, data, default_filename="scipub_results.csv"):
    """
    Export data to CSV file
    
    Args:
        parent: Parent widget for file dialog
        data (list): List of dictionaries containing the data
        default_filename (str): Default filename for the export
        
    Returns:
        bool: True if export was successful, False otherwise
    """
    if not data:
        QMessageBox.warning(parent, "Export Error", "No data to export!")
        return False
    
    try:
        # Ask for file location
        file_path, _ = QFileDialog.getSaveFileName(
            parent, 
            "Export to CSV",
            os.path.join(os.path.expanduser("~"), default_filename),
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return False  # User cancelled
            
        # Ensure the file has the correct extension
        if not file_path.lower().endswith('.csv'):
            file_path += '.csv'
        
        # Write to CSV
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            # Get fieldnames from the first dict
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                # Handle nested lists (like authors)
                row_copy = row.copy()
                for key, value in row_copy.items():
                    if isinstance(value, list):
                        row_copy[key] = '; '.join(value)
                writer.writerow(row_copy)
        
        logger.info(f"Data exported to CSV: {file_path}")
        QMessageBox.information(parent, "Export Successful", f"Data exported to {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        QMessageBox.critical(parent, "Export Error", f"Failed to export data: {str(e)}")
        return False

def export_to_excel(parent, data, default_filename="scipub_results.xlsx"):
    """
    Export data to Excel file
    
    Args:
        parent: Parent widget for file dialog
        data (list): List of dictionaries containing the data
        default_filename (str): Default filename for the export
        
    Returns:
        bool: True if export was successful, False otherwise
    """
    if not data:
        QMessageBox.warning(parent, "Export Error", "No data to export!")
        return False
    
    try:
        # Ask for file location
        file_path, _ = QFileDialog.getSaveFileName(
            parent, 
            "Export to Excel",
            os.path.join(os.path.expanduser("~"), default_filename),
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if not file_path:
            return False  # User cancelled
            
        # Ensure the file has the correct extension
        if not file_path.lower().endswith('.xlsx'):
            file_path += '.xlsx'
        
        # Convert data to pandas DataFrame
        df = pd.DataFrame(data)
        
        # Handle nested lists (like authors)
        for column in df.columns:
            if df[column].apply(lambda x: isinstance(x, list)).any():
                df[column] = df[column].apply(lambda x: '; '.join(x) if isinstance(x, list) else x)
        
        # Write to Excel
        df.to_excel(file_path, index=False, engine='openpyxl')
        
        logger.info(f"Data exported to Excel: {file_path}")
        QMessageBox.information(parent, "Export Successful", f"Data exported to {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}")
        QMessageBox.critical(parent, "Export Error", f"Failed to export data: {str(e)}")
        return False

def format_search_query(query_terms, database):
    """
    Format a search query for a specific database
    
    Args:
        query_terms (dict): Dictionary of search terms
        database (str): Database name
        
    Returns:
        str: Formatted query string
    """
    if database == "pubmed":
        return format_pubmed_query(query_terms)
    elif database == "scopus":
        return format_scopus_query(query_terms)
    elif database == "webofscience":
        return format_wos_query(query_terms)
    elif database == "dnb":
        return format_dnb_query(query_terms)
    else:
        return query_terms.get("general", "")

def format_pubmed_query(query_terms):
    """Format query for PubMed"""
    parts = []
    
    if "general" in query_terms and query_terms["general"]:
        parts.append(f"{query_terms['general']}")
    
    if "author" in query_terms and query_terms["author"]:
        parts.append(f"{query_terms['author']}[Author]")
    
    if "title" in query_terms and query_terms["title"]:
        parts.append(f"{query_terms['title']}[Title]")
    
    if "journal" in query_terms and query_terms["journal"]:
        parts.append(f"{query_terms['journal']}[Journal]")
    
    if "affiliation" in query_terms and query_terms["affiliation"]:
        parts.append(f"{query_terms['affiliation']}[Affiliation]")
    
    if "doi" in query_terms and query_terms["doi"]:
        parts.append(f"{query_terms['doi']}[DOI]")
    
    return " AND ".join(parts)

def format_scopus_query(query_terms):
    """Format query for Scopus"""
    parts = []
    
    if "general" in query_terms and query_terms["general"]:
        parts.append(f"ALL({query_terms['general']})")
    
    if "author" in query_terms and query_terms["author"]:
        parts.append(f"AUTHOR-NAME({query_terms['author']})")
    
    if "title" in query_terms and query_terms["title"]:
        parts.append(f"TITLE({query_terms['title']})")
    
    if "journal" in query_terms and query_terms["journal"]:
        parts.append(f"SRCTITLE({query_terms['journal']})")
    
    if "affiliation" in query_terms and query_terms["affiliation"]:
        parts.append(f"AFFIL({query_terms['affiliation']})")
    
    if "doi" in query_terms and query_terms["doi"]:
        parts.append(f"DOI({query_terms['doi']})")
    
    return " AND ".join(parts)

def format_wos_query(query_terms):
    """Format query for Web of Science"""
    parts = []
    
    if "general" in query_terms and query_terms["general"]:
        parts.append(f"TS=({query_terms['general']})")
    
    if "author" in query_terms and query_terms["author"]:
        parts.append(f"AU=({query_terms['author']})")
    
    if "title" in query_terms and query_terms["title"]:
        parts.append(f"TI=({query_terms['title']})")
    
    if "journal" in query_terms and query_terms["journal"]:
        parts.append(f"SO=({query_terms['journal']})")
    
    if "affiliation" in query_terms and query_terms["affiliation"]:
        parts.append(f"AD=({query_terms['affiliation']})")
    
    if "doi" in query_terms and query_terms["doi"]:
        parts.append(f"DO=({query_terms['doi']})")
    
    return " AND ".join(parts)

def format_dnb_query(query_terms):
    """Format query for Deutsche Nationalbibliothek"""
    parts = []
    
    if "general" in query_terms and query_terms["general"]:
        parts.append(f"any={query_terms['general']}")
    
    if "author" in query_terms and query_terms["author"]:
        parts.append(f"per={query_terms['author']}")
    
    if "title" in query_terms and query_terms["title"]:
        parts.append(f"tit={query_terms['title']}")
    
    # DNB uses different fields than the others
    if "journal" in query_terms and query_terms["journal"]:
        parts.append(f"ser={query_terms['journal']}")
    
    # DNB doesn't have direct equivalents for these fields
    # but we'll include simplified versions
    if "affiliation" in query_terms and query_terms["affiliation"]:
        parts.append(f"any={query_terms['affiliation']}")
    
    if "doi" in query_terms and query_terms["doi"]:
        parts.append(f"num={query_terms['doi']}")
    
    return " AND ".join(parts)

def remove_duplicates(results):
    """
    Remove duplicate results based on DOI or title
    
    Args:
        results (list): List of result dictionaries
        
    Returns:
        list: Deduplicated results
    """
    unique_results = []
    seen_dois = set()
    seen_titles = {}
    
    for result in results:
        doi = result.get("doi", "").strip().lower()
        title = result.get("title", "").strip().lower()
        
        # If we have a DOI, use that for deduplication
        if doi and doi in seen_dois:
            continue
        
        # Otherwise use the title
        if not doi and title in seen_titles:
            # If this source is more preferred than the one we already have,
            # replace it (priority: WoS > Scopus > PubMed > DNB)
            current = result.get("source", "")
            existing = seen_titles[title].get("source", "")
            
            source_priority = {
                "Web of Science": 4,
                "Scopus": 3,
                "PubMed": 2,
                "Deutsche Nationalbibliothek": 1
            }
            
            if source_priority.get(current, 0) > source_priority.get(existing, 0):
                # Replace the existing one
                idx = unique_results.index(seen_titles[title])
                unique_results[idx] = result
                seen_titles[title] = result
            
            continue
        
        # This is a new unique result
        if doi:
            seen_dois.add(doi)
        
        if title:
            seen_titles[title] = result
            
        unique_results.append(result)
    
    return unique_results

def analyze_results(results):
    """
    Analyze results to generate stats
    
    Args:
        results (list): List of result dictionaries
        
    Returns:
        dict: Analysis results
    """
    analysis = {
        "total": len(results),
        "by_source": {},
        "by_year": {},
        "by_author": {}
    }
    
    # Count by source
    for result in results:
        source = result.get("source", "Unknown")
        if source not in analysis["by_source"]:
            analysis["by_source"][source] = 0
        analysis["by_source"][source] += 1
        
        # Count by year
        year = result.get("year", "Unknown")
        if year not in analysis["by_year"]:
            analysis["by_year"][year] = 0
        analysis["by_year"][year] += 1
        
        # Count by author (first author only)
        if result.get("authors") and len(result["authors"]) > 0:
            author = result["authors"][0]
            if author not in analysis["by_author"]:
                analysis["by_author"][author] = 0
            analysis["by_author"][author] += 1
    
    # Sort by year
    analysis["by_year"] = dict(sorted(
        analysis["by_year"].items(),
        key=lambda x: (x[0] != "Unknown", x[0])  # Sort Unknown last, then by year
    ))
    
    # Sort authors by count
    analysis["by_author"] = dict(sorted(
        analysis["by_author"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:10])  # Top 10 authors
    
    return analysis
