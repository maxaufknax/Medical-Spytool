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

def search_single_database(query, db_name, search_mode="simple", db_timeout=25, **kwargs):
    """
    Search a single database with proper error handling
    
    Args:
        query (str): Search query
        db_name (str): Database name to search
        search_mode (str): Search mode (simple, person, advanced)
        db_timeout (int): Timeout for database operations in seconds
        
    Returns:
        dict: Results with metadata
    """
    logger.info(f"Starting search_single_database for {db_name} with query: '{query}'")
    log_message(f"Starting search for {db_name} with query: '{query}'")
    start_time = get_utc_now()
    error = None
    results = []
    
    # Set a shorter timeout for DNB which can sometimes hang
    if db_name == "Deutsche Nationalbibliothek":
        # DNB requires a shorter timeout to avoid hanging
        db_timeout = min(db_timeout, 20)  # Use at most 20 seconds for DNB
        logger.info(f"Using reduced timeout of {db_timeout}s for DNB search")
    
    try:
        logger.debug(f"Calling original_search_database for {db_name}...")
        log_message(f"Processing search for {db_name}...")
        
        # Call the original search function with just this database and with a timeout
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Search operation for {db_name} timed out after {db_timeout} seconds")
            
        # Set the timeout handler
        if hasattr(signal, 'SIGALRM'):  # Only available on Unix platforms
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(db_timeout)
            
        try:
            # Call the original search function
            db_results = original_search_database(
                query=query, 
                databases=[db_name],
                search_mode=search_mode,
                **kwargs
            )
            
            # Reset the alarm if we're on Unix
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                
            logger.debug(f"original_search_database for {db_name} returned. Processing results.")
            log_message(f"Search for {db_name} returned results successfully")
            
            # Format results
            results = db_results or []
            
        except TimeoutError as te:
            error = str(te)
            logger.error(f"Search timeout for {db_name}: {error}")
            log_message(f"Search timeout for {db_name}: {error}", level="ERROR")
            
            # Reset the alarm if we're on Unix
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                
        except Exception as e:
            error = str(e)
            logger.error(f"Error in original_search_database for {db_name}: {error}")
            log_message(f"Error searching {db_name}: {error}", level="ERROR")
            
            # Reset the alarm if we're on Unix
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
    except Exception as e:
        error = str(e)
        # Log the detailed error with traceback
        logger.error(f"Error searching {db_name}: {str(e)}")
        logger.debug(traceback.format_exc())
        log_message(f"Exception during search for {db_name}: {str(e)}", level="ERROR")
    
    # Calculate duration
    duration = (get_utc_now() - start_time).total_seconds()
    logger.info(f"Finished search_single_database for {db_name}. Duration: {duration:.2f}s, Results: {len(results)}, Error: {error}")
    
    return {
        "database": db_name,
        "results": results,
        "error": error,
        "duration": duration,
        "count": len(results)
    }

def enhanced_search_database(query, databases, search_mode="simple", timeout=30, **kwargs):
    """
    Enhanced search function that searches each database independently
    and handles errors gracefully
    
    Args:
        query (str): Search query
        databases (list): List of database names to search
        search_mode (str): Search mode (simple, person, advanced)
        timeout (int): Timeout in seconds for each database search
        
    Returns:
        tuple: (results, errors, summary) where:
               - results is a list of all search results
               - errors is a dict mapping database names to error messages
               - summary is a dict with statistics about the search
    """
    all_results = []
    errors = {}
    search_summary = {}
    
    logger.info(f"Starting enhanced search: mode={search_mode}, query='{query}', databases={databases}")
    start_time = get_utc_now()
    
    try:
        # Use ThreadPoolExecutor for concurrent search
        with ThreadPoolExecutor(max_workers=len(databases)) as executor:
            futures = {}
            for db in databases:
                logger.info(f"Submitting search for database: {db}")
                future = executor.submit(
                    search_single_database,
                    query=query,
                    db_name=db,
                    search_mode=search_mode,
                    db_timeout=min(timeout - 5, 25),  # Leave some margin for coordination
                    **kwargs
                )
                futures[future] = db
            
            # Process results as they complete
            for future in as_completed(futures):
                db_name = futures[future]
                try:
                    logger.info(f"Waiting for results from {db_name} with timeout of {timeout}s...")
                    # Get the result with timeout
                    result = future.result(timeout=timeout)
                    search_summary[db_name] = result['count']
                    
                    if result["error"]:
                        errors[db_name] = result["error"]
                        logger.warning(f"Search for {db_name} completed with error: {result['error']}")
                        log_message(f"Search for {db_name} completed with error: {result['error']}", level="WARNING")
                    else:
                        # Add database results to combined results
                        all_results.extend(result["results"])
                        logger.info(f"Search for {db_name} completed successfully: {result['count']} results in {result['duration']:.2f}s")
                        log_message(f"Search for {db_name} completed successfully: {result['count']} results in {result['duration']:.2f}s")
                    
                except TimeoutError:
                    errors[db_name] = f"Search timed out after {timeout} seconds"
                    logger.error(f"Search for {db_name} timed out after {timeout}s")
                    log_message(f"Search for {db_name} timed out after {timeout}s", level="ERROR")
                    # Cancel the future if possible to prevent hanging threads
                    future.cancel()
                except Exception as e:
                    errors[db_name] = str(e)
                    logger.error(f"Error processing results from {db_name}: {str(e)}", exc_info=True)
                    log_message(f"Error processing results from {db_name}: {str(e)}", level="ERROR")
        
        total_duration = (get_utc_now() - start_time).total_seconds()
        logger.info(f"Enhanced search completed in {total_duration:.2f}s with {len(all_results)} total results")
        
        # Add summary information
        search_summary['total_results'] = len(all_results)
        search_summary['duration'] = total_duration
        search_summary['databases_with_errors'] = len(errors)
        
        if errors:
            logger.warning(f"Search completed with errors in {len(errors)} databases: {errors}")
            log_message(f"Search completed with {len(errors)} database errors", level="WARNING")
        
        return all_results, errors, search_summary
        
    except Exception as e:
        logger.error(f"Critical error in enhanced search: {str(e)}", exc_info=True)
        log_message(f"Critical error in enhanced search: {str(e)}", level="ERROR")
        # Ensure we return something meaningful even on critical errors
        return [], {"critical_error": str(e)}, {"total_results": 0, "duration": 0, "error": str(e)}
