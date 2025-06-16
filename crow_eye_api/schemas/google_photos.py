"""
Pydantic schemas for Google Photos integration.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime


class GooglePhotosAuthURL(BaseModel):
    """Response schema for Google Photos authorization URL."""
    auth_url: HttpUrl
    state: Optional[str] = None


class GooglePhotosTokenExchange(BaseModel):
    """Request schema for exchanging authorization code for tokens."""
    code: str
    state: Optional[str] = None


class GooglePhotosConnection(BaseModel):
    """Schema for Google Photos connection status."""
    id: int
    user_id: int
    google_user_id: Optional[str] = None
    google_email: Optional[str] = None
    connection_date: datetime
    last_sync_date: Optional[datetime] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class GooglePhotosMediaMetadata(BaseModel):
    """Schema for Google Photos media metadata."""
    creation_time: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    photo: Optional[Dict[str, Any]] = None
    video: Optional[Dict[str, Any]] = None


class GooglePhotosMediaItem(BaseModel):
    """Schema for Google Photos media item."""
    id: str
    filename: str
    description: Optional[str] = ""
    media_type: str  # "image" or "video"
    mime_type: str
    creation_time: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    base_url: str
    product_url: Optional[str] = None
    metadata: Optional[GooglePhotosMediaMetadata] = None


class GooglePhotosAlbum(BaseModel):
    """Schema for Google Photos album."""
    id: str
    title: str
    product_url: Optional[str] = None
    is_writable: Optional[bool] = False
    media_items_count: Optional[int] = 0
    cover_photo_base_url: Optional[str] = None
    cover_photo_media_item_id: Optional[str] = None


class GooglePhotosAlbumsResponse(BaseModel):
    """Response schema for albums listing."""
    albums: List[GooglePhotosAlbum]
    next_page_token: Optional[str] = None
    total_albums: int


class GooglePhotosMediaItemsResponse(BaseModel):
    """Response schema for media items listing."""
    media_items: List[GooglePhotosMediaItem]
    next_page_token: Optional[str] = None
    total_items: int


class GooglePhotosSearchRequest(BaseModel):
    """Request schema for searching media items."""
    query: Optional[str] = None
    album_id: Optional[str] = None
    page_token: Optional[str] = None
    page_size: int = Field(default=50, le=100)
    
    # Date filters
    start_date: Optional[str] = None  # ISO format
    end_date: Optional[str] = None    # ISO format
    
    # Content filters
    content_categories: Optional[List[str]] = None  # PEOPLE, ANIMALS, PLACES, etc.
    media_types: Optional[List[str]] = None  # photo, video


class GooglePhotosSearchResponse(BaseModel):
    """Response schema for media search."""
    media_items: List[GooglePhotosMediaItem]
    next_page_token: Optional[str] = None
    total_items: int
    query: Optional[str] = None
    filters_applied: Optional[Dict[str, Any]] = None


class GooglePhotosImportRequest(BaseModel):
    """Request schema for importing media items."""
    media_item_ids: List[str]
    import_to_section: str = Field(default="raw", description="Section to import to: 'raw' or 'post-ready'")
    apply_ai_tagging: bool = Field(default=True, description="Whether to apply AI tagging to imported media")
    create_gallery: bool = Field(default=False, description="Whether to create a gallery from imported media")
    gallery_name: Optional[str] = None


class GooglePhotosImportResponse(BaseModel):
    """Response schema for import operation."""
    success: bool
    imported_count: int
    failed_count: int
    imported_media_ids: List[int]  # Crow's Eye media IDs
    failed_imports: List[Dict[str, str]]  # {google_photos_id: error_message}
    gallery_id: Optional[int] = None  # If gallery was created


class GooglePhotosImportStatus(BaseModel):
    """Schema for import operation status."""
    import_id: str
    status: str  # "pending", "in_progress", "completed", "failed"
    progress: int  # 0-100
    total_items: int
    processed_items: int
    imported_items: int
    failed_items: int
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None


class NaturalLanguageQuery(BaseModel):
    """Schema for natural language queries."""
    query: str = Field(..., description="Natural language query like 'Show me photos from Paris 2023'")
    page_token: Optional[str] = None
    page_size: int = Field(default=50, le=100)


class MediaItemImportDetails(BaseModel):
    """Detailed information about imported media item."""
    crow_eye_media_id: int
    google_photos_id: str
    filename: str
    media_type: str
    imported_at: datetime
    import_source: str = "google_photos"
    ai_tags: Optional[List[Dict[str, Any]]] = None
    gallery_ids: Optional[List[int]] = None 