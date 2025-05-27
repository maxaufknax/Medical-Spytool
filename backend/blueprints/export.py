#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Export Blueprint
This blueprint handles functionality for exporting search results.
"""

import json
import pandas as pd
from io import BytesIO
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session

from backend.models import db, SearchQuery, SearchResult, Setting
from backend.export_utils import generate_filename, export_to_csv, export_to_excel, export_to_bibtex, export_to_pdf

export_bp = Blueprint("export", __name__)


@export_bp.route("/export", methods=["POST"])
def export_results():
    """Export search results in different formats (CSV, Excel, JSON)

    This function handles the export of search results based on either the search_id
    provided in the form or stored in the session. It supports multiple export formats
    and allows customization of which columns to include in the export.

    Returns:
        Response: Either a file download response with the exported data or a
                  redirect to the results page with an appropriate flash message

    Security:
        - Validates search_id before processing
        - Uses send_file with safe file name generation
        - Content-Disposition header set to attachment for secure downloads
    """
    search_id = request.form.get("search_id") or session.get("current_search_id")
    if not search_id:
        flash("Keine Suche zum Exportieren ausgewählt.", "warning")
        return redirect(url_for("search.results"))

    search_query = SearchQuery.query.get(search_id)
    if not search_query:
        flash("Die ausgewählte Suche konnte nicht gefunden werden.", "danger")
        return redirect(url_for("search.results"))

    export_format = request.form.get("format", "csv")

    # Get results
    results = []
    for result in search_query.results:
        results.append(result.to_dict())

    if not results:
        flash("Keine Ergebnisse zum Exportieren verfügbar.", "warning")
        return redirect(url_for("search.results"))

    # Get user-selected columns for export
    selected_columns = request.form.getlist("export_columns")
    settings = Setting.get_settings_dict()  # Ensure settings are loaded

    # If user has selected columns, use those
    if selected_columns:
        output_columns = selected_columns
    else:
        # Otherwise use default columns from settings
        # Ensure default_settings in config.py provides a fallback for output_columns
        output_columns = settings.get(
            "output_columns",
            [
                "Name",
                "Title",
                "Creator",
                "Publication Year",
                "Identifier",
                "URL",
                "Authors",
                "Citation Count",
                "Database",  # Added Database as it's a common field
            ],
        )

    # Filter results based on output_columns for all formats
    filtered_results_for_export = []
    for result_item in results:
        filtered_item = {
            col: result_item.get(col) for col in output_columns if col in result_item
        }
        filtered_results_for_export.append(filtered_item)

    # Generate filename
    unique = settings.get("unique_filenames", False)
    filename_base = f"medicalspy_export_{search_query.name}"

    # Use filtered results for all export formats
    if export_format == "csv":
        output = export_to_csv(filtered_results_for_export, filename_base, unique)
        filename = generate_filename(filename_base, "csv", unique)
        return send_file(
            BytesIO(output.encode("utf-8")),
            mimetype="text/csv",
            as_attachment=True,
            download_name=filename,
        )
    elif export_format == "excel":
        output = export_to_excel(filtered_results_for_export, filename_base, unique)
        filename = generate_filename(filename_base, "xlsx", unique)
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename,
        )
    elif export_format == "bibtex":
        output = export_to_bibtex(filtered_results_for_export, filename_base, unique)
        filename = generate_filename(filename_base, "bib", unique)
        return send_file(
            BytesIO(output.encode("utf-8")),
            mimetype="application/x-bibtex",
            as_attachment=True,
            download_name=filename,
        )
    elif export_format == "pdf":
        search_query_info = {
            "search_text": search_query.search_text,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        # Pass output_columns to export_to_pdf
        output_pdf_bytes = export_to_pdf(filtered_results_for_export, filename_base, unique, search_query_info, output_columns)
        filename = generate_filename(filename_base, "pdf", unique)
        return send_file(
            output_pdf_bytes,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )
    else:
        flash(f'Exportformat "{export_format}" wird nicht unterstützt.', "danger")
        return redirect(url_for("search.results"))
