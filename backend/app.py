#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Flask Application Factory
"""

import os
import logging
import click
from datetime import timedelta
from pathlib import Path

from flask import Flask, redirect, url_for
from flask_session import Session
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Import configuration classes
from config import Config, DevelopmentConfig, ProductionConfig, TestingConfig
from models import db
from csrf_config import init_csrf_protection

# Initialize extensions
csrf = CSRFProtect()
migrate = Migrate()
login_manager = LoginManager()

@click.command()
def init_db_command():
    """Initialize the database."""
    from models import db
    db.drop_all()
    db.create_all()
    click.echo('Initialized the database.')

def create_app(config_class=None):
    """Application factory pattern"""
    app = Flask(__name__, instance_relative_config=True)
    
    # Ensure instance directory exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
        app.logger.info(f"Instance directory ensured at: {app.instance_path}")
    except OSError:
        app.logger.info(f"Instance directory already exists at: {app.instance_path}")

    # Load configuration
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
    
    # Ensure SECRET_KEY is set
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback_secret_key_123!@#')
        app.logger.warning("SECRET_KEY was not set, using fallback.")
        
    # Configure Flask-Session
    app.config.setdefault('SESSION_TYPE', 'filesystem')
    app.config.setdefault('SESSION_FILE_DIR', os.path.join(app.instance_path, 'flask_session'))
    if app.config['SESSION_TYPE'] == 'filesystem' and not os.path.exists(app.config['SESSION_FILE_DIR']):
        os.makedirs(app.config['SESSION_FILE_DIR'])
        app.logger.info(f"Created SESSION_FILE_DIR at {app.config['SESSION_FILE_DIR']}")
    app.config.setdefault('SESSION_PERMANENT', True)
    app.config.setdefault('PERMANENT_SESSION_LIFETIME', timedelta(days=7))
    Session(app)
    app.logger.info(f"Flask-Session initialized with type: {app.config['SESSION_TYPE']}")

    # Configure database
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        default_db_uri = f"sqlite:///{os.path.join(app.instance_path, 'medicalspy.db')}"
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', default_db_uri)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.logger.info(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Initialize extensions
    db.init_app(app)
    app.logger.info("SQLAlchemy initialized.")
    
    migrate.init_app(app, db)
    app.logger.info("Migrate initialized.")
    
    init_csrf_protection(app, csrf)
    app.logger.info("Custom CSRF protection initialized.")    # Babel is temporarily disabled
    app.logger.info("Babel initialization is TEMPORARILY DISABLED.")
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Bitte melden Sie sich an, um auf diese Seite zuzugreifen.'
    login_manager.login_message_category = 'info'
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    app.logger.info("LoginManager initialized.")
    
    # Template context processor for CSRF token
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

    # Register blueprints
    from blueprints.main import main_bp
    from blueprints.auth import auth_bp
    from blueprints.search import search_bp
    from blueprints.persons import persons_bp
    from blueprints.settings import settings_bp
    from blueprints.analysis import analysis_bp
    from blueprints.export import export_bp
    from blueprints.logs import logs_bp

    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(persons_bp, url_prefix='/persons')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    app.register_blueprint(export_bp, url_prefix='/export')
    app.register_blueprint(logs_bp, url_prefix='/logs')

    app.logger.info("All blueprints registered successfully.")

    # Add CLI commands
    app.cli.add_command(init_db_command)

    # Create tables
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created/ensured.")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {e}")

    # Root route
    @app.route('/')
    def index():
        return redirect(url_for('main.index'))

    app.logger.info("Flask application created and configured successfully.")
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000)
