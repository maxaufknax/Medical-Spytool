# MedicalSpy - Wissenschaftliches Publikations-Suchwerkzeug

MedicalSpy ist eine umfassende Webanwendung zur Suche, Analyse und Verwaltung wissenschaftlicher medizinischer Publikationen. Sie bietet eine intuitive Oberfläche für die Abfrage mehrerer wissenschaftlicher Datenbanken, die Verwaltung von Forscherprofilen, die Visualisierung von Ergebnissen und den Export von Daten in verschiedenen Formaten.

![MedicalSpy Logo](generated-icon.png)

## Status

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker Support](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile)

## Features

- **Multi-Datenbank-Suche**: Abfrage von PubMed und Deutsche Nationalbibliothek (DNB) mit einer einheitlichen Schnittstelle
- **Forscherverwaltung**: Verwalten von Profilen von Forschern und deren Publikationen
- **Erweiterte Suchoptionen**: Filtern nach Datumsbereich, Sprache, Publikationstyp und mehr
- **Ergebnisvisualisierung**: Generieren von Diagrammen und Grafiken zu Publikationsdaten
- **Datenexport**: Export der Ergebnisse in CSV, Excel und andere Formate
- **Gespeicherte Suchen**: Speichern und Wiederverwenden komplexer Suchabfragen
- **Umfassende Protokollierung**: Nachverfolgung aller Aktivitäten und Überwachung der Systemleistung

## Neue Features in Version 3.0

- **Sicheres Authentifizierungssystem**: Benutzeranmeldung mit rollenbasierter Zugriffskontrolle
- **Verbesserte Fehlerbehandlung**: Benutzerfreundliche Fehlerseiten mit Support-IDs zur leichten Fehlerverfolgung
- **Erweiterte Exportfunktionen**: Flexibles Exportformat mit benutzerdefinierten Feldauswahlen
- **Responsive Design**: Vollständig für mobile Geräte und Tablets optimiert
- **Verbesserte Barrierefreiheit**: ARIA-Attribute, Tastaturfokus und Bildschirmleser-Unterstützung
- **Dark Mode**: Augenfreundliches Design für verschiedene Lichtverhältnisse
- **CSRF-Schutz**: Erhöhte Sicherheit für alle Formulare der Anwendung
- **Performance-Optimierungen**: Schnellere Suchgeschwindigkeit und kürzere Ladezeiten

## Schnellstart für Benutzer

### Windows-Installation

1. Stellen Sie sicher, dass Python 3.8+ installiert ist
2. Öffnen Sie PowerShell im Projektverzeichnis
3. Führen Sie das automatische Setup-Skript aus:
   ```powershell
   .\Start-MedicalSpytool.ps1
   ```
4. Die Anwendung startet automatisch und öffnet den Browser mit der Adresse: http://localhost:5000

### Linux/Mac Installation

1. Stellen Sie sicher, dass Python 3.8+ installiert ist
2. Öffnen Sie ein Terminal im Projektverzeichnis
3. Führen Sie das Setup-Script aus:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```
4. Die Anwendung startet automatisch und ist unter http://localhost:5000 erreichbar

### Docker Installation (empfohlen für Server)

1. Stellen Sie sicher, dass Docker und Docker Compose installiert sind
2. Öffnen Sie ein Terminal im Projektverzeichnis
3. Starten Sie die Anwendung mit Docker:
   ```bash
   docker-compose up -d
   ```
4. Die Anwendung ist nun unter http://localhost:5000 erreichbar
5. Überprüfen Sie den Status mit:
   ```bash
   docker-compose ps
   ```

## Entwicklerhandbuch

### Lokale Entwicklungsumgebung einrichten

1. Klonen Sie das Repository:
   ```bash
   git clone https://github.com/your-organization/medical-spytool.git
   cd medical-spytool
   ```

2. Richten Sie die Entwicklungsumgebung ein:
   ```bash
   python scripts/setup_dev_env.py
   ```
   Dieses Skript erstellt eine virtuelle Python-Umgebung, installiert alle Abhängigkeiten und initialisiert die Datenbank.

3. Starten Sie die Anwendung im Entwicklungsmodus:
   ```bash
   python run.py --debug
   ```

### Testen

Die Anwendung enthält umfangreiche Tests, die mit pytest ausgeführt werden können:

```bash
# Alle Tests ausführen
python run_tests.py

