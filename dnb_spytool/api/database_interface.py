"""
Abstract base class for database clients.

This module defines the interface that all database clients must implement
to provide a consistent API for different publication databases.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class DatabaseInterface(ABC):
    """Abstract base class for database clients."""
    
    @abstractmethod
    def search_publications(self, query: str, max_results: int = 100, **kwargs) -> List[Dict]:
        """
        Search for publications in the database.
        
        Args:
            query: Search query (typically author name)
            max_results: Maximum number of results to return
            **kwargs: Additional database-specific parameters
            
        Returns:
            List of publication dictionaries with standardized fields
        """
        pass
    
    @abstractmethod
    def validate_query(self, query: str) -> Dict[str, any]:
        """
        Validate a search query.
        
        Args:
            query: Query string to validate
            
        Returns:
            Dict with 'is_valid' boolean and optional 'error' message
        """
        pass
    
    @abstractmethod
    def get_database_info(self) -> Dict[str, str]:
        """
        Get information about the database.
        
        Returns:
            Dict with database metadata (name, description, base_url, etc.)
        """
        pass
    
    @property
    @abstractmethod
    def database_name(self) -> str:
        """Return the name of the database."""
        pass
    
    @property
    @abstractmethod
    def max_results_per_request(self) -> int:
        """Return the maximum results per single request."""
        pass


class PublicationSchema:
    """Standard publication data schema for cross-database compatibility."""
    
    REQUIRED_FIELDS = [
        'title',
        'authors', 
        'publication_year',
        'database_source'
    ]
    
    OPTIONAL_FIELDS = [
        'id',           # Record ID
        'abstract',
        'description',  # Description/summary from MARC field 520
        'journal',
        'isbn',
        'issn',
        'doi',
        'pmid',
        'pmc',
        'url',
        'all_urls',
        'publisher',
        'language',
        'subject_headings',
        'publication_type',
        'physical_description',  # Physical description from MARC
        'series',       # Series information
        'notes',        # Additional notes
        
        # Enhanced v1.4 PubMed fields
        'affiliations',
        'institutions',
        'countries',
        'departments',
        'author_emails',
        'abstract_word_count',
        'journal_abbreviation',
        'journal_issn',
        'issn_print',
        'issn_electronic',
        'journal_volume',
        'journal_issue',
        'journal_pages',
        'journal_country',
        'nlm_unique_id',
        'article_ids',
        'publication_types',
        'is_research_article',
        'is_review',
        'is_case_report',
        'is_clinical_trial',
        'is_meta_analysis',
        'mesh_headings',
        'mesh_qualifiers',
        'major_topics',
        'mesh_categories',
        'keywords',
        'grants',
        'funding_agencies',
        'grant_numbers',
        'funding_countries',
        'has_funding',
        'funding',
        'pubmed_indexed',
        'medline_indexed',
        'pmc_available',
        'free_full_text',
        'citation_subset',
        'conflict_statement',
        'journal_category'
    ]
    
    @classmethod
    def validate_publication(cls, publication: Dict) -> Dict[str, any]:
        """
        Validate a publication dictionary against the standard schema.
        
        Args:
            publication: Publication dictionary to validate
            
        Returns:
            Dict with validation results
        """
        errors = []
        warnings = []
        
        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in publication or not publication[field]:
                errors.append(f"Missing required field: {field}")
        
        # Check data types and formats
        if 'publication_year' in publication:
            try:
                year = int(publication['publication_year'])
                if year < 1000 or year > 2030:
                    warnings.append(f"Unusual publication year: {year}")
            except (ValueError, TypeError):
                errors.append("publication_year must be a valid integer")
        
        if 'authors' in publication and not isinstance(publication['authors'], (str, list)):
            errors.append("authors must be a string or list")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @classmethod
    def normalize_publication(cls, publication: Dict) -> Dict:
        """
        Normalize a publication dictionary to the standard schema.
        
        Args:
            publication: Raw publication data
            
        Returns:
            Normalized publication dictionary
        """
        # Start with a copy of all original fields to preserve enhanced data
        normalized = publication.copy()
        
        # Ensure required fields exist with default values if missing
        for field in cls.REQUIRED_FIELDS:
            if field not in normalized or normalized[field] is None:
                if field == 'title':
                    normalized[field] = 'No title available'
                elif field == 'authors':
                    normalized[field] = 'No authors listed'
                elif field == 'publication_year':
                    normalized[field] = None
                elif field == 'database_source':
                    normalized[field] = 'unknown'
                else:
                    normalized[field] = None
        
        # Normalize specific fields
        # Normalize authors to string format
        if isinstance(normalized.get('authors'), list):
            normalized['authors'] = ', '.join(str(author) for author in normalized['authors'] if author)
        
        # Ensure database_source is set
        if not normalized.get('database_source'):
            normalized['database_source'] = 'unknown'
        
        # Convert publication_year to integer if possible
        if normalized.get('publication_year'):
            try:
                normalized['publication_year'] = int(normalized['publication_year'])
            except (ValueError, TypeError):
                normalized['publication_year'] = None
        
        # Normalize URL fields
        if normalized.get('all_urls') and isinstance(normalized['all_urls'], dict):
            # Keep all_urls as dict for URL extraction results
            pass
        elif normalized.get('all_urls'):
            # Convert to dict if it's not already
            normalized['all_urls'] = {}
        
        # Ensure primary URL is set if available
        if not normalized.get('url'):
            # Try to set primary URL from available sources
            if normalized.get('doi'):
                normalized['url'] = f"https://doi.org/{normalized['doi']}"
            elif normalized.get('pmid'):
                normalized['url'] = f"https://pubmed.ncbi.nlm.nih.gov/{normalized['pmid']}/"
            elif normalized.get('pmc'):
                normalized['url'] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{normalized['pmc']}/"
        
        return normalized
