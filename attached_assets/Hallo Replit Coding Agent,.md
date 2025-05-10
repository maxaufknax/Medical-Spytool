Hallo Replit Coding Agent,

Ziel ist es, die bestehende Flask-Anwendung "Medical Spytool" zu einem robusten, wartbaren und deploybaren Minimum Viable Product (MVP) weiterzuentwickeln. Die Anwendung soll vollständig von der Replit-Umgebung entkoppelt und für die lokale Entwicklung sowie für die Bereitstellung auf einem Standard-Arbeitsserver vorbereitet werden.

**Aktueller Status der Anwendung:**
Die Anwendung ist in Flask implementiert und bietet Funktionen zur Suche in wissenschaftlichen Datenbanken (PubMed, DNB), Personenverwaltung, Ergebnisvisualisierung und Datenexport. Der Tech-Stack umfasst Flask, SQLAlchemy für die Datenbankinteraktion (PostgreSQL, wie aus `pyproject.toml` und `replit.nix` ersichtlich), Pandas für Datenmanipulation, Matplotlib für Diagramme (serverseitig), Bootstrap 5 für das UI und Vanilla JavaScript sowie Chart.js für clientseitige Interaktivität.

**Detaillierte Aufgaben zur Weiterentwicklung und Optimierung:**

**1. Fehlerbehebung, Stabilität und Logging:**
   - **Generelle Fehlerbehandlung:** Implementieren Sie eine durchgängige und robuste Fehlerbehandlung in allen Modulen, insbesondere in den API-Konnektoren (`backend/connectors.py`), bei Datenbankoperationen (`backend/models.py`, `backend/app.py`) und bei der Verarbeitung von Benutzereingaben.
   - **Logging verbessern:** Erweitern und standardisieren Sie das Logging (`backend/utils.py`, `backend/app.py`). Stellen Sie sicher, dass kritische Fehler, Warnungen und wichtige Informationsmeldungen aussagekräftig protokolliert werden, um Debugging und Monitoring zu erleichtern. Die aktuelle Logging-Implementierung in `utils.py` speichert Logs im Speicher und optional in der Datenbank; stellen Sie sicher, dass dies performant und zuverlässig funktioniert, insbesondere im Kontext einer produktiven Umgebung.

**2. Codequalität und Wartbarkeit:**
   - **Konsistente Benennung:** Vereinheitlichen Sie Namenskonventionen im gesamten Code. Aktuell gibt es eine Mischung aus deutschen und englischen Bezeichnern (z.B. in `app.py` Routen, Template-Namen, Modellattributen). Standardisieren Sie dies vorzugsweise auf Englisch.
   - **Refactoring:** Überarbeiten Sie komplexe Funktionen und Module, um die Lesbarkeit, Modularität und Testbarkeit zu verbessern. Identifizieren Sie Bereiche, die von einer Aufteilung in kleinere, spezialisierte Funktionen profitieren könnten.
   - **Kommentare und Docstrings:** Ergänzen Sie den Code flächendeckend mit aussagekräftigen Kommentaren und Docstrings, um die Funktionsweise und Verwendung der einzelnen Komponenten zu dokumentieren.
   - **Unit Tests:** Führen Sie grundlegende Unit-Tests für kritische Backend-Komponenten ein (z.B. für API-Konnektoren, Suchlogik, Datenbankmodelle).

**3. Abhängigkeitsmanagement und Entkopplung von Replit:**
   - **`pyproject.toml` und `requirements.txt`:** Bereinigen Sie die `pyproject.toml`. Erstellen Sie eine saubere und minimale `requirements.txt`, die alle notwendigen Abhängigkeiten für eine Standard-Python/Flask-Umgebung enthält. Entfernen Sie alle Replit-spezifischen Abhängigkeiten oder Konfigurationen.
   - **`replit.nix` entfernen:** Stellen Sie sicher, dass die Anwendung ohne die `replit.nix`-Datei in einer Standard-Python-Umgebung (z.B. mit `venv`) lauffähig ist. Die in `replit.nix` gelisteten Systempakete (tk, tcl, qhull, postgresql etc.) deuten auf spezifische Anforderungen hin. Klären Sie, welche davon für die Kernfunktionalität (insbesondere Matplotlib, PostgreSQL-Client) wirklich benötigt werden und dokumentieren Sie deren Installation oder finden Sie Alternativen, die einfacher über pip zu installieren sind.
   - **Abhängigkeitskonflikte:** Überprüfen Sie die Abhängigkeiten auf mögliche Konflikte oder veraltete Versionen und aktualisieren Sie diese gegebenenfalls.

