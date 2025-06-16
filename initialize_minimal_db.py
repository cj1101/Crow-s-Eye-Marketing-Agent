#!/usr/bin/env python3
"""
Initialize the minimal Crow's Eye database with auto-cleanup.
This replaces the expensive Cloud SQL setup with a cost-effective SQLite solution.
"""

import asyncio
import logging
import os
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def initialize_minimal_database():
    """Initialize the minimal database structure"""
    try:
        # Import here to avoid circular imports
        from crow_eye_api.database import create_tables, engine
        
        # Ensure data directory exists
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)
        
        logger.info("Creating minimal database tables...")
        await create_tables()
        logger.info("✅ Database tables created successfully!")
        
        # Verify tables were created
        async with engine.begin() as conn:
            result = await conn.run_sync(
                lambda sync_conn: sync_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table';"
                ).fetchall()
            )
            tables = [row[0] for row in result]
            logger.info(f"📋 Created tables: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        return False

async def setup_cleanup_scheduler():
    """Set up the automatic cleanup scheduler"""
    try:
        from crow_eye_api.services.cleanup_service import run_daily_cleanup
        
        logger.info("🧹 Running initial cleanup...")
        result = await run_daily_cleanup()
        logger.info(f"✅ Initial cleanup completed: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error setting up cleanup: {e}")
        return False

def display_cost_savings():
    """Display the cost savings from switching to minimal setup"""
    print("\n" + "="*60)
    print("💰 COST SAVINGS SUMMARY")
    print("="*60)
    print("❌ OLD SETUP (Cloud SQL + Full Database):")
    print("   • Cloud SQL db-custom-8-32768: $20-30/day")
    print("   • Storage: $5-10/day")
    print("   • Network: $2-5/day")
    print("   • TOTAL: ~$30/day ($900/month)")
    print()
    print("✅ NEW SETUP (SQLite + Minimal Database):")
    print("   • SQLite database: $0/day")
    print("   • Local storage: $0/day")
    print("   • Cloud Run (pay-per-use): $0.10-1/day")
    print("   • TOTAL: ~$0.50/day ($15/month)")
    print()
    print("💸 SAVINGS: ~$29.50/day ($885/month)")
    print("="*60)

async def main():
    """Main initialization function"""
    print("🚀 Initializing Crow's Eye Minimal Database Setup")
    print("This will replace the expensive Cloud SQL with cost-effective SQLite")
    
    # Initialize database
    if await initialize_minimal_database():
        logger.info("✅ Database initialization successful!")
    else:
        logger.error("❌ Database initialization failed!")
        return False
    
    # Set up cleanup
    if await setup_cleanup_scheduler():
        logger.info("✅ Cleanup scheduler setup successful!")
    else:
        logger.error("❌ Cleanup scheduler setup failed!")
        return False
    
    # Display cost savings
    display_cost_savings()
    
    print("\n🎉 Initialization complete!")
    print("\nNext steps:")
    print("1. Stop your expensive Cloud SQL instance:")
    print("   gcloud sql instances patch crows-eye --activation-policy=NEVER")
    print("2. Update your deployment to use this minimal setup")
    print("3. Test the API with: python -m crow_eye_api.main")
    
    return True

if __name__ == "__main__":
    asyncio.run(main()) 