from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from crow_eye_api.crud import crud_gallery, crud_media
from crow_eye_api import schemas, models
from crow_eye_api.database import get_db
from crow_eye_api.api.api_v1.dependencies import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[schemas.GalleryResponse])
async def get_galleries(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all galleries for the current user.
    """
    galleries = await crud_gallery.get_galleries(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    
    return [
        schemas.GalleryResponse(
            id=gallery.id,
            name=gallery.name,
            caption=gallery.caption,
            media_count=len(gallery.media_items),
            created_date=gallery.created_date,
            media_items=[
                schemas.MediaItemResponse(
                    id=item.id,
                    filename=item.filename,
                    original_filename=item.original_filename,
                    caption=item.caption,
                    ai_tags=item.ai_tags or [],
                    media_type=item.media_type,
                    file_size=item.file_size,
                    width=item.width,
                    height=item.height,
                    duration=item.duration,
                    is_post_ready=item.is_post_ready,
                    upload_date=item.upload_date,
                    thumbnail_url=f"/api/v1/media/{item.id}/thumbnail" if item.thumbnail_path else None,
                    download_url=f"/api/v1/media/{item.id}/download"
                )
                for item in gallery.media_items
            ]
        )
        for gallery in galleries
    ]


@router.post("/", response_model=schemas.GalleryResponse)
async def create_gallery(
    gallery: schemas.GalleryCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new gallery.
    """
    created_gallery = await crud_gallery.create_gallery(
        db=db, gallery=gallery, user_id=current_user.id
    )
    
    return schemas.GalleryResponse(
        id=created_gallery.id,
        name=created_gallery.name,
        caption=created_gallery.caption,
        media_count=len(created_gallery.media_items),
        created_date=created_gallery.created_date,
        media_items=[
            schemas.MediaItemResponse(
                id=item.id,
                filename=item.filename,
                original_filename=item.original_filename,
                caption=item.caption,
                ai_tags=item.ai_tags or [],
                media_type=item.media_type,
                file_size=item.file_size,
                width=item.width,
                height=item.height,
                duration=item.duration,
                is_post_ready=item.is_post_ready,
                upload_date=item.upload_date,
                thumbnail_url=f"/api/v1/media/{item.id}/thumbnail" if item.thumbnail_path else None,
                download_url=f"/api/v1/media/{item.id}/download"
            )
            for item in created_gallery.media_items
        ]
    )


@router.get("/{gallery_id}", response_model=schemas.GalleryResponse)
async def get_gallery(
    gallery_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific gallery by ID.
    """
    gallery = await crud_gallery.get_gallery(
        db=db, gallery_id=gallery_id, user_id=current_user.id
    )
    
    if not gallery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery not found"
        )
    
    return schemas.GalleryResponse(
        id=gallery.id,
        name=gallery.name,
        caption=gallery.caption,
        media_count=len(gallery.media_items),
        created_date=gallery.created_date,
        media_items=[
            schemas.MediaItemResponse(
                id=item.id,
                filename=item.filename,
                original_filename=item.original_filename,
                caption=item.caption,
                ai_tags=item.ai_tags or [],
                media_type=item.media_type,
                file_size=item.file_size,
                width=item.width,
                height=item.height,
                duration=item.duration,
                is_post_ready=item.is_post_ready,
                upload_date=item.upload_date,
                thumbnail_url=f"/api/v1/media/{item.id}/thumbnail" if item.thumbnail_path else None,
                download_url=f"/api/v1/media/{item.id}/download"
            )
            for item in gallery.media_items
        ]
    )


@router.put("/{gallery_id}", response_model=schemas.GalleryResponse)
async def update_gallery(
    gallery_id: int,
    gallery_update: schemas.GalleryUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a gallery.
    """
    updated_gallery = await crud_gallery.update_gallery(
        db=db, gallery_id=gallery_id, user_id=current_user.id, gallery_update=gallery_update
    )
    
    if not updated_gallery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery not found"
        )
    
    return schemas.GalleryResponse(
        id=updated_gallery.id,
        name=updated_gallery.name,
        caption=updated_gallery.caption,
        media_count=len(updated_gallery.media_items),
        created_date=updated_gallery.created_date,
        media_items=[
            schemas.MediaItemResponse(
                id=item.id,
                filename=item.filename,
                original_filename=item.original_filename,
                caption=item.caption,
                ai_tags=item.ai_tags or [],
                media_type=item.media_type,
                file_size=item.file_size,
                width=item.width,
                height=item.height,
                duration=item.duration,
                is_post_ready=item.is_post_ready,
                upload_date=item.upload_date,
                thumbnail_url=f"/api/v1/media/{item.id}/thumbnail" if item.thumbnail_path else None,
                download_url=f"/api/v1/media/{item.id}/download"
            )
            for item in updated_gallery.media_items
        ]
    )


@router.delete("/{gallery_id}")
async def delete_gallery(
    gallery_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a gallery.
    """
    success = await crud_gallery.delete_gallery(
        db=db, gallery_id=gallery_id, user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery not found"
        )
    
    return {"message": "Gallery deleted successfully"}


@router.post("/generate", response_model=schemas.GalleryGenerateResponse)
async def generate_gallery(
    gallery_params: schemas.GalleryGenerate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a smart gallery using AI based on a prompt.
    
    TODO: Implement AI-powered gallery generation logic
    """
    # For now, return a placeholder response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="AI-powered gallery generation coming next! This will analyze your media and create smart galleries based on your prompt."
    )


@router.post("/{gallery_id}/media", response_model=schemas.GalleryResponse)
async def add_media_to_gallery(
    gallery_id: int,
    media_ids: List[int],
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add media items to a gallery.
    """
    updated_gallery = await crud_gallery.add_media_to_gallery(
        db=db, gallery_id=gallery_id, media_ids=media_ids, user_id=current_user.id
    )
    
    if not updated_gallery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery not found"
        )
    
    return schemas.GalleryResponse(
        id=updated_gallery.id,
        name=updated_gallery.name,
        caption=updated_gallery.caption,
        media_count=len(updated_gallery.media_items),
        created_date=updated_gallery.created_date,
        media_items=[
            schemas.MediaItemResponse(
                id=item.id,
                filename=item.filename,
                original_filename=item.original_filename,
                caption=item.caption,
                ai_tags=item.ai_tags or [],
                media_type=item.media_type,
                file_size=item.file_size,
                width=item.width,
                height=item.height,
                duration=item.duration,
                is_post_ready=item.is_post_ready,
                upload_date=item.upload_date,
                thumbnail_url=f"/api/v1/media/{item.id}/thumbnail" if item.thumbnail_path else None,
                download_url=f"/api/v1/media/{item.id}/download"
            )
            for item in updated_gallery.media_items
        ]
    )


@router.delete("/{gallery_id}/media")
async def remove_media_from_gallery(
    gallery_id: int,
    media_ids: List[int],
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove media items from a gallery.
    """
    updated_gallery = await crud_gallery.remove_media_from_gallery(
        db=db, gallery_id=gallery_id, media_ids=media_ids, user_id=current_user.id
    )
    
    if not updated_gallery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery not found"
        )
    
    return {"message": f"Removed {len(media_ids)} media items from gallery"} 