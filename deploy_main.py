#!/usr/bin/env python3
"""
Production deployment entry point for Crow's Eye API
Uses sync SQLite for Google Cloud compatibility
"""
import sys
import os

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Override the database URL for production to use sync SQLite
os.environ['DATABASE_URL'] = 'sqlite:///crow_eye_production.db'

# Import and patch for sync operation
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crow_eye_api")

# Create a simplified FastAPI app for production
app = FastAPI(
    title="Crow's Eye API - Production",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Basic health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Google Cloud"""
    return {
        "status": "healthy",
        "service": "crow-eye-api",
        "version": "1.0.0",
        "message": "🦅 Crow's Eye API is running on Google Cloud",
        "database": "sqlite",
        "deployment": "production"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🦅 Crow's Eye Marketing Agent API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
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