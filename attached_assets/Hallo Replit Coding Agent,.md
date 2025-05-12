Hallo Replit Coding Agent,

wir entwickeln die Flask-basierte Webanwendung "Medical Spytool" (aktuelle Version basiert auf dem Inhalt von `Medical-Spytool.zip`), ein Werkzeug zur Suche und Analyse wissenschaftlicher medizinischer Publikationen. Die Anwendung wurde bereits einer initialen Analyse unterzogen. Ziel ist es nun, ein **fertiges Minimum Viable Product (MVP)** zu erstellen, das robust, benutzerfreundlich und bereit für den Einsatz ist. Die Anwendung soll primär als Webanwendung auf unserem Arbeitsserver (idealerweise via Docker) laufen. Alternativ soll eine gut dokumentierte klassische Installation als Python-Projekt möglich sein. Ein wichtiges Ziel ist die Unabhängigkeit von der Replit-Entwicklungsumgebung.

Bitte führe folgende Schritte detailliert durch und lege höchsten Wert auf Codequalität, Benutzerfreundlichkeit, Stabilität und Wartbarkeit:

**1. Umfassende Code-Überprüfung, -Optimierung und MVP-Fertigstellung:**
   - Analysiere die gesamte Codebasis (Backend: Flask/Python; Frontend: HTML/CSS/JavaScript, Bootstrap, Chart.js) auf Konsistenz, Effizienz, Sicherheit (insb. Abhängigkeiten und Input-Validierung) und Lesbarkeit. Schließe alle bekannten Lücken und vervollständige unfertige Funktionen, um einen MVP-Status zu erreichen.
   - Stelle sicher, dass alle Kernfunktionen, wie in der `README.md` beschrieben (Multi-Datenbank-Suche, Personenverwaltung, erweiterte Filter, Ergebnisvisualisierung, Datenexport nach CSV/Excel, gespeicherte Suchen, Logging), voll funktionsfähig, fehlerfrei und performant sind. Beziehe dich auch auf die Hinweise in den Dateien `attached_assets/Bewertung der Benutzerfreundlichkeit und des Nutzererlebnisses.md` und `attached_assets/Validierung der Funktionalität, Einstellungen und Navigation.md` (oder deren impliziten Anforderungen, falls die Dateien nicht existieren) für die Fertigstellung.
   - Überprüfe und optimiere die Datenbankmodelle (`backend/models.py`) und -interaktionen (SQLAlchemy mit PostgreSQL). Stelle die Datenintegrität und effiziente Abfragen sicher.
   - Stelle sicher, dass die API-Konnektoren (`backend/connectors.py` für PubMed, DNB etc.) robust sind, Fehler adäquat behandeln (z.B. API-Limits, Netzwerkfehler) und aktuelle API-Endpunkte verwenden.
   - Refaktoriere Code bei Bedarf, um die Modularität und Wartbarkeit zu verbessern. Halte dich dabei an die bestehende Projektstruktur und die in `LOCAL_DEVELOPMENT.md` beschriebenen Konventionen. Entferne nicht mehr benötigten oder veralteten Code.
   - Überprüfe die Skripte im Ordner `attached_assets`. Entscheide, welche davon für das MVP relevant sind (z.B. Datenmigrationsskripte, nützliche Utilities), integriere sie gegebenenfalls in die Anwendung oder die Testsuite, aktualisiere sie oder archiviere sie, falls sie veraltet oder nicht mehr benötigt werden.

**2. Verbesserung der Benutzerfreundlichkeit (Usability) und des Nutzererlebnisses (UX) für das MVP:**
   - **Navigation und Struktur:** Stelle sicher, dass die Navigation (definiert in `backend/templates/base.html` und den einzelnen Templates) durchgängig intuitiv, klar und konsistent ist. Alle für das MVP relevanten Hauptbereiche (Startseite, Suche, Ergebnisse, Analyse, Personen, Einstellungen, Protokoll) müssen leicht erreichbar und voll funktionsfähig sein.
   - **Suchfunktionen:** Optimiere die Benutzerführung in allen Suchmodi (`backend/templates/search.html`), insbesondere bei der "Erweiterten Datenbanksuche". Stelle sicher, dass alle Filter und Optionen verständlich sind, korrekt angewendet werden und zu sinnvollen Ergebnissen führen.
   - **Einstellungen:** Gewährleiste, dass alle Einstellungsoptionen (`backend/templates/settings.html`) klar beschriftet sind, ihre Auswirkungen verständlich sind und korrekt gespeichert und angewendet werden. Reduziere auf die für ein MVP notwendigen Einstellungen.
   - **Feedback an den Benutzer:** Implementiere klare und verständliche Flash-Nachrichten für Erfolgs-, Warn- und Fehlermeldungen. Sorge für visuelle Ladeindikatoren bei länger dauernden Operationen (z.B. komplexe Suchen, Datenexport).
   - **Fehlerbehandlung im UI:** Stelle sicher, dass Fehlermeldungen für den Endbenutzer stets informativ und handlungsorientiert sind und die Anwendung nicht in einen instabilen Zustand gerät.
   - **Sprachkonsistenz:** Die Anwendung ist primär auf Deutsch. Stelle sicher, dass alle UI-Texte, Beschriftungen und Meldungen konsistent auf Deutsch und fehlerfrei sind.
   - **Responsivität:** Teste und optimiere die Darstellung und Bedienbarkeit auf gängigen Desktop-Browsern. Mobile Optimierung ist für das MVP sekundär, sollte aber nicht komplett vernachlässigt werden.

