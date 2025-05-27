"""
Path Manager
This module provides functions for handling file paths in the application.
These functions handle the differences between running as a script and running as a frozen executable.
"""
import os
import sys
import tempfile
import logging
import platform
import appdirs

logger = logging.getLogger(__name__)

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller frozen mode.
    
    Args:
        relative_path (str): Path relative to the application root
        
    Returns:
        str: Absolute path to the resource
    """
    try:
        # Check if running in PyInstaller bundle
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            # Running in normal Python environment
            # Get the directory containing this file
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Join the base path with the relative path
        abs_path = os.path.join(base_path, relative_path)
        
        # Normalize path for current OS
        abs_path = os.path.normpath(abs_path)
        
        logger.debug(f"Resource path for '{relative_path}' resolved to: {abs_path}")
        return abs_path
    except Exception as e:
        logger.error(f"Error resolving resource path for '{relative_path}': {str(e)}", exc_info=True)
        # Fallback to searching in current directory
        fallback_path = os.path.abspath(relative_path)
        logger.warning(f"Using fallback resource path: {fallback_path}")
        return fallback_path

def get_writeable_path(relative_path=None):
    """
    Get absolute path to a writeable directory that persists between app runs.
    This handles the differences between running as a script and a frozen executable.
    
    Args:
        relative_path (str, optional): Path relative to the user data directory
        
    Returns:
        str: Absolute path to a writeable directory or file
    """
    try:
        app_name = "MedicalSpyTool"
        
        # Check if running in PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Using appdirs to get the appropriate user data directory for the platform
            user_data_dir = appdirs.user_data_dir(app_name, roaming=True)
        else:
            # In development mode, use the project directory
            user_data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # If relative_path is provided, join with the user data directory
        if relative_path:
            full_path = os.path.join(user_data_dir, relative_path)
        else:
            full_path = user_data_dir
            
        # Normalize path for current OS
        full_path = os.path.normpath(full_path)
        
        # Ensure directory exists if path points to a directory
        # or ensure parent directory exists if path points to a file
        if not os.path.splitext(full_path)[1]:  # No file extension implies it's a directory
            os.makedirs(full_path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
        logger.debug(f"Writeable path for '{relative_path}' resolved to: {full_path}")
        return full_path
    except PermissionError as e:
        logger.error(f"Permission error when creating writeable path for '{relative_path}': {str(e)}")
        # Fallback to temp directory
        temp_dir = os.path.join(tempfile.gettempdir(), app_name)
        if relative_path:
            fallback_path = os.path.join(temp_dir, relative_path)
        else:
            fallback_path = temp_dir
            
        try:
            # Ensure the fallback directory exists
            if not os.path.splitext(fallback_path)[1]:  # Directory
                os.makedirs(fallback_path, exist_ok=True)
            else:  # File
                os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
                
            logger.warning(f"Using fallback writeable path due to permission error: {fallback_path}")
            return fallback_path
        except Exception as fallback_e:
            logger.error(f"Error creating fallback path: {str(fallback_e)}")
            return os.path.join(tempfile.gettempdir(), f"medicalspytool_{os.path.basename(relative_path) if relative_path else ''}")
    except Exception as e:
        logger.error(f"Error creating writeable path for '{relative_path}': {str(e)}", exc_info=True)
        # Ultimate fallback - just use temp directory
        temp_path = os.path.join(tempfile.gettempdir(), app_name)
        if relative_path:
            temp_path = os.path.join(temp_path, relative_path)
        logger.warning(f"Using temporary directory as fallback: {temp_path}")
        try:
            # Try to create the fallback directory
            if not os.path.splitext(temp_path)[1]:  # Directory
                os.makedirs(temp_path, exist_ok=True)
            else:  # File
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        except Exception as final_e:
            logger.error(f"Final fallback failed: {str(final_e)}")
        return temp_path
