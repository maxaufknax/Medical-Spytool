#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - API Utilities
This module provides utility functions for standardizing API responses.
"""

from flask import jsonify


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
