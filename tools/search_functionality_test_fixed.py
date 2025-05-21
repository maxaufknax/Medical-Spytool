#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Search Functionality Test Script
This script tests the search functionality of the MedicalSpytool application.

Usage:
  python search_functionality_test.py

This script will:
1. Test CSRF validation in search forms
2. Test the complete search workflow from form submission to results display
3. Test search results storage and retrieval
4. Test export functionality for search results
"""

import sys
import requests
import json
import time
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import argparse
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('search_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Print startup message to ensure script execution is visible
print("Starting Medical Spytool search functionality test...")
logger.info("Search functionality test initialized")

# Configuration
BASE_URL = "http://localhost:5000"

class SearchTester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()  # Use session to maintain cookies
    
    def get_csrf_token(self, url):
        """Extract CSRF token from page"""
        response = self.session.get(url)
        if response.status_code != 200:
            logger.error(f"Failed to access {url}: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Try to get token from meta tag
        meta_token = soup.find("meta", {"name": "csrf-token"})
        if meta_token:
            return meta_token.get("content")
        
        # Try to get token from form
        form_token = soup.find("input", {"name": "csrf_token"})
        if form_token:
            return form_token.get("value")
        
        logger.warning(f"No CSRF token found on {url}")
        return None
    
    def test_csrf_validation(self):
        """Test that CSRF validation is working correctly"""
        logger.info("Testing CSRF validation...")
        
        # Try submitting form without CSRF token
        search_url = f"{self.base_url}/search/"
        response = self.session.post(search_url, data={
            "search_mode": "simple",
            "databases": ["PubMed"],
            "query": "test query"
        })
        
        if response.status_code == 400 and "csrf" in response.text.lower():
            logger.info("✓ CSRF validation passed: Form rejected without token")
        else:
            logger.error(f"✗ CSRF validation failed: Form accepted without token (status: {response.status_code})")
            return False
        
        # Try with invalid token
        response = self.session.post(search_url, data={
            "csrf_token": "invalid_token",
            "search_mode": "simple",
            "databases": ["PubMed"],
            "query": "test query"
        })
        
        if response.status_code == 400 and "csrf" in response.text.lower():
            logger.info("✓ CSRF validation passed: Form rejected with invalid token")
        else:
            logger.error(f"✗ CSRF validation failed: Form accepted with invalid token (status: {response.status_code})")
            return False
        
        return True
    
    def test_simple_search(self, query="cancer"):
        """Test simple search functionality"""
        logger.info(f"Testing simple search with query: '{query}'...")
        
        # Get CSRF token
        search_url = f"{self.base_url}/search/"
        csrf_token = self.get_csrf_token(search_url)
        
        if not csrf_token:
            logger.error("Could not get CSRF token for simple search")
            return False
        
        # Submit search
        response = self.session.post(search_url, data={
            "csrf_token": csrf_token,
            "search_mode": "simple",
            "databases": ["PubMed", "Deutsche Nationalbibliothek"],
            "query": query
        }, allow_redirects=True)
        
        if response.status_code != 200:
            logger.error(f"Simple search failed: {response.status_code}")
            return False
        
        # Check if response contains results
        if "ergebnisse" in response.text.lower() or "results" in response.text.lower():
            logger.info("✓ Simple search returned results page")
            
            # Check for actual results
            if "keine ergebnisse gefunden" not in response.text.lower() and "no results found" not in response.text.lower():
                logger.info("✓ Search returned some results")
            else:
                logger.warning("! Search returned no results (this may be valid for some queries)")
            
            return True
        else:
            logger.error("✗ Simple search failed to return results page")
            return False
    
    def test_person_search(self):
        """Test person-based search functionality"""
        logger.info("Testing person-based search...")
        
        # Get CSRF token
        search_url = f"{self.base_url}/search/"
        csrf_token = self.get_csrf_token(search_url)
        
        if not csrf_token:
            logger.error("Could not get CSRF token for person search")
            return False
        
        # Submit search
        response = self.session.post(search_url, data={
            "csrf_token": csrf_token,
            "search_mode": "person",
            "databases": ["PubMed"],
            "persons": ["1"]  # Assuming person ID 1 exists
        }, allow_redirects=True)
        
        if response.status_code != 200:
            logger.error(f"Person search failed: {response.status_code}")
            return False
        
        # Check if response contains results
        if "ergebnisse" in response.text.lower() or "results" in response.text.lower():
            logger.info("✓ Person search returned results page")
            return True
        else:
            logger.error("✗ Person search failed to return results page")
            return False
    
    def test_advanced_search(self):
        """Test advanced search functionality"""
        logger.info("Testing advanced search...")
        
        # Get CSRF token
        search_url = f"{self.base_url}/search/"
        csrf_token = self.get_csrf_token(search_url)
        
        if not csrf_token:
            logger.error("Could not get CSRF token for advanced search")
            return False
        
        # Submit search
        response = self.session.post(search_url, data={
            "csrf_token": csrf_token,
            "search_mode": "advanced",
            "databases": ["PubMed"],
            "keywords": ["cancer", "therapy"],
            "author": "Smith",
            "year_from": "2020",
            "year_to": "2023",
            "title": "treatment"
        }, allow_redirects=True)
        
        if response.status_code != 200:
            logger.error(f"Advanced search failed: {response.status_code}")
            return False
        
        # Check if response contains results
        if "ergebnisse" in response.text.lower() or "results" in response.text.lower():
            logger.info("✓ Advanced search returned results page")
            return True
        else:
            logger.error("✗ Advanced search failed to return results page")
            return False
    
    def test_export_functionality(self):
        """Test export functionality"""
        logger.info("Testing export functionality...")
        
        # First do a search to get some results
        if not self.test_simple_search("cancer treatment"):
            logger.error("Could not perform search for export test")
            return False
        
        # Get CSRF token for export
        export_url = f"{self.base_url}/export/"
        csrf_token = self.get_csrf_token(export_url)
        
        if not csrf_token:
            logger.error("Could not get CSRF token for export")
            return False
        
        # Test CSV export
        csv_response = self.session.post(export_url, data={
            "csrf_token": csrf_token,
            "format": "csv",
            "fields": ["title", "authors", "year", "url"]
        }, allow_redirects=True)
        
        if csv_response.status_code == 200 and "text/csv" in csv_response.headers.get("content-type", ""):
            logger.info("✓ CSV export successful")
        else:
            logger.error(f"✗ CSV export failed: {csv_response.status_code}")
            return False
        
        # Test Excel export
        excel_response = self.session.post(export_url, data={
            "csrf_token": csrf_token,
            "format": "excel",
            "fields": ["title", "authors", "year", "url"]
        }, allow_redirects=True)
        
        if excel_response.status_code == 200 and "application/vnd.ms-excel" in excel_response.headers.get("content-type", ""):
            logger.info("✓ Excel export successful")
        else:
            logger.error(f"✗ Excel export failed: {excel_response.status_code}")
            return False
        
        return True
    
    def run_all_tests(self):
        """Run all search functionality tests"""
        logger.info("Starting search functionality tests...")
        
        results = {
            "csrf_validation": self.test_csrf_validation(),
            "simple_search": self.test_simple_search(),
            "person_search": self.test_person_search(),
            "advanced_search": self.test_advanced_search(),
            "export": self.test_export_functionality()
        }
        
        # Print summary
        logger.info("\n--- Test Results Summary ---")
        for test, result in results.items():
            status = "✓ PASSED" if result else "✗ FAILED"
            logger.info(f"{test}: {status}")
        
        # Determine overall success
        success = all(results.values())
        logger.info(f"\nOverall Test Result: {'✓ PASSED' if success else '✗ FAILED'}")
        
        return results

def generate_html_report(results):
    """Generate an HTML report of test results"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>MedicalSpytool Search Functionality Test Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            .summary { margin: 20px 0; padding: 15px; background-color: #f5f5f5; border-radius: 5px; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; }
            th { background-color: #f2f2f2; text-align: left; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .passed { color: green; }
            .failed { color: red; }
            .timestamp { color: #666; font-size: 0.8em; }
        </style>
    </head>
    <body>
        <h1>MedicalSpytool Search Functionality Test Report</h1>
        <div class="timestamp">Generated on: """ + time.strftime("%Y-%m-%d %H:%M:%S") + """</div>
        
        <div class="summary">
            <h2>Summary</h2>
            <p>Overall result: <span class='""" + ("passed" if all(results.values()) else "failed") + """'>""" + ("PASSED" if all(results.values()) else "FAILED") + """</span></p>
            <p>Tests run: """ + str(len(results)) + """</p>
            <p>Tests passed: """ + str(sum(results.values())) + """</p>
            <p>Tests failed: """ + str(len(results) - sum(results.values())) + """</p>
        </div>
        
        <h2>Detailed Results</h2>
        <table>
            <tr>
                <th>Test</th>
                <th>Result</th>
            </tr>
    """
    
    # Add rows for each test
    for test, result in results.items():
        status = "PASSED" if result else "FAILED"
        status_class = "passed" if result else "failed"
        html += f"""
            <tr>
                <td>{test.replace('_', ' ').title()}</td>
                <td class='{status_class}'>{status}</td>
            </tr>
        """
    
    html += """
        </table>
    </body>
    </html>
    """
    
    # Write to file
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "search_test_report.html")
    with open(report_path, "w") as f:
        f.write(html)
    
    logger.info(f"HTML test report generated at: {report_path}")
    return report_path

def main():
    parser = argparse.ArgumentParser(description="Test Medical Spytool search functionality")
    parser.add_argument("--url", default=BASE_URL, help="Base URL of the application")
    parser.add_argument("--test", choices=["all", "csrf", "simple", "person", "advanced", "export"], 
                        default="all", help="Specific test to run")
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    args = parser.parse_args()
    
    tester = SearchTester(args.url)
    
    results = {}
    if args.test == "all":
        results = tester.run_all_tests()
    elif args.test == "csrf":
        results = {"csrf_validation": tester.test_csrf_validation()}
    elif args.test == "simple":
        results = {"simple_search": tester.test_simple_search()}
    elif args.test == "person":
        results = {"person_search": tester.test_person_search()}
    elif args.test == "advanced":
        results = {"advanced_search": tester.test_advanced_search()}
    elif args.test == "export":
        results = {"export": tester.test_export_functionality()}
    
    # Generate HTML report if requested
    if args.report and isinstance(results, dict):
        report_path = generate_html_report(results)
        print(f"Test report generated at: {report_path}")
    
    # Return success status
    return all(results.values()) if isinstance(results, dict) else results

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
