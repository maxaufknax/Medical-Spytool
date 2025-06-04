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
    requires_api_key = True # Web of Science API requires an API key
    
    def __init__(self, api_key=None, settings=None):
        """Initialize the Web of Science connector.
        
        Args:
            api_key (str, optional): The API key for WoS.
            settings (dict, optional): Additional settings.
        """
        super().__init__(api_key, settings)
        self.base_url = "https://wos-api.clarivate.com/api/woslite" # For WOS Lite API
        # For full WOS API, might be: "https://wos-api.clarivate.com/api/wos"
        self.citation_url = "https://wos-api.clarivate.com/api/woslite/references" # This seems specific, might not be needed for general search
        self.name = "WoS" # Added for api_key_manager
        self.max_results = 100 # Default, can be overridden
        
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

    def construct_query(self, search_term: str, **kwargs) -> str:
        """
        Construct a Web of Science query string.
        Compatible with BaseConnector.

        Args:
            search_term (str): The main search term.
            **kwargs: Additional search parameters including:
                - additional_terms (str): Additional search terms.
                - date_range (dict): Date range with 'start' and 'end' keys (YYYY-MM-DD strings or datetime objects).
                - language (str): Language filter.
                - pub_type (str): Publication type filter.
                - field (str): Specific field to search in.
                - person_names (list): List of person names to include in search.
        Returns:
            str: The constructed WoS query string.
        """
        query_parts = []

        # Field mapping
        field_map = {
            "author": "AU", "autor": "AU",
            "title": "TI", "titel": "TI",
            "abstract": "AB",
            "keywords": "KP", "keyword": "KP", # KP for Author Keywords, IK for Keywords Plus
            "address": "AD", "adresse": "AD", "affiliation": "AD",
            "doi": "DO",
            "issn": "IS",
            "journal": "SO", "source": "SO",
            "conference": "CF", "konferenz": "CF",
            "all fields": "TS", "alle felder": "TS"
        }

        # Main search term and field
        field_arg = kwargs.get('field', kwargs.get('search_field', 'all fields')).lower()
        wos_field_code = field_map.get(field_arg, "TS") # Default to Topic Search (TS)

        if search_term:
            query_parts.append(f"{wos_field_code}=({search_term})")

        # Person names (Authors)
        person_names = kwargs.get('person_names', [])
        if person_names and isinstance(person_names, list):
            author_queries = []
            for person in person_names:
                if isinstance(person, str) and person.strip():
                    # WoS author format is typically Lastname F* or Lastname Firstname I*
                    # Simple approach: use the name as is, assuming users format it correctly or WoS is flexible.
                    author_queries.append(f"AU=({person.strip()})")
            if author_queries:
                # If there was already a search term, AND these authors. Otherwise, OR them.
                conjunction = "AND" if search_term else "OR"
                query_parts.append(f"{conjunction} ({' OR '.join(author_queries)})")


        # Additional terms (treat as general topic search, ANDed)
        additional_terms = kwargs.get('additional_terms')
        if additional_terms:
            query_parts.append(f"AND TS=({additional_terms})")

        # Date range
        date_range = kwargs.get('date_range')
        # Also check for direct start_date/end_date from form which might not be in a dict
        start_date_str = kwargs.get('start_date', date_range.get('start') if date_range else None)
        end_date_str = kwargs.get('end_date', date_range.get('end') if date_range else None)

        if start_date_str and end_date_str:
            try:
                # Assuming YYYY or YYYY-MM-DD format
                start_year = str(start_date_str)[:4]
                end_year = str(end_date_str)[:4]
                if start_year.isdigit() and end_year.isdigit():
                     query_parts.append(f"AND PY=({start_year}-{end_year})")
                else:
                    logger.warning(f"Invalid date format for WoS query: {start_date_str}, {end_date_str}")
            except Exception as e:
                logger.warning(f"Error processing date range for WoS: {e}")


        # Language filter
        language = kwargs.get('language')
        if language:
            # WoS uses full language names e.g., "English", "German"
            query_parts.append(f"AND LA=({language})")

        # Publication type filter
        pub_type = kwargs.get('pub_type')
        if pub_type:
            # WoS uses specific document type codes, e.g., "Article", "Review"
            # Assuming pub_type is passed directly as WoS expects
            query_parts.append(f"AND DT=({pub_type})")

        # Join all parts to form the final query
        # WoS uses "AND", "OR", "NOT" as operators. Default to AND if multiple parts.
        final_query = " AND ".join(filter(None, query_parts))
        
        if not final_query: # Handle empty query case
            return "TS=(*) AND PY=(2000-2024)" # Example: search everything in a recent range. Or raise error.

        logger.debug(f"Constructed WoS Query: {final_query}")
        return final_query

    def search(self, search_term: str = None, query: str = None, params: Dict[str, Any] = None,
               person_names: List[str] = None, max_results: int = None, **kwargs) -> List[Dict[str, Any]]:
        """Search the Web of Science database.
        Compatible with BaseConnector.
        
        Args:
            search_term (str, optional): The main search term
            query (str, optional): A pre-constructed query string (alternative to search_term)
            params (dict, optional): Additional search parameters (largely superseded by kwargs for this connector)
            person_names (list, optional): List of person names to include in the search
            max_results (int, optional): Maximum number of results to return
            **kwargs: Any additional parameters for the search
            
        Returns:
            List[Dict[str, Any]]: The search results.
        """
        if not self.api_key:
            logger.warning("No API key for Web of Science. Using dummy search.")
            # Construct a query for dummy search to have some context
            dummy_query_context = query
            if not dummy_query_context:
                 dummy_query_context = self.construct_query(search_term, person_names=person_names, **kwargs)
            # Use effective_max_results for dummy search as well
            effective_max_results = max_results if max_results is not None else self.max_results
            return self._dummy_search(dummy_query_context, effective_max_results, person_names)

        # Determine the query to use
        if not query:
            current_query = self.construct_query(search_term, person_names=person_names, **kwargs)
        else:
            current_query = query

        if not current_query or (current_query.strip() == "TS=(*)" and not person_names): # Avoid empty or too broad queries if not intended
             logger.warning(f"WoS query '{current_query}' is empty or too broad without specific person names. Aborting search.")
             return []

        logger.info(f"Web of Science search query: {current_query}")

        headers = {
            "X-APIKey": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        effective_max_results = max_results if max_results is not None else self.max_results
        
        all_results = []
        total_fetched = 0
        current_record = 1
        API_PAGE_LIMIT = 100

        try:
            while total_fetched < effective_max_results:
                count_this_request = min(API_PAGE_LIMIT, effective_max_results - total_fetched)
                if count_this_request <= 0:
                    break

                payload = {
                    "databaseId": "WOS",
                    "usrQuery": current_query,
                    "count": count_this_request,
                    "firstRecord": current_record
                }
                
                logger.debug(f"WoS API Request Payload: {payload}")
                response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 401: # Unauthorized
                    logger.error(f"WoS API Key is invalid or expired: {response.text}")
                    raise Exception("Web of Science API Key invalid or expired.")
                if response.status_code == 403: # Forbidden
                    logger.error(f"WoS API Key does not have access or exceeded quota: {response.text}")
                    raise Exception(f"Forbidden: WoS API Key lacks permission or quota exceeded. Details: {response.text}")
                if response.status_code != 200:
                    logger.error(f"Error in WoS API request: {response.status_code} - {response.text}")
                    try:
                        error_data = response.json()
                        error_message = error_data.get("message", response.text)
                        raise Exception(f"WoS API error ({response.status_code}): {error_message}")
                    except ValueError:
                        raise Exception(f"WoS API error ({response.status_code}): {response.text}")

                data = response.json()
                logger.debug(f"WoS API Response Data (first 500 chars): {str(data)[:500]}")

                records_data = data.get("Data", {}).get("Records", {})
                if not records_data or not records_data.get("records"):
                    logger.info("No 'Records' field in WoS response or it's empty.")
                    break

                actual_records = records_data.get("records", {}).get("REC", [])
                if not isinstance(actual_records, list): # If "REC" is a single dict
                    actual_records = [actual_records]

                if not actual_records:
                    logger.info("No actual records list found in this WoS page or REC is empty.")
                    break

                search_context_name = person_names[0] if person_names and person_names[0] else "General Search"
                parsed_page_results = self.parse_results(actual_records, search_context_name)
                all_results.extend(parsed_page_results)

                total_fetched += len(parsed_page_results)
                current_record += len(parsed_page_results) # WoS uses 1-based indexing for firstRecord

                query_result_info = data.get("QueryResult", {})
                records_found_total = query_result_info.get("RecordsFound", 0)

                logger.info(f"Fetched {len(parsed_page_results)} WoS records in this page. Total fetched so far: {total_fetched}/{records_found_total}")

                if total_fetched >= records_found_total or total_fetched >= effective_max_results:
                    break

            logger.info(f"Total {len(all_results)} WoS results found for query.")
            return self.format_results(all_results)
            
        except requests.RequestException as e:
            logger.error(f"WoS API request error: {e}", exc_info=True)
            raise Exception(f"WoS API request error: {str(e)}")
        except Exception as e:
            logger.error(f"Web of Science search error: {e}", exc_info=True)
            raise Exception(f"WoS search error: {str(e)}")

    def _dummy_search(self, query_context: str, max_results: int, person_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Generate dummy results for testing.
        
        Args:
            query_context (str): The query string context for dummy results.
            max_results (int): Number of dummy results to generate.
            person_names (Optional[List[str]]): Person names for context.
            
        Returns:
            List[Dict[str, Any]]: The dummy search results.
        """
        logger.info(f"Generating {max_results} dummy results for WoS. Query context: {query_context}")
        
        dummy_results = []
        context_name = person_names[0] if person_names and person_names[0] else "General Search"
        
        for i in range(1, int(max_results) + 1): # Ensure max_results is int
            year = 2024 - (i % 5)
            month_num = (i % 12) + 1
            month = f"{month_num:02d}"
            result = {
                'Title': f"Dummy WoS Publication {i}: {query_context}",
                'Authors': f"Doe, John; Smith, Jane; {context_name if context_name != 'General Search' else 'Tester, Adam'}",
                'Journal': f"Journal of Dummy Studies {i % 10}",
                'Publication Year': str(year),
                'Publication Month': month,
                'Abstract': f"This is a dummy abstract for result {i} related to '{query_context}'. It demonstrates the structure of a WoS search result.",
                'DOI': f"10.0000/dummy.wos.{year}.{i}",
                'URL': f"https://www.webofknowledge.com/dummy/wos/{i}",
                'Database': 'Web of Science',
                'Publication Type': "Article" if i % 2 == 0 else "Review",
                'Language': "English",
                'Keywords': "dummy; testing; wos; example",
                'Citation Count': str(i * 3),
                'Identifier': f"WOS:000FAKEID{i:09d}",
                'Affiliations': "Dummy University, Test Department, City, Country",
                'Name': context_name
            }
            dummy_results.append(result)
            
        logger.info(f"Generated {len(dummy_results)} dummy WoS results.")
        return self.format_results(dummy_results)

    def parse_results(self, records: List[Dict[str, Any]], search_context_name: str) -> List[Dict[str, Any]]:
        """Parse the results from Web of Science API.
        
        Args:
            records (List[Dict[str, Any]]): The records from the Web of Science API (list of REC dicts).
            search_context_name (str): The context of the search (e.g., person name or "General Search").
            
        Returns:
            List[Dict[str, Any]]: The parsed results.
        """
        parsed_results = []
        
        for record_item in records:
            # The WoS Lite API seems to wrap each record in a list under REC key like: {"REC": [actual_record_content]}
            # Or if it's a single record, it might be {"REC": actual_record_content}
            # The new search logic passes the list of actual records directly if possible.
            # This function should expect a list of actual record dicts.
            record = record_item # Assuming 'records' is already the list of actual record dicts.
            if not isinstance(record, dict): # Basic check
                logger.warning(f"Skipping non-dictionary record item: {record}")
                continue

            try:
                item_title_info = record.get("static_data", {}).get("summary", {}).get("titles", {}).get("title", [])
                item_title = ""
                if isinstance(item_title_info, list):
                     for s_item in item_title_info:
                        if s_item.get("type") == "item": # Main title of the article/publication
                            item_title = s_item.get("content", "")
                            break
                if not item_title and isinstance(item_title_info, list) and item_title_info:
                    item_title = item_title_info[0].get("content", "N/A") # Fallback to first title

                source_data = record.get("static_data", {}).get("summary", {}).get("titles", {}).get("title", [])
                journal_title = ""
                if isinstance(source_data, list):
                    for s_item in source_data:
                        if s_item.get("type") == "source": # Journal title
                            journal_title = s_item.get("content", "")
                            break
                
                authors_data = record.get("static_data", {}).get("summary", {}).get("names", {}).get("name", [])
                authors_list = []
                if isinstance(authors_data, list):
                    for author in authors_data:
                        # Consider only authors, not other roles like 'BookEditor'
                        if author.get("role") == "author":
                             authors_list.append(author.get("full_name", ""))
                authors_str = "; ".join(filter(None, authors_list)) or "N/A"
                
                pub_info = record.get("static_data", {}).get("summary", {}).get("pub_info", {})
                pub_year = str(pub_info.get("pubyear", "N/A"))
                pub_month_str = pub_info.get("pubmonth", "")
                if pub_month_str and not pub_month_str.isdigit():
                    try:
                        month_dt = datetime.strptime(pub_month_str, "%b") # e.g. "Jan"
                        pub_month = f"{month_dt.month:02d}"
                    except ValueError:
                        pub_month = "N/A"
                elif pub_month_str.isdigit():
                    pub_month = f"{int(pub_month_str):02d}"
                else:
                    pub_month = "N/A"

                doc_types_list = record.get("static_data", {}).get("summary", {}).get("doctypes", {}).get("doctype", [])
                if not isinstance(doc_types_list, list):
                    doc_types_list = [doc_types_list] if doc_types_list else []
                pub_types_str = "; ".join(filter(None, doc_types_list)) or "N/A"

                wos_id = record.get("UID", "N/A")
                doi = ""
                other_ids = record.get("dynamic_data", {}).get("cluster_related", {}).get("identifiers", {}).get("identifier", [])
                if isinstance(other_ids, list):
                    for item_id_obj in other_ids: # Iterate through list of id objects
                        if isinstance(item_id_obj, dict) and item_id_obj.get("type") == "doi":
                            doi = item_id_obj.get("value", "")
                            break
                
                citation_count_val = record.get("dynamic_data", {}).get("citation_related", {}).get("tc_list", {}).get("silo_tc", {}).get("content")
                citation_count = str(citation_count_val) if citation_count_val is not None else "0"


                keywords_list = []
                keywords_data = record.get("static_data", {}).get("item", {}).get("keywords_plus", {}).get("keyword", [])
                if isinstance(keywords_data, list):
                    keywords_list.extend(filter(None, keywords_data))
                elif isinstance(keywords_data, str): # If it's a single string
                     keywords_list.append(keywords_data)
                keywords_str = "; ".join(keywords_list) or "N/A"

                abstract_text = "N/A" # WoS Lite often doesn't provide full abstract easily
                abstracts_section = record.get("static_data", {}).get("fullrecord_metadata", {}).get("abstracts", {}).get("abstract", [])
                if abstracts_section: # It's a list of abstract sections
                    if isinstance(abstracts_section, list) and abstracts_section[0].get("abstract_text_count", 0) > 0:
                        # Assuming the first paragraph of the first abstract section
                        first_abstract_paragraphs = abstracts_section[0].get("p", [])
                        if first_abstract_paragraphs:
                            abstract_text = first_abstract_paragraphs[0]

                url = f"https://www.webofscience.com/wos/woscc/full-record/{wos_id}" if wos_id != "N/A" else ""

                language = "N/A"
                language_section = record.get("static_data", {}).get("fullrecord_metadata", {}).get("languages", {}).get("language", [])
                if language_section: # It's a list
                    if isinstance(language_section, list) and language_section[0].get("type") == "primary_language":
                        language = language_section[0].get("content", "N/A")

                result = {
                    'Title': item_title,
                    'Authors': authors_str,
                    'Journal': journal_title,
                    'Publication Year': pub_year,
                    'Publication Month': pub_month,
                    'Abstract': abstract_text,
                    'DOI': doi,
                    'URL': url,
                    'Database': 'Web of Science',
                    'Publication Type': pub_types_str,
                    'Language': language,
                    'Keywords': keywords_str,
                    'Citation Count': citation_count,
                    'Identifier': wos_id,
                    'Name': search_context_name
                }
                parsed_results.append(result)
                
            except Exception as e:
                logger.error(f"Error parsing WoS entry (UID: {record.get('UID', 'UNKNOWN')}): {e}", exc_info=True)
                continue
                
        return parsed_results

    def validate_api_key(self, api_key: str = None) -> bool:
        """
        Validate the Web of Science API key by making a test request.
        Args:
            api_key (str, optional): The API key to validate. If None, use the one from the instance.
        Returns:
            bool: True if the API key is valid, False otherwise.
        """
        key_to_validate = api_key if api_key else self.api_key
        if not key_to_validate:
            logger.warning("No WoS API key provided for validation.")
            return False

        headers = {"X-APIKey": key_to_validate, "Accept": "application/json"}
        # A simple query that should return quickly
        payload = {"databaseId": "WOS", "usrQuery": "TI=(test)", "count": 1, "firstRecord": 1}
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("WoS API key validation successful.")
                return True
            elif response.status_code == 401: # Unauthorized
                logger.warning(f"WoS API key validation failed (Unauthorized): {response.text}")
                return False
            else: # Other errors
                logger.warning(f"WoS API key validation returned status {response.status_code}: {response.text}")
                return False
        except requests.RequestException as e:
            logger.error(f"WoS API key validation request failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during WoS API key validation: {e}")
            return False

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the Web of Science API.
        Returns:
            dict: A dictionary containing the test results.
        """
        import time
        start_time = time.time()

        if not self.api_key:
            return {
                'status': 'Error',
                'message': 'No Web of Science API key configured.',
                'response_time': None
            }

        headers = {"X-APIKey": self.api_key, "Accept": "application/json"}
        payload = {"databaseId": "WOS", "usrQuery": "TS=(cardiology)", "count": 1, "firstRecord": 1} # Test with a common term

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=20)
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                records_found = data.get("QueryResult", {}).get("RecordsFound", 0)
                return {
                    'status': 'OK',
                    'message': f'Successfully connected to WoS. Found {records_found} results for "cardiology".',
                    'response_time': round(response_time, 2)
                }
            elif response.status_code == 401:
                return {
                    'status': 'Error',
                    'message': 'WoS API Key is invalid or expired.',
                    'response_time': round(response_time, 2)
                }
            else:
                return {
                    'status': 'Error',
                    'message': f'Error connecting to WoS: {response.status_code} - {response.text}',
                    'response_time': round(response_time, 2)
                }
        except requests.exceptions.Timeout:
            return {
                'status': 'Error',
                'message': 'Connection to WoS timed out.',
                'response_time': None
            }
        except requests.exceptions.RequestException as e:
            return {
                'status': 'Error',
                'message': f'Network error connecting to WoS: {str(e)}',
                'response_time': None
            }
        except Exception as e:
            logger.error(f"WoS connection test unexpected error: {e}", exc_info=True)
            return {
                'status': 'Error',
                'message': f'Unexpected error testing WoS connection: {str(e)}',
                'response_time': None
            }

    # get_citation_count seems to be for individual lookups, not used in main search flow
    # It might be useful for a different feature (e.g., updating citation for a specific record)
    # For now, I will leave it as is but ensure it's not called during the main search.
    def get_citation_count(self, wos_id: str) -> int:
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