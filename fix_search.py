#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Search Fix Script

This script fixes issues with the search functionality in Medical Spytool.
It resets the database and restores a clean state.
"""

import os
import sys
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_utc_now():
    """Get current UTC time"""
    return datetime.now(timezone.utc)

def reset_csrf_sessions():
    """Reset all Flask sessions to fix CSRF issues"""
    try:
        # Get the Flask session directory
        base_dir = os.path.abspath(os.path.dirname(__file__))
        instance_dir = os.path.join(base_dir, 'instance')
        session_dir = os.path.join(instance_dir, 'sessions')
        
        if os.path.exists(session_dir):
            # Backup sessions first
            backup_dir = os.path.join(base_dir, 'backups', f'sessions_{get_utc_now().strftime("%Y%m%d_%H%M%S")}')
            os.makedirs(backup_dir, exist_ok=True)
            
            session_files = [f for f in os.listdir(session_dir) if os.path.isfile(os.path.join(session_dir, f))]
            
            logger.info(f"Found {len(session_files)} session files to backup")
            
            if session_files:
                for file in session_files:
                    source = os.path.join(session_dir, file)
                    dest = os.path.join(backup_dir, file)
                    shutil.copy2(source, dest)
                    os.remove(source)
                logger.info(f"Backed up and removed {len(session_files)} session files")
            
        return True
    except Exception as e:
        logger.error(f"Error resetting sessions: {str(e)}")
        return False

def reset_database():
    """Reset the database to fix search-related issues"""
    try:
        # First try to import and use the application's reset_db functions
        sys.path.append(os.path.abspath(os.path.dirname(__file__)))
        
        try:
            from backend.models import db
            from backend.app import app
            
            logger.info("Resetting database using app context")
            with app.app_context():
                # Backup the database first
                db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
                if os.path.exists(db_path):
                    backup_path = f"{db_path}.backup_{get_utc_now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(db_path, backup_path)
                    logger.info(f"Database backed up to {backup_path}")
                
                # Drop and recreate tables
                db.drop_all()
                db.create_all()
                logger.info("Database tables dropped and recreated")
                
            return True
        except ImportError:
            logger.warning("Could not import app modules, falling back to direct database reset")
            
            # Direct approach - find and delete the database file
            base_dir = os.path.abspath(os.path.dirname(__file__))
            instance_dir = os.path.join(base_dir, 'instance')
            db_file = os.path.join(instance_dir, 'medicalspy.db')
            
            if os.path.exists(db_file):
                backup_path = f"{db_file}.backup_{get_utc_now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(db_file, backup_path)
                logger.info(f"Database backed up to {backup_path}")
                os.remove(db_file)
                logger.info(f"Database file {db_file} removed")
            
            return True
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        return False

def fix_search_js_file():
    """Fix the search.js file to properly handle CSRF tokens"""
    try:
        js_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'backend', 'static', 'js', 'search.js')
        
        if os.path.exists(js_path):
            # Back up original file
            backup_path = f"{js_path}.backup_{get_utc_now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(js_path, backup_path)
            logger.info(f"search.js backed up to {backup_path}")
            
            # Create simplified version of the file
            with open(js_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix indentation and syntax errors
            fixed_content = """/**
 * MedicalSpy - Search module - Fixed version
 * This file contains functions for search functionality.
 */

// Global variables to store persons data and selected persons
let allPersons = [];
let selectedPersons = new Set();
let lastSearchQuery = '';

// Helper function to get a cookie by name
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

// Function to synchronize CSRF token from cookie to form
function syncCsrfToken() {
    const tokenFromCookie = getCookie('csrf_token');
    const tokenInput = document.querySelector('input[name="csrf_token"]');
    
    if (tokenFromCookie && tokenInput) {
        // Update form token if it differs from cookie token
        if (tokenInput.value !== tokenFromCookie) {
            console.log('Synchronizing CSRF token from cookie to form');
            tokenInput.value = tokenFromCookie;
        }
        return tokenInput.value;
    } else if (tokenInput && !tokenInput.value) {
        console.error('No CSRF token available in cookie or form');
    }
    return null;
}

