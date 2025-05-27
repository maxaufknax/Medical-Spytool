#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Database connectors module
This module provides classes for connecting to different scientific publication databases.
"""

import xml.etree.ElementTree as ET
import requests
import time
import logging
import urllib.parse
from io import BytesIO
from functools import lru_cache
from datetime import datetime
from flask import current_app

logger = logging.getLogger("MedicalSpy")

# Global settings
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 0.5

# DNB Namespace dictionary
dnb_ns = {
    "srw": "http://www.loc.gov/zing/srw/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "rdau": "http://rdaregistry.info/Elements/u/",
    "bibo": "http://purl.org/ontology/bibo/",
    "isbd": "http://iflastandards.info/ns/isbd/elements/",
}


class DatabaseConnector:
    """Base class for database connectors"""

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.name = "Generic Database"
        self.max_results_per_page = 100
        self.search_fields = []
        self.last_error = None
        self.connection_status = "Not connected"

    def search(self, query, params=None):
        """
        Search the database. To be implemented by subclasses.

        Args:
            query (str): The search query
            params (dict, optional): Additional search parameters

        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("This method must be implemented by subclasses")

    def parse_results(self, response):
        """
        Parse the search results. To be implemented by subclasses.

        Args:
            response: The response from the database (string, bytes, or other format)

        Returns:
            list: List of parsed results

        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("This method must be implemented by subclasses")

    def get_citation_count(self, id):
        """
        Get the citation count for a publication.

        Args:
            id (str): The publication identifier

        Returns:
            str: "N/A" by default
        """
        return "N/A"

    def get_available_fields(self):
        """
        Get the available search fields.

        Returns:
            list: List of search fields
        """
        return self.search_fields

    def get_max_results_per_page(self):
        """
        Get the maximum number of results per page.

        Returns:
            int: Maximum number of results per page
        """
        return self.max_results_per_page

    def construct_query(
        self,
        base_query,
        additional_terms="",
        date_range=None,
        language=None,
        pub_type=None,
        field=None,
    ):
        """
        Construct a search query.

        Args:
            base_query (str): The base search query
            additional_terms (str, optional): Additional search terms
            date_range (dict, optional): Date range for the search
            language (str, optional): Language filter
            pub_type (str, optional): Publication type filter
            field (str, optional): Field to search in

        Returns:
            str: The constructed query
        """
        query = base_query
        if additional_terms:
            query = f"({query}) AND ({additional_terms})"
        # Date, language, and publication type are added in specific subclasses
        return query

    def check_connection(self):
        """
        Check if the connector can successfully connect to the database.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Try a simple search to check connection
            self.search("test", {"max_results": 1})
            self.connection_status = "Connected"
            return True
        except Exception as e:
            self.last_error = str(e)
            self.connection_status = f"Connection error: {str(e)}"
            logger.error(f"Connection check failed for {self.name}: {e}")
            return False

    def get_status(self):
        """
        Get the current status of the connector.

        Returns:
            dict: Status information
        """
        return {
            "name": self.name,
            "connection_status": self.connection_status,
            "api_key_configured": bool(self.api_key),
            "last_error": self.last_error,
        }

    def handle_request_error(self, e, request_info=""):
        """
        Handle and log a request error.

        Args:
            e (Exception): The exception
            request_info (str): Additional information about the request

        Returns:
            str: Error message
        """
        error_msg = f"Error in {self.name} request"
        if request_info:
            error_msg += f" ({request_info})"
        error_msg += f": {str(e)}"

        self.last_error = error_msg
        logger.error(error_msg)

        if hasattr(e, "response") and hasattr(e.response, "status_code"):
            logger.error(f"{self.name} HTTP error code: {e.response.status_code}")

        return error_msg


