# Entwicklungs-Workflow für Medical Spytool

Diese Anleitung beschreibt den empfohlenen Entwicklungs-Workflow für die Medical Spytool Anwendung. Sie richtet sich an Entwickler, die an der Weiterentwicklung der Anwendung arbeiten.

## Einrichtung der Entwicklungsumgebung

### Voraussetzungen

- Python 3.8 oder höher
- Git
- Ein Code-Editor (empfohlen: VS Code mit Python-Erweiterung)
- Optional: Docker und Docker Compose (für containerisierte Entwicklung)

### Erstmalige Einrichtung

1. **Repository klonen:**

   ```powershell
   git clone <repository-url>
   cd Medical-Spytool-2
   ```

2. **Entwicklungsumgebung einrichten:**

   ```powershell
   python scripts/setup_dev_env.py
   ```

   Dieses Skript wird:
   - Eine virtuelle Python-Umgebung erstellen
   - Abhängigkeiten installieren
   - Verzeichnisse anlegen
   - Die Datenbank initialisieren
   - Eine Beispiel-Konfiguration erstellen

3. **Umgebungsvariablen konfigurieren:**

   ```powershell
   copy .env.example .env
   ```

   Bearbeiten Sie die `.env`-Datei und passen Sie die Werte an Ihre Umgebung an.

## Täglicher Entwicklungsworkflow

### 1. Anwendung starten

**Methode 1:** Direkt über Python:

```powershell
python run.py
```

**Methode 2:** Mit dem Makefile:

```powershell
make run
```

**Methode 3:** Über PowerShell-Skript:

```powershell
.\Start-MedicalSpytool.ps1
```

Die Anwendung ist dann unter http://localhost:5000 verfügbar.

### 2. Änderungen testen

Nach Änderungen am Code sollten Tests ausgeführt werden:

```powershell
python run_tests.py
```

Oder mit Coverage-Report:

```powershell
python run_tests.py --coverage --html-report
```

Der HTML-Report wird im Verzeichnis `coverage_report` erstellt.

### 3. Typische Entwicklungsaufgaben

#### Neue Route hinzufügen

1. Identifizieren Sie den passenden Blueprint in `backend/blueprints/`
2. Fügen Sie die neue Route hinzu
3. Erstellen Sie ein Template in `backend/templates/` falls benötigt
4. Fügen Sie Tests in `tests/` hinzu

Beispiel:

```python
@search_bp.route('/advanced-search', methods=['GET', 'POST'])
def advanced_search():
    # Implementierung
    return render_template('advanced_search.html', form=form)
```

#### Datenbankmodell ändern

1. Aktualisieren Sie die Modelle in `backend/models.py`
2. Starten Sie die Anwendung neu oder führen Sie die Migration manuell aus

Beispiel für ein neues Feld:

```python
class SearchQuery(db.Model):
    # Bestehende Felder...
    language = db.Column(db.String(50), nullable=True)
```

#### API-Endpunkt hinzufügen

1. Fügen Sie den Endpunkt zum entsprechenden Blueprint hinzu
2. Dokumentieren Sie den Endpunkt mit Swagger/Flasgger

Beispiel:

```python
@api_bp.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get search statistics
    ---
    tags:
      - Statistics
    responses:
      200:
        description: Statistics data
    """
    # Implementation
    return jsonify(stats)
```

## Datenbank-Management

### Datenbank initialisieren

```powershell
python init_db.py
```

### Backup erstellen

```powershell
python scripts/backup_database.py
```

### Datenbank prüfen

```powershell
python scripts/health_check.py --no-web
```

## Containerisierte Entwicklung

### Container starten

```powershell
docker-compose up -d
```

### Container-Logs anzeigen

```powershell
docker-compose logs -f
```

### Container stoppen

```powershell
docker-compose down
```

## Deployment

### Für Produktionsumgebungen

1. **Datenbank konfigurieren:**
   - Für Produktionsumgebungen wird PostgreSQL empfohlen
   - Setzen Sie die DATABASE_URL in der .env-Datei

2. **Sicherheitseinstellungen anpassen:**
   - Generieren Sie ein sicheres SESSION_SECRET
   - Setzen Sie DEBUG=False

3. **Mit Docker deployen:**

   ```powershell
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

   oder

   ```powershell
   docker-compose up -d
   ```

### Für lokale Server

Verwenden Sie Gunicorn (Linux/Mac) oder Waitress (Windows) als WSGI-Server:

```powershell
# Linux/Mac
gunicorn -w 4 main:app

# Windows
waitress-serve --port=5000 main:app
```

## Best Practices

### Code-Stil

- Befolgen Sie PEP 8 für Python-Code
- Verwenden Sie aussagekräftige Variablen- und Funktionsnamen
- Kommentieren Sie komplexe Logik
- Schreiben Sie Docstrings für alle Funktionen und Klassen

### Git-Workflow

- Verwenden Sie Feature-Branches für neue Funktionen
- Schreiben Sie aussagekräftige Commit-Messages
- Führen Sie Tests durch, bevor Sie Code pushen

### Fehlerbehandlung

- Verwenden Sie try/except-Blöcke für erwartete Fehler
- Loggen Sie Fehler mit dem integrierten Logger
- Geben Sie hilfreiche Fehlermeldungen zurück

## Problembehandlung

### Datenbank-Probleme

**Problem:** Die Anwendung kann keine Verbindung zur Datenbank herstellen
**Lösung:** Prüfen Sie die DATABASE_URL in der .env-Datei und stellen Sie sicher, dass die Datenbank erreichbar ist

### Import-Fehler

**Problem:** ModuleNotFoundError beim Start der Anwendung
**Lösung:** Stellen Sie sicher, dass alle Abhängigkeiten installiert sind (`pip install -r project_requirements.txt`)

### Port bereits in Verwendung

**Problem:** Der Port 5000 ist bereits in Verwendung
**Lösung:** Ändern Sie den Port in der .env-Datei oder beim Start (`python run.py --port 5001`)

## Weitere Ressourcen

- [Flask-Dokumentation](https://flask.palletsprojects.com/)
- [SQLAlchemy-Dokumentation](https://docs.sqlalchemy.org/)
- [Server-Bereitstellung](./SERVER_BEREITSTELLUNG.md)
- [Entwicklung mit GitHub Copilot](./DEVELOPMENT_WITH_COPILOT.md)
