"""
PubMed Database Connector

This module provides functionality to search and retrieve publications from PubMed.
"""

import time
import requests
import xml.etree.ElementTree as ET
import logging
from functools import lru_cache
from datetime import datetime

from database_connectors.base_connector import DatabaseConnector

logger = logging.getLogger(__name__)

class PubMedConnector(DatabaseConnector):
    """
    Connector for PubMed database.
    """
    
    def __init__(self, api_key=None, settings=None):
        """
        Initialize the PubMed connector.
        
        Args:
            api_key (str, optional): API key for PubMed.
            settings (dict, optional): Additional settings.
        """
        super().__init__(api_key, settings)
        self.name = "PubMed"
        self.max_results_per_page = 10000  # Erhöhen auf maximal 10.000 Ergebnisse
        self.search_fields = ["Alle Felder", "Autor", "Titel", "Journal", "MESH-Terme"]
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    @lru_cache(maxsize=128)
    def get_citation_count(self, pmid):
        """
        Get the citation count for a PubMed publication.
        
        Args:
            pmid (str): PubMed ID.
            
        Returns:
            int or str: Citation count or error message.
        """
        if not pmid or pmid == "N/A" or pmid == "Keine PMID":
            return "N/A"
            
        elink_url = self.base_url + "elink.fcgi"
        params = {
            "dbfrom": "pubmed",
            "linkname": "pubmed_pubmed_citedin",
            "id": pmid,
            "retmode": "xml",
            "api_key": self.api_key
        }
        
        max_retries = 3
        delay = 0.5
        
        for attempt in range(max_retries):
            try:
                response = requests.get(elink_url, params=params)
                response.raise_for_status()
                xml_data = ET.fromstring(response.content)
                count = len(xml_data.findall(".//LinkSetDb/Link/Id"))
                return count
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:  # Too Many Requests
                    logger.warning(f"429 Error for PMID {pmid}. Waiting {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"Error fetching citation count for PMID {pmid}: {e}")
                    return "Error"
            except ET.ParseError as e:
                logger.error(f"XML Parse error for PMID {pmid}: {e}")
                return "XML Error"
            except Exception as e:
                logger.error(f"Unexpected error for PMID {pmid}: {e}")
                return "Error"
                
        logger.error(f"Maximum retries exceeded for PMID {pmid}")
        return "Error: Too Many Requests"
    
    def construct_query(self, base_query, additional_terms="", date_range=None, 
                      language=None, pub_type=None, field=None):
        """
        Construct a PubMed search query.
        
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
        query = base_query

        if field and field != "Alle Felder":
            field_map = {
                "Autor": "[Author]",
                "Titel": "[Title]",
                "Journal": "[Journal]",
                "MESH-Terme": "[MeSH Terms]"
            }
            query = f"{query}{field_map.get(field, '')}"

        if additional_terms:
            query = f"({query}) AND ({additional_terms})"
            
        if date_range and date_range.get('start') and date_range.get('end'):
            start_date = date_range['start'].strftime("%Y/%m/%d")
            end_date = date_range['end'].strftime("%Y/%m/%d")
            query = f"{query} AND {start_date}:{end_date}[Date - Publication]"
            
        if language:
            query = f"{query} AND {language}[Language]"
            
        if pub_type:
            query = f"{query} AND {pub_type}[Publication Type]"
            
        return query
    
    def search(self, query, params=None, log_widget=None):
        """
        Search PubMed with the given query.
        
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
        
        log_message(log_widget, f"Starting PubMed search: {query}")
        
        esearch_url = self.base_url + "esearch.fcgi"
        efetch_url = self.base_url + "efetch.fcgi"
        
        esearch_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "xml",
            "api_key": self.api_key
        }
        
        try:
            response = requests.get(esearch_url, params=esearch_params)
            response.raise_for_status()
            esearch_xml = ET.fromstring(response.content)
            id_list = [node.text for node in esearch_xml.findall(".//Id")]
            
            count_node = esearch_xml.find(".//Count")
            total_count = int(count_node.text) if count_node is not None else 0
            
            log_message(log_widget, f"PubMed search: {total_count} results found")
            
            if not id_list:
                log_message(log_widget, f"No publications found for '{query}'")
                return []
        except requests.exceptions.RequestException as e:
            log_message(log_widget, f"Error in PubMed search for '{query}': {e}")
            return []
        
        efetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml",
            "api_key": self.api_key
        }
        
        try:
            log_message(log_widget, f"Retrieving PubMed details for {len(id_list)} articles...")
            response = requests.get(efetch_url, params=efetch_params)
            response.raise_for_status()
            efetch_xml = ET.fromstring(response.content)
        except requests.exceptions.RequestException as e:
            log_message(log_widget, f"Error retrieving PubMed details: {e}")
            return []
        
        return self.parse_results(efetch_xml, params={'name': name, 'log_widget': log_widget})
    
    def parse_results(self, efetch_xml, params=None):
        """
        Parse PubMed search results.
        
        Args:
            efetch_xml (xml.etree.ElementTree.Element): XML response from PubMed.
            params (dict, optional): Additional parameters.
            
        Returns:
            list: Parsed publications.
        """
        from utils.logging_manager import log_message
        
        params = params or {}
        name = params.get('name', 'Unknown')
        log_widget = params.get('log_widget', None)
        
        publications = []
        articles = efetch_xml.findall(".//PubmedArticle")
        total = len(articles)
        
        log_message(log_widget, f"Processing {total} PubMed articles...")
        
        for i, article in enumerate(articles):
            if i % 10 == 0:  # Status update every 10 articles
                log_message(log_widget, f"Processing PubMed article {i+1}/{total}...")
                
            try:
                # Extract title
                title_el = article.find(".//ArticleTitle")
                title = title_el.text if title_el is not None else "No Title"
                
                # Extract publication date
                pub_date_el = article.find(".//PubDate")
                year = pub_date_el.find("Year").text if pub_date_el is not None and pub_date_el.find("Year") is not None else "N/A"
                
                month_el = pub_date_el.find("Month") if pub_date_el is not None else None
                month_raw = month_el.text if month_el is not None else ""
                try:
                    month_numeric = datetime.strptime(month_raw, "%b").strftime("%m") if month_raw else ""
                except:
                    try:
                        month_numeric = datetime.strptime(month_raw, "%B").strftime("%m") if month_raw else ""
                    except:
                        try:
                            month_numeric = str(int(month_raw)).zfill(2) if month_raw.isdigit() else month_raw
                        except:
                            month_numeric = month_raw
                
                # Extract authors
                authors = []
                for author in article.findall(".//Author"):
                    ln = author.find(".//LastName")
                    fn = author.find(".//ForeName")
                    if ln is not None and fn is not None:
                        authors.append(f"{fn.text} {ln.text}")
                    elif ln is not None:
                        authors.append(ln.text)
                    else:
                        continue
                authors_str = ", ".join(authors) if authors else "No Authors"
                
                # Extract publication types
                pub_types = [pt.text for pt in article.findall(".//PublicationTypeList/PublicationType") if pt.text]
                pub_types_str = ", ".join(pub_types) if pub_types else "No Publication Types"
                
                # Extract identifiers
                pmid_el = article.find(".//PMID")
                pmid = pmid_el.text if pmid_el is not None else "No PMID"
                
                pmcid_el = article.find('.//ArticleId[@IdType="pmc"]')
                pmcid = pmcid_el.text if pmcid_el is not None else "No PMCID"
                
                doi_el = article.find('.//ArticleId[@IdType="doi"]')
                doi = doi_el.text if doi_el is not None else "No DOI"
                
                # Create URLs
                doi_url = f"https://doi.org/{doi}" if doi != "No DOI" else "No DOI URL"
                pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid != "No PMID" else "No PubMed URL"
                
                # Extract affiliations
                affils = [aff.text for aff in article.findall(".//AffiliationInfo/Affiliation") if aff.text]
                affils_str = "\n".join(affils) if affils else "No Affiliation Data"
                
                # Get citation count
                citation_count = self.get_citation_count(pmid) if pmid != "No PMID" else "N/A"
                
                # Create publication record
                publication = {
                    "Database": "PubMed",
                    "Name": name,
                    "Title": title,
                    "Publication Year": year,
                    "Publication Month": month_numeric,
                    "Authors": authors_str,
                    "Publication Types": pub_types_str,
                    "Affiliations": affils_str,
                    "PubMed URL": pubmed_url,
                    "DOI URL": doi_url,
                    "PubMed ID": pmid,
                    "PMCID": pmcid,
                    "DOI": doi,
                    "Citation Count": citation_count,
                    "Identifier": pmid,  # Use PMID as the primary identifier
                    "URL": pubmed_url    # Use PubMed URL as the primary URL
                }
                
                publications.append(publication)
            except Exception as e:
                logger.error(f"Error parsing PubMed article: {e}", exc_info=True)
                log_message(log_widget, f"Error parsing PubMed article: {e}")
        
        log_message(log_widget, f"Completed processing {len(publications)} PubMed articles")
        return publications