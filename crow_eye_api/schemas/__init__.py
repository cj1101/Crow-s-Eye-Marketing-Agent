from typing import List, Dict, Any
from pydantic import BaseModel

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
    "ContentSuggestionsRequest", "ContentSuggestionsResponse"
] 