class DNBConnector(DatabaseConnector):
    """Connector for Deutsche Nationalbibliothek"""

    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "Deutsche Nationalbibliothek"
        self.max_results_per_page = 100  # Reduced to avoid timeouts
        self.search_fields = ["Alle Felder", "Titel", "Autor", "Schlagwort", "Jahr"]
        self.base_url = "https://services.dnb.de/sru/dnb"

    def search(self, query, params=None):
        """Search DNB for publications."""
        logger.info(f"DNB-Search: {query}")
        all_results = []
        start_record = 1
        total_records = None
        attempt = 0
        max_attempts = MAX_RETRIES
        
        if params is None:
            params = {}

        page_size = min(params.get("page_size", self.max_results_per_page), 100)
        max_results = params.get("max_results", 1000)  # Safety limit

        while attempt < max_attempts:
            try:
                logger.info(f"DNB: Requesting records from position {start_record}")
                response = self.search_page(query, start_record, page_size)

                # Parse total number of results on first run
                if total_records is None:
                    try:
                        root = ET.fromstring(response)
                        num_elem = root.find(".//srw:numberOfRecords", dnb_ns)
                        if num_elem is not None and num_elem.text:
                            total_records = int(num_elem.text)
                            logger.info(f"DNB: Total number of results: {total_records}")

                            # Apply safety limit if needed
                            if total_records > max_results:
                                logger.warning(f"DNB: Limiting results to {max_results}")
                                total_records = max_results
                        else:
                            logger.warning("DNB: Could not determine total number of records")
                            total_records = 0
                            break

                    except ET.ParseError as e:
                        logger.error(f"DNB: XML parse error for result count: {e}")
                        if attempt < max_attempts - 1:
                            attempt += 1
                            time.sleep(RETRY_BACKOFF_FACTOR * (2**attempt))
                            continue
                        break

                # Process current page
                try:
                    page_results = self.parse_results(response)
                    if page_results:
                        all_results.extend(page_results)
                        logger.info(f"DNB: Page {start_record}: {len(page_results)} results")
                    else:
                        logger.warning(f"DNB: No results in page starting at {start_record}")
                        break

                    # Check if we've retrieved all results
                    if total_records and start_record + page_size > total_records:
                        break

                    # Next page
                    start_record += page_size
                    time.sleep(0.5)  # Pause between requests

                except ET.ParseError as e:
                    logger.error(f"DNB: XML parse error for results: {e}")
                    if attempt < max_attempts - 1:
                        attempt += 1
                        time.sleep(RETRY_BACKOFF_FACTOR * (2**attempt))
                        continue
                    break

            except requests.exceptions.Timeout:
                logger.error(f"DNB: Request timeout at position {start_record}")
                if attempt < max_attempts - 1:
                    attempt += 1
                    time.sleep(RETRY_BACKOFF_FACTOR * (2**attempt))
                    continue
                break

            except requests.exceptions.RequestException as e:
                logger.error(f"DNB: Request error at position {start_record}: {e}")
                if attempt < max_attempts - 1:
                    attempt += 1
                    time.sleep(RETRY_BACKOFF_FACTOR * (2**attempt))
                    continue
                break

            except Exception as e:
                logger.error(f"DNB: Unexpected error at position {start_record}: {e}")
                if attempt < max_attempts - 1:
                    attempt += 1
                    time.sleep(RETRY_BACKOFF_FACTOR * (2**attempt))
                    continue
                break

        logger.info(f"DNB: Search completed, {len(all_results)} total results")
        return all_results

    def parse_results(self, response):
        """
        Parse the XML response from DNB.
        
        Args:
            response (str): The XML content to parse as a string
            
        Returns:
            list: List of parsed results with standardized fields
        """
        results = []
        
        try:
            root = ET.fromstring(response)
        except ET.ParseError as e:
            logger.error(f"Error parsing DNB response: {e}")
            self.last_error = f"Error parsing DNB response: {str(e)}"
            return results
            
        # Find all records in the response
        records = root.findall(".//srw:record", dnb_ns)
        logger.info(f"DNB: Found {len(records)} records in response")
        
        for record in records:
            try:
                # Extract the RDF record content which contains the actual data
                record_data = record.find(".//srw:recordData", dnb_ns)
                if record_data is None:
                    logger.warning("DNB: Record data not found in record")
                    continue
                
                # Find the RDF description which contains all the metadata
                rdf_description = record_data.find(".//rdf:Description", dnb_ns)
                if rdf_description is None:
                    logger.warning("DNB: RDF description not found in record")
                    continue
                
                # Extract title
                title_elem = rdf_description.find("./dc:title", dnb_ns)
                title = title_elem.text if title_elem is not None and title_elem.text else "No title"
                
                # Extract publication year
                year = "No year"
                issued_elem = rdf_description.find("./dcterms:issued", dnb_ns)
                if issued_elem is not None and issued_elem.text:
                    # Try to extract year from date format (could be YYYY or YYYY-MM-DD)
                    year_match = issued_elem.text.split("-")[0] if "-" in issued_elem.text else issued_elem.text
                    year = year_match
                
                # Extract authors
                authors = []
                creator_elems = rdf_description.findall("./dc:creator", dnb_ns)
                contributor_elems = rdf_description.findall("./dc:contributor", dnb_ns)
                
                # Process both creators and contributors (authors)
                for author_elem in creator_elems + contributor_elems:
                    if author_elem is not None and author_elem.text:
                        authors.append(author_elem.text)
                
                authors_str = ", ".join(authors) if authors else "No authors"
                
                # Extract identifiers (ISBN, ISSN, etc.)
                identifiers = {}
                identifier_elems = rdf_description.findall("./dc:identifier", dnb_ns)
                
                for id_elem in identifier_elems:
                    if id_elem is not None and id_elem.text:
                        id_text = id_elem.text.strip()
                        if id_text.startswith("http://d-nb.info/gnd/"):
                            identifiers["GND"] = id_text
                        elif id_text.startswith("DOI:"):
                            identifiers["DOI"] = id_text.replace("DOI:", "").strip()
                        elif id_text.startswith("ISBN"):
                            identifiers["ISBN"] = id_text
                
                # Extract DNB ID (catalogue ID)
                dnb_id = "No ID"
                about_attr = rdf_description.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about")
                if about_attr:
                    # Extract ID from the URL pattern http://d-nb.info/XXXXXXXXX
                    parts = about_attr.split('/')
                    if len(parts) > 3:
                        dnb_id = parts[-1]
                
                # Extract URL
                dnb_url = f"https://d-nb.info/{dnb_id}" if dnb_id != "No ID" else ""
                
                # Extract publication types
                pub_types = []
                type_elems = rdf_description.findall("./dc:type", dnb_ns)
                
                for type_elem in type_elems:
                    if type_elem is not None and type_elem.text:
                        pub_types.append(type_elem.text)
                
                pub_types_str = ", ".join(pub_types) if pub_types else "No publication types"
                
                # Extract publisher
                publisher = "No publisher"
                publisher_elem = rdf_description.find("./dc:publisher", dnb_ns)
                if publisher_elem is not None and publisher_elem.text:
                    publisher = publisher_elem.text
                
                # Extract language
                language = "No language"
                language_elem = rdf_description.find("./dc:language", dnb_ns)
                if language_elem is not None and language_elem.text:
                    language = language_elem.text
                
                # Create standardized result entry
                result = {
                    "Name": "",  # Will be filled by the search function
                    "Title": title,
                    "Publication Year": year,
                    "Publication Month": "",  # Not always available in DNB
                    "Authors": authors_str,
                    "DNB URL": dnb_url,
                    "DOI URL": f"https://doi.org/{identifiers.get('DOI', '')}" if "DOI" in identifiers else "",
                    "DNB-ID": dnb_id,
                    "DOI": identifiers.get("DOI", "No DOI"),
                    "ISBN": identifiers.get("ISBN", "No ISBN"),
                    "Publication Types": pub_types_str,
                    "Publisher": publisher,
                    "Language": language,
                    "Citation Count": "N/A",  # DNB doesn't provide citation counts
                    "Database": "Deutsche Nationalbibliothek",
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error parsing DNB record: {str(e)}")
                continue
        
        return results

    def search_page(self, query, start_record, page_size=100):
        """Send a single search request to DNB."""
        params = {
            "version": "1.1",
            "operation": "searchRetrieve",
            "query": self.transform_query(query),
            "recordSchema": "RDFxml",
            "maximumRecords": str(page_size),
            "startRecord": str(start_record)
        }

        if self.api_key:
            params["accessToken"] = self.api_key

        try:
            # Log the encoded query for debugging
            logger.debug(f"DNB query URL params: {params}")
            
            # Make the request with timeout
            response = requests.get(
                self.base_url,
                params=params,
                timeout=DEFAULT_TIMEOUT,
                headers={"User-Agent": "MedicalSpy/3.0"}
            )

            # Check for HTTP errors
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            self.last_error = f"DNB request error: {str(e)}"
            logger.error(f"DNB: {self.last_error}")
            raise

    def transform_query(self, search_term):
        """Transform a search term into DNB's CQL format."""
        if not search_term:
            return 'dc.any all "*"'  # Default to match all if empty

        # If the search term is likely already a valid CQL query (e.g., contains operators or field prefixes)
        # or is meant to be passed as is by advanced users.
        # This is a simple heuristic; more robust parsing might be needed for complex cases.
        if any(op in search_term for op in [" AND ", " OR ", " NOT ", "=", ">", "<"]) or \
           (":" in search_term and not search_term.startswith("http:")): # Avoid treating URLs like http://... as CQL
            logger.debug(f"DNB transform_query: Treating as pre-formatted CQL: {search_term}")
            # Minimal escaping for pre-formatted CQL: ensure existing quotes are valid if any part is user input.
            # This path assumes the user knows CQL. If parts are from user input, they should be individually processed.
            # For now, this path returns the term as is, relying on user's CQL correctness.
            return search_term

        # For general search terms, escape for literal interpretation within quotes.
        # Escape backslashes first, then double quotes.
        processed_term = search_term.replace("\\", "\\\\").replace('"', '\\"')
        
        # Heuristic for person names (last name, first name or first name last name)
        # This is basic and might not always be correct for all names or search intentions.
        # Consider if 'dc.author' is the best field or if a general person index 'per' exists and is better.
        # Example: DNB GKD uses 'piz' for person index. For SRU, 'dc.creator' or 'dc.contributor' often used.
        # Using 'dc.author' as a common, though potentially broad, interpretation.
        terms = processed_term.split()
        if len(terms) == 2:
            first, last = terms[0], terms[1]
            # Formatted for typical "Last, First" or "First Last" author searches.
            # Ensure each part is quoted if it contains spaces, though `processed_term` handles outer quotes.
            # This heuristic is very basic. A proper solution would involve dedicated author fields if possible.
            # For `dc.author all "..."`, the full name string is within the quotes.
            # Example: (dc.author all "Doe, John" OR dc.author all "John Doe")
            # Using 'dc.any' might be safer if field is unknown, or specific 'per' (person) index if available.
            # The original used dc.author. Let's stick to that for now but refine quoting.
            # If the whole term is "Max Mustermann", it becomes `dc.any all "Max Mustermann"` below.
            # This specific person heuristic might be better handled by `construct_query` if an author field is specified.
            # For now, simplifying: if it's two terms, assume it's a name and search broadly.
            # The original heuristic:
            # return f'(dc.author all "{last}, {first}" OR dc.author all "{first} {last}")'
            # This creates a complex CQL structure directly.
            # A simpler approach for transform_query (which is about transforming a single search_term string):
            # Fall through to the general term search, which is `dc.any all " পুরো টার্ম "`.
            # If specific author search is needed, it should be handled by `construct_query` using an author field.
            pass # Let it fall through to general term search for now.

        # General search: wrap the processed term in quotes and use 'dc.any all'.
        # This means the entire processed_term is treated as a phrase.
        return f'dc.any all "{processed_term}"'

    def construct_query(self, base_query, additional_terms="", date_range=None, 
                        language=None, pub_type=None, field=None,
                        author_filter=None, title_filter=None, journal_filter=None,
                        # Database-specific flags
                        pubmed_full_text_only=False, pubmed_free_access_only=False,
                        dnb_online_only=False, dnb_academic_only=False, 
                        **kwargs): # Catch-all for unused kwargs from other connectors
        """
        Construct a DNB CQL query string from various components.
        Uses transform_query for processing individual search terms.
        """
        query_parts = []

        # Main query (base_query) and optional specified field
        if base_query:
            # DNB specific field mapping
            field_map_dnb = {
                "Alle Felder": "dc.any",
                "Titel": "dc.title",
                "Autor": "dc.creator", # Or 'per' if using a person index directly
                "Schlagwort": "dc.subject",
                "Jahr": "jhr", # Or dc.date
            }
            cql_field = field_map_dnb.get(field, "dc.any") # Default to dc.any
            
            # Use transform_query to process the base_query string for the given field context
            # transform_query itself returns a full `field all "term"` like string if not already CQL-like
            # So, we need to adapt this. If base_query is simple, transform_query wraps it.
            # If field is specified, we want `cql_field all "transformed_base_query"`
            
            # Let transform_query handle if base_query is complex (contains AND, OR etc.)
            if any(op in base_query for op in [" AND ", " OR ", " NOT ", "=", ">", "<"]) or \
               (":" in base_query and not base_query.startswith("http:")):
                transformed_base_query = self.transform_query(base_query) # Returns as is
            else: # Simple term, apply field and quote
                escaped_base_query = base_query.replace("\\", "\\\\").replace('"', '\\"')
                transformed_base_query = f'{cql_field} all "{escaped_base_query}"'
            
            query_parts.append(f"({transformed_base_query})")


        # Additional terms are treated as a general dc.any search and ANDed
        if additional_terms:
            transformed_additional = self.transform_query(additional_terms) # dc.any all "..."
            query_parts.append(f"AND ({transformed_additional})")

        # Specific filters - these are typically ANDed
        if author_filter:
            # Assuming author_filter is a name string. Use transform_query for proper formatting.
            # This will result in dc.any all "author_name". For specific author field:
            escaped_author = author_filter.replace("\\", "\\\\").replace('"', '\\"')
            query_parts.append(f'AND (dc.creator all "{escaped_author}")') 
            # Or use 'per' if DNB supports it broadly: query_parts.append(f'AND (per="{escaped_author}")')

        if title_filter:
            escaped_title = title_filter.replace("\\", "\\\\").replace('"', '\\"')
            query_parts.append(f'AND (dc.title all "{escaped_title}")')
        
        # Journal filter for DNB (e.g., searching for series title 'zti' or part of dc.source)
        if journal_filter:
            escaped_journal = journal_filter.replace("\\", "\\\\").replace('"', '\\"')
            query_parts.append(f'AND (dc.source all "{escaped_journal}")') # Example, DNB might have better fields like 'zti'

        if language:
            # Map common language names to DNB's ISO 639-2/b codes (ger, eng, fre etc.)
            lang_map = {"german": "ger", "english": "eng", "french": "fre"} # Add more as needed
            lang_code = lang_map.get(language.lower(), language) # Use raw if not in map
            query_parts.append(f'AND (dc.language = "{lang_code}")')

        if pub_type:
            # DNB uses specific URNs or keywords for publication types (e.g., Hochschulschrift, Monografie)
            # This mapping would need to be more extensive based on DNB's specific values for dc.type or mat.
            # For example: dc.type="Hochschulschrift"
            # For now, treating pub_type as a keyword search in dc.type
            escaped_pub_type = pub_type.replace("\\", "\\\\").replace('"', '\\"')
            query_parts.append(f'AND (dc.type all "{escaped_pub_type}")')

        if date_range:
            start_date = date_range.get("start", "")[:4] # Assuming YYYY from YYYY-MM-DD
            end_date = date_range.get("end", "")[:4]
            
            if start_date and end_date:
                if start_date == end_date:
                    query_parts.append(f'AND (jhr = "{start_date}")')
                else:
                    query_parts.append(f'AND (jhr >= "{start_date}" AND jhr <= "{end_date}")')
            elif start_date:
                query_parts.append(f'AND (jhr >= "{start_date}")')
            elif end_date:
                query_parts.append(f'AND (jhr <= "{end_date}")')

        # DNB-specific flags
        if dnb_online_only:
            # Common DNB SRU syntax for online resources is often via 'location' index
            # TODO: Verify exact DNB SRU syntax for filtering online resources. 'location = "online"' is a common pattern.
            query_parts.append('AND (location = "online")') 
        if dnb_academic_only:
            # This is highly dependent on DNB's indexing. Could be dc.type or other fields.
            # Using a placeholder, assuming 'Hochschulschrift' is one type of academic work.
            # TODO: Verify exact DNB SRU syntax for filtering academic publications.
            query_parts.append('AND (dc.type all "Hochschulschrift" OR dc.type all "academic")')
        
        final_query = " ".join(part for part in query_parts if part).strip()
        # Clean up leading/trailing ANDs and multiple spaces
        while final_query.startswith("AND "):
            final_query = final_query[4:].strip()
        while "  " in final_query:
            final_query = final_query.replace("  ", " ")
            
        logger.debug(f"DNB constructed query: {final_query}")
        return final_query


class PubMedConnector(DatabaseConnector):
    """Connector for PubMed"""

    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "PubMed"
        self.max_results_per_page = 1000
        # Added more specific fields that PubMed supports
        self.search_fields = [
            "All Fields", "Title/Abstract", "Title", "Abstract", "Author", 
            "Journal", "MeSH Terms", "Publication Type", "Language", "Publication Date"
        ]
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    def construct_query(self, base_query, additional_terms="", date_range=None, 
                        language=None, pub_type=None, field=None, 
                        author_filter=None, title_filter=None, journal_filter=None,
                        # Database-specific flags
                        pubmed_full_text_only=False, pubmed_free_access_only=False,
                        dnb_online_only=False, dnb_academic_only=False, # These will be ignored by PubMed but are passed
                        **kwargs): # Catch-all for other unused kwargs
        """
        Construct a PubMed query string from various components.
        """
        query_parts = []

        # Main query (base_query) and optional specified field
        if base_query:
            if field and field != "All Fields":
                # Map user-friendly field names to PubMed tags
                field_map = {
                    "Title/Abstract": "[TIAB]",
                    "Title": "[TI]",
                    "Abstract": "[AB]",
                    "Author": "[AU]",
                    "Journal": "[TA]", # Journal Title Abbreviation or Full Title
                    "MeSH Terms": "[MH]",
                    "Publication Type": "[PT]",
                    "Language": "[LA]",
                    # "Publication Date": "[DP]", # Handled by date_range
                }
                query_parts.append(f"{base_query}{field_map.get(field, '')}")
            else:
                query_parts.append(base_query) # Search all fields

        if additional_terms:
            query_parts.append(f"AND ({additional_terms})") # Assume additional terms are general

        # Specific filters - these are typically ANDed
        if author_filter:
            query_parts.append(f"AND ({author_filter}[AU])")
        if title_filter:
            query_parts.append(f"AND ({title_filter}[TI])")
        if journal_filter:
             query_parts.append(f"AND ({journal_filter}[TA])")

        if language:
            # Assuming language is provided as full name e.g., "English", "German"
            query_parts.append(f"AND ({language}[LA])")

        if pub_type:
            # Assuming pub_type is a valid PubMed publication type e.g., "Journal Article"
            query_parts.append(f"AND ({pub_type}[PT])")

        if date_range:
            start_date = date_range.get("start")
            end_date = date_range.get("end")
            # PubMed date format YYYY/MM/DD or YYYY/MM or YYYY
            # Assuming start_date and end_date are in "YYYY-MM-DD" format from parse_date_range
            # Convert to YYYY/MM/DD
            start_date_pubmed = start_date.replace("-", "/") if start_date else "mindate"
            end_date_pubmed = end_date.replace("-", "/") if end_date else "maxdate"
            
            if start_date and end_date:
                query_parts.append(f"AND ({start_date_pubmed[0:10]}:{end_date_pubmed[0:10]}[DP])")
            elif start_date:
                query_parts.append(f"AND ({start_date_pubmed[0:10]}:maxdate[DP])")
            elif end_date:
                query_parts.append(f"AND (mindate:{end_date_pubmed[0:10]}[DP])")

        # PubMed-specific boolean flags
        if pubmed_full_text_only:
            query_parts.append("AND (pubmed full text[sb])")
        if pubmed_free_access_only:
            query_parts.append("AND (free full text[sb])")
        
        final_query = " ".join(part for part in query_parts if part)
        # Clean up leading/trailing ANDs and multiple spaces
        final_query = final_query.strip()
        while final_query.startswith("AND "):
            final_query = final_query[4:].strip()
        while "  " in final_query:
            final_query = final_query.replace("  ", " ")
            
        logger.debug(f"PubMed constructed query: {final_query}")
        return final_query

    def search(self, query, params=None):
        """Search PubMed for publications."""
        logger.info(f"PubMed-Search: {query}")
        
        if params is None:
            params = {}
            
        max_results = params.get("max_results", 1000)
        
        # Step 1: Use ESearch to get PMIDs
        esearch_url = self.base_url + "esearch.fcgi"
        esearch_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",  # Using JSON format for better handling
            "usehistory": "y"
        }

        # Check for API key and add a more descriptive warning
        if self.api_key:
            esearch_params["api_key"] = self.api_key
            logger.info("PubMed: Using configured API key for requests")
        else:
            logger.warning("PubMed: No API key provided, requests will be rate limited to 3/sec. Consider adding a PubMed API key in the configuration.")

        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"PubMed ESearch attempt {attempt + 1}/{MAX_RETRIES}")
                response = requests.get(
                    esearch_url,
                    params=esearch_params,
                    timeout=DEFAULT_TIMEOUT
                )
                response.raise_for_status()
                
                try:
                    search_result = response.json()
                    if "esearchresult" not in search_result:
                        logger.error(f"PubMed: Invalid JSON response format: {search_result}")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(RETRY_BACKOFF_FACTOR * (2**attempt))
                            continue
                        self.last_error = "Invalid response format from PubMed API"
                        return []

                    result = search_result["esearchresult"]
                    if "error" in result:
                        logger.error(f"PubMed ESearch returned error: {result['error']}")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(RETRY_BACKOFF_FACTOR * (2**attempt))
                            continue
                        self.last_error = f"PubMed API error: {result['error']}"
                        return []
                except ValueError as json_error:
                    logger.error(f"PubMed: Failed to parse JSON response: {json_error}")
                    logger.debug(f"Response content: {response.text[:500]}")  # Log first 500 chars
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_BACKOFF_FACTOR * (2**attempt))
                        continue
                    self.last_error = "Failed to parse PubMed API response"
                    return []

                # Get the IDs and query key
                id_list = result.get("idlist", [])
                web_env = result.get("webenv")
                query_key = result.get("querykey")

                if not id_list:
                    logger.info("PubMed: No results found")
                    return []

                logger.info(f"PubMed: Found {len(id_list)} results")
                
                # Step 2: Use EFetch to get full records in batches to avoid URL length issues
                results = []
                batch_size = 200  # Reduced batch size to avoid URL length problems
                
                for i in range(0, len(id_list), batch_size):
                    batch_ids = id_list[i:i + batch_size]
                    logger.info(f"PubMed: Fetching batch {i//batch_size + 1}/{(len(id_list)-1)//batch_size + 1} ({len(batch_ids)} IDs)")
                    
                    efetch_url = self.base_url + "efetch.fcgi"
                    efetch_params = {
                        "db": "pubmed",
                        "id": ",".join(batch_ids),
                        "retmode": "xml",  # Keep XML for detailed data
                        "retmax": len(batch_ids)
                    }

                    if self.api_key:
                        efetch_params["api_key"] = self.api_key

                    batch_response = requests.get(
                        efetch_url,
                        params=efetch_params,
                        timeout=DEFAULT_TIMEOUT
                    )
                    batch_response.raise_for_status()

                    batch_results = self.parse_results(batch_response.content)
                    results.extend(batch_results)
                    logger.info(f"PubMed: Batch {i//batch_size + 1} returned {len(batch_results)} records")
                    
                    # Add delay between batches to respect rate limits
                    if i + batch_size < len(id_list):
                        time.sleep(0.34 if self.api_key else 1.0)  # 3/sec with API key, 1/sec without

                logger.info(f"PubMed: Successfully parsed {len(results)} total records")
                return results

            except requests.exceptions.Timeout:
                logger.error("PubMed: Request timed out")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF_FACTOR * (2**attempt))
                    continue
                self.last_error = "PubMed request timed out"
                return []

            except requests.exceptions.RequestException as e:
                logger.error(f"PubMed: Request error: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF_FACTOR * (2**attempt))
                    continue
                self.last_error = f"PubMed request error: {str(e)}"
                return []

            except ET.ParseError as e:
                logger.error(f"PubMed: XML parse error: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF_FACTOR * (2**attempt))
                    continue
                self.last_error = f"PubMed XML parsing error: {str(e)}"
                return []

            except Exception as e:
                logger.error(f"PubMed: Unexpected error: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF_FACTOR * (2**attempt))
                    continue
                self.last_error = f"PubMed unexpected error: {str(e)}"
                return []

        self.last_error = "All PubMed search attempts failed"
        return []

    def parse_results(self, response):
        """
        Parse the XML response from PubMed.

        Args:
            response (bytes): The XML content to parse

        Returns:
            list: List of parsed results
        """
        results = []

        try:
            root = ET.fromstring(response)
        except ET.ParseError as e:
            logger.error(f"Error parsing PubMed response: {e}")
            self.last_error = f"Error parsing PubMed response: {str(e)}"
            return results

        for article in root.findall(".//PubmedArticle"):
            try:
                # Get title
                title_elem = article.find(".//ArticleTitle")
                title = (
                    title_elem.text if title_elem is not None and title_elem.text else "No title"
                )

                # Get publication date
                pub_date_elem = article.find(".//PubDate")
                year = "No year"
                month = ""

                if pub_date_elem is not None:
                    year_elem = pub_date_elem.find("Year")
                    month_elem = pub_date_elem.find("Month")

                    if year_elem is not None and year_elem.text:
                        year = year_elem.text

                    if month_elem is not None and month_elem.text:
                        month = month_elem.text

                # Get authors
                authors = []
                for author in article.findall(".//Author"):
                    last_name = author.find(".//LastName")
                    fore_name = author.find(".//ForeName")

                    if (
                        last_name is not None
                        and last_name.text
                        and fore_name is not None
                        and fore_name.text
                    ):
                        authors.append(f"{fore_name.text} {last_name.text}")
                    elif last_name is not None and last_name.text:
                        authors.append(last_name.text)

                authors_str = ", ".join(authors) if authors else "No authors"

                # Get PMID
                pmid_elem = article.find(".//PMID")
                pmid = pmid_elem.text if pmid_elem is not None and pmid_elem.text else "No PMID"

                # Get DOI
                doi = "No DOI"
                doi_elem = article.find('.//ArticleId[@IdType="doi"]')
                if doi_elem is not None and doi_elem.text:
                    doi = doi_elem.text

                # Get URLs
                pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid != "No PMID" else ""
                doi_url = f"https://doi.org/{doi}" if doi != "No DOI" else ""

                # Get publication types
                pub_types = []
                for pub_type in article.findall(".//PublicationType"):
                    if pub_type.text:
                        pub_types.append(pub_type.text)

                pub_types_str = ", ".join(pub_types) if pub_types else "No publication types"

                # Create result entry with standardized English field names
                result = {
                    "Name": "",  # Will be filled by the search function
                    "Title": title,
                    "Publication Year": year,
                    "Publication Month": month,
                    "Authors": authors_str,
                    "PubMed URL": pubmed_url,
                    "DOI URL": doi_url,
                    "PubMed-ID": pmid,
                    "DOI": doi,
                    "Publication Types": pub_types_str,
                    "Citation Count": "Loading...",  # Will be updated later
                    "Database": "PubMed",
                }

                results.append(result)

            except Exception as e:
                logger.error(f"Error parsing PubMed article: {e}")
                continue

        return results

    @lru_cache(maxsize=128)
    def get_citation_count(self, pmid, timeout=5):
        """
        Get the citation count for a PubMed article.

        Args:
            pmid (str): The PubMed ID
            timeout (int): Request timeout in seconds

        Returns:
            int or str: The citation count or an error message
        """
        if not pmid or pmid == "No PMID":
            return "N/A"

        elink_url = self.base_url + "elink.fcgi"
        params = {
            "dbfrom": "pubmed",
            "linkname": "pubmed_pubmed_citedin",
            "id": pmid,
            "retmode": "xml",
        }

        # Add API key if available
        if self.api_key:
            params["api_key"] = self.api_key

        max_retries = 5  # Increased retries
        base_delay = 1.0  # Increased base delay

        for attempt in range(max_retries):
            try:
                # Add delay before request after first attempt
                if attempt > 0:
                    delay = base_delay * (2**attempt)  # Exponential backoff
                    logger.info(
                        f"PubMed: Waiting {delay} seconds before retry {attempt + 1}/{max_retries}"
                    )
                    time.sleep(delay)

                response = requests.get(elink_url, params=params, timeout=timeout)
                if response.status_code == 429:
                    continue  # Skip to next attempt with longer delay

                response.raise_for_status()
                xml = ET.fromstring(response.content)
                count = len(xml.findall(".//LinkSetDb/Link/Id"))
                return count
            except requests.exceptions.HTTPError as e:
                logger.error(f"PubMed: HTTP error for PMID {pmid}: {e}")
                if response.status_code != 429:  # If not rate limit, return error
                    return "Fehler"
            except ET.ParseError as e:
                logger.error(f"PubMed: Parse error for PMID {pmid}: {e}")
                return "Fehler XML"
            except Exception as e:
                logger.error(f"PubMed: Unexpected error for PMID {pmid}: {e}")
                return "Fehler"

        logger.error(f"PubMed: Max retries ({max_retries}) exceeded for PMID {pmid}")
        return "Fehler 429"


def get_connector_for_database(database_name, api_key=None):
    """
    Get a connector for the specified database.

    Args:
        database_name (str): The name of the database
        api_key (str, optional): API key for the database (deprecated, use app.config instead)

    Returns:
        DatabaseConnector: A connector for the specified database

    Raises:
        ValueError: If the database is not supported
    """
    # Get API keys from Flask app config if available, otherwise use None
    pubmed_api_key = None
    dnb_api_key = None
    try:
        if current_app:
            pubmed_api_key = current_app.config.get("PUBMED_API_KEY")
            dnb_api_key = current_app.config.get("DNB_API_KEY")
    except RuntimeError:
        # Not in application context, use provided key (if any)
        logger.warning("Not in application context, can't get API keys from config")

    if database_name == "PubMed":
        # Use pubmed_api_key from app.config, fall back to provided api_key
        return PubMedConnector(api_key=pubmed_api_key or api_key)
    elif database_name == "Deutsche Nationalbibliothek":
        # Use dnb_api_key from app.config, fall back to provided api_key
        return DNBConnector(api_key=dnb_api_key or api_key)
    elif database_name == "DNB":
        # Support DNB as alias for Deutsche Nationalbibliothek 
        return DNBConnector(api_key=dnb_api_key or api_key)
    else:
        raise ValueError(f"Unsupported database: {database_name}")
