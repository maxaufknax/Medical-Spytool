"""
Modul für die Verwaltung von Suchprofilen

Enthält Funktionen zum Speichern, Laden und Verwalten von gespeicherten Suchprofilen, 
die Suchanfragen und Filtereinstellungen enthalten.
"""

import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Konstanten
SEARCH_PROFILES_DIR = "search_profiles"
PROFILE_FILE_EXTENSION = ".json"


def ensure_profiles_directory():
    """Stellt sicher, dass das Verzeichnis für Suchprofile existiert."""
    if not os.path.exists(SEARCH_PROFILES_DIR):
        os.makedirs(SEARCH_PROFILES_DIR)
        logger.info(f"Verzeichnis {SEARCH_PROFILES_DIR} für Suchprofile erstellt")


def save_search_profile(profile_name, search_params):
    """
    Speichert ein Suchprofil in einer JSON-Datei.
    
    Args:
        profile_name (str): Name des Profils
        search_params (dict): Die Suchparameter und Einstellungen
    
    Returns:
        bool: True wenn erfolgreich, False im Fehlerfall
    """
    ensure_profiles_directory()
    
    # Datumsobjekte für JSON serialisierbar machen
    if 'date_range' in search_params and search_params['date_range']:
        if 'start' in search_params['date_range'] and isinstance(search_params['date_range']['start'], datetime):
            search_params['date_range']['start'] = search_params['date_range']['start'].strftime('%Y-%m-%d')
            
        if 'end' in search_params['date_range'] and isinstance(search_params['date_range']['end'], datetime):
            search_params['date_range']['end'] = search_params['date_range']['end'].strftime('%Y-%m-%d')
    
    # Aktuelles Datum und Uhrzeit hinzufügen
    search_params['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Dateiname erstellen
    filename = os.path.join(SEARCH_PROFILES_DIR, f"{profile_name}{PROFILE_FILE_EXTENSION}")
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(search_params, f, ensure_ascii=False, indent=2)
        logger.info(f"Suchprofil '{profile_name}' erfolgreich gespeichert")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Speichern des Suchprofils '{profile_name}': {str(e)}")
        return False


def load_search_profile(profile_name):
    """
    Lädt ein Suchprofil aus einer JSON-Datei.
    
    Args:
        profile_name (str): Name des Profils
    
    Returns:
        dict: Die geladenen Suchparameter und Einstellungen oder None im Fehlerfall
    """
    ensure_profiles_directory()
    
    # Wenn die Dateiendung bereits angegeben wurde, nicht nochmal anhängen
    if not profile_name.endswith(PROFILE_FILE_EXTENSION):
        filename = os.path.join(SEARCH_PROFILES_DIR, f"{profile_name}{PROFILE_FILE_EXTENSION}")
    else:
        filename = os.path.join(SEARCH_PROFILES_DIR, profile_name)
    
    try:
        if not os.path.exists(filename):
            logger.warning(f"Suchprofil '{profile_name}' existiert nicht")
            return None
            
        with open(filename, 'r', encoding='utf-8') as f:
            search_params = json.load(f)
        
        # Datumsstrings in datetime-Objekte umwandeln
        if 'date_range' in search_params and search_params['date_range']:
            if 'start' in search_params['date_range'] and isinstance(search_params['date_range']['start'], str):
                search_params['date_range']['start'] = datetime.strptime(search_params['date_range']['start'], '%Y-%m-%d')
                
            if 'end' in search_params['date_range'] and isinstance(search_params['date_range']['end'], str):
                search_params['date_range']['end'] = datetime.strptime(search_params['date_range']['end'], '%Y-%m-%d')
        
        logger.info(f"Suchprofil '{profile_name}' erfolgreich geladen")
        return search_params
    except Exception as e:
        logger.error(f"Fehler beim Laden des Suchprofils '{profile_name}': {str(e)}")
        return None


def delete_search_profile(profile_name):
    """
    Löscht ein Suchprofil.
    
    Args:
        profile_name (str): Name des Profils
    
    Returns:
        bool: True wenn erfolgreich, False im Fehlerfall
    """
    # Wenn die Dateiendung bereits angegeben wurde, nicht nochmal anhängen
    if not profile_name.endswith(PROFILE_FILE_EXTENSION):
        filename = os.path.join(SEARCH_PROFILES_DIR, f"{profile_name}{PROFILE_FILE_EXTENSION}")
    else:
        filename = os.path.join(SEARCH_PROFILES_DIR, profile_name)
    
    try:
        if not os.path.exists(filename):
            logger.warning(f"Suchprofil '{profile_name}' existiert nicht")
            return False
            
        os.remove(filename)
        logger.info(f"Suchprofil '{profile_name}' erfolgreich gelöscht")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Suchprofils '{profile_name}': {str(e)}")
        return False


def get_all_search_profiles():
    """
    Gibt eine Liste aller verfügbaren Suchprofile zurück.
    
    Returns:
        list: Liste der Profilnamen
    """
    ensure_profiles_directory()
    
    try:
        profiles = []
        for filename in os.listdir(SEARCH_PROFILES_DIR):
            if filename.endswith(PROFILE_FILE_EXTENSION):
                profile_name = filename.replace(PROFILE_FILE_EXTENSION, '')
                
                # Metadaten laden
                try:
                    with open(os.path.join(SEARCH_PROFILES_DIR, filename), 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                        
                    # Profil mit Metadaten hinzufügen
                    profile_info = {
                        'name': profile_name,
                        'created_at': profile_data.get('created_at', 'Unbekannt'),
                        'database': profile_data.get('database', 'Unbekannt'),
                        'search_term': profile_data.get('search_term', ''),
                        'person_name': profile_data.get('person_name', '')
                    }
                    profiles.append(profile_info)
                except Exception as e:
                    logger.warning(f"Fehler beim Laden der Metadaten für '{filename}': {str(e)}")
                    profiles.append({'name': profile_name, 'created_at': 'Unbekannt'})
                    
        return sorted(profiles, key=lambda p: p.get('created_at', ''), reverse=True)
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Suchprofile: {str(e)}")
        return []