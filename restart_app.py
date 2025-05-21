#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Restart Medical Spytool Application
This script will try to stop any running Flask server on port 5000
and then start a new one with all fixed configurations.
"""

import os
import sys
import time
import signal
import socket
import subprocess
import platform

def is_port_in_use(port):
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    """Kill the process using the specified port."""
    system = platform.system()
    
    if system == 'Windows':
        try:
            # Find PID on Windows
            netstat = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
            lines = netstat.split('\n')
            for line in lines:
                if 'LISTENING' in line:
                    pid = line.strip().split()[-1]
                    print(f"Killing process with PID: {pid}")
                    os.system(f"taskkill /F /PID {pid}")
                    return True
        except subprocess.CalledProcessError:
            print(f"No process found using port {port}")
    else:
        # Unix-like systems (Linux, macOS)
        try:
            cmd = f"lsof -i :{port} -t"
            pid = subprocess.check_output(cmd, shell=True).decode().strip()
            if pid:
                print(f"Killing process with PID: {pid}")
                os.kill(int(pid), signal.SIGTERM)
                time.sleep(1)  # Give it a moment to shut down
                return True
        except (subprocess.CalledProcessError, ProcessLookupError):
            print(f"No process found using port {port}")
    
    return False

def main():
    """Main function to restart the application."""
    PORT = 5000
    
    # 1. Check if port is in use and kill process if needed
    if is_port_in_use(PORT):
        print(f"Port {PORT} is in use. Attempting to kill the process...")
        if kill_process_on_port(PORT):
            print("Process successfully terminated")
            time.sleep(2)  # Wait for port to be fully released
        else:
            print("Failed to terminate process. Please do it manually.")
            return 1
    else:
        print(f"Port {PORT} is available")
    
    # 2. Start flask application
    print("Starting Medical Spytool application...")
    
    try:
        # Set environment variables
        env = os.environ.copy()
        env['FLASK_APP'] = 'backend.app:create_app()'
        env['FLASK_ENV'] = 'development'
        env['FLASK_DEBUG'] = '1'
        
        # Run the Flask application
        process = subprocess.Popen(
            ['python', 'manage.py', 'run'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Display output for a while to catch startup errors
        print("Application starting. Showing initial output:")
        
        for i in range(20):  # Show first 20 lines or for about 5 seconds
            if process.poll() is not None:
                print("Process terminated unexpectedly")
                return 1
                
            output = process.stdout.readline()
            if output:
                print(output.strip())
                
                # Check if we see the "Running on" message
                if "Running on" in output:
                    print("\nApplication started successfully! Access it at http://127.0.0.1:5000")
                    break
            
            time.sleep(0.25)
        
        # Now detach and let it run
        print("\nApplication is now running in the background.")
        return 0
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
