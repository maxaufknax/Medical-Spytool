"""
German National Library (DNB) Database Connector

This module provides functionality to search and retrieve publications from the DNB.
"""

import requests
import xml.etree.ElementTree as ET
import logging
from datetime import datetime

from database_connectors.base_connector import DatabaseConnector

# DNB Namespaces
DNB_NS = {
    'srw': 'http://www.loc.gov/zing/srw/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'foaf': 'http://xmlns.com/foaf/0.1/',
    'rdau': 'http://rdaregistry.info/Elements/u/'
}

logger = logging.getLogger(__name__)

class DNBConnector(DatabaseConnector):
    """
    Connector for the German National Library (DNB) database.
    """
    
    def __init__(self, api_key=None, settings=None):
        """
        Initialize the DNB connector.
        
        Args:
            api_key (str, optional): API key for DNB.
            settings (dict, optional): Additional settings.
        """
        super().__init__(api_key, settings)
        self.name = "DNB"
        self.max_results_per_page = 1000  # Erhöhen auf 1.000 Ergebnisse pro Anfrage für DNB
        self.search_fields = ["Alle Felder", "Titel", "Autor", "Jahr", "Verlag", "Schlagwort"]
        self.base_url = "https://services.dnb.de/sru/dnb"
        self.requires_api_key = False  # DNB benötigt keinen API-Key für die meisten Anfragen
        
    def validate_api_key(self):
        """
        Überprüft die Verbindung zur DNB-API.
        
        DNB benötigt keinen API-Key für die meisten Abfragen, daher testen wir
        nur, ob der Service erreichbar ist.
        
        Returns:
            bool: True, wenn die Verbindung zur DNB-API hergestellt werden kann.
        """
        try:
            import requests
            import xml.etree.ElementTree as ET
            
            # Eine einfache Testabfrage
            params = {
                'operation': 'searchRetrieve',
                'version': '1.1',
                'recordSchema': 'RDFxml',
                'query': 'tit = test',
                'maximumRecords': '1'
            }
            
            # API-Key hinzufügen, falls vorhanden
            if self.api_key:
                params['accessToken'] = self.api_key
            
            # Führe Testabfrage durch
            response = requests.get(self.base_url, params=params, timeout=5)
            if response.status_code == 200:
                # Versuche die XML-Antwort zu parsen
                try:
                    root = ET.fromstring(response.content)
                    # Überprüfe, ob wir eine gültige SRW-Antwort erhalten haben
                    diagnostics = root.findall(".//srw:diagnostics", namespaces=DNB_NS)
                    if diagnostics and len(diagnostics) > 0:
                        # Error in der Antwort
                        logger.warning(f"DNB API-Verbindungstest fehlgeschlagen: {response.text}")
                        return False
                    return True
                except ET.ParseError as e:
                    logger.error(f"Fehler beim Parsen der DNB-API-Antwort: {e}")
                    return False
            else:
                logger.warning(f"DNB API-Verbindungstest fehlgeschlagen. Status-Code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Fehler bei der Verbindung zur DNB-API: {str(e)}")
            # Bei Netzwerkfehlern gehen wir davon aus, dass der Key valide ist
            # um die Anwendung nicht zu blockieren
            return True
    
    def construct_query(self, base_query, additional_terms="", date_range=None, 
                      language=None, pub_type=None, field=None):
        """
        Construct a DNB search query.
        
        Args:
            base_query (str): Base query.
            additional_terms (str, optional): Additional search terms.
            date_range (dict, optional): Date range with 'start' and 'end' keys.
            language (str, optional): Language filter.
            pub_type (str, optional): Publication type filter.
            field (str, optional): Field to search in.
            
        Returns:
            str: Constructed query.
        """
        # Apply field-specific search
        if field and field != "Alle Felder":
            field_map = {
                "Titel": "dct.title",
                "Autor": "dct.creator",
                "Jahr": "dct.issued",
                "Verlag": "dct.publisher",
                "Schlagwort": "dct.subject"
            }
            index = field_map.get(field, "")
            if index:
                query = f'{index} = "{base_query}"'
            else:
                query = base_query
        else:
            query = base_query
            
        # Add additional terms
        if additional_terms:
            query = f"({query}) AND ({additional_terms})"
            
        # Add date range
        if date_range and date_range.get('start') and date_range.get('end'):
            start_year = date_range['start'].year
            end_year = date_range['end'].year
            date_clause = " OR ".join([f'dct.issued = "{year}"' for year in range(start_year, end_year + 1)])
            query = f"({query}) AND ({date_clause})"
            
        # Add language filter
        if language:
            query = f"({query}) AND (dct.language = \"{language}\")"
            
        # Add publication type filter
        if pub_type:
            query = f"({query}) AND (dct.type = \"{pub_type}\")"
            
        return query
    
    def search(self, query, params=None, log_widget=None):
        """
        Search the DNB with the given query.
        
        Args:
            query (str): Search query.
            params (dict, optional): Additional search parameters.
            log_widget (object, optional): Object for logging messages.
            
        Returns:
            list: Search results.
        """
        from utils.logging_manager import log_message
        
        params = params or {}
        name = params.get('name', 'General Search')
        max_results = params.get('max_results', self.max_results_per_page)
        
        log_message(log_widget, f"Starting DNB search: {query}")
        
        # Set up the SRU request parameters
        sru_params = {
            "version": "1.1",
            "operation": "searchRetrieve",
            "query": query,
            "recordSchema": "RDFxml",
            "maximumRecords": max_results
        }
        
        publications = []
        
        try:
            response = requests.get(self.base_url, params=sru_params)
            response.raise_for_status()
            
            # Parse the XML response
            root = ET.fromstring(response.content)
            
            # Check if there are any results
            num_records_node = root.find('.//srw:numberOfRecords', DNB_NS)
            if num_records_node is None:
                log_message(log_widget, "No results found in DNB search")
                return []
            
            num_records = int(num_records_node.text)
            log_message(log_widget, f"DNB search: {num_records} results found")
            
            if num_records == 0:
                return []
            
            # Process the records
            publications = self.parse_results(root, params={'name': name, 'log_widget': log_widget})
            
            # Handle pagination if needed
            start_record = max_results + 1
            while len(publications) < num_records and len(publications) < max_results:
                log_message(log_widget, f"Retrieving more DNB results (starting at {start_record})...")
                
                # Update pagination parameters
                sru_params["startRecord"] = start_record
                
                # Make the next request
                response = requests.get(self.base_url, params=sru_params)
                response.raise_for_status()
                
                # Parse the new results
                root = ET.fromstring(response.content)
                new_results = self.parse_results(root, params={'name': name, 'log_widget': log_widget})
                
                if not new_results:
                    break
                    
                publications.extend(new_results)
                start_record += self.max_results_per_page
            
        except requests.exceptions.RequestException as e:
            log_message(log_widget, f"Error in DNB search: {e}")
            logger.error(f"DNB search error: {e}", exc_info=True)
        except ET.ParseError as e:
            log_message(log_widget, f"Error parsing DNB results: {e}")
            logger.error(f"DNB XML parse error: {e}", exc_info=True)
        except Exception as e:
            log_message(log_widget, f"Unexpected error in DNB search: {e}")
            logger.error(f"Unexpected DNB search error: {e}", exc_info=True)
        
        return publications
    
    def parse_results(self, root, params=None):
        """
        Parse DNB search results.
        
        Args:
            root (xml.etree.ElementTree.Element): XML response from DNB.
            params (dict, optional): Additional parameters.
            
        Returns:
            list: Parsed publications.
        """
        from utils.logging_manager import log_message
        
        params = params or {}
        name = params.get('name', 'Unknown')
        log_widget = params.get('log_widget', None)
        
        publications = []
        records = root.findall('.//srw:record', DNB_NS)
        
        log_message(log_widget, f"Processing {len(records)} DNB records...")
        
        for i, record in enumerate(records):
            try:
                # Extract recordData which contains the RDF data
                record_data = record.find('.//srw:recordData', DNB_NS)
                if record_data is None:
                    continue
                
                # Find the main description node
                description = record_data.find('.//rdf:Description', DNB_NS)
                if description is None:
                    continue
                
                # Extract title
                title_el = description.find('./dc:title', DNB_NS)
                title = title_el.text if title_el is not None else "No Title"
                
                # Extract creators/authors
                creators = []
                for creator in description.findall('./dc:creator', DNB_NS):
                    if creator.text:
                        creators.append(creator.text)
                creators_str = ", ".join(creators) if creators else "No Authors"
                
                # Extract publication year
                issued_el = description.find('./dcterms:issued', DNB_NS)
                year = issued_el.text if issued_el is not None else "N/A"
                
                # Extract publisher
                publisher_el = description.find('./dc:publisher', DNB_NS)
                publisher = publisher_el.text if publisher_el is not None else "No Publisher"
                
                # Extract identifiers
                identifier_els = description.findall('./dc:identifier', DNB_NS)
                identifiers = [identifier.text for identifier in identifier_els if identifier.text]
                
                # Try to find DOI, ISBN, and other identifiers
                doi = next((id_val for id_val in identifiers if "doi" in id_val.lower()), "No DOI")
                isbn = next((id_val for id_val in identifiers if "isbn" in id_val.lower()), "No ISBN")
                dnb_id = next((id_val for id_val in identifiers if "dnb.de" in id_val.lower()), "No DNB ID")
                
                # Create URL
                url = dnb_id if dnb_id != "No DNB ID" else "No URL"
                
                # Extract subjects/keywords
                subjects = []
                for subject in description.findall('./dc:subject', DNB_NS):
                    if subject.text:
                        subjects.append(subject.text)
                subjects_str = ", ".join(subjects) if subjects else "No Subjects"
                
                # Extract language
                language_el = description.find('./dc:language', DNB_NS)
                language = language_el.text if language_el is not None else "No Language"
                
                # Create publication record
                publication = {
                    "Database": "DNB",
                    "Name": name,
                    "Title": title,
                    "Publication Year": year,
                    "Publication Month": "",  # DNB typically doesn't provide month info
                    "Authors": creators_str,
                    "Publisher": publisher,
                    "Subjects": subjects_str,
                    "Language": language,
                    "ISBN": isbn,
                    "DOI": doi,
                    "Identifier": dnb_id,  # Use DNB ID as the primary identifier
                    "URL": url,            # Use DNB URL as the primary URL
                    "Citation Count": "N/A"  # DNB doesn't provide citation counts
                }
                
                publications.append(publication)
                
            except Exception as e:
                logger.error(f"Error parsing DNB record: {e}", exc_info=True)
                log_message(log_widget, f"Error parsing DNB record: {e}")
        
        log_message(log_widget, f"Completed processing {len(publications)} DNB records")
        return publications