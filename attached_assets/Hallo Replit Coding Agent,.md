Hallo Replit Coding Agent,

wir entwickeln die Flask-basierte Webanwendung "Medical Spytool" (Version 3.0), ein Werkzeug zur Suche und Analyse wissenschaftlicher medizinischer Publikationen. Die aktuelle Codebasis ist im beigefügten ZIP-Archiv "Medical-Spytool.zip" enthalten und wurde bereits einer ersten Analyse unterzogen. Ziel ist es, die Anwendung umfassend zu überprüfen, weiterzuentwickeln und für eine benutzerfreundliche Nutzung im Arbeitsalltag unserer Kollegen vorzubereiten. Dabei soll sie entweder einfach auf unserem Arbeitsserver (idealerweise via Docker) oder als leicht installierbares Programm bereitgestellt werden können. Langfristig streben wir eine Unabhängigkeit von der Replit-Entwicklungsumgebung an.

Bitte führe folgende Schritte detailliert durch und achte dabei auf höchste Benutzerfreundlichkeit, Robustheit und Wartbarkeit:

**1. Umfassende Code-Überprüfung und -Optimierung:**
   - Analysiere die gesamte Codebasis (Backend: Flask/Python; Frontend: HTML/CSS/JavaScript, Bootstrap, Chart.js) auf Konsistenz, Effizienz, Sicherheit und Lesbarkeit.
   - Stelle sicher, dass alle in der Dokumentation (README.md) und den Analyseberichten (`usability_evaluation.md`, `functionality_validation.md`) beschriebenen Funktionen (Multi-Datenbank-Suche, Personenverwaltung, erweiterte Filter, Ergebnisvisualisierung, Datenexport nach CSV/Excel, gespeicherte Suchen, Logging) voll funktionsfähig, fehlerfrei und performant sind.
   - Überprüfe und optimiere die Datenbankmodelle (`models.py`) und -interaktionen (SQLAlchemy mit PostgreSQL).
   - Stelle sicher, dass die API-Konnektoren (`connectors.py` für PubMed, DNB) robust sind und Fehler adäquat behandeln.
   - Refaktoriere Code bei Bedarf, um die Modularität und Wartbarkeit weiter zu verbessern. Halte dich dabei an die bestehende Projektstruktur und die in der `LOCAL_DEVELOPMENT.md` beschriebenen Konventionen.
   - Überprüfe die Skripte im Ordner `attached_assets`. Entscheide, welche davon relevant sind, integriere sie gegebenenfalls in die Testsuite, aktualisiere sie oder archiviere sie, falls sie veraltet sind.

**2. Verbesserung der Benutzerfreundlichkeit (Usability) und des Nutzererlebnisses (UX):**
   - **Navigation und Struktur:** Stelle sicher, dass die Navigation (definiert in `base.html` und den einzelnen Templates) durchgängig intuitiv, klar und konsistent ist. Alle Hauptbereiche (Startseite, Suche, Ergebnisse, Analyse, Personen, Einstellungen, Protokoll) müssen leicht erreichbar sein.
   - **Suchfunktionen:** Optimiere die Benutzerführung in allen Suchmodi (`search.html`), insbesondere bei der "Erweiterten Datenbanksuche". Stelle sicher, dass alle Filter und Optionen verständlich sind und korrekt angewendet werden.
   - **Einstellungen:** Gewährleiste, dass alle Einstellungsoptionen (`settings.html`) klar beschriftet sind, ihre Auswirkungen verständlich sind und korrekt gespeichert und angewendet werden.
   - **Feedback an den Benutzer:** Implementiere klare und verständliche Flash-Nachrichten für Erfolgs-, Warn- und Fehlermeldungen. Sorge für visuelle Ladeindikatoren bei länger dauernden Operationen (z.B. komplexe Suchen, Datenexport).
   - **Fehlerbehandlung im UI:** Stelle sicher, dass Fehlermeldungen für den Endbenutzer stets informativ und handlungsorientiert sind.
   - **Integrierte Hilfe:** Erwäge die Implementierung von kontextsensitiven Tooltips oder einer kleinen Hilfesektion für komplexere Funktionen.
   - **Sprachkonsistenz:** Die Anwendung ist primär auf Deutsch. Stelle sicher, dass alle UI-Texte, Beschriftungen und Meldungen konsistent auf Deutsch sind.
   - **Barrierefreiheit (Accessibility):** Überprüfe und verbessere die Anwendung gemäß WCAG-Richtlinien (z.B. Farbkontraste, Tastaturbedienbarkeit, ARIA-Attribute).
   - **Responsivität:** Teste und optimiere die Darstellung und Bedienbarkeit auf verschiedenen Bildschirmgrößen (Desktop, Tablet, Mobil).

**3. Optimierung der Installation und Bereitstellung:**
   - **Docker-Setup:** Das vorhandene Docker-Setup (`Dockerfile`, `docker-compose.yml`) ist die bevorzugte Methode für die Bereitstellung auf einem Arbeitsserver. Überprüfe und optimiere es auf Stabilität, Sicherheit und Effizienz. Stelle sicher, dass die Datenbank (PostgreSQL) nahtlos integriert ist und Daten persistent gespeichert werden. Dokumentiere den Docker-Deployment-Prozess klar und verständlich.
   - **Klassische Installation:** Überprüfe und verbessere das Skript `setup_local_dev.py` für die Einrichtung einer lokalen Entwicklungsumgebung. Stelle sicher, dass alle Abhängigkeiten (`project_requirements.txt`, `uv.lock`) korrekt und aktuell sind. Die `README.md` und `LOCAL_DEVELOPMENT.md` enthalten bereits gute Anleitungen; stelle deren Vollständigkeit und Korrektheit sicher.
   - **Konfiguration:** Sorge dafür, dass alle notwendigen Konfigurationen (Datenbank-URL, API-Schlüssel, Session Secret, Pfade) über Umgebungsvariablen (`.env` Datei) und die `medicalspy_config.json` flexibel verwaltet werden können und dies gut dokumentiert ist.

**4. Vorbereitung für Unabhängigkeit von Replit:**
   - Stelle sicher, dass die Anwendung ohne spezifische Replit-Abhängigkeiten lauffähig ist.
   - Überprüfe die `replit.nix`-Datei und dokumentiere, wie die dort spezifizierten Systemabhängigkeiten (tk, tcl, qhull, etc.) in einer Standard-Linux-Umgebung (z.B. Ubuntu Server) für eine manuelle oder Docker-basierte Installation bereitgestellt werden können.
   - Alle Entwicklungswerkzeuge und Linting-Konfigurationen (`pyproject.toml`) sollten standardkonform sein und auch außerhalb von Replit funktionieren.

**5. Testen und Validierung:**
   - Erweitere die bestehende Testsuite (`run_tests.py`, `tests/`) um eine möglichst hohe Testabdeckung für alle Kernfunktionen und kritischen Pfade zu erreichen.
   - Führe umfassende manuelle Tests durch, um die Benutzerfreundlichkeit, Funktionalität und Stabilität in verschiedenen Szenarien zu validieren.

**Zusammenfassend:** Das Ziel ist eine ausgereifte, hochgradig benutzerfreundliche und robuste Version der Medical Spytool Anwendung, die einfach auf einem Arbeitsserver via Docker oder als gut dokumentiertes Python-Projekt installiert werden kann und für die zukünftige Wartung und Weiterentwicklung optimal vorbereitet ist.

Bitte dokumentiere alle vorgenommenen Änderungen, getroffenen Entscheidungen und wichtigen Konfigurationsdetails. Stelle am Ende eine aktualisierte Version des gesamten Projekts bereit.
