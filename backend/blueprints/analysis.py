#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Analysis Blueprint
This blueprint handles data analysis and visualization functionality.
"""

import json
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from backend.models import db, SearchQuery, SearchResult
from backend.api_utils import api_response
from flasgger import swag_from

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.route("/", methods=["GET"])
def index():
    """Show analysis page with charts and visualizations"""
    search_id = request.args.get("search_id") or session.get("current_search_id")
    if not search_id:
        flash("Keine Suche für die Analyse ausgewählt.", "warning")
        return render_template("analysis.html", search=None, results=None)

    search_query = SearchQuery.query.get(search_id)
    if not search_query:
        flash("Die ausgewählte Suche konnte nicht gefunden werden.", "danger")
        return render_template("analysis.html", search=None, results=None)

    # Get results
    results = []
    for result in search_query.results:
        results.append(result.to_dict())

    # Store current search ID in session
    session["current_search_id"] = search_id
    session["result_count"] = len(results)

    return render_template("analysis.html", search=search_query.to_dict(), results=results)


@analysis_bp.route("/api/analysis/years", methods=["GET"])
@swag_from(
    {
        "tags": ["Analysis"],
        "summary": "Get publication year distribution",
        "description": "Returns the distribution of publications by year for a given search query",
        "parameters": [
            {
                "name": "search_id",
                "in": "query",
                "type": "integer",
                "required": False,
                "description": "ID of the search query. If not provided, uses the current search from the session.",
            }
        ],
        "responses": {
            "200": {
                "description": "Year distribution data",
                "schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "years": {
                                    "type": "object",
                                    "additionalProperties": {"type": "integer"},
                                },
                                "total": {"type": "integer"},
                            },
                        },
                    },
                },
            },
            "400": {
                "description": "No search selected",
                "schema": {
                    "type": "object",
                    "properties": {"status": {"type": "string"}, "message": {"type": "string"}},
                },
            },
        },
    }
)
def year_distribution():
    """API endpoint to get publication year distribution"""
    search_id = request.args.get("search_id") or session.get("current_search_id")
    if not search_id:
        return api_response(success=False, message="No search selected", status_code=400)
        # Get results
    results = SearchResult.query.filter_by(query_id=search_id).all()
    if not results:
        return api_response(success=False, message="No results found", status_code=404)

    # Extract years
    years = []
    for result in results:
        result_dict = result.to_dict()
        year = (
            result_dict.get("Erscheinungsjahr")
            or result_dict.get("PubYear")
            or result_dict.get("Year")
        )
        if year:
            try:
                year = int(year)
                years.append(year)
            except (ValueError, TypeError):
                pass

    if not years:
        return api_response(success=False, message="No year data available", status_code=404)

    # Count occurrences
    year_counts = {}
    for year in years:
        if year in year_counts:
            year_counts[year] += 1
        else:
            year_counts[year] = 1

    # Sort by year
    sorted_years = sorted(year_counts.items())

    response_data = {
        "years": {str(year): count for year, count in sorted_years},
        "total": len(years),
    }

    return api_response(
        success=True, data=response_data, message="Year distribution retrieved successfully"
    )


@analysis_bp.route("/api/analysis/authors", methods=["GET"])
@swag_from(
    {
        "tags": ["Analysis"],
        "summary": "Get top authors from search results",
        "description": "Returns the most frequent authors in the search results",
        "parameters": [
            {
                "name": "search_id",
                "in": "query",
                "type": "integer",
                "required": False,
                "description": "ID of the search query. If not provided, uses the current search from the session.",
            },
            {
                "name": "limit",
                "in": "query",
                "type": "integer",
                "required": False,
                "default": 10,
                "description": "Maximum number of authors to return",
            },
        ],
        "responses": {
            "200": {
                "description": "Top authors data",
                "schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "authors": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "count": {"type": "integer"},
                                        },
                                    },
                                },
                                "total": {"type": "integer"},
                            },
                        },
                    },
                },
            },
            "400": {
                "description": "No search selected",
                "schema": {
                    "type": "object",
                    "properties": {"status": {"type": "string"}, "message": {"type": "string"}},
                },
            },
        },
    }
)
def top_authors():
    """API endpoint to get top authors"""
    search_id = request.args.get("search_id") or session.get("current_search_id")
    limit = request.args.get("limit", 10, type=int)

    if not search_id:
        return api_response(success=False, message="No search selected", status_code=400)

    # Get results
    results = SearchResult.query.filter_by(query_id=search_id).all()
    if not results:
        return api_response(success=False, message="No results found", status_code=404)

    # Extract authors
    all_authors = []
    for result in results:
        result_dict = result.to_dict()

        # Handle different field names
        authors = (
            result_dict.get("Authors") or result_dict.get("Autoren") or result_dict.get("Creator")
        )

        if authors:
            if isinstance(authors, list):
                all_authors.extend(authors)
            elif isinstance(authors, str):
                # Try to split by common separators
                for separator in [",", ";", " and ", " und "]:
                    if separator in authors:
                        all_authors.extend([a.strip() for a in authors.split(separator)])
                        break
                else:
                    all_authors.append(authors)

    if not all_authors:
        return api_response(success=False, message="No author data available", status_code=404)

    # Count occurrences
    author_counts = {}
    for author in all_authors:
        if author in author_counts:
            author_counts[author] += 1
        else:
            author_counts[author] = 1

    # Get top authors based on limit
    top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    # Format for API response
    authors_data = [{"name": author, "count": count} for author, count in top_authors]

    return api_response(
        success=True,
        data={"authors": authors_data, "total": len(all_authors)},
        message="Top authors retrieved successfully",
    )
