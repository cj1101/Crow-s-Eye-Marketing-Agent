#!/usr/bin/env python3
"""
Main entry point for Google Cloud App Engine
Imports and exports the FastAPI application
"""

# Import the FastAPI app
from crow_eye_api.main import app

# Export for App Engine
application = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 