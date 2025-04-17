"""
API clients for scientific databases

This module contains client classes for different scientific database APIs
including PubMed, Web of Science, Scopus, and Deutsche Nationalbibliothek.
"""
import json
import logging
import requests
from urllib.parse import urlencode
from models import ApiKey, AppLog

logger = logging.getLogger(__name__)

class BaseApiClient:
    """Base class for all API clients"""
    
    def __init__(self, database_name, user_id=None):
        self.database_name = database_name
        self.user_id = user_id
        self.api_key = self._get_api_key()
    
    def _get_api_key(self):
        """Get API key from database for the current user"""
        api_key_obj = ApiKey.get_by_database(self.database_name, user_id=self.user_id)
        return api_key_obj.api_key if api_key_obj else None
    
    def _log_api_call(self, endpoint, params, success, error=None):
        """Log API call to database"""
        message = f"API call to {self.database_name} endpoint: {endpoint}"
        if params:
            message += f" with params: {json.dumps(params)}"
        if not success:
            message += f" failed: {error}"
        
        level = "INFO" if success else "ERROR"
        AppLog.add(level, message)
    
    def is_configured(self):
        """Check if the API client is properly configured"""
        return bool(self.api_key)
    
    def search(self, query, **params):
        """
        Base search method to be implemented by subclasses
        
        Args:
            query (str): Main search query
            **params: Additional search parameters
            
        Returns:
            dict: Standardized search results
        """
        raise NotImplementedError("Subclasses must implement search method")


class PubMedClient(BaseApiClient):
    """Client for PubMed API (E-utilities)"""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    def __init__(self, user_id=None):
        super().__init__("pubmed", user_id=user_id)
    
    def search(self, query, date_from=None, date_to=None, publication_type=None, language=None, max_results=100):
        """
        Search PubMed using E-utilities
        
        Args:
            query (str): Search query
            date_from (str): Start date in format YYYY/MM/DD
            date_to (str): End date in format YYYY/MM/DD
            publication_type (str): Type of publication
            language (str): Language code
            max_results (int): Maximum number of results to return
            
        Returns:
            dict: Standardized search results
        """
        if not self.is_configured():
            return {"success": False, "error": "PubMed API key not configured", "results": []}
        
        # Build the search query with filters
        search_query = query
        
        if date_from and date_to:
            search_query += f" AND {date_from}:{date_to}[PDAT]"
        elif date_from:
            search_query += f" AND {date_from}:[PDAT]"
        elif date_to:
            search_query += f" AND :{date_to}[PDAT]"
            
        if publication_type:
            search_query += f" AND {publication_type}[PT]"
            
        if language:
            search_query += f" AND {language}[LA]"
        
        # Search for IDs first
        search_params = {
            "db": "pubmed",
            "term": search_query,
            "retmax": max_results,
            "retmode": "json",
            "api_key": self.api_key
        }
        
        search_url = f"{self.BASE_URL}esearch.fcgi"
        
        try:
            response = requests.get(search_url, params=search_params)
            response.raise_for_status()
            search_data = response.json()
            
            if "esearchresult" not in search_data or "idlist" not in search_data["esearchresult"]:
                self._log_api_call("esearch.fcgi", search_params, False, "Invalid response format")
                return {"success": False, "error": "Invalid API response format", "results": []}
            
            id_list = search_data["esearchresult"]["idlist"]
            
            if not id_list:
                self._log_api_call("esearch.fcgi", search_params, True)
                return {"success": True, "results": [], "source": "PubMed"}
            
            # Fetch details for the IDs
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "json",
                "api_key": self.api_key
            }
            
            fetch_url = f"{self.BASE_URL}efetch.fcgi"
            fetch_response = requests.get(fetch_url, params=fetch_params)
            fetch_response.raise_for_status()
            fetch_data = fetch_response.json()
            
            self._log_api_call("efetch.fcgi", fetch_params, True)
            
            # Process results into a standardized format
            results = []
            if "PubmedArticle" in fetch_data.get("PubmedArticleSet", {}):
                articles = fetch_data["PubmedArticleSet"]["PubmedArticle"]
                if not isinstance(articles, list):
                    articles = [articles]
                
                for article in articles:
                    article_data = article.get("MedlineCitation", {}).get("Article", {})
                    pmid = article.get("MedlineCitation", {}).get("PMID", {}).get("#text", "")
                    
                    # Extract authors
                    authors = []
                    author_list = article_data.get("AuthorList", {}).get("Author", [])
                    if not isinstance(author_list, list):
                        author_list = [author_list]
                    
                    for author in author_list:
                        if isinstance(author, dict):
                            lastname = author.get("LastName", "")
                            forename = author.get("ForeName", "")
                            initials = author.get("Initials", "")
                            
                            if lastname and (forename or initials):
                                authors.append(f"{lastname} {forename or initials}")
                            elif lastname:
                                authors.append(lastname)
                    
                    # Extract journal information
                    journal_info = article_data.get("Journal", {})
                    journal = journal_info.get("Title", "")
                    
                    # Extract publication date
                    pub_date = {}
                    journal_issue = journal_info.get("JournalIssue", {})
                    
                    if "PubDate" in journal_issue:
                        pub_date = journal_issue["PubDate"]
                    
                    year = pub_date.get("Year", "")
                    
                    # Extract article title
                    title = article_data.get("ArticleTitle", "")
                    
                    # Create standardized result
                    result = {
                        "id": pmid,
                        "title": title,
                        "authors": authors,
                        "journal": journal,
                        "year": year,
                        "source": "PubMed",
                        "doi": self._extract_doi(article),
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    }
                    
                    results.append(result)
            
            return {"success": True, "results": results, "source": "PubMed"}
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            self._log_api_call("PubMed search", search_params, False, error_msg)
            return {"success": False, "error": error_msg, "results": []}
    
    def _extract_doi(self, article):
        """Extract DOI from article data"""
        if "PubmedData" in article and "ArticleIdList" in article["PubmedData"]:
            article_ids = article["PubmedData"]["ArticleIdList"]["ArticleId"]
            if not isinstance(article_ids, list):
                article_ids = [article_ids]
            
            for article_id in article_ids:
                if article_id.get("@IdType") == "doi":
                    return article_id.get("#text", "")
        
        return ""


