"""
Main FastAPI application for Crow's Eye Marketing Platform.
"""

import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from .routers import auth, media, gallery, stories, highlights, audio, analytics, admin
from .dependencies import get_current_user

# Try to import database, but don't fail if not available
try:
    from .database import db_manager
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("⚠️  Database module not available - running in fallback mode")

try:
    from src.models.user import user_manager
except ImportError:
    print("⚠️  User manager not available - using minimal user handling")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting Crow's Eye API...")
    
    if DATABASE_AVAILABLE:
        try:
            await db_manager.connect()
            print("✅ Database connection established")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("⚠️  Running in fallback mode without database")
    else:
        print("⚠️  Running without database - limited functionality")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Crow's Eye API...")
    if DATABASE_AVAILABLE:
        try:
            await db_manager.disconnect()
            print("✅ Database connection closed")
        except Exception as e:
            print(f"❌ Database disconnect error: {e}")


# Create FastAPI app
app = FastAPI(
    title="Crow's Eye Marketing Platform API",
    description="REST API for the Crow's Eye marketing automation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.crowseye.tech",
        "https://crowseye.tech",
        "https://*.firebaseapp.com",
        "https://*.web.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(media.router, prefix="/media", tags=["Media"])
app.include_router(gallery.router, prefix="/gallery", tags=["Gallery"])
app.include_router(stories.router, prefix="/stories", tags=["Stories"])
app.include_router(highlights.router, prefix="/highlights", tags=["Highlights"])
app.include_router(audio.router, prefix="/audio", tags=["Audio"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


@app.get("/")
async def root():
    """Root endpoint."""
    db_status = "connected" if DATABASE_AVAILABLE and hasattr(db_manager, 'pool') and db_manager.pool else "disconnected"
    return {
        "message": "Crow's Eye Marketing Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "database": db_status,
        "status": "ready"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_status = "connected" if DATABASE_AVAILABLE and hasattr(db_manager, 'pool') and db_manager.pool else "disconnected"
    return {
        "status": "healthy", 
        "timestamp": "2024-01-01T00:00:00Z",
        "database": db_status,
        "mode": "full" if DATABASE_AVAILABLE else "fallback"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "crow_eye_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 