from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta

from crow_eye_api import models, schemas
from crow_eye_api.api.api_v1.dependencies import get_current_active_user, get_db

router = APIRouter()

# Mock analytics data for demo purposes
MOCK_POST_ANALYTICS = {
    "post_1": {
        "id": "analytics_1",
        "post_id": "post_1",
        "platform": "instagram",
        "views": 1250,
        "likes": 89,
        "comments": 12,
        "shares": 5,
        "engagement_rate": 8.48,
        "additional_metrics": {
            "saves": 23,
            "reach": 1100,
            "impressions": 1350
        },
        "recorded_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
    }
}

MOCK_PLATFORM_ANALYTICS = [
    {
        "platform": "instagram",
        "posts": 45,
        "total_views": 25000,
        "total_likes": 1800,
        "total_comments": 250,
        "total_shares": 120,
        "engagement_rate": 8.68,
        "top_performing_post": {
            "id": "post_1",
            "caption": "Amazing sunset view! 🌅",
            "metrics": {
                "views": 1250,
                "likes": 89,
                "engagement_rate": 8.48
            }
        }
    },
    {
        "platform": "facebook",
        "posts": 32,
        "total_views": 18000,
        "total_likes": 1200,
        "total_comments": 180,
        "total_shares": 95,
        "engagement_rate": 8.19,
        "top_performing_post": {
            "id": "post_2",
            "caption": "Weekly motivation! 💪",
            "metrics": {
                "views": 980,
                "likes": 67,
                "engagement_rate": 7.85
            }
        }
    },
    {
        "platform": "twitter",
        "posts": 28,
        "total_views": 12000,
        "total_likes": 800,
        "total_comments": 120,
        "total_shares": 60,
        "engagement_rate": 8.17,
        "top_performing_post": {
            "id": "post_3",
            "caption": "Quick tip for productivity! ⚡",
            "metrics": {
                "views": 750,
                "likes": 45,
                "engagement_rate": 7.20
            }
        }
    }
]

MOCK_ENGAGEMENT_TRENDS = [
    {
        "date": "2024-01-08",
        "views": 1200,
        "likes": 85,
        "comments": 12,
        "shares": 8,
        "engagement_rate": 8.75
    },
    {
        "date": "2024-01-09",
        "views": 1350,
        "likes": 92,
        "comments": 15,
        "shares": 10,
        "engagement_rate": 8.67
    },
    {
        "date": "2024-01-10",
        "views": 1100,
        "likes": 78,
        "comments": 9,
        "shares": 6,
        "engagement_rate": 8.45
    },
    {
        "date": "2024-01-11",
        "views": 1450,
        "likes": 105,
        "comments": 18,
        "shares": 12,
        "engagement_rate": 9.31
    },
    {
        "date": "2024-01-12",
        "views": 1300,
        "likes": 88,
        "comments": 14,
        "shares": 9,
        "engagement_rate": 8.54
    },
    {
        "date": "2024-01-13",
        "views": 1600,
        "likes": 115,
        "comments": 22,
        "shares": 15,
        "engagement_rate": 9.50
    },
    {
        "date": "2024-01-14",
        "views": 1250,
        "likes": 89,
        "comments": 12,
        "shares": 7,
        "engagement_rate": 8.64
    }
]

@router.get("/posts/{post_id}", response_model=schemas.Analytics)
async def get_post_analytics(
    post_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a specific post."""
    # In demo mode, return mock data
    if post_id in MOCK_POST_ANALYTICS:
        return schemas.Analytics(**MOCK_POST_ANALYTICS[post_id])
    
    # Return default analytics if post not found in mock data
    default_analytics = {
        "id": f"analytics_{post_id}",
        "post_id": post_id,
        "platform": "instagram",
        "views": 0,
        "likes": 0,
        "comments": 0,
        "shares": 0,
        "engagement_rate": 0.0,
        "recorded_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    return schemas.Analytics(**default_analytics)

@router.get("/platforms", response_model=schemas.AnalyticsSummary)
async def get_platform_analytics(
    start: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get analytics summary across all platforms for a date range."""
    # In demo mode, return mock data
    platforms = [schemas.PlatformAnalytics(**platform) for platform in MOCK_PLATFORM_ANALYTICS]
    
    # Calculate summary
    total_posts = sum(p.posts for p in platforms)
    total_engagement = sum(p.total_likes + p.total_comments + p.total_shares for p in platforms)
    avg_engagement_rate = sum(p.engagement_rate for p in platforms) / len(platforms) if platforms else 0
    best_platform = max(platforms, key=lambda p: p.engagement_rate).platform if platforms else None
    
    summary = {
        "total_posts": total_posts,
        "total_engagement": total_engagement,
        "average_engagement_rate": round(avg_engagement_rate, 2),
        "best_performing_platform": best_platform
    }
    
    return schemas.AnalyticsSummary(platforms=platforms, summary=summary)

@router.get("/trends", response_model=schemas.TrendsResponse)
async def get_engagement_trends(
    period: str = Query("7d", description="Time period (7d, 30d, 90d)"),
    platform: Optional[str] = Query(None, description="Specific platform to analyze"),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get engagement trends over time."""
    # In demo mode, return mock trend data
    trends = [schemas.EngagementTrend(**trend) for trend in MOCK_ENGAGEMENT_TRENDS]
    
    # Filter trends based on period
    if period == "7d":
        # Return last 7 days
        trends = trends[-7:]
    elif period == "30d":
        # For demo, repeat the 7-day pattern
        trends = trends * 4  # Simulate 28 days
        trends = trends[:30]
    elif period == "90d":
        # For demo, repeat the pattern
        trends = trends * 13  # Simulate ~90 days
        trends = trends[:90]
    
    return schemas.TrendsResponse(
        period=period,
        platform=platform,
        trends=trends
    ) 