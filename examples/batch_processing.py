#!/usr/bin/env python3
"""
Batch processing example for Medical Spytool.

This script demonstrates how to process multiple search queries
automatically and export results in different formats.
"""

import sys
from pathlib import Path
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dnb_spytool import MedicalSpytool

def create_sample_queries():
    """Create a sample queries file for demonstration."""
    queries = [
        "diabetes treatment",
        "covid-19 vaccines",
        "machine learning medicine",
        "cancer immunotherapy",
        "alzheimer disease therapy"
    ]
    
    queries_file = Path("sample_queries.txt")
    queries_file.write_text("\n".join(queries), encoding='utf-8')
    print(f"Created sample queries file: {queries_file}")
    return queries_file

def batch_search_example():
    """Demonstrate batch searching."""
    print("=== Batch Search Example ===")
    
    # Initialize tool
    spytool = MedicalSpytool()
    
    # Create sample queries
    queries_file = create_sample_queries()
    
    # Read queries
    queries = queries_file.read_text(encoding='utf-8').strip().split('\n')
    print(f"Processing {len(queries)} queries...")
    
    all_results = {}
    
    for i, query in enumerate(queries, 1):
        print(f"\nProcessing query {i}/{len(queries)}: {query}")
        
        try:
            # Search PubMed
            results = spytool.search_pubmed(query, max_results=50)
            all_results[query] = results
            
            print(f"  Found {len(results)} results")
            
            # Be nice to the API
            time.sleep(1)
            
        except Exception as e:
            print(f"  Error: {e}")
            all_results[query] = []
    
    return all_results

def export_batch_results(all_results):
    """Export batch results in multiple formats."""
    print("\n=== Exporting Batch Results ===")
    
    # Create results directory
    results_dir = Path("batch_results")
    results_dir.mkdir(exist_ok=True)
    
    spytool = MedicalSpytool()
    
    # Export individual query results
    for query, results in all_results.items():
        if results:
            # Clean filename
            clean_name = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
            clean_name = clean_name.replace(' ', '_')[:50]  # Limit length
            
            # Export to JSON
            json_file = results_dir / f"{clean_name}.json"
            spytool.export_json(results, str(json_file))
            
            # Export to CSV
            csv_file = results_dir / f"{clean_name}.csv"
            spytool.export_csv(results, str(csv_file))
            
            print(f"  Exported '{query}': {len(results)} results")
    
    # Create summary
    summary = {
        "total_queries": len(all_results),
        "successful_queries": len([q for q, r in all_results.items() if r]),
        "total_results": sum(len(results) for results in all_results.values()),
        "queries": {query: len(results) for query, results in all_results.items()}
    }
    
    summary_file = results_dir / "batch_summary.json"
    spytool.export_json(summary, str(summary_file))
    
    print(f"\nBatch processing complete!")
    print(f"Results saved to: {results_dir}")
    print(f"Total queries: {summary['total_queries']}")
    print(f"Total results: {summary['total_results']}")

def main():
    """Run batch processing example."""
    try:
        # Run batch search
        all_results = batch_search_example()
        
        # Export results
        export_batch_results(all_results)
        
    except Exception as e:
        print(f"Error in batch processing: {e}")

if __name__ == "__main__":
    main()
