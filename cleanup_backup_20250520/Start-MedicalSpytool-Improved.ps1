# MedicalSpy - Verbesserter Starter für Windows
# Dieser verbesserte Starter bietet erweiterte Fehlerbehandlung und Diagnose

# PowerShell-Fehlerbehandlung aktivieren
$ErrorActionPreference = "Stop"

function Show-Banner {
    Clear-Host
    Write-Host "`n=================================" -ForegroundColor Cyan
    Write-Host "    MEDICAL SPYTOOL - Version 3.0" -ForegroundColor Cyan
    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host "Wissenschaftliches Publikations-Suchwerkzeug`n" -ForegroundColor Cyan
}

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

function Check-PythonProcess {
    $pythonProcesses = Get-Process python* -ErrorAction SilentlyContinue
    if ($pythonProcesses) {
        Write-Host "! Warnung: Es laufen bereits Python-Prozesse, die möglicherweise die Anwendung blockieren könnten." -ForegroundColor Yellow
        Write-Host "  Diese Prozesse werden nun beendet." -ForegroundColor Yellow
        $pythonProcesses | ForEach-Object { 
            Write-Host "  Beende Prozess: $($_.ProcessName) (ID: $($_.Id))" -ForegroundColor Yellow
            Stop-Process -Id $_.Id -Force 
        }
        Start-Sleep -Seconds 2
    }
}

function Check-TemplateRoutes {
    Write-Host "`nPrüfe Template-Routen..." -ForegroundColor Cyan
    
    # Überprüfe, ob es URL-Routing-Probleme gibt
    $htmlFiles = Get-ChildItem -Path ".\backend\templates" -Recurse -Filter "*.html"
    $errors = @()
    
    foreach ($file in $htmlFiles) {
        $content = Get-Content -Path $file.FullName -Raw
        if ($content -match "url_for\('index'\)") {
            $errors += "$($file.FullName) enthält falsche Route: url_for('index')"
        }
    }
    
    if ($errors.Count -gt 0) {
        Write-Host "Fehlerhafte URL-Routen gefunden und werden korrigiert:" -ForegroundColor Yellow
        foreach ($error in $errors) {
            Write-Host "  - $error" -ForegroundColor Yellow
        }
        
        # Korrigiere die Routen
        foreach ($file in $htmlFiles) {
            $content = Get-Content -Path $file.FullName -Raw
            if ($content -match "url_for\('index'\)") {
                $content = $content -replace "url_for\('index'\)", "url_for('main.index')"
                Set-Content -Path $file.FullName -Value $content
                Write-Host "  ✓ Korrigiert: $($file.FullName)" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "✓ Alle Template-Routen sind korrekt." -ForegroundColor Green
    }
}

function Start-Application {
    try {
        Write-Host "`nStarte die Anwendung..." -ForegroundColor Cyan
        
        # Starte die Anwendung in einem versteckten Fenster
        $process = Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "python manage.py run" -WindowStyle Hidden -PassThru
        
        if ($process -eq $null) {
            Write-Host "✗ Konnte die Anwendung nicht starten." -ForegroundColor Red
            return $false
        }
        
        # Warte bis die Anwendung hochgefahren ist
        Write-Host "Warte auf Start der Anwendung..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        # Teste, ob der Server läuft
        try {
            $testConnection = Invoke-WebRequest -Uri "http://127.0.0.1:5000" -Method Head -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($testConnection.StatusCode -eq 200) {
                Write-Host "✓ Anwendung erfolgreich gestartet." -ForegroundColor Green
                return $true
            }
        }
        catch {
            Write-Host "! Server läuft, aber reagiert noch nicht. Warte weitere 5 Sekunden..." -ForegroundColor Yellow
            Start-Sleep -Seconds 5
            
            try {
                $testConnection = Invoke-WebRequest -Uri "http://127.0.0.1:5000" -Method Head -TimeoutSec 2 -ErrorAction SilentlyContinue
                if ($testConnection.StatusCode -eq 200) {
                    Write-Host "✓ Anwendung erfolgreich gestartet." -ForegroundColor Green
                    return $true
                }
            }
            catch {
                Write-Host "✗ Server läuft, aber reagiert nicht korrekt." -ForegroundColor Red
                return $false
            }
        }
        
        return $true
    }
    catch {
        Write-Host "✗ Fehler beim Starten der Anwendung: $_" -ForegroundColor Red
        return $false
    }
}

function Open-Browser {
    try {
        Write-Host "`nÖffne die Anwendung im Browser..." -ForegroundColor Cyan
        Start-Process "http://127.0.0.1:5000"
        Write-Host "✓ Browser geöffnet." -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ Fehler beim Öffnen des Browsers: $_" -ForegroundColor Red
        Write-Host "  Sie können die Anwendung manuell im Browser unter http://127.0.0.1:5000 öffnen." -ForegroundColor Yellow
        return $false
    }
}

# Hauptfunktion
function Main {
    Show-Banner
    Set-WorkingDirectory
    
    # Beende laufende Python-Prozesse, die die App blockieren könnten
    Check-PythonProcess
    
    # Überprüfe und korrigiere Template-Routen
    Check-TemplateRoutes
    
    # Starte die Anwendung
    $success = Start-Application
    if ($success) {
        # Öffne den Browser
        Open-Browser
        Write-Host "`nMedicalSpy-Anwendung läuft jetzt unter http://127.0.0.1:5000" -ForegroundColor Green
    } else {
        Write-Host "`n✗ Die MedicalSpy-Anwendung konnte nicht korrekt gestartet werden." -ForegroundColor Red
        Write-Host "  Bitte überprüfen Sie die Fehlermeldungen oben." -ForegroundColor Red
    }
    
    Write-Host "`nHinweis: Um die Anwendung zu beenden, schließen Sie den Browser und drücken Sie Ctrl+C in diesem Fenster." -ForegroundColor Cyan
}

# Skript starten
Main
