#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Utility functions module
This module provides utility functions for MedicalSpy.
"""

import os
import csv
import re
import pandas as pd
import logging
from datetime import datetime
from io import StringIO
from backend.models import LogEntry, db
from flask import current_app

logger = logging.getLogger("MedicalSpy")


# No longer using in-memory logs as they are redundant with file and DB logging
def log_message(message, level="INFO", save_to_db=True):
    """
    Log a message to the file log and optionally to the database.

    Args:
        message (str): The message to log
        level (str, optional): The log level (INFO, WARNING, ERROR)
        save_to_db (bool, optional): Whether to save the log message to the database
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Sanitize sensitive data in logs
    sanitized_message = sanitize_sensitive_data(message)

    # Log to file using standard Python logging
    if level == "INFO":
        logger.info(sanitized_message)
    elif level == "WARNING":
        logger.warning(sanitized_message)
    elif level == "ERROR":
        logger.error(sanitized_message)

    # Save to database if requested
    if save_to_db:
        try:
            # Only save to DB if within app context
            if current_app:
                with current_app.app_context():
                    LogEntry.add_log(sanitized_message, level)
        except Exception as e:
            logger.error(f"Failed to save log to database: {e}")


def get_log_messages(include_db_logs=True):
    """
    Get log messages from the database.

    Args:
        include_db_logs (bool, optional): Whether to include logs from the database

    Returns:
        list: List of log messages
    """
    logs = []

    if include_db_logs:
        try:
            # Only get DB logs if within app context
            if current_app:
                with current_app.app_context():
                    db_logs = LogEntry.get_logs()
                    logs.extend([log.to_dict() for log in db_logs])
        except Exception as e:
            logger.error(f"Failed to retrieve logs from database: {e}")

    return logs


def clear_log_messages():
    """
    Clear log messages from the database.
    This no longer clears in-memory logs as they are no longer used.
    """
    try:
        # Clear database logs
        if current_app:
            with current_app.app_context():
                LogEntry.clear_logs()
    except Exception as e:
        logger.error(f"Failed to clear logs from database: {e}")


