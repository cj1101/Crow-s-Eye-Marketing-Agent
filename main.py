#!/usr/bin/env python3
"""
Google App Engine entry point for Crow's Eye API
"""

import sys
import os

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import the FastAPI app from the crow_eye_api module
try:
    from crow_eye_api.main import app
    
    # Health check endpoint specifically for Google Cloud
    @app.get("/")
    async def root():
        """Root endpoint for Google App Engine"""
        return {
            "message": "Crow's Eye API is running on Google Cloud",
            "status": "healthy",
            "service": "crow-eye-api",
            "version": "1.0.0"
        }
    
    # Export the app for Google App Engine
    application = app
    
except ImportError as e:
    # Fallback if there are import issues
    from fastapi import FastAPI
    
    app = FastAPI(title="Crow's Eye API - Fallback")
    
    @app.get("/")
    async def fallback_root():
        return {
            "message": "Crow's Eye API - Import Error",
            "error": str(e),
            "status": "error"
        }
    
    @app.get("/health")
    async def fallback_health():
        return {
            "status": "error",
            "message": "Import failed",
            "error": str(e)
        }
    
    application = app

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 