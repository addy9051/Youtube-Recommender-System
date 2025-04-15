#!/usr/bin/env python3
"""
This is the main entry point for the Streamlit application.
It makes sure to run on a port that won't conflict with the existing server.
"""
import os
import sys
import subprocess

def main():
    # Define the port for Streamlit (different from the Node.js app on 5000)
    port = 8501
    
    # Run the Streamlit app
    cmd = [
        sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
        "--server.port", str(port),
        "--server.address", "0.0.0.0",  # Bind to all interfaces
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false"
    ]
    
    print(f"Starting YouTube Recommender Streamlit app on port {port}...")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()