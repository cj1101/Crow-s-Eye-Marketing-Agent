from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# Image Generation (Imagen 3)
class ImageGenerateRequest(BaseModel):
    """Schema for AI image generation requests."""
    prompt: str = Field(..., description="Text prompt for image generation")
    style: str = Field(default="photorealistic", description="Style: photorealistic, artistic, cartoon, etc.")
    aspect_ratio: str = Field(default="1:1", description="Aspect ratio: 1:1, 16:9, 4:5, etc.")
    quality: str = Field(default="standard", description="Quality: standard, hd")
    count: int = Field(default=1, description="Number of images to generate", ge=1, le=4)


class ImageGenerateResponse(BaseModel):
    """Schema for AI image generation responses."""
    images: List[Dict[str, Any]]
    generation_time: float
    total_cost: float
    prompt_used: str
    style_applied: str


# Video Generation (Veo)
class VideoGenerateRequest(BaseModel):
    """Schema for AI video generation requests."""
    prompt: str = Field(..., description="Text prompt for video generation")
    duration: int = Field(default=5, description="Video duration in seconds", ge=2, le=30)
    style: str = Field(default="cinematic", description="Video style")
    aspect_ratio: str = Field(default="16:9", description="Aspect ratio")
    fps: int = Field(default=24, description="Frames per second")


class VideoGenerateResponse(BaseModel):
    """Schema for AI video generation responses."""
    video_url: str
    video_id: str
    duration: float
    generation_time: float
    total_cost: float
    metadata: Dict[str, Any]


# Content Ideas
class ContentIdeasRequest(BaseModel):
    """Schema for AI content ideas generation."""
    topic: Optional[str] = Field(None, description="Topic or theme")
    platform: str = Field(..., description="Target platform")
    content_type: str = Field(default="post", description="Type of content")
    audience: Optional[str] = Field(None, description="Target audience description")
    brand_voice: Optional[str] = Field(None, description="Brand voice/tone")
    count: int = Field(default=5, description="Number of ideas to generate", ge=1, le=20)


class ContentIdeasResponse(BaseModel):
    """Schema for AI content ideas responses."""
    ideas: List[Dict[str, Any]]
    total: int
    platform: str
    content_type: str
    generation_metadata: Dict[str, Any]


# Enhanced Hashtag Generation
class HashtagGenerateRequest(BaseModel):
    """Schema for enhanced hashtag generation."""
    content: str = Field(..., description="Content to generate hashtags for")
    platforms: List[str] = Field(..., description="Target platforms")
    niche: Optional[str] = Field(None, description="Content niche/category")
    count: int = Field(default=10, description="Number of hashtags", ge=5, le=30)
    trending: bool = Field(default=True, description="Include trending hashtags")


class HashtagGenerateResponse(BaseModel):
    """Schema for hashtag generation responses."""
    hashtags: List[str]
    trending_hashtags: List[str]
    niche_hashtags: List[str]
    total: int
    platform_optimized: Dict[str, List[str]]
    niche: Optional[str]


# Bulk Operations
class BulkUploadRequest(BaseModel):
    """Schema for bulk upload requests."""
    files: List[Dict[str, Any]]
    folder_path: Optional[str] = None
    auto_process: bool = Field(default=False)
    processing_options: Optional[Dict[str, Any]] = None


class BulkUploadResponse(BaseModel):
    """Schema for bulk upload responses."""
    job_id: str
    status: str
    total_files: int
    processed_files: int
    failed_files: int
    uploaded_media: List[Dict[str, Any]]


class BulkScheduleRequest(BaseModel):
    """Schema for bulk scheduling requests."""
    posts: List[Dict[str, Any]]
    schedule_options: Dict[str, Any]
    platforms: List[str]


class BulkScheduleResponse(BaseModel):
    """Schema for bulk scheduling responses."""
    job_id: str
    status: str
    scheduled_count: int
    failed_count: int
    schedule_details: List[Dict[str, Any]]


class JobStatusResponse(BaseModel):
    """Schema for job status responses."""
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: float  # 0.0 to 100.0
    total_items: int
    processed_items: int
    failed_items: int
    estimated_completion: Optional[str]
    results: Optional[Dict[str, Any]]


# Platform Previews
class PreviewGenerateRequest(BaseModel):
    """Schema for platform preview generation."""
    content: Dict[str, Any]
    platforms: List[str]
    preview_type: str = Field(default="post", description="Type of preview")


class PreviewGenerateResponse(BaseModel):
    """Schema for platform preview responses."""
    preview_id: str
    previews: Dict[str, Dict[str, Any]]  # platform -> preview data
    expiry_time: str
    total_platforms: int


class PreviewResponse(BaseModel):
    """Schema for individual preview responses."""
    preview_id: str
    platform: str
    preview_data: Dict[str, Any]
    generated_at: str
    expires_at: str


# Video Processing
class VideoProcessingRequest(BaseModel):
    """Schema for video processing requests."""
    video_id: str
    operations: List[Dict[str, Any]]
    output_format: str = Field(default="mp4")
    quality: str = Field(default="1080p")


class VideoProcessingResponse(BaseModel):
    """Schema for video processing responses."""
    job_id: str
    status: str
    processed_video_url: Optional[str]
    estimated_time: int
    operations_applied: List[str]


# Analytics Enhancement
class PerformanceAnalyticsRequest(BaseModel):
    """Schema for performance analytics requests."""
    platform: Optional[str] = None
    date_range: Dict[str, str]
    metrics: List[str]
    content_type: Optional[str] = None


class PerformanceAnalyticsResponse(BaseModel):
    """Schema for performance analytics responses."""
    platform: Optional[str]
    date_range: Dict[str, str]
    metrics: Dict[str, Any]
    trends: List[Dict[str, Any]]
    insights: List[str]
    total_posts: int


# Thumbnail Generation
class ThumbnailGenerateRequest(BaseModel):
    """Schema for thumbnail generation requests."""
    video_id: str
    timestamp: Optional[float] = None
    count: int = Field(default=3, description="Number of thumbnails", ge=1, le=10)
    style: str = Field(default="auto", description="Thumbnail style")


class ThumbnailGenerateResponse(BaseModel):
    """Schema for thumbnail generation responses."""
    thumbnails: List[Dict[str, Any]]
    video_id: str
    total_generated: int
    best_thumbnail: Dict[str, Any] 