from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from .analytics import PostAnalytics

class FormattingOptions(BaseModel):
    vertical_optimization: bool = False
    caption_overlay: bool = False
    overlay_position: str = Field(default="bottom", pattern="^(top|center|bottom)$")
    overlay_font_size: str = Field(default="medium", pattern="^(small|medium|large)$")
    aspect_ratio: str = Field(default="original", pattern="^(original|1:1|4:5|16:9|9:16)$")

class PostCreate(BaseModel):
    media_id: str
    caption: str
    platforms: List[str]
    custom_instructions: Optional[str] = None
    formatting: Optional[FormattingOptions] = None
    context_files: Optional[List[str]] = Field(default_factory=list)
    scheduled_time: Optional[datetime] = None
    is_recurring: bool = False
    recurring_pattern: Optional[str] = Field(None, pattern="^(daily|weekly|monthly)$")
    recurring_end_date: Optional[datetime] = None

class PostUpdate(BaseModel):
    caption: Optional[str] = None
    custom_instructions: Optional[str] = None
    platforms: Optional[List[str]] = None
    formatting: Optional[FormattingOptions] = None
    context_files: Optional[List[str]] = None
    scheduled_time: Optional[datetime] = None
    is_recurring: Optional[bool] = None
    recurring_pattern: Optional[str] = None
    recurring_end_date: Optional[datetime] = None

class PostResponse(BaseModel):
    id: str
    media_id: str
    caption: str
    platforms: List[str]
    status: str
    created_at: datetime
    updated_at: datetime
    scheduled_time: Optional[datetime] = None
    published_time: Optional[datetime] = None
    media_type: str
    media_url: str
    is_recurring: bool
    recurring_pattern: Optional[str] = None
    custom_instructions: Optional[str] = None
    formatting: Optional[Dict[str, Any]] = None
    context_files: List[str]
    analytics: Optional[PostAnalytics] = None

    class Config:
        from_attributes = True

class PostsListResponse(BaseModel):
    posts: List[PostResponse]
    total: int
    has_more: bool

class BulkScheduleRequest(BaseModel):
    posts: List[PostCreate]
    schedule_settings: Optional[Dict[str, Any]] = None

class BulkUpdateRequest(BaseModel):
    post_ids: List[str]
    updates: PostUpdate

class BulkDeleteRequest(BaseModel):
    post_ids: List[str]

class MediaProcessingRequest(BaseModel):
    instructions: str
    output_format: str = Field(pattern="^(image|video)$")
    platforms: List[str]
    formatting: Optional[FormattingOptions] = None

class MediaOptimizationRequest(BaseModel):
    platforms: List[str]
    variations: Optional[Dict[str, Any]] = None

class CalendarEvent(BaseModel):
    date: str
    posts: List[Dict[str, Any]]

class CalendarResponse(BaseModel):
    events: List[CalendarEvent]

class GenerateContentRequest(BaseModel):
    regenerate_caption: bool = True
    regenerate_instructions: bool = False
    keep_existing: bool = False

class PlatformOptimizationRequest(BaseModel):
    platforms: List[str]
    auto_format: bool = True 