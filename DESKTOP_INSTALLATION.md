# Medical Spytool Desktop Version - Installation und Nutzung

## 🚀 Desktop Version - Vollständige lokale Windows-Installation

Die Medical Spytool Desktop Version ist eine vollständig lokale, benutzerfreundliche Anwendung für Windows PCs, die alle Funktionen der ursprünglichen Web-Anwendung in einem einfach zu installierenden Desktop-Paket bietet.

## ✨ Desktop-Features

### 🖥️ Native Desktop-Anwendung
- **Eingebauter Webserver**: Keine separate Installation erforderlich
- **Desktop GUI**: Native Windows-Oberfläche mit System-Tray-Integration
- **Auto-Start**: Automatischer Server-Start beim Programmstart
- **Browser-Integration**: Automatisches Öffnen im Standard-Browser
- **Port-Management**: Automatische Erkennung freier Ports

### 🔧 Benutzerfreundliche Installation
- **Ein-Klick-Installation**: Einfaches Setup mit `install.bat`
- **Desktop-Verknüpfung**: Automatische Erstellung von Desktop- und Startmenü-Shortcuts
- **Portable Version**: Kann auch ohne Installation direkt ausgeführt werden
- **Automatische Updates**: Einfache Update-Funktionalität
- **Deinstallation**: Vollständige Entfernung mit `uninstall.bat`

## 📦 Verfügbare Installationsmethoden

### Methode 1: Desktop-Executable (Empfohlen)
```bash
# Erstelle die Desktop-Version
python build_desktop.py

# Installiere system-weit
cd dist
install.bat
```

### Methode 2: Portable Version
```bash
# Starte direkt aus dem dist-Verzeichnis
cd dist
MedicalSpyToolDesktop.exe
```

### Methode 3: Entwicklermodus
```bash
# Für Entwickler und Tester
start_desktop.bat
```

## 🎯 Schnellstart-Anleitung

### Schritt 1: Download und Installation
1. **Download**: Lade die `Medical-Spytool-Desktop.zip` herunter
2. **Entpacken**: Entpacke die ZIP-Datei in einen beliebigen Ordner
3. **Installation**: Führe `install.bat` als Administrator aus
4. **Fertig**: Medical Spytool ist nun über das Startmenü oder Desktop verfügbar

### Schritt 2: Erste Nutzung
1. **Starten**: Klicke auf die Desktop-Verknüpfung oder Startmenü-Eintrag
2. **Server-Start**: Die Anwendung startet automatisch den lokalen Server
3. **Browser**: Dein Browser öffnet sich automatisch mit der Anwendung
4. **Los geht's**: Alle Funktionen sind sofort verfügbar

## 🔧 Desktop-Anwendung Features

### Server-Management
- **Start/Stop**: Einfache Server-Kontrolle über das Desktop-Interface
- **Port-Konfiguration**: Anpassbarer Port (Standard: 5000)
- **Status-Anzeige**: Visuelle Anzeige des Server-Status
- **Auto-Recovery**: Automatische Neustart-Funktionen bei Fehlern

### System-Integration
- **System Tray**: Minimierung in die Taskleiste
- **Kontext-Menü**: Rechtsklick-Menü im System Tray
- **Autostart**: Optional automatischer Start mit Windows
- **Benachrichtigungen**: System-Benachrichtigungen für wichtige Events

### Logging und Debugging
- **Live-Log**: Echzeit-Anzeige aller Aktivitäten
- **Log-Export**: Speichern von Logs für Support
- **Fehlerbehandlung**: Ausführliche Fehlermeldungen
- **Debug-Modus**: Erweiterte Debugging-Optionen

## 📁 Verzeichnisstruktur (Installiert)

```
C:\Program Files\Medical Spytool\
├── MedicalSpyToolDesktop.exe    # Haupt-Anwendung
├── assets\                      # Anwendungs-Assets
│   ├── icon.ico                # Anwendungs-Icon
│   └── default_config.json     # Standard-Konfiguration
├── templates\                   # Web-Interface Templates
├── static\                      # CSS, JavaScript, Bilder
├── person_lists\               # Gespeicherte Personenlisten
├── output\                     # Export-Verzeichnis
├── logs\                       # Anwendungs-Logs
├── medicalspytool_config.json  # Benutzer-Konfiguration
├── README.md                   # Dokumentation
├── BENUTZERANLEITUNG.md        # Benutzerhandbuch
└── uninstall.bat              # Deinstallationsskript
```

## 🚀 Build-Prozess für Entwickler

### Voraussetzungen
```bash
# Python 3.8+ erforderlich
python --version

# Alle Abhängigkeiten installieren
pip install -r requirements.txt
```

### Desktop-Version erstellen
```bash
# Desktop-Version mit GUI
python build_desktop.py

# Web-Only Version (Fallback)
python build_desktop.py web
```

