#!/usr/bin/env python3
"""
Create Test User for AI Generation
Ensures we have a user with proper subscription tier for testing
"""

import asyncio
import logging
from crow_eye_api.crud.crud_user import create_user
from crow_eye_api.schemas.user import UserCreate
from crow_eye_api.database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_test_user():
    """Create a test user for AI generation testing."""
    
    async for db in get_db():
        try:
            # Create user data
            user_data = UserCreate(
                email="charlie@suarezhouse.net",
                password="testpass123",
                full_name="Test User for AI Generation"
            )
            
            # Check if user already exists
            from crow_eye_api.crud.crud_user import get_user_by_email
            existing_user = await get_user_by_email(db, email=user_data.email)
            
            if existing_user:
                logger.info(f"User {user_data.email} already exists with subscription tier: {existing_user.subscription_tier}")
                return existing_user
            
            # Create new user (special handling for charlie@suarezhouse.net is in crud)
            user = await create_user(db, user=user_data)
            
            logger.info(f"✅ Created test user: {user.email}")
            logger.info(f"📊 Subscription tier: {user.subscription_tier}")
            logger.info(f"📊 Subscription status: {user.subscription_status}")
            logger.info(f"📊 Email verified: {user.email_verified}")
            
            return user
            
        except Exception as e:
            logger.error(f"❌ Error creating test user: {e}")
            raise
        finally:
            await db.close()

def main():
    """Main function."""
    print("🔄 Creating test user for AI generation...")
    
    try:
        user = asyncio.run(create_test_user())
        print(f"🎉 Test user ready: {user.email}")
        print(f"🔑 Password: testpass123")
        print(f"🏆 Subscription: {user.subscription_tier}")
        
    except Exception as e:
        print(f"💥 Failed to create test user: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 