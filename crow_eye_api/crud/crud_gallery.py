from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from crow_eye_api.models.media import Gallery, MediaItem
from crow_eye_api.schemas.gallery import GalleryCreate, GalleryUpdate


async def create_gallery(db: AsyncSession, gallery: GalleryCreate, user_id: int) -> Gallery:
    """Create a new gallery."""
    # Get media items if provided
    media_items = []
    if gallery.media_ids:
        result = await db.execute(
            select(MediaItem)
            .where(and_(MediaItem.id.in_(gallery.media_ids), MediaItem.user_id == user_id))
        )
        media_items = result.scalars().all()
    
    db_gallery = Gallery(
        name=gallery.name,
        caption=gallery.caption,
        user_id=user_id,
        media_items=media_items
    )
    db.add(db_gallery)
    await db.commit()
    await db.refresh(db_gallery)
    return db_gallery


async def get_gallery(db: AsyncSession, gallery_id: int, user_id: int) -> Optional[Gallery]:
    """Get a specific gallery by ID with media items."""
    result = await db.execute(
        select(Gallery)
        .options(selectinload(Gallery.media_items))
        .where(and_(Gallery.id == gallery_id, Gallery.user_id == user_id))
    )
    return result.scalar_one_or_none()


async def get_galleries(
    db: AsyncSession, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[Gallery]:
    """Get all galleries for a user."""
    result = await db.execute(
        select(Gallery)
        .options(selectinload(Gallery.media_items))
        .where(Gallery.user_id == user_id)
        .order_by(Gallery.created_date.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def update_gallery(
    db: AsyncSession, 
    gallery_id: int, 
    user_id: int, 
    gallery_update: GalleryUpdate
) -> Optional[Gallery]:
    """Update a gallery."""
    result = await db.execute(
        select(Gallery)
        .options(selectinload(Gallery.media_items))
        .where(and_(Gallery.id == gallery_id, Gallery.user_id == user_id))
    )
    db_gallery = result.scalar_one_or_none()
    
    if not db_gallery:
        return None
    
    update_data = gallery_update.model_dump(exclude_unset=True)
    
    # Handle media_ids separately
    if 'media_ids' in update_data:
        media_ids = update_data.pop('media_ids')
        if media_ids is not None:
            # Get new media items
            media_result = await db.execute(
                select(MediaItem)
                .where(and_(MediaItem.id.in_(media_ids), MediaItem.user_id == user_id))
            )
            db_gallery.media_items = media_result.scalars().all()
    
    # Update other fields
    for field, value in update_data.items():
        setattr(db_gallery, field, value)
    
    await db.commit()
    await db.refresh(db_gallery)
    return db_gallery


async def delete_gallery(db: AsyncSession, gallery_id: int, user_id: int) -> bool:
    """Delete a gallery."""
    result = await db.execute(
        select(Gallery)
        .where(and_(Gallery.id == gallery_id, Gallery.user_id == user_id))
    )
    db_gallery = result.scalar_one_or_none()
    
    if not db_gallery:
        return False
    
    await db.delete(db_gallery)
    await db.commit()
    return True


async def add_media_to_gallery(
    db: AsyncSession, 
    gallery_id: int, 
    media_ids: List[int], 
    user_id: int
) -> Optional[Gallery]:
    """Add media items to a gallery."""
    result = await db.execute(
        select(Gallery)
        .options(selectinload(Gallery.media_items))
        .where(and_(Gallery.id == gallery_id, Gallery.user_id == user_id))
    )
    db_gallery = result.scalar_one_or_none()
    
    if not db_gallery:
        return None
    
    # Get media items to add
    media_result = await db.execute(
        select(MediaItem)
        .where(and_(MediaItem.id.in_(media_ids), MediaItem.user_id == user_id))
    )
    new_media_items = media_result.scalars().all()
    
    # Add media items that aren't already in the gallery
    existing_media_ids = {item.id for item in db_gallery.media_items}
    for media_item in new_media_items:
        if media_item.id not in existing_media_ids:
            db_gallery.media_items.append(media_item)
    
    await db.commit()
    await db.refresh(db_gallery)
    return db_gallery


async def remove_media_from_gallery(
    db: AsyncSession, 
    gallery_id: int, 
    media_ids: List[int], 
    user_id: int
) -> Optional[Gallery]:
    """Remove media items from a gallery."""
    result = await db.execute(
        select(Gallery)
        .options(selectinload(Gallery.media_items))
        .where(and_(Gallery.id == gallery_id, Gallery.user_id == user_id))
    )
    db_gallery = result.scalar_one_or_none()
    
    if not db_gallery:
        return None
    
    # Remove specified media items
    db_gallery.media_items = [
        item for item in db_gallery.media_items 
        if item.id not in media_ids
    ]
    
    await db.commit()
    await db.refresh(db_gallery)
    return db_gallery 