**4. Datenbank und Datenmanagement (`backend/models.py`, `backend/app.py`):**
   - **Datenbankmodelle optimieren:** Überprüfen Sie die SQLAlchemy-Modelle (`SearchQuery`, `SearchResult`, `Person`, `Setting`, `LogEntry`) auf Effizienz, korrekte Beziehungen und Datentypen (insbesondere `JSONB` für `result_data`).
   - **Datenvalidierung:** Implementieren Sie eine robuste Validierung für alle Benutzereingaben und Daten, die in die Datenbank geschrieben werden.
   - **Settings-Management:** Das aktuelle Settings-Management ist redundant. `backend/config.py` lädt Einstellungen aus einer `medicalspy_config.json`, während `backend/models.py` ein `Setting`-Modell für die Datenbank definiert und in `app.py` verwendet wird. Konsolidieren Sie dies zu einer einzigen, klaren Strategie. Für eine deploybare Anwendung ist die Konfiguration über Umgebungsvariablen (ggf. mit Fallback auf eine Konfigurationsdatei) zu bevorzugen.
   - **Datenbank-URL:** Die Datenbank-URL wird in `app.py` über `os.environ.get('DATABASE_URL')` bezogen. Stellen Sie sicher, dass dies die bevorzugte Methode bleibt und gut dokumentiert ist.

**5. API-Konnektoren (`backend/connectors.py`):**
   - **Standardisierung:** Vereinheitlichen Sie die Fehlerbehandlung, Retry-Mechanismen und das Logging für alle API-Konnektoren (DNB, PubMed).
   - **API-Keys:** Stellen Sie sicher, dass API-Keys (z.B. `pubmed_api_key`) sicher über Umgebungsvariablen verwaltet werden und nicht fest im Code oder in leicht zugänglichen Konfigurationsdateien stehen. Die aktuelle Lösung in `config.py` (Laden aus JSON) ist ein Schritt, aber Umgebungsvariablen sind für Deployments besser.
   - **Logik überprüfen:** Überprüfen Sie die Logik der DNB- und PubMed-Konnektoren auf Vollständigkeit, Korrektheit und Einhaltung der jeweiligen API-Richtlinien (z.B. Rate Limiting, korrekte Query-Konstruktion).

**6. Suchfunktionalität (`backend/search.py`, `backend/app.py` Routen):**
   - **Logik verfeinern:** Überarbeiten Sie die Suchlogik in `search_database` und den zugehörigen Routen in `app.py` hinsichtlich Klarheit, Effizienz und Fehleranfälligkeit.
   - **Parameterbehandlung:** Verbessern Sie die Handhabung verschiedener Suchmodi (`simple`, `database`, `person`, `advanced`) und der zugehörigen Parameter.
   - **Ergebnis-Parsing und -Darstellung:** Optimieren Sie das Parsen der Suchergebnisse und deren Aufbereitung für die Darstellung im Frontend.

**7. Benutzeroberfläche (UI) und User Experience (UX) (Templates, CSS, JS):**
   - **Responsiveness und Intuitivität:** Verbessern Sie die Responsivität und Benutzerfreundlichkeit der Weboberfläche. Überprüfen Sie alle HTML-Templates (`templates/*.html`), CSS-Dateien (`static/css/custom.css`) und JavaScript-Dateien (`static/js/*.js`) auf Optimierungspotenzial.
   - **Interaktionen und Feedback:** Stellen Sie sicher, dass alle Frontend-Interaktionen reibungslos funktionieren und dem Benutzer klares Feedback geben (z.B. bei Ladevorgängen, Fehlern, erfolgreichen Aktionen).
   - **JavaScript-Optimierung:** Überprüfen Sie die JavaScript-Dateien (`charts.js`, `results.js`, `search.js`, `tour.js`) auf Effizienz, Fehlerfreiheit und moderne Praktiken.

