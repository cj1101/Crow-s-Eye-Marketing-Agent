"""
Stories router for Crow's Eye API.
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


class StoryRequest(BaseModel):
    """Story creation request model."""
    media_ids: List[str]
    text_overlay: Optional[str] = None
    style: Optional[str] = "modern"  # modern, minimal, bold, elegant
    duration: Optional[int] = 15  # seconds
    music: Optional[bool] = False
    transitions: Optional[str] = "fade"  # fade, slide, zoom


class StoryResponse(BaseModel):
    """Story response model."""
    id: str
    media_ids: List[str]
    text_overlay: Optional[str]
    style: str
    duration: int
    created_at: str
    preview_url: str
    download_url: str


class StoryListResponse(BaseModel):
    """Story list response model."""
    stories: List[StoryResponse]
    total: int


@router.post("/", response_model=StoryResponse)
async def create_story(
    request: StoryRequest,
    current_user: User = Depends(require_feature(Feature.POST_FORMATTING))
):
    """
    Create formatted story from media.
    
    **Tier Required:** Creator+ (Creator tier and above)
    
    Automatically formats your media for Instagram/Facebook stories with:
    - Optimal aspect ratio (9:16)
    - Text overlays
    - Style templates
    - Transition effects
    """
    if not request.media_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one media item is required"
        )
    
    # This is a simplified implementation
    # In production, you'd integrate with the actual story formatting logic
    
    import uuid
    from datetime import datetime
    
    story_id = str(uuid.uuid4())
    
    # Mock story creation
    # In production, this would process the media and create the story
    
    return StoryResponse(
        id=story_id,
        media_ids=request.media_ids,
        text_overlay=request.text_overlay,
        style=request.style,
        duration=request.duration,
        created_at=datetime.now().isoformat(),
        preview_url=f"/stories/{story_id}/preview",
        download_url=f"/stories/{story_id}/download"
    )


@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(
    story_id: str,
    current_user: User = Depends(require_feature(Feature.POST_FORMATTING))
):
    """
    Get story by ID.
    
    **Tier Required:** Creator+ (Creator tier and above)
    """
    # This is a simplified implementation
    # In production, you'd look up the story by ID in a database
    
    from datetime import datetime
    
    return StoryResponse(
        id=story_id,
        media_ids=["media_1", "media_2"],
        text_overlay="Sample story text",
        style="modern",
        duration=15,
        created_at=datetime.now().isoformat(),
        preview_url=f"/stories/{story_id}/preview",
        download_url=f"/stories/{story_id}/download"
    )


@router.get("/", response_model=StoryListResponse)
async def list_stories(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(require_feature(Feature.POST_FORMATTING))
):
    """
    List user's stories.
    
    **Tier Required:** Creator+ (Creator tier and above)
    """
    # This is a simplified implementation
    # In production, you'd query the database for user's stories
    
    from datetime import datetime
    
    # Mock story list
    stories = []
    for i in range(min(limit, 5)):  # Return up to 5 mock items
        stories.append(StoryResponse(
            id=f"story_{i + offset}",
            media_ids=[f"media_{j}" for j in range(2)],
            text_overlay=f"Story {i + offset + 1} text",
            style="modern",
            duration=15,
            created_at=datetime.now().isoformat(),
            preview_url=f"/stories/story_{i + offset}/preview",
            download_url=f"/stories/story_{i + offset}/download"
        ))
    
    return StoryListResponse(
        stories=stories,
        total=len(stories)
    )


@router.delete("/{story_id}")
async def delete_story(
    story_id: str,
    current_user: User = Depends(require_feature(Feature.POST_FORMATTING))
):
    """
    Delete story by ID.
    
    **Tier Required:** Creator+ (Creator tier and above)
    """
    # This is a simplified implementation
    # In production, you'd delete from database and file system
    
    return {"message": f"Story {story_id} deleted successfully"}


class StoryTemplateResponse(BaseModel):
    """Story template response model."""
    id: str
    name: str
    description: str
    preview_url: str
    style: str


@router.get("/templates/", response_model=List[StoryTemplateResponse])
async def list_story_templates(
    current_user: User = Depends(require_feature(Feature.POST_FORMATTING))
):
    """
    List available story templates.
    
    **Tier Required:** Creator+ (Creator tier and above)
    """
    # Mock template list
    templates = [
        StoryTemplateResponse(
            id="template_modern",
            name="Modern",
            description="Clean, contemporary design with bold typography",
            preview_url="/templates/modern/preview.jpg",
            style="modern"
        ),
        StoryTemplateResponse(
            id="template_minimal",
            name="Minimal",
            description="Simple, elegant design with plenty of white space",
            preview_url="/templates/minimal/preview.jpg",
            style="minimal"
        ),
        StoryTemplateResponse(
            id="template_bold",
            name="Bold",
            description="Eye-catching design with vibrant colors",
            preview_url="/templates/bold/preview.jpg",
            style="bold"
        ),
        StoryTemplateResponse(
            id="template_elegant",
            name="Elegant",
            description="Sophisticated design with refined typography",
            preview_url="/templates/elegant/preview.jpg",
            style="elegant"
        )
    ]
    
    return templates 