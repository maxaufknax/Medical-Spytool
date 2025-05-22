#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - API Utilities
This module provides utility functions for standardizing API responses.
"""

from flask import jsonify, url_for


def api_response(success=True, data=None, message=None, status_code=200, details=None):
    """
    Create a standardized API response.

    Args:
        success (bool): Whether the operation was successful
        data (Any, optional): Data to include in the response
        message (str, optional): Human-readable message
        status_code (int): HTTP status code for the response
        details (dict, optional): Additional details or error information

    Returns:
        tuple: (Response object, status code)
    """
    response = {"status": "success" if success else "error", "message": message}

    if data is not None:
        response["data"] = data

    if details is not None:
        response["details"] = details

    return jsonify(response), status_code


def search_status_response(status, message=None, errors=None, redirect_url=None):
    """
    Create a standardized search status response.

    Args:
        status (str): Current search status (searching, completed, no_results, error, timeout)
        message (str, optional): Human-readable status message
        errors (list, optional): List of error details by database
        redirect_url (str, optional): URL to redirect to after search completion

    Returns:
        tuple: (Response object, status code)
    """
    response_data = {
        "status": status,
        "message": message or _get_default_status_message(status),
    }

    if errors:
        response_data["errors"] = errors

    if redirect_url:
        response_data["redirect_url"] = redirect_url

    return jsonify(response_data), 200


def _get_default_status_message(status):
    """Get default message for search status."""
    messages = {
        "searching": "Suche läuft...",
        "completed": "Suche abgeschlossen",
        "no_results": "Keine Ergebnisse gefunden",
        "error": "Ein Fehler ist aufgetreten",
        "timeout": "Die Suche wurde wegen Zeitüberschreitung abgebrochen",
        "idle": "Bereit",
    }
    return messages.get(status, "Status unbekannt")
