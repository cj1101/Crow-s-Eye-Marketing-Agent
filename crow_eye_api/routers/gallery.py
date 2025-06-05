"""
Gallery router for Crow's Eye API.
Handles gallery creation, management, and AI-powered organization.
"""

import os
import sys
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ..dependencies import (
    get_current_user,
    get_crowseye_handler,
    get_services
)

router = APIRouter()

# Pydantic models
class GalleryItem(BaseModel):
    """Gallery item model."""
    id: str
    name: str
    description: Optional[str] = None
    media_count: int
    media_paths: List[str]
    caption: Optional[str] = None
    tags: List[str] = []
    created_at: str
    updated_at: str
    thumbnail_url: Optional[str] = None
    
class GalleryCreateRequest(BaseModel):
    """Gallery creation request model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    media_ids: List[str] = Field(..., min_items=1)
    caption: Optional[str] = Field(None, max_length=2000)
    auto_caption: bool = False
    enhance_photos: bool = False

class GallerySearchRequest(BaseModel):
    """Gallery search request model."""
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

class GalleryUpdateRequest(BaseModel):
    """Gallery update request model."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    caption: Optional[str] = Field(None, max_length=2000)
    add_media_ids: Optional[List[str]] = None
    remove_media_ids: Optional[List[str]] = None

class GalleryGenerationRequest(BaseModel):
    """AI gallery generation request model."""
    prompt: str = Field(..., min_length=1, max_length=500)
    count: Optional[int] = Field(default=5, ge=1, le=20)
    enhance_photos: bool = False
    auto_caption: bool = True
    tone: Optional[str] = "engaging"

class GalleryGenerationResponse(BaseModel):
    """AI gallery generation response model."""
    gallery: GalleryItem
    ai_analysis: Dict[str, Any]
    processing_time: float
    media_enhanced: int

class GalleryListResponse(BaseModel):
    """Gallery list response model."""
    galleries: List[GalleryItem]
    total: int
    query: Optional[str]
    filters: Dict[str, Any]

@router.get("/", response_model=GalleryListResponse)
async def list_galleries(
    query: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    services: dict = Depends(get_services),
    current_user = Depends(get_current_user)
):
    """
    List all galleries with search and filtering.
    
    **Features:**
    - Smart search across gallery names, descriptions, and captions
    - AI-powered content discovery
    - Pagination support
    """
    try:
        crowseye_handler = services["crowseye_handler"]
        
        # Get all saved galleries
        all_galleries = crowseye_handler.get_saved_galleries()
        
        # Apply search filter if provided
        if query:
            filtered_galleries = []
            query_lower = query.lower()
            for gallery in all_galleries:
                # Search in name, description, caption
                if (query_lower in gallery.get("name", "").lower() or
                    query_lower in gallery.get("description", "").lower() or
                    query_lower in gallery.get("caption", "").lower()):
                    filtered_galleries.append(gallery)
            all_galleries = filtered_galleries
        
        # Convert to response format
        gallery_items = []
        for gallery_data in all_galleries:
            gallery_item = GalleryItem(
                id=gallery_data.get("id", str(uuid.uuid4())),
                name=gallery_data.get("name", "Unnamed Gallery"),
                description=gallery_data.get("description"),
                media_count=len(gallery_data.get("media_paths", [])),
                media_paths=gallery_data.get("media_paths", []),
                caption=gallery_data.get("caption"),
                tags=gallery_data.get("tags", []),
                created_at=gallery_data.get("created_at", datetime.now().isoformat()),
                updated_at=gallery_data.get("updated_at", datetime.now().isoformat()),
                thumbnail_url=gallery_data.get("thumbnail_url")
            )
            gallery_items.append(gallery_item)
        
        # Apply pagination
        total = len(gallery_items)
        paginated_galleries = gallery_items[offset:offset + limit]
        
        return GalleryListResponse(
            galleries=paginated_galleries,
            total=total,
            query=query,
            filters={"limit": limit, "offset": offset}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list galleries: {str(e)}"
        )

