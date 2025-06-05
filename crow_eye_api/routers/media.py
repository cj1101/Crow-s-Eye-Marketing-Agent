"""
Media router for Crow's Eye API.
Handles media uploads, processing, editing, and management.
"""

import os
import sys
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ..dependencies import (
    get_current_user, 
    get_media_handler, 
    get_crowseye_handler,
    get_services
)

router = APIRouter()

# Pydantic models
class MediaItem(BaseModel):
    """Media item model."""
    id: str
    filename: str
    path: str
    type: str  # photo, video
    size: int
    format: str
    dimensions: Optional[tuple] = None
    duration: Optional[float] = None  # for videos
    caption: Optional[str] = None
    ai_tags: List[str] = []
    created_at: str
    updated_at: str
    status: str  # uploaded, processing, ready, failed

class MediaSearchRequest(BaseModel):
    """Media search request model."""
    query: Optional[str] = None
    type: Optional[str] = None  # photo, video, all
    tags: Optional[List[str]] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

class MediaSearchResponse(BaseModel):
    """Media search response model."""
    items: List[MediaItem]
    total: int
    query: Optional[str]
    filters: Dict[str, Any]

class MediaUploadResponse(BaseModel):
    """Media upload response model."""
    id: str
    filename: str
    status: str
    message: str
    media_item: Optional[MediaItem] = None

class MediaEditRequest(BaseModel):
    """Media edit request model."""
    media_id: str
    operations: List[str]  # resize, crop, filter, enhance, etc.
    parameters: Dict[str, Any] = {}

class MediaEditResponse(BaseModel):
    """Media edit response model."""
    id: str
    original_media_id: str
    status: str
    operations_applied: List[str]
    output_path: Optional[str] = None

class MediaBatchRequest(BaseModel):
    """Batch media operation request."""
    media_ids: List[str]
    operation: str  # delete, tag, move, etc.
    parameters: Dict[str, Any] = {}

class CaptionGenerationRequest(BaseModel):
    """Caption generation request model."""
    media_ids: List[str]
    tone: Optional[str] = "engaging"  # engaging, professional, casual, funny
    include_hashtags: bool = True
    max_length: int = Field(default=150, ge=10, le=2200)

class CaptionGenerationResponse(BaseModel):
    """Caption generation response model."""
    caption: str
    hashtags: List[str]
    media_count: int
    tone: str

@router.get("/", response_model=MediaSearchResponse)
async def list_media(
    query: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    services: dict = Depends(get_services),
    current_user = Depends(get_current_user)
):
    """
    List and search media with AI-powered filtering.
    
    **Features:**
    - AI-powered content search
    - Filter by media type (photo/video)
    - Smart tagging and categorization
    - Pagination support
    """
    try:
        crowseye_handler = services["crowseye_handler"]
        
        # Get all media or search
        if query:
            media_data = crowseye_handler.search_media(query)
        else:
            media_data = crowseye_handler.get_all_media()
        
        # Flatten and filter media items
        all_items = []
        for category, paths in media_data.items():
            media_type = "photo" if "photo" in category else "video" if "video" in category else "finished"
            
            if type and type != "all" and media_type != type:
                continue
                
            for path in paths:
                # Get media info
                info = crowseye_handler.get_media_item_info(path)
                if info:
                    item = MediaItem(
                        id=str(uuid.uuid5(uuid.NAMESPACE_DNS, path)),
                        filename=os.path.basename(path),
                        path=path,
                        type=media_type,
                        size=info.get("size", 0),
                        format=info.get("format", "unknown"),
                        dimensions=info.get("dimensions"),
                        duration=info.get("duration"),
                        caption=info.get("caption"),
                        ai_tags=info.get("ai_tags", []),
                        created_at=info.get("created_at", datetime.now().isoformat()),
                        updated_at=info.get("updated_at", datetime.now().isoformat()),
                        status="ready"
                    )
                    all_items.append(item)
        
        # Apply pagination
        total = len(all_items)
        paginated_items = all_items[offset:offset + limit]
        
        return MediaSearchResponse(
            items=paginated_items,
            total=total,
            query=query,
            filters={"type": type, "limit": limit, "offset": offset}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list media: {str(e)}"
        )

