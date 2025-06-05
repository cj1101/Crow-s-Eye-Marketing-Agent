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
from src.models.user import user_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting Crow's Eye API...")
    yield
    # Shutdown
    print("🛑 Shutting down Crow's Eye API...")


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
        "https://crowseye.tech"
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
    return {
        "message": "Crow's Eye Marketing Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


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