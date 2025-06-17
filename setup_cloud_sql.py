#!/usr/bin/env python3
"""
Cloud SQL PostgreSQL Setup Script
Alternative to SQLite for production deployments requiring scalability
"""

import os
import asyncio
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from google.cloud.sql.connector import Connector, IPTypes
import asyncpg

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CloudSQLSetup:
    """Setup and manage Cloud SQL PostgreSQL connections."""
    
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.region = os.getenv("CLOUD_SQL_REGION", "us-central1")
        self.instance_name = os.getenv("CLOUD_SQL_INSTANCE", "crow-eye-db")
        self.database_name = os.getenv("POSTGRES_DB", "crow_eye_production")
        self.username = os.getenv("POSTGRES_USER", "crow_eye_user")
        self.password = os.getenv("POSTGRES_PASSWORD")
        
        if not all([self.project_id, self.password]):
            raise ValueError("Missing required environment variables: GOOGLE_CLOUD_PROJECT, POSTGRES_PASSWORD")
        
        self.connection_name = f"{self.project_id}:{self.region}:{self.instance_name}"
        
    async def create_connection_pool(self):
        """Create async connection pool for Cloud SQL."""
        try:
            # Initialize Connector
            connector = Connector()
            
            # Create connection function
            async def getconn() -> asyncpg.Connection:
                conn = await connector.connect_async(
                    self.connection_name,
                    "asyncpg",
                    user=self.username,
                    password=self.password,
                    db=self.database_name,
                    ip_type=IPTypes.PRIVATE  # Use private IP for better security
                )
                return conn
            
            # Create async engine with Cloud SQL connector
            engine = create_async_engine(
                "postgresql+asyncpg://",
                async_creator=getconn,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            logger.info(f"✅ Created Cloud SQL connection pool for {self.connection_name}")
            return engine, connector
            
        except Exception as e:
            logger.error(f"❌ Failed to create Cloud SQL connection pool: {str(e)}")
            raise
    
    async def test_connection(self):
        """Test the Cloud SQL connection."""
        try:
            engine, connector = await self.create_connection_pool()
            
            async with engine.begin() as conn:
                result = await conn.execute("SELECT version()")
                version = result.fetchone()[0]
                logger.info(f"✅ Cloud SQL connection successful! PostgreSQL version: {version}")
                
            await engine.dispose()
            await connector.close_async()
            return True
            
        except Exception as e:
            logger.error(f"❌ Cloud SQL connection test failed: {str(e)}")
            return False
    
    async def initialize_database(self):
        """Initialize the database with tables."""
        try:
            logger.info("🔄 Initializing Cloud SQL database...")
            
            # Import models to register them
            from crow_eye_api.models import (
                user, media, analytics, ai_services, 
                social_media, gallery, subscription
            )
            from crow_eye_api.database import Base
            
            engine, connector = await self.create_connection_pool()
            
            # Create all tables
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
            logger.info("✅ Cloud SQL database initialized successfully!")
            
            await engine.dispose()
            await connector.close_async()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Cloud SQL database: {str(e)}")
            return False
    
    def get_database_url(self) -> str:
        """Get the database URL for Cloud SQL."""
        return f"postgresql+asyncpg://{self.username}:{self.password}@/{self.database_name}?host=/cloudsql/{self.connection_name}"

async def setup_cloud_sql():
    """Main setup function for Cloud SQL."""
    try:
        logger.info("🚀 Starting Cloud SQL setup...")
        
        # Initialize Cloud SQL setup
        sql_setup = CloudSQLSetup()
        
        # Test connection
        logger.info("🔍 Testing Cloud SQL connection...")
        if not await sql_setup.test_connection():
            return False
        
        # Initialize database
        logger.info("📊 Initializing database tables...")
        if not await sql_setup.initialize_database():
            return False
        
        # Print database URL for configuration
        db_url = sql_setup.get_database_url()
        logger.info(f"🎯 Use this DATABASE_URL in your environment:")
        logger.info(f"DATABASE_URL={db_url}")
        
        logger.info("🎉 Cloud SQL setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"💥 Cloud SQL setup failed: {str(e)}")
        logger.exception("Full error details:")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_cloud_sql())
    if success:
        print("\n✅ Cloud SQL setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Update your app.yaml with the new DATABASE_URL")
        print("2. Deploy your application")
        print("3. Test the deployment")
    else:
        print("\n❌ Cloud SQL setup failed!")
        print("\n🔧 Troubleshooting:")
        print("1. Check your Google Cloud credentials")
        print("2. Verify Cloud SQL instance is running")
        print("3. Check environment variables")
        exit(1) 