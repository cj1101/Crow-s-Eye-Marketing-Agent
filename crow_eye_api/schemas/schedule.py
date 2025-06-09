from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date

class ScheduleContentSources(BaseModel):
    media_library: bool = True
    ai_generated: bool = False
    templates: List[str] = []

class ScheduleRules(BaseModel):
    skip_weekends: bool = False
    skip_holidays: bool = False
    minimum_interval: int = 60  # minutes

class ScheduleBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    posts_per_day: int
    platforms: List[str]
    posting_times: List[str]  # HH:MM format
    is_active: bool = True
    content_sources: ScheduleContentSources
    rules: ScheduleRules

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    posts_per_day: Optional[int] = None
    platforms: Optional[List[str]] = None
    posting_times: Optional[List[str]] = None
    is_active: Optional[bool] = None
    content_sources: Optional[ScheduleContentSources] = None
    rules: Optional[ScheduleRules] = None

class Schedule(ScheduleBase):
    id: str
    created_at: datetime
    updated_at: datetime
    user_id: str

    class Config:
        from_attributes = True

class ScheduleCalendarEvent(BaseModel):
    date: date
    posts: List[Dict[str, Any]]

class ScheduleCalendar(BaseModel):
    events: List[ScheduleCalendarEvent] 