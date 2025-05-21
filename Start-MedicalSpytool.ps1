# MedicalSpy - Vereinfachter Startscript für Windows via manage.py
# Dieses Skript nutzt manage.py für Setup und Start der MedicalSpy-Anwendung.

# PowerShell-Fehlerbehandlung aktivieren
$ErrorActionPreference = "Stop"

# Banner anzeigen
function Show-Banner {
    Clear-Host
    Write-Host "`n=================================" -ForegroundColor Cyan
    Write-Host "    MEDICAL SPYTOOL - Version 3.0 (via manage.py)" -ForegroundColor Cyan
    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host "Wissenschaftliches Publikations-Suchwerkzeug`n" -ForegroundColor Cyan
}

# Aktuelles Verzeichnis als Arbeitsverzeichnis setzen
function Set-WorkingDirectory {
    try {
        # Zum Skriptverzeichnis wechseln
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        Set-Location -Path $scriptDir
        Write-Host "✓ Arbeitsverzeichnis gesetzt auf: $scriptDir" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ Fehler beim Setzen des Arbeitsverzeichnisses: $_" -ForegroundColor Red
        throw "Konnte Arbeitsverzeichnis nicht setzen."
    }
}

# Hauptfunktion
function Main {
    Show-Banner
    Set-WorkingDirectory

    Write-Host "`n[Phase 1/2] Führe Setup über manage.py aus..." -ForegroundColor Cyan
    Write-Host "Dies kann einige Minuten dauern, insbesondere beim ersten Mal (Erstellung der venv, Installation der Pakete)." -ForegroundColor Yellow
    
    python manage.py setup --full
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Setup via manage.py fehlgeschlagen. Überprüfen Sie die Ausgabe oben." -ForegroundColor Red
        Write-Host "Drücken Sie eine beliebige Taste zum Beenden..." -ForegroundColor Cyan
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
    Write-Host "✓ Setup erfolgreich abgeschlossen." -ForegroundColor Green

    # Der Health-Check (scripts\\health_check.py) wird hier nicht mehr automatisch er
    # Write-Host "`n[Phase 2/2] Führe Health-Check über manage.py aus..." -ForegroundColor Cyan
    # python manage.py health
    # if ($LASTEXITCODE -ne 0) {
    #     Write-Host "✗ Health-Check fehlgeschlagen. Überprüfen Sie die Ausgabe oben." -ForegroundColor Red
    #     Write-Host "Drücken Sie eine beliebige Taste zum Beenden..." -ForegroundColor Cyan
    #     $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    #     exit 1
    # }
    # Write-Host "✓ Health-Check erfolgreich abgeschlossen." -ForegroundColor Green

    # Anwendung starten und im Browser öffnen
    Write-Host "`nStarte die Anwendung und öffne sie im Browser..." -ForegroundColor Cyan
    Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "python manage.py run" -WindowStyle Hidden
    Start-Sleep -Seconds 5
    Start-Process "http://127.0.0.1:5000"

    Write-Host "`nMedicalSpy-Anwendung sollte jetzt laufen und im Browser geöffnet sein." -ForegroundColor Green
}

# Skript starten
Main

# Hinweis: Um die Anwendung zu stoppen, schließen Sie das PowerShell-Fenster oder drücken Sie Ctrl+C im PowerShell-Fenster.
# Weitere Informationen zur Verwendung von MedicalSpy finden Sie in der Dokumentation.
