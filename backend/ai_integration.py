"""
KI-Integration für MedicalSpy

Dieses Modul bietet Funktionen zur Integration von KI-Diensten in die MedicalSpy-Anwendung,
um natürliche Sprachanfragen zu verarbeiten und in strukturierte Suchanfragen umzuwandeln.
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any, Tuple

import openai
from openai.types.chat import ChatCompletion

# Konfiguration
logger = logging.getLogger("MedicalSpy")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

class AIIntegration:
    """KI-Integrationsklasse für MedicalSpy"""
    
    def __init__(self):
        """Initialisiert die KI-Integration"""
        api_key = os.environ.get("OPENAI_API_KEY")  # Aktuelle Umgebungsvariable verwenden
        self.is_configured = api_key is not None
        if self.is_configured:
            openai.api_key = api_key
            logger.info("KI-Integration wurde initialisiert")
        else:
            logger.warning("KI-Integration konnte nicht initialisiert werden: API-Schlüssel fehlt")
    
    def process_query(self, query_text: str) -> Dict[str, Any]:
        """
        Verarbeitet eine natürliche Sprachanfrage und extrahiert strukturierte Suchparameter
        
        Args:
            query_text (str): Die natürliche Sprachanfrage des Benutzers
            
        Returns:
            Dict[str, Any]: Ein Dictionary mit extrahierten Suchparametern
        """
        if not self.is_configured:
            logger.warning("KI-Integration ist nicht konfiguriert")
            return {
                "success": False,
                "error": "KI-Integration ist nicht konfiguriert. Bitte OPENAI_API_KEY setzen."
            }
        
        try:
            # Systemprompt für die KI
            system_prompt = """
            Du bist ein Assistent für ein medizinisches Suchsystem. Deine Aufgabe ist es, 
            natürliche Sprachanfragen in strukturierte Suchparameter umzuwandeln.
            Extrahiere folgende Informationen aus der Anfrage des Benutzers:
            - search_term: Hauptsuchbegriff(e)
            - person_name: Name einer Person, falls erwähnt
            - additional_terms: Zusätzliche Suchbegriffe
            - date_range: Falls ein Datumsbereich erwähnt wird (z.B. "letztes Jahr", "zwischen 2019 und 2022")
            - database: Die zu durchsuchende Datenbank, falls explizit erwähnt ("PubMed" oder "Deutsche Nationalbibliothek")
            - language: Bevorzugte Sprache der Ergebnisse, falls erwähnt
            
            Antworte NUR mit einem JSON-Objekt.
            """
            
            # Anfrage an OpenAI API
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query_text}
                ],
                temperature=0.1
            )
            
            # Extrahiere die Antwort
            result = response.choices[0].message.content
            
            # Versuche, die Antwort als JSON zu parsen
            try:
                if result is not None:
                    # Explizit zu String konvertieren
                    result_str = str(result)
                    parsed_result = json.loads(result_str)
                    return {
                        "success": True, 
                        "parameters": parsed_result
                    }
                else:
                    logger.error("KI-Antwort ist None")
                    return {
                        "success": False,
                        "error": "Keine Antwort von der KI erhalten"
                    }
            except json.JSONDecodeError as e:
                logger.error(f"Fehler beim Parsen der KI-Antwort: {str(e)}")
                return {
                    "success": False,
                    "error": "Fehler beim Verarbeiten der KI-Antwort",
                    "raw_response": result
                }
                
        except Exception as e:
            logger.error(f"Fehler bei der KI-Verarbeitung: {str(e)}")
            return {
                "success": False,
                "error": f"Fehler bei der KI-Verarbeitung: {str(e)}"
            }
    
    def analyze_results(self, search_results: List[Dict[str, Any]], user_query: str) -> Dict[str, Any]:
        """
        Analysiert Suchergebnisse mit Hilfe der KI und gibt eine Zusammenfassung zurück
        
        Args:
            search_results (List[Dict[str, Any]]): Liste der Suchergebnisse
            user_query (str): Die ursprüngliche Benutzeranfrage
            
        Returns:
            Dict[str, Any]: Ein Dictionary mit der KI-Analyse
        """
        if not self.is_configured:
            logger.warning("KI-Integration ist nicht konfiguriert")
            return {
                "success": False,
                "error": "KI-Integration ist nicht konfiguriert. Bitte OPENAI_API_KEY setzen."
            }
        
        try:
            # Begrenze die Anzahl der Ergebnisse, um das Kontextfenster nicht zu überschreiten
            limited_results = search_results[:20] if len(search_results) > 20 else search_results
            
            # Konvertiere die Ergebnisse in einen lesbaren Text
            results_text = json.dumps(limited_results, indent=2, ensure_ascii=False)
            
            # Systemprompt für die KI
            system_prompt = """
            Du bist ein Assistent für medizinische Literaturrecherche. Analysiere die folgenden
            Suchergebnisse basierend auf der Anfrage des Benutzers. Gib eine Zusammenfassung der
            wichtigsten Erkenntnisse, identifiziere Muster und hebe relevante Informationen hervor.
            
            Strukturiere deine Antwort in folgende Abschnitte:
            1. Zusammenfassung der Ergebnisse
            2. Wichtigste Erkenntnisse
            3. Identifizierte Muster oder Trends
            4. Empfehlungen für weitere Recherchen
            
            Halte deine Antwort knapp und fokussiert.
            """
            
            # Anfrage an OpenAI API
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo-16k",  # Größeres Modell für längere Kontexte
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Benutzeranfrage: {user_query}\n\nSuchergebnisse:\n{results_text}"}
                ],
                temperature=0.7
            )
            
            # Extrahiere die Antwort
            result = response.choices[0].message.content
            
            return {
                "success": True,
                "analysis": result
            }
                
        except Exception as e:
            logger.error(f"Fehler bei der KI-Analyse: {str(e)}")
            return {
                "success": False,
                "error": f"Fehler bei der KI-Analyse: {str(e)}"
            }

# Singleton-Instanz
ai_integration = AIIntegration()

def get_ai_integration() -> AIIntegration:
    """Gibt die Singleton-Instanz der KI-Integration zurück"""
    return ai_integration