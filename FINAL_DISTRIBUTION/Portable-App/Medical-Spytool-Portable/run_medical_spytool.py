#!/usr/bin/env python3
"""
Medical-Spytool Launcher
Portable launcher that handles dependencies
"""

import sys
import os
import subprocess
import importlib.util

def check_and_install_package(package_name, pip_name=None):
    """Check if package is installed, install if not"""
    if pip_name is None:
        pip_name = package_name
    
    try:
        spec = importlib.util.find_spec(package_name)
        if spec is None:
            raise ImportError
        print(f"✅ {package_name} is available")
        return True
    except ImportError:
        print(f"📦 Installing {package_name}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", pip_name, "--user"
            ])
            return True
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package_name}")
            return False

def main():
    """Main launcher function"""
    print("🚀 Starting Medical-Spytool...")
    print("📋 Checking dependencies...")
    
    # Minimal required packages
    required_packages = [
        ("requests", "requests>=2.25.0"),
        ("bs4", "beautifulsoup4>=4.9.0"),
        ("pandas", "pandas>=1.3.0"),
        ("openpyxl", "openpyxl>=3.0.0"),
        ("lxml", "lxml>=4.6.0"),
        ("dateutil", "python-dateutil>=2.8.0"),
        ("tqdm", "tqdm>=4.60.0"),
        ("numpy", "numpy>=1.20.0"),
    ]
    
    # Check and install packages
    all_available = True
    for package_name, pip_name in required_packages:
        if not check_and_install_package(package_name, pip_name):
            all_available = False
    
    if not all_available:
        print("❌ Some dependencies could not be installed.")
        print("Please run: pip install -r requirements.txt")
        input("Press Enter to continue anyway...")
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    try:
        # Import and run the application
        from dnb_spytool.__main__ import main as app_main
        app_main()
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
