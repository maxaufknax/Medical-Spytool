"""
GEPRIS Database Connector

This module provides a connector for the GEPRIS (German Project Information System) database.
"""

import requests
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_connector import DatabaseConnector
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class GEPRISConnector(DatabaseConnector):
    """Connector for the GEPRIS database."""
    
    def __init__(self, api_key=None, settings=None):
        """Initialize the GEPRIS connector.
        
        Args:
            api_key (str, optional): The API key for GEPRIS.
            settings (dict, optional): Additional settings.
        """
        super().__init__(api_key, settings)
        self.base_url = "https://gepris.dfg.de"
        self.search_url = "https://gepris.dfg.de/gepris/OCTOPUS"
        
    def get_available_fields(self) -> List[str]:
        """Get the available search fields for GEPRIS.
        
        Returns:
            List[str]: The available search fields.
        """
        return [
            "Alle Felder",
            "Projekt",
            "Person",
            "Institution",
            "Fachgebiet"
        ]
        
    def construct_query(self, base_query, additional_terms="", date_range=None, 
                         language=None, pub_type=None, field=None):
        """Construct a GEPRIS query.
        
        Args:
            base_query (str): The base query.
            additional_terms (str, optional): Additional search terms.
            date_range (dict, optional): The date range for the search.
            language (str, optional): The language filter.
            pub_type (str, optional): The publication type filter.
            field (str, optional): The field to search in.
            
        Returns:
            str: The constructed query.
        """
        # For GEPRIS, we'll create a custom query structure based on its web interface
        query = base_query
        
        # Add additional terms if provided
        if additional_terms:
            query = f"{query} {additional_terms}"
            
        return query
        
    def search(self, query, params=None, log_widget=None):
        """Search the GEPRIS database.
        
        Args:
            query (str): The query string.
            params (dict, optional): Additional search parameters.
            log_widget (object, optional): A widget for logging messages.
            
        Returns:
            List[Dict[str, Any]]: The search results.
        """
        if params is None:
            params = {}
            
        # Get parameters
        max_results = params.get('max_results', 100)
        names = params.get('names', [])
        pub_type = params.get('pub_type', '')
        
        # Map publication types to GEPRIS entity types
        type_map = {
            "Project": "task",
            "Person": "person",
            "Institution": "organisation",
            "": "OCTOPUS"  # Default is all types
        }
        
        # Determine the entity type based on publication type
        entity_type = type_map.get(pub_type, "OCTOPUS")
        
        # If using test mode without API key, generate dummy results
        # Note: GEPRIS doesn't actually require an API key, but we'll
        # use dummy results for testing when requested
        if self.api_key == "dummy":
            from utils.logging_manager import log_message
            log_message(log_widget, "Verwende Dummy-Ergebnisse für GEPRIS-Tests.")
            return self._dummy_search(query, params, log_widget)
            
        all_results = []
        
        try:
            # Use person names for person-specific queries
            if names:
                from utils.logging_manager import log_message
                
                # Search for each person
                for name in names:
                    if not name:
                        continue
                        
                    log_message(log_widget, f"Suche nach Person: {name} in GEPRIS...")
                    
                    # For person search in GEPRIS, we'll focus on the person entity type
                    person_query = name
                    
                    # Prepare search parameters
                    search_params = {
                        "task": "doSearchSimple",
                        "searchString": person_query,
                        "ctx": "person"  # Focus on persons
                    }
                    
                    try:
                        # Send request to GEPRIS
                        response = requests.get(
                            self.search_url,
                            params=search_params
                        )
                        
                        # Check if request was successful
                        if response.status_code != 200:
                            log_message(log_widget, f"Fehler bei GEPRIS-Anfrage: {response.status_code}")
                            continue
                            
                        # Parse HTML response
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Extract search results
                        result_items = soup.select('.results li.result')
                        
                        if not result_items:
                            log_message(log_widget, f"Keine Ergebnisse für '{name}' in GEPRIS gefunden.")
                            continue
                            
                        # Limit results to max_results
                        result_items = result_items[:max_results]
                        
                        # Process each result
                        for item in result_items:
                            try:
                                # Extract basic information
                                title_elem = item.select_one('h2 a')
                                title = title_elem.get_text(strip=True) if title_elem else ""
                                url = self.base_url + title_elem['href'] if title_elem and 'href' in title_elem.attrs else ""
                                
                                # Extract ID from URL
                                gepris_id = url.split("/")[-1] if url else ""
                                
                                # Extract description/details
                                details = []
                                detail_elems = item.select('.details p')
                                for detail in detail_elems:
                                    details.append(detail.get_text(strip=True))
                                
                                details_text = "\n".join(details)
                                
                                # Extract subjects/categories
                                subjects = []
                                subject_elem = item.select_one('.subject')
                                if subject_elem:
                                    subjects = [s.strip() for s in subject_elem.get_text(strip=True).split(",")]
                                
                                # Create result dictionary
                                result = {
                                    "Database": "GEPRIS",
                                    "Name": name,
                                    "Title": title,
                                    "Authors": name,  # In person search context, the person is the "author"
                                    "Publication Year": "",  # GEPRIS doesn't provide years directly in search results
                                    "Publication Types": ["Person"],
                                    "Abstract": details_text,
                                    "Affiliations": "",  # Extract from details if possible
                                    "Publisher": "Deutsche Forschungsgemeinschaft (DFG)",
                                    "Subjects": subjects,
                                    "URL": url,
                                    "Identifier": gepris_id
                                }
                                
                                all_results.append(result)
                                
                            except Exception as e:
                                log_message(log_widget, f"Fehler beim Parsen eines GEPRIS-Eintrags: {str(e)}")
                                logger.error(f"Error parsing GEPRIS entry: {e}", exc_info=True)
                                
                        log_message(log_widget, f"Gefunden: {len(result_items)} Ergebnisse für '{name}' in GEPRIS")
                        
                    except Exception as e:
                        log_message(log_widget, f"Fehler bei GEPRIS-Suche für '{name}': {str(e)}")
                        logger.error(f"GEPRIS search error for '{name}': {e}", exc_info=True)
            else:
                # Regular search without person specification
                from utils.logging_manager import log_message
                log_message(log_widget, f"Suche in GEPRIS mit Abfrage: {query}")
                
                # Prepare search parameters
                search_params = {
                    "task": "doSearchSimple",
                    "searchString": query,
                    "ctx": entity_type
                }
                
                try:
                    # Send request to GEPRIS
                    response = requests.get(
                        self.search_url,
                        params=search_params
                    )
                    
                    # Check if request was successful
                    if response.status_code != 200:
                        log_message(log_widget, f"Fehler bei GEPRIS-Anfrage: {response.status_code}")
                        return []
                        
                    # Parse HTML response
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract search results
                    result_items = soup.select('.results li.result')
                    
                    if not result_items:
                        log_message(log_widget, "Keine Ergebnisse in GEPRIS gefunden.")
                        return []
                        
                    # Limit results to max_results
                    result_items = result_items[:max_results]
                    
                    # Process each result
                    for item in result_items:
                        try:
                            # Extract basic information
                            title_elem = item.select_one('h2 a')
                            title = title_elem.get_text(strip=True) if title_elem else ""
                            url = self.base_url + title_elem['href'] if title_elem and 'href' in title_elem.attrs else ""
                            
                            # Extract ID from URL
                            gepris_id = url.split("/")[-1] if url else ""
                            
                            # Extract description/details
                            details = []
                            detail_elems = item.select('.details p')
                            for detail in detail_elems:
                                details.append(detail.get_text(strip=True))
                            
                            details_text = "\n".join(details)
                            
                            # Extract subjects/categories
                            subjects = []
                            subject_elem = item.select_one('.subject')
                            if subject_elem:
                                subjects = [s.strip() for s in subject_elem.get_text(strip=True).split(",")]
                            
                            # Determine type from class
                            result_type = "Project"
                            if "person" in item.get("class", []):
                                result_type = "Person"
                            elif "organisation" in item.get("class", []):
                                result_type = "Institution"
                            
                            # Try to extract persons/authors for projects
                            authors = ""
                            if result_type == "Project":
                                authors_elem = item.select_one('.persons')
                                if authors_elem:
                                    authors = authors_elem.get_text(strip=True)
                            
                            # Create result dictionary
                            result = {
                                "Database": "GEPRIS",
                                "Name": "General Search",
                                "Title": title,
                                "Authors": authors,
                                "Publication Year": "",  # GEPRIS doesn't provide years directly in search results
                                "Publication Types": [result_type],
                                "Abstract": details_text,
                                "Affiliations": "",  # Extract from details if possible
                                "Publisher": "Deutsche Forschungsgemeinschaft (DFG)",
                                "Subjects": subjects,
                                "URL": url,
                                "Identifier": gepris_id
                            }
                            
                            all_results.append(result)
                            
                        except Exception as e:
                            log_message(log_widget, f"Fehler beim Parsen eines GEPRIS-Eintrags: {str(e)}")
                            logger.error(f"Error parsing GEPRIS entry: {e}", exc_info=True)
                            
                    log_message(log_widget, f"Gefunden: {len(result_items)} Ergebnisse in GEPRIS")
                    
                except Exception as e:
                    log_message(log_widget, f"Fehler bei GEPRIS-Suche: {str(e)}")
                    logger.error(f"GEPRIS search error: {e}", exc_info=True)
                    
            return all_results
            
        except Exception as e:
            from utils.logging_manager import log_message
            log_message(log_widget, f"Fehler bei GEPRIS-Suche: {str(e)}")
            logger.error(f"GEPRIS search error: {e}", exc_info=True)
            return []
            
    def _dummy_search(self, query, params=None, log_widget=None):
        """Generate dummy results for testing.
        
        Args:
            query (str): The query string.
            params (dict, optional): Additional search parameters.
            log_widget (object, optional): A widget for logging messages.
            
        Returns:
            List[Dict[str, Any]]: The dummy search results.
        """
        from utils.logging_manager import log_message
        log_message(log_widget, "Generiere Dummy-Ergebnisse für GEPRIS...")
        
        # Generate some dummy results for testing without API key
        dummy_results = []
        names = params.get('names', [])
        person_name = names[0] if names else "General Search"
        
        # Define result types based on search context
        if person_name != "General Search":
            # Person-specific search - include projects and person info
            result_types = ["Project", "Person", "Institution"]
        else:
            # General search - include various types
            result_types = ["Project", "Person", "Institution"]
        
        # Generate dummy results
        for i in range(1, 11):
            # Rotate through result types
            result_type = result_types[i % len(result_types)]
            
            # Customize result based on type
            if result_type == "Person":
                title = f"Prof. Dr. {person_name if person_name != 'General Search' else f'Example Researcher {i}'}"
                subjects = ["Medizin", "Gesundheitswissenschaften"]
                details = "Universitätsklinikum XYZ\nAbteilung für Medizinische Forschung"
                
            elif result_type == "Project":
                title = f"Dummy GEPRIS Projekt {i}: {query.capitalize() if query else 'Forschungsprojekt'}"
                subjects = ["Klinische Forschung", "Medizinische Informatik"]
                details = f"Laufzeit: 2020 - 2023\nFörderkennzeichen: ABC-123-{i}\nFördersumme: {i*100000} EUR"
                
            else:  # Institution
                title = f"Institut für {query.capitalize() if query else 'Medizinische Forschung'} {i}"
                subjects = ["Universitätsmedizin", "Forschungseinrichtung"]
                details = f"Universität XYZ\nFakultät für Medizin\nAbteilung {i}"
            
            # Create result dictionary
            result = {
                "Database": "GEPRIS",
                "Name": person_name,
                "Title": title,
                "Authors": person_name if result_type == "Project" and person_name != "General Search" else "",
                "Publication Year": f"202{i % 5}",
                "Publication Types": [result_type],
                "Abstract": details,
                "Affiliations": "Universität XYZ" if result_type in ["Person", "Project"] else "",
                "Publisher": "Deutsche Forschungsgemeinschaft (DFG)",
                "Subjects": subjects,
                "URL": f"https://gepris.dfg.de/gepris/projekt/12345{i}",
                "Identifier": f"12345{i}",
            }
            dummy_results.append(result)
            
        log_message(log_widget, f"Generierte {len(dummy_results)} Dummy-Ergebnisse für GEPRIS")
        return dummy_results
        
    def parse_results(self, entries, name, log_widget):
        """Parse the results from GEPRIS search.
        
        Args:
            entries (List[Dict[str, Any]]): The entries from GEPRIS search.
            name (str): The name of the person who performed the search.
            log_widget (object, optional): A widget for logging messages.
            
        Returns:
            List[Dict[str, Any]]: The parsed results.
        """
        # Note: This method is not directly used as we parse HTML directly in the search method
        # It's included for compatibility with the DatabaseConnector interface
        return []
        
    def get_citation_count(self, gepris_id):
        """Get the citation count for a publication.
        
        Args:
            gepris_id (str): The GEPRIS ID.
            
        Returns:
            int: The citation count (always 0 for GEPRIS).
        """
        # GEPRIS doesn't provide citation counts
        return 0