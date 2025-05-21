#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Test Runner Script

This script automatically discovers and runs tests for the MedicalSpy application.
It can be used to run all tests or specific test modules/directories.

Usage:
    python run_tests.py [--path PATH] [--verbose] [--coverage] [--html-report]
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path


def run_tests(test_path=None, verbosity=1, coverage=False, html_report=False, collect_only=False):
    """
    Run tests using pytest

    Args:
        test_path (str, optional): Specific path to test file or directory
        verbosity (int): Verbosity level for test output
        coverage (bool): Whether to run with coverage reporting
        html_report (bool): Whether to generate HTML coverage report
        collect_only (bool): Only collect tests, don't execute them

    Returns:
        bool: True if tests pass, False otherwise
    """
    # Check for SQLite database compatibility
    try:
        from backend.models import JSONType

        print("✓ SQLite compatibility check passed: JSONType class is present")
    except ImportError:
        print(
            "⚠️ Warning: JSONType class not found in models. SQLite compatibility might be an issue."
        )
        print("   Consider running fix_database.py first.")

    # Try to activate virtual environment if it exists
    venv_path = Path(__file__).parent / "venv"
    if venv_path.exists():
        if os.name == "nt":  # Windows
            python_exe = venv_path / "Scripts" / "python.exe"
        else:  # Unix/Linux/Mac
            python_exe = venv_path / "bin" / "python"

        if python_exe.exists():
            print(f"✓ Using virtual environment Python: {python_exe}")
            python_command = str(python_exe)
        else:
            python_command = sys.executable
    else:
        python_command = sys.executable

    print(f"✓ Using Python interpreter: {python_command}")

    # Ensure pytest is installed
    try:
        print("Ensuring pytest and pytest-cov are installed...")
        process = subprocess.run(
            [python_command, "-m", "pip", "install", "pytest", "pytest-cov"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
        )

        if process.returncode != 0:
            print(f"⚠️ Warning: Error installing pytest: {process.stderr}")
        else:
            print("✓ pytest and pytest-cov successfully installed/verified")
    except Exception as e:
        print(f"⚠️ Warning: Error installing pytest: {e}")

    # Base pytest command
    cmd = [python_command, "-m", "pytest"]

    # Add verbosity flags
    if verbosity > 0:
        cmd.append("-v")
    if verbosity > 1:
        cmd.append("-v")  # -vv for max verbosity

    # Collect only flag - useful for test validation
    if collect_only:
        cmd.append("--collect-only")
        print("ℹ️ Running in collection-only mode (tests will not be executed)")

    # Add test path if specified
    if test_path:
        cmd.append(str(Path(test_path)))
        print(f"ℹ️ Running tests from specified path: {test_path}")
    else:
        tests_dir = Path(__file__).parent / "tests"
        cmd.append(str(tests_dir))
        print(f"ℹ️ Running all tests from: {tests_dir}")

    # Add coverage if requested
    if coverage:
        cmd.append("--cov=backend")
        if html_report:
            coverage_dir = Path(__file__).parent / "coverage_report"
            cmd.append(f"--cov-report=html:{coverage_dir}")
            print(f"ℹ️ Coverage HTML report will be generated at: {coverage_dir}")
        else:
            cmd.append("--cov-report=term")
            print("ℹ️ Coverage report will be displayed in the terminal")
    print(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=False)

        if result.returncode != 0:
            print(f"\n❌ Tests failed with exit code: {result.returncode}")
            if result.returncode == 5:
                print(
                    "   Hint: Exit code 5 often indicates an import error or a library not being installed."
                )
                print(
                    "   Try installing missing dependencies with: pip install -r project_requirements.txt"
                )
            elif result.returncode == 2:
                print("   Hint: Exit code 2 often indicates a syntax error or other Python error.")
                print("   Check the test output above for more details.")
        else:
            print("\n✅ All tests passed successfully!")

        # Return True if tests passed (exit code 0)
        return result.returncode == 0
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MedicalSpy tests")
    parser.add_argument("--test-path", help="Specific test file or directory to run")
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=1,
        help="Increase output verbosity (use -vv for more detail)",
    )
    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Run tests with coverage reporting"
    )
    parser.add_argument("--html-report", action="store_true", help="Generate HTML coverage report")
    parser.add_argument(
        "--collect-only", action="store_true", help="Only collect tests without executing them"
    )
    args = parser.parse_args()

    print(f"Starting MedicalSpy test runner from {Path(__file__).absolute()}")
    print(f"Python executable: {sys.executable}")
    print(f"Working directory: {os.getcwd()}")

    # Run tests with specified args
    success = run_tests(
        test_path=args.test_path,
        verbosity=args.verbose,
        coverage=args.coverage,
        html_report=args.html_report,
        collect_only=args.collect_only,
    )

    # Set exit code based on test success/failure
    sys.exit(0 if success else 1)
