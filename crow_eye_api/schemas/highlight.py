from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class HighlightGenerate(BaseModel):
    """Schema for AI highlight generation."""
    media_ids: List[int] = Field(..., description="List of media IDs to generate highlights from")
    highlight_type: str = Field(default="story", description="Type of highlight (story, reel, short, etc.)")
    duration: Optional[int] = Field(default=30, description="Duration in seconds for video highlights")
    style: Optional[str] = Field(default="dynamic", description="Style of the highlight (dynamic, minimal, elegant, etc.)")
    include_text: bool = Field(default=True, description="Whether to include text overlays")
    include_music: bool = Field(default=False, description="Whether to include background music")


class HighlightGenerateResponse(BaseModel):
    """Response schema for AI-generated highlights."""
    highlight_url: str
    thumbnail_url: str
    duration: float
    style_used: str
    media_count: int
    generation_metadata: Dict[str, Any]
    message: str 