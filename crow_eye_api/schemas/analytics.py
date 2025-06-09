from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date

class PostAnalytics(BaseModel):
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    engagement_rate: float = 0.0

class Analytics(BaseModel):
    id: str
    post_id: str
    platform: str
    views: int
    likes: int
    comments: int
    shares: int
    engagement_rate: float
    additional_metrics: Optional[Dict[str, Any]] = None
    recorded_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PlatformAnalytics(BaseModel):
    platform: str
    posts: int
    total_views: int
    total_likes: int
    total_comments: int
    total_shares: int
    engagement_rate: float
    top_performing_post: Optional[Dict[str, Any]] = None

class AnalyticsSummary(BaseModel):
    platforms: List[PlatformAnalytics]
    summary: Dict[str, Any]

class EngagementTrend(BaseModel):
    date: date
    views: int
    likes: int
    comments: int
    shares: int
    engagement_rate: float

class TrendsResponse(BaseModel):
    period: str
    platform: Optional[str] = None
    trends: List[EngagementTrend]

class AnalyticsRequest(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    platform: Optional[str] = None 