#!/usr/bin/env python3

"""
Main runner for the YouTube Recommendation Engine application.
This script launches the Streamlit application on the specified port.
"""

import os
import subprocess
import sys

def main():
    # Set the port for the Streamlit application
    port = 8501
    
    # Command to run the Streamlit application
    cmd = [
        "streamlit", "run", "streamlit_app.py",
        "--server.port", str(port),
        "--server.address", "0.0.0.0",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false"
    ]
    
    print(f"Starting YouTube Recommender Engine on port {port}...")
    try:
        # Run the Streamlit application
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nShutting down the YouTube Recommender Engine...")
    except Exception as e:
        print(f"Error running the Streamlit application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()