"""
Main entry point for the YouTube Recommendation Engine.
This file is used to start the Streamlit application in Replit.
"""
import os
import subprocess
import sys

def main():
    """Start the Streamlit application"""
    print("Starting YouTube Recommendation Engine...")
    
    # Run Streamlit with the app.py file
    os.system('streamlit run app.py --server.port 8501 --server.address 0.0.0.0')

if __name__ == "__main__":
    main()