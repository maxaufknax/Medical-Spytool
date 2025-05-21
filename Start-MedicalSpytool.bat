@echo off
echo =========================================
echo      MEDICAL SPYTOOL - Version 6.2      
echo =========================================
echo Starte Medical Spytool Anwendung...

:: Zum PowerShell-Skript wechseln
powershell -ExecutionPolicy Bypass -File "%~dp0Start-App.ps1"

:: Falls es einen Fehler gibt, warte auf Eingabe
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Es gab einen Fehler beim Starten der Anwendung.
    pause
)
