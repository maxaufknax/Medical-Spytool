#!/usr/bin/env python3
"""
Build script for creating Medical-Spytool.exe
Creates a standalone executable with all dependencies included.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_spec_file():
    """Create PyInstaller spec file for the Medical Spytool."""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Analysis step
a = Analysis(
    ['dnb_spytool/__main__.py'],
    pathex=['./'],
    binaries=[],
    datas=[
        ('dnb_spytool/analytics/*.py', 'dnb_spytool/analytics'),
        ('dnb_spytool/api/*.py', 'dnb_spytool/api'),
        ('dnb_spytool/gui/*.py', 'dnb_spytool/gui'),
        ('dnb_spytool/utils/*.py', 'dnb_spytool/utils'),
        ('requirements.txt', '.'),
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.figure',
        'matplotlib.pyplot',
        'requests',
        'pandas',
        'numpy',
        'lxml',
        'bs4',
        'wordcloud',
        'xml.etree.ElementTree',
        'urllib.parse',
        'urllib.request',
        'json',
        'csv',
        'openpyxl',
        'dnb_spytool.analytics.analyzer',
        'dnb_spytool.analytics.visualizer',
        'dnb_spytool.api.database_manager',
        'dnb_spytool.api.dnb_client',
        'dnb_spytool.api.pubmed_client',
        'dnb_spytool.gui.main_window',
        'dnb_spytool.utils.exporters',
        'dnb_spytool.utils.validators',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Package step
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Executable step
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
    console=False,  # GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)
'''
    
    with open('Medical-Spytool.spec', 'w') as f:
        f.write(spec_content)
    
    print("✅ PyInstaller spec file created: Medical-Spytool.spec")

def build_executable():
    """Build the executable using PyInstaller."""
    print("🔨 Building Medical-Spytool.exe...")
    
    # Create spec file
    create_spec_file()
    
    # Build with PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        'Medical-Spytool.spec'
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Build successful!")
        return True
    else:
        print("❌ Build failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False

def create_distribution():
    """Create a complete distribution package."""
    print("📦 Creating distribution package...")
    
    # Create distribution directory
    dist_dir = Path('dist_complete')
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()
    
    # Copy executable
    exe_path = Path('dist/Medical-Spytool.exe')
    if exe_path.exists():
        shutil.copy2(exe_path, dist_dir / 'Medical-Spytool.exe')
        print(f"✅ Copied executable to {dist_dir}")
    else:
        exe_path = Path('dist/Medical-Spytool')  # Linux version
        if exe_path.exists():
            shutil.copy2(exe_path, dist_dir / 'Medical-Spytool')
            print(f"✅ Copied executable to {dist_dir}")
        else:
            print("❌ Executable not found!")
            return False
    
    # Copy documentation
    files_to_copy = [
        'README.md',
        'LICENSE',
        'requirements.txt',
        'RELEASE_NOTES_v1.1.md',
        'GITHUB_READY_REPORT.md'
    ]
    
    for file in files_to_copy:
        if Path(file).exists():
            shutil.copy2(file, dist_dir / file)
            print(f"✅ Copied {file}")
    
    # Create usage guide
    usage_guide = '''# Medical Spytool - Usage Guide

## Quick Start

### GUI Mode (Recommended)
Double-click `Medical-Spytool.exe` to start the graphical interface.

### Command Line Mode
Open Command Prompt or Terminal and run:
```
Medical-Spytool.exe --help
```

## Features

### 1. Search Publications
- Single or multiple authors
- DNB (German National Library) database
- PubMed database
- Configurable result limits

### 2. Export Data
- CSV format
- JSON format  
- Excel format
- PDF reports

### 3. Analytics
- Publication timeline charts
- Author productivity analysis
- Subject word clouds
- Database source analysis

## System Requirements
- Windows 10/11 (64-bit)
- No additional software required (standalone executable)
- Internet connection for database searches

## Support
- GitHub: https://github.com/maxaufknax/Medical-Spytool
- Version: 1.1 (Stable)

## License
MIT License - see LICENSE file for details
'''
    
    with open(dist_dir / 'USAGE_GUIDE.md', 'w') as f:
        f.write(usage_guide)
    
    # Create batch files for easy execution
    gui_batch = '''@echo off
echo Starting Medical Spytool GUI...
Medical-Spytool.exe
pause
'''
    
    cli_batch = '''@echo off
echo Medical Spytool Command Line Interface
echo Type "Medical-Spytool.exe --help" for available commands
echo.
cmd /k
'''
    
    with open(dist_dir / 'Start_GUI.bat', 'w') as f:
        f.write(gui_batch)
    
    with open(dist_dir / 'Start_CLI.bat', 'w') as f:
        f.write(cli_batch)
    
    print("✅ Distribution package created successfully!")
    return True

def main():
    """Main build function."""
    print("🚀 Medical Spytool - Executable Builder")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('dnb_spytool').exists():
        print("❌ Error: Please run this script from the Medical-Spytool root directory")
        sys.exit(1)
    
    # Build executable
    if not build_executable():
        print("❌ Build failed!")
        sys.exit(1)
    
    # Create distribution
    if not create_distribution():
        print("❌ Distribution creation failed!")
        sys.exit(1)
    
    print("\n🎉 SUCCESS!")
    print("=" * 50)
    print("✅ Medical-Spytool.exe has been created successfully!")
    print(f"📁 Location: {os.path.abspath('dist_complete')}")
    print("📋 Distribution includes:")
    print("   - Medical-Spytool.exe (standalone executable)")
    print("   - Documentation (README, LICENSE, etc.)")
    print("   - Usage guide")
    print("   - Batch files for easy startup")
    print("\n🚀 Ready for distribution!")

if __name__ == '__main__':
    main()
