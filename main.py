#!/usr/bin/env python3
"""
Crow's Eye Marketing Platform
Main entry point for Google Cloud deployment.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from crow_eye_api.main import app
except ImportError as e:
    print(f"Error importing app: {e}")
    print("Current working directory:", os.getcwd())
    print("Python path:", sys.path)
    sys.exit(1)

# This is the WSGI application that Cloud Run will use
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Cloud Run sets this)
    port = int(os.environ.get("PORT", 8080))
    
    print(f"Starting Crow's Eye API on port {port}")
    print(f"Working directory: {os.getcwd()}")
    
    # Start the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    ) 