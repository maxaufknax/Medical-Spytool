"""
Database Manager for coordinating multiple publication databases.

This module provides a unified interface for searching across multiple
databases (DNB, PubMed, etc.) and managing the results.
"""

from typing import List, Dict, Optional, Union
from enum import Enum
import time
from collections import defaultdict

from .database_interface import DatabaseInterface, PublicationSchema
from .dnb_client import DNBClient
from .pubmed_client import PubMedClient


class DatabaseType(Enum):
    """Enumeration of supported database types."""
    DNB = "dnb"
    PUBMED = "pubmed"
    BOTH = "both"


class DatabaseManager:
    """Manager for coordinating searches across multiple databases."""
    
    def __init__(self):
        """Initialize the database manager."""
        self.clients = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize all available database clients."""
        try:
            self.clients[DatabaseType.DNB] = DNBClient()
            print("✓ DNB client initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize DNB client: {e}")
        
        try:
            self.clients[DatabaseType.PUBMED] = PubMedClient()
            print("✓ PubMed client initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize PubMed client: {e}")
    
    def get_available_databases(self) -> List[DatabaseType]:
        """
        Get list of available database types.
        
        Returns:
            List of available DatabaseType enums
        """
        return list(self.clients.keys())
    
    def is_database_available(self, database: DatabaseType) -> bool:
        """
        Check if a specific database is available.
        
        Args:
            database: Database type to check
            
        Returns:
            True if database is available, False otherwise
        """
        return database in self.clients
    
    def get_database_info(self, database: DatabaseType) -> Optional[Dict]:
        """
        Get information about a specific database.
        
        Args:
            database: Database type
            
        Returns:
            Database information dictionary or None if not available
        """
        client = self.clients.get(database)
        if client:
            return client.get_database_info()
        return None
    
    def validate_query(self, query: str, database: DatabaseType) -> Dict[str, any]:
        """
        Validate a query for a specific database.
        
        Args:
            query: Query string
            database: Target database
            
        Returns:
            Validation result dictionary
        """
        client = self.clients.get(database)
        if not client:
            return {
                'is_valid': False,
                'error': f'Database {database.value} not available'
            }
        
        return client.validate_query(query)
    
    def search_single_database(self, database: DatabaseType, query: str, 
                             max_results: int = 100, **kwargs) -> Dict:
        """
        Search a single database.
        
        Args:
            database: Database to search
            query: Search query
            max_results: Maximum results
            **kwargs: Additional database-specific parameters
            
        Returns:
            Search results dictionary
        """
        client = self.clients.get(database)
        if not client:
            return {
                'publications': [],
                'total_records': 0,
                'database': database.value,
                'error': f'Database {database.value} not available'
            }
        
        try:
            print(f"Searching {database.value.upper()} for: {query}")
            start_time = time.time()
            
            publications = client.search_publications(query, max_results, **kwargs)
            
            search_time = time.time() - start_time
            print(f"✓ {database.value.upper()}: Found {len(publications)} publications in {search_time:.2f}s")
            
            return {
                'publications': publications,
                'total_records': len(publications),
                'database': database.value,
                'search_time': search_time,
                'query': query
            }
            
        except Exception as e:
            print(f"✗ Error searching {database.value.upper()}: {e}")
            return {
                'publications': [],
                'total_records': 0,
                'database': database.value,
                'error': str(e),
                'query': query
            }
    
    def search_multiple_databases(self, databases: List[DatabaseType], query: str,
                                max_results_per_db: int = 100, **kwargs) -> Dict:
        """
        Search multiple databases and combine results.
        
        Args:
            databases: List of databases to search
            query: Search query
            max_results_per_db: Maximum results per database
            **kwargs: Additional parameters
            
        Returns:
            Combined search results
        """
        all_results = {
            'publications': [],
            'total_records': 0,
            'databases_searched': [],
            'search_metadata': {},
            'combined_search': True,
            'query': query,
            'deduplication_stats': {}
        }
        
        # Search each database
        for db in databases:
            if db in self.clients:
                result = self.search_single_database(db, query, max_results_per_db, **kwargs)
                
                all_results['databases_searched'].append(db.value)
                all_results['search_metadata'][db.value] = {
                    'records_found': result['total_records'],
                    'search_time': result.get('search_time', 0),
                    'error': result.get('error')
                }
                
                # Add publications with database source marking
                for pub in result['publications']:
                    pub['database_source'] = db.value
                    all_results['publications'].append(pub)
                
                all_results['total_records'] += result['total_records']
        
        # Deduplicate if searching multiple databases
        if len(databases) > 1:
            all_results['publications'], dedup_stats = self._deduplicate_publications(
                all_results['publications']
            )
            all_results['deduplication_stats'] = dedup_stats
        
        return all_results
    
    def search_by_author(self, author_name: str, databases: Union[DatabaseType, List[DatabaseType]],
                        max_results_per_db: int = 100) -> Dict:
        """
        Search for publications by author across specified databases.
        
        Args:
            author_name: Name of the author
            databases: Database(s) to search
            max_results_per_db: Maximum results per database
            
        Returns:
            Search results dictionary
        """
        # Convert single database to list
        if isinstance(databases, DatabaseType):
            databases = [databases]
        
        # Handle BOTH option
        if DatabaseType.BOTH in databases:
            databases = [db for db in [DatabaseType.DNB, DatabaseType.PUBMED] 
                        if db in self.clients]
        
        return self.search_multiple_databases(databases, author_name, max_results_per_db)

    def search_multiple_authors(self, authors: List[str], databases: Union[DatabaseType, List[DatabaseType]],
                               max_results_per_author: int = 100) -> Dict:
        """
        Search for publications by multiple authors across specified databases.
        
        Args:
            authors: List of author names to search for
            databases: Database(s) to search
            max_results_per_author: Maximum results per author per database
            
        Returns:
            Combined search results dictionary
        """
        # Convert single database to list
        if isinstance(databases, DatabaseType):
            databases = [databases]
        
        # Handle BOTH option
        if DatabaseType.BOTH in databases:
            databases = [db for db in [DatabaseType.DNB, DatabaseType.PUBMED] 
                        if db in self.clients]
        
        all_results = {
            'publications': [],
            'total_records': 0,
            'authors_searched': authors,
            'databases_searched': [],
            'search_metadata': {},
            'combined_search': True,
            'multi_author_search': True,
            'deduplication_stats': {}
        }
          # Track results per author and database
        author_db_results = {}
        author_results = None  # Initialize to avoid UnboundLocalError
        
        for author in authors:
            print(f"\n📖 Searching for author: {author}")
            author_results = self.search_multiple_databases(databases, author, max_results_per_author)
            
            # Store author-specific results
            author_db_results[author] = author_results
            
            # Combine publications
            for pub in author_results.get('publications', []):
                pub['search_author'] = author  # Track which author this publication was found for
                all_results['publications'].append(pub)
            
            # Update metadata
            all_results['total_records'] += author_results.get('total_records', 0)
            
            # Merge search metadata
            if 'search_metadata' in author_results:
                for db, metadata in author_results['search_metadata'].items():
                    key = f"{author}_{db}"
                    all_results['search_metadata'][key] = metadata
        
        # Set databases searched (from last author search or available databases)
        if author_results:
            all_results['databases_searched'] = author_results.get('databases_searched', [])
        else:
            # No authors searched, but set available databases for completeness
            all_results['databases_searched'] = [db.value for db in databases if db in self.clients]
        
        # Deduplicate across all results
        if len(all_results['publications']) > 1:
            all_results['publications'], dedup_stats = self._deduplicate_publications(
                all_results['publications']
            )
            all_results['deduplication_stats'] = dedup_stats
        
        # Add summary statistics
        all_results['author_summary'] = {}
        for author in authors:
            author_pubs = [p for p in all_results['publications'] if p.get('search_author') == author]
            all_results['author_summary'][author] = {
                'publications_found': len(author_pubs),
                'databases_searched': all_results['databases_searched']
            }
        
        print(f"\n📊 Multi-author search completed:")
        print(f"   Authors: {len(authors)}")
        print(f"   Total publications: {len(all_results['publications'])}")
        print(f"   Databases: {', '.join(all_results['databases_searched'])}")
        
        return all_results
    
    def _deduplicate_publications(self, publications: List[Dict]) -> tuple[List[Dict], Dict]:
        """
        Remove duplicate publications based on title and author similarity.
        
        Args:
            publications: List of publications to deduplicate
            
        Returns:
            Tuple of (deduplicated_publications, deduplication_stats)
        """
        if len(publications) <= 1:
            return publications, {'duplicates_removed': 0, 'method': 'none'}
        
        deduplicated = []
        duplicates_found = 0
        seen_titles = set()
        
        for pub in publications:
            title = pub.get('title', '').lower().strip()
            
            # Create a normalized title for comparison
            normalized_title = self._normalize_title_for_dedup(title)
            
            if normalized_title and normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                deduplicated.append(pub)
            else:
                duplicates_found += 1
                # Keep track of which databases had the duplicate
                if 'duplicate_sources' not in pub:
                    pub['duplicate_sources'] = []
                pub['duplicate_sources'].append(pub.get('database_source', 'unknown'))
        
        dedup_stats = {
            'duplicates_removed': duplicates_found,
            'original_count': len(publications),
            'final_count': len(deduplicated),
            'method': 'title_normalization'
        }
        
        if duplicates_found > 0:
            print(f"🔍 Deduplication: Removed {duplicates_found} duplicates, kept {len(deduplicated)} unique publications")
        
        return deduplicated, dedup_stats
    
    def _normalize_title_for_dedup(self, title: str) -> str:
        """
        Normalize a title for deduplication comparison.
        
        Args:
            title: Original title
            
        Returns:
            Normalized title
        """
        import re
        
        # Convert to lowercase
        normalized = title.lower()
        
        # Remove common punctuation and extra spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.strip()
        
        # Remove common stop words that might appear in titles
        stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words = normalized.split()
        words = [w for w in words if w not in stop_words or len(words) <= 3]
        
        return ' '.join(words)
    
    def get_search_statistics(self, search_results: Dict) -> Dict:
        """
        Generate statistics for search results.
        
        Args:
            search_results: Results from database search
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'total_publications': len(search_results.get('publications', [])),
            'databases_used': search_results.get('databases_searched', []),
            'is_multi_database': search_results.get('combined_search', False),
            'query': search_results.get('query', ''),
            'deduplication_applied': 'deduplication_stats' in search_results
        }
        
        # Database-specific stats
        if 'search_metadata' in search_results:
            stats['database_breakdown'] = {}
            for db, metadata in search_results['search_metadata'].items():
                stats['database_breakdown'][db] = {
                    'records_found': metadata.get('records_found', 0),
                    'search_time': metadata.get('search_time', 0),
                    'has_error': metadata.get('error') is not None
                }
        
        # Publication source distribution
        if search_results.get('publications'):
            source_counts = defaultdict(int)
            for pub in search_results['publications']:
                source = pub.get('database_source', 'unknown')
                source_counts[source] += 1
            stats['source_distribution'] = dict(source_counts)
        
        return stats
    
    def configure_pubmed_api(self, api_key: str = "", email: str = "", tool_name: str = ""):
        """
        Configure PubMed API settings.
        
        Args:
            api_key: NCBI API key for increased rate limits
            email: Email address (required by NCBI)
            tool_name: Tool name for identification
        """
        try:
            if DatabaseType.PUBMED in self.clients:
                pubmed_client = self.clients[DatabaseType.PUBMED]
                # Update client configuration
                if hasattr(pubmed_client, 'configure_api'):
                    pubmed_client.configure_api(api_key, email, tool_name)
                else:
                    # Fallback: recreate client with new settings
                    from .pubmed_client import PubMedClient
                    self.clients[DatabaseType.PUBMED] = PubMedClient(api_key, email)
                print(f"✓ PubMed API configured with {'API key' if api_key else 'public access'}")
                return True
        except Exception as e:
            print(f"✗ Failed to configure PubMed API: {e}")
            return False
    
    def test_pubmed_api_key(self, api_key: str = "", email: str = "", tool_name: str = "") -> bool:
        """
        Test PubMed API key configuration.
        
        Args:
            api_key: NCBI API key to test
            email: Email address
            tool_name: Tool name
            
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Temporarily configure the client for testing
            if DatabaseType.PUBMED in self.clients:
                pubmed_client = self.clients[DatabaseType.PUBMED]
                
                # Store original configuration
                original_api_key = getattr(pubmed_client, 'api_key', '')
                original_email = getattr(pubmed_client, 'email', '')
                
                # Apply test configuration
                if hasattr(pubmed_client, 'configure_api'):
                    pubmed_client.configure_api(api_key, email, tool_name)
                else:
                    pubmed_client.api_key = api_key
                    pubmed_client.email = email
                
                # Test connection
                result = pubmed_client.test_connection()
                
                # Restore original configuration if test fails
                if not result:
                    if hasattr(pubmed_client, 'configure_api'):
                        pubmed_client.configure_api(original_api_key, original_email, tool_name)
                    else:
                        pubmed_client.api_key = original_api_key
                        pubmed_client.email = original_email
                
                return result
            else:
                # Create temporary client for testing
                from .pubmed_client import PubMedClient
                test_client = PubMedClient(api_key, email)
                return test_client.test_connection()
                
        except Exception as e:
            print(f"✗ PubMed API test failed: {e}")
            return False
    
    def save_pubmed_config(self, config: Dict[str, str]) -> bool:
        """
        Save PubMed API configuration to encrypted storage.
        
        Args:
            config: Configuration dictionary with keys: api_key, email, tool_name
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            import json
            import os
            from pathlib import Path
            
            # Create config directory if it doesn't exist
            config_dir = Path.home() / '.medical_spytool'
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / 'pubmed_config.json'
            
            # Encrypt sensitive data (API key)
            encrypted_config = config.copy()
            if config.get('api_key'):
                encrypted_config['api_key'] = self._encrypt_string(config['api_key'])
                encrypted_config['_encrypted'] = True
            else:
                encrypted_config['_encrypted'] = False
            
            # Save to file
            with open(config_file, 'w') as f:
                json.dump(encrypted_config, f, indent=2)
            
            print("✓ PubMed configuration saved successfully")
            return True
            
        except Exception as e:
            print(f"✗ Failed to save PubMed configuration: {e}")
            return False
    
    def load_pubmed_config(self) -> Optional[Dict[str, str]]:
        """
        Load PubMed API configuration from encrypted storage.
        
        Returns:
            Configuration dictionary or None if not found
        """
        try:
            import json
            from pathlib import Path
            
            config_file = Path.home() / '.medical_spytool' / 'pubmed_config.json'
            
            if not config_file.exists():
                return None
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Decrypt sensitive data if encrypted
            if config.get('_encrypted', False) and config.get('api_key'):
                config['api_key'] = self._decrypt_string(config['api_key'])
            
            # Remove encryption flag
            config.pop('_encrypted', None)
            
            print("✓ PubMed configuration loaded successfully")
            return config
            
        except Exception as e:
            print(f"✗ Failed to load PubMed configuration: {e}")
            return None
    
    def _encrypt_string(self, text: str) -> str:
        """
        Encrypt a string using simple base64 encoding.
        Note: This is basic encoding, not true encryption for production use.
        
        Args:
            text: Text to encrypt
            
        Returns:
            Encrypted text
        """
        try:
            import base64
            return base64.b64encode(text.encode()).decode()
        except Exception:
            return text
    
    def _decrypt_string(self, encrypted_text: str) -> str:
        """
        Decrypt a string using simple base64 decoding.
        
        Args:
            encrypted_text: Text to decrypt
            
        Returns:
            Decrypted text
        """
        try:
            import base64
            return base64.b64decode(encrypted_text.encode()).decode()
        except Exception:
            return encrypted_text
