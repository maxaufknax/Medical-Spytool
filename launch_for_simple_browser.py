"""
Medical Spytool Simple Browser Launcher
"""

import os
import sys
import webbrowser
import subprocess
import time
import http.client
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FLASK_SCRIPT = os.path.join(BASE_DIR, "manage.py")

def is_server_running(host='127.0.0.1', port=5000):
    """Check if server is running on specified host and port"""
    try:
        conn = http.client.HTTPConnection(host, port, timeout=1)
        conn.request("HEAD", "/")
        return True
    except Exception:
        return False

def main():
    """Main function"""
    logging.info("Starting Medical Spytool for demonstration...")
    
    # Check if server is already running
    if is_server_running():
        logging.info("Server is already running")
    else:
        logging.info("Starting server (this will take a moment)...")
        
        # Start Flask using Python subprocess
        cmd = [sys.executable, FLASK_SCRIPT, "run"]
        
        # Start the process in a way that doesn't block this script
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        
        # Wait for server to start
        max_attempts = 30
        for i in range(max_attempts):
            if is_server_running():
                logging.info("Server started successfully!")
                break
            logging.info(f"Waiting for server to start... ({i+1}/{max_attempts})")
            time.sleep(1)
        else:
            logging.error("Server failed to start within the timeout period")
            return 1
    
    # Server is running, now open in Simple Browser
    url = "http://127.0.0.1:5000"
    logging.info(f"Opening URL in Simple Browser: {url}")
    
    return url

if __name__ == "__main__":
    result = main()
    print(f"BROWSER_URL:{result}")
