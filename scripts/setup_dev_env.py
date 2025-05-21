#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Development Environment Setup Script

This script helps set up a complete development environment for the MedicalSpy application.
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
import argparse


def is_command_available(command):
    """Check if a command is available in the system"""
    try:
        subprocess.run([command, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def run_command(command, description=None):
    """Run a shell command and handle errors"""
    if description:
        print(f"\n{description}...")

    try:
        result = subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def setup_virtual_environment(python_executable="python", venv_dir=".venv"):
    """Create and activate a virtual environment"""
    print("\nSetting up virtual environment...")

    # Check if virtual environment already exists
    venv_path = Path(venv_dir)
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}")
        return True

    # Create virtual environment
    cmd = f"{python_executable} -m venv {venv_dir}"
    if run_command(cmd):
        print(f"✓ Created virtual environment at {venv_dir}")
        return True
    else:
        print("✗ Failed to create virtual environment")
        return False


def install_requirements():
    """Install required Python packages"""
    print("\nInstalling required packages...")

    cmd = "pip install -r project_requirements.txt"
    if run_command(cmd):
        print("✓ Installed required packages")
        return True
    else:
        print("✗ Failed to install required packages")
        return False


def create_env_file():
    """Create .env file if it doesn't exist"""
    print("\nSetting up environment configuration...")

    env_path = Path(".env")
    if env_path.exists():
        print(".env file already exists")
        return True

    # Create a basic .env file
    try:
        with open(env_path, "w") as f:
            f.write("# Medical Spytool Environment Variables\n")
            f.write("DATABASE_URL=sqlite:///instance/medicalspy.db\n")
            f.write("SESSION_SECRET=dev_secret_key_change_in_production\n")
            f.write("LOG_LEVEL=DEBUG\n")
            f.write("PORT=5000\n")
            f.write("\n# Add your API keys and other configuration here\n")
            f.write("# PUBMED_API_KEY=\n")

        print("✓ Created .env file with default settings")
        return True
    except Exception as e:
        print(f"✗ Failed to create .env file: {e}")
        return False


def create_directories():
    """Create required directories if they don't exist"""
    print("\nCreating required directories...")

    directories = ["logs", "output", "person_lists", "instance", "backups"]

    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True)
                print(f"✓ Created directory: {directory}")
            except Exception as e:
                print(f"✗ Failed to create directory {directory}: {e}")


def initialize_database():
    """Initialize the database"""
    print("\nInitializing database...")

    cmd = "python init_db.py"
    if run_command(cmd):
        print("✓ Database initialized")
        return True
    else:
        print("✗ Failed to initialize database")
        return False


def setup_development_environment(use_venv=True, init_db=True):
    """Set up the complete development environment"""
    print("=" * 80)
    print("Medical Spytool Development Environment Setup")
    print("=" * 80)

    # Create directories
    create_directories()

    # Create .env file
    create_env_file()

    # Set up virtual environment
    if use_venv:
        setup_virtual_environment()

    # Install requirements
    install_requirements()

    # Initialize database
    if init_db:
        initialize_database()

    print("\n" + "=" * 80)
    print("Setup complete! You can now start development.")
    print("\nTo start the application:")
    print("  python run.py")
    print("\nTo run tests:")
    print("  python run_tests.py")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup Medical Spytool development environment")
    parser.add_argument("--no-venv", action="store_true", help="Skip virtual environment setup")
    parser.add_argument("--no-db-init", action="store_true", help="Skip database initialization")
    args = parser.parse_args()

    setup_development_environment(use_venv=not args.no_venv, init_db=not args.no_db_init)
