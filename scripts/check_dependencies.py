#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Dependency Checker

This script verifies that all required dependencies are installed and compatible.
It helps to identify missing or incompatible packages before running the application.
"""

import sys
import importlib
import subprocess
import platform
import re
import argparse
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError


def get_terminal_width():
    """Get the width of the terminal for pretty formatting"""
    try:
        import shutil

        return shutil.get_terminal_size().columns
    except:
        return 80


def parse_requirements(req_file):
    """
    Parse a requirements file and extract package name and version constraints

    Args:
        req_file (str): Path to requirements file

    Returns:
        dict: Dictionary of package names to version constraints
    """
    requirements = {}

    try:
        with open(req_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#") or line.startswith("//"):
                    continue

                # Handle optional dependencies
                if line.startswith("# ") and "Uncomment if" in line:
                    continue

                # Remove inline comments
                if "#" in line:
                    line = line[: line.index("#")]

                # Extract package name and version constraint
                match = re.match(r"^([a-zA-Z0-9_\-]+)([<>=!~]+.+)?$", line.strip())
                if match:
                    package = match.group(1)
                    version_constraint = match.group(2) if match.group(2) else None
                    requirements[package] = version_constraint
    except Exception as e:
        print(f"Error parsing requirements file: {e}")

    return requirements


def check_installed_packages(requirements):
    """
    Check if all required packages are installed and compatible

    Args:
        requirements (dict): Dictionary of package names to version constraints

    Returns:
        tuple: (missing_packages, incompatible_packages, installed_packages)
    """
    missing = []
    incompatible = []
    installed = []

    for package, version_constraint in requirements.items():
        try:
            # Try to get the installed version
            installed_version = version(package)

            # Check if version constraint is met
            if version_constraint:
                # Simple version check - this is not a complete implementation
                # of all possible constraints, but covers most common cases
                constraint_met = True

                if "==" in version_constraint:
                    required_version = version_constraint.replace("==", "").strip()
                    constraint_met = installed_version == required_version
                elif ">=" in version_constraint:
                    required_version = version_constraint.replace(">=", "").strip()
                    constraint_met = installed_version >= required_version
                elif ">" in version_constraint:
                    required_version = version_constraint.replace(">", "").strip()
                    constraint_met = installed_version > required_version
                elif "<=" in version_constraint:
                    required_version = version_constraint.replace("<=", "").strip()
                    constraint_met = installed_version <= required_version
                elif "<" in version_constraint:
                    required_version = version_constraint.replace("<", "").strip()
                    constraint_met = installed_version < required_version

                if not constraint_met:
                    incompatible.append((package, installed_version, version_constraint))
                else:
                    installed.append((package, installed_version, version_constraint))
            else:
                installed.append((package, installed_version, None))

        except PackageNotFoundError:
            missing.append(package)
        except Exception as e:
            print(f"Error checking package {package}: {e}")
            missing.append(package)

    return missing, incompatible, installed


def check_python_version():
    """
    Check if the Python version is compatible

    Returns:
        tuple: (is_compatible, current_version, required_version)
    """
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    required_version = "3.8.0"  # Minimum required version

    is_compatible = sys.version_info.major >= 3 and sys.version_info.minor >= 8

    return is_compatible, current_version, required_version


def check_operating_system():
    """
    Check the operating system and return info

    Returns:
        tuple: (os_name, os_version)
    """
    system = platform.system()
    version = platform.version()
    release = platform.release()

    if system == "Windows":
        return f"{system} {release}", version
    elif system == "Darwin":
        return "macOS", version
    else:
        return f"{system} {release}", version


def check_database_drivers():
    """
    Check if database drivers are available

    Returns:
        dict: Dictionary of database types to availability status
    """
    drivers = {
        "SQLite": False,
        "PostgreSQL": False,
        "MySQL/MariaDB": False,
    }

    # Check SQLite
    try:
        import sqlite3

        drivers["SQLite"] = True
    except:
        pass

    # Check PostgreSQL
    try:
        import psycopg2

        drivers["PostgreSQL"] = True
    except:
        pass

    # Check MySQL
    try:
        import MySQLdb

        drivers["MySQL/MariaDB"] = True
    except:
        try:
            import pymysql

            drivers["MySQL/MariaDB"] = True
        except:
            pass

    return drivers


def check_optional_features():
    """
    Check availability of optional features

    Returns:
        dict: Dictionary of feature names to availability status
    """
    features = {
        "Excel export": False,
        "PDF export": False,
        "Data visualization": False,
        "Internationalization": False,
    }

    # Check Excel export
    try:
        import pandas
        import openpyxl

        features["Excel export"] = True
    except:
        pass

    # Check PDF export (not in requirements but might be useful)
    try:
        import weasyprint

        features["PDF export"] = True
    except:
        pass

    # Check Data visualization
    try:
        import matplotlib

        features["Data visualization"] = True
    except:
        pass

    # Check Internationalization
    try:
        import flask_babel

        features["Internationalization"] = True
    except:
        pass

    return features


def print_section_header(title):
    """Print a section header"""
    width = get_terminal_width()
    print("\n" + "=" * width)
    print(title)
    print("=" * width)


def print_result(status, message, success_symbol="✓", failure_symbol="✗"):
    """Print a result line with status symbol"""
    symbol = success_symbol if status else failure_symbol
    print(f"{symbol} {message}")


def format_table(data, headers, alignment=None):
    """
    Format data as a text table

    Args:
        data (list): List of rows
        headers (list): List of column headers
        alignment (list, optional): List of alignment chars ('<', '>', '^')

    Returns:
        str: Formatted table
    """
    if not data:
        return "No data."

    # Default to left alignment
    if alignment is None:
        alignment = ["<"] * len(headers)

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in data:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    # Create format string for each row
    format_str = " | ".join(["{:" + a + str(w) + "}" for w, a in zip(widths, alignment)])
    separator = "-+-".join(["-" * w for w in widths])

    # Create the table
    result = [format_str.format(*headers)]
    result.append(separator)
    for row in data:
        result.append(format_str.format(*[str(cell) for cell in row]))

    return "\n".join(result)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Verify MedicalSpy dependencies")
    parser.add_argument("--fix", action="store_true", help="Attempt to install missing packages")
    parser.add_argument(
        "--upgrade", action="store_true", help="Upgrade packages to compatible versions"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show more detailed information"
    )
    args = parser.parse_args()

    print_section_header("MedicalSpy Dependency Checker")

    # Find the project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    req_file = project_root / "project_requirements.txt"

    if not req_file.exists():
        print(f"Requirements file not found: {req_file}")
        return 1

    # Check Python version
    python_compat, python_version, python_required = check_python_version()
    print_section_header("Python Environment")
    print_result(
        python_compat, f"Python version: {python_version} (required: >= {python_required})"
    )

    # Check operating system
    os_name, os_version = check_operating_system()
    print(f"Operating system: {os_name} {os_version}")

    # Parse requirements
    requirements = parse_requirements(req_file)
    print(f"\nFound {len(requirements)} required packages in {req_file}")

    # Check installed packages
    missing, incompatible, installed = check_installed_packages(requirements)

    # Print results
    print_section_header("Package Status")
    print_result(
        not missing and not incompatible,
        f"Required packages: {len(installed)} installed, {len(missing)} missing, {len(incompatible)} incompatible",
    )

    # Show missing packages
    if missing:
        print("\nMissing packages:")
        for package in missing:
            constraint = requirements.get(package, "")
            print(f"  - {package}{constraint or ''}")

        if args.fix:
            print("\nAttempting to install missing packages...")
            missing_specs = [f"{p}{requirements.get(p, '')}" for p in missing]
            cmd = [sys.executable, "-m", "pip", "install"] + missing_specs
            subprocess.call(cmd)

            # Check again
            missing, incompatible, installed = check_installed_packages(requirements)
            print_result(not missing, f"After installation: {len(missing)} packages still missing")

    # Show incompatible packages
    if incompatible:
        print("\nIncompatible packages:")
        for package, installed_ver, constraint in incompatible:
            print(f"  - {package} (installed: {installed_ver}, required: {constraint})")

        if args.upgrade:
            print("\nAttempting to upgrade incompatible packages...")
            to_upgrade = [f"{p[0]}{requirements.get(p[0], '')}" for p in incompatible]
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade"] + to_upgrade
            subprocess.call(cmd)

            # Check again
            missing, incompatible, installed = check_installed_packages(requirements)
            print_result(
                not incompatible, f"After upgrade: {len(incompatible)} packages still incompatible"
            )

    # Show detailed info for installed packages if verbose
    if args.verbose and installed:
        print("\nInstalled packages:")
        table_data = []
        for package, installed_ver, constraint in installed:
            req_str = constraint if constraint else "any"
            table_data.append([package, installed_ver, req_str])

        # Sort by package name
        table_data.sort(key=lambda x: x[0].lower())

        print(format_table(table_data, ["Package", "Installed", "Required"], ["<", "<", "<"]))

    # Check database drivers
    print_section_header("Database Support")
    drivers = check_database_drivers()
    for driver, available in drivers.items():
        print_result(
            available, f"{driver} support: {'Available' if available else 'Not available'}"
        )

    # Check optional features
    print_section_header("Optional Features")
    features = check_optional_features()
    for feature, available in features.items():
        print_result(available, f"{feature}: {'Available' if available else 'Not available'}")

    # Summary
    print_section_header("Summary")
    all_ok = python_compat and not missing and not incompatible
    print_result(
        all_ok,
        (
            "All dependencies are satisfied and compatible!"
            if all_ok
            else "Some dependencies are missing or incompatible."
        ),
    )

    if not all_ok:
        if missing:
            print("\nTo install missing packages:")
            print(
                f"  pip install {' '.join([p + (requirements.get(p, '') or '') for p in missing])}"
            )
        if incompatible:
            print("\nTo upgrade incompatible packages:")
            print(
                f"  pip install --upgrade {' '.join([p[0] + (requirements.get(p[0], '') or '') for p in incompatible])}"
            )

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
