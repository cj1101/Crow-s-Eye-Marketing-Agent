from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime, date

from crow_eye_api import models, schemas
from crow_eye_api.api.api_v1.dependencies import get_current_active_user, get_db

router = APIRouter()

# Mock data for demo purposes
MOCK_SCHEDULES = [
    {
        "id": "schedule_1",
        "name": "Daily Social Media",
        "description": "Automated daily posting across all platforms",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "posts_per_day": 3,
        "platforms": ["instagram", "facebook", "twitter"],
        "posting_times": ["09:00", "13:00", "18:00"],
        "is_active": True,
        "content_sources": {
            "media_library": True,
            "ai_generated": False,
            "templates": ["template_1", "template_2"]
        },
        "rules": {
            "skip_weekends": False,
            "skip_holidays": True,
            "minimum_interval": 120
        },
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "user_id": "user_1"
    }
]

MOCK_CALENDAR_EVENTS = [
    {
        "date": "2024-01-15",
        "posts": [
            {
                "id": "post_1",
                "time": "09:00",
                "caption": "Good morning! Starting the week strong 💪",
                "platforms": ["instagram", "facebook"],
                "status": "scheduled"
            },
            {
                "id": "post_2",
                "time": "13:00",
                "caption": "Lunch break inspiration ✨",
                "platforms": ["twitter"],
                "status": "scheduled"
            }
        ]
    }
]

@router.post("/", response_model=schemas.Schedule)
async def create_schedule(
    schedule: schemas.ScheduleCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new posting schedule."""
    # In demo mode, return mock data
    schedule_id = str(uuid.uuid4())
    mock_schedule = {
        "id": schedule_id,
        "user_id": str(current_user.id),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        **schedule.dict()
    }
    return schemas.Schedule(**mock_schedule)

@router.get("/", response_model=List[schemas.Schedule])
async def get_schedules(
    active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all schedules for the current user."""
    # In demo mode, return mock data
    schedules = MOCK_SCHEDULES.copy()
    if active is not None:
        schedules = [s for s in schedules if s["is_active"] == active]
    
    return [schemas.Schedule(**schedule) for schedule in schedules]

@router.get("/{schedule_id}", response_model=schemas.Schedule)
async def get_schedule(
    schedule_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific schedule by ID."""
    # In demo mode, return mock data
    for schedule in MOCK_SCHEDULES:
        if schedule["id"] == schedule_id:
            return schemas.Schedule(**schedule)
    
    raise HTTPException(status_code=404, detail="Schedule not found")

@router.put("/{schedule_id}", response_model=schemas.Schedule)
async def update_schedule(
    schedule_id: str,
    schedule_update: schemas.ScheduleUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing schedule."""
    # In demo mode, return updated mock data
    for i, schedule in enumerate(MOCK_SCHEDULES):
        if schedule["id"] == schedule_id:
            updated_data = schedule.copy()
            update_dict = schedule_update.dict(exclude_unset=True)
            updated_data.update(update_dict)
            updated_data["updated_at"] = datetime.utcnow().isoformat()
            MOCK_SCHEDULES[i] = updated_data
            return schemas.Schedule(**updated_data)
    
    raise HTTPException(status_code=404, detail="Schedule not found")

@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a schedule."""
    # In demo mode, remove from mock data
    for i, schedule in enumerate(MOCK_SCHEDULES):
        if schedule["id"] == schedule_id:
            MOCK_SCHEDULES.pop(i)
            return {"message": "Schedule deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Schedule not found")

@router.post("/{schedule_id}/toggle", response_model=schemas.Schedule)
async def toggle_schedule_status(
    schedule_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Toggle the active status of a schedule."""
    # In demo mode, toggle mock data
    for i, schedule in enumerate(MOCK_SCHEDULES):
        if schedule["id"] == schedule_id:
            MOCK_SCHEDULES[i]["is_active"] = not schedule["is_active"]
            MOCK_SCHEDULES[i]["updated_at"] = datetime.utcnow().isoformat()
            return schemas.Schedule(**MOCK_SCHEDULES[i])
    
    raise HTTPException(status_code=404, detail="Schedule not found")

@router.get("/calendar", response_model=schemas.ScheduleCalendar)
async def get_scheduled_posts_calendar(
    start: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: date = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get scheduled posts in calendar format for a date range."""
    # In demo mode, return mock calendar data
    return schemas.ScheduleCalendar(events=MOCK_CALENDAR_EVENTS) 