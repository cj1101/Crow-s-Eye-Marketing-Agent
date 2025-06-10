from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime, timedelta

from .... import schemas, models
from ....database import get_db
from ..dependencies import get_current_active_user

router = APIRouter()

# In-memory preview storage (in production, use Redis with TTL)
preview_storage = {}


@router.post("/generate", response_model=schemas.PreviewGenerateResponse)
async def generate_previews(
    request: schemas.PreviewGenerateRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate platform-specific previews for content.
    """
    try:
        preview_id = f"prev_{uuid.uuid4().hex[:8]}"
        expiry_time = datetime.utcnow() + timedelta(hours=24)
        
        # Generate platform-specific previews
        previews = {}
        
        for platform in request.platforms:
            preview_data = await generate_platform_preview(
                content=request.content,
                platform=platform,
                preview_type=request.preview_type
            )
            previews[platform] = preview_data
        
        # Store preview data with expiry
        preview_storage[preview_id] = {
            "preview_id": preview_id,
            "previews": previews,
            "generated_at": datetime.utcnow().isoformat(),
            "expires_at": expiry_time.isoformat(),
            "user_id": current_user.id,
            "preview_type": request.preview_type
        }
        
        return schemas.PreviewGenerateResponse(
            preview_id=preview_id,
            previews=previews,
            expiry_time=expiry_time.isoformat(),
            total_platforms=len(request.platforms)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview generation failed: {str(e)}"
        )


@router.get("/{preview_id}", response_model=schemas.PreviewResponse)
async def get_preview(
    preview_id: str,
    platform: str = None,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve generated preview by ID.
    """
    if preview_id not in preview_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preview not found or expired"
        )
    
    preview_data = preview_storage[preview_id]
    
    # Verify preview belongs to current user
    if preview_data.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this preview"
        )
    
    # Check if preview has expired
    expiry_time = datetime.fromisoformat(preview_data["expires_at"].replace('Z', '+00:00'))
    if datetime.utcnow() > expiry_time.replace(tzinfo=None):
        del preview_storage[preview_id]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preview has expired"
        )
    
    # Return specific platform preview or all previews
    if platform:
        if platform not in preview_data["previews"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preview for platform '{platform}' not found"
            )
        
        return schemas.PreviewResponse(
            preview_id=preview_id,
            platform=platform,
            preview_data=preview_data["previews"][platform],
            generated_at=preview_data["generated_at"],
            expires_at=preview_data["expires_at"]
        )
    else:
        # Return first platform or all platforms data
        first_platform = next(iter(preview_data["previews"].keys()))
        return schemas.PreviewResponse(
            preview_id=preview_id,
            platform="all",
            preview_data=preview_data["previews"],
            generated_at=preview_data["generated_at"],
            expires_at=preview_data["expires_at"]
        )


async def generate_platform_preview(content: Dict[str, Any], platform: str, preview_type: str) -> Dict[str, Any]:
    """
    Generate platform-specific preview data.
    """
    # Platform-specific configurations
    platform_configs = {
        "instagram": {
            "max_caption_length": 2200,
            "image_ratios": ["1:1", "4:5", "16:9"],
            "story_duration": 15,
            "reel_duration": 90
        },
        "facebook": {
            "max_caption_length": 63206,
            "image_ratios": ["16:9", "1:1"],
            "video_length": 240
        },
        "twitter": {
            "max_caption_length": 280,
            "image_ratios": ["16:9", "1:1"],
            "video_length": 140
        },
        "tiktok": {
            "max_caption_length": 150,
            "video_ratios": ["9:16"],
            "max_duration": 180
        },
        "linkedin": {
            "max_caption_length": 3000,
            "image_ratios": ["1.91:1", "1:1"],
            "article_length": 1300
        }
    }
    
    config = platform_configs.get(platform, platform_configs["instagram"])
    
    # Generate preview based on content type
    if preview_type == "post":
        caption = content.get("caption", "")
        if len(caption) > config["max_caption_length"]:
            caption = caption[:config["max_caption_length"]-3] + "..."
        
        preview_data = {
            "platform": platform,
            "preview_type": "post",
            "caption": caption,
            "hashtags": content.get("hashtags", []),
            "media_preview": {
                "type": content.get("media_type", "image"),
                "url": content.get("media_url", "https://placeholder.com/500x500"),
                "aspect_ratio": config["image_ratios"][0]
            },
            "engagement_estimate": {
                "likes": "2.1K - 5.6K",
                "comments": "45 - 120",
                "shares": "12 - 35"
            },
            "character_count": len(caption),
            "max_characters": config["max_caption_length"]
        }
    
    elif preview_type == "story":
        preview_data = {
            "platform": platform,
            "preview_type": "story",
            "duration": config.get("story_duration", 15),
            "text_overlay": content.get("text_overlay", ""),
            "background_color": content.get("background_color", "#FF6B6B"),
            "stickers": content.get("stickers", []),
            "music": content.get("music", None)
        }
    
    else:  # Default to post
        preview_data = {
            "platform": platform,
            "preview_type": preview_type,
            "content": content,
            "formatted_for": platform,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    return preview_data 