def sanitize_sensitive_data(text):
    """
    Sanitize sensitive data like API keys, passwords, etc. from log messages.

    Args:
        text (str): The text to sanitize

    Returns:
        str: Sanitized text
    """
    # Mask API keys
    api_key_pattern = r"(api_key=)[^&\s]+"
    sanitized = re.sub(api_key_pattern, r"\1********", text)

    # Mask passwords
    password_pattern = r"(password=)[^&\s]+"
    sanitized = re.sub(password_pattern, r"\1********", sanitized)

    # Mask potential PubMed API keys
    pubmed_key_pattern = r"(PUBMED_API_KEY=)[^&\s]+"
    sanitized = re.sub(pubmed_key_pattern, r"\1********", sanitized)

    return sanitized


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
    if not data:
        return ""

    import csv
    from io import StringIO
    
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
    if not data:
        return BytesIO()

    import pandas as pd
    from io import BytesIO
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Create an output BytesIO object
    output = BytesIO()
    
    # Write Excel
    df.to_excel(output, index=False)
    
    # Seek to the beginning of the stream
    output.seek(0)
    
    return output


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
    if not isinstance(data, list) or not data:
        logger.error("Input data is empty or not a list. Cannot export to BibTeX.")
        return ""

    import re
    from datetime import datetime
    
    bibtex_output = []

    for idx, entry in enumerate(data):
        if not isinstance(entry, dict):
            logger.warning(f"Skipping invalid entry at index {idx}: Not a dictionary.")
            continue

        # Extract key fields with fallbacks
        title = entry.get("Title") or entry.get("Titel") or ""
        author_data = entry.get("Authors") or entry.get("Autoren") or entry.get("Creator") or ""
        year_str = entry.get("Publication Year") or entry.get("Veröffentlichungsjahr") or entry.get("Erscheinungsjahr") or ""
        
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
        
    # Close the entry - remove trailing comma from the last field
        if bibtex_entry[-1].endswith(','):
            bibtex_entry[-1] = bibtex_entry[-1][:-1]
        
        bibtex_entry.append("}")
        
        # Add the complete bibtex entry to the output list
        bibtex_output.append("\n".join(bibtex_entry))
    
    # Join all entries with newlines
    return "\n\n".join(bibtex_output)
    
    # Join all entries with double newlines and return
    return "\n\n".join(bibtex_output)
        elif isinstance(author_data, str) and author_data:
            # Format author string for BibTeX
            if ";" in author_data:
                authors_str = " and ".join([a.strip() for a in author_data.split(";")])
            elif (
                "," in author_data
                and " and " not in author_data.lower()
                and " und " not in author_data.lower()
            ):
                # Assume format is "Last1, First1, Last2, First2"
                parts = [p.strip() for p in author_data.split(",")]
                authors = []
                for i in range(0, len(parts), 2):
                    if i + 1 < len(parts):
                        authors.append(f"{parts[i]}, {parts[i+1]}")
                    else:
                        authors.append(parts[i])
                authors_str = " and ".join(authors)
            else:
                # Replace natural language "and" with BibTeX "and"
                authors_str = re.sub(
                    r"\s+and\s+|\s+und\s+", " and ", author_data, flags=re.IGNORECASE
                )
            bibtex_entry.append(f"  author = {{{authors_str}}},")

        # Add title
        title = entry.get("Titel") or entry.get("Title") or entry.get("TI") or ""
        if title:
            # Preserve uppercase letters in BibTeX by adding {}
            title = title.replace("{", "{{").replace("}", "}}").replace("&", "\&")
            bibtex_entry.append(f"  title = {{{title}}},")

        # Add journal/booktitle
        journal = entry.get("Journal") or entry.get("Source") or entry.get("SO") or ""
        if journal and bibtex_type == "article":
            bibtex_entry.append(f"  journal = {{{journal}}},")
        elif journal:
            bibtex_entry.append(f"  booktitle = {{{journal}}},")

        # Add year
        if year and year != "NoYear":
            bibtex_entry.append(f"  year = {{{year}}},")

        # Add volume, number, pages
        volume = entry.get("Volume") or entry.get("Band") or ""
        if volume:
            bibtex_entry.append(f"  volume = {{{volume}}},")

        number = entry.get("Issue") or entry.get("Number") or entry.get("Ausgabe") or ""
        if number:
            bibtex_entry.append(f"  number = {{{number}}},")

        pages = entry.get("Pages") or entry.get("Seiten") or ""
        if pages:
            # Format pages for BibTeX (replace single dash with double dash)
            pages = re.sub(r"(\d+)\s*-\s*(\d+)", r"\1--\2", pages)
            bibtex_entry.append(f"  pages = {{{pages}}},")

        # Add DOI
        doi = entry.get("DOI") or ""
        if doi:
            bibtex_entry.append(f"  doi = {{{doi}}},")

        # Add URL
        url = entry.get("URL") or entry.get("Link") or ""
        if url:
            bibtex_entry.append(f"  url = {{{url}}},")

        # Add publisher
        publisher = entry.get("Publisher") or entry.get("Verlag") or ""
        if publisher:
            bibtex_entry.append(f"  publisher = {{{publisher}}},")

        # Add abstract
        abstract = entry.get("Abstract") or entry.get("Zusammenfassung") or entry.get("AB") or ""
        if abstract:
            # Truncate very long abstracts to avoid BibTeX issues
            if len(abstract) > 2000:
                abstract = abstract[:1997] + "..."
            bibtex_entry.append(f"  abstract = {{{abstract}}},")

        # Add keywords
        keywords = entry.get("Keywords") or entry.get("Schlagwörter") or ""
        if keywords:
            if isinstance(keywords, list):
                keywords = ", ".join(keywords)
            bibtex_entry.append(f"  keywords = {{{keywords}}},")

        # Close the entry
        bibtex_entry[-1] = bibtex_entry[-1].rstrip(",")
        bibtex_entry.append("}")

        # Add the entry to the output
        bibtex_output.append("\n".join(bibtex_entry))

    # Return all entries joined with newlines and an empty line between entries
    return "\n\n".join(bibtex_output)
