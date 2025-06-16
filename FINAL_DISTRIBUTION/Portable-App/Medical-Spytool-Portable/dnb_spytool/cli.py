"""
Command Line Interface for the DNB Spytool application.
"""

import argparse
import sys
import os
from typing import List, Optional
from .api.database_manager import DatabaseManager, DatabaseType
from .analytics.analyzer import PublicationAnalyzer
from .analytics.visualizer import PublicationVisualizer
from .utils.exporters import DataExporter
from .utils.validators import InputValidator


def main(args=None):
    """Main CLI function."""
    if args is None:
        parser = create_parser()
        args = parser.parse_args()
    
    # Initialize validator
    validator = InputValidator()
    
    try:
        # Validate inputs
        if not validate_cli_args(args, validator):
            return 1
        
        # Initialize database manager
        print("Initializing database connections...")
        db_manager = DatabaseManager()
        
        # Determine which database(s) to use
        database_type = DatabaseType(args.database)
        
        # Determine authors to search
        authors = get_authors_list(args)
        
        # Perform search
        print(f"Searching for {len(authors)} author(s) in {database_type.value} database(s)...")
        results = db_manager.search_multiple_authors(authors, database_type, args.max_results)
        
        if not results or not results.get('publications'):
            print("No publications found.")
            return 0
        
        publications = results['publications']
        print(f"Found {len(publications)} publications")
        
        # Print database breakdown
        db_breakdown = {}
        for pub in publications:
            source = pub.get('database_source', 'unknown')
            db_breakdown[source] = db_breakdown.get(source, 0) + 1
        
        for source, count in db_breakdown.items():
            print(f"  - {source}: {count} publications")
        
        # Export data if requested
        if args.output:
            exporter = DataExporter()
            success = exporter.export_publications(
                publications, args.format, args.output, include_metadata=True
            )
            if success:
                print(f"Data exported to: {args.output}")
            else:
                print("Failed to export data")
                return 1
        
        # Generate analytics if requested
        if args.analytics:
            print("Generating analytics...")
            analyzer = PublicationAnalyzer(publications)
            
            # Print summary to console
            summary = analyzer.generate_summary_report()
            print("\n" + "="*50)
            print(summary)
            print("="*50)
            
            # Generate detailed report if requested
            if args.output:
                base_path = os.path.splitext(args.output)[0]
                report_path = f"{base_path}_report.{args.report_format}"
                
                visualizer = PublicationVisualizer(analyzer)
                exporter = DataExporter()
                
                success = exporter.export_analysis_report(
                    analyzer, visualizer, report_path, args.report_format
                )
                
                if success:
                    print(f"Analysis report saved to: {report_path}")
                    
                    # Also save individual charts
                    charts_dir = f"{base_path}_charts"
                    chart_files = visualizer.save_all_charts(charts_dir)
                    if chart_files:
                        print(f"Charts saved to: {charts_dir}")
                else:
                    print("Failed to generate analysis report")
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description='DNB Spytool - German National Library Search Tool',
        epilog="""
Examples:
  %(prog)s --author "Johann Wolfgang von Goethe"
  %(prog)s --authors "Goethe,Schiller" --format csv --output results.csv
  %(prog)s --author "Kafka" --analytics --report-format pdf
  %(prog)s --gui
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Interface selection
    parser.add_argument('--gui', action='store_true',
                       help='Launch graphical user interface')
    
    # Database selection
    parser.add_argument('--database', type=str,
                       choices=['dnb', 'pubmed', 'both'], default='dnb',
                       help='Database to search (default: dnb)')
    
    # Author selection
    author_group = parser.add_mutually_exclusive_group()
    author_group.add_argument('--author', type=str,
                             help='Search for a single author')
    author_group.add_argument('--authors', type=str,
                             help='Search for multiple authors (comma-separated)')
    
    # Search parameters
    parser.add_argument('--max-results', type=int, default=100,
                       help='Maximum number of results per author (default: 100)')
    
    # Output options
    parser.add_argument('--output', type=str,
                       help='Output file path')
    parser.add_argument('--format', type=str, 
                       choices=['csv', 'json', 'excel', 'xlsx'], 
                       default='csv',
                       help='Output format (default: csv)')
    
    # Analytics options
    parser.add_argument('--analytics', action='store_true',
                       help='Generate analytics and visualizations')
    parser.add_argument('--report-format', type=str,
                       choices=['pdf', 'html'], default='pdf',
                       help='Analytics report format (default: pdf)')
    
    # Utility options
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate inputs without performing search')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    return parser


def validate_cli_args(args, validator: InputValidator) -> bool:
    """
    Validate command line arguments.
    
    Args:
        args: Parsed command line arguments
        validator: InputValidator instance
        
    Returns:
        True if valid, False otherwise
    """
    errors = []
    warnings = []
    
    # Check if GUI mode
    if args.gui:
        return True  # GUI will handle its own validation
    
    # Validate authors
    authors = get_authors_list(args)
    if not authors:
        errors.append("At least one author must be specified (use --author or --authors)")
    else:
        author_validation = validator.validate_author_list(authors)
        if not author_validation['is_valid']:
            errors.extend(author_validation['errors'])
        warnings.extend(author_validation['warnings'])
    
    # Validate output path if provided
    if args.output:
        path_validation = validator.validate_output_path(args.output, args.format)
        if not path_validation['is_valid']:
            errors.extend(path_validation['errors'])
        warnings.extend(path_validation['warnings'])
    
    # Validate search parameters
    search_validation = validator.validate_search_parameters(
        max_records=args.max_results,
        format=args.format
    )
    if not search_validation['is_valid']:
        errors.extend(search_validation['errors'])
    warnings.extend(search_validation['warnings'])
    
    # Print warnings
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
        print()
    
    # Print errors and exit if any
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    # If validate-only mode, exit after validation
    if args.validate_only:
        print("Validation passed!")
        sys.exit(0)
    
    return True


def get_authors_list(args) -> List[str]:
    """
    Extract list of authors from command line arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        List of author names
    """
    authors = []
    
    if args.author:
        authors.append(args.author.strip())
    elif args.authors:
        # Split by comma and clean up
        authors = [author.strip() for author in args.authors.split(',')]
        authors = [author for author in authors if author]  # Remove empty strings
    
    return authors


def print_search_progress(current: int, total: int, author: str = ""):
    """Print search progress."""
    percentage = (current / total) * 100 if total > 0 else 0
    bar_length = 30
    filled_length = int(bar_length * current // total) if total > 0 else 0
    
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    
    if author:
        print(f'\rSearching {author}: |{bar}| {percentage:.1f}% ({current}/{total})', end='')
    else:
        print(f'\rProgress: |{bar}| {percentage:.1f}% ({current}/{total})', end='')
    
    if current == total:
        print()  # New line when complete


def interactive_mode():
    """Run the CLI in interactive mode."""
    print("=== DNB Spytool Interactive Mode ===")
    print("Enter 'help' for available commands, 'quit' to exit")
    
    validator = InputValidator()
    db_manager = DatabaseManager()
    exporter = DataExporter()
    
    while True:
        try:
            command = input("\ndnb> ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            elif command.lower() == 'help':
                print_interactive_help()
            elif command.startswith('search '):
                handle_interactive_search(command, db_manager, validator)
            elif command.startswith('export '):
                handle_interactive_export(command, exporter)
            elif command.lower() == 'status':
                print_status(db_manager)
            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands")
                
        except KeyboardInterrupt:
            print("\nUse 'quit' to exit")
        except EOFError:
            print("\nGoodbye!")
            break


def print_interactive_help():
    """Print help for interactive mode."""
    help_text = """
