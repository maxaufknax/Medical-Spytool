# Medical Spytool

Ein wissenschaftliches Publikations-Suchwerkzeug für medizinische Forschung.

## Systemanforderungen

- Windows 10/11 oder Linux/macOS
- Python 3.7 oder höher
- SQLite 3.x

## Installation

### Schritt 1: Python installieren

Falls noch nicht vorhanden, laden Sie Python von [python.org](https://www.python.org/downloads/) herunter und installieren Sie es. **Wichtig:** Aktivieren Sie während der Installation die Option "Add Python to PATH".

### Schritt 2: Medical Spytool herunterladen

Laden Sie das Medical Spytool-Paket herunter und entpacken Sie es in einen Ordner Ihrer Wahl.

### Schritt 3: Abhängigkeiten installieren

Öffnen Sie eine Kommandozeile (cmd oder PowerShell unter Windows, Terminal unter Linux/macOS) und navigieren Sie zum Medical Spytool-Verzeichnis:

```
cd Pfad\zum\Medical-Spytool-2
```

Installieren Sie die erforderlichen Pakete:

```
pip install -r project_requirements.txt
```

### Schritt 4: Virtuelle Umgebung einrichten (optional, aber empfohlen)

Erstellen Sie eine virtuelle Python-Umgebung:

```
python -m venv venv
```

Aktivieren Sie die virtuelle Umgebung:

- Windows: `venv\Scripts\activate`
- Linux/macOS: `source venv/bin/activate`

Installieren Sie die Abhängigkeiten in der virtuellen Umgebung:

```
pip install -r project_requirements.txt
```

## Schnellstart

### Option 1: Mit dem automatischen Startskript

Verwenden Sie das mitgelieferte Startskript, um die Anwendung mit einem Klick zu starten:

- Windows: Doppelklick auf `activate_and_run.bat`
- Linux/macOS: Führen Sie `./start.sh` im Terminal aus

### Option 2: Manuelle Ausführung

1. Öffnen Sie eine Kommandozeile und navigieren Sie zum Medical Spytool-Verzeichnis
2. Aktivieren Sie die virtuelle Umgebung (falls verwendet)
3. Führen Sie den folgenden Befehl aus:

```
python run.py
```

Die Anwendung ist dann unter http://localhost:5000 in Ihrem Webbrowser verfügbar.

## Fehlerbehebung

Wenn Probleme auftreten, führen Sie das Diagnoseskript aus:

```
python diagnostic_improved.py
```

Das Skript identifiziert häufige Probleme und gibt Hinweise zur Behebung.

### Bekannte Probleme und Lösungen

1. **Problem:** Datenbank kann nicht erstellt werden
   **Lösung:** Führen Sie `python create_full_db.py` aus, um die Datenbank manuell zu erstellen

2. **Problem:** Unicode-Zeichen werden falsch angezeigt
   **Lösung:** Stellen Sie sicher, dass Ihr Terminal UTF-8-Unterstützung aktiviert hat. Unter Windows verwenden Sie `chcp 65001` in der Kommandozeile.

3. **Problem:** Fehlende Abhängigkeiten
   **Lösung:** Führen Sie `pip install -r project_requirements.txt` aus, um alle erforderlichen Pakete zu installieren

## Verwendung

### Login

Die Standardanmeldedaten sind:
- Benutzername: `admin`
- Passwort: `admin`

### Suche

1. Geben Sie Ihre Suchbegriffe ein
2. Wählen Sie die gewünschte Datenbank (PubMed, DNB, etc.)
3. Legen Sie Filter fest (optional)
4. Klicken Sie auf "Suchen"

### Export

Suchergebnisse können in verschiedenen Formaten exportiert werden:
- CSV
- BibTeX
- EndNote
- JSON

## Kontakt

Bei Fragen oder Problemen wenden Sie sich an:
- E-Mail: support@medicalspytool.example.com
- GitHub Issues: https://github.com/example/medical-spytool/issues