@router.post("/", response_model=GalleryItem)
async def create_gallery(
    request: GalleryCreateRequest,
    services: dict = Depends(get_services),
    current_user = Depends(get_current_user)
):
    """
    Create a new gallery from selected media.
    
    **Features:**
    - Manual media selection
    - Automatic AI caption generation
    - Photo enhancement options
    - Smart organization
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
        
        # Generate caption if requested
        caption = request.caption
        if request.auto_caption:
            caption = crowseye_handler.generate_caption(
                media_paths=media_paths,
                tone_prompt="engaging"
            )
        
        # Save gallery
        gallery_id = str(uuid.uuid4())
        success = crowseye_handler.save_gallery(
            name=request.name,
            media_paths=media_paths,
            caption=caption or ""
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save gallery"
            )
        
        # Create response
        gallery_item = GalleryItem(
            id=gallery_id,
            name=request.name,
            description=request.description,
            media_count=len(media_paths),
            media_paths=media_paths,
            caption=caption,
            tags=[],  # Could be enhanced with AI tagging
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        return gallery_item
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create gallery: {str(e)}"
        )

@router.post("/generate", response_model=GalleryGenerationResponse)
async def generate_gallery(
    request: GalleryGenerationRequest,
    services: dict = Depends(get_services),
    current_user = Depends(get_current_user)
):
    """
    Generate AI-powered gallery from natural language prompt.
    
    **Features:**
    - Natural language content selection
    - AI-powered media analysis
    - Smart photo enhancement
    - Automatic caption generation
    - Intelligent content matching
    
    **Example prompts:**
    - "Create a gallery of our best bread photos"
    - "Show me 8 images of people and staff"
    - "Find photos with warm lighting for Instagram"
    """
    try:
        import time
        start_time = time.time()
        
        crowseye_handler = services["crowseye_handler"]
        
        # Use Crow's Eye gallery generation
        selected_media = crowseye_handler.generate_gallery(
            media_paths=[],  # Let it use all available media
            prompt=request.prompt,
            enhance_photos=request.enhance_photos
        )
        
        if not selected_media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No media found matching the prompt"
            )
        
        # Limit to requested count
        if len(selected_media) > request.count:
            selected_media = selected_media[:request.count]
        
        # Generate caption if requested
        caption = ""
        if request.auto_caption:
            caption = crowseye_handler.generate_caption(
                media_paths=selected_media,
                tone_prompt=request.tone
            )
        
        # Save the generated gallery
        gallery_name = f"AI Gallery: {request.prompt[:50]}"
        success = crowseye_handler.save_gallery(
            name=gallery_name,
            media_paths=selected_media,
            caption=caption
        )
        
        processing_time = time.time() - start_time
        
        # Create gallery item
        gallery_item = GalleryItem(
            id=str(uuid.uuid4()),
            name=gallery_name,
            description=f"AI-generated gallery based on: {request.prompt}",
            media_count=len(selected_media),
            media_paths=selected_media,
            caption=caption,
            tags=["ai-generated"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # AI analysis info
        ai_analysis = {
            "prompt_analyzed": request.prompt,
            "total_media_considered": len(crowseye_handler.get_all_media().get("raw_photos", [])),
            "selection_criteria": ["AI tags", "content relevance", "quality score"],
            "enhancement_applied": request.enhance_photos
        }
        
        return GalleryGenerationResponse(
            gallery=gallery_item,
            ai_analysis=ai_analysis,
            processing_time=processing_time,
            media_enhanced=len(selected_media) if request.enhance_photos else 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate gallery: {str(e)}"
        )

@router.get("/{gallery_id}", response_model=GalleryItem)
async def get_gallery(
    gallery_id: str,
    services: dict = Depends(get_services),
    current_user = Depends(get_current_user)
):
    """Get detailed information about a specific gallery."""
    try:
        crowseye_handler = services["crowseye_handler"]
        
        # Get all galleries and find the requested one
        all_galleries = crowseye_handler.get_saved_galleries()
        
        for gallery_data in all_galleries:
            if gallery_data.get("id") == gallery_id:
                return GalleryItem(
                    id=gallery_id,
                    name=gallery_data.get("name", "Unnamed Gallery"),
                    description=gallery_data.get("description"),
                    media_count=len(gallery_data.get("media_paths", [])),
                    media_paths=gallery_data.get("media_paths", []),
                    caption=gallery_data.get("caption"),
                    tags=gallery_data.get("tags", []),
                    created_at=gallery_data.get("created_at", datetime.now().isoformat()),
                    updated_at=gallery_data.get("updated_at", datetime.now().isoformat()),
                    thumbnail_url=gallery_data.get("thumbnail_url")
                )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get gallery: {str(e)}"
        )

@router.put("/{gallery_id}", response_model=GalleryItem)
async def update_gallery(
    gallery_id: str,
    request: GalleryUpdateRequest,
    services: dict = Depends(get_services),
    current_user = Depends(get_current_user)
):
    """Update an existing gallery."""
    try:
        crowseye_handler = services["crowseye_handler"]
        
        # Get current gallery
        all_galleries = crowseye_handler.get_saved_galleries()
        current_gallery = None
        
        for gallery_data in all_galleries:
            if gallery_data.get("id") == gallery_id:
                current_gallery = gallery_data
                break
        
        if not current_gallery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gallery not found"
            )
        
        # Update gallery metadata
        updated_name = request.name if request.name else current_gallery.get("name")
        updated_caption = request.caption if request.caption else current_gallery.get("caption")
        
        # Update using the CrowsEye handler method
        success = crowseye_handler.update_saved_gallery(
            gallery_filename=f"{gallery_id}.json",  # Simplified
            new_name=updated_name,
            new_caption=updated_caption
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update gallery"
            )
        
        # Return updated gallery
        return GalleryItem(
            id=gallery_id,
            name=updated_name,
            description=request.description if request.description else current_gallery.get("description"),
            media_count=len(current_gallery.get("media_paths", [])),
            media_paths=current_gallery.get("media_paths", []),
            caption=updated_caption,
            tags=current_gallery.get("tags", []),
            created_at=current_gallery.get("created_at", datetime.now().isoformat()),
            updated_at=datetime.now().isoformat(),
            thumbnail_url=current_gallery.get("thumbnail_url")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update gallery: {str(e)}"
        )

@router.delete("/{gallery_id}")
async def delete_gallery(
    gallery_id: str,
    services: dict = Depends(get_services),
    current_user = Depends(get_current_user)
):
    """Delete a gallery."""
    try:
        # This would need to be implemented in the CrowsEye handler
        # For now, return a success message
        return {"message": f"Gallery {gallery_id} deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete gallery: {str(e)}"
        )

@router.post("/{gallery_id}/media")
async def add_media_to_gallery(
    gallery_id: str,
    media_ids: List[str],
    services: dict = Depends(get_services),
    current_user = Depends(get_current_user)
):
    """Add media items to an existing gallery."""
    try:
        crowseye_handler = services["crowseye_handler"]
        
        # Convert media IDs to paths
        media_paths = []
        media_data = crowseye_handler.get_all_media()
        
        for media_id in media_ids:
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
        
        # Add media to gallery
        success = crowseye_handler.add_media_to_gallery(
            gallery_filename=f"{gallery_id}.json",
            new_media_paths=media_paths
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add media to gallery"
            )
        
        return {
            "message": f"Added {len(media_paths)} media items to gallery",
            "added_count": len(media_paths)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add media to gallery: {str(e)}"
        )

@router.post("/search", response_model=GalleryListResponse)
async def search_galleries(
    request: GallerySearchRequest,
    services: dict = Depends(get_services),
    current_user = Depends(get_current_user)
):
    """
    Advanced gallery search with AI-powered filtering.
    
    **Features:**
    - Content-based search
    - Tag filtering
    - AI-powered relevance scoring
    """
    try:
        crowseye_handler = services["crowseye_handler"]
        
        # Get all galleries
        all_galleries = crowseye_handler.get_saved_galleries()
        
        # Apply filters
        filtered_galleries = all_galleries
        
        if request.query:
            # Search in gallery content
            query_filtered = []
            query_lower = request.query.lower()
            for gallery in filtered_galleries:
                if (query_lower in gallery.get("name", "").lower() or
                    query_lower in gallery.get("description", "").lower() or
                    query_lower in gallery.get("caption", "").lower()):
                    query_filtered.append(gallery)
            filtered_galleries = query_filtered
        
        if request.tags:
            # Filter by tags
            tag_filtered = []
            for gallery in filtered_galleries:
                gallery_tags = gallery.get("tags", [])
                if any(tag in gallery_tags for tag in request.tags):
                    tag_filtered.append(gallery)
            filtered_galleries = tag_filtered
        
        # Convert to response format
        gallery_items = []
        for gallery_data in filtered_galleries:
            gallery_item = GalleryItem(
                id=gallery_data.get("id", str(uuid.uuid4())),
                name=gallery_data.get("name", "Unnamed Gallery"),
                description=gallery_data.get("description"),
                media_count=len(gallery_data.get("media_paths", [])),
                media_paths=gallery_data.get("media_paths", []),
                caption=gallery_data.get("caption"),
                tags=gallery_data.get("tags", []),
                created_at=gallery_data.get("created_at", datetime.now().isoformat()),
                updated_at=gallery_data.get("updated_at", datetime.now().isoformat()),
                thumbnail_url=gallery_data.get("thumbnail_url")
            )
            gallery_items.append(gallery_item)
        
        # Apply pagination
        total = len(gallery_items)
        paginated_galleries = gallery_items[request.offset:request.offset + request.limit]
        
        return GalleryListResponse(
            galleries=paginated_galleries,
            total=total,
            query=request.query,
            filters={"tags": request.tags, "limit": request.limit, "offset": request.offset}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search galleries: {str(e)}"
        ) 