#!/usr/bin/env python
"""
Build script for creating a standalone desktop executable with PyInstaller.

This script configures PyInstaller to create a comprehensive desktop application
for the Medical Spytool, including all necessary resources and proper Windows integration.

Usage:
    python build_desktop.py
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
import json

# Desktop application PyInstaller configuration
def get_pyinstaller_args():
    """Get PyInstaller arguments with correct separator for current OS."""
    separator = ';' if os.name == 'nt' else ':'
    
    return [
        '--name=MedicalSpyToolDesktop',
        '--onefile',  # Create a single executable file
        '--windowed',  # Don't show console window on Windows
        '--icon=assets/icon.ico',  # Application icon
        '--version-file=version_info.txt',  # Version information
        f'--add-data=templates{separator}templates',  # Include templates
        f'--add-data=static{separator}static',  # Include static files
        f'--add-data=assets{separator}assets',  # Include assets
        f'--add-data=database_connectors{separator}database_connectors',  # Include database connectors
        f'--add-data=utils{separator}utils',  # Include utilities
        f'--add-data=gui{separator}gui',  # Include GUI components
        '--hidden-import=pandas',
        '--hidden-import=openpyxl',
        '--hidden-import=xlsxwriter',
        '--hidden-import=flask_bootstrap',
        '--hidden-import=waitress',
        '--hidden-import=pystray',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageDraw',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=database_connectors.base_connector',
        '--hidden-import=database_connectors.dnb_connector',
        '--hidden-import=database_connectors.pubmed_connector',
        '--hidden-import=database_connectors.scopus_connector',
        '--hidden-import=database_connectors.wos_connector',
        '--hidden-import=database_connectors.gepris_connector',
        '--hidden-import=utils.config_manager',
        '--hidden-import=utils.export_manager',
        '--hidden-import=utils.logging_manager',
        '--hidden-import=utils.path_manager',
        '--hidden-import=utils.search_profiles',
        '--clean',  # Clean PyInstaller cache
        'desktop_launcher.py'  # Main desktop script
    ]

# Web-only fallback version
def get_web_pyinstaller_args():
    """Get web-only PyInstaller arguments."""
    separator = ';' if os.name == 'nt' else ':'
    
    return [
        '--name=MedicalSpyToolWeb',
        '--onefile',
        '--console',  # Show console for web version
        '--icon=assets/icon.ico',
        '--version-file=version_info.txt',
        f'--add-data=templates{separator}templates',
        f'--add-data=static{separator}static',
        f'--add-data=assets{separator}assets',
        f'--add-data=database_connectors{separator}database_connectors',
        f'--add-data=utils{separator}utils',
        '--hidden-import=pandas',
        '--hidden-import=openpyxl',
        '--hidden-import=xlsxwriter',
        '--hidden-import=flask_bootstrap',
        '--hidden-import=waitress',
        '--hidden-import=database_connectors.base_connector',
        '--hidden-import=database_connectors.dnb_connector',
        '--hidden-import=database_connectors.pubmed_connector',
        '--hidden-import=database_connectors.scopus_connector',
        '--hidden-import=database_connectors.wos_connector',
        '--hidden-import=database_connectors.gepris_connector',
        '--clean',
        'main.py'
    ]

def create_build_info():
    """Create a build info file with version and build date."""
    build_info = {
        'version': '2.0.0-desktop',
        'build_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'python_version': sys.version,
        'build_type': 'desktop'
    }
    
    os.makedirs('assets', exist_ok=True)
    with open('assets/build_info.json', 'w') as f:
        json.dump(build_info, f, indent=2)

def copy_additional_files():
    """Copy additional files to the dist directory."""
    print("Copying additional files...")
    
    # Create directories
    directories = [
        'dist/person_lists',
        'dist/output', 
        'dist/logs',
        'dist/assets'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  Created: {directory}")
    
    # Copy configuration files
    files_to_copy = [
        ('README.md', 'dist/README.md'),
        ('BENUTZERANLEITUNG.md', 'dist/BENUTZERANLEITUNG.md'),
        ('DESKTOP_INSTALLATION.md', 'dist/DESKTOP_INSTALLATION.md'),
        ('medicalspytool_config.json', 'dist/medicalspytool_config.json'),
        ('assets/default_config.json', 'dist/assets/default_config.json'),
        ('start_desktop.bat', 'dist/start_desktop.bat'),
        ('start_desktop_enhanced.bat', 'dist/start_desktop_enhanced.bat')
    ]
    
    for src, dst in files_to_copy:
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  Copied: {src} -> {dst}")
    
    # Create an empty persons.json file
    with open('dist/person_lists/persons.json', 'w') as f:
        f.write('[]')
    
    # Create desktop shortcuts template
    create_desktop_shortcuts()

def create_desktop_shortcuts():
    """Create desktop shortcut templates."""
    print("Creating desktop shortcuts...")
    
    # Windows desktop shortcut (VBS script)
    vbs_content = '''Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = oWS.SpecialFolders("Desktop") & "\\Medical Spytool.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = WScript.ScriptFullName & "\\..\\MedicalSpyToolDesktop.exe"
oLink.WorkingDirectory = WScript.ScriptFullName & "\\.."
oLink.Description = "Medical Spytool Desktop Application"
oLink.IconLocation = WScript.ScriptFullName & "\\..\\assets\\icon.ico"
oLink.Save
WScript.Echo "Desktop shortcut created successfully!"
'''
    
    with open('dist/create_desktop_shortcut.vbs', 'w') as f:
        f.write(vbs_content)
    
    # Batch file for easy shortcut creation
    batch_content = '''@echo off
echo Creating desktop shortcut for Medical Spytool...
cscript //nologo create_desktop_shortcut.vbs
pause
'''
    
    with open('dist/create_shortcut.bat', 'w') as f:
        f.write(batch_content)

def create_installer_script():
    """Create a simple installer script."""
    print("Creating installer script...")
    
    installer_content = '''@echo off
echo ===============================================
echo     Medical Spytool Desktop Installer
echo ===============================================
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges.
) else (
    echo Note: Running without administrator privileges.
    echo Some features may require manual setup.
)

REM Create program files directory
set "INSTALL_DIR=%PROGRAMFILES%\\Medical Spytool"
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%" 2>nul
    if errorlevel 1 (
        echo Cannot create directory in Program Files, using user directory...
        set "INSTALL_DIR=%USERPROFILE%\\Medical Spytool"
        mkdir "%INSTALL_DIR%" 2>nul
    )
)

echo Installing to: %INSTALL_DIR%

REM Copy files
echo Copying application files...
xcopy /E /Y "*" "%INSTALL_DIR%\\" >nul 2>&1

REM Create start menu shortcut
if exist "%INSTALL_DIR%\\MedicalSpyToolDesktop.exe" (
    echo Creating start menu shortcut...
    set "START_MENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs"
    echo Set oWS = CreateObject("WScript.Shell") > temp_shortcut.vbs
    echo Set oLink = oWS.CreateShortcut("%START_MENU%\\Medical Spytool.lnk") >> temp_shortcut.vbs
    echo oLink.TargetPath = "%INSTALL_DIR%\\MedicalSpyToolDesktop.exe" >> temp_shortcut.vbs
    echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> temp_shortcut.vbs
    echo oLink.Description = "Medical Spytool Desktop Application" >> temp_shortcut.vbs
    echo oLink.IconLocation = "%INSTALL_DIR%\\assets\\icon.ico" >> temp_shortcut.vbs
    echo oLink.Save >> temp_shortcut.vbs
    cscript //nologo temp_shortcut.vbs
    del temp_shortcut.vbs
)

REM Create desktop shortcut
choice /C YN /M "Create desktop shortcut?"
if errorlevel 2 goto :skip_desktop
echo Creating desktop shortcut...
echo Set oWS = CreateObject("WScript.Shell") > temp_desktop.vbs
echo Set oLink = oWS.CreateShortcut("%USERPROFILE%\\Desktop\\Medical Spytool.lnk") >> temp_desktop.vbs
echo oLink.TargetPath = "%INSTALL_DIR%\\MedicalSpyToolDesktop.exe" >> temp_desktop.vbs
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> temp_desktop.vbs
echo oLink.Description = "Medical Spytool Desktop Application" >> temp_desktop.vbs
echo oLink.IconLocation = "%INSTALL_DIR%\\assets\\icon.ico" >> temp_desktop.vbs
echo oLink.Save >> temp_desktop.vbs
cscript //nologo temp_desktop.vbs
del temp_desktop.vbs

:skip_desktop
echo.
echo ===============================================
echo     Installation completed successfully!
echo ===============================================
echo.
echo Medical Spytool has been installed to:
echo %INSTALL_DIR%
echo.
echo You can start the application from:
echo - Start Menu: Medical Spytool
echo - Desktop shortcut (if created)
echo - Or run: %INSTALL_DIR%\\MedicalSpyToolDesktop.exe
echo.
pause
'''
    
    with open('dist/install.bat', 'w') as f:
        f.write(installer_content)

def create_uninstaller():
    """Create an uninstaller script."""
    print("Creating uninstaller...")
    
    uninstaller_content = '''@echo off
echo ===============================================
echo     Medical Spytool Desktop Uninstaller
echo ===============================================
echo.

REM Detect installation directory
set "INSTALL_DIR="
if exist "%PROGRAMFILES%\\Medical Spytool\\MedicalSpyToolDesktop.exe" (
    set "INSTALL_DIR=%PROGRAMFILES%\\Medical Spytool"
) else if exist "%USERPROFILE%\\Medical Spytool\\MedicalSpyToolDesktop.exe" (
    set "INSTALL_DIR=%USERPROFILE%\\Medical Spytool"
) else (
    echo Medical Spytool installation not found.
    pause
    exit /b 1
)

echo Found installation at: %INSTALL_DIR%
echo.

REM Confirm uninstallation
choice /C YN /M "Are you sure you want to uninstall Medical Spytool?"
if errorlevel 2 goto :cancel

echo Removing application files...
taskkill /F /IM "MedicalSpyToolDesktop.exe" >nul 2>&1

REM Remove shortcuts
echo Removing shortcuts...
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Medical Spytool.lnk" >nul 2>&1
del "%USERPROFILE%\\Desktop\\Medical Spytool.lnk" >nul 2>&1

REM Remove installation directory
echo Removing installation directory...
rmdir /S /Q "%INSTALL_DIR%" >nul 2>&1

echo.
echo Medical Spytool has been uninstalled successfully.
echo.
pause
exit /b 0

:cancel
echo Uninstallation cancelled.
pause
'''
    
    with open('dist/uninstall.bat', 'w') as f:
        f.write(uninstaller_content)

def build_executable(build_type="desktop"):
    """Build the executable using PyInstaller."""
    print(f"Building Medical Spytool {build_type} executable...")
    
    # Create build info
    create_build_info()
    
    # Choose configuration
    if build_type == "desktop":
        pyinstaller_cmd = ['pyinstaller'] + get_pyinstaller_args()
    else:
        pyinstaller_cmd = ['pyinstaller'] + get_web_pyinstaller_args()
    
    try:
        print("Running PyInstaller...")
        print(f"Command: {' '.join(pyinstaller_cmd)}")
        
        result = subprocess.run(pyinstaller_cmd, check=True, capture_output=True, text=True)
        print("PyInstaller completed successfully.")
        
        if result.stdout:
            print("PyInstaller output:")
            print(result.stdout)
        
        # Copy additional files
        copy_additional_files()
        
        # Create installer and support scripts
        create_installer_script()
        create_uninstaller()
        
        print("\n" + "="*50)
        print("BUILD COMPLETED SUCCESSFULLY!")
        print("="*50)
        
        if build_type == "desktop":
            exe_path = os.path.abspath('dist/MedicalSpyToolDesktop.exe')
            print(f"Desktop executable: {exe_path}")
        else:
            exe_path = os.path.abspath('dist/MedicalSpyToolWeb.exe')
            print(f"Web executable: {exe_path}")
            
        print(f"Distribution folder: {os.path.abspath('dist/')}")
        print("\nTo install:")
        print("1. Copy the 'dist' folder to target location")
        print("2. Run 'install.bat' for system-wide installation")
        print("3. Or run the executable directly")
        print("\nTo distribute:")
        print("- Zip the 'dist' folder")
        print("- Or use 'install.bat' for easy installation")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running PyInstaller: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during build process: {e}")
        sys.exit(1)

def main():
    """Main build function."""
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        build_executable("web")
    else:
        build_executable("desktop")

if __name__ == "__main__":
    main()