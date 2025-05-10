#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner for MedicalSpy
"""

import unittest
import sys
import os
import argparse
from pathlib import Path


def run_tests(test_path=None, verbosity=1):
    """
    Run tests using unittest
    
    Args:
        test_path (str, optional): Specific path to test file or directory
        verbosity (int): Verbosity level for test output
    
    Returns:
        bool: True if tests pass, False otherwise
    """
    if test_path:
        # Run specific test file or directory
        test_suite = unittest.defaultTestLoader.discover(
            start_dir=test_path,
            pattern="test_*.py"
        )
    else:
        # Run all tests
        test_suite = unittest.defaultTestLoader.discover(
            start_dir=str(Path(__file__).parent / 'tests'),
            pattern="test_*.py"
        )
    
    test_runner = unittest.TextTestRunner(verbosity=verbosity)
    result = test_runner.run(test_suite)
    
    # Return True if tests passed (no failures or errors)
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run MedicalSpy tests')
    parser.add_argument('--test-path', help='Specific test file or directory to run')
    parser.add_argument('--verbose', '-v', action='count', default=1,
                        help='Increase output verbosity (use -vv for more detail)')
    args = parser.parse_args()
    
    # Run tests with specified args
    success = run_tests(args.test_path, args.verbose)
    
    # Set exit code based on test success/failure
    sys.exit(0 if success else 1)