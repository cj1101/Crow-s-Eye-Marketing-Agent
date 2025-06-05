"""
Highlights router for Crow's Eye API.
"""

import os
import sys
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.models.user import User
from src.features.subscription.access_control import Feature
from ..dependencies import get_current_user, require_feature

router = APIRouter()


class HighlightRequest(BaseModel):
    """Highlight reel creation request model."""
    media_ids: List[str]
    duration: Optional[int] = 30  # seconds
    style: Optional[str] = "dynamic"  # dynamic, smooth, energetic, cinematic
    music_style: Optional[str] = "upbeat"  # upbeat, calm, dramatic, none
    text_overlay: Optional[str] = None
    brand_colors: Optional[List[str]] = None  # hex colors
    transitions: Optional[str] = "auto"  # auto, fast, slow, beat-sync


class LongFormHighlightRequest(BaseModel):
    """Long-form highlight reel creation request model for 1-3 hour content."""
    video_path: str
    duration: Optional[int] = 180  # seconds (3 minutes default)
    prompt: Optional[str] = ""  # Natural language description of what to highlight
    cost_optimize: Optional[bool] = True  # Whether to use cost optimization
    style: Optional[str] = "cinematic"  # cinematic, documentary, energetic
    include_chapters: Optional[bool] = False  # Add chapter markers for longer content


class LongFormCostEstimate(BaseModel):
    """Cost estimate for long-form highlight processing."""
    duration_hours: float
    estimated_ai_calls: int
    estimated_cost_usd: float
    processing_time_minutes: str
    recommendations: List[str]


class HighlightResponse(BaseModel):
    """Highlight reel response model."""
    id: str
    media_ids: List[str]
    duration: int
    style: str
    music_style: str
    text_overlay: Optional[str]
    created_at: str
    status: str  # processing, completed, failed
    preview_url: Optional[str]
    download_url: Optional[str]
    progress: Optional[int] = None  # 0-100


class HighlightListResponse(BaseModel):
    """Highlight reel list response model."""
    highlights: List[HighlightResponse]
    total: int


@router.post("/", response_model=HighlightResponse)
async def create_highlight_reel(
    request: HighlightRequest,
    current_user: User = Depends(require_feature(Feature.HIGHLIGHT_REEL_GENERATOR))
):
    """
    Create 30-second highlight reel from media.
    
    **Tier Required:** Creator+ ($9/month and above)
    
    AI-powered video editing creates engaging highlight reels with:
    - Automatic scene detection and best moment selection
    - Music synchronization and beat matching
    - Professional transitions and effects
    - Brand color integration
    - Text overlays and captions
    """
    if not request.media_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one media item is required"
        )
    
    if len(request.media_ids) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 3 media items are recommended for a good highlight reel"
        )
    
    # This is a simplified implementation
    # In production, you'd integrate with the actual video processing logic
    
    import uuid
    from datetime import datetime
    
    highlight_id = str(uuid.uuid4())
    
    # Mock highlight reel creation
    # In production, this would:
    # 1. Queue the video processing job
    # 2. Analyze media for best moments
    # 3. Generate the highlight reel
    # 4. Add music and effects
    
    return HighlightResponse(
        id=highlight_id,
        media_ids=request.media_ids,
        duration=request.duration,
        style=request.style,
        music_style=request.music_style,
        text_overlay=request.text_overlay,
        created_at=datetime.now().isoformat(),
        status="processing",
        progress=0
    )


