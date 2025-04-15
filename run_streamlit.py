#!/usr/bin/env python3
import os
import subprocess
import sys

def main():
    """Run the Streamlit application"""
    port = 8501  # Use a different port from the Node.js app (5000)
    
    try:
        # Check if the port is already in use
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            print(f"Port {port} is already in use. Trying another port...")
            port = 8502  # Try an alternative port
    except Exception as e:
        print(f"Error checking port availability: {e}")
    
    # Run Streamlit with the specified port
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(port)]
    
    print(f"Starting Streamlit on port {port}...")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()