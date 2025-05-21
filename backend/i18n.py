#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - i18n Configuration
This module configures Flask-Babel for internationalization.
"""

from flask import request, session, redirect, url_for
from flask_babel import Babel

babel = Babel()


def get_locale():
    """
    Determine the best locale to use for this request.

    The function checks for locale preference in this order:
    1. URL parameter: ?lang=xx
    2. User setting in session
    3. Request headers: Accept-Language
    4. Default to German

    Returns:
        str: The locale code (e.g., 'de', 'en')
    """
    # First check URL args
    locale = request.args.get("lang")
    if locale:
        session["lang"] = locale
        return locale

    # Then check user setting in session
    locale = session.get("lang")
    if locale:
        return locale

    # Then use browser headers
    return request.accept_languages.best_match(["de", "en"], default="de")


def init_babel(app):
    """
    Initialize Flask-Babel with the Flask app.

    Args:
        app: The Flask application instance
    """
    babel.init_app(app, locale_selector=get_locale)

    # Configure available languages
    app.config["BABEL_DEFAULT_LOCALE"] = "de"
    app.config["BABEL_SUPPORTED_LOCALES"] = ["de", "en"]

    return babel
