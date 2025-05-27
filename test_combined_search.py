#!/usr/bin/env python3
"""
Test script for Combined Search functionality
"""

import os
import sys
import logging

# Add the parent directory to the Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_connectors.pubmed_connector import PubMedConnector
from database_connectors.dnb_connector import DNBConnector
from utils.config_manager import ConfigManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_single_connector(connector_class, connector_name, search_term):
    """Test a single database connector with the given search term."""
    print(f"\n{'='*60}")
    print(f"Testing {connector_name} with search term: '{search_term}'")
    print(f"{'='*60}")
    
    try:
        # Create connector instance
        connector = connector_class()
        
        # Check if API key is needed and validate
        api_key_valid = connector.validate_api_key()
        print(f"API Key valid: {api_key_valid}")
        
        # Perform the search using the new method signature
        print(f"Searching for: '{search_term}'...")
        results = connector.search(
            search_term=search_term,
            person_names=None,
            max_results=10
        )
        
        print(f"Found {len(results)} results")
          # Display first few results
        for i, result in enumerate(results[:3]):
            print(f"\nResult {i+1}:")
            print(f"  Title: {result.get('Title', result.get('title', 'N/A'))}")
            print(f"  Authors: {result.get('Authors', result.get('authors', 'N/A'))}")
            print(f"  Year: {result.get('Publication Year', result.get('year', 'N/A'))}")
            print(f"  DOI: {result.get('DOI', result.get('doi', 'N/A'))}")
            print(f"  Journal: {result.get('Journal', result.get('journal', 'N/A'))}")
            print(f"  Database: {result.get('Database', result.get('database', 'N/A'))}")
            
        return len(results)
        
    except Exception as e:
        print(f"Error testing {connector_name}: {str(e)}")
        logger.error(f"Error testing {connector_name}: {str(e)}", exc_info=True)
        return 0

def test_combined_search():
    """Test the combined search functionality similar to main.py."""
    search_term = "anette melk"
    
    print(f"\n{'='*80}")
    print(f"COMBINED SEARCH TEST")
    print(f"Search term: '{search_term}'")
    print(f"{'='*80}")
    
    # Load configuration
    try:
        config_manager = ConfigManager()
        app_config = config_manager.get_config()
        print(f"Configuration loaded successfully")
    except Exception as e:
        print(f"Warning: Could not load configuration: {str(e)}")
        app_config = {}
    
    # Define available connectors (same as in main.py)
    database_connectors = {
        'PubMed': PubMedConnector,
        'DNB': DNBConnector,
        # 'Scopus': ScopusConnector,  # Commented out to avoid import errors
        # 'WoS': WoSConnector,        # Commented out to avoid import errors  
        # 'GEPRIS': GeprisConnector   # Commented out to avoid import errors
    }
    
    all_results = []
    successful_searches = 0
    
    # Test each connector individually
    for db_name, connector_class in database_connectors.items():
        try:
            print(f"\n--- Testing {db_name} ---")
            
            # Create connector instance
            connector = connector_class()
            
            # Get API key from config if available
            api_key = app_config.get(f'{db_name.lower()}_api_key')
            if api_key:
                connector.api_key = api_key
                print(f"Using API key for {db_name}")
            
            # Validate API key
            if not connector.validate_api_key(api_key):
                print(f"Warning: Invalid API key for {db_name}")
                continue
            
            # Perform search
            results = connector.search(
                search_term=search_term,
                person_names=None,
                max_results=10
            )
            
            print(f"{db_name}: Found {len(results)} results")
            
            # Add results to combined list
            for result in results:
                result['database'] = db_name  # Tag each result with its source
                all_results.append(result)
            
            successful_searches += 1
            
        except Exception as e:
            print(f"Error with {db_name}: {str(e)}")
            logger.error(f"Error with {db_name}: {str(e)}", exc_info=True)
    
    # Summary
    print(f"\n{'='*80}")
    print(f"COMBINED SEARCH SUMMARY")
    print(f"{'='*80}")
    print(f"Search term: '{search_term}'")
    print(f"Databases tested: {len(database_connectors)}")
    print(f"Successful searches: {successful_searches}")
    print(f"Total results found: {len(all_results)}")
      # Show sample results
    if all_results:
        print(f"\nSample results:")
        for i, result in enumerate(all_results[:5]):
            print(f"\nResult {i+1} (from {result.get('database', result.get('Database', 'Unknown'))}):")
            print(f"  Title: {result.get('Title', result.get('title', 'N/A'))}")
            print(f"  Authors: {result.get('Authors', result.get('authors', 'N/A'))}")
            print(f"  Year: {result.get('Publication Year', result.get('year', 'N/A'))}")
            print(f"  Journal: {result.get('Journal', result.get('journal', 'N/A'))}")
    else:
        print(f"\nNo results found for '{search_term}'")
        print("This could be due to:")
        print("- Invalid API keys")
        print("- Network connectivity issues")
        print("- Database-specific query format issues")
        print("- The search term not matching any publications")
    
    return len(all_results)

if __name__ == "__main__":
    # Test individual connectors first
    test_single_connector(PubMedConnector, "PubMed", "anette melk")
    test_single_connector(DNBConnector, "DNB", "anette melk")
    
    # Test combined search
    total_results = test_combined_search()
    
    print(f"\n{'='*80}")
    print(f"TEST COMPLETED")
    print(f"Total results found: {total_results}")
    print(f"{'='*80}")
