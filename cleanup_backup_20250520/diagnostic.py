#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Anwendungsdiagnose

Dieses Skript hilft, häufige Probleme mit der Medical Spytool-Anwendung zu identifizieren und zu beheben.
Es führt verschiedene Tests durch, um die Funktionalität und Einrichtung der Anwendung zu überprüfen.
"""

import os
import sys
import sqlite3
import logging
import platform
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("diagnostic.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("MedicalSpy-Diagnose")


class MedicalSpyDiagnostic:
    """Klasse zur Diagnose der Medical Spytool-Anwendung"""

    def __init__(self):
        """Initialisiere die Diagnose"""
        self.base_dir = Path(__file__).resolve().parent
        self.env_file = self.base_dir / ".env"
        self.db_path = self.base_dir / "instance" / "medicalspy.db"
        self.venv_dir = self.base_dir / "venv"
        self.required_packages = [
            "flask",
            "flask-sqlalchemy",
            "flask-wtf",
            "flask-login",
            "python-dotenv",
            "werkzeug",
            "itsdangerous",
        ]
        self.issues_found = []
        self.fixes_applied = []

        # System-Info
        self.python_version = platform.python_version()
        self.system_info = f"{platform.system()} {platform.release()}"

        # Setup Python-Pfad
        sys.path.insert(0, str(self.base_dir))

    def run_diagnostics(self):
        """Führt alle Diagnosetests aus"""
        print("\n" + "=" * 80)
        print("{:^80}".format("MEDICAL SPYTOOL - DIAGNOSE"))
        print("=" * 80 + "\n")

        print(f"Betriebssystem: {self.system_info}")
        print(f"Python-Version: {self.python_version}")
        print(f"Anwendungsverzeichnis: {self.base_dir}\n")

        # Führe die Diagnosen nacheinander aus
        self.check_directory_structure()
        self.check_env_file()
        self.check_virtual_environment()
        self.check_dependencies()
        self.check_database()
        self.check_application_code()
        self.check_flask_app()

        # Zeige zusammenfassende Ergebnisse
        self.show_summary()

        return len(self.issues_found) == 0

    def check_directory_structure(self):
        """Überprüft, ob alle notwendigen Verzeichnisse existieren"""
        print("\n📁 Überprüfe Verzeichnisstruktur...")

        required_dirs = ["instance", "logs", "output", "person_lists", "backend", "tests"]
        missing_dirs = []

        for dir_name in required_dirs:
            dir_path = self.base_dir / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
                self.issues_found.append(f"Fehlendes Verzeichnis: {dir_name}")
            else:
                logger.info(f"Verzeichnis gefunden: {dir_name}")

        if missing_dirs:
            print(f"❌ Fehlende Verzeichnisse: {', '.join(missing_dirs)}")
            self._create_directories(missing_dirs)
        else:
            print("✅ Alle erforderlichen Verzeichnisse sind vorhanden.")

    def _create_directories(self, directories):
        """Erstellt fehlende Verzeichnisse"""
        for dir_name in directories:
            try:
                dir_path = self.base_dir / dir_name
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Verzeichnis erstellt: {dir_name}")
                self.fixes_applied.append(f"Verzeichnis erstellt: {dir_name}")
            except Exception as e:
                logger.error(f"Fehler beim Erstellen von {dir_name}: {e}")

    def check_env_file(self):
        """Überprüft die .env-Datei"""
        print("\n📄 Überprüfe .env-Datei...")

        if not self.env_file.exists():
            print("❌ .env-Datei nicht gefunden.")
            self.issues_found.append(".env-Datei fehlt")
            self._create_env_file()
            return

        try:
            # Lese .env-Datei
            env_vars = {}
            with open(self.env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()

            # Überprüfe benötigte Variablen
            required_vars = ["DATABASE_URL", "SECRET_KEY", "SESSION_SECRET", "LOG_LEVEL"]

            missing_vars = [var for var in required_vars if var not in env_vars]

            if missing_vars:
                print(f"❌ Fehlende Umgebungsvariablen: {', '.join(missing_vars)}")
                self.issues_found.append(f"Fehlende Umgebungsvariablen: {', '.join(missing_vars)}")
                self._update_env_file(missing_vars)
            else:
                print("✅ .env-Datei vollständig.")

            # Überprüfe Datenbankeinstellungen
            if "DATABASE_URL" in env_vars:
                db_url = env_vars["DATABASE_URL"]
                if "sqlite:///" not in db_url and "sqlite:" not in db_url:
                    print(
                        "⚠️ Nicht-SQLite-Datenbank konfiguriert. Empfehle Umstellung auf SQLite für einfachere Nutzung."
                    )
                    self.issues_found.append(f"Nicht-SQLite-Datenbank: {db_url}")

        except Exception as e:
            logger.error(f"Fehler beim Lesen der .env-Datei: {e}")
            self.issues_found.append(f"Fehler in .env-Datei: {str(e)}")

    def _create_env_file(self):
        """Erstellt eine neue .env-Datei mit Standardwerten"""
        try:
            env_example = self.base_dir / ".env.example"
            if env_example.exists():
                # Kopiere von .env.example
                with (
                    open(env_example, "r", encoding="utf-8") as src,
                    open(self.env_file, "w", encoding="utf-8") as dst,
                ):
                    for line in src:
                        if line.startswith("DATABASE_URL=") and "sqlite:///" not in line:
                            dst.write("DATABASE_URL=sqlite:///instance/medicalspy.db\n")
                        else:
                            dst.write(line)
                logger.info(".env-Datei aus .env.example erstellt")
            else:
                # Erstelle neue .env-Datei
                with open(self.env_file, "w", encoding="utf-8") as f:
                    f.write("# MedicalSpy Environment Variables\n")
                    f.write("# Generated by diagnostic.py\n\n")
                    f.write("DATABASE_URL=sqlite:///instance/medicalspy.db\n")
                    f.write("FLASK_ENV=development\n")
                    f.write("DEBUG=True\n")
                    f.write("FLASK_DEBUG=True\n")
                    f.write("SECRET_KEY=dev_secret_key_123\n")
                    f.write("SESSION_SECRET=dev_secret_key_123\n")
                    f.write("LOG_LEVEL=DEBUG\n")
                    f.write("OUTPUT_PATH=./output\n")
                    f.write("PERSON_LIST_PATH=./person_lists\n")
                    f.write("DEFAULT_DATABASE=PubMed\n")
                logger.info("Neue .env-Datei mit Standardwerten erstellt")

            self.fixes_applied.append(".env-Datei erstellt")
            print("✅ Neue .env-Datei erstellt.")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der .env-Datei: {e}")

    def _update_env_file(self, missing_vars):
        """Aktualisiert die .env-Datei mit fehlenden Variablen"""
        try:
            # Standardwerte für fehlende Variablen
            default_values = {
                "DATABASE_URL": "sqlite:///instance/medicalspy.db",
                "SECRET_KEY": "dev_secret_key_123",
                "SESSION_SECRET": "dev_secret_key_123",
                "LOG_LEVEL": "DEBUG",
                "OUTPUT_PATH": "./output",
                "PERSON_LIST_PATH": "./person_lists",
                "DEFAULT_DATABASE": "PubMed",
                "FLASK_ENV": "development",
                "DEBUG": "True",
                "FLASK_DEBUG": "True",
            }

            # Füge fehlende Variablen hinzu
            with open(self.env_file, "a", encoding="utf-8") as f:
                f.write("\n# Added by diagnostic.py\n")
                for var in missing_vars:
                    if var in default_values:
                        f.write(f"{var}={default_values[var]}\n")

            self.fixes_applied.append(f".env-Datei aktualisiert mit: {', '.join(missing_vars)}")
            print(f"✅ .env-Datei mit fehlenden Variablen aktualisiert.")
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der .env-Datei: {e}")

    def check_virtual_environment(self):
        """Überprüft, ob eine virtuelle Umgebung existiert"""
        print("\n🔧 Überprüfe virtuelle Umgebung...")

        if not self.venv_dir.exists():
            print("❌ Virtuelle Umgebung nicht gefunden.")
            self.issues_found.append("Fehlende virtuelle Umgebung")
            return

        # Überprüfe, ob Python-Executable in der virtuellen Umgebung existiert
        if os.name == "nt":  # Windows
            python_exe = self.venv_dir / "Scripts" / "python.exe"
        else:  # Unix/Linux/Mac
            python_exe = self.venv_dir / "bin" / "python"

        if not python_exe.exists():
            print(f"❌ Python-Executable nicht gefunden in virtueller Umgebung: {python_exe}")
            self.issues_found.append("Beschädigte virtuelle Umgebung")
            return

        print("✅ Virtuelle Umgebung gefunden und scheint funktionsfähig.")

    def check_dependencies(self):
        """Überprüft, ob alle erforderlichen Pakete installiert sind"""
        print("\n📦 Überprüfe Python-Abhängigkeiten...")

        missing_packages = []

        for package in self.required_packages:
            spec = importlib.util.find_spec(package.replace("-", "_"))
            if spec is None:
                missing_packages.append(package)
                self.issues_found.append(f"Fehlendes Paket: {package}")

        if missing_packages:
            print(f"❌ Fehlende Pakete: {', '.join(missing_packages)}")
        else:
            print("✅ Alle erforderlichen Pakete sind installiert.")

    def check_database(self):
        """Überprüft die Datenbank"""
        print("\n🗄️ Überprüfe Datenbank...")

        if not self.db_path.exists():
            print("❌ Datenbank nicht gefunden.")
            self.issues_found.append("Datenbank fehlt")
            return

        try:
            # Überprüfe, ob die Datenbank geöffnet werden kann und Tabellen enthält
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Tabellenliste abrufen
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            if not tables:
                print("❌ Datenbank existiert, enthält aber keine Tabellen.")
                self.issues_found.append("Leere Datenbank")
            else:
                table_names = [table[0] for table in tables]
                print(
                    f"✅ Datenbank gefunden mit {len(tables)} Tabellen: {', '.join(table_names[:5])}{' und weitere...' if len(tables) > 5 else ''}"
                )

                # Überprüfe wichtige Tabellen
                expected_tables = [
                    "user",
                    "search_query",
                    "search_result",
                    "person",
                    "setting",
                    "log_entry",
                ]
                missing_tables = [table for table in expected_tables if table not in table_names]

                if missing_tables:
                    print(f"❌ Wichtige Tabellen fehlen: {', '.join(missing_tables)}")
                    self.issues_found.append(f"Fehlende Tabellen: {', '.join(missing_tables)}")

            conn.close()
        except sqlite3.Error as e:
            print(f"❌ Fehler beim Zugriff auf die Datenbank: {e}")
            self.issues_found.append(f"Datenbankfehler: {str(e)}")

    def check_application_code(self):
        """Überprüft den Anwendungscode auf häufige Fehler"""
        print("\n🔍 Überprüfe Anwendungscode...")

        # Überprüfe wichtige Dateien
        essential_files = ["backend/app.py", "backend/models.py", "backend/config.py", "run.py"]

        missing_files = []
        for file_path in essential_files:
            full_path = self.base_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
                self.issues_found.append(f"Fehlende Datei: {file_path}")

        if missing_files:
            print(f"❌ Wichtige Dateien fehlen: {', '.join(missing_files)}")
        else:
            print("✅ Alle wichtigen Dateien sind vorhanden.")

        # Überprüfe JSONB-Kompatibilität in models.py
        models_file = self.base_dir / "backend" / "models.py"
        if models_file.exists():
            try:
                with open(models_file, "r", encoding="utf-8") as f:
                    content = f.read()

                if "class JSONType" not in content:
                    print(
                        "⚠️ JSONB-Typkompatibilität könnte ein Problem sein. JSONType-Klasse fehlt."
                    )
                    self.issues_found.append("Fehlende JSONType-Klasse in models.py")
                else:
                    print("✅ JSONB-Typkompatibilität ist implementiert.")

                # Erweiterte Überprüfung der models.py auf Syntaxfehler
                if "result_data = db.Column(JSONB" in content and "JSONType" not in content:
                    print("❌ JSONB wird verwendet, aber JSONType ist nicht implementiert.")
                    self.issues_found.append("JSONB-SQLite-Inkompatibilität in models.py")

            except Exception as e:
                logger.error(f"Fehler beim Lesen von models.py: {e}")

    def check_flask_app(self):
        """Überprüft die Flask-Anwendung"""
        print("\n🌐 Überprüfe Flask-Anwendung...")

        try:
            # Versuche, die Flask-App zu importieren
            from backend.app import create_app

            # Erstelle eine Test-App
            app = create_app("testing")

            # Überprüfe Konfiguration
            print(f"✅ Flask-Anwendung konnte initialisiert werden.")
            print(f"   - Umgebung: {app.config.get('ENV', 'nicht definiert')}")
            print(f"   - Debug: {app.config.get('DEBUG', 'nicht definiert')}")
            print(
                f"   - Datenbank-URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'nicht definiert')}"
            )

        except ImportError:
            print("❌ Die Flask-Anwendung konnte nicht importiert werden.")
            self.issues_found.append("Fehler beim Importieren der Flask-Anwendung")
        except Exception as e:
            print(f"❌ Fehler beim Überprüfen der Flask-Anwendung: {e}")
            self.issues_found.append(f"Flask-App-Fehler: {str(e)}")

    def show_summary(self):
        """Zeigt eine Zusammenfassung der Diagnose"""
        print("\n" + "=" * 80)
        print("{:^80}".format("DIAGNOSE-ERGEBNIS"))
        print("=" * 80)

        if self.issues_found:
            print(f"\n❌ Es wurden {len(self.issues_found)} Probleme gefunden:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"  {i}. {issue}")

            if self.fixes_applied:
                print(f"\n🔧 {len(self.fixes_applied)} Probleme wurden automatisch behoben:")
                for i, fix in enumerate(self.fixes_applied, 1):
                    print(f"  {i}. {fix}")

            print("\n⚙️ Empfohlene Maßnahmen:")
            if any("Fehlende virtuelle Umgebung" in issue for issue in self.issues_found):
                print(
                    "  - Führen Sie 'python -m venv venv' aus, um eine virtuelle Umgebung zu erstellen."
                )

            if any("Fehlendes Paket" in issue for issue in self.issues_found):
                print(
                    "  - Führen Sie 'pip install -r project_requirements.txt' aus, um fehlende Pakete zu installieren."
                )

            if (
                any("Datenbank fehlt" in issue for issue in self.issues_found)
                or any("Leere Datenbank" in issue for issue in self.issues_found)
                or any("Fehlende Tabellen" in issue for issue in self.issues_found)
            ):
                print(
                    "  - Führen Sie 'python initialize_db.py' aus, um die Datenbank zu initialisieren."
                )

            if any("JSONB" in issue for issue in self.issues_found):
                print(
                    "  - Führen Sie 'python fix_database.py' aus, um das JSONB-Kompatibilitätsproblem zu beheben."
                )

        else:
            print("\n✅ Keine Probleme gefunden! Medical Spytool sollte korrekt funktionieren.")

        # Füge Hinweise für Tests hinzu
        print("\n🧪 Um Tests auszuführen, verwenden Sie:")
        print("  - python run_tests.py              # Führt alle Tests aus")
        print("  - python run_tests.py --coverage   # Führt Tests mit Coverage-Bericht aus")
        print("  - python run_tests.py --test-path tests/test_app.py  # Führt bestimmte Tests aus")

        # Füge Hinweise für die Anwendung hinzu
        print("\n🚀 Um die Anwendung zu starten, verwenden Sie:")
        print("  - python run.py                  # Startet die Anwendung")
        print("  - python start_medical_spytool.py  # Umfassende Lösung zum Starten")

        print("\n" + "=" * 80 + "\n")


def main():
    """Hauptfunktion"""
    try:
        diagnostic = MedicalSpyDiagnostic()
        all_ok = diagnostic.run_diagnostics()

        return 0 if all_ok else 1
    except KeyboardInterrupt:
        print("\n\nDiagnose wurde vom Benutzer abgebrochen.")
        return 130
    except Exception as e:
        logger.error(f"Unbehandelte Ausnahme: {e}", exc_info=True)
        print(f"\n❌ Ein unerwarteter Fehler ist aufgetreten: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
