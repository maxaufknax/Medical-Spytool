"""
Main entry point for the DNB Spytool CLI application.
"""

import sys
import os

# Fix import paths for both development and executable environments
def fix_imports():
    """Fix import paths for PyInstaller compatibility."""
    cli_main = None
    create_parser = None
    gui_main = None
    
    # Try different import strategies
    import_strategies = [
        # Strategy 1: Relative imports (development)
        lambda: __import_relative(),
        # Strategy 2: Absolute imports (standard)
        lambda: __import_absolute(),
        # Strategy 3: Path manipulation (last resort)
        lambda: __import_with_path(),
    ]
    
    for strategy in import_strategies:
        try:
            cli_main, create_parser, gui_main = strategy()
            break
        except ImportError as e:
            continue
    
    if cli_main is None:
        raise ImportError("Unable to import required modules using any strategy")
    
    return cli_main, create_parser, gui_main

def __import_relative():
    """Try relative imports."""
    from .cli import main as cli_main, create_parser
    try:
        from .gui.main_window import main as gui_main
    except ImportError:
        gui_main = None  # GUI might not be available
    return cli_main, create_parser, gui_main

def __import_absolute():
    """Try absolute imports."""
    from dnb_spytool.cli import main as cli_main, create_parser
    try:
        from dnb_spytool.gui.main_window import main as gui_main
    except ImportError:
        gui_main = None  # GUI might not be available
    return cli_main, create_parser, gui_main

def __import_with_path():
    """Try imports with path manipulation."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from dnb_spytool.cli import main as cli_main, create_parser
    try:
        from dnb_spytool.gui.main_window import main as gui_main
    except ImportError:
        gui_main = None  # GUI might not be available
    return cli_main, create_parser, gui_main

# Get the imports
cli_main, create_parser, gui_main = fix_imports()


def main():
    """Main entry point for the application."""
    # Use the full parser from cli.py to ensure all arguments are supported
    parser = create_parser()
    args = parser.parse_args()
    
    # If GUI is explicitly requested or no search arguments are provided, launch GUI
    if args.gui or (not args.author and not args.authors and not args.validate_only):
        if gui_main is not None:
            gui_main()
        else:
            print("GUI is not available. Running in CLI mode.")
            print("Use --help to see available commands.")
            if not (args.author or args.authors or args.validate_only):
                parser.print_help()
                return
            cli_main(args)
    else:
        cli_main(args)


if __name__ == '__main__':
    main()
