#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - CSRF Protection Test Script
This script tests the CSRF protection in the MedicalSpy application.

Usage:
  python csrf_test.py

This script will:
1. Try to submit forms without CSRF tokens
2. Verify they are rejected
3. Provide a report on CSRF protection status
"""

import sys
import requests
import random
import string
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

# Configuration
BASE_URL = "http://localhost:5000"
ENDPOINTS = ["/login", "/settings", "/search", "/export", "/persons/add", "/auth/register"]


def generate_random_string(length=10):
    """Generate a random string for form submissions"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def get_form_inputs(url):
    """Extract form inputs including CSRF token from a page"""
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to get {url}: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        forms = soup.find_all("form")

        if not forms:
            print(f"No forms found on {url}")
            return None

        # Get the first form
        form = forms[0]
        action = form.get("action", "")
        method = form.get("method", "post").lower()

        # Determine target URL
        if not action:
            target_url = url
        elif action.startswith("http"):
            target_url = action
        elif action.startswith("/"):
            parsed_url = urlparse(url)
            target_url = f"{parsed_url.scheme}://{parsed_url.netloc}{action}"
        else:
            # Relative URL
            target_url = url.rstrip("/") + "/" + action

        # Extract all input fields
        inputs = {}
        for input_field in form.find_all(["input", "select", "textarea"]):
            name = input_field.get("name")
            if name:
                # For password fields, use a random password
                if input_field.get("type") == "password":
                    inputs[name] = generate_random_string(12)
                # For checkboxes or radio buttons that are checked
                elif input_field.get("type") in ["checkbox", "radio"] and input_field.get(
                    "checked"
                ):
                    inputs[name] = input_field.get("value", "on")
                # For other fields
                else:
                    inputs[name] = input_field.get("value", generate_random_string(8))

        # For select fields, get the first option value
        for select in form.find_all("select"):
            name = select.get("name")
            if name:
                options = select.find_all("option")
                if options:
                    inputs[name] = options[0].get("value", "")

        # Extract CSRF token
        csrf_token = None
        csrf_input = form.find("input", attrs={"name": "csrf_token"})
        if csrf_input:
            csrf_token = csrf_input.get("value")

        return {"url": target_url, "method": method, "inputs": inputs, "csrf_token": csrf_token}

    except Exception as e:
        print(f"Error extracting form from {url}: {str(e)}")
        return None


def test_csrf_protection(url, form_data):
    """Test if the form is protected against CSRF attacks"""
    if not form_data:
        return {"url": url, "status": "UNKNOWN", "details": "Could not extract form data"}

    target_url = form_data["url"]
    method = form_data["method"]
    inputs = form_data["inputs"].copy()

    # Test 1: Submit without CSRF token
    if "csrf_token" in inputs:
        print(f"Testing CSRF protection on {target_url}...")
        csrf_token = inputs.pop("csrf_token")

        try:
            if method == "post":
                response = requests.post(target_url, data=inputs)
            else:
                response = requests.get(target_url, params=inputs)

            # Check if the request was rejected
            if response.status_code == 400:
                return {
                    "url": url,
                    "status": "PROTECTED",
                    "details": "Request rejected with 400 Bad Request (CSRF token missing)",
                }
            elif "csrf" in response.text.lower():
                return {
                    "url": url,
                    "status": "PROTECTED",
                    "details": "Request rejected with csrf error message",
                }
            else:
                return {
                    "url": url,
                    "status": "VULNERABLE",
                    "details": f"Request accepted without CSRF token (Status code: {response.status_code})",
                }
        except Exception as e:
            return {"url": url, "status": "ERROR", "details": f"Error during test: {str(e)}"}
    else:
        return {"url": url, "status": "NOT APPLICABLE", "details": "No CSRF token found in form"}


def main():
    """Main function to test CSRF protection"""
    print("=== MedicalSpy CSRF Protection Test ===\n")

    results = []
    for endpoint in ENDPOINTS:
        url = f"{BASE_URL}{endpoint}"
        print(f"\nChecking {url}...")

        form_data = get_form_inputs(url)
        if form_data:
            result = test_csrf_protection(url, form_data)
            results.append(result)

    # Print summary
    print("\n=== CSRF Protection Test Results ===")
    protected_count = sum(1 for r in results if r["status"] == "PROTECTED")
    vulnerable_count = sum(1 for r in results if r["status"] == "VULNERABLE")

    print(f"\nTotal endpoints tested: {len(results)}")
    print(f"Protected endpoints: {protected_count}")
    print(f"Vulnerable endpoints: {vulnerable_count}")
    print(f"Other (N/A or Error): {len(results) - protected_count - vulnerable_count}")

    print("\nDetails:")
    for result in results:
        status_color = {
            "PROTECTED": "\033[92m",  # Green
            "VULNERABLE": "\033[91m",  # Red
            "NOT APPLICABLE": "\033[93m",  # Yellow
            "ERROR": "\033[93m",  # Yellow
            "UNKNOWN": "\033[93m",  # Yellow
        }.get(result["status"], "")
        reset_color = "\033[0m"

        print(f"  {result['url']}: {status_color}{result['status']}{reset_color}")
        print(f"    {result['details']}")


if __name__ == "__main__":
    main()
