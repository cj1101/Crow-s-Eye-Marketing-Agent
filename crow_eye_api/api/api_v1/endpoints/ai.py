from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crow_eye_api.crud import crud_media
from crow_eye_api import schemas, models
from crow_eye_api.database import get_db
from crow_eye_api.api.api_v1.dependencies import get_current_active_user

router = APIRouter()


@router.post("/captions/generate", response_model=schemas.CaptionGenerateResponse)
async def generate_caption(
    caption_params: schemas.CaptionGenerate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate AI-powered captions for media items.
    """
    from crow_eye_api.services.ai import ai_service
    from crow_eye_api.services.storage import storage_service
    
    # Verify media items exist and belong to user
    media_items = await crud_media.get_media_items_by_ids(
        db=db, media_ids=caption_params.media_ids, user_id=current_user.id
    )
    
    if len(media_items) != len(caption_params.media_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more media items not found"
        )
    
    generated_captions = []
    
    for media_item in media_items:
        try:
            # Only generate captions for images currently
            if media_item.media_type != 'image':
                generated_captions.append({
                    "media_id": media_item.id,
                    "caption": "Caption generation currently supports images only.",
                    "status": "skipped"
                })
                continue
            
            # Download image from storage
            blob = storage_service.bucket.blob(media_item.filename)
            image_content = await storage_service.client.download_as_bytes(blob)
            
            # Generate caption using AI
            caption = await ai_service.generate_caption(
                image_content=image_content,
                style=caption_params.style,
                platform=caption_params.platform
            )
            
            # Optionally update the media item with the generated caption
            if caption_params.auto_apply:
                await crud_media.update_media_item(
                    db=db,
                    media_id=media_item.id,
                    user_id=current_user.id,
                    media_update=schemas.MediaItemUpdate(caption=caption)
                )
            
            generated_captions.append({
                "media_id": media_item.id,
                "caption": caption,
                "status": "success"
            })
            
        except Exception as e:
            generated_captions.append({
                "media_id": media_item.id,
                "caption": f"Error generating caption: {str(e)}",
                "status": "error"
            })
    
    return schemas.CaptionGenerateResponse(
        results=generated_captions,
        total_processed=len(generated_captions),
        success_count=len([r for r in generated_captions if r["status"] == "success"])
    )


@router.post("/highlights/generate", response_model=schemas.HighlightGenerateResponse)
async def generate_highlight(
    highlight_params: schemas.HighlightGenerate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate AI-powered highlights/reels from media items.
    
    TODO: Implement AI highlight generation
    """
    # Verify media items exist and belong to user
    media_items = await crud_media.get_media_items_by_ids(
        db=db, media_ids=highlight_params.media_ids, user_id=current_user.id
    )
    
    if len(media_items) != len(highlight_params.media_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more media items not found"
        )
    
    # Placeholder response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="AI highlight generation coming next! This will create dynamic video highlights from your media collection."
    )


@router.post("/media/{media_id}/tags")
async def generate_ai_tags(
    media_id: int,
    max_tags: int = 10,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate AI tags for a specific media item.
    """
    from crow_eye_api.services.ai import ai_service
    from crow_eye_api.services.storage import storage_service
    
    media_item = await crud_media.get_media_item(
        db=db, media_id=media_id, user_id=current_user.id
    )
    
    if not media_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media item not found"
        )
    
    if media_item.media_type != 'image':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI tagging currently supports images only"
        )
    
    try:
        # Download image from storage
        blob = storage_service.bucket.blob(media_item.filename)
        image_content = await storage_service.client.download_as_bytes(blob)
        
        # Generate tags using AI
        tags = await ai_service.generate_tags(
            image_content=image_content,
            max_tags=max_tags
        )
        
        # Update media item with generated tags
        await crud_media.update_media_item(
            db=db,
            media_id=media_id,
            user_id=current_user.id,
            media_update=schemas.MediaItemUpdate(ai_tags=tags)
        )
        
        return {
            "media_id": media_id,
            "tags": tags,
            "total_tags": len(tags),
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tag generation failed: {str(e)}"
        )


@router.post("/media/bulk-tag")
async def bulk_generate_tags(
    media_ids: List[int],
    max_tags: int = 10,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate AI tags for multiple media items in bulk.
    """
    from crow_eye_api.services.ai import ai_service
    from crow_eye_api.services.storage import storage_service
    import asyncio
    
    media_items = await crud_media.get_media_items_by_ids(
        db=db, media_ids=media_ids, user_id=current_user.id
    )
    
    if len(media_items) != len(media_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more media items not found"
        )
    
    results = []
    
    async def process_media_item(media_item):
        """Process a single media item for tagging."""
        try:
            if media_item.media_type != 'image':
                return {
                    "media_id": media_item.id,
                    "tags": [],
                    "status": "skipped",
                    "message": "AI tagging currently supports images only"
                }
            
            # Download image from storage
            blob = storage_service.bucket.blob(media_item.filename)
            image_content = await storage_service.client.download_as_bytes(blob)
            
            # Generate tags using AI
            tags = await ai_service.generate_tags(
                image_content=image_content,
                max_tags=max_tags
            )
            
            # Update media item with generated tags
            await crud_media.update_media_item(
                db=db,
                media_id=media_item.id,
                user_id=current_user.id,
                media_update=schemas.MediaItemUpdate(ai_tags=tags)
            )
            
            return {
                "media_id": media_item.id,
                "tags": tags,
                "status": "success",
                "message": f"Generated {len(tags)} tags"
            }
            
        except Exception as e:
            return {
                "media_id": media_item.id,
                "tags": [],
                "status": "error",
                "message": f"Tag generation failed: {str(e)}"
            }
    
    # Process items in batches to avoid overwhelming the AI service
    batch_size = 5
    for i in range(0, len(media_items), batch_size):
        batch = media_items[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[process_media_item(item) for item in batch],
            return_exceptions=True
        )
        
        for result in batch_results:
            if isinstance(result, Exception):
                results.append({
                    "media_id": None,
                    "tags": [],
                    "status": "error",
                    "message": f"Processing error: {str(result)}"
                })
            else:
                results.append(result)
    
    success_count = len([r for r in results if r["status"] == "success"])
    
    return {
        "results": results,
        "total_processed": len(results),
        "success_count": success_count,
        "skipped_count": len([r for r in results if r["status"] == "skipped"]),
        "error_count": len([r for r in results if r["status"] == "error"])
    } 