Available commands:
  search <author>     - Search for publications by author
  export <format>     - Export last search results
  status             - Show current status
  help               - Show this help message
  quit               - Exit interactive mode

Examples:
  search Goethe
  search "Johann Wolfgang von Goethe"
  export csv
  export json results.json
"""
    print(help_text)


def handle_interactive_search(command: str, db_manager: DatabaseManager, validator: InputValidator):
    """Handle interactive search command."""
    # Extract author name from command
    author = command[7:].strip().strip('"\'')
    
    if not author:
        print("Usage: search <author_name>")
        return
    
    # Validate author
    validation = validator.validate_author_name(author)
    if not validation['is_valid']:
        print("Invalid author name:")
        for error in validation['errors']:
            print(f"  - {error}")
        return
    
    try:
        print(f"Searching for publications by: {author}")
        # Default to DNB for interactive mode
        results = db_manager.search_by_author(author, DatabaseType.DNB, 50)
        
        if results and results.get('publications'):
            publications = results['publications']
            print(f"Found {len(publications)} publications")
            
            # Show first few results
            print("\nFirst 5 results:")
            for i, pub in enumerate(publications[:5]):
                title = pub.get('title', 'No title')
                year = pub.get('publication_year', 'Unknown year')
                print(f"  {i+1}. {title} ({year})")
            
            if len(publications) > 5:
                print(f"  ... and {len(publications) - 5} more")
            
            # Store results for export
            globals()['last_search_results'] = publications
        else:
            print("No publications found")
            
    except Exception as e:
        print(f"Search failed: {e}")


def handle_interactive_export(command: str, exporter: DataExporter):
    """Handle interactive export command."""
    if 'last_search_results' not in globals():
        print("No search results to export. Run a search first.")
        return
    
    # Parse export command
    parts = command.split()
    if len(parts) < 2:
        print("Usage: export <format> [filename]")
        return
    
    format_type = parts[1]
    filename = parts[2] if len(parts) > 2 else f"results.{format_type}"
    
    try:
        success = exporter.export_publications(
            globals()['last_search_results'], format_type, filename
        )
        if success:
            print(f"Results exported to: {filename}")
        else:
            print("Export failed")
    except Exception as e:
        print(f"Export error: {e}")


def print_status(db_manager: DatabaseManager):
    """Print current status in interactive mode."""
    print("Database Manager Status:")
    available_dbs = db_manager.get_available_databases()
    for db_type in available_dbs:
        db_info = db_manager.get_database_info(db_type)
        print(f"  ✓ {db_info['name']} - Available")
    
    if 'last_search_results' in globals():
        count = len(globals()['last_search_results'])
        print(f"Last search: {count} publications in memory")
    else:
        print("No search results in memory")


if __name__ == '__main__':
    sys.exit(main())
