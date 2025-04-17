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

logger = logging.getLogger("MedicalSpy")

# Global settings
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 0.5

# DNB Namespace dictionary
dnb_ns = {
    'srw': 'http://www.loc.gov/zing/srw/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'foaf': 'http://xmlns.com/foaf/0.1/',
    'rdau': 'http://rdaregistry.info/Elements/u/',
    'bibo': 'http://purl.org/ontology/bibo/',
    'isbd': 'http://iflastandards.info/ns/isbd/elements/'
}

class DatabaseConnector:
    """Base class for database connectors"""

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.name = "Generic Database"
        self.max_results_per_page = 100
        self.search_fields = []

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

    def construct_query(self, base_query, additional_terms="", date_range=None, 
                      language=None, pub_type=None, field=None):
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

class DNBConnector(DatabaseConnector):
    """Connector for the Deutsche Nationalbibliothek"""

    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "Deutsche Nationalbibliothek"
        self.max_results_per_page = 1000
        self.search_fields = ["Alle Felder", "Titel", "Autor", "Schlagwort", "Jahr"]
        self.base_url = "https://services.dnb.de/sru/dnb"

    def construct_query(self, base_query, additional_terms="", date_range=None, 
                      language=None, pub_type=None, field=None):
        """
        Construct a CQL query for DNB.

        Args:
            base_query (str): The base search query
            additional_terms (str, optional): Additional search terms
            date_range (dict, optional): Date range for the search
            language (str, optional): Language filter
            pub_type (str, optional): Publication type filter
            field (str, optional): Field to search in

        Returns:
            str: The constructed CQL query
        """
        # Transform the search term for DNB format
        query = self.transform_query(base_query)

        # Add additional search terms
        if additional_terms:
            additional_terms = self.transform_query(additional_terms)
            query = f"({query}) AND ({additional_terms})"

        # Add date range if present
        if date_range and date_range.get('start') and date_range.get('end'):
            start_date = date_range['start'].replace("-", "/")
            end_date = date_range['end'].replace("-", "/")
            query += f" AND (\"{start_date}\"[Date - Publication] : \"{end_date}\"[Date - Publication])"

        # Add language if present
        if language:
            query += f" AND language={language}"

        return query

    def transform_query(self, search_term):
        """
        Transform a search term to CQL format for DNB.

        Args:
            search_term (str): The search term to transform

        Returns:
            str: The transformed search term
        """
        if not search_term or not search_term.strip():
            return 'dc.any all "*"'

        # Don't transform if it's already a CQL query
        if search_term.lower().startswith("dc."):
            return search_term

        # Special handling for person names (assuming "first last" format)
        parts = search_term.split()
        if len(parts) == 2:
            # Try both "first last" and "last, first" formats
            return f'dc.creator all ("{search_term}" or "{parts[1]}, {parts[0]}")'

        # General search across all fields
        # Escape double quotes and properly format
        safe_term = search_term.replace('"', '\\"')
        return f'dc.any all "{safe_term}"'

    def search(self, query, params=None):
        """
        Search the DNB for publications.

        Args:
            query (str): The search query
            params (dict, optional): Additional search parameters

        Returns:
            list: List of search results
        """
        logger.info(f"DNB-Search: {query}")
        all_results = []
        start_record = 1
        total_records = None

        # Default parameters if not specified
        if params is None:
            params = {}

        page_size = params.get('page_size', self.max_results_per_page)
        max_results = params.get('max_results', 2000)  # Safety limit

        # Track request attempts for each page
        attempt = 0
        max_attempts = MAX_RETRIES

        while attempt < max_attempts:
            try:
                # Send request to DNB with timeout
                logger.info(f"DNB: Requesting records from position {start_record} (attempt {attempt+1}/{max_attempts})")
                response = self.search_page(query, start_record, page_size)

                # Parse total number of results on first run
                if total_records is None:
                    try:
                        root = ET.fromstring(response)
                        num_elem = root.find('.//srw:numberOfRecords', dnb_ns)
                        if num_elem is not None and num_elem.text:
                            total_records = int(num_elem.text)
                            logger.info(f"DNB: Total number of results: {total_records}")

                            # Apply safety limit if needed
                            if total_records > max_results:
                                logger.warning(f"DNB: Limiting results to {max_results} (total available: {total_records})")
                                total_records = max_results
                        else:
                            logger.warning("DNB: Could not determine total number of results, assuming zero.")
                            total_records = 0
                            break  # No results, exit loop
                    except ET.ParseError as e:
                        logger.error(f"DNB: XML parsing error for result count: {e}")
                        if attempt < max_attempts - 1:
                            attempt += 1
                            time.sleep(RETRY_BACKOFF_FACTOR * (2 ** attempt))
                            continue
                        total_records = 0
                        break

                # Process current page
                page_results = self.parse_results(response)
                if page_results:
                    all_results.extend(page_results)
                    logger.info(f"DNB: Page from {start_record}: {len(page_results)} results")

                    # Reset attempt counter for next page
                    attempt = 0

                    # Check if all results have been retrieved
                    if len(all_results) >= total_records or start_record + page_size > total_records:
                        logger.info(f"DNB: Retrieved all available results ({len(all_results)} records)")
                        break

                    # Next page
                    start_record += page_size
                    time.sleep(0.5)  # Pause between requests
                else:
                    logger.warning(f"DNB: No results in page starting at {start_record}")
                    if attempt < max_attempts - 1:
                        attempt += 1
                        time.sleep(RETRY_BACKOFF_FACTOR * (2 ** attempt))
                        continue
                    break

            except requests.exceptions.Timeout:
                logger.error(f"DNB: Timeout for request from position {start_record}")
                if attempt < max_attempts - 1:
                    attempt += 1
                    time.sleep(RETRY_BACKOFF_FACTOR * (2 ** attempt))
                    continue
                break

            except requests.exceptions.RequestException as e:
                logger.error(f"DNB: Request error from position {start_record}: {e}")
                if attempt < max_attempts - 1:
                    attempt += 1
                    time.sleep(RETRY_BACKOFF_FACTOR * (2 ** attempt))
                    continue
                break

            except ET.ParseError as e:
                logger.error(f"DNB: XML parse error from position {start_record}: {e}")
                if attempt < max_attempts - 1:
                    attempt += 1
                    time.sleep(RETRY_BACKOFF_FACTOR * (2 ** attempt))
                    continue
                break

            except Exception as e:
                logger.error(f"DNB: Unexpected error from position {start_record}: {e}")
                if attempt < max_attempts - 1:
                    attempt += 1
                    time.sleep(RETRY_BACKOFF_FACTOR * (2 ** attempt))
                    continue
                break

        logger.info(f"DNB: Total search completed: {len(all_results)} results")
        return all_results

    def search_page(self, query, start_record, page_size=1000):
        """
        Send a single search request to DNB.

        Args:
            query (str): The search query
            start_record (int): Starting record position
            page_size (int, optional): Maximum number of records to retrieve

        Returns:
            str: The response text
        """
        # Properly encode parameters for DNB SRU service
        params = {
            "version": "1.1",
            "operation": "searchRetrieve",
            "query": query,
            "recordSchema": "RDFxml",
            "maximumRecords": str(page_size),
            "startRecord": str(start_record)
        }

        # Add API key if available (for future compatibility)
        if self.api_key:
            params["apiKey"] = self.api_key

        # Make the request with timeout
        response = requests.get(
            self.base_url, 
            params=params, 
            timeout=DEFAULT_TIMEOUT,
            headers={"User-Agent": "MedicalSpy/3.0"}
        )

        # Check for HTTP errors
        if response.status_code != 200:
            logger.error(f"DNB: HTTP error {response.status_code} for request from position {start_record}")
            logger.debug(f"DNB: Response content: {response.text[:500]}...")
            response.raise_for_status()

        return response.text

    def parse_results(self, response):
        """
        Parse the RDF/XML response from DNB.

        Args:
            response (str): The XML response text

        Returns:
            list: List of parsed results
        """
        results = []
        try:
            root = ET.fromstring(response)
        except ET.ParseError as e:
            logger.error(f"DNB: XML parsing error: {e}")
            return results

        records = root.findall('.//srw:record', dnb_ns)
        if not records:
            logger.warning("DNB: No <record> elements found in response.")
            return results

        for record in records:
            try:
                record_data = record.find('srw:recordData', dnb_ns)
                if record_data is None:
                    continue

                rdf_elem = record_data.find('rdf:RDF', dnb_ns)
                if rdf_elem is None:
                    continue

                # Extract publication details
                description = rdf_elem.find('.//rdf:Description', dnb_ns)
                if description is None:
                    continue

                # Get title
                title_elem = description.find('./dc:title', dnb_ns)
                title = title_elem.text if title_elem is not None and title_elem.text else "No title"

                # Get creators
                creators = []
                for creator in description.findall('./dc:creator', dnb_ns):
                    if creator.text:
                        creators.append(creator.text)
                creators_str = ", ".join(creators) if creators else "No creator information"

                # Get publication year
                year_elem = description.find('./dcterms:issued', dnb_ns)
                year = year_elem.text if year_elem is not None and year_elem.text else "No year"

                # Get identifiers
                identifiers = []
                for identifier in description.findall('./dc:identifier', dnb_ns):
                    if identifier.text:
                        identifiers.append(identifier.text)
                identifier_str = "; ".join(identifiers) if identifiers else "No identifier"

                # Get URL if available
                url = ""
                for identifier in identifiers:
                    if identifier.startswith("http"):
                        url = identifier
                        break

                # Create result entry
                result = {
                    "Name": "",  # Will be filled by the search function
                    "Titel": title,
                    "Creator": creators_str,
                    "Erscheinungsjahr": year,
                    "Identifier": identifier_str,
                    "URL": url,
                    "Datenbank": "Deutsche Nationalbibliothek"
                }

                results.append(result)

            except Exception as e:
                logger.error(f"DNB: Error parsing record: {e}")
                continue

        return results

