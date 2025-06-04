@echo off
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
