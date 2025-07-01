#!/usr/bin/env python3
"""
Create a test user for authentication testing.
"""

import os
import sys
import asyncio

# Set environment variables for local development
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/crow_eye.db"
os.environ["JWT_SECRET_KEY"] = "pfxyGkNmRtHqLvWdZbJcEuPnSgKjDhGfTrYwMxBvNmQpLkJhGfDsEtRyUiOpAsWxCvBnMjKhGfDsEr"
os.environ["PROJECT_NAME"] = "Crow's Eye Marketing Agent - Local Development"

async def create_test_user():
    """Create or update test user with proper password hashing."""
    try:
        # Import after setting environment variables
        from crow_eye_api.crud import crud_user
        from crow_eye_api import schemas
        from crow_eye_api.database import AsyncSessionLocal
        from crow_eye_api.core.security import get_password_hash
        
        async with AsyncSessionLocal() as db:
            # Delete existing test user if it exists
            existing_user = await crud_user.get_user_by_email(db, email="test@example.com")
            if existing_user:
                await db.delete(existing_user)
                await db.commit()
                print("🗑️ Deleted existing test user")
            
            # Create new test user with properly hashed password
            print("Creating new test user...")
            user_create = schemas.UserCreate(
                email="test@example.com",
                password="testpass123",  # This will be hashed by crud_user.create_user
                full_name="Test User"
            )
            
            user = await crud_user.create_user(db, user=user_create)
            await db.commit()
            
            print(f"✅ Test user created successfully!")
            print(f"   📧 Email: {user.email}")
            print(f"   👤 Name: {user.full_name}")
            print(f"   🆔 ID: {user.id}")
            print(f"   🎯 Subscription: {getattr(user, 'subscription_tier', 'payg')}")
            print()
            print("🧪 Test credentials:")
            print("   Email: test@example.com")
            print("   Password: testpass123")
            
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(create_test_user()) 