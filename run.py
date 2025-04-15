"""
Run this file to start the YouTube Recommendation Engine Streamlit app
"""
import os
import time
import sys

def main():
    print("Starting YouTube Recommendation Engine...")
    
    # Add a delay to make sure any previous processes have been terminated
    time.sleep(1)
    
    # Run Streamlit directly to avoid terminal questions
    os.system("streamlit run app.py")
    
    # Keep the process alive
    while True:
        time.sleep(10)

if __name__ == "__main__":
    main()