class PubMedConnector(DatabaseConnector):
    """Connector for PubMed"""

    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "PubMed"
        self.max_results_per_page = 100
        self.search_fields = ["All Fields", "Title", "Author", "Journal", "MeSH Terms"]
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    def construct_query(self, base_query, additional_terms="", date_range=None, 
                      language=None, pub_type=None, field=None):
        """
        Construct a search query for PubMed.

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

        # Add field specifier if provided
        if field and field != "All Fields":
            query = f"{query}[{field}]"

        # Add additional terms
        if additional_terms:
            query = f"({query}) AND ({additional_terms})"

        # Add date range
        if date_range and date_range.get('start') and date_range.get('end'):
            start_date = date_range['start'].replace("-", "/")
            end_date = date_range['end'].replace("-", "/")
            query = f"({query}) AND (\"{start_date}\"[Date - Publication] : \"{end_date}\"[Date - Publication])"

        # Add language filter
        if language:
            query = f"({query}) AND {language}[Language]"

        # Add publication type filter
        if pub_type:
            query = f"({query}) AND {pub_type}[Publication Type]"

        return query

    def search(self, query, params=None):
        """
        Search PubMed for publications.

        Args:
            query (str): The search query
            params (dict, optional): Additional search parameters

        Returns:
            list: List of search results
        """
        logger.info(f"PubMed-Search: {query}")

        # Default parameters if not specified
        if params is None:
            params = {}

        max_results = params.get('max_results', 1000)

        # Step 1: Use ESearch to get PMIDs
        esearch_url = self.base_url + "esearch.fcgi"
        esearch_params = {
            "db": "pubmed",
            "term": urllib.parse.quote(query),  # Properly encode the query term
            "retmax": max_results,
            "retmode": "xml",
            "usehistory": "y"  # Use the history server for better reliability
        }

        # Add API key if available
        if self.api_key:
            esearch_params["api_key"] = self.api_key

        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"PubMed ESearch attempt {attempt + 1}/{MAX_RETRIES}")
                response = requests.get(
                    esearch_url, 
                    params=esearch_params, 
                    timeout=DEFAULT_TIMEOUT
                )
                response.raise_for_status()
                esearch_xml = ET.fromstring(response.content)

                # Check if there's an error message
                error_elem = esearch_xml.find(".//ERROR")
                if error_elem is not None and error_elem.text:
                    logger.error(f"PubMed ESearch returned error: {error_elem.text}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_BACKOFF_FACTOR * (2 ** attempt))
                        continue
                    return []

                # Try to get WebEnv and QueryKey for history server
                web_env = esearch_xml.find(".//WebEnv")
                query_key = esearch_xml.find(".//QueryKey")

                if web_env is not None and web_env.text and query_key is not None and query_key.text:
                    # Use history server approach (more reliable for large result sets)
                    logger.info("Using PubMed history server for retrieval")
                    return self._fetch_from_history(web_env.text, query_key.text, max_results)
                else:
                    # Fallback to direct ID list if history server info not available
                    id_list = [node.text for node in esearch_xml.findall(".//Id")]

                    if not id_list:
                        logger.info(f"No publications found for query: {query}")
                        return []

                    logger.info(f"Found {len(id_list)} PMIDs for query: {query}")
                    return self._fetch_by_id_list(id_list)

            except requests.exceptions.RequestException as e:
                logger.error(f"Error in ESearch request: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF_FACTOR * (2 ** attempt))
                    continue
                return []
            except ET.ParseError as e:
                logger.error(f"Error parsing ESearch response: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF_FACTOR * (2 ** attempt))
                    continue
                return []

        # If we've reached here, all attempts failed
        logger.error(f"All {MAX_RETRIES} attempts to ESearch PubMed failed")
        return []

    def _fetch_from_history(self, web_env, query_key, max_results):
        """
        Fetch results using PubMed history server.

        Args:
            web_env (str): WebEnv parameter from ESearch
            query_key (str): QueryKey parameter from ESearch
            max_results (int): Maximum number of results to retrieve

        Returns:
            list: List of search results
        """
        efetch_url = self.base_url + "efetch.fcgi"

        # Calculate number of batches needed (PubMed recommends max 500 records per request)
        batch_size = 500
        num_batches = (max_results + batch_size - 1) // batch_size  # Ceiling division

        all_results = []

        for batch in range(num_batches):
            start = batch * batch_size

            efetch_params = {
                "db": "pubmed",
                "WebEnv": web_env,
                "query_key": query_key,
                "retstart": start,
                "retmax": min(batch_size, max_results - start),
                "retmode": "xml"
            }

            # Add API key if available
            if self.api_key:
                efetch_params["api_key"] = self.api_key

            for attempt in range(MAX_RETRIES):
                try:
                    logger.info(f"PubMed EFetch batch {batch+1}/{num_batches} attempt {attempt+1}/{MAX_RETRIES}")
                    response = requests.get(
                        efetch_url, 
                        params=efetch_params, 
                        timeout=DEFAULT_TIMEOUT
                    )
                    response.raise_for_status()

                    batch_results = self.parse_results(response.content)
                    all_results.extend(batch_results)

                    logger.info(f"Retrieved {len(batch_results)} records in batch {batch+1}")

                    # Success, move to next batch
                    break

                except requests.exceptions.RequestException as e:
                    logger.error(f"Error in EFetch request (batch {batch+1}): {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_BACKOFF_FACTOR * (2 ** attempt))
                        continue
                    # Skip to next batch if all attempts for this batch failed
                    break

                except ET.ParseError as e:
                    logger.error(f"Error parsing EFetch response (batch {batch+1}): {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_BACKOFF_FACTOR * (2 ** attempt))
                        continue
                    break

            # Small delay between batches to be nice to the API
            if batch < num_batches - 1:
                time.sleep(0.5)

        return all_results

    def _fetch_by_id_list(self, id_list):
        """
        Fetch results using direct ID list.

        Args:
            id_list (list): List of PMIDs to fetch

        Returns:
            list: List of search results
        """
        if not id_list:
            return []

        efetch_url = self.base_url + "efetch.fcgi"

        # If we have more than 200 IDs, split into batches
        batch_size = 200
        all_results = []

        for i in range(0, len(id_list), batch_size):
            batch_ids = id_list[i:i+batch_size]

            efetch_params = {
                "db": "pubmed",
                "id": ",".join(batch_ids),
                "retmode": "xml"
            }

            # Add API key if available
            if self.api_key:
                efetch_params["api_key"] = self.api_key

            for attempt in range(MAX_RETRIES):
                try:
                    logger.info(f"PubMed EFetch (ID list) batch {i//batch_size + 1} attempt {attempt+1}/{MAX_RETRIES}")
                    response = requests.get(
                        efetch_url, 
                        params=efetch_params,
                        timeout=DEFAULT_TIMEOUT
                    )
                    response.raise_for_status()

                    batch_results = self.parse_results(response.content)
                    all_results.extend(batch_results)

                    logger.info(f"Retrieved {len(batch_results)} records in ID batch {i//batch_size + 1}")

                    # Success, move to next batch
                    break

                except requests.exceptions.RequestException as e:
                    logger.error(f"Error in EFetch request (ID batch {i//batch_size + 1}): {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_BACKOFF_FACTOR * (2 ** attempt))
                        continue
                    break

                except ET.ParseError as e:
                    logger.error(f"Error parsing EFetch response (ID batch {i//batch_size + 1}): {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_BACKOFF_FACTOR * (2 ** attempt))
                        continue
                    break

            # Small delay between batches
            if i + batch_size < len(id_list):
                time.sleep(0.5)

        return all_results

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
            return results

        for article in root.findall(".//PubmedArticle"):
            try:
                # Get title
                title_elem = article.find(".//ArticleTitle")
                title = title_elem.text if title_elem is not None and title_elem.text else "No title"

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

                    if last_name is not None and last_name.text and fore_name is not None and fore_name.text:
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

                # Create result entry without citation count initially
                result = {
                    "Name": "",  # Will be filled by the search function
                    "Titel": title,
                    "Veröffentlichungsjahr": year,
                    "Veröffentlichungsmonat": month,
                    "Autoren": authors_str,
                    "PubMed URL": pubmed_url,
                    "DOI URL": doi_url,
                    "PubMed-ID": pmid,
                    "DOI": doi,
                    "Publikationstypen": pub_types_str,
                    "Zitationsanzahl": "Loading...",  # Will be updated later
                    "Datenbank": "PubMed"
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
            "retmode": "xml"
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
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"PubMed: Waiting {delay} seconds before retry {attempt + 1}/{max_retries}")
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
        api_key (str, optional): API key for the database

    Returns:
        DatabaseConnector: A connector for the specified database

    Raises:
        ValueError: If the database is not supported
    """
    if database_name == "PubMed":
        return PubMedConnector(api_key)
    elif database_name == "Deutsche Nationalbibliothek":
        return DNBConnector(api_key)
    else:
        raise ValueError(f"Unsupported database: {database_name}")