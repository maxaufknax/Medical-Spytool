#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Settings Blueprint
This blueprint handles application settings.
"""

import os
import json
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
    current_app,
)
from flask_login import login_required
from backend.models import db, Setting
from backend.utils import log_message

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Handle settings management"""
    if request.method == "POST":
        # Update settings
        settings = {
            "output_path": request.form.get("output_path"),
            "person_list_path": request.form.get("person_list_path"),
            "unique_filenames": request.form.get("unique_filenames") == "on",
            "default_database": request.form.get("default_database", "PubMed"),
        }

        # Handle output columns (multiselect)
        output_columns = request.form.getlist("output_columns")
        if output_columns:
            settings["output_columns"] = output_columns

        # NOTE: We no longer save API keys to the database
        # They are handled through environment variables only

        # Save all settings except API keys
        for key, value in settings.items():
            setting = Setting.query.filter_by(key=key).first()

            # Convert value to string for storage
            if isinstance(value, (list, dict)):
                setting_value = json.dumps(value)
            elif isinstance(value, bool):
                setting_value = str(value).lower()
            else:
                setting_value = str(value)

            if setting:
                # Update existing
                setting.value = setting_value
            else:
                # Create new
                setting = Setting(key=key, value=setting_value)
                db.session.add(setting)

        db.session.commit()
        log_message("Settings updated successfully", "INFO")

        # Update session
        session_settings = Setting.get_settings_dict()
        session["settings"] = session_settings

        flash("Einstellungen erfolgreich gespeichert.", "success")
        return redirect(url_for("settings.index"))

    # GET request - show settings form
    settings = Setting.get_settings_dict()

    # Add API key status information (but not the actual keys)
    api_key_status = {
        "pubmed_api_key_configured": bool(current_app.config.get("PUBMED_API_KEY", ""))
    }

    return render_template("settings.html", settings=settings, api_key_status=api_key_status)


@settings_bp.route("/api/settings", methods=["GET"])
def get_settings():
    """API endpoint to get all settings (excluding sensitive data)"""
    settings = Setting.get_settings_dict()

    # Remove sensitive data
    if "pubmed_api_key" in settings:
        del settings["pubmed_api_key"]

    return jsonify(settings)
