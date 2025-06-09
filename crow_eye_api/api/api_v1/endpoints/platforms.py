from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crow_eye_api import schemas, models
from crow_eye_api.database import get_db
from crow_eye_api.api.api_v1.dependencies import get_current_active_user

router = APIRouter()

@router.get("/requirements", response_model=schemas.PlatformRequirementsResponse)
async def get_platform_requirements():
    """
    Get platform-specific requirements for content formatting.
    """
    platform_requirements = {
        "instagram": {
            "image": {
                "aspect_ratios": ["1:1", "4:5", "16:9"],
                "max_file_size": "30MB",
                "recommended_size": "1080x1080",
                "formats": ["JPG", "PNG"],
                "caption_limit": 2200
            },
            "video": {
                "aspect_ratios": ["1:1", "4:5", "16:9", "9:16"],
                "max_file_size": "4GB",
                "max_duration": "60s",
                "formats": ["MP4", "MOV"],
                "caption_limit": 2200
            },
            "story": {
                "aspect_ratios": ["9:16"],
                "max_file_size": "4GB",
                "max_duration": "15s",
                "formats": ["MP4", "MOV", "JPG", "PNG"],
                "caption_limit": None
            }
        },
        "facebook": {
            "image": {
                "aspect_ratios": ["1.91:1", "1:1", "4:5"],
                "max_file_size": "30MB",
                "recommended_size": "1200x630",
                "formats": ["JPG", "PNG"],
                "caption_limit": 63206
            },
            "video": {
                "aspect_ratios": ["16:9", "1:1", "4:5", "9:16"],
                "max_file_size": "10GB",
                "max_duration": "240m",
                "formats": ["MP4", "MOV"],
                "caption_limit": 63206
            }
        },
        "tiktok": {
            "video": {
                "aspect_ratios": ["9:16"],
                "max_file_size": "4GB",
                "max_duration": "10m",
                "min_duration": "15s",
                "formats": ["MP4", "MOV"],
                "caption_limit": 4000
            }
        },
        "twitter": {
            "image": {
                "aspect_ratios": ["16:9", "1:1"],
                "max_file_size": "5MB",
                "recommended_size": "1200x675",
                "formats": ["JPG", "PNG", "GIF"],
                "caption_limit": 280
            },
            "video": {
                "aspect_ratios": ["1:2.39", "16:9"],
                "max_file_size": "512MB",
                "max_duration": "2m20s",
                "formats": ["MP4", "MOV"],
                "caption_limit": 280
            }
        },
        "linkedin": {
            "image": {
                "aspect_ratios": ["1.91:1", "1:1"],
                "max_file_size": "20MB",
                "recommended_size": "1200x627",
                "formats": ["JPG", "PNG"],
                "caption_limit": 3000
            },
            "video": {
                "aspect_ratios": ["16:9", "1:1", "9:16"],
                "max_file_size": "5GB",
                "max_duration": "10m",
                "formats": ["MP4", "MOV"],
                "caption_limit": 3000
            }
        }
    }
    
    return schemas.PlatformRequirementsResponse(
        platforms=platform_requirements,
        last_updated="2024-01-15"
    )

# Static data for optimization recommendations
OPTIMIZATION_GUIDELINES = {
    "instagram": {
        "best_posting_times": ["11:00", "13:00", "17:00"],
        "hashtag_recommendations": {
            "optimal_count": "8-12",
            "mix": "trending + niche + branded",
            "placement": "caption or first comment"
        },
        "content_tips": [
            "Use high-quality visuals",
            "Include faces in photos for higher engagement",
            "Create vertical videos for Stories",
            "Use interactive stickers in Stories"
        ]
    },
    "facebook": {
        "best_posting_times": ["09:00", "13:00", "15:00"],
        "hashtag_recommendations": {
            "optimal_count": "2-5",
            "usage": "sparingly, focus on relevant tags"
        },
        "content_tips": [
            "Native video performs better than links",
            "Longer captions can work well",
            "Ask questions to encourage engagement",
            "Share behind-the-scenes content"
        ]
    },
    "tiktok": {
        "best_posting_times": ["06:00", "10:00", "19:00"],
        "hashtag_recommendations": {
            "optimal_count": "3-5",
            "mix": "trending + niche",
            "placement": "caption"
        },
        "content_tips": [
            "Hook viewers in first 3 seconds",
            "Use trending sounds and effects",
            "Create vertical videos only",
            "Keep content authentic and engaging"
        ]
    }
} 