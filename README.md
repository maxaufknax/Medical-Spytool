# MedicalSpy - Wissenschaftliches Publikations-Suchwerkzeug

MedicalSpy ist eine umfassende Webanwendung zur Suche, Analyse und Verwaltung wissenschaftlicher medizinischer Publikationen. Sie bietet eine intuitive Oberfläche für die Abfrage mehrerer wissenschaftlicher Datenbanken, die Verwaltung von Forscherprofilen, die Visualisierung von Ergebnissen und den Export von Daten in verschiedenen Formaten.

![MedicalSpy Logo](generated-icon.png)

## Status

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker Support](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile)

## Features

- **Multi-Datenbank-Suche**: Abfrage von PubMed und Deutsche Nationalbibliothek (DNB) mit einer einheitlichen Schnittstelle
- **Forscherverwaltung**: Verwalten von Profilen von Forschern und deren Publikationen
- **Erweiterte Suchoptionen**: Filtern nach Datumsbereich, Sprache, Publikationstyp und mehr
- **Ergebnisvisualisierung**: Generieren von Diagrammen und Grafiken zu Publikationsdaten
- **Datenexport**: Export der Ergebnisse in CSV, Excel und BibTeX Formate
- **Gespeicherte Suchen**: Speichern und Wiederverwenden komplexer Suchabfragen
- **Umfassende Protokollierung**: Nachverfolgung aller Aktivitäten und Überwachung der Systemleistung

## Neu in dieser Version

- **Verbesserte Suchfunktionalität**: PubMed und DNB Konnektoren wurden stabilisiert und optimiert
- **API-Schlüssel-Unterstützung**: Einfache Konfiguration von API-Schlüsseln über Umgebungsvariablen
- **Besseres visuelles Feedback**: Ladeanimationen und Statusmeldungen bei Suchvorgängen
- **Robuste Fehlerbehandlung**: Klare Fehlermeldungen und bessere Erholung von Fehlerzuständen
- **Verbesserte Ergebnisdarstellung**: Karten- und Listenansicht mit Sortier- und Filterfunktionen
- **Optimierte Exportfunktionen**: Verbesserte BibTeX-Generierung und flexiblere Spaltenauswahl
- **CSRF-Schutz**: Erhöhte Sicherheit für alle Formulare der Anwendung
- **Dark Mode**: Augenfreundliches Design für verschiedene Lichtverhältnisse
- **Performance-Optimierungen**: Schnellere Suchgeschwindigkeit und kürzere Ladezeiten

## Schnellstart

Das Projekt verwendet nun ein zentrales `manage.py` Skript für alle Setup- und Ausführungsaufgaben.

### Windows

1.  Stellen Sie sicher, dass Python 3.8+ installiert und im PATH verfügbar ist.
2.  Öffnen Sie eine PowerShell oder Eingabeaufforderung im Projektverzeichnis.
3.  **Setup (einmalig oder nach Updates):**
    Führen Sie den folgenden Befehl aus, um die virtuelle Umgebung einzurichten, Abhängigkeiten zu installieren, die `.env`-Datei zu erstellen und die Datenbank zu initialisieren:
    ```bash
    python manage.py setup --full
    ```
    Für spezifische Setup-Schritte, siehe `python manage.py setup --help`.
4.  **Anwendung starten:**
    ```bash
    python manage.py run --open-browser
    ```
    Dieser Befehl startet den Entwicklungsserver und öffnet die Anwendung in Ihrem Standardbrowser.
    Für weitere Optionen (z.B. anderer Port, kein Browser-Start), siehe `python manage.py run --help`.

    Alternativ können Sie die vereinfachten Batch-Skripte verwenden:
    *   `setup.cmd` (führt `python manage.py setup --full` aus)
    *   `start.bat` (führt `python manage.py run --open-browser` aus)
    *   `Start-MedicalSpytool.ps1` (PowerShell-Skript, das `manage.py` für Setup und Start verwendet)

### Linux/MacOS

