#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the DNB connector functionality.
This script tests the DNB connector's search and parse_results methods.
"""

import logging
import sys
from backend.connectors import DNBConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("DNBConnectorTest")

def test_dnb_search():
    """Test the DNB connector search functionality"""
    logger.info("Testing DNB connector search functionality...")
    
    # Create DNB connector instance
    dnb_connector = DNBConnector()
    
    # Test connection
    logger.info("Testing connection to DNB...")
    connection_status = dnb_connector.check_connection()
    logger.info(f"Connection status: {connection_status}")
    
    if connection_status:
        # Test search
        logger.info("Testing search functionality...")
        
        # Test with a medical term
        test_query = "Diabetes"
        logger.info(f"Searching for: {test_query}")
        
        try:
            results = dnb_connector.search(test_query, {"max_results": 5})
            
            logger.info(f"Search returned {len(results)} results")
            
            # Display first 5 results
            for i, result in enumerate(results[:5], 1):
                logger.info("-" * 50)
                logger.info(f"Result #{i}:")
                logger.info(f"Title: {result.get('Title', 'No title')}")
                logger.info(f"Authors: {result.get('Authors', 'No authors')}")
                logger.info(f"Year: {result.get('Publication Year', 'No year')}")
                logger.info(f"Publication Types: {result.get('Publication Types', 'No types')}")
                logger.info(f"DNB-ID: {result.get('DNB-ID', 'No ID')}")
                logger.info(f"URL: {result.get('DNB URL', 'No URL')}")
                
        except Exception as e:
            logger.error(f"Search failed with error: {str(e)}")
            return False
    
    else:
        logger.error("Connection to DNB failed, cannot test search functionality")
        return False
    
    logger.info("DNB connector test completed")
    return True

if __name__ == "__main__":
    logger.info("Starting DNB connector test...")
    result = test_dnb_search()
    sys.exit(0 if result else 1)
