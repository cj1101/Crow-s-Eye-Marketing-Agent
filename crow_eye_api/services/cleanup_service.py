import os
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

logger = logging.getLogger(__name__)

class CleanupService:
    """Service for automatic cleanup of expired content"""
    
    def __init__(self):
        self.cleanup_enabled = True
        
    async def cleanup_expired_content(self, db: AsyncSession) -> int:
        """Remove content that has exceeded the 30-day limit"""
        try:
            from ..models.minimal_models import FinishedContent
            
            now = datetime.utcnow()
            
            # Find expired content
            stmt = select(FinishedContent).where(FinishedContent.expires_at <= now)
            result = await db.execute(stmt)
            expired_content = result.scalars().all()
            
            cleanup_count = 0
            for content in expired_content:
                try:
                    # Delete associated files
                    if content.file_path and os.path.exists(content.file_path):
                        os.remove(content.file_path)
                        logger.info(f"Deleted file: {content.file_path}")
                    
                    # Delete from database
                    await db.delete(content)
                    cleanup_count += 1
                    
                except Exception as e:
                    logger.error(f"Error cleaning up content {content.id}: {e}")
                    continue
            
            if cleanup_count > 0:
                await db.commit()
                logger.info(f"Cleaned up {cleanup_count} expired content items")
            
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            await db.rollback()
            return 0
    
    async def cleanup_orphaned_files(self, content_dir: str = "./data") -> int:
        """Remove files that are no longer referenced in database"""
        try:
            from ..database import AsyncSessionLocal
            from ..models.minimal_models import FinishedContent
            
            if not os.path.exists(content_dir):
                return 0
                
            cleanup_count = 0
            async with AsyncSessionLocal() as db:
                # Get all file paths from database
                stmt = select(FinishedContent.file_path).where(FinishedContent.file_path.isnot(None))
                result = await db.execute(stmt)
                db_files = {row[0] for row in result.fetchall()}
                
                # Find orphaned files
                for root, dirs, files in os.walk(content_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if file_path not in db_files and self._is_content_file(file):
                            try:
                                os.remove(file_path)
                                cleanup_count += 1
                                logger.info(f"Removed orphaned file: {file_path}")
                            except Exception as e:
                                logger.error(f"Error removing orphaned file {file_path}: {e}")
                                
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Error during orphaned file cleanup: {e}")
            return 0
    
    def _is_content_file(self, filename: str) -> bool:
        """Check if file is a content file that should be managed"""
        content_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.webp',  # Images
            '.mp4', '.mov', '.avi', '.webm',           # Videos
            '.mp3', '.wav', '.m4a',                    # Audio
            '.json', '.txt'                            # Metadata
        }
        return Path(filename).suffix.lower() in content_extensions
    
    async def get_storage_stats(self, db: AsyncSession) -> dict:
        """Get current storage usage statistics"""
        try:
            from ..models.minimal_models import FinishedContent
            
            # Database stats
            stmt = select(FinishedContent)
            result = await db.execute(stmt)
            all_content = result.scalars().all()
            
            total_files = len(all_content)
            expired_count = sum(1 for c in all_content if c.expires_at <= datetime.utcnow())
            
            # File size stats
            total_size = 0
            for content in all_content:
                if content.file_path and os.path.exists(content.file_path):
                    total_size += os.path.getsize(content.file_path)
            
            return {
                "total_files": total_files,
                "expired_files": expired_count,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "active_files": total_files - expired_count,
                "cleanup_ready": expired_count > 0
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {"error": str(e)}

# Global cleanup service instance
cleanup_service = CleanupService()

async def run_daily_cleanup():
    """Run the daily cleanup process"""
    from ..database import AsyncSessionLocal
    
    logger.info("Starting daily cleanup process...")
    
    try:
        async with AsyncSessionLocal() as db:
            # Clean expired content
            expired_count = await cleanup_service.cleanup_expired_content(db)
            
            # Clean orphaned files
            orphaned_count = await cleanup_service.cleanup_orphaned_files()
            
            # Get final stats
            stats = await cleanup_service.get_storage_stats(db)
            
            logger.info(f"Daily cleanup completed: {expired_count} expired items, {orphaned_count} orphaned files removed")
            logger.info(f"Current storage: {stats.get('total_files', 0)} files, {stats.get('total_size_mb', 0)} MB")
            
            return {
                "expired_cleaned": expired_count,
                "orphaned_cleaned": orphaned_count,
                "storage_stats": stats
            }
            
    except Exception as e:
        logger.error(f"Daily cleanup failed: {e}")
        return {"error": str(e)} 