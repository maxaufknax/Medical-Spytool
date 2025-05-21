#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Main Blueprint
This blueprint handles the main routes of the application.
"""

from flask import Blueprint, render_template, jsonify, redirect, url_for, session
from backend.models import db, Setting

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Main landing page"""
    return render_template("index.html")


@main_bp.route("/health")
def health_check():
    """Health check endpoint for monitoring"""
    status = {"status": "ok", "database": "connected"}

    try:
        # Check database connection
        from sqlalchemy import text

        db.session.execute(text("SELECT 1"))
    except Exception as e:
        status["status"] = "error"
        status["database"] = "disconnected"
        status["error"] = str(e)

    return jsonify(status)
