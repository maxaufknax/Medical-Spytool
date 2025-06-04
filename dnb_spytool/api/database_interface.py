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
        'abstract',
        'journal',
        'isbn',
        'issn',
        'doi',
        'pmid',
        'url',
        'publisher',
        'language',
        'subject_headings',
        'publication_type'
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
        normalized = {}
        
        # Copy all fields, ensuring required ones exist
        for field in cls.REQUIRED_FIELDS + cls.OPTIONAL_FIELDS:
            normalized[field] = publication.get(field, None)
        
        # Normalize authors to string format
        if isinstance(normalized['authors'], list):
            normalized['authors'] = ', '.join(normalized['authors'])
        
        # Ensure database_source is set
        if not normalized['database_source']:
            normalized['database_source'] = 'unknown'
        
        # Convert publication_year to integer if possible
        if normalized['publication_year']:
            try:
                normalized['publication_year'] = int(normalized['publication_year'])
            except (ValueError, TypeError):
                normalized['publication_year'] = None

        # Normalize 'url' field to be a list of non-empty, stripped strings
        raw_urls = normalized.get('url')
        processed_urls = []
        if isinstance(raw_urls, str):
            stripped_url = raw_urls.strip()
            if stripped_url:
                processed_urls.append(stripped_url)
        elif isinstance(raw_urls, list):
            for item in raw_urls:
                if item is not None: # Ensure item is not None before str()
                    str_item = str(item).strip()
                    if str_item: # Ensure not empty after stripping
                        processed_urls.append(str_item)
        elif raw_urls is not None: # Handle other types that might be a single URL
            str_url = str(raw_urls).strip()
            if str_url:
                processed_urls.append(str_url)

        normalized['url'] = processed_urls
        
        return normalized
