#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medical Spytool - Lokales Entwicklungsumgebungs-Setup Skript

Dieses Skript hilft bei der Einrichtung einer lokalen Entwicklungsumgebung für das Medical Spytool Projekt.
Es führt folgende Aufgaben aus:
- Erstellen einer virtuellen Python-Umgebung
- Installation der benötigten Pakete
- Konfiguration der lokalen Umgebungsvariablen
- Initialisierung der Datenbank (optional)
- Erstellen von Testdaten (optional)

Ausführung:
    python setup_local_dev.py

Autor: Medical Spytool Team
"""

import os
import sys
import subprocess
import platform
import shutil
import json
import getpass
from pathlib import Path


# Farbcodes für Terminalausgabe
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_section(title):
    """Gibt einen formatierten Abschnittstitel aus"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD} {title}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_step(step, end="\n"):
    """Gibt einen formatierten Schritt aus"""
    print(f"{Colors.BLUE}➤ {step}{Colors.ENDC}", end=end)


def print_success(message):
    """Gibt eine Erfolgsmeldung aus"""
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")


def print_warning(message):
    """Gibt eine Warnmeldung aus"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_error(message):
    """Gibt eine Fehlermeldung aus"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def run_command(command, verbose=True, exit_on_error=True):
    """Führt einen Shell-Befehl aus und gibt das Ergebnis zurück"""
    if verbose:
        print_step(f"Führe aus: {Colors.BOLD}{command}{Colors.ENDC}")
    
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(command, shell=True, check=True, 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                  text=True, encoding='cp1252')
        else:
            result = subprocess.run(command, shell=True, check=True, 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                  text=True)
        
        if verbose and result.stdout:
            print(result.stdout)
            
        return result.stdout
    except subprocess.CalledProcessError as e:
        if verbose:
            print_error(f"Fehler beim Ausführen des Befehls: {command}")
            print(f"Fehlermeldung: {e.stderr}")
        if exit_on_error:
            print_error("Setup abgebrochen aufgrund eines Fehlers.")
            sys.exit(1)
        return None


def check_python_version():
    """Überprüft, ob die Python-Version 3.10 oder höher ist"""
    print_step("Überprüfe Python-Version... ")
    
    version = platform.python_version()
    major, minor, _ = map(int, version.split('.'))
    
    if major >= 3 and minor >= 10:
        print_success(f"Python {version} gefunden (erforderlich: 3.10+)")
        return True
    else:
        print_error(f"Python {version} gefunden, aber 3.10+ ist erforderlich")
        print_warning("Bitte installieren Sie Python 3.10 oder höher von https://www.python.org/downloads/")
        return False


def create_virtual_env():
    """Erstellt eine virtuelle Python-Umgebung"""
    print_step("Erstelle virtuelle Python-Umgebung... ")
    
    venv_path = Path("venv")
    if venv_path.exists():
        choice = input(f"{Colors.WARNING}Virtuelle Umgebung existiert bereits. Neu erstellen? (j/n): {Colors.ENDC}")
        if choice.lower() == 'j':
            if platform.system() == 'Windows':
                run_command(f"rmdir /s /q {venv_path}")
            else:
                run_command(f"rm -rf {venv_path}")
        else:
            print_warning("Bestehende virtuelle Umgebung wird verwendet.")
            return
    
    # Virtuelle Umgebung erstellen
    run_command(f"{sys.executable} -m venv venv")
    print_success("Virtuelle Umgebung erstellt")


def activate_venv_command():
    """Gibt den Befehl zurück, um die virtuelle Umgebung zu aktivieren"""
    if platform.system() == 'Windows':
        return "venv\\Scripts\\activate"
    else:
        return "source venv/bin/activate"


def install_requirements():
    """Installiert die benötigten Pakete in der virtuellen Umgebung"""
    print_step("Installiere Abhängigkeiten... ")
    
    # Pfad zum Pip in der virtuellen Umgebung
    if platform.system() == 'Windows':
        pip_path = "venv\\Scripts\\pip"
    else:
        pip_path = "venv/bin/pip"
    
    # Pip upgraden
    run_command(f"{pip_path} install --upgrade pip")
    
    # Pakete installieren
    run_command(f"{pip_path} install -r project_requirements.txt")
    print_success("Abhängigkeiten installiert")


