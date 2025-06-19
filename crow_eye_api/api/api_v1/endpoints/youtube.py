from typing import Dict, Any, Optional
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

# YouTube API configuration
YOUTUBE_SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.readonly'
]

@router.post("/auth/setup")
async def setup_youtube_auth(
    client_id: str = Form(...),
    client_secret: str = Form(...),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Setup YouTube OAuth2 credentials for the user.
    This saves the client credentials that will be used for OAuth flow.
    """
    try:
        # Create credentials structure
        credentials_data = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost:8080/callback"]
            }
        }
        
        # Save to user-specific file (in production, this would go to database)
        credentials_file = f"youtube_credentials_{current_user.id}.json"
        with open(credentials_file, 'w') as f:
            json.dump(credentials_data, f, indent=4)
        
        return {
            "success": True,
            "message": "YouTube credentials saved successfully",
            "auth_url": f"/api/v1/youtube/auth/authorize?user_id={current_user.id}"
        }
        
    except Exception as e:
        logger.error(f"Error setting up YouTube auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup YouTube authentication: {str(e)}"
        )

@router.get("/auth/authorize")
async def get_youtube_auth_url(
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get YouTube OAuth2 authorization URL for the user to authenticate.
    """
    try:
        from google_auth_oauthlib.flow import Flow
        
        credentials_file = f"youtube_credentials_{current_user.id}.json"
        if not os.path.exists(credentials_file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="YouTube credentials not configured. Please setup credentials first."
            )
        
        # Create OAuth2 flow
        flow = Flow.from_client_secrets_file(
            credentials_file,
            scopes=YOUTUBE_SCOPES
        )
        flow.redirect_uri = "http://localhost:8080/callback"
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        # Store state for validation (in production, use Redis or database)
        state_file = f"youtube_state_{current_user.id}.json"
        with open(state_file, 'w') as f:
            json.dump({"state": state}, f)
        
        return {
            "authorization_url": authorization_url,
            "state": state,
            "message": "Visit the authorization URL to grant YouTube access"
        }
        
    except Exception as e:
        logger.error(f"Error getting YouTube auth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )

@router.post("/auth/callback")
async def youtube_auth_callback(
    code: str = Form(...),
    state: str = Form(...),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Handle YouTube OAuth2 callback and save access tokens.
    """
    try:
        from google_auth_oauthlib.flow import Flow
        
        credentials_file = f"youtube_credentials_{current_user.id}.json"
        state_file = f"youtube_state_{current_user.id}.json"
        
        # Validate state
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                stored_state = json.load(f)["state"]
            if stored_state != state:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid state parameter"
                )
            os.remove(state_file)  # Clean up
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="State validation failed"
            )
        
        # Exchange code for tokens
        flow = Flow.from_client_secrets_file(
            credentials_file,
            scopes=YOUTUBE_SCOPES
        )
        flow.redirect_uri = "http://localhost:8080/callback"
        
        flow.fetch_token(code=code)
        
        # Save tokens
        token_file = f"youtube_token_{current_user.id}.json"
        with open(token_file, 'w') as f:
            f.write(flow.credentials.to_json())
        
        return {
            "success": True,
            "message": "YouTube authentication completed successfully",
            "authenticated": True
        }
        
    except Exception as e:
        logger.error(f"Error in YouTube auth callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication callback failed: {str(e)}"
        )

@router.get("/status")
async def get_youtube_status(
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get YouTube authentication and connection status.
    """
    try:
        from google.oauth2.credentials import Credentials
        import googleapiclient.discovery
        
        token_file = f"youtube_token_{current_user.id}.json"
        
        if not os.path.exists(token_file):
            return {
                "authenticated": False,
                "connected": False,
                "message": "Not authenticated with YouTube"
            }
        
        # Load and validate credentials
        credentials = Credentials.from_authorized_user_file(token_file, YOUTUBE_SCOPES)
        
        if not credentials.valid:
            return {
                "authenticated": False,
                "connected": False,
                "message": "YouTube credentials expired or invalid"
            }
        
        # Test connection
        youtube = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)
        request = youtube.channels().list(part="snippet,statistics", mine=True)
        response = request.execute()
        
        if 'items' in response and len(response['items']) > 0:
            channel = response['items'][0]
            channel_title = channel['snippet']['title']
            subscriber_count = channel['statistics'].get('subscriberCount', '0')
            
            return {
                "authenticated": True,
                "connected": True,
                "channel_name": channel_title,
                "subscriber_count": subscriber_count,
                "message": f"Connected to YouTube channel: {channel_title}"
            }
        else:
            return {
                "authenticated": True,
                "connected": False,
                "message": "No YouTube channel found for this account"
            }
            
    except Exception as e:
        logger.error(f"Error checking YouTube status: {e}")
        return {
            "authenticated": False,
            "connected": False,
            "message": f"Status check failed: {str(e)}"
        }

@router.post("/upload")
async def upload_to_youtube(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    is_short: bool = Form(False),
    privacy_status: str = Form("public"),
    tags: Optional[str] = Form(None),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Upload a video to YouTube.
    """
    try:
        from google.oauth2.credentials import Credentials
        import googleapiclient.discovery
        from googleapiclient.http import MediaFileUpload
        
        token_file = f"youtube_token_{current_user.id}.json"
        
        if not os.path.exists(token_file):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated with YouTube"
            )
        
        # Load credentials
        credentials = Credentials.from_authorized_user_file(token_file, YOUTUBE_SCOPES)
        
        if not credentials.valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="YouTube credentials expired"
            )
        
        # Save uploaded file temporarily
        temp_file_path = f"temp_upload_{current_user.id}_{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        try:
            # Build YouTube service
            youtube = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)
            
            # Parse tags
            tag_list = []
            if tags:
                tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tag_list,
                    'categoryId': '22'  # People & Blogs
                },
                'status': {
                    'privacyStatus': privacy_status
                }
            }
            
            # Add YouTube Shorts indicator if applicable
            if is_short:
                body['snippet']['title'] = f"#Shorts {title}" if not title.startswith('#Shorts') else title
            
            # Create media upload
            media = MediaFileUpload(temp_file_path, resumable=True)
            
            # Execute upload
            request = youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = request.execute()
            
            return {
                "success": True,
                "video_id": response['id'],
                "video_url": f"https://www.youtube.com/watch?v={response['id']}",
                "title": response['snippet']['title'],
                "message": "Video uploaded successfully to YouTube"
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    except Exception as e:
        logger.error(f"Error uploading to YouTube: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"YouTube upload failed: {str(e)}"
        )

@router.delete("/auth/disconnect")
async def disconnect_youtube(
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Disconnect YouTube account by removing stored credentials.
    """
    try:
        # Remove user-specific files
        files_to_remove = [
            f"youtube_credentials_{current_user.id}.json",
            f"youtube_token_{current_user.id}.json",
            f"youtube_state_{current_user.id}.json"
        ]
        
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return {
            "success": True,
            "message": "YouTube account disconnected successfully"
        }
        
    except Exception as e:
        logger.error(f"Error disconnecting YouTube: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect YouTube: {str(e)}"
        ) 