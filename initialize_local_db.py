#!/usr/bin/env python3
"""
Initialize local SQLite database for development.
"""

import os
import sys
import asyncio
import sqlite3
from pathlib import Path

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set environment variables for local development
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/crow_eye.db"
os.environ["JWT_SECRET_KEY"] = "pfxyGkNmRtHqLvWdZbJcEuPnSgKjDhGfTrYwMxBvNmQpLkJhGfDsEtRyUiOpAsWxCvBnMjKhGfDsEr"
os.environ["PROJECT_NAME"] = "Crow's Eye Marketing Agent - Local Development"
os.environ["ENVIRONMENT"] = "development"

async def initialize_database():
    """Initialize the SQLite database for local development."""
    try:
        # Ensure data directory exists
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)
        
        # Create SQLite database file if it doesn't exist
        db_path = data_dir / "crow_eye.db"
        if not db_path.exists():
            print(f"Creating SQLite database at: {db_path}")
            # Create empty SQLite database
            conn = sqlite3.connect(str(db_path))
            conn.close()
            print("✅ SQLite database file created")
        else:
            print(f"✅ SQLite database already exists at: {db_path}")
        
        # Import and initialize database
        from crow_eye_api.database import engine, Base
        from crow_eye_api import models  # Import models to register them
        
        print("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database tables created successfully")
        
        # Create a test user for authentication testing
        from crow_eye_api.crud import crud_user
        from crow_eye_api import schemas
        from crow_eye_api.database import AsyncSessionLocal
        
        print("Creating test user...")
        async with AsyncSessionLocal() as db:
            # Check if test user already exists
            existing_user = await crud_user.get_user_by_email(db, email="test@example.com")
            if not existing_user:
                user_create = schemas.UserCreate(
                    email="test@example.com",
                    password="testpass123",
                    full_name="Test User"
                )
                user = await crud_user.create_user(db, user=user_create)
                await db.commit()
                print(f"✅ Test user created: {user.email}")
            else:
                print(f"✅ Test user already exists: {existing_user.email}")
        
        print("\n🎉 Local database initialization complete!")
        print("Test credentials: test@example.com / testpass123")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(initialize_database()) 