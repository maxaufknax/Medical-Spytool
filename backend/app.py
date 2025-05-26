#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Main Application File
This file initializes and runs the Flask application.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

from datetime import timedelta 
from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
    session,
    flash 
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_login import LoginManager
# from flask_babel import _ # Temporarily commented out for Babel disabling
# from flask_babel import Babel # Removed
from flask_session import Session 
import click 
from flask.cli import with_appcontext 

from backend.config import Config, DevelopmentConfig, ProductionConfig, TestingConfig
from backend.models import db, User 
from backend.csrf_config import init_csrf_protection 
from backend.utils import log_message, get_log_messages, clear_log_messages
# from backend.i18n import init_babel # Temporarily commented out for Babel disabling

migrate = Migrate()
csrf = CSRFProtect() 
# babel = Babel()      # Removed global babel instance
login_manager = LoginManager()
login_manager.login_view = "auth.login"
# login_manager.login_message = _("Bitte melden Sie sich an, um auf diese Seite zuzugreifen.") # Babel disabled
login_manager.login_message = "Bitte melden Sie sich an, um auf diese Seite zuzugreifen." # Raw string
login_manager.login_message_category = "info"

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    click.echo('Dropping existing database tables...')
    db.drop_all()
    click.echo('Creating new database tables...')
    db.create_all()
    click.echo('Initialized the database.')

