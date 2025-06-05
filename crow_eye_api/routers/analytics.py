"""
Analytics router for Crow's Eye API.
"""

import os
import sys
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Response
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import csv
import io

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.models.user import User
from src.features.subscription.access_control import Feature
from ..dependencies import get_current_user, require_feature

router = APIRouter()


class AnalyticsResponse(BaseModel):
    """Analytics response model."""
    period: str
    total_posts: int
    total_engagement: int
    avg_engagement_rate: float
    top_performing_content: List[dict]
    platform_breakdown: dict
    growth_metrics: dict


class ExportRequest(BaseModel):
    """Analytics export request model."""
    start_date: str
    end_date: str
    platforms: Optional[List[str]] = None
    metrics: Optional[List[str]] = None
    format: str = "csv"  # csv, json, xlsx


@router.get("/", response_model=AnalyticsResponse)
async def get_analytics(
    period: str = "30d",  # 7d, 30d, 90d, 1y
    platform: Optional[str] = None,  # instagram, facebook, twitter, etc.
    current_user: User = Depends(require_feature(Feature.ADVANCED_ANALYTICS))
):
    """
    Get performance analytics for user's content.
    
    **Tier Required:** Pro+ ($19/month and above)
    
    Provides comprehensive analytics including:
    - Engagement rates and trends
    - Top performing content
    - Platform-specific metrics
    - Growth tracking
    - Audience insights
    """
    # This is a simplified implementation
    # In production, you'd query your analytics database
    
    # Mock analytics data
    mock_data = {
        "7d": {
            "total_posts": 12,
            "total_engagement": 1250,
            "avg_engagement_rate": 4.2,
            "growth_rate": 2.1
        },
        "30d": {
            "total_posts": 45,
            "total_engagement": 5800,
            "avg_engagement_rate": 3.8,
            "growth_rate": 8.5
        },
        "90d": {
            "total_posts": 120,
            "total_engagement": 18500,
            "avg_engagement_rate": 4.1,
            "growth_rate": 15.2
        },
        "1y": {
            "total_posts": 480,
            "total_engagement": 75000,
            "avg_engagement_rate": 3.9,
            "growth_rate": 45.8
        }
    }
    
    data = mock_data.get(period, mock_data["30d"])
    
    return AnalyticsResponse(
        period=period,
        total_posts=data["total_posts"],
        total_engagement=data["total_engagement"],
        avg_engagement_rate=data["avg_engagement_rate"],
        top_performing_content=[
            {
                "id": "post_1",
                "type": "image",
                "engagement": 450,
                "engagement_rate": 6.2,
                "platform": "instagram"
            },
            {
                "id": "post_2", 
                "type": "video",
                "engagement": 380,
                "engagement_rate": 5.8,
                "platform": "facebook"
            },
            {
                "id": "post_3",
                "type": "carousel",
                "engagement": 320,
                "engagement_rate": 5.1,
                "platform": "instagram"
            }
        ],
        platform_breakdown={
            "instagram": {"posts": data["total_posts"] // 2, "engagement": data["total_engagement"] // 2},
            "facebook": {"posts": data["total_posts"] // 3, "engagement": data["total_engagement"] // 3},
            "twitter": {"posts": data["total_posts"] // 6, "engagement": data["total_engagement"] // 6}
        },
        growth_metrics={
            "follower_growth": data["growth_rate"],
            "engagement_growth": data["growth_rate"] * 0.8,
            "reach_growth": data["growth_rate"] * 1.2
        }
    )


@router.post("/export")
async def export_analytics(
    request: ExportRequest,
    current_user: User = Depends(require_feature(Feature.ADVANCED_ANALYTICS))
):
    """
    Export analytics data in CSV, JSON, or Excel format.
    
    **Tier Required:** Pro+ ($19/month and above)
    
    Export comprehensive analytics data for external analysis:
    - Custom date ranges
    - Platform filtering
    - Multiple export formats
    - Bulk data export
    """
    # This is a simplified implementation
    # In production, you'd generate real export data
    
    # Mock export data
    export_data = [
        {
            "date": "2024-01-01",
            "platform": "instagram",
            "post_id": "post_1",
            "post_type": "image",
            "likes": 150,
            "comments": 25,
            "shares": 8,
            "engagement_rate": 4.2
        },
        {
            "date": "2024-01-02", 
            "platform": "facebook",
            "post_id": "post_2",
            "post_type": "video",
            "likes": 200,
            "comments": 35,
            "shares": 15,
            "engagement_rate": 5.1
        },
        {
            "date": "2024-01-03",
            "platform": "instagram",
            "post_id": "post_3",
            "post_type": "carousel",
            "likes": 180,
            "comments": 30,
            "shares": 12,
            "engagement_rate": 4.8
        }
    ]
    
    if request.format.lower() == "json":
        # Return JSON export
        return {
            "export_format": "json",
            "data": export_data,
            "metadata": {
                "start_date": request.start_date,
                "end_date": request.end_date,
                "total_records": len(export_data),
                "exported_at": datetime.now().isoformat()
            }
        }
    
    elif request.format.lower() == "csv":
        # Generate CSV export
        output = io.StringIO()
        if export_data:
            writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
            writer.writeheader()
            writer.writerows(export_data)
        
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=analytics_export.csv"}
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format: {request.format}"
        )


@router.get("/insights")
async def get_insights(
    current_user: User = Depends(require_feature(Feature.ADVANCED_ANALYTICS))
):
    """
    Get AI-powered insights and recommendations.
    
    **Tier Required:** Pro+ ($19/month and above)
    """
    # Mock insights
    return {
        "insights": [
            {
                "type": "performance",
                "title": "Best Posting Time",
                "description": "Your content performs 35% better when posted between 2-4 PM",
                "recommendation": "Schedule more posts during peak engagement hours",
                "confidence": 0.85
            },
            {
                "type": "content",
                "title": "Video Content Success",
                "description": "Video posts have 2.3x higher engagement than image posts",
                "recommendation": "Increase video content ratio to 40% of total posts",
                "confidence": 0.92
            },
            {
                "type": "audience",
                "title": "Audience Growth",
                "description": "Your audience is growing 15% faster on Instagram vs Facebook",
                "recommendation": "Focus more resources on Instagram content strategy",
                "confidence": 0.78
            }
        ],
        "generated_at": datetime.now().isoformat()
    }


@router.get("/competitors")
async def get_competitor_analysis(
    current_user: User = Depends(require_feature(Feature.ADVANCED_ANALYTICS))
):
    """
    Get competitor analysis and benchmarking.
    
    **Tier Required:** Pro+ ($19/month and above)
    """
    # Mock competitor data
    return {
        "industry_benchmarks": {
            "avg_engagement_rate": 3.2,
            "avg_posting_frequency": 5.5,
            "top_content_types": ["video", "carousel", "image"]
        },
        "your_performance": {
            "engagement_rate": 4.1,
            "posting_frequency": 6.2,
            "performance_vs_industry": "+28%"
        },
        "recommendations": [
            "Your engagement rate is above industry average - great work!",
            "Consider increasing video content to match industry trends",
            "Your posting frequency is optimal for your audience size"
        ]
    }


@router.get("/reports/summary")
async def get_summary_report(
    period: str = "30d",
    current_user: User = Depends(require_feature(Feature.ADVANCED_ANALYTICS))
):
    """
    Get executive summary report.
    
    **Tier Required:** Pro+ ($19/month and above)
    """
    # Mock summary report
    return {
        "period": period,
        "summary": {
            "total_reach": 25000,
            "total_engagement": 5800,
            "new_followers": 450,
            "top_platform": "instagram",
            "best_performing_post": {
                "id": "post_1",
                "engagement": 450,
                "platform": "instagram"
            }
        },
        "key_metrics": {
            "engagement_rate": 4.1,
            "growth_rate": 8.5,
            "content_performance_score": 85,
            "audience_quality_score": 92
        },
        "trends": {
            "engagement": "increasing",
            "reach": "stable", 
            "followers": "increasing"
        }
    } 