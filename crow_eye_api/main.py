import os 
import sys
import uvicorn 
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Create minimal FastAPI app first
app = FastAPI(
    title="Crow's Eye Marketing Platform API",
    description="AI-powered social media content creation and automation platform",
    version="5.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic health check endpoint
@app.get("/health") 
def health(): 
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "port": os.environ.get("PORT", "8000")
    } 

@app.get("/") 
def read_root(): 
    return {
        "message": "Crow's Eye Marketing Platform API", 
        "version": "5.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "gallery": "/api/gallery",
            "test": "/api/test"
        }
    } 

@app.get("/api/test")
def test_endpoint():
    return {
        "message": "API is working", 
        "timestamp": datetime.now().isoformat(),
        "status": "success"
    }

@app.get("/api/test-array")
def test_array_endpoint():
    """Test endpoint that returns an array structure like the frontend expects."""
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

@app.get("/api/gallery-test")
def gallery_test_endpoint():
    """Test endpoint that returns gallery-like data structure."""
    return {
        "galleries": [
            {
                "id": "gallery-1",
                "name": "Test Gallery 1",
                "description": "A test gallery",
                "media_count": 5,
                "media_paths": ["/test/path1.jpg", "/test/path2.jpg"],
                "caption": "Test caption",
                "tags": ["test", "sample"],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "thumbnail_url": None
            },
            {
                "id": "gallery-2", 
                "name": "Test Gallery 2",
                "description": "Another test gallery",
                "media_count": 3,
                "media_paths": ["/test/path3.jpg"],
                "caption": "Another test caption",
                "tags": ["test", "demo"],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "thumbnail_url": None
            }
        ],
        "total": 2,
        "query": None,
        "filters": {"limit": 20, "offset": 0},
        "success": True,
        "message": None
    }

# Try to import routers - fail gracefully if they don't work
ROUTERS_LOADED = False
try:
    # Add src to path for imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    
    from .routers import gallery
    
    # Include gallery router with safe error handling
    app.include_router(gallery.router, prefix="/api/gallery", tags=["gallery"])
    ROUTERS_LOADED = True
    
except ImportError as e:
    print(f"Warning: Could not import gallery router: {e}")
    
    # Fallback gallery endpoint
    @app.get("/api/gallery")
    def fallback_gallery():
        return {
            "galleries": [],
            "total": 0,
            "query": None,
            "filters": {"limit": 20, "offset": 0},
            "success": False,
            "message": "Gallery functionality temporarily unavailable"
        }

# Add router status to root endpoint
@app.get("/status")
def get_status():
    return {
        "api_status": "running",
        "routers_loaded": ROUTERS_LOADED,
        "timestamp": datetime.now().isoformat(),
        "environment": "cloud_run" if os.environ.get("K_SERVICE") else "local"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting Crow's Eye API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port) 
