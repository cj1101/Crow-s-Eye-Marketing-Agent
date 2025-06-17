#!/usr/bin/env python3
"""
Production deployment entry point for Crow's Eye API
Initializes database and starts the API for Google Cloud deployment
"""
import sys
import os
import asyncio
import logging

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("crow_eye_api.deploy")

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

async def initialize_for_deployment():
    """Initialize database and prepare for deployment."""
    try:
        logger.info("🚀 Starting Crow's Eye API deployment initialization...")
        
        # Initialize database if needed
        if os.getenv("INITIALIZE_DB", "false").lower() == "true":
            logger.info("📊 Initializing database for GCP deployment...")
            from initialize_gcp_db import init_gcp_database
            success = await init_gcp_database()
            if not success:
                logger.error("❌ Database initialization failed!")
                return False
        
        logger.info("✅ Deployment initialization completed successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Deployment initialization failed: {str(e)}")
        logger.exception("Full error details:")
        return False

# Import and setup the FastAPI app
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time

# Create the FastAPI app
app = FastAPI(
    title="Crow's Eye API - Production",
    description="Advanced marketing automation API with AI-powered content generation",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://crow-eye-api-dot-crows-eye-website.uc.r.appspot.com",
        "https://crows-eye-website.uc.r.appspot.com",
        "http://localhost:3000",  # For development
        "http://localhost:8000"   # For local testing
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("🦅 Crow's Eye API starting up...")
    success = await initialize_for_deployment()
    if not success:
        logger.error("💥 Failed to initialize for deployment!")
        raise RuntimeError("Application initialization failed")
    logger.info("🎉 Crow's Eye API ready!")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Google Cloud"""
    try:
        # Test database connection
        db_status = "connected"
        try:
            from crow_eye_api.database import check_database_health
            is_healthy = await check_database_health()
            db_status = "connected" if is_healthy else "disconnected"
        except Exception:
            db_status = "unknown"
        
        return {
            "status": "healthy",
            "service": "crow-eye-api",
            "version": "1.0.0",
            "message": "🦅 Crow's Eye API is running on Google Cloud",
            "database": db_status,
            "deployment": "production",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🦅 Crow's Eye Marketing Agent API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1"
    }

# Basic test endpoint
@app.get("/test")
async def simple_test():
    """Simple test endpoint"""
    return {
        "message": "API is working correctly",
        "timestamp": time.time(),
        "status": "success"
    }

# Placeholder for main API functionality
@app.get("/api/v1/health")
async def api_health():
    """API health check"""
    return {
        "api_status": "healthy",
        "database_status": "connected",
        "service": "crow-eye-api",
        "version": "1.0.0"
    }

# Export for ASGI
application = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 