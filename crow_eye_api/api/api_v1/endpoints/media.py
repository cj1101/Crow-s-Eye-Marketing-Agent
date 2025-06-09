from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from crow_eye_api.crud import crud_media
from crow_eye_api import schemas, models
from crow_eye_api.database import get_db
from crow_eye_api.api.api_v1.dependencies import get_current_active_user
from crow_eye_api.core.config import settings

router = APIRouter()


@router.get("/", response_model=List[schemas.MediaItemResponse])
async def get_media_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all media items for the current user.
    """
    media_items = await crud_media.get_media_items(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    
    return [
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
        for item in media_items
    ]


@router.post("/search", response_model=schemas.MediaSearchResponse)
async def search_media(
    search_params: schemas.MediaSearch,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search media items with advanced filtering and AI tag search.
    """
    media_items, total = await crud_media.search_media_items(
        db=db, user_id=current_user.id, search_params=search_params
    )
    
    items_response = [
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
        for item in media_items
    ]
    
    return schemas.MediaSearchResponse(
        items=items_response,
        total=total,
        limit=search_params.limit,
        offset=search_params.offset,
        has_more=(search_params.offset + search_params.limit) < total
    )


@router.get("/{media_id}", response_model=schemas.MediaItemResponse)
async def get_media_item(
    media_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific media item by ID.
    """
    media_item = await crud_media.get_media_item(
        db=db, media_id=media_id, user_id=current_user.id
    )
    
    if not media_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media item not found"
        )
    
    return schemas.MediaItemResponse(
        id=media_item.id,
        filename=media_item.filename,
        original_filename=media_item.original_filename,
        caption=media_item.caption,
        ai_tags=media_item.ai_tags or [],
        media_type=media_item.media_type,
        file_size=media_item.file_size,
        width=media_item.width,
        height=media_item.height,
        duration=media_item.duration,
        is_post_ready=media_item.is_post_ready,
        upload_date=media_item.upload_date,
        thumbnail_url=f"/api/v1/media/{media_item.id}/thumbnail" if media_item.thumbnail_path else None,
        download_url=f"/api/v1/media/{media_item.id}/download"
    )


@router.put("/{media_id}", response_model=schemas.MediaItemResponse)
async def update_media_item(
    media_id: int,
    media_update: schemas.MediaItemUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a media item (caption, tags, post-ready status).
    """
    updated_media = await crud_media.update_media_item(
        db=db, media_id=media_id, user_id=current_user.id, media_update=media_update
    )
    
    if not updated_media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media item not found"
        )
    
    return schemas.MediaItemResponse(
        id=updated_media.id,
        filename=updated_media.filename,
        original_filename=updated_media.original_filename,
        caption=updated_media.caption,
        ai_tags=updated_media.ai_tags or [],
        media_type=updated_media.media_type,
        file_size=updated_media.file_size,
        width=updated_media.width,
        height=updated_media.height,
        duration=updated_media.duration,
        is_post_ready=updated_media.is_post_ready,
        upload_date=updated_media.upload_date,
        thumbnail_url=f"/api/v1/media/{updated_media.id}/thumbnail" if updated_media.thumbnail_path else None,
        download_url=f"/api/v1/media/{updated_media.id}/download"
    )


