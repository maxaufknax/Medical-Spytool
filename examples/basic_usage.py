#!/usr/bin/env python3
"""
Basic usage example for Medical Spytool.

This script demonstrates how to perform basic searches
and export results using the Medical Spytool API.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dnb_spytool import MedicalSpytool

def main():
    """Run basic search examples."""
    
    # Initialize the tool
    print("Initializing Medical Spytool...")
    spytool = MedicalSpytool()
    
    # Example 1: Basic PubMed search
    print("\n=== Example 1: Basic PubMed Search ===")
    try:
        results = spytool.search_pubmed("diabetes treatment", max_results=10)
        print(f"Found {len(results)} articles about diabetes treatment")
        
        # Show first result
        if results:
            first = results[0]
            print(f"First result: {first.get('title', 'No title')}")
    
    except Exception as e:
        print(f"Error in PubMed search: {e}")
    
    # Example 2: Multi-database search
    print("\n=== Example 2: Multi-Database Search ===")
    try:
        results = spytool.search_multiple(
            queries=["covid-19 vaccines"],
            databases=["pubmed", "dnb"],
            max_results=5
        )
        
        for db, db_results in results.items():
            print(f"{db.upper()}: {len(db_results)} results")
    
    except Exception as e:
        print(f"Error in multi-database search: {e}")
    
    # Example 3: Advanced search with filters
    print("\n=== Example 3: Advanced Search with Filters ===")
    try:
        results = spytool.search_pubmed(
            query="machine learning medicine",
            max_results=20,
            year_from=2020,
            year_to=2023
        )
        print(f"Found {len(results)} recent ML in medicine articles")
    
    except Exception as e:
        print(f"Error in advanced search: {e}")
    
    # Example 4: Export results
    print("\n=== Example 4: Export Results ===")
    try:
        if 'results' in locals() and results:
            # Export to JSON
            json_file = "example_results.json"
            spytool.export_json(results, json_file)
            print(f"Results exported to {json_file}")
            
            # Export to CSV
            csv_file = "example_results.csv"
            spytool.export_csv(results, csv_file)
            print(f"Results exported to {csv_file}")
    
    except Exception as e:
        print(f"Error in export: {e}")
    
    print("\n=== Examples completed ===")

if __name__ == "__main__":
    main()
