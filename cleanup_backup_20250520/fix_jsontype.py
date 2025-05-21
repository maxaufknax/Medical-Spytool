#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - JSONType Fix

This script specifically fixes the duplicate JSONType class in models.py
"""

import os
import sys
from pathlib import Path


def main():
    """Fix duplicate JSONType class in models.py"""
    models_path = Path("backend/models.py")

    if not models_path.exists():
        print(f"Error: {models_path} not found")
        return 1

    try:
        # Read the file
        with open(models_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Count JSONType class declarations
        jsontype_count = content.count("class JSONType")
        print(f"Found {jsontype_count} JSONType class declarations")

        if jsontype_count <= 1:
            print("No duplicate JSONType class found. Nothing to fix.")
            return 0

        # Remove the duplicate section - specific pattern match
        duplicate_pattern = """from sqlalchemy.dialects import postgresql
from sqlalchemy.types import TypeDecorator, TEXT
import json

# JSON type that works with both SQLite and PostgreSQL
class JSONType(TypeDecorator):
    impl = TEXT"""

        if duplicate_pattern in content:
            fixed_content = content.replace(duplicate_pattern, "")

            # Write back to file
            with open(models_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)

            print("Successfully removed duplicate JSONType class")
            return 0
        else:
            print("Could not find the exact duplicate pattern. Trying alternative approach...")

            # Find the position of all JSONType class declarations
            positions = []
            pos = -1
            while True:
                pos = content.find("class JSONType", pos + 1)
                if pos == -1:
                    break
                positions.append(pos)

            if len(positions) >= 2:
                # Find a good cut-off point between the first JSONType class and the second
                first_pos = positions[0]
                second_pos = positions[1]

                # Look for the end of the first JSONType implementation
                # We'll use the next class or import statement as a marker
                next_class_pos = content.find("class ", first_pos + 10)
                next_import_pos = content.find("import ", first_pos + 10)

                if next_class_pos != -1 and next_class_pos < second_pos:
                    cut_pos = next_class_pos
                elif next_import_pos != -1 and next_import_pos < second_pos:
                    cut_pos = next_import_pos
                else:
                    # If we can't find a good marker, use a position a bit before the second JSONType
                    # Find the last newline before second_pos
                    line_break_pos = content.rfind("\n", 0, second_pos)
                    if line_break_pos != -1:
                        # Find an earlier line break for safety
                        for _ in range(3):  # Look for a few lines up
                            prev_break = content.rfind("\n", 0, line_break_pos - 1)
                            if prev_break != -1:
                                line_break_pos = prev_break
                            else:
                                break
                        cut_pos = line_break_pos
                    else:
                        cut_pos = second_pos - 10  # Arbitrary backup

                # Keep content before cut_pos and after second_pos
                part1 = content[:cut_pos]

                # Find the end of the second JSONType implementation
                # Look for the next class or import after second_pos
                next_class_after_second = content.find("class ", second_pos + 10)
                next_import_after_second = content.find("import ", second_pos + 10)

                if next_class_after_second != -1:
                    part2 = content[next_class_after_second:]
                elif next_import_after_second != -1:
                    part2 = content[next_import_after_second:]
                else:
                    # If we can't find the end, look for a good line break
                    end_pos = second_pos + 10
                    while True:
                        line_break = content.find("\n", end_pos)
                        if line_break == -1:
                            break
                        end_pos = line_break + 1
                        # Look for a non-empty, non-whitespace line
                        if (
                            content[end_pos : end_pos + 10].strip()
                            and not content[end_pos : end_pos + 4].isspace()
                        ):
                            break

                    part2 = content[end_pos:]

                # Combine parts
                fixed_content = part1 + part2

                # Write back to file
                with open(models_path, "w", encoding="utf-8") as f:
                    f.write(fixed_content)

                print("Successfully removed duplicate JSONType class using position-based approach")
                return 0
            else:
                print("Could not locate duplicate JSONType classes for removal")
                return 1

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    print("\n=== MedicalSpy JSONType Fix ===\n")
    result = main()
    if result == 0:
        print("\n✅ Fix completed successfully")
    else:
        print("\n❌ Fix failed")
    sys.exit(result)
