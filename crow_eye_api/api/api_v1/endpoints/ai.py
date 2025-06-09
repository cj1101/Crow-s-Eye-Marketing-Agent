from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....crud import crud_media
from .... import schemas, models
from ....database import get_db
from ..dependencies import get_current_active_user

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
    from ....services.ai import ai_service
    from ....services.storage import storage_service
    
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
    """
    from ....services.highlight import highlight_service
    import tempfile
    import os
    import asyncio
    from datetime import datetime
    
    # Verify media items exist and belong to user
    media_items = await crud_media.get_media_items_by_ids(
        db=db, media_ids=highlight_params.media_ids, user_id=current_user.id
    )
    
    if len(media_items) != len(highlight_params.media_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more media items not found"
        )
    
    # Filter only video media items
    video_items = [item for item in media_items if item.media_type == 'video']
    
    if not video_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No video items found in the provided media IDs. Highlight generation requires video content."
        )
    
    try:
        # For now, use the first video item
        # In the future, we could combine multiple videos
        primary_video = video_items[0]
        
        # Generate highlight reel
        result = await highlight_service.generate_highlight_reel(
            media_item=primary_video,
            target_duration=highlight_params.duration or 30,
            highlight_type=highlight_params.highlight_type,
            style=highlight_params.style or "dynamic",
            include_text=highlight_params.include_text,
            include_music=highlight_params.include_music
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Highlight generation failed: {result.error_message}"
            )
        
        return schemas.HighlightGenerateResponse(
            highlight_url=result.output_url,
            thumbnail_url=result.thumbnail_url,
            duration=result.duration,
            style_used=result.style_used,
            media_count=len(video_items),
            generation_metadata=result.metadata,
            message=result.message
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during highlight generation: {str(e)}"
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
    from ....services.ai import ai_service
    from ....services.storage import storage_service
    
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

# New AI endpoints for API specification compliance

@router.post("/caption")
async def generate_caption_new(
    request: dict,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate caption with enhanced options."""
    # For demo mode, return mock caption
    tone = request.get("tone", "professional")
    platforms = request.get("platforms", ["instagram"])
    custom_instructions = request.get("customInstructions", "")
    include_hashtags = request.get("includeHashtags", True)
    
    mock_captions = {
        "professional": "Elevating your brand with innovative solutions. Experience excellence in every detail.",
        "casual": "Just vibing with this amazing moment! ✨ Life's too short not to enjoy the little things.",
        "friendly": "Hey everyone! Hope you're having an amazing day. Sharing some good vibes your way! 😊",
        "humorous": "When life gives you lemons, make a viral TikTok about it! 🍋😂",
        "inspiring": "Dream big, work hard, stay focused. Your journey to greatness starts with a single step. 💪"
    }
    
    caption = mock_captions.get(tone, mock_captions["professional"])
    
    if custom_instructions:
        caption += f"\n\n{custom_instructions}"
    
    hashtags = ""
    if include_hashtags:
        platform_hashtags = {
            "instagram": "#inspiration #motivation #success #lifestyle #goals",
            "facebook": "#community #sharing #connection #growth",
            "twitter": "#trending #thoughts #daily #life",
            "tiktok": "#viral #fyp #trending #creative",
            "linkedin": "#professional #business #networking #career"
        }
        hashtags = " ".join([platform_hashtags.get(p, "#general") for p in platforms])
    
    return {
        "caption": caption,
        "hashtags": hashtags,
        "tone": tone,
        "platforms": platforms,
        "character_count": len(caption + hashtags)
    }

@router.post("/hashtags")
async def generate_hashtags(
    request: dict,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate hashtags for content."""
    content = request.get("content", "")
    platforms = request.get("platforms", ["instagram"])
    niche = request.get("niche", "general")
    count = request.get("count", 10)
    
    # Mock hashtag generation based on niche
    niche_hashtags = {
        "fitness": ["#fitness", "#workout", "#gym", "#health", "#motivation", "#fitlife", "#training", "#exercise", "#wellness", "#strong"],
        "food": ["#food", "#foodie", "#delicious", "#cooking", "#recipe", "#yummy", "#foodporn", "#chef", "#tasty", "#homemade"],
        "travel": ["#travel", "#wanderlust", "#adventure", "#explore", "#vacation", "#trip", "#traveling", "#tourism", "#journey", "#discover"],
        "business": ["#business", "#entrepreneur", "#success", "#marketing", "#leadership", "#innovation", "#growth", "#strategy", "#professional", "#networking"],
        "lifestyle": ["#lifestyle", "#life", "#daily", "#inspiration", "#motivation", "#goals", "#happiness", "#mindset", "#positivity", "#selfcare"],
        "general": ["#amazing", "#awesome", "#beautiful", "#love", "#happy", "#fun", "#cool", "#nice", "#great", "#wonderful"]
    }
    
    hashtags = niche_hashtags.get(niche, niche_hashtags["general"])[:count]
    
    return {
        "hashtags": hashtags,
        "count": len(hashtags),
        "niche": niche,
        "platforms": platforms,
        "formatted": " ".join(hashtags)
    }

@router.post("/suggestions")
async def content_suggestions(
    request: dict,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate content suggestions for media."""
    media_id = request.get("mediaId", "")
    platforms = request.get("platforms", ["instagram"])
    content_type = request.get("contentType", "caption")
    variations = request.get("variations", 3)
    
    # Mock content suggestions
    if content_type == "caption":
        suggestions = [
            "Capturing moments that matter. Every frame tells a story worth sharing.",
            "Behind every great photo is an even greater story. What's yours?",
            "Life is a collection of moments. This is one of my favorites."
        ]
    elif content_type == "story":
        suggestions = [
            "Quick behind-the-scenes look at today's adventure!",
            "Sharing some Monday motivation with you all!",
            "Can't believe how amazing this turned out!"
        ]
    else:  # description
        suggestions = [
            "A detailed look at the creative process behind this amazing content.",
            "Exploring the inspiration and technique that brought this vision to life.",
            "The story behind the shot: planning, execution, and final results."
        ]
    
    return {
        "suggestions": suggestions[:variations],
        "media_id": media_id,
        "content_type": content_type,
        "platforms": platforms,
        "variations_count": len(suggestions[:variations])
    } 