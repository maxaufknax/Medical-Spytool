# Medical Spytool

## Inhaltsverzeichnis
1.  [Projektbeschreibung](#projektbeschreibung)
2.  [Funktionsübersicht](#funktionsübersicht)
3.  [Installation (Windows)](#installation-windows)
    *   [Option 1: Aus dem Quellcode](#option-1-aus-dem-quellcode)
    *   [Option 2: Vorkompilierte Windows-Executable](#option-2-vorkompilierte-windows-executable)
4.  [Konfiguration](#konfiguration)
    *   [API-Schlüssel](#api-schlüssel)
    *   [Speicherpfade & Exporteinstellungen](#speicherpfade--exporteinstellungen)
    *   [Allgemeine Sucheinstellungen](#allgemeine-sucheinstellungen)
5.  [Benutzerhandbuch](#benutzerhandbuch)
    *   [Erste Schritte](#erste-schritte)
    *   [Suche durchführen](#suche-durchführen)
    *   [Personen verwalten](#personen-verwalten)
    *   [Suchprofile nutzen](#suchprofile-nutzen)
    *   [Ergebnisse anzeigen und filtern](#ergebnisse-anzeigen-und-filtern)
    *   [Datenanalyse](#datenanalyse)
    *   [Datenexport](#datenexport)
    *   [Logs und Diagnose](#logs-und-diagnose)
6.  [Lizenz](#lizenz)

## Projektbeschreibung

Medical Spytool ist eine webbasierte Anwendung, die als modulares und interaktives System für die umfassende Suche und Analyse von wissenschaftlichen Publikationen und Projekten dient. Es ermöglicht Benutzern, gleichzeitig mehrere medizinische und wissenschaftliche Datenbanken abzufragen, Suchergebnisse zu verwalten, zu visualisieren und zu exportieren. Die Verwaltung von Personenprofilen und Suchprofilen erleichtert wiederkehrende und komplexe Recherchen.

Das Tool richtet sich an Forscher, Mediziner, Studenten und alle, die einen schnellen und integrierten Zugriff auf wissenschaftliche Literatur benötigen.

## Funktionsübersicht

*   **Integrierte Suche**: Parallele oder spezifische Suche in Datenbanken wie PubMed, Deutsche Nationalbibliothek (DNB), Scopus, Web of Science (WoS) und GEPRIS.
*   **Suchmodi**:
    *   **Einfache Suche**: Schnelle Suche mit einem Suchbegriff über alle konfigurierten Datenbanken.
    *   **Spezifische Datenbanksuche**: Detaillierte Suche in einer einzelnen Datenbank mit erweiterten Filteroptionen (Suchfelder, Publikationstyp, Sprache, Datum, Personen).
    *   **Personenbezogene Suche**: Suche basierend auf vordefinierten Personenprofilen.
*   **Personenverwaltung**: Anlegen und Verwalten von Personenprofilen (z.B. Autoren, Forscher) mit spezifischen Suchbegriffen und zusätzlichen Filterkriterien.
*   **Suchprofile**: Speichern und Laden von komplexen Suchkonfigurationen für wiederkehrende Recherchen.
*   **Ergebnisdarstellung**: Übersichtliche Tabellenansicht der Suchergebnisse mit Optionen zur Spaltenauswahl und Detailansicht für jede Publikation.
*   **Client-seitige Filterung**: Erweiterte Filterung der angezeigten Ergebnisse direkt im Browser (Text, Jahr, Datenbank, Publikationstyp, Autor).
*   **Datenanalyse**: Visualisierung von Publikationstrends (z.B. nach Jahr, Datenbank, Person) und Anzeige von Basisstatistiken sowie meistzitierten Publikationen.
*   **Datenexport**: Exportieren von Suchergebnissen in Excel (.xlsx) oder CSV (.csv) Format mit anpassbaren Spalten und Exportoptionen.
*   **API-Schlüsselverwaltung**: Zentrale Konfiguration und Validierung von API-Schlüsseln für die angebundenen Datenbanken.
*   **Dynamische Benutzeroberfläche**: Interaktive Elemente wie Ladeindikatoren, Statusmeldungen und dynamisch aktualisierte Formularfelder.
*   **Logging und Diagnose**: Umfangreiche Logging-Funktionen und Systeminformationen zur Fehleranalyse und Diagnose.

## Installation (Windows)

Es gibt zwei Hauptmethoden, um Medical Spytool unter Windows zu installieren und auszuführen.

### Option 1: Aus dem Quellcode

Diese Methode erfordert Python und Git auf Ihrem System.

**Voraussetzungen:**
*   Python 3.8 oder höher (Download: [python.org](https://www.python.org/downloads/))
    *   Stellen Sie sicher, dass Python während der Installation zum Windows PATH hinzugefügt wird.
*   Git (Download: [git-scm.com](https://git-scm.com/download/win))

**Schritte:**

1.  **Repository klonen:**
    Öffnen Sie eine Kommandozeile (CMD) oder PowerShell und führen Sie folgenden Befehl aus, um das Repository zu klonen:
    ```bash
    git clone <URL_des_Git_Repositorys>
    cd medical-spytool
    ```
    (Ersetzen Sie `<URL_des_Git_Repositorys>` mit der tatsächlichen URL und `medical-spytool` mit dem Verzeichnisnamen, falls abweichend.)

2.  **Python-Umgebung erstellen (empfohlen):**
    Erstellen Sie eine virtuelle Umgebung, um Abhängigkeiten isoliert zu halten:
    ```bash
    python -m venv .venv
    ```
    Aktivieren Sie die virtuelle Umgebung:
    ```bash
    .venv\Scripts\activate
    ```
    Ihre Kommandozeilen-Prompt sollte sich ändern und `(.venv)` anzeigen.

3.  **Abhängigkeiten installieren:**
    Installieren Sie die benötigten Python-Pakete mit pip und der `requirements.txt` Datei:
    ```bash
    pip install -r requirements.txt
    ```
    Dies kann einige Minuten dauern, da alle Bibliotheken heruntergeladen und installiert werden.

4.  **Anwendung starten:**
    Nachdem alle Abhängigkeiten installiert sind, starten Sie die Flask-Anwendung:
    ```bash
    python main.py
    ```
    Die Anwendung sollte nun gestartet werden. In der Konsole sehen Sie eine Ausgabe ähnlich wie:
    `* Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)`
    Öffnen Sie Ihren Webbrowser und navigieren Sie zu `http://127.0.0.1:5000/`. Die Anwendung sollte automatisch im Browser geöffnet werden, wenn sie im Entwicklungsmodus gestartet wird.

5.  **Anwendung beenden:**
    Drücken Sie `CTRL+C` in der Kommandozeile, in der die Anwendung läuft.

### Option 2: Vorkompilierte Windows-Executable

Wenn eine vorkompilierte Version (`.exe`) verfügbar ist:

1.  **Executable herunterladen:**
    Laden Sie die `medical_spytool.exe` (oder ähnlich benannte Datei) aus dem Release-Bereich des Projekts oder von der bereitgestellten Quelle herunter.

2.  **Datei speichern:**
    Speichern Sie die `.exe`-Datei in einem beliebigen Ordner auf Ihrem Computer (z.B. `C:\MedicalSpytool\`).

3.  **Anwendung starten:**
    Doppelklicken Sie auf die `medical_spytool.exe`-Datei. Ein Konsolenfenster könnte sich kurz öffnen und die Anwendung wird gestartet. Ihr Standard-Webbrowser sollte sich automatisch öffnen und die Startseite der Anwendung anzeigen (`http://127.0.0.1:5000/` oder eine ähnliche Adresse).

4.  **Konfigurationsdateien und Ordner:**
    Beim ersten Start erstellt die Executable möglicherweise automatisch notwendige Konfigurationsdateien und Ordner (wie `medicalspytool_config.json`, `person_lists/`, `output/`, `search_profiles/`) im selben Verzeichnis, in dem die `.exe`-Datei liegt, oder in einem Benutzerverzeichnis (z.B. unter `AppData`). Überprüfen Sie die Dokumentation der Executable für genaue Speicherorte.

5.  **Anwendung beenden:**
    Schließen Sie das Konsolenfenster, das sich beim Start der `.exe`-Datei geöffnet hat (falls es geöffnet bleibt), oder schließen Sie den Webbrowser-Tab.

## Konfiguration

Nach der Installation (insbesondere bei der Ausführung aus dem Quellcode oder beim ersten Start der Executable) müssen einige Einstellungen vorgenommen werden, um die volle Funktionalität zu gewährleisten. Die Konfiguration erfolgt über die Weboberfläche unter dem Menüpunkt **Einstellungen**.

Die Konfigurationsdatei (`medicalspytool_config.json`) wird in der Regel automatisch im Hauptverzeichnis der Anwendung oder einem benutzerspezifischen Pfad erstellt und durch die Eingaben in der UI aktualisiert.

### API-Schlüssel

Für den Zugriff auf die meisten externen Datenbanken sind API-Schlüssel erforderlich.

1.  Navigieren Sie in der Anwendung zu **Einstellungen**.
2.  Sie finden Eingabefelder für die API-Schlüssel der unterstützten Datenbanken:
    *   **PubMed**: Optional, erhöht aber die Abfragelimits. Ein Link zur Beantragung ist vorhanden.
    *   **DNB**: API-Schlüssel (Zugangstoken) ist für die SRU-Schnittstelle erforderlich. Informationen zur Beantragung finden sich auf den DNB-Informationsseiten.
    *   **Scopus**: Erforderlich. Link zur Beantragung auf der Elsevier Developer-Seite.
    *   **Web of Science**: Erforderlich. Link zur Beantragung bei Clarivate.
    *   GEPRIS benötigt keinen API-Schlüssel.
3.  Geben Sie Ihre vorhandenen API-Schlüssel in die entsprechenden Felder ein.
4.  Die Anwendung validiert die Schlüssel automatisch beim Verlassen des Eingabefeldes und zeigt den Status (gültig/ungültig) an.
5.  Klicken Sie auf "Einstellungen speichern".

### Speicherpfade & Exporteinstellungen

Unter **Einstellungen** können Sie auch folgende Pfade und Optionen konfigurieren:

*   **Ausgabeverzeichnis für Exporte**: Der Server-Pfad, in dem exportierte Dateien (Excel, CSV) gespeichert werden (z.B. `./output`).
*   **Verzeichnis für Personenlisten**: Der Server-Pfad, in dem die `persons.json` Datei gespeichert wird (z.B. `./person_lists`).
*   **Eindeutige Dateinamen für Exporte**: Aktivieren/Deaktivieren der Zeitstempel-basierten eindeutigen Benennung von Exportdateien.
*   **Standard Spaltenauswahl für Export**: Wählen Sie die Spalten aus, die standardmäßig in Exportdateien enthalten sein sollen. Diese Auswahl kann auf der Exportseite für jeden einzelnen Export angepasst werden.

### Allgemeine Sucheinstellungen

*   **Standard-Datenbank für spezifische Suche**: Legt fest, welche Datenbank im Tab "Spezifische Datenbanksuche" vorausgewählt ist.

Klicken Sie nach allen Änderungen auf "Einstellungen speichern".

## Benutzerhandbuch

### Erste Schritte
*   **Startseite**: Bietet einen Überblick und Schnellzugriff auf Hauptfunktionen. Starten Sie eine "Einfache Suche" direkt von hier.
*   **Navigation**: Die obere Navigationsleiste ermöglicht den Zugriff auf alle Bereiche: Suche, Personen, Ergebnisse, Analyse, Export, Logs, Einstellungen und Info/Hilfe.

### Suche durchführen

Navigieren Sie zum Menüpunkt **Suche**. Hier stehen drei Suchmodi zur Verfügung:

1.  **Einfache Suche**:
    *   Geben Sie einen allgemeinen Suchbegriff ein.
    *   Legen Sie optional die maximale Anzahl der Ergebnisse pro Datenbank fest.
    *   Die Suche wird über alle konfigurierten Datenbanken ausgeführt.

2.  **Spezifische Datenbanksuche**:
    *   Wählen Sie eine Zieldatenbank aus (z.B. PubMed).
    *   Abhängig von der Datenbank ändern sich die verfügbaren Suchfelder (z.B. Titel, Autor, MeSH Terms für PubMed), Publikationstypen und Sprachen. Füllen Sie diese dynamisch.
    *   Geben Sie Ihren Suchbegriff ein.
    *   Fügen Sie optional Personenprofile als Filter hinzu.
    *   Stellen Sie optional einen Datumsbereich ein.

3.  **Personenbezogene Suche**:
    *   Wählen Sie eine zuvor angelegte Person aus der Dropdown-Liste aus.
    *   Die für diese Person hinterlegten Suchbegriffe werden automatisch verwendet.
    *   Wählen Sie, ob die Suche über alle Datenbanken oder eine spezifische Datenbank erfolgen soll.

Nach dem Absenden des Suchformulars wird ein Ladeindikator angezeigt. Die Ergebnisse werden auf der Ergebnisseite dargestellt.

### Personen verwalten

Unter **Personen**:
*   **Person hinzufügen**: Geben Sie Vorname, Nachname, einen optionalen spezifischen Suchbegriff (z.B. Namensvarianten, ORCID) und zusätzliche Begriffe (z.B. Fachgebiete, Institutionen) ein. Diese Details werden für präzisere Suchen im Modus "Personenbezogene Suche" oder als Filter in der "Spezifischen Datenbanksuche" verwendet.
*   **Personenliste**: Zeigt alle gespeicherten Personen. Von hier aus können Sie:
    *   Suchen direkt mit dieser Person starten (kombiniert oder in spezifischen Datenbanken).
    *   Personen bearbeiten (zukünftige Funktion) oder löschen.
*   **Schnellsuche-Optionen**: Bietet Links zu den verschiedenen Suchmodi und eine "Direktsuche" für jede gelistete Person.

### Suchprofile nutzen

*   **Speichern**: Auf der Suchseite können Sie nach Eingabe Ihrer Kriterien über den Button "Als Profil speichern" die aktuelle Konfiguration (Suchbegriffe, Datenbank, Filter) unter einem Namen sichern.
*   **Verwalten**: Unter **Suchprofile** sehen Sie eine Liste aller gespeicherten Profile.
*   **Laden & Starten**: Klicken Sie bei einem Profil auf "Profil laden & Suchen", um die Einstellungen zu übernehmen und direkt zur Suchseite mit den geladenen Parametern weitergeleitet zu werden.
*   **Löschen**: Entfernen Sie nicht mehr benötigte Profile.

### Ergebnisse anzeigen und filtern

Die Seite **Ergebnisse** zeigt die gefundenen Publikationen in einer Tabelle.
*   **Übersicht**: Anzahl der Ergebnisse, Suchkontext.
*   **Aktionen**: Direkte Links zum Export (Excel/CSV) und zur Analyse-Seite.
*   **Filter-Panel**:
    *   **Textsuche**: Filtern Sie die angezeigten Ergebnisse nach einem Textbegriff.
    *   **Dynamische Filter**: Filtern Sie nach Datenbank, Publikationsjahr (Bereich), Publikationstyp und Autor. Diese Filteroptionen werden basierend auf den aktuellen Ergebnissen generiert.
    *   Filter können zurückgesetzt werden. Der Filterstatus (Anzahl angezeigter Ergebnisse) wird angezeigt.
*   **Spaltenauswahl**: Blenden Sie Spalten in der Ergebnistabelle nach Bedarf ein oder aus. Ihre Auswahl wird für die aktuelle Sitzung gespeichert.
*   **Detailansicht**: Klicken Sie auf das Info-Symbol <i class="fas fa-info-circle"></i> bei einem Ergebnis, um ein Modal mit allen verfügbaren Details (Abstract, Keywords, etc.) zu öffnen.
*   **Direktlinks**: Externe Links zur Publikation (falls URL vorhanden) und zum DOI.

### Datenanalyse

Auf der Seite **Analyse** (erreichbar von der Ergebnisseite):
*   **Visualisierungen**: Diagramme zeigen die Verteilung der Publikationen nach Jahr, Datenbank oder Person (Suchkontext).
*   **Statistiken**: Zusammenfassende Statistiken wie Gesamtanzahl, Anzahl pro Datenbank und abgedeckter Zeitraum.
*   **Meistzitierte Publikationen**: Eine Tabelle listet die Top-10 meistzitierten Publikationen aus den aktuellen Suchergebnissen (sofern Zitationsdaten verfügbar sind).

### Datenexport

Auf der Seite **Export** (erreichbar von der Ergebnisseite oder Hauptnavigation):
*   **Formatwahl**: Exportieren Sie die aktuellen Suchergebnisse als Excel (.xlsx) oder CSV (.csv) Datei.
*   **Exporteinstellungen**:
    *   **Spaltenauswahl**: Wählen Sie, welche Spalten in die Exportdatei aufgenommen werden sollen.
    *   **Dateioptionen**: Legen Sie den Exportpfad (serverseitig), Dateinamen-Präfix und die Verwendung eindeutiger Dateinamen fest.
    *   **Excel-/CSV-Optionen**: Spezifische Einstellungen für das jeweilige Format (z.B. Excel-Formatierung, CSV-Trennzeichen und -Kodierung).
    *   Diese Einstellungen können gespeichert werden und werden dann standardmäßig für zukünftige Exporte verwendet.

### Logs und Diagnose

Die Seite **Logs** ist primär für fortgeschrittene Benutzer und zur Fehlerbehebung gedacht.
*   **Log-Ansichten**: Standard-Log (wichtige Ereignisse) und Erweiterter Log (alle Details).
*   **Filter**: Durchsuchen und filtern Sie Logeinträge nach Text, Log-Level und Zeit.
*   **Aktionen**: Logs aktualisieren, herunterladen, automatisch scrollen.
*   **Systeminformationen**: Zeigt Details zur Anwendungsumgebung, Konfiguration und Speichernutzung.
*   **Diagnosewerkzeuge**: Führen Sie Tests für Abhängigkeiten, Datenbankverbindungen und Speicherpfade durch. Ergebnisse werden direkt auf der Seite angezeigt. Hier können auch Logs zurückgesetzt werden.

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Details finden Sie in der Datei `LICENSE.md` (falls vorhanden) oder im Quellcode.
(Hinweis: Eine `LICENSE.md`-Datei wurde im Rahmen dieser Aufgabe nicht explizit erstellt, aber die MIT-Lizenz ist eine übliche Wahl für Open-Source-Projekte.)

---

Readme-Datei erstellt für Medical Spytool.
