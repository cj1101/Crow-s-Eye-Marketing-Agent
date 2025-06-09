from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class GalleryBase(BaseModel):
    """Base schema for galleries."""
    name: str
    caption: Optional[str] = None
    media_ids: List[int] = []


class GalleryCreate(GalleryBase):
    """Schema for creating galleries."""
    pass


class GalleryUpdate(BaseModel):
    """Schema for updating galleries."""
    name: Optional[str] = None
    caption: Optional[str] = None
    media_ids: Optional[List[int]] = None


class Gallery(GalleryBase):
    """Complete gallery schema."""
    id: int
    created_date: datetime
    user_id: int
    
    class Config:
        from_attributes = True


class GalleryResponse(BaseModel):
    """Response schema for galleries with media details."""
    id: int
    name: str
    caption: Optional[str]
    media_count: int
    created_date: datetime
    media_items: Optional[List[Any]] = None  # Will be populated with MediaItemResponse


class GalleryGenerate(BaseModel):
    """Schema for AI-powered gallery generation."""
    prompt: str = Field(..., description="Prompt describing the desired gallery content")
    max_items: int = Field(default=10, ge=1, le=50, description="Maximum number of items in gallery")
    media_types: Optional[List[str]] = Field(default=["image"], description="Types of media to include")
    enhance_photos: bool = Field(default=False, description="Whether to enhance photos")
    prefer_post_ready: bool = Field(default=True, description="Prefer post-ready media items")


class GalleryGenerateResponse(BaseModel):
    """Response schema for AI-generated galleries."""
    gallery_id: int
    name: str
    media_items: List[Any]  # MediaItemResponse objects
    generation_metadata: Dict[str, Any]
    message: str 