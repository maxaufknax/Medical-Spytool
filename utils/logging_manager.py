"""
Logging Manager

This module provides functions for logging messages.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Global log list to store log messages
GLOBAL_LOG = []

def log_message(log_widget, message):
    """
    Log a message both to the file logger and to the global log list.
    
    Args:
        log_widget: Widget or object to update with the message (can be None)
        message (str): Message to log
        
    Returns:
        str: The logged message with timestamp
    """
    # Create timestamped message
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"{timestamp} - {message}"
    
    # Log to file
    logger.info(message)
    
    # Add to global log
    global GLOBAL_LOG
    GLOBAL_LOG.append(log_entry)
    
    # Keep only the last 1000 log entries
    if len(GLOBAL_LOG) > 1000:
        GLOBAL_LOG = GLOBAL_LOG[-1000:]
    
    return log_entry

def clear_log():
    """
    Clear the global log.
    """
    global GLOBAL_LOG
    GLOBAL_LOG = []
    logger.info("Log cleared")

def get_log():
    """
    Get the current log content.
    
    Returns:
        list: The global log entries.
    """
    global GLOBAL_LOG
    return GLOBAL_LOG