@echo off
echo ========================================
echo Medical Spytool v1.2-beta Schnellstart
echo Phase 1 Fixes - Vollstaendig funktionsfaehig
echo ========================================
echo.

cd /d "c:\Users\paaschma\Documents\coding\medical_spytool_1.2\Medical-Spytool-medicalspy-1.2-beta-"

echo Verfuegbare Optionen:
echo.
echo [1] GUI starten (Empfohlen)
echo [2] CLI Test - Robert Koch
echo [3] CLI Test - Mehrere Mediziner
echo [4] Analytics Test - Fleming
echo [5] Funktionstest ausfuehren
echo [6] Hilfe anzeigen
echo [0] Beenden
echo.

choice /c 1234560 /n /m "Waehlen Sie eine Option (1-6, 0 zum Beenden): "

if errorlevel 7 goto :end
if errorlevel 6 goto :help
if errorlevel 5 goto :functest
if errorlevel 4 goto :analytics
if errorlevel 3 goto :multi
if errorlevel 2 goto :koch
if errorlevel 1 goto :gui

:gui
echo.
echo Starte GUI...
python -m dnb_spytool --gui
goto :end

:koch
echo.
echo Suche nach Robert Koch...
python -m dnb_spytool --author "Robert Koch" --max-results 10 --format csv --output koch_test.csv
echo Ergebnisse in koch_test.csv gespeichert.
pause
goto :end

:multi
echo.
echo Suche nach mehreren deutschen Medizinern...
python -m dnb_spytool --authors "Koch,Virchow,Ehrlich" --max-results 5 --format excel --output mediziner_test.xlsx
echo Ergebnisse in mediziner_test.xlsx gespeichert.
pause
goto :end

:analytics
echo.
echo Analytics-Test mit Alexander Fleming...
python -m dnb_spytool --author "Alexander Fleming" --max-results 15 --analytics --report-format pdf
echo Analytics-Report erstellt.
pause
goto :end

:functest
echo.
echo Fuehre vollstaendigen Funktionstest durch...
python test_complete_functionality.py
pause
goto :end

:help
echo.
echo Hilfe anzeigen...
python -m dnb_spytool --help
pause
goto :end

:end
echo.
echo Auf Wiedersehen!
pause
