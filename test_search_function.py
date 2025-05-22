#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Medical Spytool search functionality
This script tests the enhanced search functionality
"""

import sys
import logging
from datetime import datetime
from backend.search_fix import enhanced_search_database

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_search():
    """Test the enhanced search functionality"""
    logger.info("Starting test search with enhanced_search_database...")
    query = "diabetes"
    databases = ["PubMed", "Deutsche Nationalbibliothek"]
    
    # Log start time
    start_time = datetime.now()
    logger.info(f"Search started at {start_time.strftime('%H:%M:%S')} with query: '{query}'")
    
    try:
        # Execute search
        results, errors, summary = enhanced_search_database(
            query=query,
            databases=databases,
            search_mode="simple"
        )
        
        # Log completion
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Search completed at {end_time.strftime('%H:%M:%S')} (duration: {duration:.2f}s)")
        
        # Log results summary
        logger.info(f"Total results: {len(results)}")
        logger.info(f"Results by database: {summary}")
        
        # Check for errors
        if errors:
            logger.warning(f"Search completed with errors: {errors}")
        
        return True
    except Exception as e:
        logger.error(f"Search test failed with exception: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("Testing search functionality...")
    success = test_search()
    
    if success:
        print("Search test completed successfully.")
        sys.exit(0)
    else:
        print("Search test failed.")
        sys.exit(1)
