# Medical Spytool - Test Guide

Dieses Dokument bietet eine umfassende Anleitung zum Testen und zur Fehlerbehebung der Medical Spytool-Anwendung.

## Inhaltsverzeichnis

1. [Voraussetzungen](#voraussetzungen)
2. [Schnellstart](#schnellstart)
3. [Schritt-für-Schritt-Anleitung](#schritt-für-schritt-anleitung)
4. [Testen der Anwendung](#testen-der-anwendung)
5. [Bekannte Probleme & Lösungen](#bekannte-probleme--lösungen)
6. [Diagnoseskripte](#diagnoseskripte)

## Voraussetzungen

- Python 3.6 oder höher
- Pip (Python-Paketmanager)
- Venv (für virtuelle Umgebungen)
- Git (optional, für Versionskontrolle)

## Schnellstart

Führen Sie die folgenden Befehle aus, um die Anwendung schnell zu starten:

```powershell
# 1. Diagnose ausführen, um Probleme zu identifizieren und zu beheben
python diagnostic.py

# 2. Datenbank mit Beispieldaten erstellen
python create_test_data.py

# 3. Anwendung starten
python run.py
```

## Schritt-für-Schritt-Anleitung

### 1. Umgebung einrichten

```powershell
# Virtuelle Umgebung erstellen
python -m venv venv

# Virtuelle Umgebung aktivieren
.\venv\Scripts\Activate.ps1

# Abhängigkeiten installieren
pip install -r project_requirements.txt
```

### 2. Probleme mit JSONB-Typ beheben

Das häufigste Problem ist die Inkompatibilität zwischen SQLite und PostgreSQL bei JSONB-Typen:

```powershell
python fix_database.py
```

### 3. Datenbank initialisieren

```powershell
python initialize_db.py
```

Erstellen Sie eine Testdatenbank mit Beispieldaten:

```powershell
python create_test_data.py
```

### 4. Anwendung starten

```powershell
python run.py
```

## Testen der Anwendung

### Automatisierte Tests

Medical Spytool verfügt über eine umfangreiche Testsuite, die mit PyTest implementiert ist:

```powershell
# Alle Tests ausführen
python run_tests.py

# Tests mit Coverage-Bericht ausführen
python run_tests.py --coverage

# HTML-Coverage-Bericht erstellen
python run_tests.py --coverage --html-report

# Spezifische Tests ausführen
python run_tests.py --test-path tests/test_app.py
```

### Manuelle Tests

1. Öffnen Sie die Anwendung im Browser unter http://localhost:5000
2. Melden Sie sich mit folgenden Testdaten an (wenn Sie `create_test_data.py` ausgeführt haben):
   - Admin: admin / admin123
   - Benutzer: benutzer / passwort123
3. Führen Sie eine Suche durch
4. Exportieren Sie Ergebnisse
5. Überprüfen Sie die Protokolle und Analysen

## Bekannte Probleme & Lösungen

### JSONB-Kompatibilitätsproblem

**Problem**: SQLite unterstützt den JSONB-Typ von PostgreSQL nicht.

**Lösung**: 
1. Führen Sie `python fix_database.py` aus, um den JSONB-Typ durch einen kompatiblen JSONType zu ersetzen.
2. Alternativ können Sie die `models.py` manuell bearbeiten, um eine JSONType-Klasse hinzuzufügen.

### Datenbank-Initialisierungsfehler

**Problem**: Fehler: "Working outside of application context".

**Lösung**: 
1. Stellen Sie sicher, dass Sie zuerst `python initialize_db.py` ausführen.
2. Überprüfen Sie die `.env`-Datei auf die richtige Datenbank-URL.
3. Erstellen Sie eine neue Datenbank mit `python initialize_db.py --force`.

### Fehlende Abhängigkeiten

**Problem**: ImportError oder ModuleNotFoundError.

**Lösung**:
1. Aktivieren Sie die virtuelle Umgebung: `.\venv\Scripts\Activate.ps1`
2. Installieren Sie alle Abhängigkeiten: `pip install -r project_requirements.txt`

## Diagnoseskripte

Medical Spytool enthält mehrere Skripte zur Diagnose und Fehlerbehebung:

### diagnostic.py

Führt eine umfassende Diagnose der Anwendung durch und identifiziert Probleme:

```powershell
python diagnostic.py
```

### create_test_data.py

Erstellt eine Testdatenbank mit Beispieldaten für Tests und Training:

```powershell
python create_test_data.py
```

Optionen:
- `--force` oder `-f`: Überschreibt eine bestehende Datenbank
- `--path` oder `-p`: Gibt einen alternativen Pfad für die Datenbank an

### create_test_database.py

Erstellt eine In-Memory-Testdatenbank für automatisierte Tests:

```powershell
python create_test_database.py
```

### Fix-Skripte

- `fix_database.py` - Behebt das JSONB-Kompatibilitätsproblem
- `scripts/check_indentation.py` - Überprüft Python-Dateien auf Einrückungsfehler

---

Bei weiteren Fragen oder Problemen erstellen Sie bitte ein Issue im GitHub-Repository oder kontaktieren Sie das Entwicklungsteam.
