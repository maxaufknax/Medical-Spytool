#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Export Utilities
These functions support data export from MedicalSpy.
"""

import csv
import re
import pandas as pd
import logging
from datetime import datetime
from io import StringIO, BytesIO
import os

logger = logging.getLogger(__name__)

def generate_filename(base_name, extension, unique=False):
    """
    Generate a filename with optional uniqueness.

    Args:
        base_name (str): Base name for the file
        extension (str): File extension without dot
        unique (bool): Whether to add timestamp for uniqueness

    Returns:
        str: Generated filename
    """
    # Replace spaces and special characters with underscores
    safe_name = re.sub(r'[^\w\-\.]', '_', base_name)
    
    if unique:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{safe_name}_{timestamp}.{extension}"
    else:
        return f"{safe_name}.{extension}"

def export_to_csv(data, filename_base=None, unique=False):
    """
    Export data to a CSV file.

    Args:
        data (list): List of dictionaries to export
        filename_base (str): Base filename for the export
        unique (bool): Whether to generate a unique filename

    Returns:
        str: CSV formatted string
    """
    if not data or not isinstance(data, list) or not data[0]:
        logger.warning("No data to export to CSV")
        return ""

    output = StringIO()
    
    # Get field names from the first item
    fieldnames = list(data[0].keys())

    # Write CSV
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue()

def export_to_excel(data, filename_base=None, unique=False):
    """
    Export data to an Excel file.

    Args:
        data (list): List of dictionaries to export
        filename_base (str): Base filename for the export
        unique (bool): Whether to generate a unique filename

    Returns:
        BytesIO: Excel file as BytesIO object
    """
    if not data or not isinstance(data, list):
        logger.warning("No data to export to Excel")
        return BytesIO()

    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Create an output BytesIO object
    output = BytesIO()
    
    # Write Excel
    df.to_excel(output, index=False)
    
    # Seek to the beginning of the stream
    output.seek(0)
    
    return output

def export_to_bibtex(data, filename_base=None, unique=False):
    """
    Export data to BibTeX format.

    Args:
        data (list): List of dictionaries containing publication data
        filename_base (str): Base filename for the export
        unique (bool): Whether to generate a unique filename

    Returns:
        str: BibTeX formatted string
    """
    if not data or not isinstance(data, list):
        logger.warning("No data to export to BibTeX")
        return ""

    bibtex_output = []

    for idx, entry in enumerate(data):
        if not isinstance(entry, dict):
            logger.warning(f"Skipping invalid entry at index {idx}: Not a dictionary")
            continue

        # Extract key fields with fallbacks
        title = entry.get("Title") or entry.get("Titel") or ""
        author_data = entry.get("Authors") or entry.get("Autoren") or entry.get("Creator") or ""
        year_str = entry.get("Publication Year") or entry.get("Veröffentlichungsjahr") or entry.get("Erscheinungsjahr") or ""
        
        # Skip entries without essential fields
        if not title:
            logger.warning(f"Skipping entry at index {idx}: Missing title")
            continue
        
        # Try to get a valid year
        year = "0000"
        if year_str:
            # Extract first 4-digit number
            year_match = re.search(r'\d{4}', str(year_str))
            if year_match:
                year = year_match.group(0)
                
        # Generate citation key
        first_author = ""
        if isinstance(author_data, list) and author_data:
            # Use first author's last name
            author_parts = author_data[0].split(',')
            if len(author_parts) > 0:
                first_author = author_parts[0].strip().lower()
        elif isinstance(author_data, str) and author_data:
            # Try to get first author from string
            if ',' in author_data:
                first_author = author_data.split(',')[0].strip().lower()
            else:
                names = author_data.split()
                if names:
                    first_author = names[-1].strip().lower()  # Assume last word is surname
                    
        # Clean up first_author for citation key
        first_author = re.sub(r'[^a-z]', '', first_author)
        if not first_author:
            first_author = f"ref{idx}"
            
        citation_key = f"{first_author}{year}"
        
        # Determine entry type - default to article
        bibtex_type = "article"
        
        # Begin BibTeX entry
        bibtex_entry = [f"@{bibtex_type}{{{citation_key},"]
        
        # Add authors
        if author_data:
            if isinstance(author_data, list):
                author_str = " and ".join(author_data)
            else:
                author_str = author_data
            bibtex_entry.append(f"  author = {{{author_str}}},")
            
        # Add title
        if title:
            bibtex_entry.append(f"  title = {{{title}}},")
            
        # Add year
        if year and year != "0000":
            bibtex_entry.append(f"  year = {{{year}}},")
            
        # Add journal
        journal = entry.get("Journal") or entry.get("Source") or entry.get("Quelle") or ""
        if journal:
            bibtex_entry.append(f"  journal = {{{journal}}},")
            
        # Add URL
        url = entry.get("URL") or entry.get("PubMed URL") or entry.get("DOI URL") or ""
        if url:
            bibtex_entry.append(f"  url = {{{url}}},")
            
        # Add DOI
        doi = entry.get("DOI") or ""
        if doi:
            bibtex_entry.append(f"  doi = {{{doi}}},")
            
        # Add database as note
        database = entry.get("Database") or entry.get("Datenbank") or ""
        if database:
            bibtex_entry.append(f"  note = {{Source: {database}}},")
            
        # Remove trailing comma from last field
        if bibtex_entry[-1].endswith(','):
            bibtex_entry[-1] = bibtex_entry[-1][:-1]
            
        # Close entry
        bibtex_entry.append("}")
        
        # Add to output
        bibtex_output.append("\n".join(bibtex_entry))
        
    # Join all entries with newlines
    return "\n\n".join(bibtex_output)
