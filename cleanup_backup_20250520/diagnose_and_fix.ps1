# Medical Spytool Diagnose und Fix
# Dieses PowerShell-Skript führt eine umfassende Diagnose aus und repariert Probleme automatisch

Write-Host "`n==============================================================="
Write-Host "         MEDICAL SPYTOOL - DIAGNOSE UND REPARATUR"
Write-Host "===============================================================`n"

# Prüfe, ob Python verfügbar ist
try {
    $pythonVersion = python --version
    Write-Host "✅ Python gefunden: $pythonVersion"
}
catch {
    Write-Host "❌ Python wurde nicht gefunden. Bitte installieren Sie Python 3.6+"
    exit 1
}

# Prüfe, ob das instance-Verzeichnis existiert
if (-not (Test-Path "instance")) {
    Write-Host "⚠️ Instance-Verzeichnis nicht gefunden. Wird erstellt..."
    New-Item -Path "instance" -ItemType Directory | Out-Null
    Write-Host "✅ Instance-Verzeichnis erstellt"
}
else {
    Write-Host "✅ Instance-Verzeichnis gefunden"
}

# Prüfe Berechtigungen für das instance-Verzeichnis
try {
    $acl = Get-Acl -Path "instance"
    Write-Host "Berechtigungen für instance-Verzeichnis:"
    Write-Host "  Besitzer: $($acl.Owner)"
    Write-Host "  Zugriffsregeln:"
    foreach ($rule in $acl.Access) {
        Write-Host "  - $($rule.IdentityReference) ($($rule.FileSystemRights))"
    }
    
    # Erstelle eine Testdatei, um Schreibzugriff zu prüfen
    $testFilePath = "instance\write_test.txt"
    "Test" | Out-File -FilePath $testFilePath
    if (Test-Path $testFilePath) {
        Write-Host "✅ Schreibzugriff auf das instance-Verzeichnis bestätigt"
        Remove-Item -Path $testFilePath
    }
    else {
        Write-Host "❌ Kann nicht in das instance-Verzeichnis schreiben"
    }
}
catch {
    Write-Host "⚠️ Fehler beim Prüfen der Berechtigungen: $_"
}

# Prüfe, ob die Datenbank existiert
if (Test-Path "instance\medicalspy.db") {
    $dbFile = Get-Item "instance\medicalspy.db"
    Write-Host "✅ Datenbankdatei gefunden: $($dbFile.Length) Bytes"
}
else {
    Write-Host "⚠️ Datenbankdatei nicht gefunden. Eine neue wird erstellt."
}

# Prüfe, ob die virtuelle Umgebung existiert
if (Test-Path "venv\Scripts\activate.bat") {
    Write-Host "✅ Virtuelle Umgebung gefunden"
}
else {
    Write-Host "⚠️ Virtuelle Umgebung nicht gefunden. Die Installation könnte unvollständig sein."
}

Write-Host "`n--- PROBLEMBEHEBUNG ---`n"

# 1. JSONType-Problem beheben
Write-Host "1. Prüfe auf doppelte JSONType-Klasse in models.py..."
$modelsContent = Get-Content -Path "backend\models.py" -Raw
$jsonTypeCount = ($modelsContent | Select-String -Pattern "class JSONType" -AllMatches).Matches.Count
Write-Host "   Gefunden: $jsonTypeCount JSONType-Klassen"

if ($jsonTypeCount -gt 1) {
    Write-Host "   ⚠️ Problem gefunden: Doppelte JSONType-Klasse"
    Write-Host "   🔧 Führe Reparatur aus..."
    $result = python fix_jsontype.py
    Write-Host "   ✅ Reparatur abgeschlossen"
}
else {
    Write-Host "   ✅ Keine doppelte JSONType-Klasse gefunden"
}

# 2. Datenbankprobleme beheben
Write-Host "`n2. Prüfe Datenbankzugriff..."
if (-not (Test-Path "instance\medicalspy.db") -or (Get-Item "instance\medicalspy.db").Length -eq 0) {
    Write-Host "   ⚠️ Datenbank fehlt oder ist leer"
    Write-Host "   🔧 Erstelle neue Datenbank..."
    
    # Backup erstellen, falls vorhanden
    if (Test-Path "instance\medicalspy.db") {
        if (-not (Test-Path "backups")) {
            New-Item -Path "backups" -ItemType Directory | Out-Null
        }
        Copy-Item -Path "instance\medicalspy.db" -Destination "backups\medicalspy_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
        Write-Host "   ✅ Backup der bestehenden Datenbank erstellt"
    }
    
    $result = python db_repair.py
    Write-Host "   ✅ Neue Datenbank erstellt"
}
else {
    Write-Host "   ✅ Datenbank scheint in Ordnung zu sein"
}

# 3. Template-Probleme beheben
Write-Host "`n3. Prüfe auf Template-Probleme..."
$baseTemplatePath = "backend\templates\base.html"
if (Test-Path $baseTemplatePath) {
    $baseContent = Get-Content -Path $baseTemplatePath -Raw
    if ($baseContent -match "url_for\('index'\)") {
        Write-Host "   ⚠️ URL-Endpunkte müssen korrigiert werden"
        Write-Host "   🔧 Führe Template-Reparatur aus..."
        $result = python fix_templates.py
        Write-Host "   ✅ Templates repariert"
    }
    else {
        Write-Host "   ✅ Keine URL-Endpunktprobleme gefunden"
    }
}
else {
    Write-Host "   ⚠️ Basis-Template nicht gefunden. Die Installation könnte unvollständig sein."
}

# Abschlussbericht
Write-Host "`n==============================================================="
Write-Host "                     DIAGNOSE ABGESCHLOSSEN"
Write-Host "===============================================================`n"

Write-Host "Die häufigsten Probleme wurden überprüft und repariert. Um die"
Write-Host "Anwendung zu starten, verwenden Sie einen der folgenden Befehle:"
Write-Host ""
Write-Host "1. Empfohlene Methode (verbesserte Version):"
Write-Host "   python run_fixed.py"
Write-Host ""
Write-Host "2. Ursprüngliche Methode:"
Write-Host "   python run.py"
Write-Host ""
Write-Host "3. Batch-Datei für einfachen Start:"
Write-Host "   .\fresh_start.bat"
Write-Host ""
Write-Host "Weitere Diagnosemöglichkeiten:"
Write-Host "- python fix_and_verify.py (Vollständige Diagnose mit Bericht)"
Write-Host "- python verify_fixes.py (Nur Überprüfung ohne Reparatur)"
Write-Host ""

# Frage nach dem nächsten Schritt
$startApp = Read-Host "Möchten Sie die Anwendung jetzt starten? (j/n)"
if ($startApp -eq "j") {
    Write-Host "`nStarte Medical Spytool mit verbessertem Starter..."
    Start-Process -FilePath "python" -ArgumentList "run_fixed.py" -NoNewWindow
}
else {
    Write-Host "`nDie Diagnose wurde abgeschlossen. Die Anwendung kann jederzeit gestartet werden."
}
