#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for configuration module
"""

import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import sys
import json

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.config import load_settings, save_settings, get_env_setting, ensure_directories


class TestConfig(unittest.TestCase):
    """Test the configuration module"""

    @patch("os.environ.get")
    def test_get_env_setting(self, mock_get):
        """Test environment variable retrieval"""
        # Test with default value
        mock_get.return_value = None
        result = get_env_setting("TEST_VAR", default="default_value")
        mock_get.assert_called_with("TEST_VAR", "default_value")
        self.assertEqual(result, "default_value")

        # Test with existing environment variable
        mock_get.return_value = "env_value"
        result = get_env_setting("TEST_VAR", default="default_value")
        self.assertEqual(result, "env_value")

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    @patch("backend.config.save_non_sensitive_settings")
    def test_load_settings(self, mock_save, mock_json_load, mock_file_open, mock_exists):
        """Test settings loading"""
        # Setup mocks
        mock_exists.return_value = True
        mock_json_load.return_value = {
            "output_path": "./custom_output",
            "person_list_path": "./custom_persons",
            "pubmed_api_key": "test_key",
        }

        # Call function
        settings = load_settings()

        # Verify results
        self.assertEqual(settings["output_path"], "./custom_output")
        self.assertEqual(settings["person_list_path"], "./custom_persons")
        self.assertEqual(settings["pubmed_api_key"], "test_key")
        mock_save.assert_called_once()

    @patch("os.makedirs")
    def test_ensure_directories(self, mock_makedirs):
        """Test directory creation"""
        settings = {"output_path": "./test_output", "person_list_path": "./test_persons"}

        ensure_directories(settings)

        # Verify both directories were created
        self.assertEqual(mock_makedirs.call_count, 2)
        mock_makedirs.assert_any_call("./test_output", exist_ok=True)
        mock_makedirs.assert_any_call("./test_persons", exist_ok=True)


if __name__ == "__main__":
    unittest.main()
