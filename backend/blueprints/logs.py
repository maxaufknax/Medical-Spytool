#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Logs Blueprint
This blueprint handles log viewing functionality.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from backend.models import db, LogEntry
from backend.utils import get_log_messages, clear_log_messages
from backend.api_utils import api_response
from flasgger import swag_from

logs_bp = Blueprint("logs", __name__)


@logs_bp.route("/", methods=["GET"])
def index():
    """Show application logs with filtering options"""
    # Get filter parameters
    level = request.args.get("level")
    limit = request.args.get("limit", 100, type=int)

    # Get logs from database with optional filtering
    db_logs = LogEntry.get_logs(limit=limit, level=level)

    # Convert to dictionary form
    logs = [log.to_dict() for log in db_logs]

    # Sort by timestamp (newest first)
    logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return render_template("logs.html", logs=logs, current_level=level, current_limit=limit)


@logs_bp.route("/clear", methods=["POST"])
def clear():
    """Clear application logs"""
    # Clear database logs
    LogEntry.clear_logs()

    flash("Logs wurden erfolgreich gelöscht.", "success")
    return redirect(url_for("logs.index"))


@logs_bp.route("/api/logs", methods=["GET"])
@swag_from(
    {
        "tags": ["Logs"],
        "summary": "Get application logs",
        "description": "Returns application logs with optional filtering by level and limit",
        "parameters": [
            {
                "name": "level",
                "in": "query",
                "type": "string",
                "required": False,
                "description": "Filter logs by level (INFO, WARNING, ERROR, etc.)",
            },
            {
                "name": "limit",
                "in": "query",
                "type": "integer",
                "required": False,
                "default": 100,
                "description": "Maximum number of logs to return",
            },
        ],
        "responses": {
            "200": {
                "description": "List of log entries",
                "schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "logs": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "level": {"type": "string"},
                                            "message": {"type": "string"},
                                            "timestamp": {"type": "string", "format": "date-time"},
                                            "source": {"type": "string"},
                                        },
                                    },
                                },
                                "total": {"type": "integer"},
                            },
                        },
                    },
                },
            }
        },
    }
)
def api_logs():
    """API endpoint to get logs in JSON format"""
    level = request.args.get("level")
    limit = request.args.get("limit", 100, type=int)
    db_logs = LogEntry.get_logs(limit=limit, level=level)
    logs = [log.to_dict() for log in db_logs]

    return api_response(
        success=True,
        data={"logs": logs, "total": len(logs), "filters": {"level": level, "limit": limit}},
        message="Logs retrieved successfully",
    )
