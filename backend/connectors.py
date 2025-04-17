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
from functools import lru_cache

logger = logging.getLogger("MedicalSpy")

# DNB Namespace dictionary
dnb_ns = {
    'srw': 'http://www.loc.gov/zing/srw/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'foaf': 'http://xmlns.com/foaf/0.1/',
    'rdau': 'http://rdaregistry.info/Elements/u/'
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
            response: The response from the database
            
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
        if not search_term.lower().startswith("dc.any"):
            parts = search_term.split()
            if len(parts) == 2:
                return f'dc.any all ("{search_term}" or "{parts[1]}, {parts[0]}")'
            else:
                return f'dc.any all "{search_term}"'
        return search_term
        
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
        
        while True:
            try:
                # Send request to DNB
                response = self.search_page(query, start_record, page_size)
                
                # Parse total number of results on first run
                if total_records is None:
                    try:
                        root = ET.fromstring(response)
                        num_elem = root.find('.//srw:numberOfRecords', dnb_ns)
                        if num_elem is not None and num_elem.text:
                            total_records = int(num_elem.text)
                            logger.info(f"DNB: Total number of results: {total_records}")
                        else:
                            total_records = 0
                            logger.warning("DNB: Could not determine total number of results.")
                    except ET.ParseError as e:
                        logger.error(f"DNB: XML parsing error for result count: {e}")
                        total_records = 0
                
                # Process current page
                page_results = self.parse_results(response)
                all_results.extend(page_results)
                logger.info(f"DNB: Page from {start_record}: {len(page_results)} results")
                
                # Check if all results have been retrieved
                if total_records is not None and start_record + page_size > total_records:
                    break
                
                # Next page
                start_record += page_size
                time.sleep(0.5)  # Pause between requests
                
            except Exception as e:
                logger.error(f"DNB: Error in request from position {start_record}: {e}")
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
        params = {
            "version": "1.1",
            "operation": "searchRetrieve",
            "query": query,
            "recordSchema": "RDFxml",
            "maximumRecords": str(page_size),
            "startRecord": str(start_record)
        }
        
        response = requests.get(self.base_url, params=params)
        if response.status_code != 200:
            logger.error(f"DNB: HTTP error {response.status_code} for request from position {start_record}")
            response.raise_for_status()
            
        return response.text
        
    def parse_results(self, xml_text):
        """
        Parse the RDF/XML response from DNB.
        
        Args:
            xml_text (str): The XML response text
            
        Returns:
            list: List of parsed results
        """
        results = []
        try:
            root = ET.fromstring(xml_text)
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
            "term": query,
            "retmax": max_results,
            "retmode": "xml"
        }
        
        # Add API key if available
        if self.api_key:
            esearch_params["api_key"] = self.api_key
            
        try:
            response = requests.get(esearch_url, params=esearch_params)
            response.raise_for_status()
            esearch_xml = ET.fromstring(response.content)
            id_list = [node.text for node in esearch_xml.findall(".//Id")]
            
            if not id_list:
                logger.info(f"No publications found for query: {query}")
                return []
                
            logger.info(f"Found {len(id_list)} PMIDs for query: {query}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in ESearch request: {e}")
            return []
        except ET.ParseError as e:
            logger.error(f"Error parsing ESearch response: {e}")
            return []
            
        # Step 2: Use EFetch to get publication details
        efetch_url = self.base_url + "efetch.fcgi"
        efetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml"
        }
        
        # Add API key if available
        if self.api_key:
            efetch_params["api_key"] = self.api_key
            
        try:
            response = requests.get(efetch_url, params=efetch_params)
            response.raise_for_status()
            return self.parse_results(response.content)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in EFetch request: {e}")
            return []
        
    def parse_results(self, xml_content):
        """
        Parse the XML response from PubMed.
        
        Args:
            xml_content (bytes): The XML content to parse
            
        Returns:
            list: List of parsed results
        """
        results = []
        
        try:
            root = ET.fromstring(xml_content)
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
                
                # Get citation count
                citation_count = self.get_citation_count(pmid) if pmid != "No PMID" else "N/A"
                
                # Create result entry
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
                    "Zitationsanzahl": citation_count,
                    "Datenbank": "PubMed"
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error parsing PubMed article: {e}")
                continue
                
        return results
        
    @lru_cache(maxsize=128)
    def get_citation_count(self, pmid):
        """
        Get the citation count for a PubMed article.
        
        Args:
            pmid (str): The PubMed ID
            
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
            
        max_retries = 3
        delay = 0.5
        
        for attempt in range(max_retries):
            try:
                response = requests.get(elink_url, params=params)
                response.raise_for_status()
                xml = ET.fromstring(response.content)
                count = len(xml.findall(".//LinkSetDb/Link/Id"))
                return count
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:
                    logger.warning(f"429 Error for PMID {pmid}. Waiting {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"HTTP error when retrieving citation count for PMID {pmid}: {e}")
                    return "Error"
            except ET.ParseError as e:
                logger.error(f"Parse error for PMID {pmid}: {e}")
                return "XML Error"
            except Exception as e:
                logger.error(f"Unexpected error for PMID {pmid}: {e}")
                return "Error"
                
        logger.warning(f"Maximum retries exceeded for PMID {pmid}")
        return "Timeout"

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