@router.post("/upload", response_model=MediaUploadResponse)
async def upload_media(
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    is_post_ready: bool = Form(False),
    services: dict = Depends(get_services),
    current_user = Depends(get_current_user)
):
    """
    Upload media file with automatic AI tagging and processing.
    
    **Features:**
    - Automatic AI content analysis
    - Smart tagging and categorization
    - Thumbnail generation
    - Format validation and conversion
    """
    try:
        media_handler = services["media_handler"]
        crowseye_handler = services["crowseye_handler"]
        
        # Validate file type
        if not file.content_type.startswith(('image/', 'video/')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image and video files are supported"
            )
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Save file
        upload_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'media')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Add to media handler
        success = crowseye_handler.add_media_item(
            media_path=file_path,
            caption=caption or "",
            is_post_ready=is_post_ready
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process uploaded file"
            )
        
        # Get media info
        info = crowseye_handler.get_media_item_info(file_path)
        
        media_item = MediaItem(
            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, file_path)),
            filename=unique_filename,
            path=file_path,
            type="photo" if file.content_type.startswith('image/') else "video",
            size=len(content),
            format=file_extension[1:] if file_extension else "unknown",
            dimensions=info.get("dimensions") if info else None,
            duration=info.get("duration") if info else None,
            caption=caption,
            ai_tags=info.get("ai_tags", []) if info else [],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            status="ready"
        )
        
        return MediaUploadResponse(
            id=media_item.id,
            filename=unique_filename,
            status="success",
            message="Media uploaded and processed successfully",
            media_item=media_item
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.get("/{media_id}", response_model=MediaItem)
async def get_media(
    media_id: str,
    services: dict = Depends(get_services),
    current_user = Depends(get_current_user)
):
    """Get detailed information about a specific media item."""
    try:
        crowseye_handler = services["crowseye_handler"]
        
        # Find media by ID (simplified implementation)
        media_data = crowseye_handler.get_all_media()
        for category, paths in media_data.items():
            for path in paths:
                item_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, path))
                if item_id == media_id:
                    info = crowseye_handler.get_media_item_info(path)
                    if info:
                        return MediaItem(
                            id=media_id,
                            filename=os.path.basename(path),
                            path=path,
                            type="photo" if "photo" in category else "video" if "video" in category else "finished",
                            size=info.get("size", 0),
                            format=info.get("format", "unknown"),
                            dimensions=info.get("dimensions"),
                            duration=info.get("duration"),
                            caption=info.get("caption"),
                            ai_tags=info.get("ai_tags", []),
                            created_at=info.get("created_at", datetime.now().isoformat()),
                            updated_at=info.get("updated_at", datetime.now().isoformat()),
                            status="ready"
                        )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media item not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get media: {str(e)}"
        )

@router.delete("/{media_id}")
async def delete_media(
    media_id: str,
    services: dict = Depends(get_services),
    current_user = Depends(get_current_user)
):
    """Delete a media item."""
    try:
        crowseye_handler = services["crowseye_handler"]
        
        # Find and delete media by ID
        media_data = crowseye_handler.get_all_media()
        for category, paths in media_data.items():
            for path in paths:
                item_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, path))
                if item_id == media_id:
                    success = crowseye_handler.remove_media_item(path)
                    if success:
                        return {"message": "Media deleted successfully"}
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to delete media"
                        )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media item not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete media: {str(e)}"
        )

