@echo off
title MedicalSpy Setup
color 0A

echo.
echo ******************************************************
echo *                                                    *
echo *  Medical Spytool - Installation und Einrichtung    *
echo *  (using manage.py)                               *
echo *                                                    *
echo ******************************************************
echo.

REM Überprüfen, ob Python installiert ist
echo Überprüfe Python-Installation...
python --version > nul 2>&1
if %errorlevel% neq 0 (
  echo.
  echo FEHLER: Python scheint nicht installiert zu sein oder nicht im PATH!
  echo.
  echo Bitte installieren Sie Python 3.8 oder höher von:
  echo https://www.python.org/downloads/
  echo.
  echo Wichtig: Bei der Installation "Add Python to PATH" auswählen!
  echo.
  pause
  exit /b 1
)
echo Python-Installation gefunden.

echo.
echo Führe umfassendes Setup über manage.py aus...
echo Dies beinhaltet:
echo   - Überprüfung der Python-Version (erneut, durch manage.py)
echo   - Erstellung notwendiger Verzeichnisse (logs, instance, etc.)
echo   - Einrichtung einer virtuellen Python-Umgebung (in ./venv)
echo   - Installation der Projektanforderungen (aus project_requirements.txt)
echo   - Erstellung einer .env-Datei mit Standardkonfiguration
echo   - Initialisierung der Datenbank
echo.
python manage.py setup --full

if %errorlevel% neq 0 (
  echo.
  echo FEHLER: Der Setup-Prozess mit manage.py ist fehlgeschlagen.
  echo Bitte überprüfen Sie die obigen Meldungen.
  echo.
  pause
  exit /b 1
)

echo.
echo ******************************************************
echo *                                                    *
echo *  Setup über manage.py abgeschlossen!               *
echo *                                                    *
echo *  Sie können die Anwendung jetzt starten mit:       *
echo *  > python manage.py run                            *
echo *  oder über start.bat / Start-MedicalSpytool.ps1    *
echo *                                                    *
echo ******************************************************
echo.
pause
