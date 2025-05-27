"""
Test Core Functions - Medical SpyTool

Dieses Skript führt grundlegende Tests für die Kernfunktionen des Medical SpyTools durch.
Es prüft:
- Konfigurationsmanagement
- Datenbankverbindungen
- Datei- und Verzeichniszugriffe

Verwendung:
    python test_core_functions.py
"""

import os
import sys
import json
import logging
import tempfile
import unittest
from datetime import datetime
from unittest import mock

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Füge das Stammverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Importiere die benötigten Module
try:
    from utils.config_manager import ConfigManager, load_settings, save_settings, ensure_directories
    from utils.path_manager import get_resource_path
    from database_connectors.base_connector import DatabaseConnector
    from database_connectors import DATABASE_CONNECTORS
    logger.info("Module erfolgreich importiert.")
except ImportError as e:
    logger.error(f"Fehler beim Importieren der Module: {e}")
    sys.exit(1)

class TestConfigManager(unittest.TestCase):
    """Testfälle für das Konfigurationsmanagement"""
    
    def setUp(self):
        """Testumgebung einrichten"""
        # Erstelle temporäre Datei für Tests
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = self.temp_dir.name
        self.config_file = os.path.join(self.temp_path, 'test_config.json')
        
        # Minimale Testkonfiguration
        self.test_config = {
            "output_path": "./output",
            "person_list_path": "./person_lists",
            "unique_filenames": True,
            "default_database": "PubMed"
        }
        
        # Schreibe die Testkonfiguration
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_config, f, indent=4)
            
    def tearDown(self):
        """Aufräumen nach den Tests"""
        self.temp_dir.cleanup()
    
    def test_config_load(self):
        """Testet das Laden einer Konfiguration"""
        # Mocke den get_resource_path, um auf unsere Testdatei zu verweisen
        with mock.patch('utils.config_manager.get_resource_path', return_value=self.config_file):
            config_manager = ConfigManager()
            loaded_config = config_manager.get_config()
            
            # Überprüfe, dass die Konfiguration korrekt geladen wurde
            self.assertEqual(loaded_config["output_path"], "./output")
            self.assertEqual(loaded_config["person_list_path"], "./person_lists")
            self.assertTrue(loaded_config["unique_filenames"])
            self.assertEqual(loaded_config["default_database"], "PubMed")
    
    def test_config_save(self):
        """Testet das Speichern einer Konfiguration"""
        # Mocke den get_resource_path, um auf unsere Testdatei zu verweisen
        with mock.patch('utils.config_manager.get_resource_path', return_value=self.config_file):
            config_manager = ConfigManager()
            
            # Ändere Konfiguration
            config = config_manager.get_config()
            config["output_path"] = "./new_output"
            config["default_database"] = "DNB"
            
            # Speichere Konfiguration
            result = config_manager.save_config(config)
            self.assertTrue(result, "Speichern der Konfiguration sollte erfolgreich sein")
            
            # Lade Konfiguration neu und prüfe Änderungen
            new_config_manager = ConfigManager()
            loaded_config = new_config_manager.get_config()
            self.assertEqual(loaded_config["output_path"], "./new_output")
            self.assertEqual(loaded_config["default_database"], "DNB")
    
    def test_ensure_directories(self):
        """Testet die Funktion zum Erstellen der benötigten Verzeichnisse"""
        config = {
            "output_path": os.path.join(self.temp_path, "output"),
            "person_list_path": os.path.join(self.temp_path, "person_lists")
        }
        
        # Stelle sicher, dass die Verzeichnisse nicht existieren
        self.assertFalse(os.path.exists(config["output_path"]))
        self.assertFalse(os.path.exists(config["person_list_path"]))
        
        # Führe ensure_directories aus
        ensure_directories(config)
        
        # Prüfe, dass die Verzeichnisse erstellt wurden
        self.assertTrue(os.path.exists(config["output_path"]))
        self.assertTrue(os.path.exists(config["person_list_path"]))


class TestDatabaseConnectors(unittest.TestCase):
    """Testfälle für die Datenbankverbindungen"""
    
    def test_base_connector(self):
        """Testet die Basisklasse für Datenbank-Connectors"""
        # Erstelle einen einfachen Connector
        connector = DatabaseConnector()
        
        # Teste Standardmethoden
        self.assertEqual(connector.name, "Base")
        self.assertEqual(connector.construct_query("test"), "test")
        self.assertEqual(connector.get_citation_count("123"), "N/A")
        self.assertEqual(connector.search("test"), [])
        
    def test_available_connectors(self):
        """Testet, dass alle erwarteten Connector-Klassen verfügbar sind"""
        # Überprüfe, ob die wichtigsten Connector-Klassen existieren
        self.assertIn("PubMed", DATABASE_CONNECTORS)
        self.assertIn("DNB", DATABASE_CONNECTORS)
        
        # Erstelle Instanzen für jeden verfügbaren Connector und prüfe Basismethoden
        for connector_name, connector_class in DATABASE_CONNECTORS.items():
            connector = connector_class()
            self.assertEqual(connector.name, connector_name)
            self.assertTrue(hasattr(connector, "search"))
            self.assertTrue(hasattr(connector, "construct_query"))
            self.assertTrue(hasattr(connector, "parse_results"))


class TestPathManager(unittest.TestCase):
    """Testfälle für den Pfad-Manager"""
    
    def test_get_resource_path(self):
        """Testet die Funktion zum Abrufen von Ressourcenpfaden"""
        # Erwarteter Pfad basierend auf der aktuellen Umgebung
        expected_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_path"))
        
        # Tatsächlicher Pfad aus der Funktion
        actual_path = get_resource_path("test_path")
        
        # In Entwicklungsumgebung sollte der Pfad relativ zum aktuellen Verzeichnis sein
        self.assertEqual(os.path.normpath(actual_path), os.path.normpath(expected_path))


if __name__ == "__main__":
    print("Starte Testläufe für Medical SpyTool Kernfunktionen...")
    unittest.main(verbosity=2)