#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medical Spytool - Browser Launcher
This script launches a web browser pointing to the Medical Spytool application.
"""

import os
import sys
import time
import webbrowser
import socket
import logging

def is_port_in_use(port, host='127.0.0.1'):
    """Check if the specified port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def wait_for_server(port, host='127.0.0.1', timeout=30):
    """Wait for the server to start"""
    print(f"Warte auf Server-Start auf {host}:{port}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if is_port_in_use(port, host):
            print(f"Server läuft auf {host}:{port}")
            return True
        time.sleep(1)
    
    print(f"Timeout nach {timeout} Sekunden. Server konnte nicht gestartet werden.")
    return False

def main():
    host = '127.0.0.1'
    port = 5000
    url = f"http://{host}:{port}"
    
    # Check if server is already running
    if is_port_in_use(port, host):
        print(f"Server läuft bereits auf {host}:{port}")
    else:
        print("Server scheint nicht zu laufen. Starte ihn im Hintergrund...")
        
        # Start the server in a separate process
        if sys.platform.startswith('win'):
            os.system('start powershell -NoExit -Command "& {python start_app.py}"')
        else:
            os.system('python start_app.py &')
            
        # Wait for the server to start
        if not wait_for_server(port, host):
            print("Server konnte nicht gestartet werden. Bitte starten Sie ihn manuell.")
            return 1
    
    # Open browser
    print(f"Öffne Browser mit URL: {url}")
    webbrowser.open(url)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