class ScopusClient(BaseApiClient):
    """Client for Elsevier Scopus API"""
    
    BASE_URL = "https://api.elsevier.com/content/search/scopus"
    
    def __init__(self, user_id=None):
        super().__init__("scopus", user_id=user_id)
    
    def search(self, query, date_from=None, date_to=None, publication_type=None, language=None, max_results=100):
        """
        Search Scopus
        
        Args:
            query (str): Search query
            date_from (str): Start date in format YYYY
            date_to (str): End date in format YYYY
            publication_type (str): Type of publication
            language (str): Language code
            max_results (int): Maximum number of results to return
            
        Returns:
            dict: Standardized search results
        """
        if not self.is_configured():
            return {"success": False, "error": "Scopus API key not configured", "results": []}
        
        # Build the search query with filters
        search_query = query
        
        if date_from and date_to:
            search_query += f" AND PUBYEAR > {date_from} AND PUBYEAR < {date_to}"
        elif date_from:
            search_query += f" AND PUBYEAR > {date_from}"
        elif date_to:
            search_query += f" AND PUBYEAR < {date_to}"
            
        if publication_type:
            search_query += f" AND DOCTYPE({publication_type})"
            
        if language:
            search_query += f" AND LANGUAGE({language})"
        
        params = {
            "query": search_query,
            "count": min(max_results, 100),  # Scopus API typically limits to 100 per request
            "view": "COMPLETE"
        }
        
        headers = {
            "X-ELS-APIKey": self.api_key,
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(self.BASE_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            self._log_api_call("search", params, True)
            
            results = []
            if "search-results" in data and "entry" in data["search-results"]:
                entries = data["search-results"]["entry"]
                
                for entry in entries:
                    # Extract authors
                    authors = []
                    if "author" in entry:
                        for author in entry["author"]:
                            if "authname" in author:
                                authors.append(author["authname"])
                    
                    # Create standardized result
                    result = {
                        "id": entry.get("dc:identifier", "").replace("SCOPUS_ID:", ""),
                        "title": entry.get("dc:title", ""),
                        "authors": authors,
                        "journal": entry.get("prism:publicationName", ""),
                        "year": entry.get("prism:coverDate", "")[:4] if "prism:coverDate" in entry else "",
                        "source": "Scopus",
                        "doi": entry.get("prism:doi", ""),
                        "url": entry.get("link", [{}])[0].get("@href", "") if isinstance(entry.get("link", []), list) and entry.get("link", []) else ""
                    }
                    
                    results.append(result)
            
            return {"success": True, "results": results, "source": "Scopus"}
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            self._log_api_call("Scopus search", params, False, error_msg)
            return {"success": False, "error": error_msg, "results": []}


class WebOfScienceClient(BaseApiClient):
    """Client for Web of Science API"""
    
    BASE_URL = "https://wos-api.clarivate.com/api/v1/search"
    AUTH_URL = "https://wos-api.clarivate.com/api/v1/authenticate"
    
    def __init__(self, user_id=None):
        super().__init__("webofscience", user_id=user_id)
        self.session_token = None
    
    def _get_session_token(self):
        """Get a session token for the WoS API"""
        if not self.api_key:
            return None
            
        headers = {
            "X-ApiKey": self.api_key
        }
        
        try:
            response = requests.post(self.AUTH_URL, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            return data.get("access_token")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error authenticating with Web of Science API: {e}")
            return None
    
    def search(self, query, date_from=None, date_to=None, publication_type=None, language=None, max_results=100):
        """
        Search Web of Science
        
        Args:
            query (str): Search query
            date_from (str): Start date in format YYYY
            date_to (str): End date in format YYYY
            publication_type (str): Type of publication
            language (str): Language code
            max_results (int): Maximum number of results to return
            
        Returns:
            dict: Standardized search results
        """
        if not self.is_configured():
            return {"success": False, "error": "Web of Science API key not configured", "results": []}
        
        # Get session token if we don't have one
        if not self.session_token:
            self.session_token = self._get_session_token()
            
        if not self.session_token:
            return {"success": False, "error": "Failed to authenticate with Web of Science API", "results": []}
        
        # Build the search query with filters
        search_query = query
        
        if date_from and date_to:
            search_query += f" AND PY=({date_from}-{date_to})"
        elif date_from:
            search_query += f" AND PY>={date_from}"
        elif date_to:
            search_query += f" AND PY<={date_to}"
            
        if publication_type:
            search_query += f" AND DT=({publication_type})"
            
        if language:
            search_query += f" AND LA=({language})"
        
        params = {
            "db": "WOS",
            "q": search_query,
            "count": min(max_results, 100),  # WoS API typically limits to 100 per request
            "firstRecord": 1
        }
        
        headers = {
            "X-ApiKey": self.api_key,
            "Authorization": f"Bearer {self.session_token}",
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(self.BASE_URL, headers=headers, params=params)
            
            # If token expired, get a new one and retry
            if response.status_code == 401:
                self.session_token = self._get_session_token()
                if not self.session_token:
                    return {"success": False, "error": "Failed to authenticate with Web of Science API", "results": []}
                
                headers["Authorization"] = f"Bearer {self.session_token}"
                response = requests.get(self.BASE_URL, headers=headers, params=params)
            
            response.raise_for_status()
            data = response.json()
            
            self._log_api_call("search", params, True)
            
            results = []
            if "data" in data and "records" in data["data"]:
                records = data["data"]["records"]
                
                for record in records:
                    # Extract authors
                    authors = []
                    if "authors" in record:
                        for author in record["authors"]:
                            if "displayName" in author:
                                authors.append(author["displayName"])
                    
                    # Create standardized result
                    result = {
                        "id": record.get("uid", ""),
                        "title": record.get("title", {}).get("value", "") if isinstance(record.get("title", {}), dict) else "",
                        "authors": authors,
                        "journal": record.get("source", {}).get("sourceTitle", "") if isinstance(record.get("source", {}), dict) else "",
                        "year": record.get("source", {}).get("publishYear", "") if isinstance(record.get("source", {}), dict) else "",
                        "source": "Web of Science",
                        "doi": record.get("doi", ""),
                        "url": f"https://www.webofscience.com/wos/woscc/full-record/{record.get('uid', '')}" if record.get("uid", "") else ""
                    }
                    
                    results.append(result)
            
            return {"success": True, "results": results, "source": "Web of Science"}
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            self._log_api_call("Web of Science search", params, False, error_msg)
            return {"success": False, "error": error_msg, "results": []}


class DNBClient(BaseApiClient):
    """Client for Deutsche Nationalbibliothek (DNB) API"""
    
    BASE_URL = "https://services.dnb.de/sru/dnb"
    
    def __init__(self):
        super().__init__("dnb")
    
    def search(self, query, date_from=None, date_to=None, publication_type=None, language=None, max_results=100):
        """
        Search Deutsche Nationalbibliothek
        
        Args:
            query (str): Search query
            date_from (str): Start date in format YYYY
            date_to (str): End date in format YYYY
            publication_type (str): Type of publication
            language (str): Language code
            max_results (int): Maximum number of results to return
            
        Returns:
            dict: Standardized search results
        """
        if not self.is_configured():
            return {"success": False, "error": "DNB API key not configured", "results": []}
        
        # Build the search query with filters
        search_query = query
        
        if date_from and date_to:
            search_query += f" AND jhr >= {date_from} AND jhr <= {date_to}"
        elif date_from:
            search_query += f" AND jhr >= {date_from}"
        elif date_to:
            search_query += f" AND jhr <= {date_to}"
            
        if publication_type:
            search_query += f" AND mat = {publication_type}"
            
        if language:
            search_query += f" AND spr = {language}"
        
        params = {
            "operation": "searchRetrieve",
            "version": "1.1",
            "recordSchema": "MARC21-xml",
            "query": search_query,
            "maximumRecords": max_results,
            "accessToken": self.api_key
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            
            # DNB returns XML, using simple string parsing for now
            # In a real implementation, use proper XML parsing libraries
            data = response.text
            
            self._log_api_call("searchRetrieve", params, True)
            
            # Very basic parsing - in real implementation use proper XML parsing
            results = []
            record_sections = data.split("<record>")[1:]  # Split by record tag and skip the first element
            
            for i, record_section in enumerate(record_sections):
                if i >= max_results:
                    break
                    
                # Extract basic info from XML
                # These are simplified extractions - real implementation would need proper XML parsing
                try:
                    title = record_section.split("<datafield tag=\"245\">")[1].split("</datafield>")[0]
                    title = title.split("<subfield code=\"a\">")[1].split("</subfield>")[0] if "<subfield code=\"a\">" in title else ""
                except (IndexError, AttributeError):
                    title = ""
                
                try:
                    authors = []
                    author_sections = record_section.split("<datafield tag=\"100\">")
                    if len(author_sections) > 1:
                        author_section = author_sections[1].split("</datafield>")[0]
                        author = author_section.split("<subfield code=\"a\">")[1].split("</subfield>")[0] if "<subfield code=\"a\">" in author_section else ""
                        if author:
                            authors.append(author)
                except (IndexError, AttributeError):
                    authors = []
                
                try:
                    year = ""
                    pub_sections = record_section.split("<datafield tag=\"264\">")
                    if len(pub_sections) > 1:
                        pub_section = pub_sections[1].split("</datafield>")[0]
                        year = pub_section.split("<subfield code=\"c\">")[1].split("</subfield>")[0] if "<subfield code=\"c\">" in pub_section else ""
                        year = ''.join(c for c in year if c.isdigit())[:4]  # Extract up to 4 digits
                except (IndexError, AttributeError):
                    year = ""
                
                # Create a record ID for DNB
                record_id = f"DNB-{i+1}"
                
                result = {
                    "id": record_id,
                    "title": title,
                    "authors": authors,
                    "journal": "",  # DNB doesn't easily provide this in the basic response
                    "year": year,
                    "source": "Deutsche Nationalbibliothek",
                    "doi": "",  # DNB doesn't easily provide this in the basic response
                    "url": f"https://portal.dnb.de/opac.htm?query={urlencode({'query': title})}" if title else ""
                }
                
                results.append(result)
            
            return {"success": True, "results": results, "source": "Deutsche Nationalbibliothek"}
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            self._log_api_call("DNB search", params, False, error_msg)
            return {"success": False, "error": error_msg, "results": []}
