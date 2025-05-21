# Bereitstellung von Medical Spytool auf einem Server

Diese Anleitung beschreibt, wie Sie die Medical Spytool Anwendung auf einem Server bereitstellen können, damit mehrere Benutzer darauf zugreifen können.

## Voraussetzungen

- Ein Server mit einer der folgenden Betriebssysteme:
  - Linux (Ubuntu, Debian, CentOS, etc.)
  - Windows Server 2016 oder höher
- Python 3.8 oder höher
- Internetzugang für den Server
- Grundlegende Kenntnisse der Serveradministration oder Unterstützung durch IT-Abteilung

## Option A: Einfache Bereitstellung mit Docker (empfohlen)

### 1. Docker und Docker Compose installieren

#### Für Linux:
```bash
sudo apt update
sudo apt install docker.io docker-compose
```

#### Für Windows Server:
- Docker Desktop herunterladen und installieren: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)

### 2. Medical Spytool Anwendung auf den Server kopieren
- Kopieren Sie den gesamten Medical Spytool Ordner auf den Server

### 3. Anwendung starten
Im Medical Spytool Ordner:

```bash
docker-compose up -d
```

Die Anwendung ist jetzt unter http://[server-ip]:5000 verfügbar.

## Option B: Manuelle Installation

### 1. Python und Abhängigkeiten installieren

#### Für Linux:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

#### Für Windows Server:
- Python von [python.org](https://www.python.org/downloads/) herunterladen und installieren

### 2. Medical Spytool Anwendung auf den Server kopieren
- Kopieren Sie den gesamten Medical Spytool Ordner auf den Server

### 3. Virtuelle Umgebung erstellen und Abhängigkeiten installieren

#### Für Linux:
```bash
cd Medical-Spytool-2
python3 -m venv venv
source venv/bin/activate
pip install -r project_requirements.txt
```

#### Für Windows:
```
cd Medical-Spytool-2
python -m venv venv
venv\Scripts\activate
pip install -r project_requirements.txt
```

### 4. Datenbank initialisieren
```
python init_db.py
```

### 5. Anwendung starten

#### Für Linux:
```bash
gunicorn -b 0.0.0.0:5000 "backend.app:app"
```

#### Für Windows:
```
waitress-serve --port=5000 backend.app:app
```

Die Anwendung ist jetzt unter http://[server-ip]:5000 verfügbar.

## Option C: Als Windows-Dienst einrichten

Um die Anwendung als Windows-Dienst zu installieren (startet automatisch mit dem Server):

1. NSSM (Non-Sucking Service Manager) herunterladen: [https://nssm.cc/download](https://nssm.cc/download)
2. Dienst installieren:
```
nssm install MedicalSpytool "C:\pfad\zu\venv\Scripts\python.exe" "C:\pfad\zu\Medical-Spytool-2\run.py"
nssm set MedicalSpytool AppDirectory "C:\pfad\zu\Medical-Spytool-2"
nssm start MedicalSpytool
```

## Für die IT-Abteilung

### Sicherheitshinweise
- Die Anwendung verwendet CSRF-Schutz und Authentifizierung für Sicherheit
- Für Produktionsumgebungen wird empfohlen:
  - HTTPS mit gültigem SSL-Zertifikat zu konfigurieren
  - Eine Firewall einzurichten
  - Regelmäßige Backups der Datenbank durchzuführen

### Performance-Optimierung
- Für mehr als 10 gleichzeitige Benutzer:
  - Erhöhen Sie die Anzahl der Worker in der Docker-Konfiguration
  - Verwenden Sie einen dedizierten Datenbank-Server
  - Erwägen Sie die Verwendung eines Load-Balancers

### Hochverfügbarkeit
- Die Anwendung kann auf mehreren Servern bereitgestellt werden
- Ein Load-Balancer kann den Verkehr verteilen
- Die Datenbank sollte auf einem separaten Server mit Backup-Strategie laufen
