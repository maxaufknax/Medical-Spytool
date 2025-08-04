# Medical Spytool Desktop Version 2.0

## 🚀 Vollständige lokale Windows Desktop-Anwendung

Medical Spytool Desktop ist eine benutzerfreundliche, vollständig lokal installierbare Desktop-Version der beliebten Medical Spytool Web-Anwendung. Sie bietet alle Funktionen der ursprünglichen Anwendung in einem einfach zu installierenden Desktop-Paket für Windows PCs.

## ✨ Desktop-Highlights

### 🖥️ Native Windows-Integration
- **Desktop-Anwendung**: Echte Windows-Desktop-App mit nativer GUI
- **System Tray**: Minimierung in die Windows-Taskleiste
- **Auto-Start**: Automatischer Server-Start beim Programmstart
- **One-Click**: Einfache Installation mit einem Klick

### 🔧 Benutzerfreundlich
- **Keine Konfiguration**: Funktioniert sofort nach der Installation
- **Automatisch**: Server-Management läuft im Hintergrund
- **Portable**: Kann auch ohne Installation verwendet werden
- **Sicher**: Alle Daten bleiben lokal auf Ihrem PC

## 📦 Schnellstart

### Option 1: Vollinstallation (Empfohlen)
```
1. Medical-Spytool-Desktop.zip herunterladen
2. ZIP-Datei entpacken
3. Als Administrator: install.bat ausführen
4. Desktop-Verknüpfung oder Startmenü verwenden
```

### Option 2: Portable Version
```
1. ZIP-Datei entpacken
2. MedicalSpyToolDesktop.exe direkt ausführen
3. Fertig - keine Installation erforderlich
```

### Option 3: Entwicklermodus
```
1. Python 3.8+ installieren
2. start_desktop_enhanced.bat ausführen
3. Entwicklungsoptionen wählen
```

## 🎯 Funktionsumfang

Alle Funktionen der Web-Version plus:

### Desktop-Spezifische Features
- **Server-Management**: Start/Stop über Desktop-Interface
- **Port-Konfiguration**: Automatische Porterkennung
- **Status-Anzeige**: Live-Status des Servers
- **System-Integration**: Windows-Benachrichtigungen
- **Log-Viewer**: Integrierte Log-Anzeige
- **Auto-Recovery**: Automatische Fehlerbehandlung

### Erweiterte Funktionen
- **Multi-Datenbank-Suche**: PubMed, DNB, Scopus, Web of Science, GEPRIS
- **Personenverwaltung**: Import/Export von Forscherlisten
- **Erweiterte Suche**: Komplexe Suchfilter und Parameter
- **Analyse & Visualisierung**: Statistische Auswertungen
- **Export-Funktionen**: Excel, CSV mit konfigurierbaren Spalten
- **Suchprofile**: Wiederverwendbare Suchkonfigurationen

## 📁 Installationsverzeichnis