**8. MVP-Feature-Vervollständigung und -Verfeinerung:**
   - **`attached_assets` sichten:** Gehen Sie die Dateien im Verzeichnis `attached_assets` systematisch durch. Dieses Verzeichnis enthält diverse Skripte (z.B. `dnb_skript_4.0.py`, `pubmed_skript_4.2.py`, `medical_spytool_1.0.py`, `medical_spytool_2.0.py`), Logdateien, Textnotizen und ZIP-Archive (`medical spytool (flask v2).zip`, `medical spytool (flask).zip`).
     - Konsolidieren Sie Code aus älteren/alternativen Skriptversionen in die Hauptcodebasis, falls dieser Verbesserungen oder nützliche Funktionen enthält.
     - Werten Sie die Textnotizen und Logs aus, um mögliche Fehlerquellen oder gewünschte, aber noch nicht implementierte Features zu identifizieren.
     - Untersuchen Sie die ZIP-Archive auf relevanten Kontext oder Code.
   - **Kernfeatures:** Stellen Sie sicher, dass alle im `README.md` beschriebenen Kernfeatures (Multi-DB-Suche, erweiterte Suchoptionen, Personenverwaltung, Ergebnisvisualisierung, Datenexport, gespeicherte Suchen, Logging) robust implementiert sind. Die "Personenverwaltung" scheint ein zentrales Element zu sein; gewährleisten Sie dessen fehlerfreie Funktion im Backend und Frontend.

**9. Vorbereitung für Deployment und lokale Entwicklung:**
   - **Lokale Ausführbarkeit:** Stellen Sie sicher, dass die Anwendung einfach lokal mit einem Standardbefehl (z.B. `python run.py` oder `flask run` nach Setzen der `FLASK_APP` Umgebungsvariable) innerhalb eines Python Virtual Environments gestartet werden kann. Der `main.py` und `run.py` deuten bereits auf eine solche Struktur hin.
   - **Server-Deployment:** Bereiten Sie die Anwendung für den Einsatz auf einem Standardserver mit Gunicorn vor (wie in `main.py` angedeutet und in den Logs aus `attached_assets` ersichtlich). Die App muss auf `0.0.0.0` lauschen.
   - **Setup-Anleitung:** Erstellen Sie eine klare Anleitung (z.B. in der `README.md`) für das Setup der Entwicklungsumgebung, die Installation von Abhängigkeiten und das Starten der Anwendung.
   - **(Optional) Packaging:** Erwägen Sie die Erstellung eines `Dockerfile` für eine einfachere Containerisierung und Bereitstellung, falls dies im Rahmen des MVP sinnvoll ist.

**Allgemeine Anweisungen:**
- Priorisieren Sie Änderungen, die zu einem stabilen und funktionalen MVP führen.
- Arbeiten Sie inkrementell und testen Sie Änderungen häufig.
- Dokumentieren Sie vorgenommene Änderungen und wichtige Entscheidungen im Code oder in Commit-Nachrichten.
- Der Fokus liegt darauf, die Anwendung unabhängig von Replit lauffähig und wartbar zu machen.

**Liefergegenstände:**
- Die aktualisierte und refaktorisierte Codebasis der Medical Spytool Anwendung.
- Eine saubere `requirements.txt` Datei.
- Eine aktualisierte `README.md` mit klaren Anweisungen für Setup, Konfiguration (insbesondere Umgebungsvariablen für Datenbank und API-Keys) und lokale Ausführung.
- (Optional) Ein `Dockerfile` für die Containerisierung.

Vielen Dank für Ihre Unterstützung bei der Weiterentwicklung des Medical Spytools!
