#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medical Spytool - Search Functionality Test
This script tests the search functionality of the Medical Spytool application.
"""

import os
import sys
import json
import requests
import logging
from pathlib import Path
from pprint import pprint

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Base URL for requests
BASE_URL = "http://127.0.0.1:5000"

def get_csrf_token():
    """Get CSRF token from the search page"""
    try:
        # First get a session cookie
        session = requests.Session()
        response = session.get(f"{BASE_URL}/search/")
        
        if response.status_code != 200:
            logging.error(f"Failed to get search page: {response.status_code}")
            return None, None
        
        # Check for csrf_token in cookies
        csrf_token = session.cookies.get('csrf_token')
        if not csrf_token:
            logging.error("No CSRF token found in cookies")
            
        # Also try to extract the token from the HTML form
        import re
        match = re.search(r'<input[^>]*name="csrf_token"[^>]*value="([^"]*)"', response.text)
        form_token = match.group(1) if match else None
        
        logging.info(f"CSRF token from cookie: {csrf_token}")
        logging.info(f"CSRF token from form: {form_token}")
        
        return session, csrf_token or form_token
    
    except Exception as e:
        logging.error(f"Error getting CSRF token: {e}")
        return None, None

def run_simple_search(session, csrf_token, query="cancer", databases=["PubMed"]):
    """Run a simple search with the given parameters"""
    try:
        # Prepare search form data
        form_data = {
            "csrf_token": csrf_token,
            "search_mode": "simple",
            "simple_query_content": query,
            "databases": databases
        }
        
        logging.info(f"Submitting search: {form_data}")
        
        # Make the search request
        response = session.post(
            f"{BASE_URL}/search/", 
            data=form_data,
            allow_redirects=True
        )
        
        if response.status_code == 200:
            logging.info("Search successful! Results page received.")
            
            # Check if we have any results
            if "Keine Ergebnisse gefunden" in response.text:
                logging.warning("No search results found")
            else:
                # Try to count results from the page
                import re
                result_count_match = re.search(r'([0-9,]+)\s+Ergebnisse gefunden', response.text)
                if result_count_match:
                    result_count = result_count_match.group(1).replace(',', '')
                    logging.info(f"Approximately {result_count} results found")
                else:
                    logging.info("Results found but couldn't determine count")
                
            return True, response.text
        else:
            logging.error(f"Search failed with status code: {response.status_code}")
            return False, response.text
            
    except Exception as e:
        logging.error(f"Error performing search: {e}")
        return False, str(e)

def run_dnb_search(session, csrf_token, query="medizin"):
    """Run a search in the Deutsche Nationalbibliothek"""
    return run_simple_search(
        session=session,
        csrf_token=csrf_token,
        query=query,
        databases=["Deutsche Nationalbibliothek"]
    )

def main():
    """Main test function"""
    logging.info("Starting search functionality test")
    
    # Get CSRF token
    session, csrf_token = get_csrf_token()
    if not csrf_token or not session:
        logging.error("Failed to get CSRF token, exiting")
        return 1
    
    # Run a simple PubMed search
    logging.info("Testing PubMed search...")
    pubmed_success, pubmed_results = run_simple_search(
        session=session,
        csrf_token=csrf_token,
        query="diabetes",
        databases=["PubMed"]
    )
    
    # Run a DNB search
    logging.info("Testing Deutsche Nationalbibliothek search...")
    dnb_success, dnb_results = run_dnb_search(
        session=session,
        csrf_token=csrf_token,
        query="herzinfarkt"
    )
    
    # Run a combined search
    logging.info("Testing combined search...")
    combined_success, combined_results = run_simple_search(
        session=session,
        csrf_token=csrf_token,
        query="kardiologie",
        databases=["PubMed", "Deutsche Nationalbibliothek"]
    )
    
    # Summarize results
    logging.info("\n=== Test Results Summary ===")
    logging.info(f"PubMed Search: {'SUCCESS' if pubmed_success else 'FAILED'}")
    logging.info(f"DNB Search: {'SUCCESS' if dnb_success else 'FAILED'}")
    logging.info(f"Combined Search: {'SUCCESS' if combined_success else 'FAILED'}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
