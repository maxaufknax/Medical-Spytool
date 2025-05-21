#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Test Runner Script

This script automatically discovers and runs tests for the MedicalSpy application.
It can be used to run all tests or specific test modules/directories.

Usage:
    python test_runner.py [--path PATH] [--verbose] [--coverage] [--html-report]
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path


def run_tests(test_path=None, verbosity=1, coverage=False, html_report=False):
    """
    Run tests using pytest

    Args:
        test_path (str, optional): Specific path to test file or directory
        verbosity (int): Verbosity level for test output
        coverage (bool): Whether to run with coverage reporting
        html_report (bool): Whether to generate HTML coverage report

    Returns:
        bool: True if tests passed, False otherwise
    """
    print("=" * 70)
    print(f"Running MedicalSpy tests {'with coverage' if coverage else ''}")
    print("=" * 70)

    # Default to 'tests' directory if no path specified
    if test_path is None:
        test_path = "tests"

    # Build command
    cmd = [sys.executable, "-m", "pytest"]

    # Add verbosity flag if requested
    if verbosity > 1:
        cmd.append("-v")

    # Add coverage if requested
    if coverage:
        cmd.extend(["--cov=backend", "--cov-report=term"])
        if html_report:
            cmd.append("--cov-report=html:coverage_report")

    # Add test path
    cmd.append(test_path)

    # Run tests
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    success = result.returncode == 0

    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")

    print("=" * 70)
    return success


def main():
    """Parse command line arguments and run tests"""
    parser = argparse.ArgumentParser(description="Run MedicalSpy tests")
    parser.add_argument("--path", "-p", help="Path to test file or directory")
    parser.add_argument("--verbose", "-v", action="count", default=1, help="Increase verbosity")
    parser.add_argument("--coverage", "-c", action="store_true", help="Run with coverage reporting")
    parser.add_argument(
        "--html-report", "-H", action="store_true", help="Generate HTML coverage report"
    )

    args = parser.parse_args()

    # Add the current directory to the Python path
    sys.path.insert(0, os.path.abspath("."))

    # Run the tests
    success = run_tests(
        test_path=args.path,
        verbosity=args.verbose,
        coverage=args.coverage,
        html_report=args.html_report,
    )

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
