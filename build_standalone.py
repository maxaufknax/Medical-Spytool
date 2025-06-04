#!/usr/bin/env python3
"""
Enhanced standalone build script for Medical-Spytool
Creates a distributable package that works across platforms
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path
import zipfile
import tempfile

class StandaloneBuild:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.source_dir = self.project_dir / "dnb_spytool"
        self.dist_dir = self.project_dir / "dist"
        self.build_dir = self.project_dir / "build_temp"
        
    def clean_build(self):
        """Clean previous build artifacts"""
        print("🧹 Cleaning previous builds...")
        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_minimal_requirements(self):
        """Get minimal requirements without heavy dependencies"""
        return [
            "requests>=2.25.0",
            "beautifulsoup4>=4.9.0", 
            "pandas>=1.3.0",
            "openpyxl>=3.0.0",
            "lxml>=4.6.0",
            "python-dateutil>=2.8.0",
            "tqdm>=4.60.0",
            # Skip matplotlib, seaborn for lighter build
            "numpy>=1.20.0",
            # Skip biopython for lighter build
        ]
    
    def create_portable_app(self):
        """Create a portable Python application"""
        print("📦 Creating portable Python application...")
        
        app_dir = self.dist_dir / "Medical-Spytool-Portable"
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy source code
        source_dest = app_dir / "dnb_spytool"
        shutil.copytree(self.source_dir, source_dest)
        
        # Create launcher script
        launcher_script = app_dir / "run_medical_spytool.py"
        launcher_content = '''#!/usr/bin/env python3
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
'''
        
        with open(launcher_script, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
        
        # Create Windows batch file
        batch_file = app_dir / "Medical-Spytool.bat"
        batch_content = '''@echo off
echo Starting Medical-Spytool...
cd /d "%~dp0"
python run_medical_spytool.py
if errorlevel 1 (
    echo.
    echo Error: Python not found or failed to start.
    echo Please install Python 3.8+ from https://python.org
    echo.
    pause
)
'''
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        # Create Linux/Mac shell script
        shell_script = app_dir / "medical-spytool.sh"
        shell_content = '''#!/bin/bash
echo "Starting Medical-Spytool..."
cd "$(dirname "$0")"
python3 run_medical_spytool.py || python run_medical_spytool.py
'''
        with open(shell_script, 'w', encoding='utf-8') as f:
            f.write(shell_content)
        os.chmod(shell_script, 0o755)
        
        # Copy documentation
        for doc_file in ["README.md", "LICENSE", "requirements.txt"]:
            src_file = self.project_dir / doc_file
            if src_file.exists():
                shutil.copy2(src_file, app_dir)
        
        return app_dir
    
    def try_pyinstaller_build(self):
        """Attempt PyInstaller build with optimized settings"""
        print("🔧 Attempting PyInstaller build...")
        
        try:
            # Create minimal spec file
            spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Minimal data files
added_files = [
    ('{self.project_dir}/README.md', '.'),
    ('{self.project_dir}/LICENSE', '.'),
]

# Hidden imports for core functionality
hidden_imports = [
    'requests',
    'bs4',
    'pandas',
    'openpyxl',
    'lxml',
    'dateutil',
    'tqdm',
    'numpy',
    'dnb_spytool',
    'dnb_spytool.api',
    'dnb_spytool.gui',
    'dnb_spytool.utils',
    'dnb_spytool.analytics',
]

a = Analysis(
    ['{self.source_dir}/__main__.py'],
    pathex=['{self.project_dir}'],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'seaborn', 
        'scipy',
        'torch',
        'tensorflow',
        'jupyter',
        'IPython',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Medical-Spytool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon=None,
)
'''
            
            spec_file = self.project_dir / "Medical-Spytool-minimal.spec"
            with open(spec_file, 'w', encoding='utf-8') as f:
                f.write(spec_content)
            
            # Try to build
            cmd = [sys.executable, "-m", "PyInstaller", "--clean", str(spec_file)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ PyInstaller build successful!")
                return True
            else:
                print(f"❌ PyInstaller failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ PyInstaller error: {e}")
            return False
    
    def try_auto_py_to_exe(self):
        """Create an auto-py-to-exe configuration for easy building"""
        print("🎯 Creating auto-py-to-exe configuration...")
        
        config = {
            "version": "auto-py-to-exe-configuration_v1",
            "pyinstallerOptions": [
                {
                    "optionDest": "noconfirm",
                    "value": True
                },
                {
                    "optionDest": "filenames",
                    "value": [str(self.source_dir / "__main__.py")]
                },
                {
                    "optionDest": "onefile",
                    "value": True
                },
                {
                    "optionDest": "console",
                    "value": True
                },
                {
                    "optionDest": "name",
                    "value": "Medical-Spytool"
                },
                {
                    "optionDest": "ascii",
                    "value": False
                },
                {
                    "optionDest": "clean_build",
                    "value": True
                },
                {
                    "optionDest": "strip",
                    "value": False
                },
                {
                    "optionDest": "noupx",
                    "value": False
                },
                {
                    "optionDest": "uac_admin",
                    "value": False
                },
                {
                    "optionDest": "uac_uiaccess",
                    "value": False
                },
                {
                    "optionDest": "win_private_assemblies",
                    "value": False
                },
                {
                    "optionDest": "win_no_prefer_redirects",
                    "value": False
                },
                {
                    "optionDest": "bootloader_ignore_signals",
                    "value": False
                },
                {
                    "optionDest": "hiddenimports",
                    "value": "requests,bs4,pandas,openpyxl,lxml,dateutil,tqdm,numpy"
                },
                {
                    "optionDest": "datas",
                    "value": f"{self.project_dir}/README.md;.;{self.project_dir}/LICENSE;."
                },
                {
                    "optionDest": "excludes",
                    "value": "matplotlib,seaborn,scipy,torch,tensorflow,jupyter"
                }
            ]
        }
        
        config_file = self.dist_dir / "auto-py-to-exe-config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        # Create instructions
        instructions = f'''
# Medical-Spytool Build Instructions

## Method 1: Auto-py-to-exe (Recommended for Windows)

1. Install auto-py-to-exe:
   pip install auto-py-to-exe

2. Run auto-py-to-exe:
   auto-py-to-exe

3. Load the configuration:
   - Click "Configuration" -> "Load Configuration File"
   - Select: {config_file}
   - Click "Convert .py to .exe"

## Method 2: PyInstaller Command Line

Run this command in the project directory:

```bash
pyinstaller --onefile --console --name "Medical-Spytool" \\
  --hidden-import requests --hidden-import bs4 --hidden-import pandas \\
  --hidden-import openpyxl --hidden-import lxml --hidden-import dateutil \\
  --hidden-import tqdm --hidden-import numpy \\
  --exclude-module matplotlib --exclude-module seaborn \\
  --exclude-module scipy --exclude-module torch \\
  --add-data "README.md;." --add-data "LICENSE;." \\
  dnb_spytool/__main__.py
```

## Method 3: Portable Python Package

Use the portable package in: {self.dist_dir}/Medical-Spytool-Portable/

This works on any system with Python 3.8+ installed.
'''
        
        instructions_file = self.dist_dir / "BUILD_INSTRUCTIONS.md"
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        return config_file, instructions_file
    
    def create_distribution_package(self):
        """Create final distribution package"""
        print("📦 Creating distribution package...")
        
        # Create ZIP package
        zip_path = self.dist_dir / "Medical-Spytool-Distribution.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add portable app
            portable_dir = self.dist_dir / "Medical-Spytool-Portable"
            if portable_dir.exists():
                for file_path in portable_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = f"Medical-Spytool-Portable/{file_path.relative_to(portable_dir)}"
                        zipf.write(file_path, arcname)
            
            # Add build configs and instructions
            for file_name in ["auto-py-to-exe-config.json", "BUILD_INSTRUCTIONS.md"]:
                file_path = self.dist_dir / file_name
                if file_path.exists():
                    zipf.write(file_path, file_name)
        
        return zip_path
    
    def build(self):
        """Main build process"""
        print("🚀 Starting Medical-Spytool build process...")
        
        # Clean previous builds
        self.clean_build()
        
        # Create portable app (always works)
        portable_app = self.create_portable_app()
        print(f"✅ Portable app created: {portable_app}")
        
        # Try PyInstaller build
        pyinstaller_success = self.try_pyinstaller_build()
        if pyinstaller_success:
            print("✅ PyInstaller executable created!")
        
        # Create auto-py-to-exe config
        config_file, instructions_file = self.try_auto_py_to_exe()
        print(f"✅ Build configuration created: {config_file}")
        print(f"✅ Instructions created: {instructions_file}")
        
        # Create distribution package
        dist_package = self.create_distribution_package()
        print(f"✅ Distribution package created: {dist_package}")
        
        # Print summary
        print("\n" + "="*60)
        print("🎉 BUILD COMPLETE!")
        print("="*60)
        print(f"📂 Distribution folder: {self.dist_dir}")
        print(f"📦 Portable app: {portable_app}")
        print(f"⚙️  Build config: {config_file}")
        print(f"📋 Instructions: {instructions_file}")
        print(f"🗜️  ZIP package: {dist_package}")
        
        if pyinstaller_success:
            exe_path = self.dist_dir / "Medical-Spytool.exe"
            if exe_path.exists():
                print(f"🎯 Executable: {exe_path}")
        
        print("\nNext steps:")
        print("1. For immediate use: Run the portable app")
        print("2. For .exe creation: Follow BUILD_INSTRUCTIONS.md")
        print("3. For distribution: Use the ZIP package")

def main():
    """Entry point"""
    builder = StandaloneBuild()
    builder.build()

if __name__ == "__main__":
    main()
