#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Fix SQLite JSONB Issue

This script fixes the issue with JSONB type in SQLite by:
1. Creating a new .env file if it doesn't exist
2. Ensuring the SQLAlchemy backend uses appropriate JSON type based on database
3. Setting up proper database URL
"""

import os
import sys
import shutil
from pathlib import Path

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# Function to create a proper .env file
def create_env_file():
    env_file = Path(".env")
    env_example = Path(".env.example")

    # Don't overwrite if exists
    if env_file.exists():
        print(f"✓ Found existing .env file at {env_file.absolute()}")
        return

    if env_example.exists():
        print(f"Creating .env file from template...")
        shutil.copy(env_example, env_file)

        # Update the file with proper SQLite configuration
        with open(env_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Ensure SQLite is used
        content = content.replace(
            "# DATABASE_URL=postgresql://username:password@localhost:5432/medicalspy",
            "# DATABASE_URL=postgresql://username:password@localhost:5432/medicalspy\n# Using SQLite for development",
        )

        with open(env_file, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✓ Created .env file with SQLite configuration")
    else:
        # Create a minimal .env file
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(
                """# MedicalSpy Environment Variables
# Datenbank Konfiguration - SQLite
DATABASE_URL=sqlite:///instance/medicalspy.db

# Webserver Einstellungen
PORT=5000
HOST=127.0.0.1

# Session Secret für Entwicklung
SESSION_SECRET=dev_secret_key_change_in_production

# Logging-Konfiguration
LOG_LEVEL=DEBUG
LOG_TO_FILE=TRUE
"""
            )
        print(f"✓ Created minimal .env file with SQLite configuration")


# Ensure instance directory exists
def ensure_instance_dir():
    instance_dir = Path("instance")
    if not instance_dir.exists():
        instance_dir.mkdir()
        print(f"✓ Created instance directory")
    else:
        print(f"✓ Instance directory already exists")


# Fix the JSONB type issue in models.py
def fix_models_json_type():
    models_file = Path("backend/models.py")
    if not models_file.exists():
        print(f"✕ Could not find models.py at {models_file.absolute()}")
        return False

    # Read the current content
    with open(models_file, "r", encoding="utf-8") as f:
        content = f.readlines()

    # Look for imports and add SQLAlchemy imports for dialect detection
    imports_end = 0
    for i, line in enumerate(content):
        if line.strip() == "# Initialize SQLAlchemy":
            imports_end = i
            break

    new_imports = [
        "from sqlalchemy.dialects import postgresql\n",
        "from sqlalchemy.types import TypeDecorator, TEXT\n",
        "import json\n",
        "\n",
        "# JSON type that works with both SQLite and PostgreSQL\n",
        "class JSONType(TypeDecorator):\n",
        "    impl = TEXT\n",
        "    \n",
        "    def load_dialect_impl(self, dialect):\n",
        "        if dialect.name == 'postgresql':\n",
        "            from sqlalchemy.dialects.postgresql import JSON\n",
        "            return dialect.type_descriptor(JSON())\n",
        "        else:\n",
        "            return dialect.type_descriptor(self.impl)\n",
        "    \n",
        "    def process_bind_param(self, value, dialect):\n",
        "        if value is None:\n",
        "            return None\n",
        "        if dialect.name == 'postgresql':\n",
        "            return value\n",
        "        return json.dumps(value)\n",
        "    \n",
        "    def process_result_value(self, value, dialect):\n",
        "        if value is None:\n",
        "            return None\n",
        "        if dialect.name == 'postgresql':\n",
        "            return value\n",
        "        if isinstance(value, str):\n",
        "            return json.loads(value)\n",
        "        return value\n",
        "\n",
    ]

    # Insert custom JSON type after imports
    content = content[:imports_end] + new_imports + content[imports_end:]

    # Fix the SearchResult model's result_data field
    for i, line in enumerate(content):
        if "result_data = db.Column(db.Text, " in line:
            content[i] = (
                "    result_data = db.Column(JSONType, nullable=False)  # Store as JSON - works with SQLite and PostgreSQL\n"
            )

    # Write changes back to file
    with open(models_file, "w", encoding="utf-8") as f:
        f.writelines(content)

    print(f"✓ Fixed JSON type in models.py")
    return True


def main():
    print("===== MedicalSpy Database Fix Script =====")

    # Create .env file if it doesn't exist
    create_env_file()

    # Ensure instance directory exists
    ensure_instance_dir()

    # Fix models.py
    if fix_models_json_type():
        print("\n✅ Fixes applied successfully!")
        print("\nYou can now run the application with:")
        print("  python run.py")
        return 0
    else:
        print("\n❌ Failed to apply all fixes")
        return 1


if __name__ == "__main__":
    sys.exit(main())
