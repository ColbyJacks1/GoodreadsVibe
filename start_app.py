#!/usr/bin/env python3
"""Start script for Book Mirror Plus application."""

import subprocess
import time
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import streamlit
        import fastapi
        import uvicorn
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: poetry install")
        return False

def start_backend():
    """Start the FastAPI backend."""
    print("🚀 Starting FastAPI backend...")
    try:
        # Start backend in background
        backend_process = subprocess.Popen(
            ["poetry", "run", "uvicorn", "app.api:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for backend to start
        time.sleep(3)
        
        # Check if backend is running
        try:
            import requests
            response = requests.get("http://localhost:8000/", timeout=5)
            if response.status_code == 200:
                print("✅ FastAPI backend is running on http://localhost:8000")
                return backend_process
            else:
                print("❌ FastAPI backend failed to start properly")
                return None
        except Exception as e:
            print(f"❌ Cannot connect to FastAPI backend: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting FastAPI backend: {e}")
        return None

def start_frontend():
    """Start the Streamlit frontend."""
    print("🎨 Starting Streamlit frontend...")
    try:
        frontend_process = subprocess.Popen(
            ["poetry", "run", "streamlit", "run", "ui/streamlit_app.py", "--server.port", "8501"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for frontend to start
        time.sleep(3)
        print("✅ Streamlit frontend is starting on http://localhost:8501")
        return frontend_process
        
    except Exception as e:
        print(f"❌ Error starting Streamlit frontend: {e}")
        return None

def main():
    """Main function to start the application."""
    print("📚 Book Mirror Plus - Starting Application")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        print("❌ Failed to start backend. Exiting.")
        sys.exit(1)
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ Failed to start frontend. Exiting.")
        backend_process.terminate()
        sys.exit(1)
    
    print("\n🎉 Application started successfully!")
    print("📊 Backend: http://localhost:8000")
    print("🎨 Frontend: http://localhost:8501")
    print("📖 API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop both services...")
    
    try:
        # Keep both processes running
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process stopped unexpectedly")
                break
                
            if frontend_process.poll() is not None:
                print("❌ Frontend process stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        
        # Terminate processes
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        
        print("✅ Services stopped")

if __name__ == "__main__":
    main() 