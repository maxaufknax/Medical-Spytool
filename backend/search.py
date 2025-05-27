#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Search module
This module handles searches in different databases.
"""

import logging
from datetime import datetime
import time # Import time module for duration calculation
from backend.connectors import get_connector_for_database

logger = logging.getLogger("MedicalSpy")


def _execute_search_for_db(connector, query, person_name="", db_timeout=30, **kwargs):
    """
    Executes a search for a single database using its connector,
    captures results, count, duration, and errors.

    Args:
        connector: The database connector instance.
        query (str): The search query.
        person_name (str, optional): Name of the person for association.
        db_timeout (int, optional): Timeout for this database search in seconds.
        **kwargs: Additional parameters for search_database_with_connector (e.g., additional_terms).

    Returns:
        dict: A dictionary containing:
            - "database" (str): Name of the database.
            - "results" (list): List of search results.
            - "count" (int): Number of results.
            - "error" (str or None): Error message if an error occurred, else None.
            - "duration" (float): Duration of the search in seconds.
    """
    start_time = time.time()
    results = []
    error_message = None
    search_params = kwargs.pop("params", {}) # Extract specific params for connector.search if any
    
    # Pass db_timeout to connector if it supports it via params
    # This is an assumption; connectors need to be designed to use params['timeout']
    if db_timeout:
        search_params['timeout'] = db_timeout

    try:
        # person_name is passed to search_database_with_connector for result association
        # kwargs (additional_terms, date_range etc.) are used for query construction
        results = search_database_with_connector(
            connector,
            query,
            person_name=person_name,
            params=search_params, 
            **kwargs # Pass other kwargs like additional_terms, date_range for query construction
        )
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error during search in {connector.name} (via _execute_search_for_db): {error_message}")
        # results remains []
    
    duration = time.time() - start_time
    return {
        "database": connector.name,
        "results": results,
        "count": len(results),
        "error": error_message,
        "duration": duration,
    }


def search_database_with_connector(
    connector,
    query,
    person_name="",
    additional_terms="",
    date_range=None,
    language=None,
    pub_type=None,
    field=None,
    params=None,
):
    """
    Search a database using the provided connector.

    Args:
        connector: The database connector to use
        query (str): The search query
        person_name (str, optional): Name of the person for association
        additional_terms (str, optional): Additional search terms
        date_range (dict, optional): Date range for the search
        language (str, optional): Language filter
        pub_type (str, optional): Publication type filter
        field (str, optional): Field to search in
        params (dict, optional): Additional parameters

    Returns:
        list: List of search results
    """
    if connector is None:
        logger.error("No connector provided for search")
        raise ValueError("Kein Datenbank-Connector für die Suche angegeben")

    # Log connector details for troubleshooting
    logger.debug(f"Using connector: {connector.name}")
    
    # Stelle sicher, dass query ein nicht-leerer String ist
    if not query or not isinstance(query, str):
        logger.warning(f"Invalid search query: {query} (type: {type(query)})")
        query = str(query) if query else ""
        logger.info(f"Converted query to: '{query}'")

    # Parameter-Dictionary erstellen, falls None
    if params is None:
        params = {}
        
    logger.debug(f"Search parameters: person_name='{person_name}', additional_terms='{additional_terms}', " 
                f"date_range={date_range}, language='{language}', pub_type='{pub_type}', field='{field}'")

    try:
        # Construct the full query
        try:
            full_query = connector.construct_query(
                query,
                additional_terms=additional_terms,
                date_range=date_range,
                language=language,
                pub_type=pub_type,
                field=field,
            )
            logger.debug(f"Query constructed by connector: '{full_query}'")
        except AttributeError as ae:
            # Falls der Connector keine construct_query Methode hat
            logger.warning(
                f"Connector {connector.name} has no construct_query method, using raw query: {str(ae)}"
            )
            full_query = query
            if additional_terms:
                full_query += f" {additional_terms}"
            logger.debug(f"Fallback query: '{full_query}'")

        # Log the search
        logger.info(f"Searching {connector.name} for: '{full_query}'")

        # Execute the search
        results = connector.search(full_query, params)

        # Überprüfe, ob Ergebnisse zurückgegeben wurden
        if results is None:
            logger.warning(f"Connector {connector.name} returned None instead of empty list")
            results = []
        
        # Log the result count
        logger.info(f"Search in {connector.name} returned {len(results)} results")
        
        # Log a sample result for debugging if available
        if results and len(results) > 0:
            logger.debug(f"Sample result from {connector.name}: {results[0]}")

        # Associate results with the person name
        for result in results:
            result["Name"] = person_name

        return results

    except Exception as e:
        logger.error(f"Error during search with {connector.name}: {str(e)}")
        import traceback
        logger.debug(f"Detailed error: {traceback.format_exc()}")
        # Re-raise mit aussagekräftiger Fehlermeldung
        raise Exception(f"Fehler bei der Suche in {connector.name}: {str(e)}") from e


def search_database(query, databases, search_mode="simple", person_name="", db_timeout=30, **kwargs):
    """
    Execute a search across specified databases.

    Args:
        query (str): The search query.
        databases (list): List of database names to search.
        search_mode (str, optional): Mode of search ('simple', 'person', 'advanced').
                                     Currently, this mainly influences logging or query construction
                                     if person_name is used directly in query.
        person_name (str, optional): Name of the person for association or if used in query.
        db_timeout (int, optional): Timeout in seconds for each database search.
        **kwargs: Additional arguments for query construction (e.g., additional_terms, date_range).

    Returns:
        list: A list of dictionaries, where each dictionary contains the
              search results and metadata for a single database:
              {"database": str, "results": list, "count": int, "error": str|None, "duration": float}
    """
    if not databases:
        # raise ValueError("No databases specified for search") # Or return empty list with error?
        logger.warning("No databases specified for search.")
        return [{"database": db_name, "results": [], "count": 0, "error": "No databases specified", "duration": 0.0} for db_name in databases]


    if not query and not person_name and search_mode != "advanced": # Advanced search can have empty main query
        logger.warning("Neither search query nor person name provided for non-advanced search.")
        # Return info for each database that was supposed to be searched
        return [{"database": db_name, "results": [], "count": 0, "error": "Neither search query nor person name provided", "duration": 0.0} for db_name in databases]

    all_db_outcomes = []

    for db_name in databases:
        try:
            connector = get_connector_for_database(db_name)
            logger.info(f"Initiating search for {db_name}. Mode: {search_mode}. Query: '{query[:100]}...'")
            
            # The 'query' here is the base query term.
            # person_name is passed for association.
            # kwargs (additional_terms, date_range etc.) are for query construction within search_database_with_connector.
            # db_timeout is for the individual database operation.
            outcome = _execute_search_for_db(
                connector,
                query,
                person_name=person_name,
                db_timeout=db_timeout,
                **kwargs # Pass additional_terms, date_range, etc.
            )
            
            # Add database name to each result dictionary if results exist
            # This is now handled by _execute_search_for_db returning connector.name
            # but results from connector might not have it, so search_database_with_connector adds it.
            # Let's ensure 'Database' field is in each result item.
            for res_item in outcome["results"]:
                res_item['Database'] = db_name # Ensure this key is present

            all_db_outcomes.append(outcome)
            
            if outcome["error"]:
                logger.warning(f"Search in {db_name} completed with error: {outcome['error']}. Duration: {outcome['duration']:.2f}s")
            else:
                logger.info(f"Search in {db_name} completed. Found {outcome['count']} results. Duration: {outcome['duration']:.2f}s")

        except Exception as e:
            # This catches errors from get_connector_for_database or unexpected errors in the loop itself
            logger.error(f"Critical error while processing database {db_name}: {str(e)}", exc_info=True)
            duration = 0 # Unknown as error was outside _execute_search_for_db
            # Attempt to get a start_time if possible, or set to a sensible default
            # For simplicity, if we error here, duration might be less accurate.
            # if 'start_time' in locals(): # Check if start_time was defined before error
            #    duration = time.time() - start_time
            
            all_db_outcomes.append({
                "database": db_name,
                "results": [],
                "count": 0,
                "error": f"Failed to initialize or process search for {db_name}: {str(e)}",
                "duration": 0.0 # Or calculate if possible
            })
            continue # Continue to the next database

    total_results_count = sum(o['count'] for o in all_db_outcomes)
    logger.info(f"All database searches concluded. Total results gathered: {total_results_count}.")
    
    # Previously, an exception was raised if all DBs failed.
    # Now, we return a list of outcomes, so the caller (blueprint) can decide how to handle errors.
    # The blueprint can check if all 'error' fields are non-None.

    return all_db_outcomes


# Alias for backwards compatibility (if it's truly needed and how it should behave with new return type)
# Considering the significant change in return type, an alias might be misleading.
# If external systems rely on the old return type of `search_databases`, this needs careful consideration.
# For now, let's assume direct refactoring is acceptable. If not, a more complex adapter for the alias would be needed.
# search_databases = search_database 


def parse_date_range(start_date, end_date):
    """
    Parse and validate a date range.

    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format

    Returns:
        dict or None: Date range dictionary or None if invalid
    """
    if not start_date or not end_date:
        return None

    try:
        # Validate dates
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")

        return {"start": start_date, "end": end_date}
    except ValueError:
        logger.warning(f"Invalid date format: {start_date} - {end_date}")
        return None


# combine_results might be less relevant if results are already aggregated by the blueprint from the new search_database output
def combine_results(db_outcomes_list):
    """
    Combine results from a list of database outcome dictionaries.
    Each dictionary is expected to have a "results" key.

    Args:
        db_outcomes_list (list): List of database outcome dictionaries 
                                 (from refactored search_database).

    Returns:
        list: Combined list of all individual result items.
    """
    combined = []
    for outcome in db_outcomes_list:
        if outcome.get("results"): # Check if 'results' key exists and is not None
            combined.extend(outcome["results"])
    return combined


def filter_results(results, filters):
    """
    Filter search results based on criteria.

    Args:
        results (list): Search results to filter
        filters (dict): Filter criteria

    Returns:
        list: Filtered results
    """
    filtered = []

    for result in results:
        # Check each filter condition
        include = True

        for key, value in filters.items():
            if key in result:
                # For text fields, check if value is contained
                if isinstance(result[key], str) and isinstance(value, str):
                    if value.lower() not in result[key].lower():
                        include = False
                        break
                # For numeric fields, check equality
                elif result[key] != value:
                    include = False
                    break

        if include:
            filtered.append(result)

    return filtered


def sort_results(results, sort_key, reverse=False):
    """
    Sort search results.

    Args:
        results (list): Search results to sort
        sort_key (str): Key to sort by
        reverse (bool, optional): Sort in descending order

    Returns:
        list: Sorted results
    """

    # Handle missing keys
    def get_sort_value(result):
        if sort_key in result:
            # Try to convert to int for numeric sorting
            try:
                return int(result[sort_key])
            except (ValueError, TypeError):
                return result[sort_key]
        return ""  # Default value for sorting

    return sorted(results, key=get_sort_value, reverse=reverse)
