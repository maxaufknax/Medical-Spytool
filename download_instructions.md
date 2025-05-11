# Medical Spytool - Download und Installation

Dieses Dokument enthält Anweisungen zum Herunterladen und Installieren der Medical Spytool Anwendung für die lokale Entwicklung.

## Repository herunterladen

Es gibt mehrere Möglichkeiten, das Repository herunterzuladen:

### Option 1: Git Clone (empfohlen)

Wenn Sie Git installiert haben, können Sie das Repository mit folgendem Befehl klonen:

```bash
git clone <repository-url>
cd medicalspy
```

### Option 2: ZIP-Datei herunterladen

1. Laden Sie die ZIP-Datei des Repositories herunter:
   - Besuchen Sie die Repository-URL
   - Klicken Sie auf "Code" und wählen Sie "Download ZIP"
   - Entpacken Sie die heruntergeladene ZIP-Datei

## Lokale Entwicklungsumgebung einrichten

Nach dem Herunterladen können Sie die Entwicklungsumgebung mit dem mitgelieferten Setup-Skript einrichten:

```bash
# Wechseln Sie in das Projektverzeichnis
cd medicalspy

# Führen Sie das Setup-Skript aus
python setup_local_dev.py
```

Das Skript führt Sie durch den Einrichtungsprozess und:
- Erstellt eine virtuelle Python-Umgebung
- Installiert alle benötigten Abhängigkeiten
- Konfiguriert Umgebungsvariablen
- Richtet die Datenbank ein
- Erstellt ein VS Code Startskript

## Manuelle Einrichtung

Wenn Sie die Umgebung lieber manuell einrichten möchten, folgen Sie den Anweisungen in der [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md) Datei.

## Voraussetzungen

- Python 3.10 oder höher
- PostgreSQL Datenbank
- Visual Studio Code (optional, aber empfohlen)

## Fehlerbehebung

Wenn Sie Probleme bei der Einrichtung haben, lesen Sie bitte den Abschnitt "Bekannte Probleme und Workarounds" in der [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md) Datei.