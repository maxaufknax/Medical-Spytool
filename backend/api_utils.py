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


def search_status_response(status, errors=None, redirect_url=None, query_id=None, message=None, progress=None):
    """
    Create a standardized search status response.

    Args:
        status (str): Current search status (searching, completed, no_results, error, timeout)
        errors (list, optional): List of error details by database
        redirect_url (str, optional): URL to redirect to after search completion
        query_id (str, optional): The ID of the current search query
        message (str, optional): Human-readable status message. Overrides default if provided.
        progress (dict, optional): Progress information (e.g., {'current': 50, 'total': 100})

    Returns:
        tuple: (Response object, status code)
    """
    response_data = {
        "status": status,
        "message": message if message is not None else _get_default_status_message(status), # Use provided message or default
        "errors": errors, # Will be removed if None
        "redirect_url": redirect_url, # Will be removed if None
        "query_id": query_id, # Will be removed if None
        "progress": progress # Will be removed if None
    }
    
    # Remove keys with None values to keep the response clean
    response_data = {k: v for k, v in response_data.items() if v is not None}
    
    # Ensure errors is an empty list if not provided and not None (e.g. if it was an empty list initially)
    # This part might be redundant if we remove None keys, as "errors": null would be removed.
    # If the frontend expects "errors": [] instead of the key being absent, this is important.
    # Based on current usage (data.errors && data.errors.length > 0 in JS), absent key is fine.
    # if "errors" not in response_data and errors is None: # errors argument was None
    #    response_data["errors"] = []


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
