@echo off
title Medical Spytool Installation
color 0A

REM Überprüfen, ob Admin-Rechte vorhanden sind
NET SESSION >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    color 0C
    echo.
    echo *** FEHLER: Diese Installation benötigt Administratorrechte ***
    echo.
    echo Bitte klicken Sie mit der rechten Maustaste auf diese Datei und wählen
    echo "Als Administrator ausführen".
    echo.
    pause
    exit /b 1
)

cls
echo.
echo  ╔════════════════════════════════════════════════════════╗
echo  ║                                                        ║
echo  ║  Medical Spytool - Installation                        ║
echo  ║                                                        ║
echo  ╚════════════════════════════════════════════════════════╝
echo.
echo  Diese Installation richtet die Medical Spytool Anwendung
echo  auf Ihrem Computer ein.
echo.
echo  Während des Vorgangs werden folgende Schritte ausgeführt:
echo    * Überprüfung der Python-Installation
echo    * Installation der notwendigen Bibliotheken
echo    * Einrichtung der Datenbank
echo    * Erstellung einer Desktop-Verknüpfung
echo.
echo  ╔════════════════════════════════════════════════════════╗
echo  ║  HINWEIS: Dieser Vorgang kann einige Minuten dauern.   ║
echo  ╚════════════════════════════════════════════════════════╝
echo.
pause

cls
echo.
echo  *** Installiere Medical Spytool... ***
echo.

REM Starte den Setup-Prozess
call setup.cmd

echo.
echo  ╔════════════════════════════════════════════════════════╗
echo  ║                                                        ║
echo  ║  Installation abgeschlossen!                           ║
echo  ║                                                        ║
echo  ║  Sie können Medical Spytool jetzt über die             ║
echo  ║  Desktop-Verknüpfung oder die Datei                    ║
echo  ║  "RunMedicalSpytool.bat" starten.                      ║
echo  ║                                                        ║
echo  ╚════════════════════════════════════════════════════════╝
echo.
pause
exit /b 0
