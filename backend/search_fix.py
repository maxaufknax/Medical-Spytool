#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Search Fix

This helper script provides enhanced search functionality by extending 
the existing search_database function with better error handling and
timeout management for individual database searches.

Usage:
Import and use the enhanced_search_database function instead of search_database
"""

import logging
import traceback
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

from backend.search import search_database as original_search_database
from backend.utils import log_message

logger = logging.getLogger(__name__)

def get_utc_now():
    """Helper function to get current UTC time"""
    return datetime.now(timezone.utc)

def search_single_database(query, db_name, search_mode="simple", **kwargs):
    """
    Search a single database with proper error handling
    
    Args:
        query (str): Search query
        db_name (str): Database name to search
        search_mode (str): Search mode (simple, person, advanced)
        
    Returns:
        dict: Results with metadata
    """
    start_time = get_utc_now()
    error = None
    results = []
    
    try:
        # Call the original search function with just this database
        db_results = original_search_database(
            query=query, 
            databases=[db_name],
            search_mode=search_mode,
            **kwargs
        )
        
        # Format results
        results = db_results or []
        
    except Exception as e:
        error = str(e)
        # Log the detailed error with traceback
        logger.error(f"Error searching {db_name}: {str(e)}")
        logger.debug(traceback.format_exc())
    
    # Calculate duration
    duration = (get_utc_now() - start_time).total_seconds()
    
    return {
        "database": db_name,
        "results": results,
        "error": error,
        "duration": duration,
        "count": len(results)
    }

def enhanced_search_database(query, databases, search_mode="simple", timeout=60, **kwargs):
    """
    Enhanced search function that searches each database independently
    and handles errors gracefully
    
    Args:
        query (str): Search query
        databases (list): List of database names to search
        search_mode (str): Search mode (simple, person, advanced)
        timeout (int): Timeout in seconds for each database search
        
    Returns:
        tuple: (results, errors) where results is a list of all results
               and errors is a dict mapping database names to error messages
    """
    all_results = []
    errors = {}
    
    logger.info(f"Starting enhanced search: mode={search_mode}, query='{query}', databases={databases}")
    start_time = get_utc_now()
    
    # Use ThreadPoolExecutor for concurrent search (but can be made sequential if needed)
    with ThreadPoolExecutor(max_workers=len(databases)) as executor:
        # Submit all search tasks
        futures = {}
        for db in databases:
            logger.info(f"Submitting search for database: {db}")
            future = executor.submit(
                search_single_database,
                query=query,
                db_name=db,
                search_mode=search_mode,
                **kwargs
            )
            futures[future] = db
        
        # Process results as they complete
        for future in as_completed(futures):
            db_name = futures[future]
            try:
                # Get the result with timeout
                result = future.result(timeout=timeout)
                
                if result["error"]:
                    errors[db_name] = result["error"]
                    logger.warning(f"Search for {db_name} completed with error: {result['error']}")
                else:
                    # Add database results to combined results
                    all_results.extend(result["results"])
                    logger.info(f"Search for {db_name} completed successfully: {result['count']} results in {result['duration']:.2f}s")
                
            except TimeoutError:
                errors[db_name] = f"Search timed out after {timeout} seconds"
                logger.error(f"Search for {db_name} timed out after {timeout}s")
            except Exception as e:
                errors[db_name] = str(e)
                logger.error(f"Error processing results from {db_name}: {str(e)}")
    
    total_duration = (get_utc_now() - start_time).total_seconds()
    logger.info(f"Enhanced search completed in {total_duration:.2f}s with {len(all_results)} total results")
    
    if errors:
        logger.warning(f"Search completed with errors in {len(errors)} databases: {errors}")
    
    return all_results, errors
