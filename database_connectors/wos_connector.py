"""
Web of Science (WoS) Connector Module

This module provides functionality to search the Web of Science database.
"""

from typing import List, Dict, Any, Optional
import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from .base_connector import BaseConnector  # Changed from DatabaseConnector to BaseConnector

logger = logging.getLogger(__name__)

class WoSConnector(BaseConnector):
    """Connector for the Web of Science database."""
    
    def __init__(self, api_key=None, settings=None):
        """Initialize the Web of Science connector.
        
        Args:
            api_key (str, optional): The API key for WoS.
            settings (dict, optional): Additional settings.
        """
        super().__init__(api_key, settings)
        self.base_url = "https://wos-api.clarivate.com/api/woslite"
        self.citation_url = "https://wos-api.clarivate.com/api/woslite/references"
        
    def get_available_fields(self) -> List[str]:
        """Get the available search fields for Web of Science.
        
        Returns:
            List[str]: The available search fields.
        """
        return [
            "Alle Felder",
            "Autor",
            "Titel",
            "Abstract",
            "Keywords",
            "Adresse",
            "DOI",
            "ISSN",
            "Journal",
            "Konferenz"
        ]
        
    def construct_query(self, base_query, additional_terms="", date_range=None, 
                         language=None, pub_type=None, field=None):
        """Construct a Web of Science query.
        
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
        # Map fields to WoS search fields
        field_map = {
            "Autor": "AU",
            "Titel": "TI",
            "Abstract": "AB",
            "Keywords": "KW",
            "Adresse": "AD",
            "DOI": "DO",
            "ISSN": "IS",
            "Journal": "SO",
            "Konferenz": "CF"
        }
        
        # If no field specified or "Alle Felder" is chosen, search in all fields
        search_field = field_map.get(field, "TS")
        
        # Start with base query
        query_parts = []
        
        # Add the main search term
        if base_query:
            query_parts.append(f"{search_field}=({base_query})")
        
        # Add additional terms if provided
        if additional_terms:
            query_parts.append(f"AND ({additional_terms})")
            
        # Add date range filter
        if date_range:
            start_year = date_range.get('start').year
            end_year = date_range.get('end').year
            query_parts.append(f"AND PY=({start_year}-{end_year})")
            
        # Add language filter
        if language:
            lang_map = {
                "English": "English",
                "German": "German",
                "French": "French",
                "Spanish": "Spanish"
            }
            wos_lang = lang_map.get(language)
            if wos_lang:
                query_parts.append(f"AND LA=({wos_lang})")
                
        # Add publication type filter
        if pub_type:
            type_map = {
                "Article": "Article",
                "Review": "Review",
                "Proceedings Paper": "Proceedings Paper",
                "Book Chapter": "Book Chapter",
                "Editorial": "Editorial"
            }
            wos_type = type_map.get(pub_type)
            if wos_type:
                query_parts.append(f"AND DT=({wos_type})")
                
        # Join all parts to form the final query
        final_query = " ".join(query_parts)
        
        return final_query
        
    def search(self, query, params=None, log_widget=None):
        """Search the Web of Science database.
        
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
        
        # If using test mode without API key, generate dummy results
        if not self.api_key:
            from utils.logging_manager import log_message
            log_message(log_widget, "Kein API-Schlüssel für Web of Science. Verwende Dummy-Ergebnisse für Testzwecke.")
            return self._dummy_search(query, params, log_widget)
            
        # Get API key
        headers = {
            "X-APIKey": self.api_key,
            "Content-Type": "application/json"
        }
        
        all_results = []
        
        try:
            # Use person names for person-specific queries
            if names:
                from utils.logging_manager import log_message
                
                # Search for each person
                for name in names:
                    if not name:
                        continue
                        
                    log_message(log_widget, f"Suche nach Person: {name} in Web of Science...")
                    
                    # Person name query: Look for author name
                    person_query = f"AU=({name})" if query == "" else f"AU=({name}) AND ({query})"
                    
                    # Prepare search parameters
                    payload = {
                        "databaseId": "WOS",
                        "usrQuery": person_query,
                        "count": min(max_results, 100),  # WoS API limit per request
                        "firstRecord": 1
                    }
                    
                    total_fetched = 0
                    
                    # Paginate through results
                    while total_fetched < max_results:
                        payload["firstRecord"] = total_fetched + 1
                        
                        response = requests.post(
                            self.base_url,
                            headers=headers,
                            json=payload
                        )
                        
                        # Check if request was successful
                        if response.status_code != 200:
                            log_message(log_widget, f"Fehler bei WoS-Anfrage: {response.status_code} - {response.text}")
                            break
                            
                        # Parse response
                        try:
                            data = response.json()
                            records = data.get("Data", {}).get("Records", {}).get("records", [])
                            
                            if not records:
                                break
                                
                            # Parse results
                            parsed_results = self.parse_results(records, name, log_widget)
                            all_results.extend(parsed_results)
                            
                            total_fetched += len(records)
                            
                            # Check if we have more results
                            record_count = data.get("QueryResult", {}).get("RecordsFound", 0)
                            if total_fetched >= record_count:
                                break
                                
                            log_message(log_widget, f"Abgerufen: {total_fetched}/{record_count} Ergebnisse für {name}...")
                            
                        except Exception as e:
                            log_message(log_widget, f"Fehler beim Verarbeiten der WoS-Antwort: {str(e)}")
                            break
            else:
                # Regular query without person specification
                from utils.logging_manager import log_message
                log_message(log_widget, f"Suche in Web of Science mit Abfrage: {query}")
                
                # Prepare search parameters
                payload = {
                    "databaseId": "WOS",
                    "usrQuery": query,
                    "count": min(max_results, 100),  # WoS API limit per request
                    "firstRecord": 1
                }
                
                total_fetched = 0
                
                # Paginate through results
                while total_fetched < max_results:
                    payload["firstRecord"] = total_fetched + 1
                    
                    response = requests.post(
                        self.base_url,
                        headers=headers,
                        json=payload
                    )
                    
                    # Check if request was successful
                    if response.status_code != 200:
                        log_message(log_widget, f"Fehler bei WoS-Anfrage: {response.status_code} - {response.text}")
                        break
                        
                    # Parse response
                    try:
                        data = response.json()
                        records = data.get("Data", {}).get("Records", {}).get("records", [])
                        
                        if not records:
                            break
                            
                        # Parse results
                        parsed_results = self.parse_results(records, "General Search", log_widget)
                        all_results.extend(parsed_results)
                        
                        total_fetched += len(records)
                        
                        # Check if we have more results
                        record_count = data.get("QueryResult", {}).get("RecordsFound", 0)
                        if total_fetched >= record_count:
                            break
                            
                        log_message(log_widget, f"Abgerufen: {total_fetched}/{record_count} Ergebnisse...")
                        
                    except Exception as e:
                        log_message(log_widget, f"Fehler beim Verarbeiten der WoS-Antwort: {str(e)}")
                        break
                        
            return all_results
            
        except Exception as e:
            from utils.logging_manager import log_message
            log_message(log_widget, f"Fehler bei Web of Science-Suche: {str(e)}")
            logger.error(f"Web of Science search error: {e}", exc_info=True)
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
        log_message(log_widget, "Generiere Dummy-Ergebnisse für Web of Science...")
        
        # Generate some dummy results for testing without API key
        dummy_results = []
        names = params.get('names', [])
        person_name = names[0] if names else "General Search"
        
        # Generate 10 dummy results
        for i in range(1, 11):
            year = 2020 - (i % 5)
            result = {
                "Database": "Web of Science",
                "Name": person_name,
                "Title": f"Dummy WoS Publication {i}: {query}",
                "Authors": f"Author A, Author B, {person_name if person_name != 'General Search' else 'Author C'}",
                "Publication Year": str(year),
                "Publication Month": f"{(i % 12) + 1}",
                "Publication Types": ["Article"],
                "Abstract": f"This is a dummy abstract for testing Web of Science integration. Search query: {query}",
                "Affiliations": "Dummy University, Department of Testing",
                "Publisher": "Dummy Publisher",
                "URL": f"https://www.webofscience.com/record/dummy-{i}",
                "DOI": f"10.1234/dummy.{year}.{i}",
                "Citation Count": str(i * 5),
                "Identifier": f"WOS:{i}000000000000",
                "Subjects": ["Testing", "Dummy Data", "API Integration"]
            }
            dummy_results.append(result)
            
        log_message(log_widget, f"Generierte {len(dummy_results)} Dummy-Ergebnisse für Web of Science")
        return dummy_results
        
    def parse_results(self, records, name, log_widget):
        """Parse the results from Web of Science API.
        
        Args:
            records (List[Dict[str, Any]]): The records from the Web of Science API.
            name (str): The name of the person who performed the search.
            log_widget (object, optional): A widget for logging messages.
            
        Returns:
            List[Dict[str, Any]]: The parsed results.
        """
        parsed_results = []
        
        for record in records:
            try:
                # Extract source metadata
                source_data = record.get("source", {})
                
                # Extract record metadata
                wos_id = record.get("uid", "")
                title = record.get("title", {}).get("title", "")
                
                # Extract authors
                authors_list = record.get("authors", {}).get("authors", [])
                authors = ", ".join([author.get("full_name", "") for author in authors_list]) if authors_list else ""
                
                # Extract publication date
                pub_info = record.get("source", {}).get("publishinfo", {})
                pub_year = pub_info.get("pubyear", "")
                pub_month = pub_info.get("pubmonth", "")
                
                # Extract publication types
                doc_type = record.get("doctype", {}).get("doctype", "")
                pub_types = [doc_type] if doc_type else []
                
                # Extract journal/source info
                journal_info = source_data.get("sourceTitle", "")
                publisher = source_data.get("publisher", "")
                
                # Extract identifiers
                ids = record.get("identifiers", {}).get("identifier", [])
                doi = ""
                for id_item in ids:
                    if id_item.get("type", "") == "doi":
                        doi = id_item.get("value", "")
                        break
                        
                # Extract citation count
                citation_count = record.get("citation_data", {}).get("total_cites", "0")
                
                # Extract subjects
                categories = record.get("categories", {}).get("category", [])
                subjects = [cat.get("name", "") for cat in categories] if categories else []
                
                # Extract URL
                url = f"https://www.webofscience.com/wos/woscc/full-record/{wos_id}" if wos_id else ""
                
                # Extract language
                languages = record.get("languages", {}).get("language", [])
                language = languages[0].get("name", "") if languages else ""
                
                # Extract affiliations
                addresses = record.get("addresses", {}).get("address_name", [])
                affiliations = ", ".join([addr.get("full_address", "") for addr in addresses]) if addresses else ""
                
                # Create result dictionary
                result = {
                    "Database": "Web of Science",
                    "Name": name,
                    "Title": title,
                    "Authors": authors,
                    "Publication Year": pub_year,
                    "Publication Month": pub_month,
                    "Publication Types": pub_types,
                    "Affiliations": affiliations,
                    "Publisher": publisher,
                    "Subjects": subjects,
                    "Language": language,
                    "DOI": doi,
                    "URL": url,
                    "Citation Count": citation_count,
                    "Identifier": wos_id
                }
                
                parsed_results.append(result)
                
            except Exception as e:
                from utils.logging_manager import log_message
                log_message(log_widget, f"Fehler beim Parsen eines WoS-Eintrags: {str(e)}")
                logger.error(f"Error parsing WoS entry: {e}", exc_info=True)
                
        return parsed_results
        
    def get_citation_count(self, wos_id):
        """Get the citation count for a publication.
        
        Args:
            wos_id (str): The Web of Science ID.
            
        Returns:
            int: The citation count.
        """
        if not self.api_key or not wos_id:
            return 0
            
        try:
            # Get API key
            headers = {
                "X-APIKey": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Prepare request payload
            payload = {
                "databaseId": "WOS",
                "uid": wos_id
            }
            
            # Get citation data
            response = requests.post(
                self.citation_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"Error fetching citation count: {response.status_code} - {response.text}")
                return 0
                
            data = response.json()
            citation_count = data.get("Data", {}).get("Citation", {}).get("TimesCited", 0)
            
            return int(citation_count)
            
        except Exception as e:
            logger.error(f"Error getting citation count: {e}", exc_info=True)
            return 0