@router.post("/long-form", response_model=HighlightResponse)
async def create_long_form_highlight_reel(
    request: LongFormHighlightRequest,
    current_user: User = Depends(require_feature(Feature.HIGHLIGHT_REEL_GENERATOR))
):
    """
    Create long-form highlight reel (2-5 minutes) from 1-3 hour content.
    
    **Tier Required:** Creator+ ($9/month and above)
    
    Cost-optimized processing for long-form content:
    - Intelligent sampling to minimize AI costs
    - Technical analysis for motion and audio activity
    - Smart segment selection based on prompt
    - Enhanced transitions for longer content
    - Estimated cost: $0.10-$0.50 per hour of content
    
    **Note:** Processing time: 5-15 minutes for 1-3 hour content
    """
    import uuid
    from datetime import datetime
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Long-form highlight request from user {current_user.email}")
    
    try:
        # Input validation
        if not request.video_path or not isinstance(request.video_path, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid video path provided"
            )
        
        if request.duration < 30 or request.duration > 600:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duration must be between 30 seconds and 10 minutes"
            )
        
        # Sanitize prompt
        if request.prompt:
            prompt = request.prompt.strip()[:500]  # Limit prompt length
        else:
            prompt = ""
        
        # Import video handler
        from src.features.media_processing.video_handler import VideoHandler
        
        video_handler = VideoHandler()
        
        # Validate file exists and is accessible
        if not os.path.exists(request.video_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Video file not found: {request.video_path}"
            )
        
        # Check file permissions and size
        try:
            file_size = os.path.getsize(request.video_path)
            if file_size == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Video file is empty"
                )
            if file_size > 10 * 1024 * 1024 * 1024:  # 10GB limit
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Video file is too large (>10GB)"
                )
        except (OSError, IOError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot access video file: {str(e)}"
            )
        
        # Get video info with timeout
        try:
            video_info = video_handler.get_video_info(request.video_path)
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not read video file: {str(e)}"
            )
        
        if not video_info or 'duration' not in video_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not read video file information"
            )
        
        duration_seconds = video_info.get('duration', 0)
        duration_hours = duration_seconds / 3600
        
        # Validate video duration
        if duration_hours > 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video is too long (>4 hours). Please use shorter content."
            )
        
        if duration_hours < 0.5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video is too short (<30 minutes). Use regular highlight reel endpoint."
            )
        
        # Check video quality
        width = video_info.get('width', 0)
        height = video_info.get('height', 0)
        if width < 100 or height < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video resolution too low (minimum 100x100)"
            )
        
        # Estimate cost and warn if high
        estimated_cost = 0.1 * duration_hours if request.cost_optimize else 0.5 * duration_hours
        if estimated_cost > 2.0:
            logger.warning(f"High cost estimate: ${estimated_cost:.2f} for user {current_user.email}")
        
        logger.info(f"Processing {duration_hours:.1f}h video, estimated cost: ${estimated_cost:.2f}")
        
        # Generate highlight reel with comprehensive error handling
        try:
            success, output_path, message = video_handler.generate_long_form_highlight_reel(
                video_path=request.video_path,
                target_duration=request.duration,
                prompt=prompt,
                cost_optimize=request.cost_optimize
            )
        except Exception as e:
            logger.error(f"Error in video processing: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Video processing failed: {str(e)}"
            )
        
        if not success:
            logger.error(f"Video processing failed: {message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create highlight reel: {message}"
            )
        
        # Verify output file exists
        if not output_path or not os.path.exists(output_path):
            logger.error(f"Output file not found: {output_path}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Highlight reel was not created properly"
            )
        
        highlight_id = str(uuid.uuid4())
        
        logger.info(f"Successfully created highlight reel: {output_path}")
        
        return HighlightResponse(
            id=highlight_id,
            media_ids=[request.video_path],
            duration=request.duration,
            style=request.style,
            music_style="cinematic",
            text_overlay=f"Generated from {duration_hours:.1f}h content",
            created_at=datetime.now().isoformat(),
            status="completed",
            preview_url=f"/api/highlights/{highlight_id}/preview",
            download_url=output_path,
            progress=100
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in long-form highlight generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{highlight_id}", response_model=HighlightResponse)
async def get_highlight_reel(
    highlight_id: str,
    current_user: User = Depends(require_feature(Feature.HIGHLIGHT_REEL_GENERATOR))
):
    """
    Get highlight reel by ID.
    
    **Tier Required:** Creator+ ($9/month and above)
    """
    # This is a simplified implementation
    # In production, you'd look up the highlight reel by ID in a database
    
    from datetime import datetime
    
    return HighlightResponse(
        id=highlight_id,
        media_ids=["media_1", "media_2", "media_3"],
        duration=30,
        style="dynamic",
        music_style="upbeat",
        text_overlay="Amazing highlights!",
        created_at=datetime.now().isoformat(),
        status="completed",
        preview_url=f"/highlights/{highlight_id}/preview",
        download_url=f"/highlights/{highlight_id}/download",
        progress=100
    )


@router.get("/", response_model=HighlightListResponse)
async def list_highlight_reels(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,  # processing, completed, failed
    current_user: User = Depends(require_feature(Feature.HIGHLIGHT_REEL_GENERATOR))
):
    """
    List user's highlight reels.
    
    **Tier Required:** Creator+ ($9/month and above)
    """
    # This is a simplified implementation
    # In production, you'd query the database for user's highlight reels
    
    from datetime import datetime
    
    # Mock highlight reel list
    highlights = []
    for i in range(min(limit, 5)):  # Return up to 5 mock items
        item_status = status or ("completed" if i % 3 != 0 else "processing")
        highlights.append(HighlightResponse(
            id=f"highlight_{i + offset}",
            media_ids=[f"media_{j}" for j in range(3, 6)],
            duration=30,
            style="dynamic",
            music_style="upbeat",
            text_overlay=f"Highlight {i + offset + 1}",
            created_at=datetime.now().isoformat(),
            status=item_status,
            preview_url=f"/highlights/highlight_{i + offset}/preview" if item_status == "completed" else None,
            download_url=f"/highlights/highlight_{i + offset}/download" if item_status == "completed" else None,
            progress=100 if item_status == "completed" else 45
        ))
    
    return HighlightListResponse(
        highlights=highlights,
        total=len(highlights)
    )


@router.delete("/{highlight_id}")
async def delete_highlight_reel(
    highlight_id: str,
    current_user: User = Depends(require_feature(Feature.HIGHLIGHT_REEL_GENERATOR))
):
    """
    Delete highlight reel by ID.
    
    **Tier Required:** Creator+ ($9/month and above)
    """
    # This is a simplified implementation
    # In production, you'd delete from database and file system
    
    return {"message": f"Highlight reel {highlight_id} deleted successfully"}


@router.post("/long-form/estimate", response_model=LongFormCostEstimate)
async def estimate_long_form_cost(
    video_path: str,
    cost_optimize: bool = True,
    current_user: User = Depends(require_feature(Feature.HIGHLIGHT_REEL_GENERATOR))
):
    """
    Estimate cost and processing time for long-form highlight generation.
    
    **Tier Required:** Creator+ ($9/month and above)
    
    Get cost and time estimates before processing your long-form content.
    """
    try:
        from src.features.media_processing.video_handler import VideoHandler
        
        video_handler = VideoHandler()
        
        # Validate file exists
        if not os.path.exists(video_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Video file not found: {video_path}"
            )
        
        # Get video info
        video_info = video_handler.get_video_info(video_path)
        if not video_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not read video file information"
            )
        
        duration_hours = video_info.get('duration', 0) / 3600
        
        if duration_hours > 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video is too long (>4 hours). Please use shorter content."
            )
        
        if duration_hours < 0.5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video is too short (<30 minutes). Use regular highlight reel endpoint."
            )
        
        # Calculate estimates
        if cost_optimize:
            ai_calls = min(20, max(5, int(duration_hours * 5)))  # 5-20 calls for optimized
            cost_usd = ai_calls * 0.01  # $0.01 per call estimate
            processing_time = f"{5 + duration_hours * 2:.0f}-{10 + duration_hours * 3:.0f}"
        else:
            ai_calls = int(duration_hours * 30)  # 30 calls per hour for full analysis
            cost_usd = ai_calls * 0.01
            processing_time = f"{10 + duration_hours * 5:.0f}-{20 + duration_hours * 8:.0f}"
        
        # Generate recommendations
        recommendations = []
        if duration_hours > 2:
            recommendations.append("Consider using cost optimization for videos longer than 2 hours")
        if cost_usd > 1.0:
            recommendations.append("High cost detected - ensure this is important content")
        if duration_hours > 3:
            recommendations.append("Consider splitting very long content into shorter segments")
        if not cost_optimize:
            recommendations.append("Enable cost optimization to reduce AI analysis costs by 70-80%")
        
        recommendations.append(f"Estimated savings with optimization: ${(ai_calls * 0.7 * 0.01):.2f}")
        
        return LongFormCostEstimate(
            duration_hours=duration_hours,
            estimated_ai_calls=ai_calls,
            estimated_cost_usd=cost_usd,
            processing_time_minutes=processing_time,
            recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error estimating cost: {str(e)}"
        )


