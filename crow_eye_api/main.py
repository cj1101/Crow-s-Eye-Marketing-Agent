import os 
import sys
import uvicorn 
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Dict, List, Optional

# Create FastAPI app with proper metadata
app = FastAPI(
    title="Crow's Eye Marketing Platform API",
    description="AI-powered social media content creation and automation platform",
    version="5.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global state for tracking service status
SERVICE_STATUS = {
    "api_status": "running",
    "routers_loaded": False,
    "database_connected": False,
    "services_initialized": False
}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "port": os.environ.get("PORT", "8080"),
        "environment": "production" if os.environ.get("K_SERVICE") else "development",
        "services": SERVICE_STATUS
    }

# Root endpoint with API info
@app.get("/")
async def read_root():
    """API root endpoint with service information."""
    return {
        "name": "Crow's Eye Marketing Platform API", 
        "version": "5.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "documentation": "/docs",
        "health_check": "/health",
        "endpoints": {
            "auth": "/api/auth",
            "gallery": "/api/gallery", 
            "media": "/api/media",
            "analytics": "/api/analytics",
            "test": "/api/test"
        }
    }

# Basic test endpoints
@app.get("/api/test")
async def test_endpoint():
    """Basic API test endpoint."""
    return {
        "message": "API is working", 
        "timestamp": datetime.now().isoformat(),
        "status": "success"
    }

@app.get("/api/test-array")
async def test_array_endpoint():
    """Test endpoint that returns proper array structure."""
    return {
        "data": [
            {"id": "test1", "name": "Test Item 1", "description": "First test item"},
            {"id": "test2", "name": "Test Item 2", "description": "Second test item"},
            {"id": "test3", "name": "Test Item 3", "description": "Third test item"}
        ],
        "total": 3,
        "success": True,
        "message": "Test data retrieved successfully"
    }

# Status endpoint
@app.get("/api/status")
async def get_api_status():
    """Get detailed API status information."""
    return {
        "api_status": "running",
        "routers_loaded": SERVICE_STATUS["routers_loaded"],
        "database_connected": SERVICE_STATUS["database_connected"],
        "services_initialized": SERVICE_STATUS["services_initialized"],
        "timestamp": datetime.now().isoformat(),
        "environment": "production" if os.environ.get("K_SERVICE") else "development",
        "version": "5.0.0"
    }

# Try to import and include routers with graceful error handling
try:
    # Add src to path for imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    
    from .routers import gallery, media
    from .dependencies import get_current_user
    
    # Include routers
    app.include_router(gallery.router, prefix="/api/gallery", tags=["gallery"])
    app.include_router(media.router, prefix="/api/media", tags=["media"])
    # Also include media router without /api prefix for direct access
    app.include_router(media.router, prefix="/media", tags=["media-direct"])
    SERVICE_STATUS["routers_loaded"] = True
    
except ImportError as e:
    print(f"Warning: Could not import routers: {e}")
    
    # Fallback gallery endpoint
    @app.get("/api/gallery")
    async def fallback_gallery():
        """Fallback gallery endpoint when router is not available."""
        return {
            "galleries": [],
            "total": 0,
            "query": None,
            "filters": {"limit": 20, "offset": 0},
            "success": False,
            "message": "Gallery functionality temporarily unavailable - router not loaded"
        }
    
    # Fallback media endpoint - THIS IS THE KEY FIX
    @app.get("/api/media")
    @app.get("/media")  # Also handle the route without /api prefix
    async def fallback_media():
        """Fallback media endpoint that returns proper array structure."""
        return []  # Return empty array instead of object to prevent map() errors

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": f"Endpoint {request.url.path} not found"
            },
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred"
            },
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting Crow's Eye API on port {port}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🌍 Environment: {'Production' if os.environ.get('K_SERVICE') else 'Development'}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    ) 
