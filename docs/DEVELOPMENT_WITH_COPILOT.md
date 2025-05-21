# Entwicklung mit GitHub Copilot für Medical Spytool

Diese Anleitung erklärt, wie GitHub Copilot effektiv für die Entwicklung und Erweiterung der Medical Spytool Anwendung eingesetzt werden kann.

## Einführung

GitHub Copilot ist ein KI-gestützter Programmierassistent, der bei der Codierung unterstützt. Für die Medical Spytool Anwendung kann Copilot besonders hilfreich sein, um:

- Neue Features zu implementieren
- Bestehenden Code zu verstehen
- Tests zu schreiben
- Bugs zu fixen
- Dokumentation zu generieren

## Vorteile für die Medical Spytool-Entwicklung

1. **Schnellere Implementierung**: Copilot kann Flask-Routen, SQLAlchemy-Modelle und andere projektspezifische Elemente basierend auf dem bestehenden Code generieren
2. **Konsistenter Stil**: Der Code folgt einem einheitlichen Stil, den Copilot erkennt und reproduzieren kann
3. **Automatische Dokumentation**: Automatisches Erstellen von Docstrings und Kommentaren
4. **Unterstützung bei Tests**: Generieren von Testfällen basierend auf der Funktionalität

## Effektive Nutzung mit Medical Spytool

### 1. Verständnis der Anwendungsstruktur

Medical Spytool folgt einer klaren Struktur, die Copilot leicht verstehen kann:

- `backend/models.py`: Datenbankmodelle mit SQLAlchemy
- `backend/app.py`: Hauptanwendungslogik und Flask-Setup
- `backend/connectors.py`: Verbindungen zu externen Datenbanken (PubMed, DNB)
- `backend/blueprints/`: Modularisierte Routen nach Funktionalität
- `tests/`: Automatisierte Tests
- `scripts/`: Hilfsskripte für Entwicklung und Wartung

### 2. Best Practices für Prompts

Verwenden Sie diese Strategien für effektive Prompts mit dem Medical Spytool Codebase:

#### Spezifische Kontextangabe

```
# Für eine neue Route zum Exportieren von Daten im CSV-Format
# Datei: backend/blueprints/export.py
# Benötigt: Zugriff auf SearchResult-Modell und CSV-Generierung
```

#### Referenzieren Sie bestehende Implementierungen

```
# Implementiere eine neue Methode im SearchQuery-Modell, ähnlich wie
# die get_logs Methode im LogEntry-Modell (backend/models.py)
```

#### Für Fehlerbehebungen

```
# Fehler: Die Suche in der DNB schlägt fehl mit folgendem Fehler: [error details]
# Datei: backend/connectors.py, DNBConnector-Klasse
# Problem: XML-Parsing funktioniert nicht korrekt
```

### 3. Code-Generierung Beispiele

#### Neue Datenbankmodelle erstellen

```python
# Erstelle ein neues Modell für gespeicherte Exportvorlagen
# mit Feldern für: Name, Format (CSV/Excel/PDF), ausgewählte Spalten
```

#### API-Endpunkt erweitern

```python
# Erweitere den /api/search Endpunkt um Parameter für Filterung nach Datum
# mit start_date und end_date als optionale Parameter
```

#### Tests schreiben

```python
# Schreibe einen Test für die LogEntry.clear_logs Methode
# der prüft, ob Logs älter als ein Datum gelöscht werden
```

### 4. Debugging mit Copilot

Für das Debugging kann man Copilot so anleiten:

```
# Debug-Hilfe: get_database_stats() function in backend/utils.py
# gibt KeyError: 'PubMed' wenn die Datenbank leer ist
# Implementiere eine Lösung, die prüft ob Daten vorhanden sind
```

## Projektspezifische Themen

### Datenbankverbindungen

Die Medical Spytool Anwendung verbindet sich mit mehreren externen Datenbanken. Kopilot kann bei der Implementierung neuer Connectoren helfen:

```
# Implementiere einen neuen Connector für Scopus
# basierend auf dem PubMedConnector in backend/connectors.py
```

### Datenmodellierung

Die Anwendung verwendet SQLAlchemy für die Datenbankmodellierung:

```
# Erweitere das SearchQuery-Modell um ein Feld für die Suchsprache
# mit einer Beziehung zu einer neuen Language-Tabelle
```

### Frontend-Integration

Für die Integration neuer Features ins Frontend:

```
# Erstelle eine neue Jinja2-Template für die Anzeige von Statistiken
# basierend auf analysis.html mit Plotly-Diagrammen
```

## Zusammenfassung

GitHub Copilot kann die Entwicklung der Medical Spytool Anwendung erheblich beschleunigen. Durch das Verständnis der Projektstruktur und die Verwendung spezifischer Prompts können Entwickler:

1. Zeit beim Implementieren neuer Features sparen
2. Die Codequalität und -konsistenz verbessern
3. Bessere Tests und Dokumentation erstellen
4. Schneller Bugs identifizieren und beheben

Kombinieren Sie Copilot mit den bereitgestellten Entwicklungswerkzeugen wie dem `run_tests.py` Script und dem Makefile für eine optimale Entwicklungserfahrung.
