#!/usr/bin/env python3
"""
GCP Database Initialization Script
Creates the database file and tables if they don't exist.
"""

import os
import asyncio
import logging
from pathlib import Path
import sqlite3
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
        database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:////tmp/crow_eye_production.db")
        logger.info(f"Initializing database: {database_url}")
        
        # Extract SQLite file path
        if "sqlite" in database_url:
            # Remove the sqlite+aiosqlite:// or sqlite:// prefix
            db_path = database_url.split("://")[-1]
            
            # Create directory if it doesn't exist
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Created directory: {db_dir}")
            
            # Check if database file exists
            if not os.path.exists(db_path):
                logger.info(f"Database file doesn't exist, creating: {db_path}")
                
                # Create empty database file
                Path(db_path).touch()
                
                # Test basic SQLite connection
                conn = sqlite3.connect(db_path)
                conn.execute("SELECT 1")
                conn.close()
                logger.info("✅ SQLite database file created successfully")
            else:
                logger.info(f"✅ Database file already exists: {db_path}")
        
        # Now initialize tables using SQLAlchemy
        logger.info("Initializing database tables...")
        
        # Import models to register them with Base
        from crow_eye_api.models import (
            User, MediaItem, Gallery, GooglePhotosConnection,
            Post, Schedule, Template, Analytics, AnalyticsSummary
        )
        from crow_eye_api.database import Base, engine, init_database
        
        # Initialize database and create tables
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