from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
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

@router.get("/status")
async def get_google_business_status(
    current_user: models.User = Depends(get_current_active_user)
):
    """Get Google My Business authentication and connection status."""
    try:
        from google.oauth2.credentials import Credentials
        
        token_file = f"google_google_business_token_{current_user.id}.json"
        
        if not os.path.exists(token_file):
            return {
                "authenticated": False,
                "connected": False,
                "message": "Not authenticated with Google My Business"
            }
        
        # Load and validate credentials
        credentials = Credentials.from_authorized_user_file(
            token_file, 
            ['https://www.googleapis.com/auth/business.manage']
        )
        
        if not credentials.valid:
            return {
                "authenticated": False,
                "connected": False,
                "message": "Google My Business credentials expired or invalid"
            }
        
        # Test connection
        import requests
        response = requests.get(
            'https://mybusinessbusinessinformation.googleapis.com/v1/accounts',
            headers={'Authorization': f'Bearer {credentials.token}'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            accounts = data.get('accounts', [])
            if accounts:
                return {
                    "authenticated": True,
                    "connected": True,
                    "account_name": accounts[0].get('name', 'Unknown'),
                    "account_count": len(accounts),
                    "message": f"Connected to Google My Business: {accounts[0].get('name', 'Unknown')}"
                }
            else:
                return {
                    "authenticated": True,
                    "connected": False,
                    "message": "No Google My Business accounts found"
                }
        else:
            return {
                "authenticated": False,
                "connected": False,
                "message": f"Google My Business connection failed: HTTP {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"Error checking Google My Business status: {e}")
        return {
            "authenticated": False,
            "connected": False,
            "message": f"Status check failed: {str(e)}"
        }

@router.get("/accounts")
async def get_google_business_accounts(
    current_user: models.User = Depends(get_current_active_user)
):
    """Get Google My Business accounts for the authenticated user."""
    try:
        from google.oauth2.credentials import Credentials
        
        token_file = f"google_google_business_token_{current_user.id}.json"
        
        if not os.path.exists(token_file):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated with Google My Business"
            )
        
        credentials = Credentials.from_authorized_user_file(
            token_file, 
            ['https://www.googleapis.com/auth/business.manage']
        )
        
        if not credentials.valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google My Business credentials expired"
            )
        
        import requests
        response = requests.get(
            'https://mybusinessbusinessinformation.googleapis.com/v1/accounts',
            headers={'Authorization': f'Bearer {credentials.token}'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "accounts": data.get('accounts', []),
                "message": "Successfully retrieved Google My Business accounts"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to retrieve accounts: HTTP {response.status_code}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Google My Business accounts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get accounts: {str(e)}"
        )

@router.get("/locations")
async def get_google_business_locations(
    account_name: str,
    current_user: models.User = Depends(get_current_active_user)
):
    """Get Google My Business locations for a specific account."""
    try:
        from google.oauth2.credentials import Credentials
        
        token_file = f"google_google_business_token_{current_user.id}.json"
        
        if not os.path.exists(token_file):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated with Google My Business"
            )
        
        credentials = Credentials.from_authorized_user_file(
            token_file, 
            ['https://www.googleapis.com/auth/business.manage']
        )
        
        if not credentials.valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google My Business credentials expired"
            )
        
        import requests
        response = requests.get(
            f'https://mybusinessbusinessinformation.googleapis.com/v1/{account_name}/locations',
            headers={'Authorization': f'Bearer {credentials.token}'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "locations": data.get('locations', []),
                "message": "Successfully retrieved Google My Business locations"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to retrieve locations: HTTP {response.status_code}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Google My Business locations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get locations: {str(e)}"
        )

@router.post("/post")
async def create_google_business_post(
    location_name: str = Form(...),
    summary: str = Form(...),
    file: Optional[UploadFile] = File(None),
    call_to_action: str = Form("LEARN_MORE"),
    current_user: models.User = Depends(get_current_active_user)
):
    """Create a post on Google My Business."""
    try:
        from google.oauth2.credentials import Credentials
        
        token_file = f"google_google_business_token_{current_user.id}.json"
        
        if not os.path.exists(token_file):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated with Google My Business"
            )
        
        credentials = Credentials.from_authorized_user_file(
            token_file, 
            ['https://www.googleapis.com/auth/business.manage']
        )
        
        if not credentials.valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google My Business credentials expired"
            )
        
        # Prepare post data
        post_data = {
            'languageCode': 'en-US',
            'summary': summary[:1500],  # Limit to 1500 characters
            'callToAction': {
                'actionType': call_to_action
            }
        }
        
        # Handle media upload if provided
        if file:
            # Save file temporarily
            temp_file_path = f"temp_gmb_{current_user.id}_{file.filename}"
            with open(temp_file_path, "wb") as temp_file:
                content = await file.read()
                temp_file.write(content)
            
            try:
                # Upload media (this would need to be implemented based on GMB API)
                # For now, we'll skip media upload and focus on text posts
                pass
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        
        # Create the post
        import requests
        response = requests.post(
            f'https://mybusiness.googleapis.com/v4/{location_name}/localPosts',
            headers={
                'Authorization': f'Bearer {credentials.token}',
                'Content-Type': 'application/json'
            },
            json=post_data,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            return {
                "success": True,
                "post_name": result.get('name', 'Unknown'),
                "message": "Successfully created Google My Business post"
            }
        else:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create post: {error_msg}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Google My Business post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create post: {str(e)}"
        )

@router.delete("/auth/disconnect")
async def disconnect_google_business(
    current_user: models.User = Depends(get_current_active_user)
):
    """Disconnect Google My Business account."""
    try:
        # Remove user-specific files
        files_to_remove = [
            f"google_google_business_credentials_{current_user.id}.json",
            f"google_google_business_token_{current_user.id}.json",
            f"google_google_business_state_{current_user.id}.json"
        ]
        
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return {
            "success": True,
            "message": "Google My Business account disconnected successfully"
        }
        
    except Exception as e:
        logger.error(f"Error disconnecting Google My Business: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect Google My Business: {str(e)}"
        ) 