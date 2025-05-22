# Einrichtung der Medical-Spytool-Anwendung in Visual Studio Code

Diese Anleitung beschreibt die Schritte, um die entpackte Anwendung in Visual Studio Code einzurichten und auszuführen.

---

## Voraussetzungen
Stelle sicher, dass die folgenden Tools und Software auf deinem Computer installiert sind:
1. **Python** (Version 3.8 oder höher)
   - [Python herunterladen](https://www.python.org/downloads/)
   - Stelle sicher, dass `pip` (Python Package Installer) installiert ist.
   - Füge Python zur PATH-Umgebungsvariable hinzu.
2. **Visual Studio Code**
   - [VS Code herunterladen](https://code.visualstudio.com/)
3. **Git** (optional, falls du später mit einem Repository arbeiten möchtest)
   - [Git herunterladen](https://git-scm.com/)

---

## Einrichtungsschritte

### 1. Projekt in Visual Studio Code öffnen
1. Entpacke die `.ZIP`-Datei in einen Ordner deiner Wahl.
2. Öffne Visual Studio Code.
3. Wähle den entpackten Projektordner aus:
   - **Datei → Ordner öffnen...** und navigiere zum Projektordner.

---

### 2. Virtuelle Umgebung erstellen
1. Öffne das Terminal in Visual Studio Code (`Strg + ``).
2. Navigiere in das Projektverzeichnis (falls nicht bereits dort):
   ```powershell
   cd <Pfad-zum-Projektordner>
   ```
3. Erstelle eine virtuelle Umgebung:
   ```powershell
   python -m venv venv
   ```
4. Aktiviere die virtuelle Umgebung:
   ```powershell
   .\venv\Scripts\activate
   ```

---

### 3. Abhängigkeiten installieren
1. Stelle sicher, dass die Datei `requirements.txt` im Projektordner vorhanden ist.
2. Installiere die Abhängigkeiten:
   ```powershell
   pip install -r requirements.txt
   ```

---

### 4. Datenbank zurücksetzen und initialisieren
1. In Visual Studio Code ist eine vordefinierte Aufgabe verfügbar, um die Datenbank zurückzusetzen und neu zu erstellen.
2. Führe die Aufgabe aus:
   - Öffne die **Befehlspalette** (`Strg + Umschalt + P`).
   - Suche nach **"Tasks: Run Task"** und wähle sie aus.
   - Wähle die Aufgabe **"Database: Reset and Initialize"** aus.
3. Alternativ kannst du den folgenden Befehl im Terminal ausführen:
   ```powershell
   python -c "from backend.models import db; from backend.app import app; with app.app_context(): db.drop_all(); db.create_all()"
   ```

---

### 5. Anwendung starten
1. Starte die Anwendung über das Hauptskript:
   ```powershell
   python start_app.py
   ```
2. Öffne die Anwendung im Browser:
   - Standardmäßig läuft die Anwendung unter `http://127.0.0.1:5000`.

---

### 6. Fehlerbehebung
Falls Probleme auftreten:
1. **Fehlende Abhängigkeiten**:
   - Stelle sicher, dass alle Pakete aus `requirements.txt` installiert wurden.
2. **Datenbankprobleme**:
   - Überprüfe die Datenbankkonfiguration in der Datei `config.py`.
3. **Port-Konflikte**:
   - Ändere den Port in der Anwendungskonfiguration (z. B. `app.run(port=5001)`).

---

### 7. Optional: Git-Repository einrichten
Falls du das Projekt mit einem GitHub-Repository verknüpfen möchtest:
1. Initialisiere ein Git-Repository:
   ```powershell
   git init
   ```
2. Füge das Remote-Repository hinzu:
   ```powershell
   git remote add origin https://github.com/<dein-benutzername>/<repository-name>.git
   ```
3. Führe die Änderungen aus:
   ```powershell
   git add .
   git commit -m "Initial commit"
   git push -u origin main
   ```

---

## Hinweise
- Stelle sicher, dass du die virtuelle Umgebung jedes Mal aktivierst, bevor du an der Anwendung arbeitest.
- Aktualisiere die Datei `requirements.txt`, wenn neue Abhängigkeiten hinzugefügt werden:
  ```powershell
  pip freeze > requirements.txt
  ```

---

Viel Erfolg bei der Einrichtung und Weiterentwicklung der Anwendung! 😊
