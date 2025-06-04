"""
Command-line interface for DNB Spytool.
"""

import sys
import logging
from typing import List, Dict, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.dnb_client import DNBClient
try:
    from api.pubmed_client import PubMedClient
except ImportError:
    # Fallback to main package if local version not found
    import sys
    from pathlib import Path
    main_package = Path(__file__).parent.parent.parent / 'dnb_spytool'
    sys.path.insert(0, str(main_package))
    from api.pubmed_client import PubMedClient
try:
    from core.exporters import CSVExporter, JSONExporter, ExcelExporter, ReportExporter
    from core.visualizer import PublicationVisualizer
except ImportError:
    # Use utils from main package
    import sys
    from pathlib import Path
    main_package = Path(__file__).parent.parent.parent / 'dnb_spytool'
    sys.path.insert(0, str(main_package))
    
    # Create wrapper classes for the DataExporter
    class DataExporter:
        def __init__(self):
            from utils.exporters import DataExporter as MainDataExporter
            self._exporter = MainDataExporter()
        
        def export_publications(self, publications, format_type, output_path, **kwargs):
            return self._exporter.export_publications(publications, format_type, output_path, **kwargs)
    
    CSVExporter = JSONExporter = ExcelExporter = ReportExporter = DataExporter
    
    from analytics.visualizer import PublicationVisualizer

logger = logging.getLogger(__name__)

def search_publications(author: str, max_results: int, dnb_only: bool, pubmed_only: bool) -> List[Dict[str, Any]]:
    """Search for publications using specified databases."""
    all_publications = []
    
    # Determine which databases to search
    search_dnb = not pubmed_only
    search_pubmed = not dnb_only
    
    if search_dnb:
        logger.info("Searching DNB database...")
        try:
            dnb_client = DNBClient()
            dnb_results = dnb_client.search_publications(author, max_results)
            all_publications.extend(dnb_results)
            logger.info(f"Found {len(dnb_results)} publications in DNB")
        except Exception as e:
            logger.error(f"DNB search failed: {e}")
    
    if search_pubmed:
        logger.info("Searching PubMed database...")
        try:
            pubmed_client = PubMedClient()
            pubmed_results = pubmed_client.search_publications(author, max_results)
            all_publications.extend(pubmed_results)
            logger.info(f"Found {len(pubmed_results)} publications in PubMed")
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
    
    logger.info(f"Total publications found: {len(all_publications)}")
    return all_publications

def export_results(publications: List[Dict[str, Any]], args) -> None:
    """Export results in requested formats."""
    if not publications:
        logger.warning("No publications to export")
        return
    
    try:
        # Use the unified DataExporter approach
        exporter = DataExporter() if 'DataExporter' in globals() else CSVExporter()
        
        if args.export_csv:
            logger.info(f"Exporting to CSV: {args.export_csv}")
            if hasattr(exporter, 'export_publications'):
                exporter.export_publications(publications, 'csv', args.export_csv)
            else:
                exporter.export(publications, args.export_csv)
            logger.info("CSV export completed")
        
        if args.export_json:
            logger.info(f"Exporting to JSON: {args.export_json}")
            if hasattr(exporter, 'export_publications'):
                exporter.export_publications(publications, 'json', args.export_json)
            else:
                exporter.export(publications, args.export_json)
            logger.info("JSON export completed")
        
        if args.export_excel:
            logger.info(f"Exporting to Excel: {args.export_excel}")
            if hasattr(exporter, 'export_publications'):
                exporter.export_publications(publications, 'excel', args.export_excel)
            else:
                exporter.export(publications, args.export_excel)
            logger.info("Excel export completed")
        
        if args.generate_report:
            logger.info(f"Generating PDF report: {args.generate_report}")
            exporter = ReportExporter()
            exporter.export_report(publications, args.generate_report)
            logger.info("PDF report generated")
            
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise

def display_summary(publications: List[Dict[str, Any]]) -> None:
    """Display summary of search results."""
    if not publications:
        print("\nNo publications found.")
        return
    
    # Count by source
    sources = {}
    for pub in publications:
        source = pub.get('source', 'Unknown')
        sources[source] = sources.get(source, 0) + 1
      # Count by year
    years = {}
    for pub in publications:
        year = pub.get('year', pub.get('publication_year', 'Unknown'))
        # Handle different year formats safely
        if isinstance(year, int):
            year = str(year)
        elif isinstance(year, str) and year.isdigit():
            year = year
        else:
            year = 'Unknown'
        years[year] = years.get(year, 0) + 1
    
    print(f"\n=== Search Results Summary ===")
    print(f"Total Publications: {len(publications)}")
    
    print(f"\nBy Source:")
    for source, count in sources.items():
        print(f"  {source}: {count}")
    
    print(f"\nBy Year (top 5):")
    sorted_years = sorted(years.items(), key=lambda x: x[1], reverse=True)[:5]
    for year, count in sorted_years:
        print(f"  {year}: {count}")
    
    # Show first few publications
    print(f"\nFirst 3 Publications:")
    for i, pub in enumerate(publications[:3], 1):
        title = pub.get('title', 'No title')[:60]
        if len(pub.get('title', '')) > 60:
            title += "..."
        authors = ', '.join(pub.get('authors', [])[:2])
        if len(pub.get('authors', [])) > 2:
            authors += ", et al."
        print(f"  {i}. {title}")
        print(f"     Authors: {authors}")
        print(f"     Year: {pub.get('year', 'Unknown')} | Source: {pub.get('source', 'Unknown')}")
        print()

def main(args):
    """Main CLI function."""
    logger.info(f"Starting CLI search for author: {args.author}")
    
    try:
        # Search publications
        publications = search_publications(
            args.author, 
            args.max_results, 
            args.dnb_only, 
            args.pubmed_only
        )
        
        # Display summary
        display_summary(publications)
        
        # Export if requested
        export_results(publications, args)
        
        # Generate analytics if we have results
        if publications:
            try:
                visualizer = PublicationVisualizer()
                stats = visualizer.generate_summary_statistics(publications)
                
                print(f"\n=== Analytics Summary ===")
                print(f"Year Range: {stats.get('year_range', {}).get('earliest', 'N/A')} - {stats.get('year_range', {}).get('latest', 'N/A')}")
                print(f"Publications with DOI: {stats.get('content_completeness', {}).get('with_doi', 0)} ({stats.get('content_completeness', {}).get('with_doi_percent', 0):.1f}%)")
                print(f"Publications with Abstract: {stats.get('content_completeness', {}).get('with_abstract', 0)} ({stats.get('content_completeness', {}).get('with_abstract_percent', 0):.1f}%)")
                
            except Exception as e:
                logger.warning(f"Analytics generation failed: {e}")
        
        logger.info("CLI operation completed successfully")
        
    except Exception as e:
        logger.error(f"CLI operation failed: {e}")
        raise

if __name__ == '__main__':
    print("This module should be called from main.py with --cli flag")
    sys.exit(1)
