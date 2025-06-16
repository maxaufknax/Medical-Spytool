#!/usr/bin/env python3
"""
DNB Spytool - Medical Publication Research Tool
Main entry point for the application.
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Setup logging configuration."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def run_gui():
    """Run the GUI application."""
    from gui.main_window import main
    main()

def run_cli(args):
    """Run the CLI application."""
    from cli.main import main as cli_main
    cli_main(args)

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description='DNB Spytool - Medical Publication Research Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Run GUI
  %(prog)s --cli --author "John Smith"        # CLI search
  %(prog)s --cli --author "John Smith" --export-csv results.csv
        """
    )
    
    parser.add_argument('--cli', action='store_true',
                       help='Run in command-line mode')
    parser.add_argument('--author', type=str,
                       help='Author name to search for (CLI mode)')
    parser.add_argument('--max-results', type=int, default=1000,
                       help='Maximum number of results (default: 1000)')
    parser.add_argument('--dnb-only', action='store_true',
                       help='Search only DNB database')
    parser.add_argument('--pubmed-only', action='store_true',
                       help='Search only PubMed database')
    parser.add_argument('--export-csv', type=str,
                       help='Export results to CSV file')
    parser.add_argument('--export-json', type=str,
                       help='Export results to JSON file')
    parser.add_argument('--export-excel', type=str,
                       help='Export results to Excel file')
    parser.add_argument('--generate-report', type=str,
                       help='Generate PDF report')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Set logging level')
    parser.add_argument('--log-file', type=str,
                       help='Log to file instead of console')
    parser.add_argument('--version', action='version', version='DNB Spytool 1.0')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting DNB Spytool v1.0")
    
    try:
        if args.cli:
            if not args.author:
                parser.error("--author is required in CLI mode")
            run_cli(args)
        else:
            run_gui()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
