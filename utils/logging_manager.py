"""
Logging Manager

This module handles application logging.
"""

import os
import logging
from datetime import datetime

# Global log list for the application
GLOBAL_LOG = []

def setup_logging():
    """
    Set up application logging.
    
    Returns:
        logging.Logger: Configured logger.
    """
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Get current timestamp for log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join("logs", f"medicalspytool_{timestamp}.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("MedicalSpyTool")
    logger.info("Logging initialized")
    
    return logger

def log_message(log_widget, message):
    """
    Add a message to the log and display it in the widget.
    
    Args:
        log_widget (tkinter.Text or None): Widget for displaying log messages.
        message (str): Message to log.
    """
    global GLOBAL_LOG
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {message}\n"
    
    # Add to global log
    GLOBAL_LOG.append(full_msg)
    
    # Log to logger
    logging.getLogger("MedicalSpyTool").info(message)
    
    # Display in widget if available
    if log_widget:
        try:
            log_widget.config(state="normal")
            log_widget.insert("end", full_msg)
            log_widget.see("end")
            log_widget.config(state="disabled")
        except Exception as e:
            print(f"Error logging to GUI: {e}")
    else:
        print(full_msg.strip())

def clear_log(log_widget):
    """
    Clear the log content.
    
    Args:
        log_widget (tkinter.Text): Widget containing the log.
    """
    global GLOBAL_LOG
    GLOBAL_LOG = []
    
    if log_widget:
        log_widget.config(state="normal")
        log_widget.delete("1.0", "end")
        log_widget.config(state="disabled")

def export_log(log_widget, file_path):
    """
    Export the log to a file.
    
    Args:
        log_widget (tkinter.Text): Widget containing the log.
        file_path (str): Path to save the log file.
        
    Returns:
        bool: True if export was successful, False otherwise.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("".join(GLOBAL_LOG))
        
        log_message(log_widget, f"Log exported to {file_path}")
        return True
    except Exception as e:
        logging.getLogger("MedicalSpyTool").error(f"Error exporting log: {e}", exc_info=True)
        log_message(log_widget, f"Error exporting log: {e}")
        return False
