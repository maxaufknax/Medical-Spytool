#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Verbesserter Anwendungsstarter

Dieses Skript startet die MedicalSpy-Anwendung mit verbesserter Fehlerbehandlung
und korrekter Verwaltung des Anwendungskontexts.
"""

import os
import sys
import logging
from pathlib import Path
import webbrowser
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus .env
load_dotenv()

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("application.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("MedicalSpy-Runner")

# Stelle sicher, dass das Instance-Verzeichnis existiert
instance_dir = Path("instance")
if not instance_dir.exists():
    logger.info(f"Erstelle Instance-Verzeichnis: {instance_dir}")
    instance_dir.mkdir(parents=True, exist_ok=True)

# Importiere Flask-App mit korrektem Fehlerhandling
try:
    from backend.app import create_app
    from backend.models import db

    # Erstelle Flask-App
    app = create_app()

    # Stelle sicher, dass die Datenbank im Anwendungskontext initialisiert wird
    with app.app_context():
        try:
            # Erstelle Datenbanktabellen, falls sie nicht existieren
            db.create_all()
            logger.info("Datenbanktabellen erfolgreich erstellt/überprüft")

            # Teste Datenbankverbindung
            from backend.models import User

            user_count = User.query.count()
            logger.info(f"Datenbankverbindung erfolgreich getestet, {user_count} Benutzer gefunden")

        except Exception as e:
            logger.error(f"Fehler bei der Datenbankinitialisierung: {e}")
            logger.warning(
                "Die Anwendung wird trotzdem gestartet, aber Datenbankoperationen könnten fehlschlagen"
            )

    # Anwendungsparameter
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")

    # Öffne Browser, sofern nicht deaktiviert
    if os.environ.get("NO_BROWSER", "False").lower() not in ("true", "1", "t"):
        url = f"http://{host}:{port}/"
        webbrowser.open(url)

    # Starte die Anwendung
    logger.info(f"MedicalSpy wird gestartet auf http://{host}:{port}/")
    app.run(host=host, port=port, debug=debug)

except ImportError as e:
    logger.error(f"Fehler beim Importieren der Anwendungsmodule: {e}")
    logger.error("Bitte stellen Sie sicher, dass alle Abhängigkeiten installiert sind")
    logger.error("Führen Sie 'pip install -r project_requirements.txt' aus")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unerwarteter Fehler: {e}")
    sys.exit(1)
