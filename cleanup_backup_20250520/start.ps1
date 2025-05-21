# MedicalSpy Start-Skript für Windows (PowerShell)
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Medical Spytool - Wissenschaftliches Publikations-Suchwerkzeug" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Überprüfe, ob virtuelle Umgebung existiert
if (-Not (Test-Path "venv")) {
    Write-Host "Die virtuelle Python-Umgebung wurde nicht gefunden." -ForegroundColor Red
    Write-Host "Bitte führen Sie zuerst 'setup.ps1' aus." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Öffnen Sie PowerShell und führen Sie aus:" -ForegroundColor Yellow
    Write-Host "    .\setup.ps1" -ForegroundColor White -BackgroundColor DarkBlue
    Read-Host -Prompt "Drücken Sie Enter, um zu beenden"
    exit 1
}

# Aktiviere die virtuelle Umgebung
Write-Host "Aktiviere virtuelle Umgebung..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Stelle sicher, dass notwendige Verzeichnisse existieren
$directories = @("instance", "logs", "output", "person_lists")
foreach ($dir in $directories) {
    if (-Not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
}

# Starte die Anwendung mit run.py für bessere Konfiguration
Write-Host "Starte MedicalSpy Anwendung..." -ForegroundColor Green
Write-Host ""
Write-Host "Die Anwendung ist erreichbar unter: http://localhost:5000" -ForegroundColor Cyan
Write-Host "Drücken Sie STRG+C, um die Anwendung zu beenden." -ForegroundColor Yellow
Write-Host ""

try {
    python run.py
} catch {
    Write-Host ""
    Write-Host "Es ist ein Fehler aufgetreten!" -ForegroundColor Red
    Write-Host $_.Exception.Message
    Read-Host -Prompt "Drücken Sie Enter, um zu beenden"
}
