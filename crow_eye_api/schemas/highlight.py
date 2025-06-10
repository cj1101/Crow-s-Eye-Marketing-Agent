from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class HighlightExample(BaseModel):
    """Schema for example segment input for highlight detection."""
    start_time: Optional[float] = Field(None, description="Start time of example segment in seconds")
    end_time: Optional[float] = Field(None, description="End time of example segment in seconds")
    description: Optional[str] = Field(None, description="Optional description of what makes this segment special")


class HighlightGenerate(BaseModel):
    """Schema for AI highlight generation."""
    media_ids: List[int] = Field(..., description="List of media IDs to generate highlights from")
    highlight_type: str = Field(default="story", description="Type of highlight (story, reel, short, etc.)")
    duration: Optional[int] = Field(default=30, description="Duration in seconds for video highlights")
    style: Optional[str] = Field(default="dynamic", description="Style of the highlight (dynamic, minimal, elegant, etc.)")
    include_text: bool = Field(default=True, description="Whether to include text overlays")
    include_music: bool = Field(default=False, description="Whether to include background music")
    example: Optional[HighlightExample] = Field(None, description="Example time segment to find similar content")
    context_padding: Optional[float] = Field(default=2.0, description="Seconds of context to add before each highlight scene")
    content_instructions: Optional[str] = Field(None, description="Additional content guidance and instructions")


class ExtendedHighlightGenerate(BaseModel):
    """Schema for BETA extended video highlight generation (hours-long videos, cost-optimized)."""
    media_ids: List[int] = Field(..., description="List of media IDs to generate extended highlights from")
    duration: int = Field(default=900, ge=30, le=1800, description="Target duration in seconds (30 seconds to 30 minutes)")
    prompt: Optional[str] = Field(default="", description="Natural language prompt for content guidance")
    max_cost: float = Field(default=1.0, ge=0.1, le=5.0, description="Maximum cost budget for AI analysis (default: $1.00)")
    content_instructions: Optional[str] = Field(None, description="Additional content guidance and instructions")
    enable_motion_detection: bool = Field(default=True, description="Use motion detection for pre-filtering")
    enable_audio_analysis: bool = Field(default=True, description="Use audio energy analysis for pre-filtering")
    enable_scene_detection: bool = Field(default=True, description="Use scene change detection for pre-filtering")


class HighlightGenerateResponse(BaseModel):
    """Response schema for AI-generated highlights."""
    highlight_url: str
    thumbnail_url: str
    duration: float
    style_used: str
    media_count: int
    generation_metadata: Dict[str, Any]
    message: str


class ExtendedHighlightGenerateResponse(BaseModel):
    """Response schema for BETA extended highlight generation."""
    highlight_url: str
    thumbnail_url: str
    duration: float
    processing_mode: str = Field(default="BETA_extended_video", description="Processing mode used")
    cost_optimized: bool = Field(default=True, description="Whether cost optimization was applied")
    media_count: int
    generation_metadata: Dict[str, Any]
    message: str
    estimated_cost: Optional[float] = Field(None, description="Estimated cost of AI analysis in USD") 