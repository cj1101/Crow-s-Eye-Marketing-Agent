#!/usr/bin/env python3
"""
Migration script to transfer data from JSON files to PostgreSQL database.
This ensures data consistency across the website, desktop app, and API.
"""

import os
import sys
import json
import asyncio
import asyncpg
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crow_eye_api.database import DatabaseManager

class DataMigrator:
    """Handles migration from JSON files to PostgreSQL database."""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.data_dir = project_root / "data"
        self.migration_log = []
    
    async def migrate_all(self):
        """Run complete migration process."""
        print("🚀 Starting data migration from JSON to PostgreSQL...")
        
        try:
            await self.db.connect()
            print("✅ Database connection established")
            
            # Migrate users
            await self.migrate_users()
            
            # Migrate media library
            await self.migrate_media_library()
            
            # Migrate scheduled posts
            await self.migrate_scheduled_posts()
            
            print("\n📊 Migration Summary:")
            for log_entry in self.migration_log:
                print(f"  {log_entry}")
            
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise
        finally:
            await self.db.disconnect()
    
    async def migrate_users(self):
        """Migrate users from users.json to database."""
        users_file = self.data_dir / "users.json"
        
        if not users_file.exists():
            print("⚠️  No users.json file found, skipping user migration")
            return
        
        print("📁 Migrating users...")
        
        with open(users_file, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        migrated_count = 0
        
        for user_email, user_info in users_data.items():
            try:
                # Check if user already exists
                existing_user = await self.db.get_user_by_email(user_email)
                if existing_user:
                    print(f"  ⏭️  User {user_email} already exists, skipping")
                    continue
                
                # Create user data
                user_data = {
                    'email': user_email,
                    'password': user_info.get('password', 'migrated_user'),  # Placeholder
                    'displayName': user_info.get('display_name', user_email.split('@')[0]),
                    'firstName': user_info.get('first_name'),
                    'lastName': user_info.get('last_name'),
                    'plan': user_info.get('subscription_tier', 'FREE').upper()
                }
                
                user_id = await self.db.create_user(user_data)
                migrated_count += 1
                print(f"  ✅ Migrated user: {user_email} (ID: {user_id})")
                
            except Exception as e:
                print(f"  ❌ Failed to migrate user {user_email}: {e}")
        
        self.migration_log.append(f"Users: {migrated_count} migrated")
    
    async def migrate_media_library(self):
        """Migrate media library from library.json to database."""
        library_file = self.data_dir / "library.json"
        
        if not library_file.exists():
            print("⚠️  No library.json file found, skipping media migration")
            return
        
        print("📁 Migrating media library...")
        
        with open(library_file, 'r', encoding='utf-8') as f:
            library_data = json.load(f)
        
        migrated_count = 0
        
        # Get a default user for media items (or create one)
        default_user = await self.get_or_create_default_user()
        
        for item_id, item_data in library_data.get('items', {}).items():
            try:
                # Check if media already exists
                existing_media = await self.db.execute_query(
                    "SELECT id FROM media_items WHERE id = $1", item_id
                )
                if existing_media:
                    print(f"  ⏭️  Media {item_id} already exists, skipping")
                    continue
                
                # Determine media type
                file_path = item_data.get('path', '')
                media_type = self.determine_media_type(file_path)
                
                # Calculate file size if possible
                size = 0
                if file_path and os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                elif 'size_str' in item_data:
                    # Parse size string like "219.9 KB"
                    size = self.parse_size_string(item_data['size_str'])
                
                # Create media data
                media_data = {
                    'name': item_data.get('filename', f"media_{item_id}"),
                    'type': media_type,
                    'url': f"/media/{item_data.get('filename', f'{item_id}.jpg')}",
                    'size': size,
                    'tags': item_data.get('tags', []),
                    'userId': default_user['id']
                }
                
                # Insert with specific ID
                command = """
                    INSERT INTO media_items (id, name, type, url, thumbnail, size, tags, "userId", "createdAt")
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """
                
                created_at = datetime.fromisoformat(
                    item_data.get('date_added', datetime.now().isoformat())
                )
                
                await self.db.execute_command(
                    command,
                    item_id,
                    media_data['name'],
                    media_data['type'],
                    media_data['url'],
                    None,  # thumbnail
                    media_data['size'],
                    media_data['tags'],
                    media_data['userId'],
                    created_at
                )
                
                migrated_count += 1
                print(f"  ✅ Migrated media: {item_data.get('filename', item_id)}")
                
            except Exception as e:
                print(f"  ❌ Failed to migrate media {item_id}: {e}")
        
        self.migration_log.append(f"Media items: {migrated_count} migrated")
    
    async def migrate_scheduled_posts(self):
        """Migrate scheduled posts from scheduled_posts.json to database."""
        posts_file = self.data_dir / "scheduled_posts.json"
        
        if not posts_file.exists():
            print("⚠️  No scheduled_posts.json file found, skipping posts migration")
            return
        
        print("📁 Migrating scheduled posts...")
        
        with open(posts_file, 'r', encoding='utf-8') as f:
            posts_data = json.load(f)
        
        migrated_count = 0
        
        # Get default user
        default_user = await self.get_or_create_default_user()
        
        for post_data in posts_data:
            try:
                # Create post data
                command = """
                    INSERT INTO posts (content, platforms, hashtags, "scheduledFor", published, "userId")
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                """
                
                scheduled_for = None
                if 'scheduled_for' in post_data:
                    scheduled_for = datetime.fromisoformat(post_data['scheduled_for'])
                
                post_id = await self.db.execute_command(
                    command,
                    post_data.get('content', ''),
                    post_data.get('platforms', []),
                    post_data.get('hashtags', []),
                    scheduled_for,
                    post_data.get('published', False),
                    default_user['id']
                )
                
                migrated_count += 1
                print(f"  ✅ Migrated post: {post_data.get('content', 'Untitled')[:50]}...")
                
            except Exception as e:
                print(f"  ❌ Failed to migrate post: {e}")
        
        self.migration_log.append(f"Posts: {migrated_count} migrated")
    
    async def get_or_create_default_user(self) -> Dict[str, Any]:
        """Get or create a default user for migration purposes."""
        default_email = "migration@crowseye.local"
        
        user = await self.db.get_user_by_email(default_email)
        if user:
            return user
        
        # Create default user
        user_data = {
            'email': default_email,
            'password': 'migration_user',
            'displayName': 'Migration User',
            'plan': 'FREE'
        }
        
        user_id = await self.db.create_user(user_data)
        return await self.db.get_user_by_email(default_email)
    
    def determine_media_type(self, file_path: str) -> str:
        """Determine media type from file path."""
        if not file_path:
            return "IMAGE"
        
        extension = Path(file_path).suffix.lower()
        
        if extension in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            return "VIDEO"
        elif extension in ['.mp3', '.wav', '.aac', '.flac']:
            return "AUDIO"
        else:
            return "IMAGE"
    
    def parse_size_string(self, size_str: str) -> int:
        """Parse size string like '219.9 KB' to bytes."""
        try:
            parts = size_str.strip().split()
            if len(parts) != 2:
                return 0
            
            value = float(parts[0])
            unit = parts[1].upper()
            
            multipliers = {
                'B': 1,
                'KB': 1024,
                'MB': 1024 * 1024,
                'GB': 1024 * 1024 * 1024
            }
            
            return int(value * multipliers.get(unit, 1))
        except:
            return 0

async def main():
    """Main migration function."""
    migrator = DataMigrator()
    await migrator.migrate_all()

if __name__ == "__main__":
    asyncio.run(main()) 