#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for database connectors
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.connectors import DatabaseConnector, DNBConnector, PubMedConnector


class TestDatabaseConnector(unittest.TestCase):
    """Test the base DatabaseConnector class"""

    def test_constructor(self):
        """Test constructor sets default values"""
        connector = DatabaseConnector(api_key="test_key")
        self.assertEqual(connector.api_key, "test_key")
        self.assertEqual(connector.name, "Generic Database")
        self.assertEqual(connector.max_results_per_page, 100)
        self.assertEqual(connector.search_fields, [])
        self.assertIsNone(connector.last_error)
        self.assertEqual(connector.connection_status, "Not connected")

    def test_get_methods(self):
        """Test the basic getter methods"""
        connector = DatabaseConnector()
        self.assertEqual(connector.get_available_fields(), [])
        self.assertEqual(connector.get_max_results_per_page(), 100)
        self.assertEqual(connector.get_citation_count("any_id"), "N/A")

    def test_construct_query(self):
        """Test query construction"""
        connector = DatabaseConnector()
        
        # Test with just a base query
        self.assertEqual(connector.construct_query("test"), "test")
        
        # Test with additional terms
        self.assertEqual(
            connector.construct_query("test", additional_terms="additional"),
            "(test) AND (additional)"
        )


class TestDNBConnector(unittest.TestCase):
    """Test the DNB connector"""

    def test_constructor(self):
        """Test DNB connector constructor"""
        connector = DNBConnector(api_key="test_key")
        self.assertEqual(connector.api_key, "test_key")
        self.assertEqual(connector.name, "Deutsche Nationalbibliothek")
        self.assertEqual(connector.max_results_per_page, 1000)
        self.assertGreater(len(connector.search_fields), 0)

    @patch('requests.get')
    def test_search_page(self, mock_get):
        """Test the search_page method with mocked requests"""
        # Configure the mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<xml>test</xml>"
        mock_get.return_value = mock_response
        
        # Create connector and call search_page
        connector = DNBConnector()
        result = connector.search_page("test_query", 1, 10)
        
        # Verify the mock was called correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs['params']['query'], "test_query")
        self.assertEqual(kwargs['params']['startRecord'], "1")
        self.assertEqual(kwargs['params']['maximumRecords'], "10")
        
        # Verify the result
        self.assertEqual(result, "<xml>test</xml>")


class TestPubMedConnector(unittest.TestCase):
    """Test the PubMed connector"""

    def test_constructor(self):
        """Test PubMed connector constructor"""
        connector = PubMedConnector(api_key="test_key")
        self.assertEqual(connector.api_key, "test_key")
        self.assertEqual(connector.name, "PubMed")
        self.assertGreater(connector.max_results_per_page, 0)
        self.assertGreater(len(connector.search_fields), 0)


if __name__ == '__main__':
    unittest.main()