### Ausgabe
- `dist/MedicalSpyToolDesktop.exe` - Haupt-Desktop-Anwendung
- `dist/install.bat` - Installer-Skript
- `dist/uninstall.bat` - Deinstaller-Skript
- `dist/create_shortcut.bat` - Desktop-Verknüpfung erstellen

## ⚙️ Konfiguration

### Desktop-Einstellungen
- **Auto-Start Server**: Automatischer Server-Start beim Programmstart
- **Auto-Open Browser**: Automatisches Öffnen des Browsers
- **Minimize to Tray**: Minimierung in System Tray
- **Port**: Server-Port-Konfiguration
- **Startup Options**: Verschiedene Startoptionen

### Erweiterte Konfiguration
Die Datei `medicalspytool_config.json` kann für erweiterte Einstellungen bearbeitet werden:
```json
{
  "default_database": "PubMed",
  "output_path": "./output",
  "max_results": 1000,
  "timeout": 30,
  "auto_start": true,
  "auto_browser": true,
  "minimize_to_tray": true,
  "debug_mode": false
}
```

## 🔄 Update-Prozess

### Automatische Updates
1. Neue Version herunterladen
2. Alte Installation stoppen
3. `install.bat` der neuen Version ausführen
4. Konfiguration und Daten bleiben erhalten

### Manuelle Updates
1. Anwendung beenden
2. Neue Dateien über alte kopieren
3. Anwendung neu starten

## 🛠️ Problembehandlung

### Häufige Probleme

#### Server startet nicht
```
Lösung 1: Port bereits belegt
- Anderen Port in den Einstellungen wählen
- Oder: Andere Anwendung beenden, die den Port verwendet

Lösung 2: Firewall-Blockierung
- Windows Firewall-Ausnahme hinzufügen
- Antivirus-Software prüfen
```

#### Anwendung startet nicht
```
Lösung 1: Fehlende Abhängigkeiten
- Python 3.8+ installieren
- Visual C++ Redistributable installieren

Lösung 2: Berechtigungsprobleme
- Als Administrator ausführen
- Installationsverzeichnis-Berechtigungen prüfen
```

#### Browser öffnet sich nicht
```
Lösung 1: Standard-Browser-Problem
- Standard-Browser in Windows-Einstellungen setzen
- Manuell Browser öffnen: http://localhost:5000

Lösung 2: Firewall/Proxy-Probleme
- Lokale Verbindungen in Firewall erlauben
- Proxy-Einstellungen prüfen
```

### Log-Dateien
- **Desktop-Logs**: Siehe Desktop-Anwendung Log-Fenster
- **Server-Logs**: `logs/medicalspytool.log`
- **Error-Logs**: `logs/error.log`

### Debug-Modus
```bash
# Desktop-Anwendung im Debug-Modus starten
MedicalSpyToolDesktop.exe --debug

# Oder Entwicklermodus
python desktop_launcher.py --debug
```

## 📞 Support und Hilfe

### Online-Dokumentation
- **README.md**: Allgemeine Informationen
- **BENUTZERANLEITUNG.md**: Detaillierte Anleitung
- **API-Dokumentation**: Im Anwendungsmenü verfügbar

### Lokale Hilfe
- **Anwendungsmenü**: Hilfe → Über / Hilfe
- **Tooltip-Hilfen**: Hover-Hilfen in der Anwendung
- **Kontextmenü**: Rechtsklick-Hilfen

### Erweiterte Hilfe
```bash
# Kommandozeilen-Hilfe
MedicalSpyToolDesktop.exe --help

# Entwickler-Konsole in Browser: F12
# Anwendungs-Logs: Siehe Desktop-Interface
```

## 🔒 Sicherheit und Datenschutz

### Lokale Ausführung
- **Keine Cloud**: Alle Daten bleiben lokal auf Ihrem PC
- **Keine Telemetrie**: Keine Datensammlung oder -übertragung
- **Offline-Fähig**: Funktioniert ohne Internetverbindung (außer für Datenbankabfragen)

### Datenverarbeitung
- **API-Keys**: Werden lokal und verschlüsselt gespeichert
- **Suchergebnisse**: Bleiben auf Ihrem System
- **Personendaten**: Nur lokale Speicherung

### Berechtigungen
- **Netzwerk**: Nur für Datenbankabfragen erforderlich
- **Dateisystem**: Nur für Anwendungsverzeichnis und Exports
- **System**: Minimal erforderliche Berechtigungen

---

## 🎉 Viel Erfolg mit Medical Spytool Desktop!

Die Desktop-Version bietet die volle Funktionalität der Medical Spytool in einer benutzerfreundlichen, lokal installierbaren Form. Bei Fragen oder Problemen konsultieren Sie die umfangreiche Dokumentation oder verwenden Sie die eingebauten Hilfe-Features.