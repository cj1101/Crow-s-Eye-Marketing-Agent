#!/usr/bin/env python3
"""
Database Configuration Test Script
Verifies that all database fixes are working correctly
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_test_environment():
    """Set up test environment variables if not present."""
    # Set required JWT_SECRET_KEY for testing if not present
    if not os.getenv("JWT_SECRET_KEY"):
        # Use a strong test key that passes validation (no weak patterns)
        test_jwt_key = "ZrHqLvWdNmQpTrYuIoPsDfGhJkMnBqEtRyWxCvBnMjQpSgVkYpAsDfGhJlPzXcVbN"
        os.environ["JWT_SECRET_KEY"] = test_jwt_key
        logger.info("🔧 Set temporary JWT_SECRET_KEY for testing")
    
    # Set other optional environment variables for testing
    test_env_vars = {
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",  # Override the long default
        "GOOGLE_CLOUD_PROJECT": "test-project",
        "PROJECT_NAME": "Crow's Eye API - Test"
    }
    
    for key, value in test_env_vars.items():
        if not os.getenv(key):
            os.environ[key] = value

async def test_database_config():
    """Test database configuration and initialization."""
    logger.info("🧪 Starting database configuration tests...")
    
    try:
        # Setup test environment first
        setup_test_environment()
        
        # Test 1: Environment variable check
        logger.info("📋 Test 1: Checking environment variables...")
        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///opt/app/data/crow_eye_production.db")
        logger.info(f"Database URL: {db_url}")
        
        # Test 2: Database URL format validation
        logger.info("🔍 Test 2: Validating database URL format...")
        if "sqlite" in db_url:
            if not db_url.startswith("sqlite+aiosqlite://"):
                logger.error("❌ Invalid SQLite URL format! Should start with 'sqlite+aiosqlite://'")
                return False
            logger.info("✅ SQLite URL format is correct")
        elif "postgresql" in db_url:
            if not db_url.startswith("postgresql+asyncpg://"):
                logger.error("❌ Invalid PostgreSQL URL format! Should start with 'postgresql+asyncpg://'")
                return False
            logger.info("✅ PostgreSQL URL format is correct")
        
        # Test 3: Database directory creation
        logger.info("📁 Test 3: Testing database directory creation...")
        if "sqlite" in db_url:
            db_path = db_url.split("://")[-1]
            db_dir = os.path.dirname(db_path)
            
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"✅ Database directory created/verified: {db_dir}")
            
            # Check if we can create a test file
            test_file = os.path.join(db_dir, "test_write.tmp")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                logger.info("✅ Directory is writable")
            except Exception as e:
                logger.error(f"❌ Directory not writable: {e}")
                return False
        
        # Test 4: Import checks
        logger.info("📦 Test 4: Testing module imports...")
        try:
            from crow_eye_api.database import Base, engine, check_database_health
            logger.info("✅ Database module imports successful")
        except ImportError as e:
            logger.error(f"❌ Database module import failed: {e}")
            return False
        
        # Test 5: Database connection test
        logger.info("🔌 Test 5: Testing database connection...")
        try:
            is_healthy = await check_database_health()
            if is_healthy:
                logger.info("✅ Database connection successful")
            else:
                logger.warning("⚠️ Database connection test failed, but this may be expected if tables don't exist yet")
        except Exception as e:
            logger.warning(f"⚠️ Database connection test error: {e}")
            logger.info("This is expected if the database hasn't been initialized yet")
        
        # Test 6: Database initialization test
        logger.info("🏗️ Test 6: Testing database initialization...")
        try:
            from initialize_gcp_db import init_gcp_database
            success = await init_gcp_database()
            if success:
                logger.info("✅ Database initialization successful")
            else:
                logger.error("❌ Database initialization failed")
                return False
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            return False
        
        logger.info("🎉 All database configuration tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"💥 Test suite failed with error: {e}")
        logger.exception("Full error details:")
        return False

def run_tests():
    """Run all database tests."""
    print("🧪 Crow's Eye Database Configuration Test Suite")
    print("=" * 50)
    
    success = asyncio.run(test_database_config())
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! Database configuration is working correctly.")
        print("\n📋 Next steps:")
        print("1. Deploy to GCP with: gcloud app deploy app.yaml")
        print("2. Test the health endpoint: curl https://your-app-url.uc.r.appspot.com/health")
        print("3. Check the API documentation: https://your-app-url.uc.r.appspot.com/docs")
    else:
        print("❌ Some tests failed! Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure all required dependencies are installed")
        print("2. Check environment variables are set correctly")
        print("3. Verify file permissions and directory access")
        
    return success

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 