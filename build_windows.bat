@echo off
SETLOCAL

REM --- Configuration ---
SET PYTHON_EXE=python
SET INNO_SETUP_COMPILER="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
SET VENV_PATH=venv

REM Get the directory of this batch script (project root)
SET PROJECT_ROOT=%~dp0

REM --- Activate Virtual Environment (Optional) ---
REM If you use a virtual environment, uncomment and adjust the path to activate.bat
REM ECHO Activating virtual environment...
REM IF EXIST "%PROJECT_ROOT%%VENV_PATH%\Scripts\activate.bat" (
REM     CALL "%PROJECT_ROOT%%VENV_PATH%\Scripts\activate.bat"
REM     ECHO Virtual environment activated.
REM ) ELSE (
REM     ECHO Virtual environment not found at %PROJECT_ROOT%%VENV_PATH%. Assuming Python is in PATH.
REM )

REM --- Step 1: Run PyInstaller Build Script ---
ECHO ========================================
ECHO Running PyInstaller build script...
ECHO ========================================
%PYTHON_EXE% "%PROJECT_ROOT%build.py"
IF ERRORLEVEL 1 (
    ECHO PyInstaller build failed. Exiting.
    GOTO :EOF
)
ECHO PyInstaller build completed.

REM --- Step 2: Run Inno Setup Compiler ---
ECHO.
ECHO ========================================
ECHO Running Inno Setup compiler...
ECHO ========================================
IF NOT EXIST %INNO_SETUP_COMPILER% (
    ECHO Inno Setup Compiler (ISCC.exe) not found at %INNO_SETUP_COMPILER%.
    ECHO Please install Inno Setup 6 or later and adjust the INNO_SETUP_COMPILER path in this script.
    GOTO :EOF
)

%INNO_SETUP_COMPILER% "%PROJECT_ROOT%MedicalSpytool.iss"
IF ERRORLEVEL 1 (
    ECHO Inno Setup compilation failed.
    GOTO :EOF
)
ECHO Inno Setup compilation completed successfully.
ECHO Installer should be in the 'Output' sub-directory created by Inno Setup (usually within the directory of MedicalSpytool.iss).

:EOF
ENDLOCAL
ECHO.
ECHO Build process finished.
