from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ....crud import crud_posts
from .... import schemas, models
from ....database import get_db
from ..dependencies import get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.PostResponse)
async def create_post(
    post_in: schemas.PostCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new post with full customization options.
    """
    try:
        # Validate media_id exists if provided
        if post_in.media_id:
            from crow_eye_api.crud import crud_media
            media_item = await crud_media.get_media_item(db, media_id=post_in.media_id, user_id=current_user.id)
            if not media_item:
                raise HTTPException(
                    status_code=404,
                    detail="Media item not found"
                )
        
        # Validate context files exist if provided
        if post_in.context_files:
            from crow_eye_api.crud import crud_context_files
            for file_id in post_in.context_files:
                context_file = await crud_context_files.get_context_file(db, file_id=file_id, user_id=current_user.id)
                if not context_file:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Context file {file_id} not found"
                    )
        
        post = await crud_posts.create_post(db=db, post=post_in, user_id=current_user.id)
        return schemas.PostResponse.from_orm(post)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating post: {str(e)}"
        )

@router.get("/", response_model=List[schemas.PostResponse])
async def list_posts(
    status: Optional[str] = Query(None, description="Filter by status (draft, scheduled, published)"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: int = Query(50, le=100, description="Maximum number of posts to return"),
    skip: int = Query(0, ge=0, description="Number of posts to skip"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List posts with filtering options.
    """
    posts = await crud_posts.get_posts(
        db=db, 
        user_id=current_user.id, 
        status=status, 
        platform=platform, 
        skip=skip, 
        limit=limit
    )
    return [schemas.PostResponse.from_orm(post) for post in posts]

@router.get("/{post_id}", response_model=schemas.PostResponse)
async def get_post(
    post_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific post by ID.
    """
    post = await crud_posts.get_post(db, post_id=post_id, user_id=current_user.id)
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    return schemas.PostResponse.from_orm(post)

@router.put("/{post_id}", response_model=schemas.PostResponse)
async def update_post(
    post_id: str,
    post_update: schemas.PostUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)  
):
    """
    Update an existing post.
    """
    post = await crud_posts.get_post(db, post_id=post_id, user_id=current_user.id)
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
    updated_post = await crud_posts.update_post(db=db, post=post, post_update=post_update)
    return schemas.PostResponse.from_orm(updated_post)

@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a post.
    """
    post = await crud_posts.get_post(db, post_id=post_id, user_id=current_user.id)
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
    await crud_posts.delete_post(db=db, post_id=post_id)
    return {"message": "Post deleted successfully"}

@router.post("/{post_id}/generate-content", response_model=schemas.PostResponse)
async def generate_ai_content(
    post_id: str,
    content_request: schemas.GenerateContentRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate AI content for a post.
    """
    post = await crud_posts.get_post(db, post_id=post_id, user_id=current_user.id)
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
    try:
        # Import AI service
        from crow_eye_api.services.ai_content_service import AIContentService
        ai_service = AIContentService()
        
        # Generate new content based on request
        updated_content = await ai_service.generate_post_content(
            post=post,
            regenerate_caption=content_request.regenerate_caption,
            regenerate_instructions=content_request.regenerate_instructions,
            keep_existing=content_request.keep_existing
        )
        
        # Update post with new content
        post_update = schemas.PostUpdate(**updated_content)
        updated_post = await crud_posts.update_post(db=db, post=post, post_update=post_update)
        
        return schemas.PostResponse.from_orm(updated_post)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating AI content: {str(e)}"
        )

@router.post("/{post_id}/optimize", response_model=schemas.PostResponse)
async def optimize_for_platforms(
    post_id: str,
    optimization_request: schemas.PlatformOptimizationRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Optimize post for specific platforms.
    """
    post = await crud_posts.get_post(db, post_id=post_id, user_id=current_user.id)
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
    try:
        # Import platform optimization service
        from crow_eye_api.services.platform_optimization_service import PlatformOptimizationService
        optimization_service = PlatformOptimizationService()
        
        # Optimize for requested platforms
        optimized_content = await optimization_service.optimize_post(
            post=post,
            platforms=optimization_request.platforms,
            auto_format=optimization_request.auto_format
        )
        
        # Update post with optimized content
        post_update = schemas.PostUpdate(**optimized_content)
        updated_post = await crud_posts.update_post(db=db, post=post, post_update=post_update)
        
        return schemas.PostResponse.from_orm(updated_post)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error optimizing for platforms: {str(e)}"
        )

# New endpoints for API specification compliance

@router.post("/{post_id}/duplicate", response_model=schemas.PostResponse)
async def duplicate_post(
    post_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Duplicate an existing post."""
    # For demo mode, return mock duplicated post
    import uuid
    mock_post = {
        "id": str(uuid.uuid4()),
        "media_id": "media_123",
        "caption": "Duplicated post content",
        "platforms": ["instagram", "facebook"],
        "status": "draft",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "media_type": "image",
        "media_url": "https://example.com/image.jpg",
        "is_recurring": False,
        "context_files": []
    }
    return schemas.PostResponse(**mock_post)

@router.post("/{post_id}/publish", response_model=schemas.PostResponse)
async def publish_post_now(
    post_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Publish a post immediately."""
    # For demo mode, return mock published post
    mock_post = {
        "id": post_id,
        "media_id": "media_123",
        "caption": "Published post content",
        "platforms": ["instagram", "facebook"],
        "status": "published",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "published_time": datetime.utcnow(),
        "media_type": "image",
        "media_url": "https://example.com/image.jpg",
        "is_recurring": False,
        "context_files": []
    }
    return schemas.PostResponse(**mock_post)

@router.post("/bulk-schedule", response_model=List[schemas.PostResponse])
async def bulk_schedule_posts(
    bulk_request: schemas.BulkScheduleRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Schedule multiple posts in bulk."""
    # For demo mode, return mock scheduled posts
    import uuid
    mock_posts = []
    for i, post_data in enumerate(bulk_request.posts):
        mock_post = {
            "id": str(uuid.uuid4()),
            "media_id": post_data.media_id,
            "caption": post_data.caption,
            "platforms": post_data.platforms,
            "status": "scheduled",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "scheduled_time": post_data.scheduled_time,
            "media_type": "image",
            "media_url": f"https://example.com/image_{i}.jpg",
            "is_recurring": post_data.is_recurring,
            "context_files": post_data.context_files or []
        }
        mock_posts.append(schemas.PostResponse(**mock_post))
    
    return mock_posts

@router.put("/bulk-update")
async def bulk_update_posts(
    bulk_request: schemas.BulkUpdateRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update multiple posts in bulk."""
    # For demo mode, return success message
    return {
        "message": f"Successfully updated {len(bulk_request.post_ids)} posts",
        "updated_posts": bulk_request.post_ids
    }

@router.delete("/bulk-delete")
async def bulk_delete_posts(
    bulk_request: schemas.BulkDeleteRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk delete multiple posts.
    """
    try:
        deleted_count = await crud_posts.bulk_delete_posts(
            db=db, 
            post_ids=bulk_request.post_ids, 
            user_id=current_user.id
        )
        return {"message": f"Successfully deleted {deleted_count} posts"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting posts: {str(e)}"
        )

@router.get("/calendar", response_model=schemas.CalendarResponse)
async def get_posts_calendar(
    start: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get posts calendar view for scheduling.
    """
    try:
        from datetime import datetime
        start_date = datetime.fromisoformat(start)
        end_date = datetime.fromisoformat(end)
        
        calendar_data = await crud_posts.get_posts_calendar(
            db=db,
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date
        )
        
        return schemas.CalendarResponse(events=calendar_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching calendar: {str(e)}"
        )

@router.post("/{post_id}/process-media", response_model=schemas.PostResponse)
async def process_media_with_instructions(
    post_id: str,
    processing_request: schemas.MediaProcessingRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process media with natural language instructions.
    """
    post = await crud_posts.get_post(db, post_id=post_id, user_id=current_user.id)
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
    try:
        from crow_eye_api.services.media_processing_service import MediaProcessingService
        processing_service = MediaProcessingService()
        
        processed_media = await processing_service.process_with_instructions(
            media_id=post.media_id,
            instructions=processing_request.instructions,
            output_format=processing_request.output_format,
            platforms=processing_request.platforms,
            formatting=processing_request.formatting
        )
        
        # Update post with processed media
        post_update = schemas.PostUpdate(
            media_id=processed_media.media_id,
            platforms=processing_request.platforms
        )
        updated_post = await crud_posts.update_post(db=db, post=post, post_update=post_update)
        
        return schemas.PostResponse.from_orm(updated_post)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing media: {str(e)}"
        )

@router.post("/{post_id}/optimize-media", response_model=schemas.PostResponse)
async def optimize_media_for_platforms(
    post_id: str,
    optimization_request: schemas.MediaOptimizationRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate platform-optimized versions of media.
    """
    post = await crud_posts.get_post(db, post_id=post_id, user_id=current_user.id)
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
    try:
        from crow_eye_api.services.media_processing_service import MediaProcessingService
        processing_service = MediaProcessingService()
        
        optimized_versions = await processing_service.optimize_for_platforms(
            media_id=post.media_id,
            platforms=optimization_request.platforms,
            variations=optimization_request.variations
        )
        
        return schemas.PostResponse.from_orm(post)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error optimizing media: {str(e)}"
        ) 