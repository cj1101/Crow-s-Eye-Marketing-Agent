"""
Gallery router for Crow's Eye API.
"""

import os
import sys
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.models.user import User
from src.features.subscription.access_control import Feature
from ..dependencies import get_current_user, require_feature

router = APIRouter()


class GalleryRequest(BaseModel):
    """Gallery generation request model."""
    prompt: str
    media_ids: Optional[List[str]] = None
    max_items: Optional[int] = 10
    enhance_photos: Optional[bool] = False
    generate_caption: Optional[bool] = True
    caption_style: Optional[str] = "engaging and creative"


class GalleryResponse(BaseModel):
    """Gallery response model."""
    id: str
    name: str
    media_ids: List[str]
    caption: str
    created_at: str
    prompt: str


class GalleryListResponse(BaseModel):
    """Gallery list response model."""
    galleries: List[GalleryResponse]
    total: int


@router.post("/", response_model=GalleryResponse)
async def create_gallery(
    request: GalleryRequest,
    current_user: User = Depends(require_feature(Feature.SMART_GALLERY_GENERATOR))
):
    """
    Create a smart gallery using AI-powered media selection.
    
    **Tier Required:** Creator+ (Creator tier and above)
    
    The AI will analyze your media library and select the best items
    based on your prompt. For example:
    - "Best 5 photos for a winter campaign"
    - "Show me photos with people for social media"
    - "Find bread and bakery images for our website"
    """
    # This is a simplified implementation
    # In production, you'd integrate with the actual gallery generation logic
    
    import uuid
    from datetime import datetime
    
    # Mock gallery generation
    # In production, this would call the CrowsEyeHandler.generate_gallery method
    
    # If specific media_ids provided, use those; otherwise simulate AI selection
    if request.media_ids:
        selected_media = request.media_ids[:request.max_items]
    else:
        # Simulate AI selection based on prompt
        selected_media = [f"media_{i}" for i in range(min(request.max_items, 5))]
    
    # Generate caption if requested
    caption = ""
    if request.generate_caption:
        # In production, this would call the AI caption generation
        caption = f"A curated collection showcasing {request.prompt.lower()}. Perfect for your marketing needs!"
    
    gallery_id = str(uuid.uuid4())
    
    return GalleryResponse(
        id=gallery_id,
        name=f"Gallery: {request.prompt[:50]}",
        media_ids=selected_media,
        caption=caption,
        created_at=datetime.now().isoformat(),
        prompt=request.prompt
    )


@router.get("/{gallery_id}", response_model=GalleryResponse)
async def get_gallery(
    gallery_id: str,
    current_user: User = Depends(require_feature(Feature.SMART_GALLERY_GENERATOR))
):
    """
    Get gallery by ID.
    
    **Tier Required:** Creator+ (Creator tier and above)
    """
    # This is a simplified implementation
    # In production, you'd look up the gallery by ID in a database
    
    from datetime import datetime
    
    return GalleryResponse(
        id=gallery_id,
        name="Sample Gallery",
        media_ids=["media_1", "media_2", "media_3"],
        caption="A beautiful collection of curated media items.",
        created_at=datetime.now().isoformat(),
        prompt="Best photos for social media"
    )


@router.get("/", response_model=GalleryListResponse)
async def list_galleries(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(require_feature(Feature.SMART_GALLERY_GENERATOR))
):
    """
    List user's galleries.
    
    **Tier Required:** Creator+ (Creator tier and above)
    """
    # This is a simplified implementation
    # In production, you'd query the database for user's galleries
    
    from datetime import datetime
    
    # Mock gallery list
    galleries = []
    for i in range(min(limit, 5)):  # Return up to 5 mock items
        galleries.append(GalleryResponse(
            id=f"gallery_{i + offset}",
            name=f"Gallery {i + offset + 1}",
            media_ids=[f"media_{j}" for j in range(3)],
            caption=f"A curated collection for gallery {i + offset + 1}.",
            created_at=datetime.now().isoformat(),
            prompt=f"Sample prompt {i + offset + 1}"
        ))
    
    return GalleryListResponse(
        galleries=galleries,
        total=len(galleries)
    )


@router.delete("/{gallery_id}")
async def delete_gallery(
    gallery_id: str,
    current_user: User = Depends(require_feature(Feature.SMART_GALLERY_GENERATOR))
):
    """
    Delete gallery by ID.
    
    **Tier Required:** Creator+ (Creator tier and above)
    """
    # This is a simplified implementation
    # In production, you'd delete from database
    
    return {"message": f"Gallery {gallery_id} deleted successfully"}


class GalleryUpdateRequest(BaseModel):
    """Gallery update request model."""
    name: Optional[str] = None
    caption: Optional[str] = None
    media_ids: Optional[List[str]] = None


@router.put("/{gallery_id}", response_model=GalleryResponse)
async def update_gallery(
    gallery_id: str,
    request: GalleryUpdateRequest,
    current_user: User = Depends(require_feature(Feature.SMART_GALLERY_GENERATOR))
):
    """
    Update gallery by ID.
    
    **Tier Required:** Creator+ (Creator tier and above)
    """
    # This is a simplified implementation
    # In production, you'd update the gallery in the database
    
    from datetime import datetime
    
    return GalleryResponse(
        id=gallery_id,
        name=request.name or "Updated Gallery",
        media_ids=request.media_ids or ["media_1", "media_2"],
        caption=request.caption or "Updated gallery caption.",
        created_at=datetime.now().isoformat(),
        prompt="Updated prompt"
    ) 