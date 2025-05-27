# MedicalSpyTool - Flask Webanwendung

## ✅ Status: Vollständig funktionsfähig und einsatzbereit

Die MedicalSpyTool Anwendung ist **vollständig getestet** und **produktionsbereit**. 

### 🚀 Schnellstart

#### Option 1: Automatischer Start (Empfohlen)
```bash
# Doppelklick auf das Startskript
start_application.bat
```

#### Option 2: Manueller Start
```bash
# Terminal öffnen und ausführen
python main.py
```

#### Option 3: Test vor Start
```bash
# Alle Funktionen testen
python test_setup.py

# Demo ausführen  
python demo.py

# Dann die Anwendung starten
python main.py
```

### 🌐 Zugriff
Nach dem Start ist die Anwendung verfügbar unter:
**http://127.0.0.1:5000**

## ✨ Vollständig implementierte Features

### 🔍 Multi-Datenbank Suche
- ✅ **PubMed**: Medizinische Publikationen
- ✅ **Deutsche Nationalbibliothek (DNB)**: Deutsche Publikationen  
- ✅ **Scopus**: Wissenschaftliche Abstracts
- ✅ **Web of Science**: Zitationsdatenbank
- ✅ **GEPRIS**: Deutsche Forschungsprojekte
- ✅ **Kombinierte Suche**: Alle Datenbanken gleichzeitig

### 🎯 Suchfunktionen
- ✅ **Schnellsuche**: Einfache Eingabe über alle Datenbanken
- ✅ **Erweiterte Suche**: Detaillierte Filter und Parameter
- ✅ **Personenbezogene Suche**: Gezielte Suchen für Forscher
- ✅ **Suchprofile**: Wiederverwendbare Suchkonfigurationen
- ✅ **Batch-Verarbeitung**: Mehrere Personen gleichzeitig

### 👥 Personenverwaltung
- ✅ **Person hinzufügen/bearbeiten/löschen**
- ✅ **Import aus CSV/Excel**
- ✅ **Suchbegriffe pro Person**
- ✅ **Automatisierte Personensuchen**

### 📊 Analyse & Visualisierung
- ✅ **Statistische Auswertungen**
- ✅ **Publikationstrends über Zeit**
- ✅ **Datenbankverteilung**
- ✅ **Häufigste Autoren**
- ✅ **Interaktive Diagramme**

### 📄 Export-Funktionen
- ✅ **Excel Export**: Vollständige Metadaten
- ✅ **CSV Export**: Einfacher Datenexport
- ✅ **Eindeutige Dateinamen**: Vermeidung von Überschreibungen
- ✅ **Konfigurierbare Spalten**

### ⚙️ Konfiguration & Einstellungen
- ✅ **API-Key Verwaltung**
- ✅ **Ausgabepfad-Konfiguration**
- ✅ **Suchparameter anpassen**
- ✅ **System-Informationen**
- ✅ **Pfad-Validierung**

### 🔧 Benutzerfreundlichkeit
- ✅ **Responsive Web-Interface**
- ✅ **Dark Theme Design**
- ✅ **Progress-Anzeigen bei Suchen**
- ✅ **Fehlerbehandlung und Validierung**
- ✅ **Vollständiges Logging**
- ✅ **Automatische Verzeichniserstellung**

## 🧪 Getestete Funktionen

Alle wichtigen Komponenten wurden erfolgreich getestet:

- ✅ **Module-Importe**: Alle Dependencies verfügbar
- ✅ **Verzeichnisstruktur**: Alle Ordner erstellt
- ✅ **Konfiguration**: Settings korrekt geladen  
- ✅ **Datenbankverbindungen**: Alle Connectoren funktional
- ✅ **Flask-Anwendung**: Alle Routes erreichbar
- ✅ **Webinterface**: Vollständig funktional
- ✅ **Suchfunktionen**: Multi-Datenbank Suche getestet
- ✅ **Export**: Excel/CSV Generation funktional

## Systemanforderungen

- Python 3.8 oder höher
- Alle erforderlichen Python-Pakete (siehe requirements.txt)
- Internetverbindung für Datenbankabfragen

## Verzeichnisstruktur

```
├── main.py                 # Haupt-Flask-Anwendung
├── start_application.bat   # Automatisches Startskript
├── requirements.txt        # Python-Abhängigkeiten
├── medicalspytool_config.json # Konfigurationsdatei
├── database_connectors/    # Datenbankverbindungen
├── utils/                  # Hilfsfunktionen
├── templates/              # HTML-Templates
├── static/                 # CSS, JS, Bilder
├── output/                 # Exportierte Dateien
├── logs/                   # Anwendungslogs
└── person_lists/           # Gespeicherte Personenlisten
```

## Problembehandlung

### Anwendung startet nicht
1. Prüfen Sie ob Python installiert ist: `python --version`
2. Installieren Sie fehlende Abhängigkeiten: `pip install -r requirements.txt`
3. Prüfen Sie die Logs im `logs/` Verzeichnis

### Port bereits belegt
Falls Port 5000 bereits belegt ist, können Sie die Anwendung auf einem anderen Port starten:
```bash
python main.py --port 5001
```

### API-Fehler
1. Überprüfen Sie Ihre Internetverbindung
2. Konfigurieren Sie API-Keys in den Einstellungen (falls erforderlich)
3. Prüfen Sie die Verfügbarkeit der externen Datenbanken

## Unterstützung

Bei Problemen oder Fragen:
1. Prüfen Sie die Logdateien im `logs/` Verzeichnis
2. Überprüfen Sie die Konfiguration in `medicalspytool_config.json`
3. Stellen Sie sicher, dass alle Abhängigkeiten installiert sind

---

**Version:** 1.0  
**Entwickelt für:** Medizinische Publikationssuche und -analyse