class HighlightStyleResponse(BaseModel):
    """Highlight style response model."""
    id: str
    name: str
    description: str
    preview_url: str
    duration_range: str
    best_for: List[str]


@router.get("/styles/", response_model=List[HighlightStyleResponse])
async def list_highlight_styles(
    current_user: User = Depends(require_feature(Feature.HIGHLIGHT_REEL_GENERATOR))
):
    """
    List available highlight reel styles.
    
    **Tier Required:** Creator+ ($9/month and above)
    """
    # Mock style list
    styles = [
        HighlightStyleResponse(
            id="dynamic",
            name="Dynamic",
            description="Fast-paced editing with quick cuts and energetic transitions",
            preview_url="/styles/dynamic/preview.mp4",
            duration_range="15-60 seconds",
            best_for=["Sports", "Events", "Product launches"]
        ),
        HighlightStyleResponse(
            id="smooth",
            name="Smooth",
            description="Flowing transitions with elegant pacing",
            preview_url="/styles/smooth/preview.mp4",
            duration_range="30-90 seconds",
            best_for=["Lifestyle", "Travel", "Fashion"]
        ),
        HighlightStyleResponse(
            id="energetic",
            name="Energetic",
            description="High-energy cuts synchronized to music beats",
            preview_url="/styles/energetic/preview.mp4",
            duration_range="15-45 seconds",
            best_for=["Fitness", "Music", "Dance"]
        ),
        HighlightStyleResponse(
            id="cinematic",
            name="Cinematic",
            description="Professional film-style editing with dramatic pacing",
            preview_url="/styles/cinematic/preview.mp4",
            duration_range="45-120 seconds",
            best_for=["Brand stories", "Documentaries", "Testimonials"]
        )
    ]
    
    return styles


@router.get("/{highlight_id}/status")
async def get_highlight_status(
    highlight_id: str,
    current_user: User = Depends(require_feature(Feature.HIGHLIGHT_REEL_GENERATOR))
):
    """
    Get processing status of highlight reel.
    
    **Tier Required:** Creator+ ($9/month and above)
    """
    # Mock status response
    return {
        "id": highlight_id,
        "status": "processing",
        "progress": 75,
        "estimated_completion": "2 minutes",
        "current_step": "Adding music and effects"
    } 