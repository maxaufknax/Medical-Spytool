#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medical Spytool - Database Connection Test
This script tests the connection to the PubMed and DNB databases.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to sys.path
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(BASE_DIR))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def test_pubmed_connection():
    """Test connection to PubMed"""
    from backend.connectors import PubMedConnector
    
    logging.info("Testing PubMed connection...")
    
    # Try with and without API key
    try:
        # Try to get API key from environment or default
        api_key = os.environ.get("PUBMED_API_KEY")
        
        # Create connector
        connector = PubMedConnector(api_key=api_key)
        logging.info(f"PubMed connector created, API key present: {bool(api_key)}")
        
        # Test simple search
        results = connector.search("diabetes", {"max_results": 3})
        
        if results:
            logging.info(f"PubMed connection successful! Found {len(results)} results.")
            logging.debug(f"Sample result: {results[0] if results else 'No results'}")
            return True
        else:
            logging.warning("PubMed connection returned no results.")
            if connector.last_error:
                logging.error(f"PubMed error: {connector.last_error}")
            return False
            
    except Exception as e:
        logging.error(f"PubMed connection error: {e}")
        import traceback
        logging.debug(traceback.format_exc())
        return False

def test_dnb_connection():
    """Test connection to Deutsche Nationalbibliothek"""
    from backend.connectors import DNBConnector
    
    logging.info("Testing DNB connection...")
    
    # Try with and without API key
    try:
        # Try to get API key from environment or default
        api_key = os.environ.get("DNB_API_KEY")
        
        # Create connector
        connector = DNBConnector(api_key=api_key)
        logging.info(f"DNB connector created, API key present: {bool(api_key)}")
        
        # Test simple search
        results = connector.search("medizin", {"max_results": 3})
        
        if results:
            logging.info(f"DNB connection successful! Found {len(results)} results.")
            logging.debug(f"Sample result: {results[0] if results else 'No results'}")
            return True
        else:
            logging.warning("DNB connection returned no results.")
            if connector.last_error:
                logging.error(f"DNB error: {connector.last_error}")
            return False
            
    except Exception as e:
        logging.error(f"DNB connection error: {e}")
        import traceback
        logging.debug(traceback.format_exc())
        return False

def main():
    """Main test function"""
    logging.info("Starting database connection tests...")
    
    pubmed_success = test_pubmed_connection()
    dnb_success = test_dnb_connection()
    
    # Print summary
    logging.info("\n=== Connection Test Results ===")
    logging.info(f"PubMed Connection: {'SUCCESS' if pubmed_success else 'FAILED'}")
    logging.info(f"DNB Connection: {'SUCCESS' if dnb_success else 'FAILED'}")
    
    # Return success only if both connections work
    return 0 if pubmed_success and dnb_success else 1

if __name__ == "__main__":
    sys.exit(main())