@router.post("/generate-caption", response_model=CaptionGenerationResponse)
async def generate_caption(
    request: CaptionGenerationRequest,
    services: dict = Depends(get_services),
    current_user = Depends(get_current_user)
):
    """
    Generate AI-powered captions for media items.
    
    **Features:**
    - AI-powered content analysis
    - Tone and style customization
    - Automatic hashtag generation
    - Multi-media caption support
    """
    try:
        crowseye_handler = services["crowseye_handler"]
        
        # Convert media IDs to paths
        media_paths = []
        media_data = crowseye_handler.get_all_media()
        
        for media_id in request.media_ids:
            found = False
            for category, paths in media_data.items():
                for path in paths:
                    item_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, path))
                    if item_id == media_id:
                        media_paths.append(path)
                        found = True
                        break
                if found:
                    break
        
        if not media_paths:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No valid media items found"
            )
        
        # Generate caption
        caption = crowseye_handler.generate_caption(
            media_paths=media_paths,
            tone_prompt=request.tone
        )
        
        # Extract hashtags from caption (simple implementation)
        hashtags = []
        if request.include_hashtags and caption:
            # Simple hashtag extraction
            words = caption.split()
            hashtags = [word for word in words if word.startswith('#')]
        
        return CaptionGenerationResponse(
            caption=caption,
            hashtags=hashtags,
            media_count=len(media_paths),
            tone=request.tone
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate caption: {str(e)}"
        )

@router.post("/edit", response_model=MediaEditResponse)
async def edit_media(
    request: MediaEditRequest,
    services: dict = Depends(get_services),
    current_user = Depends(get_current_user)
):
    """
    Apply AI-powered editing to media items.
    
    **Operations:**
    - Image enhancement and filtering
    - Automatic cropping and resizing
    - Color correction and adjustments
    - Video trimming and effects
    """
    try:
        # This would integrate with the image/video edit handlers
        # For now, return a mock response
        
        edit_id = str(uuid.uuid4())
        
        return MediaEditResponse(
            id=edit_id,
            original_media_id=request.media_id,
            status="processing",
            operations_applied=request.operations,
            output_path=None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to edit media: {str(e)}"
        )

@router.post("/batch")
async def batch_operation(
    request: MediaBatchRequest,
    services: dict = Depends(get_services),
    current_user = Depends(get_current_user)
):
    """
    Perform batch operations on multiple media items.
    
    **Operations:**
    - Bulk delete
    - Bulk tagging
    - Bulk move/organize
    - Batch processing
    """
    try:
        crowseye_handler = services["crowseye_handler"]
        
        results = []
        for media_id in request.media_ids:
            try:
                if request.operation == "delete":
                    # Find and delete media
                    media_data = crowseye_handler.get_all_media()
                    deleted = False
                    for category, paths in media_data.items():
                        for path in paths:
                            item_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, path))
                            if item_id == media_id:
                                success = crowseye_handler.remove_media_item(path)
                                results.append({
                                    "media_id": media_id,
                                    "success": success,
                                    "operation": "delete"
                                })
                                deleted = True
                                break
                        if deleted:
                            break
                    
                    if not deleted:
                        results.append({
                            "media_id": media_id,
                            "success": False,
                            "operation": "delete",
                            "error": "Media not found"
                        })
                
                # Add other batch operations here
                
            except Exception as e:
                results.append({
                    "media_id": media_id,
                    "success": False,
                    "operation": request.operation,
                    "error": str(e)
                })
        
        return {
            "operation": request.operation,
            "total_items": len(request.media_ids),
            "results": results,
            "success_count": len([r for r in results if r.get("success", False)])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch operation failed: {str(e)}"
        )

@router.get("/{media_id}/download")
async def download_media(
    media_id: str,
    services: dict = Depends(get_services),
    current_user = Depends(get_current_user)
):
    """Download a media file."""
    try:
        crowseye_handler = services["crowseye_handler"]
        
        # Find media by ID
        media_data = crowseye_handler.get_all_media()
        for category, paths in media_data.items():
            for path in paths:
                item_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, path))
                if item_id == media_id:
                    if os.path.exists(path):
                        return FileResponse(
                            path=path,
                            filename=os.path.basename(path),
                            media_type='application/octet-stream'
                        )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Media file not found on disk"
                        )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media item not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        ) 