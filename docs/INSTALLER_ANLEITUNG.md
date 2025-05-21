# Anleitung: Erstellung eines Installationsprogramms für Medical Spytool

Diese Anleitung beschreibt, wie Sie ein Installationsprogramm für die Medical Spytool Anwendung erstellen können, das Sie an Ihre Kollegen verteilen können.

## Benötigte Software

1. **Inno Setup**: Ein kostenloses Programm zum Erstellen von Windows-Installationsprogrammen
   - Download: [https://jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php)

## Schritt-für-Schritt-Anleitung

### 1. Inno Setup installieren

1. Laden Sie Inno Setup von der offiziellen Website herunter
2. Führen Sie die Installation aus (alle Standardoptionen belassen)

### 2. Medical Spytool Installer erstellen

1. Öffnen Sie die Datei `MedicalSpytool.iss` in Inno Setup (Rechtsklick -> Öffnen mit -> Inno Setup)
2. Klicken Sie auf das "Kompilieren"-Symbol (grünes Dreieck) oder drücken Sie F9
3. Warten Sie, bis die Kompilierung abgeschlossen ist (kann einige Minuten dauern)
4. Der fertige Installer (`MedicalSpytool_Setup.exe`) wird im Ordner `Output` erstellt

### 3. Installer verteilen

- Kopieren Sie die Datei `MedicalSpytool_Setup.exe` auf einen USB-Stick oder in ein Netzlaufwerk
- Geben Sie die Datei an Ihre Kollegen weiter
- Sie können den Installer auch per E-Mail versenden (achten Sie auf Größenbeschränkungen)

## Anpassungsoptionen

Möchten Sie den Installer anpassen, können Sie folgende Änderungen in der Datei `MedicalSpytool.iss` vornehmen:

- **Name der Anwendung**: Ändern Sie `#define MyAppName "Medical Spytool"`
- **Version**: Ändern Sie `#define MyAppVersion "2.0"`
- **Publisher**: Ändern Sie `#define MyAppPublisher "Medizinische Fakultät"`
- **Website**: Ändern Sie `#define MyAppURL "https://www.example.com/medicalspytool"`

## Hinweise

- Der Installer installiert automatisch alle notwendigen Komponenten
- Python wird überprüft und bei Bedarf heruntergeladen
- Die Installation benötigt Administratorrechte (normale Verwendung jedoch nicht)
- Alle Projektdateien werden in den Programmordner kopiert

Bei Fragen oder Problemen wenden Sie sich bitte an Ihre IT-Abteilung.
