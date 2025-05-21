#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    flash,
    send_file,
    g,
    abort,
)
from flask_wtf.csrf import CSRFProtect, generate_csrf, CSRFError
from flask_login import LoginManager
from flask_babel import Babel, _
from flask_session import Session
from backend.csrf_config import init_csrf_protection

# Configure logging to console
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Import models after logging configuration
from backend.models import db, User, SearchQuery, SearchResult, Person, Setting, LogEntry
from backend.config import load_settings, save_settings, ensure_directories
from backend.utils import log_message, get_log_messages, clear_log_messages
from backend.i18n import init_babel
from backend.constants import DEFAULT_API_KEY


def get_utc_now():
    """Helper function to get current UTC time"""
    return datetime.now(timezone.utc)


def cleanup_expired_sessions(app):
    """Clean up expired session files"""
    session_dir = app.config['SESSION_FILE_DIR']
    if os.path.exists(session_dir):
        current_time = get_utc_now()
        for session_file in os.listdir(session_dir):
            try:
                file_path = os.path.join(session_dir, session_file)
                # Check if file is older than session lifetime
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path), tz=timezone.utc)
                age = current_time - mtime
                if age > app.config['PERMANENT_SESSION_LIFETIME']:
                    os.remove(file_path)
                    logger.info(f"Removed expired session file: {session_file}")
            except Exception as e:
                logger.error(f"Error cleaning up session file {session_file}: {e}")


def create_app(config_name=None):
    """Create Flask application with appropriate configuration"""
    app = Flask(__name__)

    # Import and use the correct SECRET_KEY from config
    from backend.config import SECRET_KEY
    app.secret_key = SECRET_KEY
    
    # Configure server-side session handling
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'medicalspy_'
    app.config['SESSION_FILE_DIR'] = os.path.join(app.instance_path, 'sessions')

    # Ensure instance and session directories exist
    instance_dir = Path(app.instance_path)
    try:
        instance_dir.mkdir(exist_ok=True, parents=True)
        Path(app.config['SESSION_FILE_DIR']).mkdir(exist_ok=True, parents=True)
        logger.info(f"Instance directory ensured at: {instance_dir}")
    except Exception as e:
        logger.error(f"Failed to create instance directory: {e}")
        raise

    # Configure database
    db_path = instance_dir / "medicalspy.db"
    database_url = f"sqlite:///{db_path}"
    logger.info(f"Database URL: {database_url}")

    # Configure Flask app
    app.config.update(
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            "pool_pre_ping": True,
            "pool_recycle": 280,
            "pool_timeout": 30,
            "max_overflow": 5,
        },
        # Enhanced CSRF protection
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_TIME_LIMIT=3600,
        WTF_CSRF_SSL_STRICT=True,
        WTF_CSRF_CHECK_DEFAULT=True,
        # API Keys from environment variables (with fallbacks)
        PUBMED_API_KEY=os.environ.get("PUBMED_API_KEY", None),
        DNB_API_KEY=os.environ.get("DNB_API_KEY", None),
    )

    # Initialize extensions
    db.init_app(app)
    csrf = CSRFProtect(app)
    init_csrf_protection(app, csrf)
    
    # Initialize server-side session
    Session(app)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Bitte melden Sie sich an, um auf diese Seite zuzugreifen."
    login_manager.login_message_category = "info"

    # Initialize database
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    # Register blueprints
    from backend.blueprints import all_blueprints
    for blueprint in all_blueprints:
        url_prefix = "/" if blueprint.name == "main" else f"/{blueprint.name}"
        app.register_blueprint(blueprint, url_prefix=url_prefix)
        logger.info(f"Registered blueprint: {blueprint.name} with prefix: {url_prefix}")

    # Initialize internationalization
    babel = init_babel(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            logger.error(f"Error loading user {user_id}: {e}")
            return None

    @app.before_request
    def before_request():
        try:
            # Clean up old sessions periodically
            if not hasattr(app, 'last_session_cleanup'):
                app.last_session_cleanup = get_utc_now()
            
            # Clean up every hour
            if get_utc_now() - app.last_session_cleanup > timedelta(hours=1):
                cleanup_expired_sessions(app)
                app.last_session_cleanup = get_utc_now()

            # Set language preference
            g.lang = request.accept_languages.best_match(["de", "en"], default="de")
            
            # Set session timeout
            session.permanent = True
            session.modified = True
            
            # Ensure CSRF token is in session
            if 'csrf_token' not in session:
                session['csrf_token'] = generate_csrf()
                session.modified = True
                logger.debug("CSRF token added to session")
            
        except Exception as e:
            logger.error(f"Error in before_request: {e}")
            g.lang = "de"

    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning(f"404 error: {request.url}")
        return render_template("404.html"), 404

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        logger.error(f"CSRF error: {str(e)}")
        flash("Sicherheitstoken ungültig oder abgelaufen. Bitte laden Sie die Seite neu.", "error")
        return redirect(url_for("main.index")), 302

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        logger.error(f"500 error: {error}")
        return render_template("500.html"), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Log any unhandled exceptions and return a user-friendly error response"""
        logger.error("Unhandled exception:", exc_info=True)
        db.session.rollback()
        return (
            jsonify(
                {
                    "error": "Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.",
                    "details": str(e) if app.debug else None,
                }
            ),
            500,
        )

    return app

# Create the Flask app instance
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
