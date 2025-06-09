from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CaptionGenerate(BaseModel):
    """Schema for AI caption generation."""
    media_ids: List[int] = Field(..., description="List of media IDs to generate caption for")
    tone: Optional[str] = Field(default="professional", description="Tone for the caption (professional, casual, creative, etc.)")
    platform: Optional[str] = Field(default=None, description="Target platform for optimization (instagram, tiktok, etc.)")
    max_length: Optional[int] = Field(default=None, description="Maximum caption length")
    include_hashtags: bool = Field(default=True, description="Whether to include hashtags")
    include_emojis: bool = Field(default=True, description="Whether to include emojis")


class CaptionGenerateResponse(BaseModel):
    """Response schema for AI-generated captions."""
    caption: str
    hashtags: List[str]
    tone_used: str
    platform_optimized: Optional[str]
    generation_metadata: Dict[str, Any]
    message: str 