**3. Optimierung der Installation und Bereitstellung für das MVP:**
   - **Docker-Setup:** Das vorhandene Docker-Setup (`Dockerfile`, `docker-compose.yml`) ist die bevorzugte Methode für die Bereitstellung auf einem Arbeitsserver. Überprüfe und optimiere es auf Stabilität, Sicherheit und Effizienz für einen MVP-Betrieb. Stelle sicher, dass die Datenbank (PostgreSQL) nahtlos integriert ist und Daten persistent gespeichert werden. Dokumentiere den Docker-Deployment-Prozess klar und verständlich für einen Systemadministrator.
   - **Klassische Installation:** Überprüfe und verbessere das Skript `setup_local_dev.py` für die Einrichtung einer lokalen Entwicklungsumgebung. Stelle sicher, dass alle Abhängigkeiten (`project_requirements.txt`, `uv.lock`) korrekt, aktuell und auf das für das MVP Notwendige reduziert sind. Die `README.md` und `LOCAL_DEVELOPMENT.md` enthalten bereits gute Anleitungen; stelle deren Vollständigkeit, Korrektheit und Ausrichtung auf das MVP sicher.
   - **Konfiguration:** Sorge dafür, dass alle notwendigen Konfigurationen (Datenbank-URL, API-Schlüssel, Session Secret, Pfade) über Umgebungsvariablen (`.env` Datei) flexibel verwaltet werden können und dies gut dokumentiert ist. Standardwerte sollten für einen schnellen Start sinnvoll vorkonfiguriert sein.

**4. Vorbereitung für Unabhängigkeit von Replit:**
   - Stelle sicher, dass die Anwendung ohne spezifische Replit-Abhängigkeiten lauffähig ist. Entferne alle Replit-spezifischen Konfigurationen, die nicht für eine Standardbereitstellung relevant sind.
   - Überprüfe die `replit.nix`-Datei und dokumentiere, wie die dort spezifizierten Systemabhängigkeiten (tk, tcl, qhull, etc.) in einer Standard-Linux-Umgebung (z.B. Ubuntu Server) für eine manuelle oder Docker-basierte Installation bereitgestellt werden können. Minimiere diese Abhängigkeiten, wenn möglich.
   - Alle Entwicklungswerkzeuge und Linting-Konfigurationen (`pyproject.toml`) sollten standardkonform sein und auch außerhalb von Replit funktionieren.

**5. Testen und Validierung des MVP:**
   - Erweitere die bestehende Testsuite (`run_tests.py`, `tests/`) um eine solide Testabdeckung für alle Kernfunktionen und kritischen Pfade des MVP zu erreichen (Unit- und Integrationstests).
   - Führe umfassende manuelle Tests durch, um die Benutzerfreundlichkeit, Funktionalität und Stabilität des MVP in verschiedenen Szenarien zu validieren.

**Zusammenfassend:** Das Ziel ist eine stabile, benutzerfreundliche und funktionale MVP-Version der Medical Spytool Anwendung, die einfach auf einem Arbeitsserver via Docker oder als gut dokumentiertes Python-Projekt installiert werden kann und für die zukünftige Wartung und Weiterentwicklung optimal vorbereitet ist.

Bitte dokumentiere alle vorgenommenen Änderungen, getroffenen Entscheidungen und wichtigen Konfigurationsdetails. Stelle am Ende eine aktualisierte Version des gesamten Projekts als ZIP-Archiv bereit, die alle genannten Punkte berücksichtigt und als MVP lauffähig ist.
