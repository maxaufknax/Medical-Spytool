"""
Configuration Manager for Medical Spytool.

This module handles loading, saving, and managing the application's
configuration settings. It uses a default configuration (`assets/default_config.json`)
as a base, which is overridden by a user-specific configuration
(`medicalspytool_config.json`) stored in a writable location.

Key functionalities include:
- Initializing user configuration from defaults if it doesn't exist.
- Merging user settings over default settings.
- Saving configuration changes securely using temporary files and backups.
- Ensuring necessary application directories (for output, logs, person lists)
  are created at startup.
"""
import os
import json
import logging
import tempfile
from utils.path_manager import get_resource_path, get_writeable_path

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self):
        self.config = {}
        self.load_config()
        
    def load_config(self):
        """
        Lade die Konfiguration aus den Config-Dateien.
        Versucht zuerst die Benutzer-Konfiguration zu laden, 
        und fällt dann auf die Standard-Konfiguration zurück, falls nötig.
        """
        # Pfade für Konfigurations-Dateien
        user_config_path = get_writeable_path('medicalspytool_config.json')
        default_config_path = get_resource_path('assets/default_config.json')
        
        # Starte mit einer leeren Konfiguration
        self.config = {}
        
        # Lade Standard-Konfiguration
        try:
            with open(default_config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"Standard-Konfiguration aus {default_config_path} geladen")
        except FileNotFoundError:
            logger.error(f"Standard-Konfigurationsdatei nicht gefunden: {default_config_path}")
            # Erstelle minimal notwendige Standardkonfiguration
            self.config = {
                "output_path": get_writeable_path("output"),
                "person_list_path": get_writeable_path("person_lists"),
                "unique_filenames": True,
                "default_database": "PubMed",
                "search_timeout": 30,
                "api_keys": {},
                "enable_logging": True
            }
            logger.info("Minimale Standardkonfiguration erstellt")
            # Removed attempt to write back to default_config_path as it should be read-only resource.
            # If default_config.json is missing from assets, it's a build/packaging issue.
                
        except json.JSONDecodeError as e:
            logger.error(f"Fehler beim Parsen der Standard-Konfiguration ({default_config_path}): {str(e)}")
            # Erstelle minimal notwendige Standardkonfiguration
            self.config = {
                "output_path": get_writeable_path("output"),
                "person_list_path": get_writeable_path("person_lists"),
                "unique_filenames": True,
                "default_database": "PubMed",
                "search_timeout": 30,
                "api_keys": {},
                "enable_logging": True
            }
            logger.info("Minimale Standardkonfiguration erstellt wegen JSONDecodeError")
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Laden der Standard-Konfiguration: {str(e)}", exc_info=True)
            # Erstelle minimal notwendige Standardkonfiguration
            self.config = {
                "output_path": get_writeable_path("output"),
                "person_list_path": get_writeable_path("person_lists"),
                "unique_filenames": True,
                "default_database": "PubMed",
                "search_timeout": 30,
                "api_keys": {},
                "enable_logging": True
            }
            logger.info("Minimale Standardkonfiguration erstellt wegen unerwarteten Fehlers")
        
        # Überschreibe mit Benutzer-Konfiguration, falls vorhanden
        if os.path.exists(user_config_path):
            try:
                with open(user_config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                logger.info(f"Benutzer-Konfiguration aus {user_config_path} geladen")
            except json.JSONDecodeError as e:
                logger.error(f"Fehler beim Parsen der Benutzer-Konfiguration: {str(e)}")
                logger.info("Verwende Standardkonfiguration stattdessen")
                # Erstelle Backup der defekten Konfiguration
                try:
                    backup_path = f"{user_config_path}.backup"
                    if os.path.exists(user_config_path):
                        with open(user_config_path, 'r') as src, open(backup_path, 'w') as dst:
                            dst.write(src.read())
                        logger.info(f"Backup der defekten Konfiguration erstellt: {backup_path}")
                except Exception as backup_e:
                    logger.error(f"Fehler beim Erstellen eines Backups der defekten Konfiguration: {str(backup_e)}")
            except PermissionError as e:
                logger.error(f"Keine Berechtigung zum Lesen der Benutzer-Konfiguration: {str(e)}")
            except Exception as e:
                logger.error(f"Unerwarteter Fehler beim Laden der Benutzer-Konfiguration: {str(e)}", exc_info=True)
        else:
            logger.info(f"Keine Benutzer-Konfigurationsdatei gefunden unter {user_config_path}")
            # Erstelle initiale Benutzer-Konfiguration
            try:
                # Ensure parent directory exists
                os.makedirs(os.path.dirname(user_config_path), exist_ok=True)
                with open(user_config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=4)
                logger.info(f"Initiale Benutzer-Konfiguration erstellt unter {user_config_path}")
            except Exception as e:
                logger.error(f"Fehler beim Erstellen der initialen Benutzer-Konfiguration: {str(e)}")
                
    def get_config(self):
        """Gibt die aktuelle Konfiguration zurück."""
        return self.config
        
    def save_config(self, config):
        """
        Speichert die Konfiguration.
        
        Args:
            config (dict): Die zu speichernde Konfiguration
        
        Returns:
            bool: True wenn erfolgreich, sonst False
        """
        self.config = config
        user_config_path = get_writeable_path('medicalspytool_config.json')
        
        try:
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(user_config_path), exist_ok=True)
            
            # Temporäre Datei erstellen, um atomic write sicherzustellen
            temp_fd, temp_path = tempfile.mkstemp(prefix="medicalspytool_", suffix=".tmp")
            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=4)
                
                # Wenn temporäre Datei erfolgreich erstellt wurde, ersetze die aktuelle Datei
                # Erstelle Backup der alten Konfiguration, falls vorhanden
                if os.path.exists(user_config_path):
                    backup_path = f"{user_config_path}.bak"
                    try:
                        with open(user_config_path, 'r', encoding='utf-8') as src, open(backup_path, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
                    except Exception as e:
                        logger.warning(f"Konnte kein Backup der alten Konfiguration erstellen: {str(e)}")
                
                # Ersetze die aktuelle Datei
                if os.path.exists(user_config_path):
                    os.replace(temp_path, user_config_path)
                else:
                    os.rename(temp_path, user_config_path)
                
                logger.info(f"Konfiguration erfolgreich gespeichert unter {user_config_path}")
                return True
            except Exception as e:
                # Clean up the temp file if something went wrong
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass
                raise e
                
        except PermissionError as e:
            logger.error(f"Keine Berechtigung zum Speichern der Konfiguration: {str(e)}")
            return False
        except OSError as e:
            logger.error(f"Betriebssystem-Fehler beim Speichern der Konfiguration: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Speichern der Konfiguration: {str(e)}", exc_info=True)
            return False

# Standalone-Funktionen, die in main.py importiert werden
def load_settings():
    """
    Load settings from configuration files.
    Returns a dictionary containing all settings.
    """
    config_manager = ConfigManager()
    return config_manager.get_config()

def save_settings(config):
    """
    Save settings to the configuration file.
    
    Args:
        config (dict): Configuration dictionary to save
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    config_manager = ConfigManager()
    return config_manager.save_config(config)

def ensure_directories(config):
    """
    Ensure that all required directories in the config exist.
    Creates them if they don't exist.
    
    Args:
        config (dict): Configuration dictionary containing paths
    """
    try:
        # Convert relative paths to absolute writeable paths if needed
        if 'output_path' in config and not os.path.isabs(config['output_path']):
            config['output_path'] = get_writeable_path(config['output_path'])
            
        if 'person_list_path' in config and not os.path.isabs(config['person_list_path']):
            config['person_list_path'] = get_writeable_path(config['person_list_path'])
        
        # Create output directory if it doesn't exist
        output_path = config.get('output_path', get_writeable_path('output'))
        if output_path:
            try:
                os.makedirs(output_path, exist_ok=True)
                logger.info(f"Ausgabe-Verzeichnis sichergestellt: {output_path}")
            except PermissionError as e:
                logger.error(f"Keine Berechtigung zum Erstellen des Ausgabe-Verzeichnisses {output_path}: {str(e)}")
                # Try to use a fallback directory in user's temp folder
                fallback_path = os.path.join(tempfile.gettempdir(), "MedicalSpyTool", "output")
                try:
                    os.makedirs(fallback_path, exist_ok=True)
                    config['output_path'] = fallback_path
                    logger.warning(f"Fallback Ausgabe-Verzeichnis verwendet: {fallback_path}")
                except Exception as fallback_e:
                    logger.error(f"Auch Fallback-Verzeichnis konnte nicht erstellt werden: {str(fallback_e)}")
            except OSError as e:
                logger.error(f"Betriebssystem-Fehler beim Erstellen des Ausgabe-Verzeichnisses {output_path}: {str(e)}")
        
        # Create person list directory if it doesn't exist
        person_list_path = config.get('person_list_path', get_writeable_path('person_lists'))
        if person_list_path:
            try:
                os.makedirs(person_list_path, exist_ok=True)
                logger.info(f"Personenlisten-Verzeichnis sichergestellt: {person_list_path}")
                
                # Create default persons.json if it doesn't exist
                persons_file = os.path.join(person_list_path, 'persons.json')
                if not os.path.exists(persons_file):
                    try:
                        with open(persons_file, 'w', encoding='utf-8') as f:
                            json.dump([], f, indent=4) # Create as an empty list
                        logger.info(f"Leere Personenliste erstellt: {persons_file}")
                    except Exception as pf_e:
                        logger.error(f"Konnte keine leere Personenliste erstellen: {str(pf_e)}")
                        
            except PermissionError as e:
                logger.error(f"Keine Berechtigung zum Erstellen des Personenlisten-Verzeichnisses {person_list_path}: {str(e)}")
                # Try to use a fallback directory in user's temp folder
                fallback_path = os.path.join(tempfile.gettempdir(), "MedicalSpyTool", "person_lists")
                try:
                    os.makedirs(fallback_path, exist_ok=True)
                    config['person_list_path'] = fallback_path
                    logger.warning(f"Fallback Personenlisten-Verzeichnis verwendet: {fallback_path}")
                except Exception as fallback_e:
                    logger.error(f"Auch Fallback-Verzeichnis konnte nicht erstellt werden: {str(fallback_e)}")
            except OSError as e:
                logger.error(f"Betriebssystem-Fehler beim Erstellen des Personenlisten-Verzeichnisses {person_list_path}: {str(e)}")
        
        # Create logs directory if logging is enabled
        if config.get('enable_logging', True):
            logs_path = get_writeable_path('logs')
            try:
                os.makedirs(logs_path, exist_ok=True)
                logger.info(f"Logs-Verzeichnis sichergestellt: {logs_path}")
            except Exception as e:
                logger.warning(f"Konnte Logs-Verzeichnis nicht erstellen: {str(e)}")
        
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Erstellen der Verzeichnisse: {str(e)}", exc_info=True)
        
    # Return the potentially modified config with fallback paths
    return config