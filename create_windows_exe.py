"""
Windows Executable Creator for Medical-Spytool
Creates a standalone .exe file using PyInstaller with Windows-specific optimizations
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json

class WindowsExeBuilder:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.source_dir = self.project_dir / "dnb_spytool"
        self.dist_dir = self.project_dir / "dist_windows"
        
    def create_optimized_spec(self):
        """Create optimized PyInstaller spec for Windows"""
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# Medical-Spytool Windows Executable Spec
# Optimized for standalone distribution

import sys
from pathlib import Path

block_cipher = None

# Application data files
added_files = [
    (r'{self.project_dir}\\README.md', '.'),
    (r'{self.project_dir}\\LICENSE', '.'),
    (r'{self.project_dir}\\requirements.txt', '.'),
]

# Core hidden imports for medical research functionality
hidden_imports = [
    # Core Python packages
    'requests',
    'urllib3', 
    'certifi',
    
    # HTML/XML parsing
    'bs4',
    'lxml',
    'html.parser',
    
    # Data handling
    'pandas',
    'numpy',
    'openpyxl',
    'xlsxwriter',
    
    # Date/time utilities
    'dateutil',
    'dateutil.parser',
    'dateutil.tz',
    
    # Progress bars and utilities
    'tqdm',
    
    # Application modules
    'dnb_spytool',
    'dnb_spytool.__main__',
    'dnb_spytool.api',
    'dnb_spytool.api.dnb_api',
    'dnb_spytool.api.pubmed_api',
    'dnb_spytool.gui',
    'dnb_spytool.gui.main_window',
    'dnb_spytool.utils',
    'dnb_spytool.utils.file_handler',
    'dnb_spytool.utils.validators',
    'dnb_spytool.analytics',
    'dnb_spytool.analytics.analyzer',
    'dnb_spytool.cli',
    
    # GUI libraries (if used)
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
]

# Modules to exclude for smaller executable
excluded_modules = [
    # Heavy scientific packages not essential for core functionality
    'matplotlib',
    'seaborn',
    'scipy',
    'scikit-learn',
    'torch',
    'tensorflow',
    'keras',
    
    # Development and testing
    'pytest',
    'unittest',
    'doctest',
    'pdb',
    'pydoc',
    
    # Jupyter/IPython
    'jupyter',
    'IPython',
    'notebook',
    'jupyterlab',
    
    # Other optional packages
    'PIL',
    'cv2',
    'sqlite3',
    'multiprocessing',
]

a = Analysis(
    [r'{self.source_dir}\\__main__.py'],
    pathex=[r'{self.project_dir}'],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excluded_modules,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate entries
a.datas = list(set(a.datas))

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
    version_file=None,
)

# Optional: Create an installer directory structure
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Medical-Spytool-Installer',
)
'''
        
        spec_file = self.project_dir / "Medical-Spytool-Windows.spec"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        return spec_file
    
    def create_build_script(self):
        """Create Windows batch script for building"""
        batch_content = '''@echo off
echo Building Medical-Spytool for Windows...
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller
        pause
        exit /b 1
    )
)

REM Clean previous builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo.
echo Starting build process...
echo.

REM Build with PyInstaller
pyinstaller --clean Medical-Spytool-Windows.spec

if errorlevel 1 (
    echo.
    echo Build failed! Check the error messages above.
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ================================
    echo Build completed successfully!
    echo ================================
    echo.
    echo Executable location: dist\\Medical-Spytool.exe
    echo Installer directory: dist\\Medical-Spytool-Installer\\
    echo.
)

pause
'''
        
        batch_file = self.project_dir / "build_windows_exe.bat"
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        return batch_file
    
    def create_nsis_installer_script(self):
        """Create NSIS installer script for professional distribution"""
        nsis_content = f'''# Medical-Spytool NSIS Installer Script
# Creates a professional Windows installer

!define APPNAME "Medical-Spytool"
!define COMPANYNAME "Medical Research Tools"
!define DESCRIPTION "Medical Literature Research Tool for DNB and PubMed"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0
!define HELPURL "https://github.com/your-username/Medical-Spytool"
!define UPDATEURL "https://github.com/your-username/Medical-Spytool/releases"
!define ABOUTURL "https://github.com/your-username/Medical-Spytool"
!define INSTALLSIZE 50000  # Estimated size in KB

RequestExecutionLevel admin
InstallDir "$PROGRAMFILES\\${{COMPANYNAME}}\\${{APPNAME}}"
Icon "Medical-Spytool.ico"

# Pages
Page directory
Page instfiles

# Installer sections
Section "install"
    SetOutPath $INSTDIR
    
    # Copy main executable
    File "dist\\Medical-Spytool.exe"
    
    # Copy documentation
    File "README.md"
    File "LICENSE"
    File "requirements.txt"
    
    # Create uninstaller
    WriteUninstaller "$INSTDIR\\uninstall.exe"
    
    # Create start menu shortcuts
    CreateDirectory "$SMPROGRAMS\\${{COMPANYNAME}}"
    CreateShortCut "$SMPROGRAMS\\${{COMPANYNAME}}\\${{APPNAME}}.lnk" "$INSTDIR\\Medical-Spytool.exe"
    CreateShortCut "$SMPROGRAMS\\${{COMPANYNAME}}\\Uninstall.lnk" "$INSTDIR\\uninstall.exe"
    
    # Create desktop shortcut
    CreateShortCut "$DESKTOP\\Medical-Spytool.lnk" "$INSTDIR\\Medical-Spytool.exe"
    
    # Registry entries for Add/Remove Programs
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "DisplayName" "${{APPNAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "UninstallString" "$\\"$INSTDIR\\uninstall.exe$\\""
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "QuietUninstallString" "$\\"$INSTDIR\\uninstall.exe$\\" /S"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "InstallLocation" "$\\"$INSTDIR$\\""
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "DisplayIcon" "$\\"$INSTDIR\\Medical-Spytool.exe$\\""
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "Publisher" "${{COMPANYNAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "HelpLink" "${{HELPURL}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "URLUpdateInfo" "${{UPDATEURL}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "URLInfoAbout" "${{ABOUTURL}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "DisplayVersion" "${{VERSIONMAJOR}}.${{VERSIONMINOR}}.${{VERSIONBUILD}}"
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "VersionMajor" ${{VERSIONMAJOR}}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "VersionMinor" ${{VERSIONMINOR}}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "NoRepair" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "EstimatedSize" ${{INSTALLSIZE}}
SectionEnd

# Uninstaller section
Section "uninstall"
    Delete "$INSTDIR\\Medical-Spytool.exe"
    Delete "$INSTDIR\\README.md"
    Delete "$INSTDIR\\LICENSE"
    Delete "$INSTDIR\\requirements.txt"
    Delete "$INSTDIR\\uninstall.exe"
    
    RMDir "$INSTDIR"
    
    Delete "$SMPROGRAMS\\${{COMPANYNAME}}\\${{APPNAME}}.lnk"
    Delete "$SMPROGRAMS\\${{COMPANYNAME}}\\Uninstall.lnk"
    RMDir "$SMPROGRAMS\\${{COMPANYNAME}}"
    
    Delete "$DESKTOP\\Medical-Spytool.lnk"
    
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}"
SectionEnd
'''
        
        nsis_file = self.project_dir / "Medical-Spytool-Installer.nsi"
        with open(nsis_file, 'w', encoding='utf-8') as f:
            f.write(nsis_content)
        
        return nsis_file
    
    def create_comprehensive_readme(self):
        """Create comprehensive Windows distribution README"""
        readme_content = '''# Medical-Spytool Windows Distribution

## Quick Start

### Option 1: Portable Application (Recommended)
1. Extract the ZIP file to any folder
2. Navigate to `Medical-Spytool-Portable`
3. Double-click `Medical-Spytool.bat` to start

### Option 2: Build Standalone Executable
1. Install Python 3.8+ from https://python.org
2. Open Command Prompt as Administrator
3. Navigate to the extracted folder
4. Run: `build_windows_exe.bat`
5. Find the executable in `dist/Medical-Spytool.exe`

### Option 3: Auto-py-to-exe (GUI Method)
1. Install: `pip install auto-py-to-exe`
2. Run: `auto-py-to-exe`
3. Load configuration: `auto-py-to-exe-config.json`
4. Click "Convert .py to .exe"

## Features

✅ **Medical Literature Search**
- German National Library (DNB) integration
- PubMed database support
- Advanced search filters

✅ **Data Export**
- Excel (XLSX) format
- CSV format
- JSON format

✅ **Analytics & Reporting**
- Publication statistics
- Author analysis
- Visual charts and graphs

✅ **User Interface**
- Command-line interface
- Graphical user interface (GUI)
- Batch processing support

## System Requirements

- **Operating System**: Windows 7, 8, 10, 11 (64-bit)
- **Python**: 3.8+ (for source version)
- **Memory**: 512 MB RAM minimum
- **Storage**: 100 MB free space
- **Internet**: Required for database searches

## Usage Examples

### Command Line
```cmd
# Search for a single author
Medical-Spytool.exe --author "Johann Wolfgang von Goethe"

# Search multiple authors with Excel output
Medical-Spytool.exe --authors "Goethe,Schiller" --format xlsx --output results.xlsx

# Generate analytics report
Medical-Spytool.exe --author "Kafka" --analytics --report-format pdf

# Launch GUI
Medical-Spytool.exe --gui
```

### Graphical Interface
1. Run `Medical-Spytool.exe --gui`
2. Enter author names in the search field
3. Select database (DNB, PubMed, or both)
4. Choose output format
5. Click "Start Search"

## Troubleshooting

### Common Issues

**"Missing Python libraries"**
- Solution: Use the portable version or install missing packages

**"Connection timeout"**
- Solution: Check internet connection and firewall settings

**"Access denied"**
- Solution: Run as Administrator or check antivirus settings

**"Slow performance"**
- Solution: Reduce maximum results or use filters

### Support

For technical support and bug reports:
- GitHub Issues: https://github.com/your-username/Medical-Spytool/issues
- Documentation: https://github.com/your-username/Medical-Spytool/wiki

## License

This software is distributed under the MIT License.
See LICENSE file for details.

## Acknowledgments

- German National Library (DNB) for API access
- PubMed/NCBI for research database
- Open source Python community

---
Medical-Spytool v1.0 - Professional Medical Literature Research Tool
'''
        
        readme_file = self.dist_dir / "README-Windows.md"
        self.dist_dir.mkdir(exist_ok=True)
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        return readme_file
    
    def build(self):
        """Build Windows executable package"""
        print("🚀 Creating Windows executable package...")
        
        # Create output directory
        self.dist_dir.mkdir(exist_ok=True)
        
        # Create optimized spec file
        spec_file = self.create_optimized_spec()
        print(f"✅ Created optimized spec file: {spec_file}")
        
        # Create build script
        batch_file = self.create_build_script()
        print(f"✅ Created build script: {batch_file}")
        
        # Create NSIS installer script
        nsis_file = self.create_nsis_installer_script()
        print(f"✅ Created installer script: {nsis_file}")
        
        # Create comprehensive README
        readme_file = self.create_comprehensive_readme()
        print(f"✅ Created Windows README: {readme_file}")
        
        print("\n" + "="*60)
        print("🎉 WINDOWS PACKAGE CREATED!")
        print("="*60)
        print(f"📂 Build files location: {self.project_dir}")
        print(f"📋 Build script: {batch_file}")
        print(f"⚙️  PyInstaller spec: {spec_file}")
        print(f"📦 NSIS installer: {nsis_file}")
        print(f"📖 Documentation: {readme_file}")
        
        print("\nTo create the .exe file:")
        print("1. Run this on a Windows machine")
        print("2. Double-click build_windows_exe.bat")
        print("3. Or manually run: pyinstaller Medical-Spytool-Windows.spec")
        
        print("\nFor professional installer:")
        print("1. Install NSIS (Nullsoft Scriptable Install System)")
        print("2. Right-click Medical-Spytool-Installer.nsi")
        print("3. Select 'Compile NSIS Script'")

def main():
    builder = WindowsExeBuilder()
    builder.build()

if __name__ == "__main__":
    main()