// Initialize search functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize CSRF token handling first
    syncCsrfToken();
    
    // Set up an interval to periodically check and refresh the CSRF token
    setInterval(syncCsrfToken, 60000); // Check every minute
    
    // Then initialize the search form
    initializeSearchForm();
    initializePersonsData();
});

// Initialize form handlers
function initializeSearchForm() {
    const searchForm = document.getElementById('searchForm');
    if (!searchForm) return;

    const searchModeInput = document.getElementById('searchMode');
    const searchModeTabs = document.getElementById('searchModeTabs');
    
    // Update search mode when tabs change
    if (searchModeTabs) {
        searchModeTabs.addEventListener('show.bs.tab', function(event) {
            const activeTab = event.target.id;
            switch(activeTab) {
                case 'simple-search-tab':
                    searchModeInput.value = 'simple';
                    break;
                case 'person-search-tab':
                    searchModeInput.value = 'person';
                    break;
                case 'advanced-search-tab':
                    searchModeInput.value = 'advanced';
                    break;
            }
        });
    }
    
    // Handle form submission
    searchForm.addEventListener('submit', function(event) {
        // First sync the CSRF token from cookie to form
        const csrfToken = syncCsrfToken();
        
        // Verify CSRF token exists after synchronizing
        if (!csrfToken) {
            event.preventDefault();
            console.error('Missing CSRF token even after sync attempt');
            alert('Sicherheitstoken fehlt. Bitte laden Sie die Seite neu.');
            return false;
        }
        
        // Get active tab to determine which search mode is active
        const activeTab = document.querySelector('#searchModeTabs .nav-link.active');
        if (!activeTab) {
            console.warn('No active tab found');
        } else {
            const tabId = activeTab.id;
            if (tabId === 'simple-search-tab') {
                // Check simple search fields
                const simpleQuery = document.querySelector('#simple-search input[name="simple_query_content"]');
                if (simpleQuery && !simpleQuery.value.trim()) {
                    event.preventDefault();
                    alert('Bitte geben Sie einen Suchbegriff ein.');
                    return false;
                }
            }
        }
        
        // Validate database selection
        const databases = Array.from(document.querySelectorAll('input[name="databases"]:checked'));
        if (databases.length === 0) {
            event.preventDefault();
            alert('Bitte mindestens eine Datenbank auswählen.');
            return false;
        }
        
        // Show loading indicator
        const searchButton = document.querySelector('button[type="submit"]');
        if (searchButton) {
            searchButton.disabled = true;
            searchButton.innerHTML = '<span class="spinner-border spinner-border-sm mr-2"></span> Suche läuft...';
        }
        
        // Let the form submit naturally
        return true;
    });
}

// Initialize persons data
function initializePersonsData() {
    if (window.allPersons && Array.isArray(window.allPersons)) {
        allPersons = window.allPersons;
        console.log('Persons data initialized:', allPersons.length + ' persons loaded');
    }
}
"""
            # Write the fixed content
            with open(js_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
                
            logger.info(f"search.js file fixed successfully")
            return True
        else:
            logger.error(f"search.js file not found at {js_path}")
            return False
    except Exception as e:
        logger.error(f"Error fixing search.js file: {str(e)}")
        return False

def main():
    """Main function to fix search functionality"""
    logger.info("Starting Medical Spytool search fix")
    
    # 1. Reset CSRF sessions
    if reset_csrf_sessions():
        logger.info("✅ Sessions reset successful")
    else:
        logger.error("❌ Sessions reset failed")
    
    # 2. Reset database
    if reset_database():
        logger.info("✅ Database reset successful")
    else:
        logger.error("❌ Database reset failed")
    
    # 3. Fix search.js file
    if fix_search_js_file():
        logger.info("✅ search.js file fixed successfully")
    else:
        logger.error("❌ Failed to fix search.js file")
    
    logger.info("Medical Spytool search fix complete")

if __name__ == "__main__":
    main()