1.  Stellen Sie sicher, dass Python 3.8+ (oder `python3`) installiert und im PATH verfügbar ist.
2.  Öffnen Sie ein Terminal im Projektverzeichnis.
3.  **Setup (einmalig oder nach Updates):**
    Führen Sie den folgenden Befehl aus, um die virtuelle Umgebung einzurichten, Abhängigkeiten zu installieren, die `.env`-Datei zu erstellen und die Datenbank zu initialisieren:
    ```bash
    python3 manage.py setup --full 
    # oder: python manage.py setup --full
    ```
    Für spezifische Setup-Schritte, siehe `python3 manage.py setup --help`.
4.  **Anwendung starten:**
    ```bash
    python3 manage.py run --open-browser
    # oder: python manage.py run --open-browser
    ```
    Dieser Befehl startet den Entwicklungsserver und öffnet die Anwendung in Ihrem Standardbrowser.
    Für weitere Optionen (z.B. anderer Port, kein Browser-Start), siehe `python3 manage.py run --help`.

    Alternativ können Sie das vereinfachte Shell-Skript verwenden (stellen Sie sicher, dass es ausführbar ist: `chmod +x start.sh`):
    *   `./start.sh` (führt `manage.py setup --full` und dann `manage.py run --open-browser` aus)

### Docker Installation

1.  Stellen Sie sicher, dass Docker und Docker Compose installiert sind.
2.  Öffnen Sie ein Terminal im Projektverzeichnis.
3.  Erstellen und starten Sie die Container:
    ```bash
    docker-compose up -d
    ```
4.  Öffnen Sie Ihren Browser unter: http://localhost:5000 (oder dem in Ihrer Docker-Konfiguration festgelegten Port).

## System Requirements

### Minimum Requirements

- Python 3.8 oder höher
- 2GB RAM
- 1GB free disk space
- Internet connection for database queries

### Optional

- PostgreSQL database (SQLite is used by default, konfiguriert durch `manage.py`)
- PubMed API key for higher rate limits (kann in der `.env`-Datei gesetzt werden)

## Configuration

Die Anwendung wird primär über eine `.env`-Datei im Projekt-Root-Verzeichnis konfiguriert. Diese Datei wird automatisch vom `manage.py setup --env` Befehl mit Standardwerten erstellt.

### Wichtige Konfigurationsoptionen (`.env` Datei)

| Variable         | Beschreibung                                     | Standard (von `manage.py` gesetzt) |
|------------------|--------------------------------------------------|------------------------------------|
| `DATABASE_URL`   | Datenbank-Verbindungsstring                      | `sqlite:///instance/medicalspy.db` |
| `FLASK_APP`      | Flask Applikationseinstiegspunkt                 | `backend.app:create_app()`         |
| `FLASK_ENV`      | Flask Umgebung (development, production)         | `development`                      |
| `SECRET_KEY`     | Geheimer Schlüssel für Session-Verschlüsselung   | (generierter Zufallswert)          |
| `LOG_LEVEL`      | Logging-Level (DEBUG, INFO, WARNING, ERROR)    | `INFO`                             |
| `PUBMED_API_KEY` | API-Schlüssel für PubMed (optional)              | `your_pubmed_api_key_here`         |
| `DNB_API_KEY`    | API-Schlüssel für DNB (optional)                 | `your_dnb_api_key_here`            |


## Nutzung

### Einfache Suche

1. Navigieren Sie zur Suchseite über das Hauptmenü
2. Geben Sie Suchbegriffe ein
3. Wählen Sie Datenbanken aus (PubMed, DNB, oder beide)
4. Klicken Sie auf "Suchen"

### Erweiterte Suche

- Klicken Sie auf "Erweiterte Suche" für komplexe Abfragen
- Filtern nach Zeitraum, Publikationstyp und mehr
- Verwenden Sie Autor:in-basierte Suche für gezielte Resultate

### Ergebnisse exportieren

1. Führen Sie eine Suche durch
2. Auf der Ergebnisseite finden Sie Export-Optionen oben rechts
3. Wählen Sie das gewünschte Format (CSV, Excel, BibTeX)
4. Wählen Sie die zu exportierenden Spalten im Dialog
5. Klicken Sie auf "Exportieren" um die Datei herunterzuladen

### Ergebnisse filtern und sortieren

- Verwenden Sie das Filterfeld auf der Ergebnisseite, um Ergebnisse zu filtern
- Klicken Sie auf Spaltenüberschriften in der Listenansicht zum Sortieren
- Wechseln Sie zwischen Listen- und Kartenansicht mit den entsprechenden Buttons
