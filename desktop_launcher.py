#!/usr/bin/env python3
"""
Desktop Launcher for Medical Spytool

This module provides a unified desktop application that manages the Flask server
and provides a native desktop experience for Windows users.
"""

import sys
import os
import threading
import time
import webbrowser
import socket
import subprocess
import logging
from datetime import datetime
import json
import tempfile
import atexit

# GUI imports - with fallback for headless environments
HAS_GUI = False
try:
    # Check if we have a display (not in headless environment)
    if os.name == 'nt' or os.environ.get('DISPLAY'):
        import tkinter as tk
        from tkinter import ttk, messagebox, PhotoImage
        HAS_GUI = True
        
        # Try system tray imports
        try:
            import pystray
            from pystray import MenuItem as item
            from PIL import Image, ImageDraw
            HAS_SYSTRAY = True
        except ImportError:
            HAS_SYSTRAY = False
    else:
        HAS_SYSTRAY = False
except ImportError:
    HAS_SYSTRAY = False

# Flask app import
from main import app, ensure_directories, app_config, setup_logging, log_message

class MedicalSpytoolDesktop:
    """Main desktop application class."""
    
    def __init__(self):
        """Initialize the desktop application."""
        self.flask_thread = None
        self.flask_process = None
        self.server_running = False
        self.port = 5000
        self.host = '127.0.0.1'
        self.icon = None
        self.root = None
        
        # Setup logging
        setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Ensure directories exist
        ensure_directories(app_config)
        
        # Check if we can use GUI
        if not HAS_GUI:
            self.logger.info("GUI components not available, running in web-only mode")
            self.start_flask_server()
            return
            
        # Initialize GUI
        self.init_gui()
        
    def init_gui(self):
        """Initialize the GUI components."""
        self.root = tk.Tk()
        self.root.title("Medical Spytool Desktop")
        self.root.geometry("800x600")
        
        # Set window icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            self.logger.warning(f"Could not set window icon: {e}")
            
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Medical Spytool Desktop", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Server status frame
        status_frame = ttk.LabelFrame(main_frame, text="Server Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_var = tk.StringVar()
        self.status_var.set("Server stopped")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
        self.status_indicator = tk.Canvas(status_frame, width=20, height=20)
        self.status_indicator.pack(side=tk.RIGHT)
        self.update_status_indicator(False)
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_btn = ttk.Button(control_frame, text="Start Server", 
                                   command=self.start_server)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(control_frame, text="Stop Server", 
                                  command=self.stop_server, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.open_browser_btn = ttk.Button(control_frame, text="Open in Browser", 
                                          command=self.open_browser, state=tk.DISABLED)
        self.open_browser_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Port setting
        port_frame = ttk.Frame(settings_frame)
        port_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(port_frame, text="Port:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value=str(self.port))
        port_entry = ttk.Entry(port_frame, textvariable=self.port_var, width=10)
        port_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Auto-start option
        self.autostart_var = tk.BooleanVar(value=True)
        autostart_cb = ttk.Checkbutton(settings_frame, text="Auto-start server", 
                                      variable=self.autostart_var)
        autostart_cb.pack(anchor=tk.W)
        
        # Auto-open browser option
        self.auto_browser_var = tk.BooleanVar(value=True)
        auto_browser_cb = ttk.Checkbutton(settings_frame, text="Auto-open browser", 
                                         variable=self.auto_browser_var)
        auto_browser_cb.pack(anchor=tk.W)
        
        # System tray option (only if available)
        if HAS_SYSTRAY:
            self.minimize_to_tray_var = tk.BooleanVar(value=True)
            tray_cb = ttk.Checkbutton(settings_frame, text="Minimize to system tray", 
                                     variable=self.minimize_to_tray_var)
            tray_cb.pack(anchor=tk.W)
        else:
            self.minimize_to_tray_var = tk.BooleanVar(value=False)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Application Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log text widget with scrollbar
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_text_frame, height=10, state=tk.DISABLED)
        log_scrollbar = ttk.Scrollbar(log_text_frame, orient=tk.VERTICAL, 
                                     command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Clear log button
        ttk.Button(log_frame, text="Clear Log", 
                  command=self.clear_log).pack(anchor=tk.E, pady=(5, 0))
        
        # Configure window close behavior
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        # Auto-start if enabled
        if self.autostart_var.get():
            self.root.after(1000, self.start_server)  # Start after 1 second
            
        self.log_message("Medical Spytool Desktop initialized")
        
    def update_status_indicator(self, running):
        """Update the status indicator color."""
        if hasattr(self, 'status_indicator'):
            self.status_indicator.delete("all")
            color = "green" if running else "red"
            self.status_indicator.create_oval(2, 2, 18, 18, fill=color, outline=color)
        
    def log_message(self, message):
        """Add a message to the log display."""
        if hasattr(self, 'log_text'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}\n"
            
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, formatted_message)
            self.log_text.config(state=tk.DISABLED)
            self.log_text.see(tk.END)
            
        # Also log to file
        self.logger.info(message)
        
    def clear_log(self):
        """Clear the log display."""
        if hasattr(self, 'log_text'):
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)
            
    def find_free_port(self, start_port=5000):
        """Find a free port starting from the given port."""
        port = start_port
        while port < 65535:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host, port))
                    return port
            except OSError:
                port += 1
        raise RuntimeError("No free ports available")
        
    def start_server(self):
        """Start the Flask server."""
        if self.server_running:
            self.log_message("Server is already running")
            return
            
        try:
            # Get port from settings
            try:
                requested_port = int(self.port_var.get()) if hasattr(self, 'port_var') else 5000
            except (ValueError, AttributeError):
                requested_port = 5000
                
            # Find free port
            self.port = self.find_free_port(requested_port)
            if hasattr(self, 'port_var') and self.port != requested_port:
                self.port_var.set(str(self.port))
                self.log_message(f"Port {requested_port} was busy, using port {self.port}")
                
            # Start Flask server in thread
            self.flask_thread = threading.Thread(target=self._run_flask_server, daemon=True)
            self.flask_thread.start()
            
            # Wait a moment for server to start
            if self.root:
                self.root.after(2000, self._check_server_started)
            else:
                time.sleep(2)
                self._check_server_started()
                
            self.log_message(f"Starting server on http://{self.host}:{self.port}")
            
        except Exception as e:
            self.log_message(f"Error starting server: {e}")
            self.logger.error(f"Server start error: {e}", exc_info=True)
            
    def _run_flask_server(self):
        """Run the Flask server in a separate thread."""
        try:
            app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
        except Exception as e:
            self.log_message(f"Flask server error: {e}")
            self.logger.error(f"Flask server error: {e}", exc_info=True)
            
    def _check_server_started(self):
        """Check if the server has started successfully."""
        try:
            import requests
            response = requests.get(f"http://{self.host}:{self.port}", timeout=5)
            if response.status_code == 200:
                self.server_running = True
                if hasattr(self, 'status_var'):
                    self.status_var.set(f"Server running on http://{self.host}:{self.port}")
                self.update_status_indicator(True)
                
                if hasattr(self, 'start_btn'):
                    self.start_btn.config(state=tk.DISABLED)
                    self.stop_btn.config(state=tk.NORMAL)
                    self.open_browser_btn.config(state=tk.NORMAL)
                
                self.log_message("Server started successfully")
                
                # Auto-open browser if enabled
                if hasattr(self, 'auto_browser_var') and self.auto_browser_var.get():
                    self.open_browser()
                    
                # Setup system tray
                if HAS_SYSTRAY and hasattr(self, 'minimize_to_tray_var') and self.minimize_to_tray_var.get():
                    self.setup_system_tray()
                    
        except Exception as e:
            self.log_message(f"Server failed to start: {e}")
            self.server_running = False
            
    def stop_server(self):
        """Stop the Flask server."""
        if not self.server_running:
            self.log_message("Server is not running")
            return
            
        try:
            # Send shutdown request to server
            import requests
            requests.post(f"http://{self.host}:{self.port}/shutdown", timeout=5)
        except:
            pass
            
        self.server_running = False
        if hasattr(self, 'status_var'):
            self.status_var.set("Server stopped")
        self.update_status_indicator(False)
        
        if hasattr(self, 'start_btn'):
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.open_browser_btn.config(state=tk.DISABLED)
        
        self.log_message("Server stopped")
        
    def open_browser(self):
        """Open the application in the default browser."""
        if self.server_running:
            url = f"http://{self.host}:{self.port}"
            webbrowser.open(url)
            self.log_message(f"Opened browser: {url}")
        else:
            self.log_message("Cannot open browser: server is not running")
            
    def setup_system_tray(self):
        """Setup system tray icon."""
        if not HAS_SYSTRAY:
            return
            
        try:
            # Create a simple icon
            image = Image.new('RGB', (64, 64), color='blue')
            draw = ImageDraw.Draw(image)
            draw.rectangle([16, 16, 48, 48], fill='white')
            draw.text((20, 25), "MS", fill='blue')
            
            # Create menu
            menu = pystray.Menu(
                item('Open Medical Spytool', self.show_window),
                item('Open in Browser', self.open_browser),
                pystray.Menu.SEPARATOR,
                item('Quit', self.quit_application)
            )
            
            # Create and run icon
            self.icon = pystray.Icon("Medical Spytool", image, menu=menu)
            threading.Thread(target=self.icon.run, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"Could not create system tray icon: {e}")
            
    def show_window(self, icon=None, item=None):
        """Show the main window."""
        if self.root:
            self.root.deiconify()
            self.root.lift()
            
    def hide_window(self):
        """Hide the main window to system tray."""
        if self.root and hasattr(self, 'minimize_to_tray_var') and self.minimize_to_tray_var.get() and self.icon:
            self.root.withdraw()
            
    def on_window_close(self):
        """Handle window close event."""
        if hasattr(self, 'minimize_to_tray_var') and self.minimize_to_tray_var.get() and self.icon:
            self.hide_window()
        else:
            self.quit_application()
            
    def quit_application(self, icon=None, item=None):
        """Quit the application completely."""
        self.log_message("Shutting down application...")
        
        # Stop Flask server
        if self.server_running:
            self.stop_server()
            
        # Stop system tray icon
        if self.icon:
            self.icon.stop()
            
        # Close GUI
        if self.root:
            self.root.quit()
            
        sys.exit(0)
        
    def run(self):
        """Run the desktop application."""
        if self.root:
            self.root.mainloop()
        else:
            # Fallback to web-only mode
            self.start_flask_server()
            
    def start_flask_server(self):
        """Start Flask server without GUI."""
        try:
            self.port = self.find_free_port()
            print(f"Starting Medical Spytool on http://{self.host}:{self.port}")
            print("Opening browser...")
            webbrowser.open(f'http://{self.host}:{self.port}/')
            app.run(host=self.host, port=self.port, debug=False)
        except Exception as e:
            print(f"Error starting server: {e}")
            sys.exit(1)


def main():
    """Main entry point for the desktop application."""
    # Register cleanup function
    atexit.register(lambda: print("Medical Spytool Desktop shutting down..."))
    
    try:
        # Create and run desktop app
        desktop_app = MedicalSpytoolDesktop()
        desktop_app.run()
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()