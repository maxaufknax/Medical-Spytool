@echo off
title Medical Spytool
color 0B

echo ============================================
echo   Medical Spytool - Wissenschaftliches Publikations-Suchwerkzeug
echo ============================================
echo.

REM Prüfe, ob manage.py existiert
if not exist manage.py (
  echo FEHLER: manage.py nicht gefunden. Das Startskript kann nicht ausgeführt werden.
  echo Bitte stellen Sie sicher, dass Sie sich im Hauptverzeichnis des Projekts befinden.
  pause
  exit /b 1
)

REM Prüfe, ob die virtuelle Umgebung (venv) bereits durch manage.py setup erstellt wurde.
REM manage.py kümmert sich um die Erstellung, falls nicht vorhanden, während des 'run' oder 'setup'.

echo Starte Medical Spytool über manage.py...
echo.
echo Die Anwendung wird gestartet. Wenn dies der erste Start ist oder die Einrichtung
echo unvollständig ist, kann manage.py versuchen, notwendige Schritte auszuführen.
echo.
echo Die Anwendung wird im Browser geöffnet, falls konfiguriert.
echo Drücken Sie STRG+C im Konsolenfenster der Anwendung, um sie zu beenden.
echo.

REM Starte die Anwendung über manage.py. 
REM --open-browser ist ein Argument für den 'run' Befehl in manage.py.
REM Das manage.py Skript sollte die Aktivierung der venv und andere Prüfungen intern handhaben.
python manage.py run --open-browser

if %errorlevel% neq 0 (
  echo.
  echo Es gab ein Problem beim Starten der Anwendung mit manage.py.
  echo Möglicherweise müssen Sie zuerst das Setup ausführen:
  echo   python manage.py setup --full
  echo Oder überprüfen Sie die Fehlermeldungen oben oder in den Logdateien (logs-Verzeichnis).
  echo.
  pause
)

REM Das manage.py Skript läuft im Vordergrund, daher ist kein Warten oder manuelles Öffnen des Browsers hier mehr nötig.
REM Das Beenden des Fensters erfolgt, wenn der manage.py Prozess (Flask Server) beendet wird.
exit /b 0