@router.delete("/{media_id}")
async def delete_media_item(
    media_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a media item and its files from Google Cloud Storage.
    """
    from crow_eye_api.services.storage import storage_service
    
    # Get media item first to access file paths
    media_item = await crud_media.get_media_item(
        db=db, media_id=media_id, user_id=current_user.id
    )
    
    if not media_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media item not found"
        )
    
    # Delete from database first
    success = await crud_media.delete_media_item(
        db=db, media_id=media_id, user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete media item from database"
        )
    
    # Delete files from Google Cloud Storage
    try:
        await storage_service.delete_file(media_item.filename)
    except Exception as e:
        # Log the error but don't fail the entire operation
        print(f"Warning: Failed to delete file from GCS: {e}")
    
    return {"message": "Media item deleted successfully"}


@router.post("/upload", response_model=schemas.MediaUploadResponse)
async def upload_media(
    file: UploadFile = File(...),
    caption: Optional[str] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a new media file to Google Cloud Storage.
    """
    import magic
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Media upload requested by user: {current_user.email}")
    
    # Validate file type
    allowed_types = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'video/mp4', 'video/mpeg', 'video/quicktime', 'video/webm'
    }
    
    # Read file content
    file_content = await file.read()
    logger.info(f"File read: {len(file_content)} bytes")
    
    # Detect actual MIME type
    try:
        detected_type = magic.from_buffer(file_content, mime=True)
        content_type = detected_type if detected_type in allowed_types else file.content_type
        logger.info(f"Detected content type: {detected_type}, using: {content_type}")
    except Exception as e:
        logger.error(f"Error detecting file type: {e}")
        content_type = file.content_type
    
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {content_type} not supported. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Check file size (max 50MB)
    max_size = 50 * 1024 * 1024  # 50MB
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 50MB limit"
        )
    
    try:
        # Try to upload to Google Cloud Storage
        from crow_eye_api.services.storage import storage_service
        
        blob_name, file_metadata = await storage_service.upload_file(
            file_content=file_content,
            filename=file.filename or "unnamed_file",
            content_type=content_type,
            user_id=current_user.id
        )
        
        # Generate thumbnail for images
        thumbnail_path = None
        if file_metadata['media_type'] == 'image':
            try:
                thumbnail_path = await storage_service.generate_thumbnail(blob_name)
            except Exception as e:
                logger.warning(f"Failed to generate thumbnail: {e}")
        
        # Create database record
        media_create = schemas.MediaItemCreate(
            filename=blob_name,
            original_filename=file.filename or "unnamed_file",
            gcs_path=blob_name,  # Use blob_name as GCS path
            caption=caption,
            media_type=file_metadata['media_type'],
            file_size=file_metadata['file_size'],
            width=file_metadata.get('width'),
            height=file_metadata.get('height'),
            ai_tags=[],
            is_post_ready=False
        )
        
        media_item = await crud_media.create_media_item(db=db, media_item=media_create, user_id=current_user.id)
        
        # Generate URLs
        try:
            download_url = await storage_service.get_signed_url(blob_name)
            thumbnail_url = None
            if thumbnail_path:
                thumbnail_url = await storage_service.get_signed_url(thumbnail_path)
        except Exception as e:
            logger.warning(f"Failed to generate signed URLs: {e}")
            download_url = f"gs://{settings.GOOGLE_CLOUD_STORAGE_BUCKET}/{blob_name}"
            thumbnail_url = None
        
        media_response = schemas.MediaItemResponse(
            id=media_item.id,
            filename=media_item.filename,
            original_filename=media_item.original_filename,
            caption=media_item.caption,
            ai_tags=media_item.ai_tags or [],
            media_type=media_item.media_type,
            file_size=media_item.file_size,
            width=media_item.width,
            height=media_item.height,
            duration=media_item.duration,
            is_post_ready=media_item.is_post_ready,
            upload_date=media_item.upload_date,
            download_url=download_url,
            thumbnail_url=thumbnail_url
        )
        
        return schemas.MediaUploadResponse(
            media_item=media_response,
            message="File uploaded successfully"
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Upload failed: {error_msg}")
        
        # Check if it's a Google Cloud billing/authentication issue
        if "billing account" in error_msg.lower() or "403" in error_msg or "authentication" in error_msg.lower():
            # For testing purposes, create a mock database entry when GCP is not available
            logger.warning("Google Cloud Storage not available, creating mock database entry for testing")
            
            # Determine media type from content type
            media_type = 'image' if content_type.startswith('image/') else 'video'
            
            # Create database record without GCS upload
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            test_filename = f"test_{unique_id}_{file.filename or 'unnamed_file'}"
            media_create = schemas.MediaItemCreate(
                filename=test_filename,
                original_filename=file.filename or "unnamed_file",
                gcs_path=f"test/{test_filename}",  # Mock GCS path for testing
                caption=caption,
                media_type=media_type,
                file_size=len(file_content),
                width=None,
                height=None,
                ai_tags=[],
                is_post_ready=False
            )
            
            try:
                media_item = await crud_media.create_media_item(db=db, media_item=media_create, user_id=current_user.id)
                
                media_response = schemas.MediaItemResponse(
                    id=media_item.id,
                    filename=media_item.filename,
                    original_filename=media_item.original_filename,
                    caption=media_item.caption,
                    ai_tags=media_item.ai_tags or [],
                    media_type=media_item.media_type,
                    file_size=media_item.file_size,
                    width=media_item.width,
                    height=media_item.height,
                    duration=media_item.duration,
                    is_post_ready=media_item.is_post_ready,
                    upload_date=media_item.upload_date,
                    download_url="[Google Cloud Storage not configured - testing mode]",
                    thumbnail_url=None
                )
                
                return schemas.MediaUploadResponse(
                    media_item=media_response,
                    message="File uploaded successfully (testing mode - Google Cloud Storage not configured)"
                )
            except Exception as db_error:
                logger.error(f"Database error: {db_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database error: {str(db_error)}"
                )
        else:
            # Other errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Upload failed: {error_msg}"
            )


@router.get("/{media_id}/download")
async def download_media(
    media_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a signed URL to download media file from Google Cloud Storage.
    """
    from crow_eye_api.services.storage import storage_service
    
    media_item = await crud_media.get_media_item(
        db=db, media_id=media_id, user_id=current_user.id
    )
    
    if not media_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media item not found"
        )
    
    try:
        # Generate signed URL (valid for 1 hour)
        signed_url = await storage_service.get_signed_url(media_item.filename)
        return {"download_url": signed_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}"
        )


@router.get("/{media_id}/thumbnail")
async def get_thumbnail(
    media_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get thumbnail for media item.
    """
    from crow_eye_api.services.storage import storage_service
    
    media_item = await crud_media.get_media_item(
        db=db, media_id=media_id, user_id=current_user.id
    )
    
    if not media_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media item not found"
        )
    
    if not media_item.thumbnail_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail not available for this media item"
        )
    
    try:
        # Generate signed URL for thumbnail
        signed_url = await storage_service.get_signed_url(media_item.thumbnail_path)
        return {"thumbnail_url": signed_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate thumbnail URL: {str(e)}"
        ) 