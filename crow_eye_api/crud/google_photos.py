"""
CRUD operations for Google Photos integration.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from datetime import datetime

from crow_eye_api.models.media import GooglePhotosConnection, MediaItem, Gallery
from crow_eye_api.models.user import User
from crow_eye_api.schemas.google_photos import GooglePhotosConnection as GooglePhotosConnectionSchema


class GooglePhotosCRUD:
    """CRUD operations for Google Photos connections."""
    
    async def create_connection(
        self,
        db: AsyncSession,
        user_id: int,
        access_token: str,
        refresh_token: str,
        token_expires_at: Optional[datetime],
        google_user_id: str,
        google_email: str
    ) -> GooglePhotosConnection:
        """Create a new Google Photos connection."""
        
        # Check if connection already exists for this user
        existing = await self.get_connection_by_user_id(db, user_id)
        if existing:
            # Update existing connection
            return await self.update_connection(
                db, existing.id, access_token, refresh_token, 
                token_expires_at, google_user_id, google_email
            )
        
        # Create new connection
        connection = GooglePhotosConnection(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            google_user_id=google_user_id,
            google_email=google_email,
            is_active=True
        )
        
        db.add(connection)
        await db.commit()
        await db.refresh(connection)
        return connection
    
    async def get_connection_by_user_id(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Optional[GooglePhotosConnection]:
        """Get Google Photos connection by user ID."""
        result = await db.execute(
            select(GooglePhotosConnection)
            .where(GooglePhotosConnection.user_id == user_id)
            .where(GooglePhotosConnection.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def get_connection_by_id(
        self,
        db: AsyncSession,
        connection_id: int
    ) -> Optional[GooglePhotosConnection]:
        """Get Google Photos connection by ID."""
        result = await db.execute(
            select(GooglePhotosConnection)
            .where(GooglePhotosConnection.id == connection_id)
        )
        return result.scalar_one_or_none()
    
    async def update_connection(
        self,
        db: AsyncSession,
        connection_id: int,
        access_token: str,
        refresh_token: str,
        token_expires_at: Optional[datetime],
        google_user_id: str,
        google_email: str
    ) -> GooglePhotosConnection:
        """Update Google Photos connection tokens."""
        await db.execute(
            update(GooglePhotosConnection)
            .where(GooglePhotosConnection.id == connection_id)
            .values(
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=token_expires_at,
                google_user_id=google_user_id,
                google_email=google_email,
                is_active=True
            )
        )
        await db.commit()
        
        # Return updated connection
        return await self.get_connection_by_id(db, connection_id)
    
    async def update_last_sync(
        self,
        db: AsyncSession,
        connection_id: int,
        last_sync_date: datetime
    ) -> None:
        """Update last sync date for connection."""
        await db.execute(
            update(GooglePhotosConnection)
            .where(GooglePhotosConnection.id == connection_id)
            .values(last_sync_date=last_sync_date)
        )
        await db.commit()
    
    async def deactivate_connection(
        self,
        db: AsyncSession,
        connection_id: int
    ) -> None:
        """Deactivate Google Photos connection."""
        await db.execute(
            update(GooglePhotosConnection)
            .where(GooglePhotosConnection.id == connection_id)
            .values(is_active=False)
        )
        await db.commit()
    
    async def delete_connection(
        self,
        db: AsyncSession,
        connection_id: int
    ) -> None:
        """Delete Google Photos connection."""
        await db.execute(
            delete(GooglePhotosConnection)
            .where(GooglePhotosConnection.id == connection_id)
        )
        await db.commit()
    
    async def get_imported_media_by_google_id(
        self,
        db: AsyncSession,
        google_photos_id: str,
        user_id: int
    ) -> Optional[MediaItem]:
        """Get media item by Google Photos ID."""
        result = await db.execute(
            select(MediaItem)
            .where(MediaItem.google_photos_id == google_photos_id)
            .where(MediaItem.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_imported_media_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[MediaItem]:
        """Get all imported media for a user."""
        result = await db.execute(
            select(MediaItem)
            .where(MediaItem.user_id == user_id)
            .where(MediaItem.import_source == "google_photos")
            .order_by(MediaItem.import_date.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    async def create_imported_media(
        self,
        db: AsyncSession,
        user_id: int,
        filename: str,
        original_filename: str,
        gcs_path: str,
        thumbnail_path: Optional[str],
        media_type: str,
        file_size: int,
        width: Optional[int],
        height: Optional[int],
        duration: Optional[float],
        google_photos_id: str,
        google_photos_metadata: dict,
        is_post_ready: bool = False
    ) -> MediaItem:
        """Create a new imported media item."""
        media_item = MediaItem(
            user_id=user_id,
            filename=filename,
            original_filename=original_filename,
            gcs_path=gcs_path,
            thumbnail_path=thumbnail_path,
            media_type=media_type,
            file_size=file_size,
            width=width,
            height=height,
            duration=duration,
            google_photos_id=google_photos_id,
            google_photos_metadata=google_photos_metadata,
            import_source="google_photos",
            import_date=datetime.utcnow(),
            is_post_ready=is_post_ready
        )
        
        db.add(media_item)
        await db.commit()
        await db.refresh(media_item)
        return media_item
    
    async def create_gallery_from_imported_media(
        self,
        db: AsyncSession,
        user_id: int,
        name: str,
        media_ids: List[int],
        caption: Optional[str] = None
    ) -> Gallery:
        """Create a gallery from imported media items."""
        # Get media items
        result = await db.execute(
            select(MediaItem)
            .where(MediaItem.id.in_(media_ids))
            .where(MediaItem.user_id == user_id)
        )
        media_items = result.scalars().all()
        
        # Create gallery
        gallery = Gallery(
            user_id=user_id,
            name=name,
            caption=caption,
            media_items=media_items
        )
        
        db.add(gallery)
        await db.commit()
        await db.refresh(gallery)
        return gallery
    
    async def search_imported_media(
        self,
        db: AsyncSession,
        user_id: int,
        query: Optional[str] = None,
        media_type: Optional[str] = None,
        import_date_from: Optional[datetime] = None,
        import_date_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[MediaItem]:
        """Search imported media with filters."""
        stmt = select(MediaItem).where(
            MediaItem.user_id == user_id,
            MediaItem.import_source == "google_photos"
        )
        
        if query:
            stmt = stmt.where(
                MediaItem.filename.ilike(f"%{query}%") |
                MediaItem.caption.ilike(f"%{query}%")
            )
        
        if media_type:
            stmt = stmt.where(MediaItem.media_type == media_type)
        
        if import_date_from:
            stmt = stmt.where(MediaItem.import_date >= import_date_from)
        
        if import_date_to:
            stmt = stmt.where(MediaItem.import_date <= import_date_to)
        
        stmt = stmt.order_by(MediaItem.import_date.desc()).limit(limit).offset(offset)
        
        result = await db.execute(stmt)
        return result.scalars().all()


# Create CRUD instance
google_photos_crud = GooglePhotosCRUD() 