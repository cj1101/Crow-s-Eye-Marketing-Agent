from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AITag(BaseModel):
    """AI-generated tag for media content."""
    tag: str
    confidence: float = Field(ge=0.0, le=1.0)


class MediaItemBase(BaseModel):
    """Base schema for media items."""
    filename: str
    caption: Optional[str] = None
    ai_tags: List[AITag] = []
    media_type: str  # "image", "video", "audio"
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None  # For videos/audio
    is_post_ready: bool = False


class MediaItemCreate(MediaItemBase):
    """Schema for creating media items."""
    gcs_path: str  # Google Cloud Storage path
    original_filename: str


class MediaItemUpdate(BaseModel):
    """Schema for updating media items."""
    caption: Optional[str] = None
    ai_tags: Optional[List[AITag]] = None
    is_post_ready: Optional[bool] = None


class MediaItem(MediaItemBase):
    """Complete media item schema."""
    id: int
    gcs_path: str
    original_filename: str
    thumbnail_path: Optional[str] = None
    upload_date: datetime
    user_id: int
    
    class Config:
        from_attributes = True


class MediaItemResponse(BaseModel):
    """Response schema for media items with additional metadata."""
    id: int
    filename: str
    original_filename: str
    caption: Optional[str]
    ai_tags: List[AITag]
    media_type: str
    file_size: int
    width: Optional[int]
    height: Optional[int]
    duration: Optional[float]
    is_post_ready: bool
    upload_date: datetime
    thumbnail_url: Optional[str] = None
    download_url: Optional[str] = None


class MediaUploadResponse(BaseModel):
    """Response schema for media upload."""
    media_item: MediaItemResponse
    message: str
    upload_url: Optional[str] = None  # Signed URL for upload


class MediaSearch(BaseModel):
    """Schema for media search requests."""
    query: Optional[str] = None
    media_type: Optional[str] = None  # "image", "video", "audio"
    tags: Optional[List[str]] = None
    is_post_ready: Optional[bool] = None
    limit: int = Field(default=50, le=100)
    offset: int = Field(default=0, ge=0)


class MediaSearchResponse(BaseModel):
    """Response schema for media search."""
    items: List[MediaItemResponse]
    total: int
    limit: int
    offset: int
    has_more: bool 