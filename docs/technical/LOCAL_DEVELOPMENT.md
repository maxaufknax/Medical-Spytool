# Lokale Entwicklung von MedicalSpy in Visual Studio Code

Diese Anleitung hilft Ihnen bei der Einrichtung und Entwicklung der MedicalSpy-Anwendung in Visual Studio Code.

## Voraussetzungen

1. **Python 3.10 oder höher**
   - [Python herunterladen und installieren](https://www.python.org/downloads/)
   - Überprüfen Sie die Installation: `python --version`

2. **PostgreSQL Datenbank**
   - [PostgreSQL herunterladen und installieren](https://www.postgresql.org/download/)
   - Standardmäßig wird der Port 5432 verwendet

3. **Visual Studio Code**
   - [Visual Studio Code herunterladen und installieren](https://code.visualstudio.com/download)
   - Empfohlene Erweiterungen werden automatisch vorgeschlagen, wenn Sie das Projekt öffnen

## Einrichtung der Entwicklungsumgebung

### 1. Klonen des Repositories

```bash
git clone <repository-url>
cd medicalspy
```

### 2. Virtuelle Umgebung erstellen

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Abhängigkeiten installieren

```bash
pip install -r project_requirements.txt
```

### 4. Umgebungsvariablen konfigurieren

Kopieren Sie die `.env.example`-Datei zu `.env` und passen Sie die Variablen an:

```bash
cp .env.example .env
```

Bearbeiten Sie dann die `.env`-Datei mit Ihren Einstellungen:

```
# Datenbank-Konfiguration
DATABASE_URL=postgresql://benutzername:passwort@localhost:5432/medicalspy

# API-Schlüssel
PUBMED_API_KEY=Ihr_PubMed_API_Schlüssel

# Anwendungseinstellungen
LOG_LEVEL=DEBUG
OUTPUT_PATH=./output
PERSON_LIST_PATH=./person_lists
```

### 5. Projekt in Visual Studio Code öffnen

```bash
code .
```

## Entwicklung mit Visual Studio Code

Die Projekteinstellungen für VS Code wurden bereits konfiguriert. Dazu gehören:

1. **Ausführungskonfigurationen (Debug-Konfigurationen)**
   - `MedicalSpy: Run (Debug)`: Startet die Anwendung im Debug-Modus
   - `MedicalSpy: Run (Production)`: Startet die Anwendung mit Gunicorn (Produktionsmodus)
   - `MedicalSpy: Check only`: Führt nur die Konfigurations- und Verbindungsprüfungen durch
   - `MedicalSpy: Run tests`: Führt die Tests aus
   - `MedicalSpy: DB Tools`: Führt die Datenbank-Tools aus

2. **Empfohlene Erweiterungen**
   - Python-Unterstützung und Linting
   - Docker-Integration
   - Git-Unterstützung
   - und mehr

## Datenbank-Initialisierung

Verwenden Sie das `db_tools.py`-Skript, um die Datenbank zu initialisieren:

```bash
# Datenbank initialisieren
python db_tools.py --init

# Datenbank-Verbindung überprüfen
python db_tools.py --check

# Testdaten hinzufügen
python db_tools.py --add-sample
```

## Testen

Die Tests befinden sich im Verzeichnis `tests/`. Sie können einzelne Tests oder das gesamte Test-Suite ausführen:

```bash
# Alle Tests ausführen
python run_tests.py

# Tests mit erhöhter Ausführlichkeit
python run_tests.py --verbosity 2

# Spezifische Tests ausführen
python run_tests.py --test-path tests/test_connectors.py
```

## Debugging in VS Code

1. Setzen Sie Breakpoints, indem Sie auf die linke Seite neben der Zeilennummer klicken
2. Wählen Sie eine Debug-Konfiguration aus dem Debug-Menü
3. Drücken Sie F5 oder klicken Sie auf den grünen Play-Button, um das Debugging zu starten

## Entwicklung mit Docker

Wenn Sie Docker verwenden möchten, wird die Anwendung ebenfalls mit Docker-Unterstützung geliefert:

```bash
# Anwendung mit Docker Compose starten
docker-compose up --build

# Im Hintergrund ausführen
docker-compose up -d

# Container stoppen
docker-compose down
```

## Bekannte Probleme und Workarounds

### Datenbankfehler

Wenn Sie Probleme mit der Datenbankverbindung haben:

1. Stellen Sie sicher, dass PostgreSQL läuft
2. Überprüfen Sie die PostgreSQL-Anmeldedaten in der `.env`-Datei
3. Führen Sie `python db_tools.py --check` aus, um die Verbindung zu testen

### Fehlende API-Schlüssel

Für bestimmte Funktionen werden API-Schlüssel benötigt:

- **PubMed**: Beantragen Sie einen API-Schlüssel bei [NCBI](https://www.ncbi.nlm.nih.gov/home/develop/api/)
- **Scopus**: Beantragen Sie einen API-Schlüssel bei [Elsevier](https://dev.elsevier.com/)
- **Web of Science**: Beantragen Sie Zugriff bei [Clarivate](https://clarivate.com/products/web-of-science/)

## Projektstruktur

```
medicalspy/
├── .vscode/                    # VS Code-Konfiguration
├── backend/                    # Hauptmodul der Anwendung
│   ├── connectors/             # API-Konnektoren für verschiedene Datenbanken
│   ├── models/                 # SQLAlchemy-Modelle
│   ├── static/                 # Statische Dateien (CSS, JS)
│   ├── templates/              # Jinja2-Templates
│   ├── app.py                  # Flask-Anwendung
│   ├── config.py               # Konfigurationsmodul
│   └── ...
├── tests/                      # Test-Dateien
├── docker-compose.yml          # Docker Compose-Konfiguration
├── Dockerfile                  # Docker-Konfiguration
├── main.py                     # Haupteinstiegspunkt für Produktion
├── run.py                      # Einstiegspunkt für Entwicklung
├── db_tools.py                 # Datenbank-Tools
└── ...
```

## Hilfe und Support

Bei Fragen oder Problemen:

1. Überprüfen Sie die [offizielle Dokumentation](link-zur-dokumentation)
2. Erstellen Sie ein Issue im GitHub-Repository
3. Kontaktieren Sie das Entwicklungsteam unter [Kontakt-E-Mail]