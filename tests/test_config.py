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

from backend.config import PROJECT_ROOT, INSTANCE_PATH, LOG_DIR_PATH, DEFAULT_SQLITE_DB_PATH


class TestConfig(unittest.TestCase):
    """Test the configuration module"""

    def test_project_paths(self):
        """Test that project paths are correctly set"""
        self.assertTrue(PROJECT_ROOT.exists())
        self.assertTrue(INSTANCE_PATH.exists())
        self.assertTrue(LOG_DIR_PATH.exists())
        
    def test_database_path(self):
        """Test database path configuration"""
        self.assertTrue(str(DEFAULT_SQLITE_DB_PATH).endswith('medicalspy.db'))


if __name__ == "__main__":
    unittest.main()


if __name__ == "__main__":
    unittest.main()
