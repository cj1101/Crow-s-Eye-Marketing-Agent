#!/usr/bin/env python3
"""
Google App Engine entry point for Crow's Eye API
"""

import sys
import os

# Add the current directory and crow_eye_api directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.join(current_dir, 'crow_eye_api')
sys.path.insert(0, current_dir)
sys.path.insert(0, api_dir)

# Import the FastAPI app from the crow_eye_api module
try:
    # First try direct import from crow_eye_api directory
    os.chdir(api_dir)
    import main as api_main
    app = api_main.app
    
    # Health check endpoint specifically for Google Cloud
    @app.get("/")
    async def root():
        """Root endpoint for Google App Engine"""
        return {
            "message": "🦅 Crow's Eye API is running on Google Cloud",
            "status": "healthy",
            "service": "crow-eye-api",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "api_health": "/api/v1/health", 
                "docs": "/docs",
                "redoc": "/redoc"
            }
        }
    
    # Export the app for Google App Engine
    application = app
    
except Exception as e:
    # Fallback if there are import issues
    from fastapi import FastAPI
    
    app = FastAPI(title="Crow's Eye API - Fallback Mode")
    
    @app.get("/")
    async def fallback_root():
        return {
            "message": "🦅 Crow's Eye API - Fallback Mode",
            "error": f"Import failed: {str(e)}",
            "status": "error",
            "debug_info": {
                "current_dir": current_dir,
                "api_dir": api_dir,
                "python_path": sys.path[:3]
            }
        }
    
    @app.get("/health")
    async def fallback_health():
        return {
            "status": "error",
            "message": "Import failed - running in fallback mode",
            "error": str(e)
        }
    
    application = app

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 