#!/usr/bin/env python3
"""
GCP Database Initialization Script
Creates the database tables for PostgreSQL Cloud SQL if they don't exist.
"""

import os
import asyncio
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def init_gcp_database():
    """Initialize database for GCP deployment."""
    try:
        # Get database URL from environment
        database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:crowseye2024@/crowseye_db?host=/cloudsql/crows-eye-website:us-central1:crowseye-postgres")
        logger.info(f"Initializing database: {database_url.split('@')[0]}@[REDACTED]")
        
        # Import models to register them with Base
        from crow_eye_api.models import (
            User, MediaItem, Gallery, GooglePhotosConnection,
            Post, FinishedContent, Schedule, Template, Analytics, AnalyticsSummary
        )
        from crow_eye_api.database import Base, engine, init_database
        
        # Test database connection first
        logger.info("Testing database connection...")
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            logger.info(f"✅ Database connection successful: {row[0]}")
        
        # Initialize database and create tables
        logger.info("Creating database tables...")
        await init_database()
        logger.info("✅ Database tables initialized successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        logger.exception("Full error details:")
        return False

def sync_init_gcp_database():
    """Synchronous wrapper for database initialization."""
    return asyncio.run(init_gcp_database())

if __name__ == "__main__":
    success = sync_init_gcp_database()
    if success:
        logger.info("🎉 GCP database initialization completed successfully!")
    else:
        logger.error("💥 GCP database initialization failed!")
        exit(1) 