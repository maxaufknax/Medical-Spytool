"""
API Key Manager

Dieses Modul stellt Funktionen für die Verwaltung und Validierung von API-Keys bereit.
Es bietet eine zentrale Stelle für API-Key-Validierungen mit Timeout-Handling
und Caching von Validierungsergebnissen.
"""

import concurrent.futures
import logging
import time
from functools import lru_cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Constants
DEFAULT_VALIDATION_TIMEOUT = 5  # Sekunden
API_VALIDATION_CACHE_TIMEOUT = 3600  # Sekunden (1 Stunde)

# Cache für Validierungsergebnisse
validation_cache = {}

def validate_api_key(connector, api_key, timeout=DEFAULT_VALIDATION_TIMEOUT):
    """
    Validiert einen API-Key mit dem angegebenen Connector.
    
    Args:
        connector: Datenbank-Connector-Instanz
        api_key (str): Der zu validierende API-Key
        timeout (int): Timeout in Sekunden
        
    Returns:
        tuple: (bool, str) - (is_valid, message)
    """
    # Wenn kein API-Key angegeben wurde
    if not api_key:
        if connector.requires_api_key:
            return False, "Kein API-Key angegeben, aber für diese Datenbank erforderlich"
        else:
            return True, "Diese Datenbank erfordert keinen API-Key"
    
    # Prüfe Cache
    cache_key = f"{connector.name}:{api_key}"
    if cache_key in validation_cache:
        timestamp, is_valid, message = validation_cache[cache_key]
        if datetime.now() - timestamp < timedelta(seconds=API_VALIDATION_CACHE_TIMEOUT):
            logger.debug(f"Verwende gecachtes Validierungsergebnis für {connector.name}")
            return is_valid, message
    
    # Prüfe, ob die validate_api_key-Methode implementiert ist
    if not hasattr(connector, 'validate_api_key') or not callable(connector.validate_api_key):
        result = (True, "API-Key angenommen (keine Validierung verfügbar)")
        validation_cache[cache_key] = (datetime.now(), *result)
        return result
        
    # Führe Validierung mit Timeout aus
    try:
        def validation_task():
            try:
                return connector.validate_api_key(), "API-Key ist gültig"
            except Exception as e:
                logger.error(f"Fehler bei der API-Key-Validierung für {connector.name}: {str(e)}")
                return False, f"Fehler bei der Validierung: {str(e)}"
                
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(validation_task)
            try:
                is_valid, message = future.result(timeout=timeout)
                if not is_valid:
                    message = "API-Key ist ungültig"
                result = (is_valid, message)
                validation_cache[cache_key] = (datetime.now(), *result)
                return result
            except concurrent.futures.TimeoutError:
                logger.warning(f"Zeitüberschreitung bei der API-Key-Validierung für {connector.name} nach {timeout} Sekunden")
                result = (False, f"Zeitüberschreitung bei der Validierung nach {timeout} Sekunden")
                validation_cache[cache_key] = (datetime.now(), *result)
                return result
                
    except Exception as e:
        logger.error(f"Unerwarteter Fehler bei der API-Key-Validierung für {connector.name}: {str(e)}")
        result = (False, f"Fehler bei der Validierung: {str(e)}")
        validation_cache[cache_key] = (datetime.now(), *result)
        return result

def clear_validation_cache(connector_name=None, api_key=None):
    """
    Löscht den Validierungs-Cache für einen bestimmten Connector oder API-Key,
    oder den gesamten Cache, wenn keine Parameter angegeben sind.
    
    Args:
        connector_name (str, optional): Name des Connectors
        api_key (str, optional): Zu löschender API-Key
    """
    global validation_cache
    
    if connector_name and api_key:
        cache_key = f"{connector_name}:{api_key}"
        if cache_key in validation_cache:
            del validation_cache[cache_key]
            logger.debug(f"Cache gelöscht für {cache_key}")
    elif connector_name:
        # Lösche alle Einträge für diesen Connector
        keys_to_delete = [k for k in validation_cache.keys() if k.startswith(f"{connector_name}:")]
        for key in keys_to_delete:
            del validation_cache[key]
        logger.debug(f"Cache gelöscht für Connector {connector_name}")
    else:
        # Lösche gesamten Cache
        validation_cache = {}
        logger.debug("Gesamter Validierungs-Cache gelöscht")

def get_connector_status(connectors, config):
    """
    Prüft den Status mehrerer Datenbankverbindungen.
    
    Args:
        connectors (dict): Dictionary mit Connector-Klassen
        config (dict): Konfiguration mit API-Keys
        
    Returns:
        dict: Status für jeden Connector
    """
    results = {}
    
    for name, connector_class in connectors.items():
        try:
            # API-Key für diesen Connector aus der Konfiguration holen
            api_key = config.get(f"{name.lower()}_api_key", "")
            
            # Connector instanziieren
            connector = connector_class(api_key=api_key, settings=config)
            
            # Validiere API-Key
            is_valid, message = validate_api_key(connector, api_key)
            
            # Speichere Ergebnis
            results[name] = {
                "name": name,
                "status": "Bereit" if is_valid else "Fehler",
                "message": message,
                "requires_key": connector.requires_api_key,
                "has_key": bool(api_key)
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Prüfen des Connectors {name}: {str(e)}")
            results[name] = {
                "name": name,
                "status": "Fehler",
                "message": f"Fehler beim Initialisieren: {str(e)}",
                "requires_key": True,  # Vorsichtshalber
                "has_key": bool(api_key if 'api_key' in locals() else "")
            }
    
    return results