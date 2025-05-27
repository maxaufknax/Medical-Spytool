# Medical Spytool - Benutzerhandbuch

## Inhaltsverzeichnis
1. [Schnellstart](#schnellstart)
2. [Installation](#installation)
3. [Bedienung der Anwendung](#bedienung-der-anwendung)
4. [Häufige Aufgaben](#häufige-aufgaben)
5. [Systemanforderungen](#systemanforderungen)
6. [Problembehebung](#problembehebung)

## Schnellstart

### Fertige Installation mit Installer (empfohlen)
1. Laden Sie den MedicalSpytool_Setup.exe Installer herunter
2. Führen Sie den Installer aus und folgen Sie den Anweisungen
3. Starten Sie die Anwendung über das Desktop-Symbol oder das Startmenü

### Manuelle Ausführung vom USB-Stick oder Netzwerklaufwerk
1. Doppelklick auf `RunMedicalSpytool.bat`
2. Die Anwendung öffnet sich automatisch in Ihrem Webbrowser

## Installation

### Neue Installation
1. Doppelklick auf `INSTALLATION.bat`
2. Folgen Sie den Anweisungen auf dem Bildschirm
3. Nach der Installation können Sie die Anwendung über das Desktop-Symbol starten

### Updates installieren
1. Laden Sie die neue Version herunter
2. Führen Sie erneut die Installation aus. Ihre Daten bleiben erhalten.

## Bedienung der Anwendung

### Suchen nach wissenschaftlichen Publikationen
1. Geben Sie Ihre Suchbegriffe in das Suchfeld ein
2. Wählen Sie die gewünschten Datenbanken aus (PubMed, Scopus, etc.)
3. Klicken Sie auf "Suche starten"

### Ergebnisse exportieren
1. Wählen Sie die gewünschten Ergebnisse aus
2. Klicken Sie auf "Exportieren"
3. Wählen Sie das gewünschte Format (Excel, CSV, etc.)

### Einstellungen anpassen
1. Klicken Sie auf "Einstellungen" in der oberen Leiste
2. Ändern Sie die gewünschten Einstellungen
3. Klicken Sie auf "Speichern"

## Systemanforderungen

- Windows 10 oder höher
- Python 3.8 oder höher (wird automatisch installiert)
- 2 GB freier Speicherplatz
- Internetzugang (für Datenbankabfragen)

## Problembehebung

### Die Anwendung startet nicht

1. Führen Sie `setup.cmd` aus, um alle Abhängigkeiten zu installieren
2. Überprüfen Sie, ob Python korrekt installiert ist (`python --version` in CMD)
3. Prüfen Sie die Logdateien im Ordner `logs`

### Browser öffnet sich nicht automatisch

Öffnen Sie manuell http://localhost:5000 in Ihrem Browser.

### Fehlermeldungen

Überprüfen Sie den Inhalt der Dateien im `logs`-Ordner.

## Support

Bei Fragen oder Problemen wenden Sie sich bitte an:
[supportadresse@beispiel.de]

---

© 2025 Medical Spytool Team
