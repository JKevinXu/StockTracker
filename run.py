#!/usr/bin/env python3
"""
Amazon Stock Tracker - Run Script
This script launches the Amazon Stock Tracker application with proper error handling.
"""

import sys
import os
import socket
import webbrowser
from time import sleep

def check_dependencies():
    """Verify all required dependencies are installed."""
    try:
        import dash
        import dash_bootstrap_components as dbc
        import yfinance
        import pandas
        import plotly
        import numpy
        print("✅ All dependencies installed.")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nPlease install all dependencies with:")
        print("pip install -r requirements.txt\n")
        return False

def get_ip_address():
    """Get the local IP address for network access."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Could not determine IP"

def main():
    """Main entry point for the application."""
    # Check if dependencies are installed
    if not check_dependencies():
        return 1
    
    # Check if config file exists
    if not os.path.exists('config.py'):
        print("❌ config.py file not found!")
        print("Please create config.py with your RSU details.")
        return 1
    
    # Import our app module
    try:
        import app
        import config
    except Exception as e:
        print(f"❌ Error importing application modules: {e}")
        return 1
    
    # Get network information
    hostname = socket.gethostname()
    ip_address = get_ip_address()
    port = config.DEFAULT_PORT
    
    # Display startup information
    print("\n" + "="*60)
    print(f"🚀 Launching Amazon Stock Tracker!")
    print("="*60)
    print(f"📊 Local URL: http://localhost:{port}")
    print(f"🌐 Network URL: http://{ip_address}:{port}")
    print(f"💻 Hostname: {hostname}")
    print("="*60)
    
    # Open browser automatically after delay
    def open_browser():
        sleep(2)  # Short delay to allow server to start
        local_url = f"http://localhost:{port}"
        print(f"\n🔗 Opening {local_url} in your browser...")
        webbrowser.open(local_url)

    # Run in a separate thread to not block the main thread
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Launch the application
    try:
        app.app.run(
            debug=config.DEBUG_MODE, 
            host=config.HOST, 
            port=port
        )
        return 0
    except Exception as e:
        print(f"❌ Error starting application server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 