# Tests mit Coverage-Report ausführen
python run_tests.py --coverage --html-report

# Spezifische Tests ausführen
python run_tests.py --test-path tests/test_models.py
```

### Mit dem Makefile arbeiten

Die Anwendung enthält ein Makefile für häufige Entwicklungsaufgaben:

```bash
# Hilfe anzeigen
make help

# Anwendung starten
make run

# Tests ausführen
make test

# Cache-Dateien löschen
make clean

# Docker starten
make docker

# Datenbank initialisieren
make init-db

# Abhängigkeiten aktualisieren
make update-deps
```

### Datenbank-Management

Die SQLite-Datenbank wird standardmäßig im `instance/medicalspy.db` gespeichert. PostgreSQL kann alternativ konfiguriert werden.

```bash
# Datenbank initialisieren/zurücksetzen
python init_db.py

# Backup erstellen
python scripts/backup_database.py

# Systemzustand überprüfen
python scripts/health_check.py
```

### Verzeichnisstruktur

```
medical-spytool/
│
├── backend/             # Backend-Code
│   ├── app.py           # Flask-App-Definition
│   ├── models.py        # Datenbank-Modelle (SQLAlchemy)
│   ├── connectors.py    # Datenbankverbindungen (PubMed, DNB)
│   └── utils.py         # Hilfsfunktionen
│
├── docs/                # Dokumentation
├── instance/            # Instanz-spezifische Daten (DB)
├── logs/                # Logdateien
├── output/              # Exportierte Daten
├── person_lists/        # Personenlisten
├── scripts/             # Hilfsskripte
├── static/              # Statische Dateien (CSS, JS)
├── templates/           # HTML-Templates
└── tests/               # Testfälle
```

## Logging und Fehlerbehandlung

Die Anwendung verwendet strukturierte Logs, die in der Datei `logs/medicalspy.log` gespeichert werden. Das Logging-Level kann in der `.env`-Datei oder beim Start der Anwendung konfiguriert werden:

```bash
# Über Umgebungsvariable
LOG_LEVEL=DEBUG python run.py

# Über Parameter
python run.py --log-level DEBUG
```

## API-Dokumentation

Die API-Dokumentation ist unter `/api/docs` verfügbar, wenn die Anwendung läuft.

## Abhängigkeiten

Alle Abhängigkeiten sind in der `project_requirements.txt` aufgeführt und können mit pip installiert werden.

## Entwicklung mit KI-Unterstützung

Die Anwendung ist für die Entwicklung mit GitHub Copilot oder anderen KI-Coding-Assistenten optimiert:

1. Die Code-Struktur ist klar dokumentiert und folgt den Best Practices
2. Klare Namenskonventionen und Kommentare erleichtern das Verständnis
3. Die Architektur ist modular aufgebaut, was Erweiterungen vereinfacht
4. Die bereitgestellten Hilfsskripte unterstützen eine schnelle Iteration

Tipps für KI-gestützte Entwicklung:
- Verwenden Sie detaillierte Prompt-Beschreibungen
- Verweisen Sie auf bestehende Dateien und Funktionen
- Nutzen Sie die Tests als Dokumentation der erwarteten Funktionalität

## Lizenz

MedicalSpy wird unter der MIT-Lizenz verteilt. Siehe die `LICENSE`-Datei für weitere Details.

## Mitwirkung

Beiträge sind willkommen! Bitte lesen Sie die `CONTRIBUTING.md` für Richtlinien zum Einreichen von Pull Requests und Issues.

---

Entwickelt mit ♥ für die medizinische Forschungsgemeinschaft.