from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from .user import User, UserCreate, UserUpdate, Token, TokenData
from .media import (
    MediaItem, MediaItemCreate, MediaItemUpdate, MediaItemResponse,
    MediaSearch, MediaSearchResponse, AITag, MediaUploadResponse,
    MediaEditRequest, MediaEditResponse, MediaEditStatusResponse, MediaEditFormattingOptions
)
from .gallery import (
    Gallery, GalleryCreate, GalleryUpdate, GalleryResponse,
    GalleryGenerate, GalleryGenerateResponse
)
from .caption import (
    CaptionGenerate, CaptionGenerateResponse
)
from .highlight import (
    HighlightGenerate, HighlightGenerateResponse
)
from .posts import (
    PostCreate, PostUpdate, PostResponse, FormattingOptions,
    PostsListResponse, BulkScheduleRequest, BulkUpdateRequest, BulkDeleteRequest,
    MediaProcessingRequest, MediaOptimizationRequest, GenerateContentRequest,
    PlatformOptimizationRequest, CalendarEvent, CalendarResponse
)
from .platforms import (
    PlatformRequirementsResponse
)
from .context_files import (
    ContextFileCreate, ContextFileResponse
)
from .schedule import (
    Schedule, ScheduleCreate, ScheduleUpdate, ScheduleCalendar, ScheduleCalendarEvent,
    ScheduleContentSources, ScheduleRules
)
from .template import (
    Template, TemplateCreate, TemplateUpdate, TemplateApplyRequest, TemplateApplyResponse,
    TemplateVariable, TemplateContent
)
from .analytics import (
    Analytics, PostAnalytics, PlatformAnalytics, AnalyticsSummary,
    EngagementTrend, TrendsResponse, AnalyticsRequest
)
from .ai_services import (
    ImageGenerateRequest, ImageGenerateResponse,
    VideoGenerateRequest, VideoGenerateResponse,
    ContentIdeasRequest, ContentIdeasResponse,
    HashtagGenerateRequest, HashtagGenerateResponse,
    BulkUploadRequest, BulkUploadResponse,
    BulkScheduleRequest, BulkScheduleResponse,
    JobStatusResponse, PreviewGenerateRequest, PreviewGenerateResponse,
    PreviewResponse, VideoProcessingRequest, VideoProcessingResponse,
    PerformanceAnalyticsRequest, PerformanceAnalyticsResponse,
    ThumbnailGenerateRequest, ThumbnailGenerateResponse
)

# Platform Compliance Schemas
class PlatformValidationRequest(BaseModel):
    """Request schema for platform validation."""
    platform: str = Field(..., description="Platform name")
    content_type: str = Field(..., description="Content type")
    caption: Optional[str] = None
    media_url: Optional[str] = None
    media_size_mb: Optional[float] = None
    media_duration_seconds: Optional[int] = None
    media_resolution: Optional[str] = None
    media_format: Optional[str] = None
    hashtags: List[str] = []
    mentions: List[str] = []


class PlatformValidationResponse(BaseModel):
    """Response schema for platform validation."""
    platform: str
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []
    compliance_score: float = 100.0
    optimization_tips: List[str] = []


class BulkPlatformValidationRequest(BaseModel):
    """Request schema for validating content across multiple platforms."""
    platforms: List[str] = Field(..., description="List of platform names")
    content_type: str = Field(..., description="Content type")
    caption: Optional[str] = None
    media_url: Optional[str] = None
    media_size_mb: Optional[float] = None
    media_duration_seconds: Optional[int] = None
    media_resolution: Optional[str] = None
    media_format: Optional[str] = None
    hashtags: List[str] = []
    mentions: List[str] = []


class BulkPlatformValidationResponse(BaseModel):
    """Response schema for bulk platform validation."""
    overall_score: float
    platform_results: Dict[str, PlatformValidationResponse]
    cross_platform_suggestions: List[str] = []
    recommended_platforms: List[str] = []

# Add new schemas for enhanced AI functionality
class HashtagGenerateRequest(BaseModel):
    content: str
    platforms: List[str]
    niche: str
    count: int = 10

class HashtagGenerateResponse(BaseModel):
    hashtags: List[str]
    total: int
    platform_optimized: bool
    niche: str

class ContentSuggestionsRequest(BaseModel):
    media_id: str
    platforms: List[str]
    content_type: str = "caption"
    variations: int = 3

class ContentSuggestionsResponse(BaseModel):
    suggestions: List[Dict[str, Any]]
    media_id: str
    content_type: str
    platforms: List[str]

__all__ = [
    "User", "UserCreate", "UserUpdate", "Token", "TokenData",
    "MediaItem", "MediaItemCreate", "MediaItemUpdate", "MediaItemResponse",
    "MediaSearch", "MediaSearchResponse", "AITag", "MediaUploadResponse",
    "MediaEditRequest", "MediaEditResponse", "MediaEditStatusResponse", "MediaEditFormattingOptions",
    "Gallery", "GalleryCreate", "GalleryUpdate", "GalleryResponse",
    "GalleryGenerate", "GalleryGenerateResponse",
    "CaptionGenerate", "CaptionGenerateResponse",
    "HighlightGenerate", "HighlightGenerateResponse",
    "PostCreate", "PostUpdate", "PostResponse", "FormattingOptions",
    "PostsListResponse", "BulkScheduleRequest", "BulkUpdateRequest", "BulkDeleteRequest",
    "MediaProcessingRequest", "MediaOptimizationRequest", "GenerateContentRequest",
    "PlatformOptimizationRequest", "CalendarEvent", "CalendarResponse",
    "PlatformRequirementsResponse",
    "ContextFileCreate", "ContextFileResponse",
    "Schedule", "ScheduleCreate", "ScheduleUpdate", "ScheduleCalendar", "ScheduleCalendarEvent",
    "ScheduleContentSources", "ScheduleRules",
    "Template", "TemplateCreate", "TemplateUpdate", "TemplateApplyRequest", "TemplateApplyResponse",
    "TemplateVariable", "TemplateContent",
    "Analytics", "PostAnalytics", "PlatformAnalytics", "AnalyticsSummary",
    "EngagementTrend", "TrendsResponse", "AnalyticsRequest",
    "HashtagGenerateRequest", "HashtagGenerateResponse",
    "ContentSuggestionsRequest", "ContentSuggestionsResponse",
    "ImageGenerateRequest", "ImageGenerateResponse",
    "VideoGenerateRequest", "VideoGenerateResponse",
    "ContentIdeasRequest", "ContentIdeasResponse",
    "BulkUploadRequest", "BulkUploadResponse",
    "BulkScheduleRequest", "BulkScheduleResponse",
    "JobStatusResponse", "PreviewGenerateRequest", "PreviewGenerateResponse",
    "PreviewResponse", "VideoProcessingRequest", "VideoProcessingResponse",
    "PerformanceAnalyticsRequest", "PerformanceAnalyticsResponse",
    "ThumbnailGenerateRequest", "ThumbnailGenerateResponse",
    "PlatformValidationRequest", "PlatformValidationResponse",
    "BulkPlatformValidationRequest", "BulkPlatformValidationResponse"
] 