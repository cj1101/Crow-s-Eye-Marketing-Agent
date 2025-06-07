import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Create FastAPI app
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

# Import routers
try:
    from crow_eye_api.routers import (
        highlights,
        media,
        gallery,
        analytics,
        auth,
        stories,
        audio,
        admin
    )

    # Include all routers
    app.include_router(highlights.router, prefix="/api/highlights", tags=["highlights"])
    app.include_router(media.router, prefix="/api/media", tags=["media"])
    app.include_router(gallery.router, prefix="/api/gallery", tags=["gallery"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
    app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
    app.include_router(stories.router, prefix="/api/stories", tags=["stories"])
    app.include_router(audio.router, prefix="/api/audio", tags=["audio"])
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

    ROUTERS_LOADED = True
    print("✅ All routers loaded successfully!")
except ImportError as e:
    print(f"❌ Warning: Could not import routers: {e}")
    print("🔍 Attempting individual router imports...")
    ROUTERS_LOADED = False
    
    # Try importing routers individually to see which ones fail
    router_modules = ['highlights', 'media', 'gallery', 'analytics', 'auth', 'stories', 'audio', 'admin']
    successful_routers = []
    
    for router_name in router_modules:
        try:
            router_module = __import__(f'crow_eye_api.routers.{router_name}', fromlist=[router_name])
            router = getattr(router_module, 'router')
            app.include_router(router, prefix=f"/api/{router_name}", tags=[router_name])
            successful_routers.append(router_name)
            print(f"✅ {router_name} router loaded successfully")
        except Exception as router_error:
            print(f"❌ Failed to load {router_name} router: {router_error}")
    
    if successful_routers:
        ROUTERS_LOADED = True
        print(f"🎉 Successfully loaded {len(successful_routers)} routers: {', '.join(successful_routers)}")
    else:
        print("❌ No routers could be loaded")
except Exception as e:
    print(f"❌ Unexpected error loading routers: {e}")
    ROUTERS_LOADED = False

@app.get("/")
def read_root():
    return {
        "message": "Crow's Eye Marketing Platform API",
        "version": "5.0.0",
        "status": "running",
        "routers_loaded": ROUTERS_LOADED,
        "features": [
            "Long-form highlight generation",
            "AI-powered video analysis",
            "Cost-optimized processing",
            "Media gallery management",
            "AI tagging and search",
            "Caption generation",
            "Analytics and insights",
            "Scheduling and automation",
            "Image and video editing",
            "Story creation",
            "Audio processing",
            "Multi-platform posting"
        ],
        "endpoints": {
            "highlights": "/api/highlights",
            "media": "/api/media",
            "gallery": "/api/gallery",
            "analytics": "/api/analytics",
            "auth": "/api/auth",
            "stories": "/api/stories",
            "audio": "/api/audio",
            "admin": "/api/admin"
        }
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "port": os.environ.get("PORT", "8000"),
        "routers_loaded": ROUTERS_LOADED
    }

@app.get("/api/test")
def test_endpoint():
    return {
        "message": "API is working",
        "timestamp": "2025-01-05T16:00:00Z",
        "routers_loaded": ROUTERS_LOADED
    }

@app.get("/api/capabilities")
def get_capabilities():
    """Get detailed API capabilities and feature list."""
    capabilities = {
        "media_processing": {
            "image_editing": True,
            "video_editing": True,
            "ai_tagging": True,
            "thumbnail_generation": True,
            "format_conversion": True
        },
        "content_creation": {
            "highlight_reels": True,
            "story_creation": True,
            "caption_generation": True,
            "automated_posting": True
        },
        "gallery_management": {
            "smart_search": True,
            "ai_organization": True,
            "bulk_operations": True,
            "custom_galleries": True
        },
        "analytics": {
            "engagement_tracking": True,
            "performance_insights": True,
            "cost_optimization": True,
            "trend_analysis": True
        },
        "integrations": {
            "instagram": True,
            "facebook": False,  # Meta integration disabled
            "twitter": False,
            "tiktok": False
        }
    }

    return {
        "capabilities": capabilities,
        "status": "operational",
        "version": "5.0.0"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 