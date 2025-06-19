"""
Google Services API endpoints for Crow's Eye.
Handles authentication and management for various Google services.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
import os
import json
import logging
from datetime import datetime

from crow_eye_api import schemas, models
from crow_eye_api.database import get_db
from crow_eye_api.api.api_v1.dependencies import get_current_active_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Service configurations
GOOGLE_SERVICES = {
    "youtube": {
        "scopes": [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/youtube.readonly"
        ],
        "name": "YouTube",
        "description": "Upload videos and manage your YouTube channel"
    },
    "google_photos": {
        "scopes": [
            "https://www.googleapis.com/auth/photoslibrary.readonly",
            "https://www.googleapis.com/auth/photoslibrary.sharing"
        ],
        "name": "Google Photos",
        "description": "Access and import photos from your Google Photos library"
    },
    "google_business": {
        "scopes": [
            "https://www.googleapis.com/auth/business.manage"
        ],
        "name": "Google My Business",
        "description": "Manage your Google My Business posts and locations"
    }
}

@router.get("/services")
async def get_google_services():
    """Get list of available Google services."""
    return {
        "services": GOOGLE_SERVICES,
        "message": "Available Google services for integration"
    }

@router.get("/services/status")
async def get_all_services_status(
    current_user: models.User = Depends(get_current_active_user)
):
    """Get authentication status for all Google services."""
    try:
        status_data = {}
        
        for service_key, service_info in GOOGLE_SERVICES.items():
            status_data[service_key] = await get_service_status(service_key, current_user.id)
            
        return {
            "user_id": current_user.id,
            "services": status_data,
            "authenticated_services": [k for k, v in status_data.items() if v.get("authenticated", False)]
        }
        
    except Exception as e:
        logger.error(f"Error getting services status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get services status: {str(e)}"
        )

async def get_service_status(service_name: str, user_id: int) -> Dict[str, Any]:
    """Helper function to get authentication status for a service."""
    try:
        token_file = f"google_{service_name}_token_{user_id}.json"
        
        if not os.path.exists(token_file):
            return {
                "authenticated": False,
                "connected": False,
                "message": f"Not authenticated with {GOOGLE_SERVICES[service_name]['name']}"
            }
        
        return {
            "authenticated": True,
            "connected": True,
            "message": f"Connected to {GOOGLE_SERVICES[service_name]['name']}"
        }
        
    except Exception as e:
        return {
            "authenticated": False,
            "connected": False,
            "message": f"Status check failed: {str(e)}"
        } 