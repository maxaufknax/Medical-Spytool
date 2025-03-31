"""
Scopus Database Connector

This module provides a connector for the Scopus database.
"""

import requests
import logging
import json
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from .base_connector import DatabaseConnector

logger = logging.getLogger(__name__)

class ScopusConnector(DatabaseConnector):
    """Connector for the Scopus database."""
    
    def __init__(self, api_key=None, settings=None):
        """Initialize the Scopus connector.
        
        Args:
            api_key (str, optional): The API key for Scopus.
            settings (dict, optional): Additional settings.
        """
        super().__init__(api_key, settings)
        self.base_url = "https://api.elsevier.com/content/search/scopus"
        self.citation_url = "https://api.elsevier.com/content/abstract/citations"
        
    def get_available_fields(self) -> List[str]:
        """Get the available search fields for Scopus.
        
        Returns:
            List[str]: The available search fields.
        """
        return [
            "Alle Felder",
            "Autor",
            "Titel",
            "Abstract",
            "Keywords",
            "Affiliation",
            "DOI",
            "ISSN",
            "Journal",
            "Subject"
        ]
        
    def construct_query(self, base_query, additional_terms="", date_range=None, 
                         language=None, pub_type=None, field=None):
        """Construct a Scopus query.
        
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
        # Map fields to Scopus search fields
        field_map = {
            "Autor": "AUTHOR-NAME",
            "Titel": "TITLE",
            "Abstract": "ABS",
            "Keywords": "KEY",
            "Affiliation": "AFFIL",
            "DOI": "DOI",
            "ISSN": "ISSN",
            "Journal": "SRCTITLE",
            "Subject": "SUBJAREA"
        }
        
        # If no field specified or "Alle Felder" is chosen, search in all fields
        search_field = field_map.get(field, "ALL")
        
        # Start with base query
        query_parts = []
        
        # Add the main search term
        if base_query:
            query_parts.append(f"{search_field}({base_query})")
        
        # Add additional terms if provided
        if additional_terms:
            query_parts.append(f"AND ({additional_terms})")
            
        # Add date range filter
        if date_range and isinstance(date_range, dict):
            start_year = date_range.get('start')
            end_year = date_range.get('end')
            if start_year and end_year:
                start_year_str = start_year.year if hasattr(start_year, 'year') else start_year
                end_year_str = end_year.year if hasattr(end_year, 'year') else end_year
                query_parts.append(f"AND PUBYEAR AFT {start_year_str-1} AND PUBYEAR BEF {end_year_str+1}")
            
        # Add language filter
        if language:
            lang_map = {
                "English": "English",
                "German": "German",
                "French": "French",
                "Spanish": "Spanish"
            }
            scopus_lang = lang_map.get(language)
            if scopus_lang:
                query_parts.append(f"AND LANGUAGE({scopus_lang})")
                
        # Add publication type filter
        if pub_type:
            type_map = {
                "Article": "ar",
                "Review": "re",
                "Conference Paper": "cp",
                "Book Chapter": "ch",
                "Editorial": "ed"
            }
            scopus_type = type_map.get(pub_type)
            if scopus_type:
                query_parts.append(f"AND DOCTYPE({scopus_type})")
                
        # Join all parts to form the final query
        final_query = " ".join(query_parts)
        
        return final_query
        
    def search(self, query, params=None, log_widget=None):
        """Search the Scopus database.
        
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
            log_message(log_widget, "Kein API-Schlüssel für Scopus. Verwende Dummy-Ergebnisse für Testzwecke.")
            return self._dummy_search(query, params, log_widget)
            
        # Get API key
        headers = {
            "X-ELS-APIKey": self.api_key,
            "Accept": "application/json"
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
                        
                    log_message(log_widget, f"Suche nach Person: {name} in Scopus...")
                    
                    # Person name query: Look for author name
                    person_query = f"AUTHOR-NAME({name})" if query == "" else f"AUTHOR-NAME({name}) AND ({query})"
                    
                    # Prepare search parameters
                    search_params = {
                        "query": person_query,
                        "count": min(max_results, 25),  # Scopus API limit per request
                        "start": 0,
                        "view": "COMPLETE"
                    }
                    
                    total_fetched = 0
                    
                    # Paginate through results
                    while total_fetched < max_results:
                        search_params["start"] = total_fetched
                        
                        response = requests.get(
                            self.base_url,
                            headers=headers,
                            params=search_params
                        )
                        
                        # Check if request was successful
                        if response.status_code != 200:
                            log_message(log_widget, f"Fehler bei Scopus-Anfrage: {response.status_code} - {response.text}")
                            break
                            
                        # Parse response
                        try:
                            data = response.json()
                            entries = data.get("search-results", {}).get("entry", [])
                            
                            if not entries:
                                break
                                
                            # Parse results
                            parse_params = {'name': name, 'log_widget': log_widget}
                            parsed_results = self.parse_results(entries, parse_params)
                            all_results.extend(parsed_results)
                            
                            total_fetched += len(entries)
                            
                            # Check if we have more results
                            total_count = int(data.get("search-results", {}).get("opensearch:totalResults", "0"))
                            if total_fetched >= total_count:
                                break
                                
                            log_message(log_widget, f"Abgerufen: {total_fetched}/{total_count} Ergebnisse für {name}...")
                            
                        except Exception as e:
                            log_message(log_widget, f"Fehler beim Verarbeiten der Scopus-Antwort: {str(e)}")
                            break
            else:
                # Regular query without person specification
                from utils.logging_manager import log_message
                log_message(log_widget, f"Suche in Scopus mit Abfrage: {query}")
                
                # Prepare search parameters
                search_params = {
                    "query": query,
                    "count": min(max_results, 25),  # Scopus API limit per request
                    "start": 0,
                    "view": "COMPLETE"
                }
                
                total_fetched = 0
                
                # Paginate through results
                while total_fetched < max_results:
                    search_params["start"] = total_fetched
                    
                    response = requests.get(
                        self.base_url,
                        headers=headers,
                        params=search_params
                    )
                    
                    # Check if request was successful
                    if response.status_code != 200:
                        log_message(log_widget, f"Fehler bei Scopus-Anfrage: {response.status_code} - {response.text}")
                        break
                        
                    # Parse response
                    try:
                        data = response.json()
                        entries = data.get("search-results", {}).get("entry", [])
                        
                        if not entries:
                            break
                            
                        # Parse results
                        parse_params = {'name': "General Search", 'log_widget': log_widget}
                        parsed_results = self.parse_results(entries, parse_params)
                        all_results.extend(parsed_results)
                        
                        total_fetched += len(entries)
                        
                        # Check if we have more results
                        total_count = int(data.get("search-results", {}).get("opensearch:totalResults", "0"))
                        if total_fetched >= total_count:
                            break
                            
                        log_message(log_widget, f"Abgerufen: {total_fetched}/{total_count} Ergebnisse...")
                        
                    except Exception as e:
                        log_message(log_widget, f"Fehler beim Verarbeiten der Scopus-Antwort: {str(e)}")
                        break
                        
            return all_results
            
        except Exception as e:
            from utils.logging_manager import log_message
            log_message(log_widget, f"Fehler bei Scopus-Suche: {str(e)}")
            logger.error(f"Scopus search error: {e}", exc_info=True)
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
        log_message(log_widget, "Generiere Dummy-Ergebnisse für Scopus...")
        
        # Generate some dummy results for testing without API key
        dummy_results = []
        names = params.get('names', [])
        person_name = names[0] if names else "General Search"
        
        # Generate 10 dummy results
        for i in range(1, 11):
            year = 2020 - (i % 5)
            result = {
                "Database": "Scopus",
                "Name": person_name,
                "Title": f"Dummy Scopus Publication {i}: {query}",
                "Authors": f"Author A, Author B, {person_name if person_name != 'General Search' else 'Author C'}",
                "Publication Year": str(year),
                "Publication Month": f"{(i % 12) + 1}",
                "Publication Types": ["Article"],
                "Abstract": f"This is a dummy abstract for testing Scopus integration. Search query: {query}",
                "Affiliations": "Dummy University, Department of Testing",
                "Publisher": "Elsevier",
                "URL": f"https://www.scopus.com/record/dummy-{i}",
                "DOI": f"10.1016/j.dummy.{year}.{i}",
                "Citation Count": str(i * 10),
                "Identifier": f"SCOPUS_ID:{i}000000000000",
                "Subjects": ["Medicine", "Computer Science", "Engineering"]
            }
            dummy_results.append(result)
            
        log_message(log_widget, f"Generierte {len(dummy_results)} Dummy-Ergebnisse für Scopus")
        return dummy_results
        
    def parse_results(self, response, params=None):
        """Parse the results from Scopus API.
        
        Args:
            response: The entries from the Scopus API.
            params (dict, optional): Additional parameters including name and log_widget.
            
        Returns:
            List[Dict[str, Any]]: The parsed results.
        """
        # Extract parameters from params dict
        entries = response
        name = params.get('name', 'General Search') if params else 'General Search'
        log_widget = params.get('log_widget') if params else None
        parsed_results = []
        
        for entry in entries:
            try:
                # Extract basic information
                title = entry.get("dc:title", "")
                scopus_id = entry.get("dc:identifier", "")
                if scopus_id and scopus_id.startswith("SCOPUS_ID:"):
                    scopus_id = scopus_id[10:]  # Remove "SCOPUS_ID:" prefix
                
                # Extract authors
                creator = entry.get("dc:creator", "")
                author_list = entry.get("author", [])
                if isinstance(author_list, dict):
                    author_list = [author_list]
                authors = creator
                if not authors and author_list:
                    author_names = []
                    for author in author_list:
                        author_name = author.get("authname", "")
                        if author_name:
                            author_names.append(author_name)
                    authors = ", ".join(author_names)
                
                # Extract publication date
                pub_date = entry.get("prism:coverDate", "")
                pub_year = ""
                pub_month = ""
                if pub_date:
                    try:
                        date_parts = pub_date.split("-")
                        pub_year = date_parts[0]
                        pub_month = date_parts[1] if len(date_parts) > 1 else ""
                    except:
                        pass
                
                # Extract publication types
                pub_type = entry.get("subtypeDescription", "")
                pub_types = [pub_type] if pub_type else []
                
                # Extract abstract
                abstract = entry.get("dc:description", "")
                
                # Extract affiliations
                affiliation = entry.get("affiliation", {}).get("affilname", "")
                
                # Extract publisher
                publisher = entry.get("dc:publisher", "")
                
                # Extract subjects
                subject_areas = entry.get("subject-area", [])
                if isinstance(subject_areas, dict):
                    subject_areas = [subject_areas]
                subjects = []
                for area in subject_areas:
                    area_name = area.get("$", "")
                    if area_name:
                        subjects.append(area_name)
                
                # Extract DOI
                doi = entry.get("prism:doi", "")
                
                # Extract URL
                url = entry.get("link", [])
                if isinstance(url, dict):
                    url = [url]
                url_str = ""
                for link in url:
                    if link.get("@ref", "") == "scopus":
                        url_str = link.get("@href", "")
                        break
                
                # Extract citation count
                citation_count = entry.get("citedby-count", "0")
                
                # Create result dictionary
                result = {
                    "Database": "Scopus",
                    "Name": name,
                    "Title": title,
                    "Authors": authors,
                    "Publication Year": pub_year,
                    "Publication Month": pub_month,
                    "Publication Types": pub_types,
                    "Abstract": abstract,
                    "Affiliations": affiliation,
                    "Publisher": publisher,
                    "Subjects": subjects,
                    "DOI": doi,
                    "URL": url_str,
                    "Citation Count": citation_count,
                    "Identifier": scopus_id
                }
                
                parsed_results.append(result)
                
            except Exception as e:
                from utils.logging_manager import log_message
                if log_widget:
                    log_message(log_widget, f"Fehler beim Parsen eines Scopus-Eintrags: {str(e)}")
                logger.error(f"Error parsing Scopus entry: {e}", exc_info=True)
                
        return parsed_results
        
    def get_citation_count(self, identifier):
        """Get the citation count for a publication.
        
        Args:
            identifier (str): The Scopus ID.
            
        Returns:
            int or str: The citation count or error message.
        """
        scopus_id = identifier
        if not self.api_key or not scopus_id:
            return 0
            
        try:
            # Get API key
            headers = {
                "X-ELS-APIKey": self.api_key,
                "Accept": "application/json"
            }
            
            # Get citation data
            url = f"{self.citation_url}/{scopus_id}"
            response = requests.get(
                url,
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"Error fetching citation count: {response.status_code} - {response.text}")
                return 0
                
            data = response.json()
            citation_count = data.get("abstract-citations-response", {}).get("citeColumnTotalXocs", {}).get("$", 0)
            
            return int(citation_count)
            
        except Exception as e:
            logger.error(f"Error getting citation count: {e}", exc_info=True)
            return 0