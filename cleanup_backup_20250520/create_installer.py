import os
import shutil
import subprocess

# NSIS script for creating a Windows installer
NSIS_SCRIPT = r"""
!include MUI2.nsh

; Application information
Name "Medical Spytool"
OutFile "MedicalSpytoolSetup.exe"
InstallDir "$PROGRAMFILES\Medical Spytool"
InstallDirRegKey HKCU "Software\Medical Spytool" "Install_Dir"

; Request application privileges
RequestExecutionLevel admin

; Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "static\favicon.ico"
!define MUI_UNICON "static\favicon.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installer sections
Section "Medical Spytool" SecMain
    SetOutPath "$INSTDIR"
    
    ; Application files
    File /r "dist\MedicalSpytool\*.*"
    
    ; Create shortcut
    CreateDirectory "$SMPROGRAMS\Medical Spytool"
    CreateShortCut "$SMPROGRAMS\Medical Spytool\Medical Spytool.lnk" "$INSTDIR\MedicalSpytool.exe"
    CreateShortCut "$DESKTOP\Medical Spytool.lnk" "$INSTDIR\MedicalSpytool.exe"
    
    ; Write registry keys
    WriteRegStr HKCU "Software\Medical Spytool" "Install_Dir" $INSTDIR
    
    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Medical Spytool" \
                     "DisplayName" "Medical Spytool"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Medical Spytool" \
                     "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
SectionEnd

; Uninstaller section
Section "Uninstall"
    ; Remove application files
    RMDir /r "$INSTDIR\*.*"
    
    ; Remove shortcuts
    Delete "$SMPROGRAMS\Medical Spytool\Medical Spytool.lnk"
    Delete "$DESKTOP\Medical Spytool.lnk"
    RMDir "$SMPROGRAMS\Medical Spytool"
    
    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Medical Spytool"
    DeleteRegKey HKCU "Software\Medical Spytool"
    
    ; Remove installation directory
    RMDir "$INSTDIR"
SectionEnd
"""

def create_installer():
    """Create an NSIS installer for the application"""
    # Ensure NSIS is installed and available
    try:
        subprocess.run(['makensis', '-VERSION'], check=True, capture_output=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("ERROR: NSIS is not installed or not in PATH. Please install NSIS from https://nsis.sourceforge.io/")
        return False
    
    # Create NSIS script file
    with open('installer.nsi', 'w') as f:
        f.write(NSIS_SCRIPT)
    
    # Create a LICENSE.txt file if it doesn't exist
    if not os.path.exists('LICENSE.txt'):
        with open('LICENSE.txt', 'w') as f:
            f.write("Medical Spytool License\n")
            f.write("Copyright (c) 2023 Medical Spytool Team\n")
            f.write("\nAll rights reserved.\n")
    
    # Run NSIS to create the installer
    try:
        print("Building installer...")
        subprocess.run(['makensis', 'installer.nsi'], check=True)
        print("Installer created successfully: MedicalSpytoolSetup.exe")
        return True
    except subprocess.SubprocessError as e:
        print(f"Error creating installer: {e}")
        return False

if __name__ == '__main__':
    # First, build the executable
    import build_exe
    build_exe.build_executable()
    
    # Then, create the installer
    create_installer()
