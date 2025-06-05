#!/usr/bin/env python3
"""
Crow's Eye Marketing Platform
Main entry point for the application.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from crow_eye_api.main import app

# This is the WSGI application that App Engine will use
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 