def configure_environment():
    """Konfiguriert die lokale Umgebung (.env-Datei)"""
    print_step("Konfiguriere Umgebungsvariablen... ")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        choice = input(f"{Colors.WARNING}.env-Datei existiert bereits. Überschreiben? (j/n): {Colors.ENDC}")
        if choice.lower() != 'j':
            print_warning("Bestehende .env-Datei wird beibehalten.")
            return
    
    # .env.example kopieren, falls vorhanden
    if env_example.exists():
        shutil.copy(env_example, env_file)
        
        # Benutzerabfrage für Datenbankverbindung
        print("\nDatenbank-Konfiguration:")
        db_host = input("  Datenbankhost [localhost]: ") or "localhost"
        db_port = input("  Datenbankport [5432]: ") or "5432"
        db_name = input("  Datenbankname [medicalspy]: ") or "medicalspy"
        db_user = input("  Datenbankbenutzer [postgres]: ") or "postgres"
        db_password = getpass.getpass("  Datenbankpasswort: ")
        
        # Generiere einen zufälligen Session-Secret
        import secrets
        session_secret = secrets.token_hex(32)
        
        # Ersetze Werte in .env-Datei
        with open(env_file, 'r', encoding='utf-8') as file:
            env_content = file.read()
        
        env_content = env_content.replace(
            "DATABASE_URL=postgresql://username:password@localhost:5432/medicalspy", 
            f"DATABASE_URL=postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )
        
        env_content = env_content.replace(
            "SESSION_SECRET=your_secure_session_key_here", 
            f"SESSION_SECRET={session_secret}"
        )
        
        with open(env_file, 'w', encoding='utf-8') as file:
            file.write(env_content)
        
        print_success(".env-Datei konfiguriert")
    else:
        print_error(".env.example nicht gefunden. Bitte erstellen Sie die .env-Datei manuell.")


def check_database():
    """Überprüft die Datenbankverbindung"""
    print_step("Überprüfe Datenbankverbindung... ")
    
    # Path zum Python in der virtuellen Umgebung
    if platform.system() == 'Windows':
        python_path = "venv\\Scripts\\python"
    else:
        python_path = "venv/bin/python"
    
    result = run_command(f"{python_path} db_tools.py --check", verbose=False, exit_on_error=False)
    
    if result and "Database connection successful" in result:
        print_success("Datenbankverbindung erfolgreich")
        return True
    else:
        print_error("Datenbankverbindung fehlgeschlagen")
        print_warning("Bitte überprüfen Sie die Datenbankeinstellungen in der .env-Datei")
        print_warning("Stellen Sie sicher, dass PostgreSQL läuft und die angegebene Datenbank existiert")
        return False


def setup_database():
    """Initialisiert die Datenbank und erstellt Testdaten"""
    print_step("Initialisiere Datenbank... ")
    
    # Path zum Python in der virtuellen Umgebung
    if platform.system() == 'Windows':
        python_path = "venv\\Scripts\\python"
    else:
        python_path = "venv/bin/python"
    
    # Datenbank initialisieren
    run_command(f"{python_path} db_tools.py --init")
    print_success("Datenbank initialisiert")
    
    # Testperson hinzufügen
    choice = input(f"{Colors.BLUE}Testperson zur Datenbank hinzufügen? (j/n): {Colors.ENDC}")
    if choice.lower() == 'j':
        run_command(f"{python_path} db_tools.py --add-sample")
        print_success("Testperson hinzugefügt")


def check_visual_studio_code():
    """Überprüft, ob Visual Studio Code installiert ist"""
    print_step("Überprüfe Visual Studio Code Installation... ")
    
    if platform.system() == 'Windows':
        result = run_command("where code", verbose=False, exit_on_error=False)
    else:
        result = run_command("which code", verbose=False, exit_on_error=False)
        
    if result:
        print_success("Visual Studio Code gefunden")
        return True
    else:
        print_warning("Visual Studio Code wurde nicht gefunden")
        print_warning("Sie können es von https://code.visualstudio.com/ herunterladen")
        return False


def create_vscode_startup_script():
    """Erstellt ein Startskript für VS Code mit voreingestellter virtueller Umgebung"""
    print_step("Erstelle VS Code Startskript... ")
    
    content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Dieses Skript startet VS Code mit aktivierter virtueller Umgebung
\"\"\"

import os
import subprocess
import platform

def run_command(command):
    subprocess.run(command, shell=True, check=True)

if __name__ == "__main__":
    # Virtuelle Umgebung aktivieren und VS Code starten
    if platform.system() == 'Windows':
        # Windows-Variante mit PowerShell
        command = "powershell -c \\"& {. ./venv/Scripts/Activate.ps1; code .}\\"" 
    else:
        # Linux/Mac-Variante
        command = "source ./venv/bin/activate && code ."
        
    try:
        run_command(command)
    except subprocess.CalledProcessError:
        print("Fehler beim Starten von VS Code. Stellen Sie sicher, dass VS Code installiert ist.")
"""
    
    with open("start_vscode.py", 'w', encoding='utf-8') as file:
        file.write(content)
    
    # Ausführbar machen (nur unter Unix)
    if platform.system() != 'Windows':
        run_command("chmod +x start_vscode.py")
    
    print_success("VS Code Startskript erstellt")


def print_final_instructions():
    """Gibt abschließende Anweisungen aus"""
    activate_cmd = activate_venv_command()
    
    print_section("Setup abgeschlossen")
    print(f"{Colors.GREEN}Die lokale Entwicklungsumgebung wurde erfolgreich eingerichtet!{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}Nächste Schritte:{Colors.ENDC}")
    print(f"1. Aktivieren Sie die virtuelle Umgebung:")
    print(f"   {Colors.BOLD}{activate_cmd}{Colors.ENDC}")
    print(f"2. Starten Sie die Anwendung:")
    print(f"   {Colors.BOLD}python run.py{Colors.ENDC}")
    print(f"3. Öffnen Sie Visual Studio Code (mit virtueller Umgebung):")
    print(f"   {Colors.BOLD}python start_vscode.py{Colors.ENDC}")
    
    print(f"\nFür detaillierte Informationen zur lokalen Entwicklung lesen Sie bitte:")
    print(f"{Colors.BOLD}LOCAL_DEVELOPMENT.md{Colors.ENDC}")


def main():
    """Hauptfunktion"""
    print_section("Medical Spytool - Setup der lokalen Entwicklungsumgebung")
    
    # Python-Version überprüfen
    if not check_python_version():
        sys.exit(1)
    
    # Virtuelle Umgebung erstellen
    create_virtual_env()
    
    # Abhängigkeiten installieren
    install_requirements()
    
    # Umgebungsvariablen konfigurieren
    configure_environment()
    
    # VS Code überprüfen und Startskript erstellen
    if check_visual_studio_code():
        create_vscode_startup_script()
    
    # Datenbank überprüfen und initialisieren
    db_connected = check_database()
    if db_connected:
        choice = input(f"{Colors.BLUE}Datenbank initialisieren? (j/n): {Colors.ENDC}")
        if choice.lower() == 'j':
            setup_database()
    
    # Abschließende Anweisungen
    print_final_instructions()


if __name__ == "__main__":
    main()