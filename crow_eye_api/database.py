"""
Database connection and utilities for Crow's Eye API.
"""

import os
import asyncio
import asyncpg
from typing import Optional, Dict, List, Any
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for PostgreSQL operations."""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = os.getenv(
            "DATABASE_URL", 
            "postgresql://username:password@localhost:5432/crow_eye_db"
        )
    
    async def connect(self):
        """Initialize database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as connection:
            try:
                rows = await connection.fetch(query, *args)
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                raise
    
    async def execute_command(self, command: str, *args) -> str:
        """Execute an INSERT/UPDATE/DELETE command."""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as connection:
            try:
                result = await connection.execute(command, *args)
                return result
            except Exception as e:
                logger.error(f"Command execution failed: {e}")
                raise
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        query = """
            SELECT id, email, "displayName", "firstName", "lastName", 
                   avatar, plan, "createdAt", "updatedAt", "lastLoginAt"
            FROM users WHERE email = $1
        """
        results = await self.execute_query(query, email)
        return results[0] if results else None
    
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user and return the user ID."""
        command = """
            INSERT INTO users (email, password, "displayName", "firstName", "lastName", plan)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as connection:
            try:
                user_id = await connection.fetchval(
                    command,
                    user_data['email'],
                    user_data['password'],
                    user_data.get('displayName', ''),
                    user_data.get('firstName'),
                    user_data.get('lastName'),
                    user_data.get('plan', 'FREE')
                )
                return user_id
            except Exception as e:
                logger.error(f"User creation failed: {e}")
                raise
    
    async def get_user_media(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get media items for a user."""
        query = """
            SELECT id, name, type, url, thumbnail, size, tags, "createdAt", "updatedAt"
            FROM media_items 
            WHERE "userId" = $1
            ORDER BY "createdAt" DESC
            LIMIT $2 OFFSET $3
        """
        return await self.execute_query(query, user_id, limit, offset)
    
    async def create_media_item(self, media_data: Dict[str, Any]) -> str:
        """Create a new media item and return the media ID."""
        command = """
            INSERT INTO media_items (name, type, url, thumbnail, size, tags, "userId")
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as connection:
            try:
                media_id = await connection.fetchval(
                    command,
                    media_data['name'],
                    media_data['type'],
                    media_data['url'],
                    media_data.get('thumbnail'),
                    media_data['size'],
                    media_data.get('tags', []),
                    media_data['userId']
                )
                return media_id
            except Exception as e:
                logger.error(f"Media creation failed: {e}")
                raise
    
    async def get_user_galleries(self, user_id: str) -> List[Dict[str, Any]]:
        """Get galleries for a user."""
        query = """
            SELECT g.id, g.title, g."createdAt", g."updatedAt",
                   COUNT(gm.id) as media_count
            FROM galleries g
            LEFT JOIN gallery_media gm ON g.id = gm."galleryId"
            WHERE g."userId" = $1
            GROUP BY g.id, g.title, g."createdAt", g."updatedAt"
            ORDER BY g."createdAt" DESC
        """
        return await self.execute_query(query, user_id)
    
    async def create_gallery(self, gallery_data: Dict[str, Any]) -> str:
        """Create a new gallery and return the gallery ID."""
        command = """
            INSERT INTO galleries (title, "userId")
            VALUES ($1, $2)
            RETURNING id
        """
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as connection:
            try:
                gallery_id = await connection.fetchval(
                    command,
                    gallery_data['title'],
                    gallery_data['userId']
                )
                return gallery_id
            except Exception as e:
                logger.error(f"Gallery creation failed: {e}")
                raise

# Global database manager instance
db_manager = DatabaseManager()

async def get_database() -> DatabaseManager:
    """Dependency to get database manager."""
    if not db_manager.pool:
        await db_manager.connect()
    return db_manager 