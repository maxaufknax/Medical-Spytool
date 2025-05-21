# Start-App.ps1
# Dieses Skript startet die Medical Spytool Anwendung

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "     MEDICAL SPYTOOL - Version 6.2       " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Starte Medical Spytool Anwendung..." -ForegroundColor Yellow

# Zum richtigen Verzeichnis wechseln
Set-Location -Path $PSScriptRoot

# Überprüfen, ob python im PATH ist
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python gefunden: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "FEHLER: Python konnte nicht gefunden werden." -ForegroundColor Red
    Write-Host "Bitte installieren Sie Python 3.8 oder höher." -ForegroundColor Red
    Read-Host "Drücken Sie eine Taste, um zu beenden"
    exit 1
}

# Anwendung starten
Write-Host "Starte Flask-Anwendung..." -ForegroundColor Yellow
try {
    # Starte die Python-Anwendung
    python start_app.py
} catch {
    Write-Host "FEHLER beim Starten der Anwendung: $_" -ForegroundColor Red
    Read-Host "Drücken Sie eine Taste, um zu beenden"
}
