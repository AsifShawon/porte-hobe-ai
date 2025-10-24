#!/usr/bin/env python3
"""
Start script for the Porte Hobe AI FastAPI server
"""

import sys
import os
import subprocess

def main():
    """Start the FastAPI server"""
    print("🚀 Starting Porte Hobe AI FastAPI server...")
    
    # Change to the server directory
    server_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(server_dir)
    
    try:
        # Run uvicorn with the main app
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--reload-exclude", ".venv"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
