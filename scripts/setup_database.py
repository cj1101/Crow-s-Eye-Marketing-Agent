#!/usr/bin/env python3
"""
Database setup script for Crow's Eye Marketing Platform.
Initializes PostgreSQL database and creates all necessary tables.
"""

import os
import sys
import asyncio
import asyncpg
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class DatabaseSetup:
    """Handles database initialization and setup."""
    
    def __init__(self):
        self.database_url = os.getenv(
            "DATABASE_URL", 
            "postgresql://username:password@localhost:5432/crow_eye_db"
        )
        self.connection = None
    
    async def setup_database(self):
        """Complete database setup process."""
        print("🚀 Setting up Crow's Eye database...")
        
        try:
            # Connect to database
            await self.connect()
            print("✅ Database connection established")
            
            # Create tables
            await self.create_tables()
            print("✅ Database tables created")
            
            # Create indexes
            await self.create_indexes()
            print("✅ Database indexes created")
            
            print("\n✅ Database setup completed successfully!")
            
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            raise
        finally:
            if self.connection:
                await self.connection.close()
    
    async def connect(self):
        """Connect to PostgreSQL database."""
        self.connection = await asyncpg.connect(self.database_url)
    
    async def create_tables(self):
        """Create all necessary database tables."""
        
        # Users table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                "displayName" TEXT NOT NULL,
                "firstName" TEXT,
                "lastName" TEXT,
                avatar TEXT,
                plan TEXT NOT NULL DEFAULT 'FREE',
                "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                "updatedAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                "lastLoginAt" TIMESTAMP WITH TIME ZONE
            );
        ''')
        
        # Refresh tokens table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                token TEXT UNIQUE NOT NULL,
                "userId" TEXT NOT NULL,
                "expiresAt" TIMESTAMP WITH TIME ZONE NOT NULL,
                "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY ("userId") REFERENCES users(id) ON DELETE CASCADE
            );
        ''')
        
        # Media items table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS media_items (
                id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('IMAGE', 'VIDEO', 'AUDIO')),
                url TEXT NOT NULL,
                thumbnail TEXT,
                size INTEGER NOT NULL,
                tags TEXT[] DEFAULT '{}',
                "userId" TEXT NOT NULL,
                "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                "updatedAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY ("userId") REFERENCES users(id) ON DELETE CASCADE
            );
        ''')
        
        # Galleries table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS galleries (
                id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                title TEXT NOT NULL,
                "userId" TEXT NOT NULL,
                "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                "updatedAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY ("userId") REFERENCES users(id) ON DELETE CASCADE
            );
        ''')
        
        # Gallery media junction table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS gallery_media (
                id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                "galleryId" TEXT NOT NULL,
                "mediaId" TEXT NOT NULL,
                "order" INTEGER DEFAULT 0,
                FOREIGN KEY ("galleryId") REFERENCES galleries(id) ON DELETE CASCADE,
                FOREIGN KEY ("mediaId") REFERENCES media_items(id) ON DELETE CASCADE,
                UNIQUE ("galleryId", "mediaId")
            );
        ''')
        
        # Stories table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS stories (
                id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                "userId" TEXT NOT NULL,
                "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                "updatedAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY ("userId") REFERENCES users(id) ON DELETE CASCADE
            );
        ''')
        
        # Story media junction table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS story_media (
                id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                "storyId" TEXT NOT NULL,
                "mediaId" TEXT NOT NULL,
                "order" INTEGER DEFAULT 0,
                FOREIGN KEY ("storyId") REFERENCES stories(id) ON DELETE CASCADE,
                FOREIGN KEY ("mediaId") REFERENCES media_items(id) ON DELETE CASCADE,
                UNIQUE ("storyId", "mediaId")
            );
        ''')
        
        # Highlight reels table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS highlight_reels (
                id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                title TEXT NOT NULL,
                duration INTEGER NOT NULL,
                "userId" TEXT NOT NULL,
                "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                "updatedAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY ("userId") REFERENCES users(id) ON DELETE CASCADE
            );
        ''')
        
        # Highlight media junction table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS highlight_media (
                id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                "highlightReelId" TEXT NOT NULL,
                "mediaId" TEXT NOT NULL,
                "order" INTEGER DEFAULT 0,
                FOREIGN KEY ("highlightReelId") REFERENCES highlight_reels(id) ON DELETE CASCADE,
                FOREIGN KEY ("mediaId") REFERENCES media_items(id) ON DELETE CASCADE,
                UNIQUE ("highlightReelId", "mediaId")
            );
        ''')
        
        # Posts table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                content TEXT NOT NULL,
                platforms TEXT[] DEFAULT '{}',
                hashtags TEXT[] DEFAULT '{}',
                "scheduledFor" TIMESTAMP WITH TIME ZONE,
                published BOOLEAN DEFAULT FALSE,
                "userId" TEXT NOT NULL,
                "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                "updatedAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY ("userId") REFERENCES users(id) ON DELETE CASCADE
            );
        ''')
        
        # Post media junction table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS post_media (
                id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                "postId" TEXT NOT NULL,
                "mediaId" TEXT NOT NULL,
                "order" INTEGER DEFAULT 0,
                FOREIGN KEY ("postId") REFERENCES posts(id) ON DELETE CASCADE,
                FOREIGN KEY ("mediaId") REFERENCES media_items(id) ON DELETE CASCADE,
                UNIQUE ("postId", "mediaId")
            );
        ''')
        
        # Post analytics table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS post_analytics (
                id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                "postId" TEXT NOT NULL,
                platform TEXT NOT NULL,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                engagement REAL DEFAULT 0,
                "recordedAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY ("postId") REFERENCES posts(id) ON DELETE CASCADE,
                UNIQUE ("postId", platform)
            );
        ''')
        
        # Activities table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                "userId" TEXT NOT NULL,
                action TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'INFO' CHECK (type IN ('SUCCESS', 'INFO', 'WARNING', 'ERROR')),
                metadata JSONB,
                "createdAt" TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        ''')
        
        print("  📋 All tables created successfully")
    
    async def create_indexes(self):
        """Create database indexes for better performance."""
        
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);',
            'CREATE INDEX IF NOT EXISTS idx_media_items_user_id ON media_items("userId");',
            'CREATE INDEX IF NOT EXISTS idx_media_items_type ON media_items(type);',
            'CREATE INDEX IF NOT EXISTS idx_galleries_user_id ON galleries("userId");',
            'CREATE INDEX IF NOT EXISTS idx_stories_user_id ON stories("userId");',
            'CREATE INDEX IF NOT EXISTS idx_highlight_reels_user_id ON highlight_reels("userId");',
            'CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts("userId");',
            'CREATE INDEX IF NOT EXISTS idx_posts_scheduled_for ON posts("scheduledFor");',
            'CREATE INDEX IF NOT EXISTS idx_posts_published ON posts(published);',
            'CREATE INDEX IF NOT EXISTS idx_activities_user_id ON activities("userId");',
            'CREATE INDEX IF NOT EXISTS idx_activities_created_at ON activities("createdAt");',
        ]
        
        for index_sql in indexes:
            await self.connection.execute(index_sql)
        
        print("  🔍 All indexes created successfully")

async def main():
    """Main setup function."""
    setup = DatabaseSetup()
    await setup.setup_database()

if __name__ == "__main__":
    asyncio.run(main()) 