import PyInstaller.__main__
import os
import shutil

# --- Configuration ---
APP_NAME = 'MedicalSpytool'
ENTRY_POINT = 'main.py' # Assuming main.py is in the root directory
DIST_PATH = 'dist'
BUILD_PATH = 'build'

# Determine the project root directory (where build.py is located)
project_root = os.path.abspath(os.path.dirname(__file__))

# --- PyInstaller Options ---
pyinstaller_options = [
    '--name={}'.format(APP_NAME),
    '--windowed',  # Hide console window for GUI applications
    # '--onefile', # Consider --onedir for easier debugging first
    '--onedir',    # Creates a directory with all dependencies
    '--clean',     # Clean PyInstaller cache and remove temporary files before building
    '--noconfirm', # Replace output directory without asking
    '--distpath={}'.format(os.path.join(project_root, DIST_PATH)),
    '--workpath={}'.format(os.path.join(project_root, BUILD_PATH)),
    '--specpath={}'.format(project_root), # Place .spec file in root
    
    # Path to search for imports (project root)
    '--paths={}'.format(project_root),

    # --- Data files to include ---
    # Syntax: '--add-data=source{os.pathsep}destination_in_bundle'
    # os.pathsep is ';' on Windows, ':' on Linux/Mac
    '--add-data={}{}{}'.format(os.path.join(project_root, 'backend', 'static'), os.pathsep, os.path.join('backend', 'static')),
    '--add-data={}{}{}'.format(os.path.join(project_root, 'backend', 'templates'), os.pathsep, os.path.join('backend', 'templates')),
    '--add-data={}{}{}'.format(os.path.join(project_root, 'backend', 'translations'), os.pathsep, os.path.join('backend', 'translations')),
    # Add other necessary data like images, icons, etc.
    # Example: '--add-data={}{}{}'.format(os.path.join(project_root, 'icon.ico'), os.pathsep, '.'),

    # --- Hidden imports ---
    # Add modules that PyInstaller might miss, especially for Flask extensions
    '--hidden-import=flask_sqlalchemy',
    '--hidden-import=flask_login',
    '--hidden-import=flask_wtf',
    '--hidden-import=flask_babel', # For flask_babel
    '--hidden-import=babel.support', # For flask_babel
    '--hidden-import=werkzeug.security',
    '--hidden-import=sqlite3',
    '--hidden-import=sqlalchemy.dialects.sqlite',
    '--hidden-import=jinja2.ext', # Often needed for Flask templates
    '--hidden-import=itsdangerous', # Flask dependency
    '--hidden-import=click', # Flask CLI dependency
    '--hidden-import=blinker', # Signals in Flask
    '--hidden-import=wtforms.validators',
    # Add other potential hidden imports based on your project's dependencies
    # e.g., specific database drivers if not sqlite, other libraries used
    # '--hidden-import=pandas',
    # '--hidden-import=numpy',
]

# --- Main Execution ---
if __name__ == '__main__':
    print("Starting PyInstaller build for {}...".format(APP_NAME))
    
    # Construct the full command with entry point
    full_command = pyinstaller_options + [ENTRY_POINT]
    
    print("PyInstaller command: {}".format(' '.join(full_command)))
    
    try:
        PyInstaller.__main__.run(full_command)
        print("PyInstaller build completed successfully.")
        print("Output directory: {}".format(os.path.join(project_root, DIST_PATH, APP_NAME)))
    except Exception as e:
        print("Error during PyInstaller build: {}".format(e))
        # You might want to log the full traceback here
    
    # Optional: Clean up .spec file after build
    spec_file = os.path.join(project_root, '{}.spec'.format(APP_NAME))
    if os.path.exists(spec_file):
        try:
            # os.remove(spec_file)
            print(f"Spec file left at {spec_file} for review. You can delete it if not needed.")
        except OSError as e:
            print(f"Warning: Could not remove spec file {spec_file}: {e}")

    # Note on backend/instance:
    # The development database (e.g., medicalspy.db in backend/instance) should typically
    # not be bundled. The application should be designed to create the database file
    # in a user-writable location (e.g., AppData) if it doesn't exist on first run.
    # If you have essential *non-database* files in backend/instance that *must* be bundled,
    # you would add another '--add-data' line for them, e.g.:
    # '--add-data={}{}{}'.format(os.path.join(project_root, 'backend', 'instance', 'some_config.json'), os.pathsep, os.path.join('backend', 'instance')),
    # However, be very careful about bundling files that the app might try to modify.
    print("\n--- Build Script Finished ---")
    print("Remember to test the bundled application thoroughly.")
    print("If you encounter 'ModuleNotFound' errors, add the missing modules to '--hidden-import'.")
    print("If data files are missing, check your '--add-data' paths.")
