#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Python Indentation Checker
This script scans Python files for indentation issues and reports them
"""

import os
import sys
import io
import tokenize
from pathlib import Path


def check_file(file_path):
    """Check a file for indentation issues"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        # Try to tokenize the source code - this will raise exceptions for syntax errors
        io_obj = io.StringIO(source)
        tokenize.tokenize(io_obj.readline)
        return True
    except tokenize.TokenError as e:
        print(f"❌ {file_path}: TokenError - {e}")
        return False
    except tokenize.IndentationError as e:
        print(f"❌ {file_path}: IndentationError - {e}")
        return False
    except SyntaxError as e:
        print(f"❌ {file_path}: SyntaxError - {e}")
        return False
    except Exception as e:
        print(f"❌ {file_path}: Error - {e}")
        return False


def scan_directory(directory, include_dirs=None, exclude_dirs=None):
    """Scan a directory recursively for Python files"""
    if include_dirs is None:
        include_dirs = []
    if exclude_dirs is None:
        exclude_dirs = ["venv", "__pycache__", ".git"]

    issues = []

    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        # If include_dirs is specified, only scan those directories
        if include_dirs and not any(inc_dir in root for inc_dir in include_dirs):
            continue

        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                if not check_file(file_path):
                    issues.append(str(file_path))

    return issues


def main():
    """Main function"""
    directory = Path(".")
    include_dirs = ["backend"]  # Focus on the backend directory

    print(f"Scanning Python files in {directory.absolute()}/backend...")
    issues = scan_directory(directory, include_dirs=include_dirs)

    if issues:
        print(f"\n{len(issues)} files have indentation or syntax issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    else:
        print("\n✅ All scanned Python files have correct indentation!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