def create_app(config_class=None):
    app = Flask(__name__, instance_relative_config=True)
    # Use app.logger for consistency after app object is created
    # print(f"Flask app created. Instance path: {app.instance_path}")
    
    try:
        os.makedirs(app.instance_path)
        app.logger.info(f"Instance directory created at: {app.instance_path}")
    except OSError:
        app.logger.info(f"Instance directory ensured at: {app.instance_path}")
        pass 

    if config_class:
        app.config.from_object(config_class)
        app.logger.info(f"Loaded config from class: {config_class.__name__}")
    else:
        env = os.environ.get('FLASK_ENV', 'development')
        if env == 'production':
            app.config.from_object(ProductionConfig)
        elif env == 'testing':
            app.config.from_object(TestingConfig)
        else:
            app.config.from_object(DevelopmentConfig)
        app.logger.info(f"Loaded {env} config via FLASK_ENV or default.")

    app.config.from_pyfile('config.py', silent=True)
    app.logger.info(f"Attempted to load instance/config.py. Silent: True")

    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback_secret_key_123!@#')
        app.logger.warning("SECRET_KEY was not set, using fallback.")
        
    app.config.setdefault('SESSION_TYPE', 'filesystem')
    app.config.setdefault('SESSION_FILE_DIR', os.path.join(app.instance_path, 'flask_session'))
    if app.config['SESSION_TYPE'] == 'filesystem' and not os.path.exists(app.config['SESSION_FILE_DIR']):
        os.makedirs(app.config['SESSION_FILE_DIR'])
        app.logger.info(f"Created SESSION_FILE_DIR at {app.config['SESSION_FILE_DIR']}")

    app.config.setdefault('SESSION_PERMANENT', True) 
    app.config.setdefault('PERMANENT_SESSION_LIFETIME', timedelta(days=7)) 
    Session(app) 
    app.logger.info(f"Flask-Session initialized with type: {app.config['SESSION_TYPE']}")

    default_db_uri = f"sqlite:///{os.path.join(app.instance_path, 'medicalspy.db')}"
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', default_db_uri)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.logger.info(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")

    db.init_app(app)
    app.logger.info("SQLAlchemy initialized.")
    migrate.init_app(app, db)
    app.logger.info("Migrate initialized.")
    
    init_csrf_protection(app, csrf) 
    app.logger.info("Custom CSRF protection initialized.")

    # init_babel(app) # Temporarily disable Babel initialization by commenting out this line
    app.logger.info("Babel initialization via backend.i18n.init_babel is TEMPORARILY DISABLED.")
    login_manager.init_app(app)
    app.logger.info("LoginManager initialized.")

    app.config['WTF_CSRF_TIME_LIMIT'] = None 
    app.logger.info("WTF_CSRF_TIME_LIMIT set to None for testing.")

    log_level = logging.DEBUG if app.debug else logging.INFO # Adjusted from app.testing
    
    for handler in logging.root.handlers[:]: # Clear root handlers
        logging.root.removeHandler(handler)
    logging.basicConfig(level=log_level,
                        format='%(asctime)s %(levelname)s %(name)s: %(message)s [in %(pathname)s:%(lineno)d]')
    
    if not app.debug and not app.testing:
        logs_dir_from_config = app.config.get('LOG_FILE', 'logs/medicalspy.log') 
        logs_folder = os.path.dirname(logs_dir_from_config)
        if not os.path.exists(logs_folder):
            os.makedirs(logs_folder)
            # app.logger.info(f"Created logs directory: {logs_folder}") # app.logger might not be configured yet
            print(f"Created logs directory: {logs_folder}") 
            
        file_handler = RotatingFileHandler(logs_dir_from_config, maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        # file_handler.setLevel(logging.INFO) # Will inherit from root or app.logger
        app.logger.addHandler(file_handler) 
    
    app.logger.info(f"Flask logging configured. App logger effective level: {logging.getLevelName(app.logger.getEffectiveLevel())}")
    app.logger.debug("This is a DEBUG message from create_app.") # Test debug logging

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Removed local get_locale function and @babel.localeselector decorator
    # Also removed diagnostic prints for the local 'babel' object.
    app.logger.info("Babel localeselector handling is skipped as Babel is disabled.")

    from backend.blueprints import all_blueprints
    app.logger.info("Registering blueprints...")
    for bp_name, bp_instance, url_prefix in all_blueprints:
        app.register_blueprint(bp_instance, url_prefix=url_prefix)
        app.logger.info(f"Registered blueprint: {bp_name} with prefix: {url_prefix}")

    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully or already exist via db.create_all().")
        except Exception as e:
            app.logger.error(f"Error creating database tables via db.create_all(): {e}", exc_info=True)

    if 'init_db_command' in globals():
        app.cli.add_command(init_db_command)
        app.logger.info("init-db CLI command registered.")
    else:
        app.logger.warning("init_db_command not found for CLI registration.")

    @app.route('/health')
    def health_check():
        return "OK", 200
        
    @app.route('/log-test')
    def log_test_route(): 
        log_message("Test log message from /log-test route", "INFO")
        return "Log test message sent."

    @app.route('/view-logs')
    def view_logs_route():
        return jsonify(get_log_messages())

    @app.route('/clear-logs')
    def clear_logs_route():
        clear_log_messages()
        return "Logs cleared."
        
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f"Page not found: {request.url} - {error}")
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {request.url} - {error}", exc_info=True)
        return render_template('errors/500.html'), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        app.logger.error(f"CSRF error: {e.description} at {request.url} - Referrer: {request.referrer}")
        if request.is_json or "application/json" in request.accept_mimetypes:
            return jsonify(error="CSRF token error", details=e.description), 400
        
        # flash(_('Das Formular ist abgelaufen oder ungültig. Bitte versuchen Sie es erneut.'), 'warning') # Babel disabled
        flash('Das Formular ist abgelaufen oder ungültig. Bitte versuchen Sie es erneut.', 'warning') # Raw string
        redirect_url = request.referrer or url_for('main.index')
        app.logger.info(f"Redirecting to {redirect_url} after CSRF error.")
        return redirect(redirect_url)
        
    app.logger.info("create_app function finished successfully.")
    return app

if __name__ == "__main__":
    flask_env = os.environ.get('FLASK_ENV')
    config_class_to_use = DevelopmentConfig 
    if flask_env == 'production':
        config_class_to_use = ProductionConfig
    elif flask_env == 'testing':
        config_class_to_use = TestingConfig
        
    app = create_app(config_class=config_class_to_use)
    host = os.environ.get('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    
    print(f"Starting Flask app with FLASK_ENV='{flask_env}', Config Class: {config_class_to_use.__name__}, Debug Mode: {app.debug} on {host}:{port}")
    app.run(host=host, port=port)
