#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Search module
This module handles searches in different databases.
"""

import logging
from datetime import datetime
from backend.connectors import get_connector_for_database

logger = logging.getLogger("MedicalSpy")


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


def search_database(query, databases, search_mode="simple", person_name="", **kwargs):
    """Execute a search across specified databases."""
    all_results = []
    search_errors = []
    
    if not databases:
        raise ValueError("No databases specified for search")
    
    if not query and not person_name:
        raise ValueError("Neither search query nor person name provided")
        
    for db_name in databases:
        try:
            connector = get_connector_for_database(db_name)
            logger.info(f"Searching in {db_name} with query: {query}")
            
            if search_mode == "person" and person_name:
                # Person search - uses person name as primary search term
                results = search_database_with_connector(connector, query, person_name=person_name, **kwargs)
            else:
                # Regular search
                results = search_database_with_connector(connector, query, **kwargs)
            
            if results:
                # Add database name to each result
                for result in results:
                    result['Database'] = db_name
                all_results.extend(results)
                logger.info(f"Found {len(results)} results in {db_name}")
            else:
                logger.warning(f"No results found in {db_name}")
                
        except Exception as e:
            # The error 'e' from search_database_with_connector is already specific
            # e.g., "Fehler bei der Suche in [DB_NAME]: [original error]"
            error_message_for_this_db = str(e)
            logger.error(f"Error during search in {db_name}: {error_message_for_this_db}")
            
            # If called for only one database (as from search_fix.py),
            # re-raise the specific error to be caught by search_fix.py
            if len(databases) == 1:
                raise Exception(error_message_for_this_db) from e
            
            # For multiple database calls (if search_database is ever called directly with multiple dbs),
            # collect errors and continue.
            search_errors.append({"database": db_name, "error": error_message_for_this_db})
            continue

    # This part is now mainly for direct calls to search_database with multiple databases,
    # if any such calls exist and expect this behavior.
    # For calls from search_fix.py (single DB), this won't be reached if an error occurred,
    # as the exception would have been re-raised above.
    if not all_results and search_errors:
        # Consolidate error messages if it was a multi-database search call that failed for all.
        error_messages_summary = [f"{err['database']}: {err['error']}" for err in search_errors]
        # This generic message might be too broad if some DBs succeeded and this is still hit.
        # However, if all_results is empty, it implies all failed or returned nothing.
        raise Exception(f"Search failed for all specified databases. Errors: {'; '.join(error_messages_summary)}")

    logger.info(f"Total results found: {len(all_results)}")
    if search_errors:
        logger.warning(f"Encountered {len(search_errors)} errors during search")

    return all_results


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


def combine_results(results_list):
    """
    Combine multiple result lists.

    Args:
        results_list (list): List of result lists

    Returns:
        list: Combined results
    """
    combined = []

    for results in results_list:
        combined.extend(results)

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


def perform_search(query, database=None, params=None):
    """Perform a search across specified databases."""
    logger.info(f"Starting search with query: '{query}', database: {database}, params: {params}")
    
    results = []
    try:
        if not query:
            logger.warning("Empty search query provided")
            return results
            
        if database == "PubMed" or not database:
            logger.info("Initializing PubMed search...")
            pubmed = PubMedConnector()
            try:
                pubmed_results = pubmed.search(query, params)
                logger.info(f"PubMed search returned {len(pubmed_results)} results")
                results.extend(pubmed_results)
            except Exception as e:
                logger.error(f"PubMed search failed: {e}", exc_info=True)
                
        if database == "DNB" or not database:
            logger.info("Initializing DNB search...")
            dnb = DNBConnector()
            try:
                dnb_results = dnb.search(query, params)
                logger.info(f"DNB search returned {len(dnb_results)} results")
                results.extend(dnb_results)
            except Exception as e:
                logger.error(f"DNB search failed: {e}", exc_info=True)
                
        logger.info(f"Total results found: {len(results)}")
        return results
        
    except Exception as e:
        logger.error(f"Search failed with error: {e}", exc_info=True)
        return []
