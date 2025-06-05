"""
Media router for Crow's Eye API.
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from pydantic import BaseModel

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.models.user import User
from src.features.subscription.access_control import Feature
from ..dependencies import get_current_user, require_feature

router = APIRouter()

# Media storage directory
MEDIA_DIR = Path("data/media")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


class MediaResponse(BaseModel):
    """Media response model."""
    id: str
    filename: str
    content_type: str
    size: int
    upload_date: str
    url: str


class MediaListResponse(BaseModel):
    """Media list response model."""
    media: List[MediaResponse]
    total: int


@router.post("/", response_model=MediaResponse)
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(require_feature(Feature.MEDIA_LIBRARY))
):
    """
    Upload media file (image, video, etc.).
    
    **Tier Required:** Free+ (Spark tier and above)
    
    Supports common media formats:
    - Images: JPG, PNG, GIF, WebP
    - Videos: MP4, MOV, AVI
    """
    # Validate file type
    allowed_types = {
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "video/mp4", "video/quicktime", "video/x-msvideo"
    }
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    # Generate unique filename
    import uuid
    from datetime import datetime
    
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = MEDIA_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Get file stats
    file_stats = file_path.stat()
    
    return MediaResponse(
        id=str(uuid.uuid4()),
        filename=file.filename,
        content_type=file.content_type,
        size=file_stats.st_size,
        upload_date=datetime.now().isoformat(),
        url=f"/media/{unique_filename}"
    )


@router.get("/{media_id}", response_model=MediaResponse)
async def get_media(
    media_id: str,
    current_user: User = Depends(require_feature(Feature.MEDIA_LIBRARY))
):
    """
    Get media file information by ID.
    
    **Tier Required:** Free+ (Spark tier and above)
    """
    # This is a simplified implementation
    # In production, you'd look up the media by ID in a database
    
    # For demo, return a mock response
    from datetime import datetime
    
    return MediaResponse(
        id=media_id,
        filename="sample_image.jpg",
        content_type="image/jpeg",
        size=1024000,
        upload_date=datetime.now().isoformat(),
        url=f"/media/{media_id}"
    )


@router.get("/", response_model=MediaListResponse)
async def list_media(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_feature(Feature.MEDIA_LIBRARY))
):
    """
    List user's media files.
    
    **Tier Required:** Free+ (Spark tier and above)
    """
    # This is a simplified implementation
    # In production, you'd query the database for user's media
    
    from datetime import datetime
    
    # Mock media list
    media_list = []
    for i in range(min(limit, 10)):  # Return up to 10 mock items
        media_list.append(MediaResponse(
            id=f"media_{i + offset}",
            filename=f"sample_{i + offset}.jpg",
            content_type="image/jpeg",
            size=1024000 + i * 1000,
            upload_date=datetime.now().isoformat(),
            url=f"/media/sample_{i + offset}.jpg"
        ))
    
    return MediaListResponse(
        media=media_list,
        total=len(media_list)
    )


@router.delete("/{media_id}")
async def delete_media(
    media_id: str,
    current_user: User = Depends(require_feature(Feature.MEDIA_LIBRARY))
):
    """
    Delete media file by ID.
    
    **Tier Required:** Free+ (Spark tier and above)
    """
    # This is a simplified implementation
    # In production, you'd delete from database and file system
    
    return {"message": f"Media {media_id} deleted successfully"} 