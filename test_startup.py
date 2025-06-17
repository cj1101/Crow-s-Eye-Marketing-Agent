#!/usr/bin/env python3
"""
Test script to verify that both API and desktop application can start successfully.
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_startup():
    """Test that the API can be imported and started."""
    try:
        # Set required environment variables
        os.environ['JWT_SECRET_KEY'] = 'pfxyGkNmRtHqLvWdZbJcEuPnSgKjDhGfTrYwMxBvNmQpLkJhGfDsEtRyUiOpAsWxCvBnMjKhGfDsEr'
        os.environ['ACCESS_TOKEN_EXPIRE_MINUTES'] = '60'
        
        logger.info("Testing API import...")
        from crow_eye_api.main import app
        logger.info("✅ API imported successfully")
        
        # Test database initialization
        logger.info("Testing database initialization...")
        from crow_eye_api.database import init_database
        import asyncio
        
        async def test_db():
            try:
                await init_database()
                logger.info("✅ Database initialized successfully")
                return True
            except Exception as e:
                logger.error(f"❌ Database initialization failed: {e}")
                return False
        
        db_success = asyncio.run(test_db())
        
        return True and db_success
        
    except Exception as e:
        logger.error(f"❌ API startup test failed: {e}")
        return False

def test_desktop_app_import():
    """Test that the desktop application can be imported."""
    try:
        logger.info("Testing desktop app imports...")
        
        # Test core imports
        from src.models.app_state import AppState
        logger.info("✅ AppState imported successfully")
        
        from src.handlers.media_handler import MediaHandler
        logger.info("✅ MediaHandler imported successfully")
        
        from src.handlers.library_handler import LibraryManager
        logger.info("✅ LibraryManager imported successfully")
        
        # Test if PySide6 is available (but don't create actual GUI)
        try:
            import PySide6
            logger.info("✅ PySide6 is available")
        except ImportError:
            logger.warning("⚠️ PySide6 not available - desktop app will not work")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Desktop app import test failed: {e}")
        return False

def main():
    """Run all startup tests."""
    logger.info("🚀 Starting Crow's Eye Marketing Agent startup tests...")
    
    results = {}
    
    # Test API
    results['api'] = test_api_startup()
    
    # Test Desktop App
    results['desktop'] = test_desktop_app_import()
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("STARTUP TEST RESULTS:")
    logger.info("="*50)
    
    for component, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{component.upper()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 All startup tests passed! The application is ready to use.")
        logger.info("\nTo start the application:")
        logger.info("  API Server: python crow_eye_api/main.py")
        logger.info("  Desktop App: python main.py")
        logger.info("  Both: python scripts/run_with_scheduling.py")
    else:
        logger.error("\n💥 Some startup tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 