#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Verbessertes Ausführungsskript

Dieses Skript behebt häufige Probleme und stellt sicher, dass die Anwendung
korrekt gestartet wird. Es enthält Fehlerbehandlung für:
- Unicode-Kodierungsprobleme
- Datenbankverbindungsprobleme
- Fehlende Abhängigkeiten
"""

import os
import sys
import time
import logging
import subprocess
import webbrowser
import argparse
from pathlib import Path
from datetime import datetime

# Konfiguriere UTF-8 für die Konsole (Windows)
if os.name == "nt":
    os.system("chcp 65001 > nul")

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("run_improved.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("MedicalSpy-Runner")


def check_dependencies():
    """Überprüft und installiert fehlende Abhängigkeiten"""
    logger.info("Überprüfe Abhängigkeiten...")
    required_packages = [
        "flask",
        "flask-sqlalchemy",
        "flask-wtf",
        "flask-login",
        "python-dotenv",
        "werkzeug",
        "itsdangerous",
        "beautifulsoup4",
    ]

    missing = []
    for package in required_packages:
        try:
            # Prüfe, ob das Paket importiert werden kann
            package_name = package.replace("-", "_")
            __import__(package_name.split(".")[0])
        except ImportError:
            missing.append(package)

    if missing:
        logger.warning(f"Fehlende Pakete: {', '.join(missing)}")
        logger.info("Installiere fehlende Pakete...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True)
            logger.info("Alle fehlenden Pakete wurden installiert.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Fehler beim Installieren von Paketen: {e}")
            return False
    else:
        logger.info("Alle erforderlichen Pakete sind installiert.")

    return True


def fix_database_issues():
    """Behebt Probleme mit der Datenbank"""
    logger.info("Überprüfe Datenbank...")

    # Überprüfe, ob das Instance-Verzeichnis existiert
    instance_dir = Path("instance")
    if not instance_dir.exists():
        logger.warning("Instance-Verzeichnis nicht gefunden, erstelle es...")
        instance_dir.mkdir(exist_ok=True)

    # Überprüfe, ob die Datenbank existiert
    db_path = instance_dir / "medicalspy.db"
    if not db_path.exists():
        logger.warning("Datenbank nicht gefunden, initialisiere neu...")
        init_script = Path("initialize_db.py")
        if init_script.exists():
            try:
                subprocess.run([sys.executable, str(init_script), "--force"], check=True)
                if db_path.exists():
                    logger.info("Datenbank erfolgreich initialisiert.")
                else:
                    logger.error("Datenbank konnte nicht initialisiert werden.")
                    return False
            except subprocess.CalledProcessError as e:
                logger.error(f"Fehler beim Initialisieren der Datenbank: {e}")
                return False
        else:
            logger.error("initialize_db.py nicht gefunden.")
            return False
    else:
        logger.info(f"Datenbank gefunden: {db_path}")

    # Überprüfe .env-Datei
    env_file = Path(".env")
    if not env_file.exists():
        logger.warning(".env-Datei nicht gefunden, erstelle sie...")
        default_env = """
DATABASE_URL=sqlite:///instance/medicalspy.db
FLASK_ENV=development
DEBUG=True
FLASK_APP=backend.app
SECRET_KEY=dev_secret_key_123
SESSION_SECRET=dev_secret_key_123
LOG_LEVEL=DEBUG
OUTPUT_PATH=./output
PERSON_LIST_PATH=./person_lists
DEFAULT_DATABASE=PubMed
FLASK_DEBUG=True
        """.strip()

        try:
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(default_env)
            logger.info(".env-Datei erstellt.")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der .env-Datei: {e}")
            return False

    return True


def run_application(host="127.0.0.1", port=5000, no_browser=False, debug=True):
    """Startet die MedicalSpy-Anwendung"""
    logger.info(f"Starte MedicalSpy-Anwendung auf http://{host}:{port}/")

    cmd = [sys.executable, "run.py"]

    if host != "127.0.0.1":
        cmd.extend(["--host", host])

    cmd.extend(["--port", str(port)])

    if no_browser:
        cmd.append("--no-browser")

    if debug:
        cmd.append("--debug")

    try:
        # Starte die Anwendung asynchron
        process = subprocess.Popen(cmd)

        # Warte kurz, um sicherzustellen, dass die Anwendung gestartet wurde
        time.sleep(2)

        # Öffne den Browser, wenn gewünscht
        if not no_browser:
            url = f"http://{host}:{port}/"
            logger.info(f"Öffne Browser: {url}")
            webbrowser.open(url)

        logger.info("Anwendung läuft. Drücken Sie Strg+C, um zu beenden.")

        # Warte auf Benutzereingabe
        try:
            process.wait()
            return True
        except KeyboardInterrupt:
            logger.info("Benutzerabbruch erkannt, beende Anwendung...")
            process.terminate()
            process.wait(timeout=5)
            return True

    except Exception as e:
        logger.error(f"Fehler beim Starten der Anwendung: {e}")
        return False


def run_tests(test_path=None, coverage=False):
    """Führt die Tests aus"""
    logger.info("Führe Tests aus...")

    cmd = [sys.executable, "run_tests.py"]

    if test_path:
        cmd.extend(["--test-path", test_path])

    if coverage:
        cmd.append("--coverage")

    try:
        subprocess.run(cmd, check=True)
        logger.info("Tests erfolgreich ausgeführt.")
        return True
    except subprocess.CalledProcessError:
        logger.error("Fehler beim Ausführen der Tests.")
        return False


def main():
    """Hauptfunktion"""
    parser = argparse.ArgumentParser(description="Verbessertes MedicalSpy Ausführungsskript")
    parser.add_argument("--host", default="127.0.0.1", help="Host für die Anwendung")
    parser.add_argument("--port", type=int, default=5000, help="Port für die Anwendung")
    parser.add_argument("--no-browser", action="store_true", help="Browser nicht öffnen")
    parser.add_argument("--no-deps-check", action="store_true", help="Keine Abhängigkeitsprüfung")
    parser.add_argument("--test", action="store_true", help="Tests ausführen")
    parser.add_argument("--test-path", help="Spezifischer Testpfad")
    parser.add_argument("--coverage", action="store_true", help="Coverage-Report erstellen")
    parser.add_argument("--debug", action="store_true", help="Debug-Modus aktivieren")
    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("{:^80}".format("MEDICAL SPYTOOL - VERBESSERTES AUSFÜHRUNGSSKRIPT"))
    print("=" * 80 + "\n")

    # Setze sys.path auf das aktuelle Verzeichnis
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    # Überprüfe Abhängigkeiten
    if not args.no_deps_check and not check_dependencies():
        logger.error("Fehler bei der Abhängigkeitsprüfung.")
        return 1

    # Behebe Datenbankprobleme
    if not fix_database_issues():
        logger.error("Fehler bei der Datenbankkorrektur.")
        return 1

    # Führe Tests aus, wenn gewünscht
    if args.test:
        success = run_tests(args.test_path, args.coverage)
        if not success:
            logger.error("Tests fehlgeschlagen.")
            return 1

        if not args.no_browser and not args.host:
            # Beende nach Tests, wenn keine Anwendung gestartet werden soll
            return 0

    # Starte die Anwendung
    success = run_application(
        host=args.host, port=args.port, no_browser=args.no_browser, debug=args.debug
    )

    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("Prozess durch Benutzer abgebrochen.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unbehandelte Ausnahme: {e}", exc_info=True)
        sys.exit(1)
