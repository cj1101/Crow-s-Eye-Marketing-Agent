"""
Platform Compliance API Endpoints

Provides platform compliance validation for all supported social media platforms.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from crow_eye_api.services.platform_compliance_service import PlatformComplianceService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_compliance_service() -> PlatformComplianceService:
    """Dependency to get compliance service."""
    return PlatformComplianceService()


@router.get("/platform-compliance/platforms")
async def get_supported_platforms(
    compliance_service: PlatformComplianceService = Depends(get_compliance_service)
):
    """
    Get list of all supported platforms with basic information.
    
    Returns:
    - List of supported platforms
    - Platform display names
    - Basic capabilities
    """
    try:
        platforms_info = []
        
        for platform_id, config in compliance_service.platforms.items():
            platforms_info.append({
                "platform_id": platform_id,
                "display_name": config["display_name"],
                "supports_images": "image" in config["media"],
                "supports_videos": "video" in config["media"],
                "supports_links": config["content"]["supports_links"],
                "business_account_required": config["posting"].get("business_account_required", False)
            })
        
        logger.info(f"Retrieved {len(platforms_info)} supported platforms")
        
        return {
            "status": "success",
            "platforms": platforms_info,
            "total_platforms": len(platforms_info)
        }
        
    except Exception as e:
        logger.error(f"Error getting supported platforms: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving platforms: {str(e)}")


@router.get("/platform-compliance/platforms/{platform_id}")
async def get_platform_details(
    platform_id: str,
    compliance_service: PlatformComplianceService = Depends(get_compliance_service)
):
    """
    Get detailed information about a specific platform.
    
    Returns:
    - Platform requirements
    - Content limitations
    - Media specifications
    - Posting requirements
    """
    try:
        platform_info = compliance_service.get_platform_info(platform_id)
        
        if not platform_info:
            raise HTTPException(status_code=404, detail=f"Platform '{platform_id}' not found")
        
        logger.info(f"Retrieved platform details for {platform_id}")
        
        return {
            "status": "success",
            "platform_id": platform_id,
            "platform_info": platform_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting platform details for {platform_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving platform details: {str(e)}")


@router.post("/platform-compliance/validate")
async def validate_content(
    content_data: Dict[str, Any],
    compliance_service: PlatformComplianceService = Depends(get_compliance_service)
):
    """
    Validate content against platform-specific requirements.
    
    Request body should include:
    - platform: Target platform ID
    - content_type: "image", "video", or "text"
    - caption: Content caption/description
    - media_size_mb: File size in MB (optional)
    - media_format: File format (optional)
    - hashtags: List of hashtags (optional)
    - mentions: List of mentions (optional)
    
    Returns:
    - Validation result
    - Compliance score
    - Errors and warnings
    - Optimization suggestions
    """
    try:
        platform = content_data.get("platform")
        content_type = content_data.get("content_type")
        
        if not platform:
            raise HTTPException(status_code=400, detail="Platform is required")
        
        if not content_type:
            raise HTTPException(status_code=400, detail="Content type is required")
        
        # Extract content data
        validation_data = {
            "caption": content_data.get("caption", ""),
            "media_size_mb": content_data.get("media_size_mb"),
            "media_format": content_data.get("media_format"),
            "hashtags": content_data.get("hashtags", []),
            "mentions": content_data.get("mentions", [])
        }
        
        # Validate content
        result = compliance_service.validate_content(platform, content_type, **validation_data)
        
        logger.info(f"Content validation completed for {platform}. Score: {result['compliance_score']:.1f}%")
        
        return {
            "status": "success",
            "validation_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during content validation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.post("/platform-compliance/validate-bulk")
async def validate_bulk_content(
    content_data: Dict[str, Any],
    compliance_service: PlatformComplianceService = Depends(get_compliance_service)
):
    """
    Validate content against multiple platforms simultaneously.
    
    Request body should include:
    - platforms: List of platform IDs
    - content_type: "image", "video", or "text"
    - caption: Content caption/description
    - media_size_mb: File size in MB (optional)
    - media_format: File format (optional)
    - hashtags: List of hashtags (optional)
    - mentions: List of mentions (optional)
    
    Returns:
    - Overall compliance score
    - Platform-specific results
    - Cross-platform suggestions
    - Recommended platforms
    """
    try:
        platforms = content_data.get("platforms", [])
        content_type = content_data.get("content_type")
        
        if not platforms:
            raise HTTPException(status_code=400, detail="At least one platform is required")
        
        if not content_type:
            raise HTTPException(status_code=400, detail="Content type is required")
        
        # Extract content data
        validation_data = {
            "caption": content_data.get("caption", ""),
            "media_size_mb": content_data.get("media_size_mb"),
            "media_format": content_data.get("media_format"),
            "hashtags": content_data.get("hashtags", []),
            "mentions": content_data.get("mentions", [])
        }
        
        # Validate content across platforms
        result = compliance_service.validate_bulk_content(platforms, content_type, **validation_data)
        
        logger.info(f"Bulk validation completed for {len(platforms)} platforms. Overall score: {result['overall_score']:.1f}%")
        
        return {
            "status": "success",
            "bulk_validation_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during bulk validation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bulk validation failed: {str(e)}")


@router.get("/platform-compliance/quick-check")
async def quick_compliance_check(
    platform: str = Query(..., description="Platform to check"),
    caption_length: Optional[int] = Query(None, description="Caption length to check"),
    media_size_mb: Optional[float] = Query(None, description="Media size in MB to check"),
    hashtag_count: Optional[int] = Query(None, description="Number of hashtags to check"),
    compliance_service: PlatformComplianceService = Depends(get_compliance_service)
):
    """
    Quick compliance check for basic content parameters.
    
    Query parameters:
    - platform: Platform ID to check against
    - caption_length: Length of caption to validate (optional)
    - media_size_mb: Media file size in MB (optional)
    - hashtag_count: Number of hashtags (optional)
    
    Returns:
    - Quick validation result
    - Basic compliance indicators
    """
    try:
        platform_info = compliance_service.get_platform_info(platform)
        
        if not platform_info:
            raise HTTPException(status_code=404, detail=f"Platform '{platform}' not found")
        
        issues = []
        warnings = []
        
        # Check caption length
        if caption_length is not None:
            max_caption = platform_info["content"]["max_caption_length"]
            if caption_length > max_caption:
                issues.append(f"Caption length ({caption_length}) exceeds limit ({max_caption})")
            elif caption_length > max_caption * 0.9:
                warnings.append(f"Caption length is close to limit ({max_caption})")
        
        # Check media size
        if media_size_mb is not None:
            # Assume image for quick check
            if "image" in platform_info["media"]:
                max_size = platform_info["media"]["image"]["max_file_size_mb"]
                if media_size_mb > max_size:
                    issues.append(f"Media size ({media_size_mb}MB) exceeds limit ({max_size}MB)")
        
        # Check hashtag count
        if hashtag_count is not None:
            max_hashtags = platform_info["content"]["max_hashtags"]
            if hashtag_count > max_hashtags:
                issues.append(f"Hashtag count ({hashtag_count}) exceeds limit ({max_hashtags})")
        
        is_compliant = len(issues) == 0
        
        logger.info(f"Quick compliance check for {platform}: {'PASS' if is_compliant else 'FAIL'}")
        
        return {
            "status": "success",
            "platform": platform,
            "is_compliant": is_compliant,
            "issues": issues,
            "warnings": warnings,
            "platform_limits": {
                "max_caption_length": platform_info["content"]["max_caption_length"],
                "max_hashtags": platform_info["content"]["max_hashtags"],
                "max_image_size_mb": platform_info["media"].get("image", {}).get("max_file_size_mb"),
                "max_video_size_mb": platform_info["media"].get("video", {}).get("max_file_size_mb")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during quick compliance check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quick check failed: {str(e)}")


@router.get("/platform-compliance/health")
async def platform_compliance_health():
    """
    Health check endpoint for platform compliance service.
    """
    try:
        service = PlatformComplianceService()
        platform_count = len(service.platforms)
        
        return {
            "status": "healthy",
            "service": "Platform Compliance",
            "supported_platforms": platform_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}") 