from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
import random
from datetime import datetime, date, timedelta
from dateutil import tz

from crow_eye_api import models, schemas
from crow_eye_api.api.api_v1.dependencies import get_current_active_user, get_db

router = APIRouter()

# Helper functions for campaign management
def calculate_posting_schedule(
    campaign: dict,
    start_date: datetime,
    end_date: datetime
) -> List[datetime]:
    """Calculate all posting times for a campaign based on its rules."""
    posting_times = []
    current_date = start_date.date()
    end_date_only = end_date.date()
    
    campaign_times = campaign.get("posting_times", ["09:00"])
    posts_per_day = campaign.get("posts_per_day", 1)
    skip_weekends = campaign.get("skip_weekends", False)
    minimum_interval = campaign.get("minimum_interval_minutes", 60)
    randomize_times = campaign.get("randomize_times", False)
    
    while current_date <= end_date_only:
        # Skip weekends if configured
        if skip_weekends and current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            current_date += timedelta(days=1)
            continue
        
        # Generate posting times for this day
        day_times = []
        for i in range(posts_per_day):
            if i < len(campaign_times):
                time_str = campaign_times[i]
            else:
                # Distribute remaining posts evenly
                base_hour = 9 + (i * 2) % 12
                time_str = f"{base_hour:02d}:00"
            
            hour, minute = map(int, time_str.split(':'))
            
            # Add randomization if enabled
            if randomize_times:
                hour += random.randint(-1, 1)
                minute += random.randint(-30, 30)
                hour = max(6, min(22, hour))  # Keep between 6 AM and 10 PM
                minute = max(0, min(59, minute))
            
            post_time = datetime.combine(current_date, datetime.min.time().replace(hour=hour, minute=minute))
            day_times.append(post_time)
        
        # Sort day times and ensure minimum interval
        day_times.sort()
        filtered_times = []
        last_time = None
        
        for post_time in day_times:
            if last_time is None or (post_time - last_time).total_seconds() >= minimum_interval * 60:
                filtered_times.append(post_time)
                last_time = post_time
        
        posting_times.extend(filtered_times)
        current_date += timedelta(days=1)
    
    return posting_times

# Campaign CRUD Operations
@router.post("/", response_model=schemas.Campaign)
async def create_campaign(
    campaign: schemas.CampaignCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new campaign with comprehensive scheduling features."""
    campaign_id = str(uuid.uuid4())
    
    # Calculate total posts planned
    posting_times = calculate_posting_schedule(
        campaign.dict(),
        campaign.start_date,
        campaign.end_date
    )
    
    mock_campaign = {
        "id": campaign_id,
        "user_id": current_user.id,
        "status": "draft",
        "total_posts_planned": len(posting_times),
        "total_posts_published": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        **campaign.dict()
    }
    
    return schemas.Campaign(**mock_campaign)

@router.get("/", response_model=List[schemas.Campaign])
async def get_campaigns(
    status: Optional[schemas.CampaignStatus] = Query(None, description="Filter by campaign status"),
    active_only: bool = Query(False, description="Show only active campaigns"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all campaigns for the current user."""
    # Mock campaigns data
    mock_campaigns = [
        {
            "id": "campaign_1",
            "name": "Daily Social Media Blitz",
            "description": "High-frequency posting across all platforms",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=30),
            "timezone": "UTC",
            "posts_per_day": 3,
            "posting_times": ["09:00", "13:00", "18:00"],
            "platforms": ["instagram", "facebook", "twitter", "linkedin"],
            "skip_weekends": False,
            "skip_holidays": True,
            "minimum_interval_minutes": 120,
            "randomize_times": False,
            "randomize_order": False,
            "content_sources": {"media_library": True, "ai_generated": True},
            "auto_generate_content": True,
            "content_themes": ["business", "motivation", "tips"],
            "status": "active",
            "total_posts_planned": 90,
            "total_posts_published": 15,
            "created_at": datetime.now() - timedelta(days=5),
            "updated_at": datetime.now(),
            "user_id": current_user.id
        },
        {
            "id": "campaign_2",
            "name": "Product Launch Campaign",
            "description": "Focused campaign for new product announcement",
            "start_date": datetime.now() + timedelta(days=7),
            "end_date": datetime.now() + timedelta(days=21),
            "timezone": "UTC",
            "posts_per_day": 2,
            "posting_times": ["10:00", "16:00"],
            "platforms": ["instagram", "facebook", "linkedin"],
            "skip_weekends": True,
            "skip_holidays": True,
            "minimum_interval_minutes": 360,
            "randomize_times": True,
            "randomize_order": False,
            "content_sources": {"media_library": True, "ai_generated": False},
            "auto_generate_content": False,
            "content_themes": ["product", "launch", "announcement"],
            "status": "draft",
            "total_posts_planned": 20,
            "total_posts_published": 0,
            "created_at": datetime.now() - timedelta(days=2),
            "updated_at": datetime.now(),
            "user_id": current_user.id
        }
    ]
    
    # Apply filters
    if status:
        mock_campaigns = [c for c in mock_campaigns if c["status"] == status.value]
    
    if active_only:
        mock_campaigns = [c for c in mock_campaigns if c["status"] == "active"]
    
    return [schemas.Campaign(**campaign) for campaign in mock_campaigns]

