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
# API-Schlüssel wird dynamisch aus der Umgebung oder den Einstellungen geholt

class AIIntegration:
    """KI-Integrationsklasse für MedicalSpy"""
    
    def __init__(self):
        """Initialisiert die KI-Integration"""
        self.update_api_key()
        
    def update_api_key(self):
        """Aktualisiert den API-Schlüssel aus allen verfügbaren Quellen"""
        from flask import session
        
        # Schlüssel aus verschiedenen Quellen versuchen
        api_key = None
        
        # 1. Aus Umgebungsvariablen
        env_key = os.environ.get("OPENAI_API_KEY")
        if env_key and len(env_key.strip()) > 0:
            api_key = env_key
            logger.debug("API-Schlüssel aus Umgebungsvariable gefunden")
        
        # 2. Aus Session-Einstellungen (wenn nicht schon in Umgebungsvariablen gefunden)
        if not api_key:
            try:
                settings = session.get('settings', {})
                if settings and 'openai_api_key' in settings and settings['openai_api_key']:
                    api_key = settings['openai_api_key']
                    logger.debug("API-Schlüssel aus Session-Einstellungen gefunden")
            except Exception as e:
                # Session könnte nicht verfügbar sein, wenn außerhalb eines Anfrage-Kontexts
                logger.debug(f"Konnte Session nicht lesen: {str(e)}")
        
        # Status aktualisieren
        self.is_configured = api_key is not None and len(str(api_key).strip()) > 0
        
        # OpenAI-Client mit dem Schlüssel konfigurieren
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
        # Sicherstellen, dass der API-Schlüssel aktuell ist
        self.update_api_key()
        
        if not self.is_configured:
            logger.warning("KI-Integration ist nicht konfiguriert")
            return {
                "success": False,
                "error": "KI-Integration ist nicht konfiguriert. Bitte einen OpenAI API-Schlüssel in den Einstellungen setzen."
            }
        
        try:
            # Ausführliche Anleitung als Systemprompt für die KI
            system_prompt = """
            Du bist ein Assistent für ein medizinisches und wissenschaftliches Suchsystem. 
            Deine Aufgabe ist es, natürliche Sprachanfragen präzise in strukturierte Suchparameter umzuwandeln.
            
            Extrahiere folgende Informationen aus der Anfrage des Benutzers:
            
            - search_term (String): Hauptsuchbegriff(e) für die Suche. Extrahiere die wichtigsten medizinischen oder 
              wissenschaftlichen Begriffe. Bei mehreren Begriffen verbinde sie mit UND/AND-Logik.
            
            - person_name (String): Name des Autors oder der Person, nach der gesucht wird. 
              Gib den vollständigen Namen an, wenn möglich mit Nachnamen zuerst.
            
            - additional_terms (String): Zusätzliche Suchbegriffe oder Einschränkungen, die den Hauptsuchbegriff ergänzen.
              Diese sollten getrennt vom Hauptsuchbegriff sein.
            
            - date_range (String): Zeitraum für die Suche im Format "YYYY-YYYY" oder einen beschreibenden Text wie 
              "letzten 5 Jahre", "seit 2020" oder "zwischen 2018 und 2022".
            
            - database (String): Die zu durchsuchende Datenbank, falls explizit erwähnt. Gültige Werte sind "PubMed" oder 
              "Deutsche Nationalbibliothek" (auch "DNB"). Wenn keine genannt wird, lasse dieses Feld leer.
            
            - language (String): Die bevorzugte Sprache der Ergebnisse. Gib einen Sprachcode oder den vollen Namen 
              der Sprache an (z.B. "Deutsch", "English").
            
            Wichtig:
            - Behalte die Originalterminologie des Nutzers bei.
            - Füge keine Informationen hinzu, die nicht in der Anfrage enthalten sind.
            - Lasse Felder leer, wenn keine entsprechenden Informationen vorhanden sind.
            - Antworte NUR mit einem validen JSON-Objekt, ohne zusätzlichen Text.
            
            Beispiele:
            Anfrage: "Finde Publikationen von Dr. Maria Schmidt über Diabetes in den letzten 3 Jahren"
            Antwort: {"search_term": "Diabetes", "person_name": "Maria Schmidt", "additional_terms": "", "date_range": "letzten 3 Jahre", "database": "", "language": ""}
            
            Anfrage: "Suche nach Artikeln über Herzinfarkt und Bluthochdruck in PubMed auf Englisch"
            Antwort: {"search_term": "Herzinfarkt Bluthochdruck", "person_name": "", "additional_terms": "", "date_range": "", "database": "PubMed", "language": "English"}
            """
            
            # Anfrage an OpenAI API mit verbessertem Response-Format
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query_text}
                ],
                response_format={"type": "json_object"},  # Erzwingt JSON-Format
                temperature=0.1  # Niedrige Temperatur für konsistente Ergebnisse
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
        # API-Schlüssel aktualisieren für den Fall, dass er in den Einstellungen geändert wurde
        self.update_api_key()
        
        if not self.is_configured:
            logger.warning("KI-Integration ist nicht konfiguriert")
            return {
                "success": False,
                "error": "KI-Integration ist nicht konfiguriert. Bitte einen OpenAI API-Schlüssel in den Einstellungen setzen."
            }
            
        # Überprüfen, ob überhaupt Ergebnisse vorliegen
        if not search_results or len(search_results) == 0:
            return {
                "success": False,
                "error": "Keine Suchergebnisse zur Analyse vorhanden."
            }
        
        try:
            # Begrenze die Anzahl der Ergebnisse, um das Kontextfenster nicht zu überschreiten
            limited_results = search_results[:20] if len(search_results) > 20 else search_results
            
            # Konvertiere die Ergebnisse in einen lesbaren Text
            results_text = json.dumps(limited_results, indent=2, ensure_ascii=False)
            
            # Ausführlicher Systemprompt für die KI
            system_prompt = """
            Du bist ein Experte für medizinische und wissenschaftliche Literaturrecherche.
            Deine Aufgabe ist es, die folgenden Suchergebnisse basierend auf der Anfrage des Benutzers
            gründlich zu analysieren und eine strukturierte, informative Zusammenfassung zu erstellen.
            
            Analysiere dabei folgende Aspekte:
            - Relevanz der Ergebnisse zur ursprünglichen Suchanfrage
            - Wichtigste wissenschaftliche Erkenntnisse und Kernaussagen
            - Häufig vorkommende Autoren, Institutionen oder Fachzeitschriften
            - Zeitliche Entwicklung des Forschungsgebiets
            - Übereinstimmungen und Widersprüche in den Ergebnissen
            - Wissenslücken oder Bereiche für weitere Forschung
            
            Strukturiere deine Antwort in folgende Abschnitte mit Überschriften:
            1. Überblick
               Kurze Zusammenfassung der Suchergebnisse im Kontext der Anfrage (etwa 2-3 Sätze).
            
            2. Haupterkenntnisse
               Die 3-5 wichtigsten wissenschaftlichen Erkenntnisse oder Schlussfolgerungen.
            
            3. Muster und Trends
               Identifizierte Muster, Trends oder Zusammenhänge in den Ergebnissen.
            
            4. Empfehlungen
               Konkrete Vorschläge für weitere, verfeinerte Suchanfragen oder ergänzende Datenbanken.
            
            Wichtige Hinweise:
            - Fokussiere dich auf die medizinischen/wissenschaftlichen Inhalte und nicht auf die Metadaten.
            - Verzichte auf Spekulationen, wenn keine ausreichenden Informationen vorliegen.
            - Verwende eine sachliche, wissenschaftliche Sprache.
            - Halte die Analyse präzise und auf den Punkt (maximal 350 Wörter insgesamt).
            - Sollten keine oder kaum relevante Ergebnisse vorliegen, gib konkrete Hinweise zur Verbesserung der Suchanfrage.
            """
            
            # Anfrage an OpenAI API mit dem aktualisierten Prompt
            response = openai.chat.completions.create(
                model="gpt-4o",  # Verwende das neueste und beste Modell für hochwertige Analysen
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Benutzeranfrage: {user_query}\n\nAnzahl der Suchergebnisse: {len(search_results)}\n\nSuchergebnisse:\n{results_text}"}
                ],
                temperature=0.4  # Niedrigere Temperatur für konsistentere, fokussiertere Ergebnisse
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