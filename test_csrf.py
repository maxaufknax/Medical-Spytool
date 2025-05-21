#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - CSRF Token Test

This script tests the CSRF token handling in the Medical Spytool application.
Run this script to verify that CSRF tokens are correctly generated and validated.

Usage:
python test_csrf.py
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://127.0.0.1:5000"  # Default Flask development server
SEARCH_URL = urljoin(BASE_URL, "/search/")
MAX_REDIRECTS = 5  # Maximum number of redirects to follow

def get_csrf_token(html_content):
    """Extract CSRF token from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    token_input = soup.find('input', {'name': 'csrf_token'})
    if token_input and 'value' in token_input.attrs:
        return token_input['value']
    return None

def test_csrf_token():
    """Test CSRF token handling"""
    session = requests.Session()
    
    try:
        # Step 1: Get the search page and extract the CSRF token
        logger.info(f"Requesting search page: {SEARCH_URL}")
        response = session.get(SEARCH_URL, allow_redirects=True)
        response.raise_for_status()
        
        html_content = response.text
        csrf_token = get_csrf_token(html_content)
        
        if not csrf_token:
            logger.error("No CSRF token found in the search page")
            return False
            
        logger.info(f"Found CSRF token: {csrf_token[:5]}...")
        
        # Step 2: Submit the search form with the CSRF token
        search_data = {
            'csrf_token': csrf_token,
            'search_mode': 'simple',
            'simple_query_content': 'test search',
            'databases': ['PubMed']  # Use a test database
        }
        
        logger.info(f"Submitting search form with CSRF token")
        response = session.post(SEARCH_URL, data=search_data, allow_redirects=False)
        
        # Check if the form submission is accepted (redirect indicates success)
        if response.status_code == 302:
            logger.info(f"Search form submission accepted, redirecting to: {response.headers.get('Location')}")
            return True
        else:
            logger.error(f"Search form submission failed with status code: {response.status_code}")
            logger.error(f"Response content: {response.text[:500]}...")
            return False
        
    except Exception as e:
        logger.error(f"Error testing CSRF token: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting CSRF token test")
    success = test_csrf_token()
    
    if success:
        logger.info("CSRF test passed successfully!")
        sys.exit(0)
    else:
        logger.error("CSRF test failed!")
        sys.exit(1)
