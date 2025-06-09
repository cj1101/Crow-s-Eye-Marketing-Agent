from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from crow_eye_api.models.media import MediaItem, Gallery
from crow_eye_api.schemas.media import MediaItemCreate, MediaItemUpdate, MediaSearch


async def create_media_item(db: AsyncSession, media_item: MediaItemCreate, user_id: int) -> MediaItem:
    """Create a new media item."""
    db_media = MediaItem(
        **media_item.model_dump(),
        user_id=user_id
    )
    db.add(db_media)
    await db.commit()
    await db.refresh(db_media)
    return db_media


async def get_media_item(db: AsyncSession, media_id: int, user_id: int) -> Optional[MediaItem]:
    """Get a specific media item by ID."""
    result = await db.execute(
        select(MediaItem)
        .where(and_(MediaItem.id == media_id, MediaItem.user_id == user_id))
    )
    return result.scalar_one_or_none()


async def get_media_items(
    db: AsyncSession, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[MediaItem]:
    """Get all media items for a user."""
    result = await db.execute(
        select(MediaItem)
        .where(MediaItem.user_id == user_id)
        .order_by(MediaItem.upload_date.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def search_media_items(
    db: AsyncSession,
    user_id: int,
    search_params: MediaSearch
) -> tuple[List[MediaItem], int]:
    """Search media items with filters."""
    query = select(MediaItem).where(MediaItem.user_id == user_id)
    count_query = select(func.count(MediaItem.id)).where(MediaItem.user_id == user_id)
    
    # Apply filters
    conditions = []
    
    if search_params.query:
        query_filter = or_(
            MediaItem.filename.ilike(f"%{search_params.query}%"),
            MediaItem.original_filename.ilike(f"%{search_params.query}%"),
            MediaItem.caption.ilike(f"%{search_params.query}%")
        )
        conditions.append(query_filter)
    
    if search_params.media_type:
        conditions.append(MediaItem.media_type == search_params.media_type)
    
    if search_params.is_post_ready is not None:
        conditions.append(MediaItem.is_post_ready == search_params.is_post_ready)
    
    if search_params.tags:
        # Search in AI tags JSON field
        for tag in search_params.tags:
            conditions.append(
                func.json_search(MediaItem.ai_tags, 'one', f'$.*.tag') == tag
            )
    
    if conditions:
        combined_conditions = and_(*conditions)
        query = query.where(combined_conditions)
        count_query = count_query.where(combined_conditions)
    
    # Apply ordering and pagination
    query = query.order_by(MediaItem.upload_date.desc())
    query = query.offset(search_params.offset).limit(search_params.limit)
    
    # Execute queries
    result = await db.execute(query)
    count_result = await db.execute(count_query)
    
    items = result.scalars().all()
    total = count_result.scalar()
    
    return items, total


async def update_media_item(
    db: AsyncSession, 
    media_id: int, 
    user_id: int, 
    media_update: MediaItemUpdate
) -> Optional[MediaItem]:
    """Update a media item."""
    result = await db.execute(
        select(MediaItem)
        .where(and_(MediaItem.id == media_id, MediaItem.user_id == user_id))
    )
    db_media = result.scalar_one_or_none()
    
    if not db_media:
        return None
    
    update_data = media_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_media, field, value)
    
    await db.commit()
    await db.refresh(db_media)
    return db_media


async def delete_media_item(db: AsyncSession, media_id: int, user_id: int) -> bool:
    """Delete a media item."""
    result = await db.execute(
        select(MediaItem)
        .where(and_(MediaItem.id == media_id, MediaItem.user_id == user_id))
    )
    db_media = result.scalar_one_or_none()
    
    if not db_media:
        return False
    
    await db.delete(db_media)
    await db.commit()
    return True


async def get_media_by_gcs_path(db: AsyncSession, gcs_path: str) -> Optional[MediaItem]:
    """Get media item by Google Cloud Storage path."""
    result = await db.execute(
        select(MediaItem).where(MediaItem.gcs_path == gcs_path)
    )
    return result.scalar_one_or_none()


async def get_media_items_by_ids(db: AsyncSession, media_ids: List[int], user_id: int) -> List[MediaItem]:
    """Get multiple media items by their IDs."""
    result = await db.execute(
        select(MediaItem)
        .where(and_(MediaItem.id.in_(media_ids), MediaItem.user_id == user_id))
    )
    return result.scalars().all() 