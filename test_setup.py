#!/usr/bin/env python3
"""
Test Script für MedicalSpyTool
Überprüft die wichtigsten Funktionen der Anwendung
"""

import sys
import os
import importlib
import time
import requests
from pathlib import Path

def test_imports():
    """Teste ob alle wichtigen Module importiert werden können"""
    print("🔍 Teste Module-Importe...")
    
    modules_to_test = [
        'flask',
        'requests', 
        'pandas',
        'openpyxl',
        'bs4',
        'database_connectors',
        'utils.config_manager',
        'utils.path_manager'
    ]
    
    failed_imports = []
    
    for module in modules_to_test:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n⚠️  {len(failed_imports)} Module konnten nicht importiert werden")
        return False
    else:
        print("✅ Alle Module erfolgreich importiert")
        return True

def test_directories():
    """Teste ob alle erforderlichen Verzeichnisse existieren"""
    print("\n🔍 Teste Verzeichnisstruktur...")
    
    required_dirs = [
        'templates',
        'static',
        'database_connectors', 
        'utils',
        'output',
        'logs',
        'person_lists'
    ]
    
    missing_dirs = []
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"  ✅ {directory}/")
        else:
            print(f"  ❌ {directory}/ (fehlt)")
            missing_dirs.append(directory)
    
    if missing_dirs:
        print(f"\n⚠️  {len(missing_dirs)} Verzeichnisse fehlen")
        return False
    else:
        print("✅ Alle Verzeichnisse vorhanden")
        return True

def test_config():
    """Teste die Konfiguration"""
    print("\n🔍 Teste Konfiguration...")
    
    try:
        from utils.config_manager import load_settings
        config = load_settings()
        print(f"  ✅ Konfiguration geladen")
        print(f"     - Output Path: {config.get('output_path', 'Nicht gesetzt')}")
        print(f"     - Default Database: {config.get('default_database', 'Nicht gesetzt')}")
        return True
    except Exception as e:
        print(f"  ❌ Konfigurationsfehler: {e}")
        return False

def test_database_connectors():
    """Teste die Datenbankverbindungen"""
    print("\n🔍 Teste Datenbankverbindungen...")
    
    try:
        from database_connectors import PubMedConnector, DNBConnector
        
        # Teste PubMed Connector
        pubmed = PubMedConnector()
        print(f"  ✅ PubMed Connector erstellt")
        
        # Teste DNB Connector  
        dnb = DNBConnector()
        print(f"  ✅ DNB Connector erstellt")
        
        return True
    except Exception as e:
        print(f"  ❌ Datenbankverbindungsfehler: {e}")
        return False

def test_flask_app():
    """Teste die Flask-Anwendung"""
    print("\n🔍 Teste Flask-Anwendung...")
    
    try:
        # Importiere die Flask App
        sys.path.insert(0, '.')
        from main import app
        
        print("  ✅ Flask App importiert")
        
        # Teste ob wichtige Routes existieren
        with app.test_client() as client:
            routes_to_test = [
                '/',
                '/search', 
                '/persons',
                '/settings'
            ]
            
            for route in routes_to_test:
                try:
                    response = client.get(route)
                    if response.status_code == 200:
                        print(f"  ✅ Route {route} funktioniert")
                    else:
                        print(f"  ⚠️  Route {route} Status: {response.status_code}")
                except Exception as e:
                    print(f"  ❌ Route {route} Fehler: {e}")
        
        return True
    except Exception as e:
        print(f"  ❌ Flask App Fehler: {e}")
        return False

def main():
    """Führe alle Tests aus"""
    print("🧪 MedicalSpyTool Funktionstest")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_directories,
        test_config,
        test_database_connectors,
        test_flask_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test fehlgeschlagen: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Testergebnisse: {passed}/{total} Tests bestanden")
    
    if passed == total:
        print("🎉 Alle Tests erfolgreich! Die Anwendung ist bereit.")
        return 0
    else:
        print("⚠️  Einige Tests sind fehlgeschlagen. Überprüfen Sie die Fehler oben.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
