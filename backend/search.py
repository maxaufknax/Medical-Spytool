#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Search module
This module handles searches in different databases.
"""

import logging
from datetime import datetime

logger = logging.getLogger("MedicalSpy")

def search_database(connector, query, person_name="", additional_terms="", date_range=None,
                   language=None, pub_type=None, field=None, params=None):
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
    
    # Stelle sicher, dass query ein nicht-leerer String ist
    if not query or not isinstance(query, str):
        logger.warning(f"Invalid search query: {query}")
        query = str(query) if query else ""
    
    # Parameter-Dictionary erstellen, falls None
    if params is None:
        params = {}
    
    try:
        # Construct the full query
        try:
            full_query = connector.construct_query(
                query, 
                additional_terms=additional_terms,
                date_range=date_range,
                language=language,
                pub_type=pub_type,
                field=field
            )
        except AttributeError:
            # Falls der Connector keine construct_query Methode hat
            logger.warning(f"Connector {connector.name} has no construct_query method, using raw query")
            full_query = query
            if additional_terms:
                full_query += f" {additional_terms}"
        
        # Log the search
        logger.info(f"Searching {connector.name} for: {full_query}")
        
        # Execute the search
        results = connector.search(full_query, params)
        
        # Überprüfe, ob Ergebnisse zurückgegeben wurden
        if results is None:
            logger.warning(f"Connector {connector.name} returned None instead of empty list")
            results = []
        
        # Associate results with the person name
        for result in results:
            result["Name"] = person_name
            
        logger.info(f"Found {len(results)} results from {connector.name}")
        return results
        
    except Exception as e:
        logger.error(f"Error during search with {connector.name}: {e}")
        # Re-raise mit aussagekräftiger Fehlermeldung
        raise Exception(f"Fehler bei der Suche in {connector.name}: {str(e)}") from e

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
        
        return {
            'start': start_date,
            'end': end_date
        }
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