@router.get("/{campaign_id}", response_model=schemas.CampaignWithPosts)
async def get_campaign(
    campaign_id: str,
    include_posts: bool = Query(True, description="Include scheduled posts"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific campaign with its scheduled posts."""
    # Mock campaign data
    mock_campaign = {
        "id": campaign_id,
        "name": "Daily Social Media Blitz",
        "description": "High-frequency posting across all platforms",
        "start_date": datetime.now(),
        "end_date": datetime.now() + timedelta(days=30),
        "timezone": "UTC",
        "posts_per_day": 3,
        "posting_times": ["09:00", "13:00", "18:00"],
        "platforms": ["instagram", "facebook", "twitter"],
        "skip_weekends": False,
        "skip_holidays": True,
        "minimum_interval_minutes": 120,
        "randomize_times": False,
        "randomize_order": False,
        "content_sources": {"media_library": True, "ai_generated": True},
        "auto_generate_content": True,
        "content_themes": ["business", "motivation"],
        "status": "active",
        "total_posts_planned": 90,
        "total_posts_published": 15,
        "created_at": datetime.now() - timedelta(days=5),
        "updated_at": datetime.now(),
        "user_id": current_user.id
    }
    
    scheduled_posts = []
    if include_posts:
        # Generate mock scheduled posts
        for i in range(10):  # Show next 10 posts
            post_time = datetime.now() + timedelta(hours=i*8)
            scheduled_posts.append({
                "id": f"post_{i+1}",
                "campaign_id": campaign_id,
                "caption": f"Engaging post #{i+1} for your audience! 🚀",
                "hashtags": ["business", "motivation", "success"],
                "media_urls": [f"https://example.com/media_{i+1}.jpg"],
                "media_types": ["image"],
                "scheduled_time": post_time,
                "platforms": ["instagram", "facebook"],
                "is_manually_scheduled": i % 3 == 0,  # Some manually scheduled
                "campaign_position": i + 1,
                "is_ai_generated": True,
                "generation_prompt": "Create engaging business content",
                "context_files": [],
                "status": "scheduled" if i > 2 else "published",
                "published_at": post_time - timedelta(hours=1) if i <= 2 else None,
                "error_message": None,
                "retry_count": 0,
                "platform_post_ids": {"instagram": f"ig_post_{i+1}", "facebook": f"fb_post_{i+1}"} if i <= 2 else {},
                "created_at": datetime.now() - timedelta(days=1),
                "updated_at": datetime.now(),
                "user_id": current_user.id
            })
    
    mock_campaign["scheduled_posts"] = scheduled_posts
    return schemas.CampaignWithPosts(**mock_campaign)

@router.put("/{campaign_id}", response_model=schemas.Campaign)
async def update_campaign(
    campaign_id: str,
    campaign_update: schemas.CampaignUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing campaign."""
    # Mock update
    mock_campaign = {
        "id": campaign_id,
        "name": "Updated Campaign Name",
        "description": "Updated description",
        "start_date": datetime.now(),
        "end_date": datetime.now() + timedelta(days=30),
        "timezone": "UTC",
        "posts_per_day": 3,
        "posting_times": ["09:00", "13:00", "18:00"],
        "platforms": ["instagram", "facebook", "twitter"],
        "skip_weekends": False,
        "skip_holidays": True,
        "minimum_interval_minutes": 120,
        "randomize_times": False,
        "randomize_order": False,
        "content_sources": {"media_library": True, "ai_generated": True},
        "auto_generate_content": True,
        "content_themes": ["business", "motivation"],
        "status": "active",
        "total_posts_planned": 90,
        "total_posts_published": 15,
        "created_at": datetime.now() - timedelta(days=5),
        "updated_at": datetime.now(),
        "user_id": current_user.id
    }
    
    # Apply updates
    update_dict = campaign_update.dict(exclude_unset=True)
    mock_campaign.update(update_dict)
    
    return schemas.Campaign(**mock_campaign)

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a campaign and all its scheduled posts."""
    return {"message": "Campaign deleted successfully", "campaign_id": campaign_id}

@router.post("/{campaign_id}/toggle", response_model=schemas.Campaign)
async def toggle_campaign_status(
    campaign_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle campaign between active/paused status."""
    mock_campaign = {
        "id": campaign_id,
        "name": "Daily Social Media Blitz",
        "description": "High-frequency posting across all platforms",
        "start_date": datetime.now(),
        "end_date": datetime.now() + timedelta(days=30),
        "timezone": "UTC",
        "posts_per_day": 3,
        "posting_times": ["09:00", "13:00", "18:00"],
        "platforms": ["instagram", "facebook", "twitter"],
        "skip_weekends": False,
        "skip_holidays": True,
        "minimum_interval_minutes": 120,
        "randomize_times": False,
        "randomize_order": False,
        "content_sources": {"media_library": True, "ai_generated": True},
        "auto_generate_content": True,
        "content_themes": ["business", "motivation"],
        "status": "paused",  # Toggled status
        "total_posts_planned": 90,
        "total_posts_published": 15,
        "created_at": datetime.now() - timedelta(days=5),
        "updated_at": datetime.now(),
        "user_id": current_user.id
    }
    
    return schemas.Campaign(**mock_campaign)

# Calendar Functionality
@router.get("/calendar", response_model=schemas.CampaignCalendar)
async def get_campaign_calendar(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    campaign_ids: Optional[List[str]] = Query(None, description="Filter by specific campaign IDs"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get calendar view of all scheduled posts across campaigns."""
    calendar_days = []
    current_date = start_date
    total_posts = 0
    
    while current_date <= end_date:
        # Mock posts for each day
        day_posts = []
        posts_count = random.randint(0, 4)  # 0-4 posts per day
        
        for i in range(posts_count):
            post_time = f"{9 + i*3}:00"  # 9:00, 12:00, 15:00, 18:00
            day_posts.append({
                "id": f"post_{current_date}_{i}",
                "campaign_id": f"campaign_{(i % 2) + 1}",
                "campaign_name": f"Campaign {(i % 2) + 1}",
                "time": post_time,
                "caption": f"Scheduled post for {current_date}",
                "platforms": ["instagram", "facebook"],
                "status": "scheduled",
                "is_manually_scheduled": i % 2 == 0,
                "media_count": random.randint(1, 3)
            })
        
        calendar_days.append({
            "date": current_date,
            "posts": day_posts,
            "total_posts": len(day_posts)
        })
        
        total_posts += len(day_posts)
        current_date += timedelta(days=1)
    
    return schemas.CampaignCalendar(
        start_date=start_date,
        end_date=end_date,
        days=calendar_days,
        total_posts=total_posts
    )

# Analytics
@router.get("/analytics", response_model=schemas.CampaignAnalytics)
async def get_campaign_analytics(
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics overview for all campaigns."""
    mock_analytics = {
        "campaigns": [
            {
                "campaign_id": "campaign_1",
                "campaign_name": "Daily Social Media Blitz",
                "total_posts_planned": 90,
                "total_posts_published": 15,
                "total_posts_failed": 2,
                "posts_this_week": 12,
                "posts_this_month": 45,
                "completion_percentage": 16.7,
                "avg_posts_per_day": 2.1,
                "next_post_time": datetime.now() + timedelta(hours=4),
                "status": "active"
            },
            {
                "campaign_id": "campaign_2",
                "campaign_name": "Product Launch Campaign",
                "total_posts_planned": 20,
                "total_posts_published": 0,
                "total_posts_failed": 0,
                "posts_this_week": 0,
                "posts_this_month": 0,
                "completion_percentage": 0.0,
                "avg_posts_per_day": 0.0,
                "next_post_time": datetime.now() + timedelta(days=7),
                "status": "draft"
            }
        ],
        "total_active_campaigns": 1,
        "total_posts_this_week": 12,
        "total_posts_this_month": 45,
        "most_active_campaign": "Daily Social Media Blitz"
    }
    
    return schemas.CampaignAnalytics(**mock_analytics)

@router.get("/{campaign_id}/calendar", response_model=schemas.CampaignCalendar)
async def get_single_campaign_calendar(
    campaign_id: str,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get calendar view for a specific campaign."""
    calendar_days = []
    current_date = start_date
    total_posts = 0
    
    while current_date <= end_date:
        # Mock posts for specific campaign
        day_posts = []
        if current_date.weekday() < 5:  # Weekdays only for this campaign
            posts_count = 2  # 2 posts per weekday
            
            for i in range(posts_count):
                post_time = f"{10 + i*6}:00"  # 10:00, 16:00
                day_posts.append({
                    "id": f"post_{campaign_id}_{current_date}_{i}",
                    "campaign_id": campaign_id,
                    "campaign_name": "Daily Social Media Blitz",
                    "time": post_time,
                    "caption": f"Campaign post for {current_date}",
                    "platforms": ["instagram", "facebook", "twitter"],
                    "status": "scheduled",
                    "is_manually_scheduled": False,
                    "media_count": 1
                })
        
        calendar_days.append({
            "date": current_date,
            "posts": day_posts,
            "total_posts": len(day_posts)
        })
        
        total_posts += len(day_posts)
        current_date += timedelta(days=1)
    
    return schemas.CampaignCalendar(
        start_date=start_date,
        end_date=end_date,
        days=calendar_days,
        total_posts=total_posts
    )

# Queue Management
@router.get("/{campaign_id}/queue", response_model=schemas.CampaignQueue)
async def get_campaign_queue(
    campaign_id: str,
    limit: int = Query(50, description="Maximum number of posts to return"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the posting queue for a specific campaign."""
    # Mock queue data
    queue_posts = []
    for i in range(min(limit, 20)):  # Return up to 20 mock posts
        post_time = datetime.now() + timedelta(hours=i*4)
        queue_posts.append({
            "id": f"queue_post_{i+1}",
            "campaign_id": campaign_id,
            "campaign_name": "Daily Social Media Blitz",
            "caption": f"Queued post #{i+1} ready to go! 🎯",
            "hashtags": ["business", "growth", "success"],
            "media_urls": [f"https://example.com/queue_media_{i+1}.jpg"],
            "platforms": ["instagram", "facebook"],
            "scheduled_time": post_time,
            "status": "queued" if i > 5 else "scheduled",
            "position_in_queue": i + 1,
            "is_manually_scheduled": i % 4 == 0,
            "created_at": datetime.now() - timedelta(hours=i)
        })
    
    next_post_time = queue_posts[0]["scheduled_time"] if queue_posts else None
    
    return schemas.CampaignQueue(
        campaign_id=campaign_id,
        campaign_name="Daily Social Media Blitz",
        posts=queue_posts,
        total_queued=len([p for p in queue_posts if p["status"] == "queued"]),
        next_post_time=next_post_time
    )

# Post Management within Campaigns
@router.post("/{campaign_id}/posts", response_model=schemas.ScheduledPost)
async def add_post_to_campaign(
    campaign_id: str,
    post: schemas.ScheduledPostCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a new post to a campaign."""
    post_id = str(uuid.uuid4())
    
    mock_post = {
        "id": post_id,
        "campaign_id": campaign_id,
        "status": "scheduled",
        "published_at": None,
        "error_message": None,
        "retry_count": 0,
        "platform_post_ids": {},
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "user_id": current_user.id,
        **post.dict()
    }
    
    return schemas.ScheduledPost(**mock_post)

@router.put("/{campaign_id}/posts/{post_id}", response_model=schemas.ScheduledPost)
async def update_campaign_post(
    campaign_id: str,
    post_id: str,
    post_update: schemas.ScheduledPostUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a specific post within a campaign."""
    mock_post = {
        "id": post_id,
        "campaign_id": campaign_id,
        "caption": "Updated caption content",
        "hashtags": ["updated", "content"],
        "media_urls": ["https://example.com/updated_media.jpg"],
        "media_types": ["image"],
        "scheduled_time": datetime.now() + timedelta(hours=2),
        "platforms": ["instagram", "facebook"],
        "is_manually_scheduled": True,
        "campaign_position": 1,
        "is_ai_generated": False,
        "generation_prompt": None,
        "context_files": [],
        "status": "scheduled",
        "published_at": None,
        "error_message": None,
        "retry_count": 0,
        "platform_post_ids": {},
        "created_at": datetime.now() - timedelta(hours=1),
        "updated_at": datetime.now(),
        "user_id": current_user.id
    }
    
    # Apply updates
    update_dict = post_update.dict(exclude_unset=True)
    mock_post.update(update_dict)
    
    return schemas.ScheduledPost(**mock_post)

@router.delete("/{campaign_id}/posts/{post_id}")
async def delete_campaign_post(
    campaign_id: str,
    post_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific post from a campaign."""
    return {"message": "Post deleted successfully", "post_id": post_id}

# Bulk Operations
@router.post("/{campaign_id}/bulk-schedule", response_model=List[schemas.ScheduledPost])
async def bulk_schedule_posts(
    campaign_id: str,
    bulk_request: schemas.BulkCampaignSchedule,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Bulk schedule multiple posts for a campaign."""
    scheduled_posts = []
    
    for i, post_data in enumerate(bulk_request.posts):
        post_id = str(uuid.uuid4())
        
        # Auto-schedule if requested
        if bulk_request.auto_schedule and not post_data.scheduled_time:
            # Calculate next available time slot
            scheduled_time = datetime.now() + timedelta(hours=(i+1)*4)
        else:
            scheduled_time = post_data.scheduled_time or datetime.now() + timedelta(hours=1)
        
        mock_post = {
            "id": post_id,
            "campaign_id": campaign_id,
            "caption": post_data.caption,
            "hashtags": post_data.hashtags,
            "media_urls": post_data.media_urls,
            "media_types": post_data.media_types,
            "scheduled_time": scheduled_time,
            "platforms": post_data.platforms,
            "is_manually_scheduled": not bulk_request.auto_schedule,
            "campaign_position": i + 1,
            "is_ai_generated": bool(post_data.generation_prompt),
            "generation_prompt": post_data.generation_prompt,
            "context_files": post_data.context_files,
            "status": "scheduled",
            "published_at": None,
            "error_message": None,
            "retry_count": 0,
            "platform_post_ids": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "user_id": current_user.id
        }
        
        scheduled_posts.append(schemas.ScheduledPost(**mock_post))
    
    return scheduled_posts

 