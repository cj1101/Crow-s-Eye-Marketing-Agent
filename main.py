#!/usr/bin/env python3
"""
Simple entry point for the Crow's Eye API
This ensures proper module loading in Google Cloud App Engine
"""
import sys
import os

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import the FastAPI app
try:
    from crow_eye_api.main import app
    
    # For debugging
    print(f"✅ Successfully imported FastAPI app from crow_eye_api.main")
    print(f"📁 Current directory: {current_dir}")
    print(f"🐍 Python path: {sys.path[:3]}")  # Show first 3 entries
    
except ImportError as e:
    print(f"❌ Failed to import FastAPI app: {e}")
    print(f"📁 Current directory: {current_dir}")
    print(f"🐍 Python path: {sys.path[:3]}")
    raise

# Make app available for gunicorn
application = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 