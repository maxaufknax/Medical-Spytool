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

from fpdf import FPDF
from fpdf.fonts import FontFace

class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add DejaVu fonts for UTF-8 support
        # The .ttf files must be available. For a real app, they'd be packaged or in a known location.
        # For this environment, I cannot add .ttf files directly.
        # FPDF2 by default uses 'helvetica', 'times', 'courier'.
        # For broader UTF-8, it's best to bundle a font.
        # If DejaVuSans.ttf is not found, this will fall back to core fonts, potentially causing encoding issues for some characters.
        try:
            self.add_font("DejaVu", "", "DejaVuSans.ttf")
            self.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf")
            self.set_fallback_fonts(["DejaVu", "Arial", "Helvetica"]) # Fallback fonts
            self.font_family_utf8 = "DejaVu"
        except RuntimeError: # Font file not found
            logger.warning("DejaVu font not found. PDF output might have limited UTF-8 support. Using core fonts.")
            self.font_family_utf8 = "Helvetica" # Fallback to a core font

    def header(self):
        if hasattr(self, 'custom_header_text') and self.custom_header_text:
            self.set_font(self.font_family_utf8, 'B', 12)
            self.cell(0, 10, self.custom_header_text, 0, 1, 'C')
        self.ln(5) # Space after header

    def footer(self):
        self.set_y(-15)
        self.set_font(self.font_family_utf8, '', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font(self.font_family_utf8, 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font(self.font_family_utf8, '', 10)
        self.multi_cell(0, 5, body) # Using 5 for line height
        self.ln()

    def add_table(self, headers, data, col_widths=None):
        self.set_font(self.font_family_utf8, 'B', 8)
        self.set_fill_color(200, 220, 255) # Light blue for header
        
        if col_widths is None:
            num_cols = len(headers)
            # Calculate effective page width (page width - 2 * margin)
            effective_page_width = self.w - 2 * self.l_margin
            default_col_width = effective_page_width / num_cols if num_cols > 0 else effective_page_width
            col_widths = [default_col_width] * num_cols

        # Header
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, str(header), 1, 0, 'C', 1)
        self.ln()

        # Data
        self.set_font(self.font_family_utf8, '', 7)
        self.set_fill_color(240, 240, 240) # Light grey for alternate rows
        fill = False
        for row in data:
            for i, header in enumerate(headers):
                # Ensure text is string and handle potential None values
                text = str(row.get(header, '')) 
                # multi_cell for wrapping. Need to calculate height dynamically or use fixed height and clip/truncate.
                # For simplicity, using cell with fixed height. Long text will be truncated by FPDF's cell.
                # A more advanced solution would calculate max height needed for the row.
                self.cell(col_widths[i], 6, text, 1, 0, 'L', fill)
            self.ln()
            fill = not fill


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
    
    # Get field names from the first item if data is not empty
    fieldnames = list(data[0].keys()) if data and isinstance(data[0], dict) else []


    # Write CSV
    writer = csv.DictWriter(output, fieldnames=fieldnames, restval="", extrasaction='ignore')
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

    for idx, entry_data in enumerate(data):
        if not isinstance(entry_data, dict):
            logger.warning(f"Skipping invalid BibTeX entry data at index {idx}: Not a dictionary")
            continue
        
        try:
            # --- Title (Required) ---
            title = entry_data.get("Title") or entry_data.get("Titel")
            if not title:
                logger.warning(f"Skipping BibTeX entry at index {idx}: Missing title.")
                continue
            
            # --- Authors ---
            authors_str = ""
            author_data = entry_data.get("Authors") or entry_data.get("Autoren") or entry_data.get("Creator")
            if isinstance(author_data, list):
                # Assuming list of "Last, First" or "First Last"
                # BibTeX expects "Lastname, Firstname and Otherlastname, Otherfirstname"
                # This requires more robust parsing if names are not already in Last, First format.
                # For now, join with " and " and escape.
                author_str = " and ".join(str(a) for a in author_data if a)
            elif isinstance(author_data, str):
                # Attempt to split common delimiters if not already formatted for BibTeX
                # This is a basic attempt; true "Last, First" parsing is complex.
                if ';' in author_data:
                    author_str = " and ".join(a.strip() for a in author_data.split(';'))
                elif ',' in author_data and not any(kw in author_data.lower() for kw in [" and ", " und "]):
                    # Simple assumption: if only commas, maybe it's Last, F., Last, F.
                    # Better to just join with "and" if structure is unclear, or require "Last, First" input.
                    # For now, treating as potentially multiple authors separated by comma.
                    author_str = " and ".join(a.strip() for a in author_data.split(','))
                else:
                    author_str = author_data # Assumes it's already "Name1 and Name2" or single author
            else:
                author_str = ""

            # --- Year ---
            year = ""
            year_str_data = entry_data.get("Publication Year") or entry_data.get("Veröffentlichungsjahr") or entry_data.get("Erscheinungsjahr")
            if year_str_data:
                year_match = re.search(r'\d{4}', str(year_str_data))
                if year_match:
                    year = year_match.group(0)

            # --- Citation Key Generation (Improved) ---
            citation_key_author_part = "untitled"
            if author_str:
                first_author_full = author_str.split(" and ")[0]
                if ',' in first_author_full: # "Last, First"
                    citation_key_author_part = first_author_full.split(",")[0].strip().lower()
                else: # "First Last" or single name
                    citation_key_author_part = first_author_full.split(" ")[-1].strip().lower() # Take last word
            
            citation_key_author_part = re.sub(r'[^a-z]', '', citation_key_author_part)
            if not citation_key_author_part: citation_key_author_part = f"ref{idx}"
            citation_key_year_part = year if year else "nodate"
            citation_key_title_part = re.sub(r'[^a-z]', '', title.split(" ")[0].lower())[:5] # First word of title, max 5 chars
            citation_key = f"{citation_key_author_part}{citation_key_year_part}{citation_key_title_part}"


            # --- Entry Type Detection ---
            pub_types_str = entry_data.get("Publication Types") or entry_data.get("Publikationstypen") or ""
            bibtex_type = get_bibtex_entry_type(pub_types_str)

            # --- Building BibTeX Entry ---
            bib_fields = []
            bib_fields.append(f"  title = {{{escape_bibtex_chars(title)}}}")
            if author_str:
                bib_fields.append(f"  author = {{{escape_bibtex_chars(author_str)}}}")
            if year:
                bib_fields.append(f"  year = {{{year}}}")

            # Journal / Booktitle / School / Institution
            journal = entry_data.get("Journal") or entry_data.get("Source") or entry_data.get("Quelle")
            publisher = entry_data.get("Publisher") # For books, reports
            
            if bibtex_type == "article" and journal:
                bib_fields.append(f"  journal = {{{escape_bibtex_chars(journal)}}}")
            elif bibtex_type == "inproceedings" and journal: # Conference proceedings often in 'booktitle'
                bib_fields.append(f"  booktitle = {{{escape_bibtex_chars(journal)}}}")
            elif bibtex_type == "book" and publisher:
                bib_fields.append(f"  publisher = {{{escape_bibtex_chars(publisher)}}}")
            elif bibtex_type == "phdthesis" and publisher: # Publisher can be school for thesis
                 bib_fields.append(f"  school = {{{escape_bibtex_chars(publisher)}}}")
            elif journal : # Fallback for other types if journal/source info is present
                 bib_fields.append(f"  note = {{In: {escape_bibtex_chars(journal)}}}")


            # Volume, Number, Pages (common for articles)
            volume = entry_data.get("Volume")
            number = entry_data.get("Number") or entry_data.get("Issue")
            pages = entry_data.get("Pages")
            if volume: bib_fields.append(f"  volume = {{{escape_bibtex_chars(volume)}}}")
            if number: bib_fields.append(f"  number = {{{escape_bibtex_chars(number)}}}")
            if pages: bib_fields.append(f"  pages = {{{escape_bibtex_chars(pages).replace('-', '--')}}}") # BibTeX page range

            # Month
            month_str_data = entry_data.get("Publication Month") or entry_data.get("Veröffentlichungsmonat")
            bib_month = format_bibtex_month(month_str_data)
            if bib_month:
                bib_fields.append(f"  month = {{{bib_month}}}")

            # DOI and URL
            doi = entry_data.get("DOI")
            url = entry_data.get("URL") or entry_data.get("PubMed URL") or entry_data.get("DNB URL") 
            if doi: bib_fields.append(f"  doi = {{{escape_bibtex_chars(doi)}}}")
            if url: bib_fields.append(f"  url = {{{escape_bibtex_chars(url)}}}")
            
            # Abstract (optional, some BibTeX styles support it)
            abstract = entry_data.get("Abstract")
            if abstract: bib_fields.append(f"  abstract = {{{escape_bibtex_chars(abstract)}}}")

            # Database as note
            database = entry_data.get("Database") or entry_data.get("Datenbank")
            if database:
                bib_fields.append(f"  note = {{Source: {escape_bibtex_chars(database)}}}")

            bibtex_entry_str = f"@{bibtex_type}{{{citation_key},\n"
            bibtex_entry_str += ",\n".join(bib_fields)
            bibtex_entry_str += "\n}"
            bibtex_output.append(bibtex_entry_str)

        except Exception as e:
            logger.error(f"Error processing BibTeX entry at index {idx} for title '{title[:50]}...': {e}", exc_info=True)
            continue # Skip this entry

    return "\n\n".join(bibtex_output)

# --- Helper functions for BibTeX ---
BIBTEX_ESCAPES = {
    ord('{'): r'\{', ord('}'): r'\}', ord('\\'): r'\textbackslash{}',
    ord('"'): r"{\textquotedbl}", # More robust than '' or "" for general use
    ord('#'): r'\#', ord('%'): r'\%', ord('&'): r'\&',
    ord('~'): r'\textasciitilde{}', ord('$'): r'\$', ord('^'): r'\^{}',
    ord('_'): r'\_',
    # Common ligatures / special chars often needing protection if not using unicode-bibtex
    # For unicode-bibtex (like biblatex), direct UTF-8 is often better.
    # For traditional bibtex, these are safer:
    ord('ä'): r'{\"a}', ord('ö'): r'{\"o}', ord('ü'): r'{\"u}',
    ord('Ä'): r'{\"A}', ord('Ö'): r'{\"O}', ord('Ü'): r'{\"U}',
    ord('ß'): r'{\ss}',
    # Add more accented characters as needed, e.g., á -> \'a, é -> \'e, etc.
    # For simplicity, only common German umlauts and sz are added here.
}

def escape_bibtex_chars(text):
    if not text:
        return ""
    # Ensure it's a string first
    text_str = str(text)
    # Replace characters that might break BibTeX if not handled by LaTeX macros
    # This simple replacement is a basic measure. Full LaTeX escaping is complex.
    # For fields that are verbatim or URLs, often less escaping is needed or different rules apply.
    return text_str.translate(BIBTEX_ESCAPES)

MONTH_ABBREVIATIONS = {
    "01": "jan", "1": "jan", "jan": "jan", "january": "jan",
    "02": "feb", "2": "feb", "feb": "feb", "february": "feb",
    "03": "mar", "3": "mar", "mar": "mar", "march": "mar",
    "04": "apr", "4": "apr", "apr": "apr", "april": "apr",
    "05": "may", "5": "may", "may": "may", "may.": "may",
    "06": "jun", "6": "jun", "jun": "jun", "june": "jun",
    "07": "jul", "7": "jul", "jul": "jul", "july": "jul",
    "08": "aug", "8": "aug", "aug": "aug", "august": "aug",
    "09": "sep", "9": "sep", "sep": "sep", "september": "sep", "sept": "sep",
    "10": "oct", "oct": "oct", "october": "oct",
    "11": "nov", "nov": "nov", "november": "nov",
    "12": "dec", "dec": "dec", "december": "dec",
}

def format_bibtex_month(month_str):
    if not month_str: return None
    # Normalize: remove dots, lowercase, strip
    normalized_month = str(month_str).replace('.', '').lower().strip()
    return MONTH_ABBREVIATIONS.get(normalized_month, None)

def get_bibtex_entry_type(publication_types_str):
    if not publication_types_str: return "misc"
    
    types_lower = [pt.strip().lower() for pt in str(publication_types_str).split(',')]
    
    # Prioritized mapping
    if "journal article" in types_lower or "article" in types_lower: return "article"
    if "book" in types_lower: return "book"
    if "conference paper" in types_lower or "inproceedings" in types_lower or "conference" in types_lower : return "inproceedings"
    if "report" in types_lower: return "techreport"
    if "phd thesis" in types_lower or "doctoral thesis" in types_lower : return "phdthesis"
    if "master thesis" in types_lower or "mastersthesis" in types_lower : return "mastersthesis"
    if "bachelor thesis" in types_lower or "bachelorthesis" in types_lower : return "bachelorthesis"
    if any("thesis" in t for t in types_lower): return "thesis" # Generic thesis
    if "unpublished" in types_lower: return "unpublished"
    if "preprint" in types_lower: return "article" # Often treated as article or online
    
    # Fallbacks based on keywords
    if any("journal" in t for t in types_lower): return "article"
    if any("conference" in t for t in types_lower): return "inproceedings"
        
    return "misc"
# --- End of Helper functions for BibTeX ---


def export_to_pdf(data, filename_base=None, unique=False, search_query_info=None, output_columns=None):
    """
    Export data to a PDF file.

    Args:
        data (list): List of dictionaries to export.
        filename_base (str): Base filename for the export.
        unique (bool): Whether to generate a unique filename.
        search_query_info (dict, optional): Dict with 'search_text', 'timestamp'.
        output_columns (list, optional): List of column names (headers) to include.

    Returns:
        BytesIO: PDF file as BytesIO object.
    """
    if not data or not isinstance(data, list):
        logger.warning("No data to export to PDF")
        return BytesIO()

    pdf = PDF(orientation='L', unit='mm', format='A4') # Landscape A4
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.custom_header_text = "MedicalSpy - Search Results"
    pdf.add_page()
    
    if search_query_info:
        pdf.set_font(pdf.font_family_utf8, '', 10)
        if search_query_info.get("search_text"):
            pdf.multi_cell(0, 5, f"Search Query: {search_query_info['search_text']}")
        if search_query_info.get("timestamp"):
            pdf.multi_cell(0, 5, f"Export Date: {search_query_info['timestamp']}")
        pdf.ln(5)

    headers = output_columns if output_columns else (list(data[0].keys()) if data and isinstance(data[0], dict) else [])
    if not headers:
        logger.warning("No headers for PDF export.")
        pdf.cell(0,10,"No data or headers to display.",0,1)
        return BytesIO(pdf.output(dest='S').encode('latin-1')) # FPDF outputs latin-1 by default

    # Simple column width calculation (equally distributed)
    # For better results, calculate widths based on content or provide predefined widths
    num_cols = len(headers)
    effective_page_width = pdf.w - 2 * pdf.l_margin # landscape A4 width is 297mm
    col_width = effective_page_width / num_cols if num_cols > 0 else effective_page_width
    col_widths = [col_width] * num_cols
    
    # Adjust specific column widths (example: make 'Title' wider)
    # This requires knowing the header names and their typical content length.
    try:
        title_idx = headers.index("Title") if "Title" in headers else headers.index("Titel")
        if title_idx != -1:
            # Give title more space, reduce others proportionally
            title_width_factor = 1.5 # Title gets 1.5x average width
            other_cols_width_factor = (num_cols - title_width_factor) / (num_cols -1) if num_cols > 1 else 1
            
            temp_widths = []
            current_total_width = 0
            for i, h in enumerate(headers):
                if i == title_idx:
                    w = col_width * title_width_factor
                else:
                    w = col_width * other_cols_width_factor
                temp_widths.append(w)
                current_total_width +=w
            
            # Normalize widths to fit effective_page_width
            if current_total_width > 0 : # Avoid division by zero
                 col_widths = [(w / current_total_width) * effective_page_width for w in temp_widths]

    except ValueError: # If 'Title' or 'Titel' not in headers
        pass


    pdf.add_table(headers, data, col_widths=col_widths)

    pdf_bytes_io = BytesIO(pdf.output(dest='S').encode('latin-1')) # FPDF default encoding
    pdf_bytes_io.seek(0)
    return pdf_bytes_io