Nach der Installation unter `C:\Program Files\Medical Spytool\`:

```
Medical Spytool/
├── MedicalSpyToolDesktop.exe    # Haupt-Anwendung
├── assets/                      # Icons und Konfiguration
├── README.md                    # Diese Datei
├── DESKTOP_INSTALLATION.md      # Detaillierte Anleitung
├── person_lists/               # Ihre Personenlisten
├── output/                     # Export-Verzeichnis
├── logs/                       # Anwendungs-Logs
└── uninstall.bat              # Deinstallation
```

## ⚡ Systemanforderungen

### Minimum
- Windows 10 oder höher
- 4 GB RAM
- 100 MB freier Speicherplatz
- Internetverbindung (für Datenbankabfragen)

### Empfohlen
- Windows 11
- 8 GB RAM
- 500 MB freier Speicherplatz
- Schnelle Internetverbindung

## 🛠️ Desktop-Anwendung Bedienung

### Hauptfenster
1. **Server-Status**: Zeigt aktuellen Status an
2. **Steuerung**: Start/Stop/Browser öffnen Buttons
3. **Einstellungen**: Port, Auto-Start, System Tray Optionen
4. **Log-Anzeige**: Live-Protokoll aller Aktivitäten

### System Tray Menü
- **Anwendung öffnen**: Hauptfenster anzeigen
- **Im Browser öffnen**: Web-Interface öffnen
- **Beenden**: Anwendung komplett schließen

### Tastenkombinationen
- `Strg+O`: Browser öffnen
- `Strg+L`: Log leeren
- `Strg+Q`: Anwendung beenden

## 🔧 Konfiguration

### Standard-Einstellungen
Die Anwendung funktioniert ohne Konfiguration. Für erweiterte Einstellungen:

```json
{
  "auto_start": true,           // Server automatisch starten
  "auto_browser": true,         // Browser automatisch öffnen
  "minimize_to_tray": true,     // In System Tray minimieren
  "port": 5000,                // Server-Port
  "debug_mode": false          // Debug-Modus
}
```

### API-Keys (Optional)
Für höhere Rate Limits können API-Keys in der Web-Oberfläche unter "Einstellungen" konfiguriert werden.

## 🔄 Updates

### Automatische Updates
1. Neue Version herunterladen
2. Alte Installation stoppen
3. `install.bat` der neuen Version ausführen
4. Einstellungen und Daten bleiben erhalten

## 🆘 Problembehandlung

### Server startet nicht
- **Port belegt**: Anderen Port in Einstellungen wählen
- **Firewall**: Windows Firewall-Ausnahme hinzufügen
- **Berechtigungen**: Als Administrator ausführen

### Anwendung öffnet sich nicht
- **Python fehlt**: Portable Version verwenden
- **Antivirus**: Ausnahme für MedicalSpyToolDesktop.exe
- **Logs prüfen**: `logs/medicalspytool.log` ansehen

### Browser öffnet nicht
- **Standard-Browser**: In Windows-Einstellungen setzen
- **Manuell öffnen**: http://localhost:5000
- **Proxy**: Proxy-Einstellungen prüfen

### Debug-Modus
```bash
# Für Entwickler und detaillierte Fehlersuche
MedicalSpyToolDesktop.exe --debug
```

## 📞 Support

### Hilfe-Quellen
1. **DESKTOP_INSTALLATION.md**: Detaillierte Installationsanleitung
2. **BENUTZERANLEITUNG.md**: Umfassendes Benutzerhandbuch
3. **Anwendung → Hilfe**: Integrierte Hilfe-Funktion
4. **Log-Dateien**: Für technische Probleme

### Online-Hilfe
- Projekt-Repository: [GitHub](https://github.com/maxaufknax/Medical-Spytool)
- Entwickler-Dokumentation: Im Code verfügbar

## 🔒 Datenschutz & Sicherheit

### Lokale Ausführung
- ✅ **Keine Cloud**: Alle Daten bleiben auf Ihrem PC
- ✅ **Keine Telemetrie**: Keine Datensammlung
- ✅ **Offline-fähig**: Funktioniert ohne Internet (außer Datenbankabfragen)
- ✅ **Verschlüsselt**: API-Keys werden verschlüsselt gespeichert

### Minimale Berechtigungen
- 🔒 **Netzwerk**: Nur für Datenbankabfragen
- 🔒 **Dateisystem**: Nur eigenes Verzeichnis
- 🔒 **System**: Standard-Benutzerrechte ausreichend

## 🎉 Los geht's!

Nach der Installation:

1. **Starten**: Desktop-Verknüpfung oder Startmenü
2. **Warten**: Server startet automatisch (ca. 5-10 Sekunden)
3. **Arbeiten**: Browser öffnet sich automatisch
4. **Minimieren**: Anwendung läuft im System Tray weiter

**Viel Erfolg mit Medical Spytool Desktop Version 2.0!** 🚀

---

*Entwickelt für medizinische Forschung und Publikationsanalyse*  
*Version 2.0 - Desktop Edition*