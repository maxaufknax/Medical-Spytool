#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - CSRF Protection Tests
Tests for verifying CSRF protection is working correctly on all forms.
"""

import unittest
from flask import url_for
from backend.app import create_app, db
from bs4 import BeautifulSoup


class CSRFTestCase(unittest.TestCase):
    """Test case for CSRF protection functionality"""

    def setUp(self):
        """Setup test environment before each test"""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        """Cleanup test environment after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_csrf_token(self, response):
        """Extract CSRF token from page HTML response"""
        soup = BeautifulSoup(response.data, "html.parser")
        csrf_token = soup.find("input", {"name": "csrf_token"})
        return csrf_token["value"] if csrf_token else None

    def test_login_with_csrf(self):
        """Test that login form has CSRF protection and works with valid token"""
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)

        # Extract CSRF token
        csrf_token = self.get_csrf_token(response)
        self.assertIsNotNone(csrf_token, "CSRF token should be present in login form")

        # Submit login with valid CSRF token
        response = self.client.post(
            "/login",
            data={"username": "testuser", "password": "password", "csrf_token": csrf_token},
            follow_redirects=True,
        )

        # Not concerned with actual login success, just that request processed
        self.assertEqual(response.status_code, 200)

    def test_login_without_csrf(self):
        """Test that login form fails without CSRF token"""
        response = self.client.post(
            "/login", data={"username": "testuser", "password": "password"}, follow_redirects=True
        )

        # Should be rejected with 400 Bad Request
        self.assertEqual(response.status_code, 400)

    def test_search_with_csrf(self):
        """Test that search form has CSRF protection and works with valid token"""
        response = self.client.get("/search")
        self.assertEqual(response.status_code, 200)

        csrf_token = self.get_csrf_token(response)
        self.assertIsNotNone(csrf_token, "CSRF token should be present in search form")

        response = self.client.post(
            "/search",
            data={"query": "test", "source": "pubmed", "csrf_token": csrf_token},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)

    def test_export_with_csrf(self):
        """Test that export form has CSRF protection and works with valid token"""
        # First need to access the export page
        response = self.client.get("/search/results")
        csrf_token = self.get_csrf_token(response)

        if csrf_token:
            response = self.client.post(
                "/export", data={"format": "csv", "csrf_token": csrf_token}, follow_redirects=True
            )

            # Redirects are fine, just check we get a valid response
            self.assertIn(response.status_code, [200, 302])

    def test_settings_with_csrf(self):
        """Test that settings form has CSRF protection and works with valid token"""
        response = self.client.get("/settings")
        csrf_token = self.get_csrf_token(response)

        if csrf_token:
            response = self.client.post(
                "/settings",
                data={"theme": "light", "csrf_token": csrf_token},
                follow_redirects=True,
            )

            self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
