"""
Enhanced Platform Compliance API Endpoints

Provides comprehensive compliance validation and monitoring for all social media platforms.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from crow_eye_api.services.enhanced_platform_compliance import EnhancedPlatformComplianceService
from crow_eye_api.schemas import PlatformRequirementsResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def get_enhanced_compliance_service() -> EnhancedPlatformComplianceService:
    """Dependency to get enhanced compliance service."""
    return EnhancedPlatformComplianceService()


@router.get("/compliance/comprehensive-check")
async def comprehensive_compliance_check(
    platforms: Optional[List[str]] = Query(None, description="Specific platforms to check (all if not specified)"),
    compliance_service: EnhancedPlatformComplianceService = Depends(get_enhanced_compliance_service)
):
    """
    Perform comprehensive compliance check across all or specified platforms.
    
    Checks:
    - API version compliance
    - Rate limiting implementation
    - Authentication requirements
    - Content policy compliance
    - Privacy and data protection compliance
    
    Returns detailed compliance scores and recommendations.
    """
    try:
        logger.info(f"Starting comprehensive compliance check for platforms: {platforms or 'all'}")
        
        results = await compliance_service.comprehensive_compliance_check(platforms)
        
        logger.info(f"Compliance check completed. Overall score: {results['overall_compliance_score']:.1f}%")
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "compliance_results": results
        }
        
    except Exception as e:
        logger.error(f"Error during comprehensive compliance check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Compliance check failed: {str(e)}")


@router.get("/compliance/platform/{platform_id}")
async def get_platform_compliance_details(
    platform_id: str,
    compliance_service: EnhancedPlatformComplianceService = Depends(get_enhanced_compliance_service)
):
    """
    Get detailed compliance requirements and current status for a specific platform.
    
    Includes:
    - Content requirements (caption length, hashtag limits, etc.)
    - Media specifications (formats, file sizes, resolutions)
    - Rate limiting configuration
    - Authentication requirements
    - Content policy restrictions
    - Privacy compliance requirements
    """
    try:
        requirements = compliance_service.get_platform_requirements(platform_id)
        
        if "error" in requirements:
            raise HTTPException(status_code=404, detail=requirements["error"])
        
        logger.info(f"Platform requirements retrieved for {platform_id}")
        
        return {
            "status": "success",
            "platform_requirements": requirements,
            "last_updated": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting platform requirements for {platform_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving platform requirements: {str(e)}")


@router.get("/compliance/platforms/summary")
async def get_all_platforms_summary(
    compliance_service: EnhancedPlatformComplianceService = Depends(get_enhanced_compliance_service)
):
    """
    Get summary of all supported platforms with key compliance information.
    
    Provides overview of:
    - Total supported platforms
    - Platform-specific capabilities
    - Compliance overview (GDPR, CCPA, business account requirements)
    - API versions and status
    """
    try:
        summary = compliance_service.get_all_platforms_summary()
        
        logger.info(f"Platform summary retrieved for {summary['total_platforms']} platforms")
        
        return {
            "status": "success",
            "platforms_summary": summary,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting platforms summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving platforms summary: {str(e)}")


@router.get("/compliance/rate-limits")
async def get_platform_rate_limits(
    platform: Optional[str] = Query(None, description="Specific platform (all if not specified)"),
    compliance_service: EnhancedPlatformComplianceService = Depends(get_enhanced_compliance_service)
):
    """
    Get rate limiting information for platforms.
    
    Returns:
    - Requests per minute/hour/day limits
    - Burst limits
    - Cooldown periods
    - Current usage (if available)
    """
    try:
        if platform:
            requirements = compliance_service.get_platform_requirements(platform)
            if "error" in requirements:
                raise HTTPException(status_code=404, detail=requirements["error"])
            
            rate_limits = {
                platform: {
                    "display_name": requirements["display_name"],
                    "rate_limits": requirements["rate_limits"]
                }
            }
        else:
            summary = compliance_service.get_all_platforms_summary()
            rate_limits = {}
            
            for platform_id in summary["platforms"]:
                requirements = compliance_service.get_platform_requirements(platform_id)
                rate_limits[platform_id] = {
                    "display_name": requirements["display_name"],
                    "rate_limits": requirements["rate_limits"]
                }
        
        logger.info(f"Rate limits retrieved for {len(rate_limits)} platform(s)")
        
        return {
            "status": "success",
            "rate_limits": rate_limits,
            "last_updated": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rate limits: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving rate limits: {str(e)}")


@router.get("/compliance/authentication-requirements")
async def get_authentication_requirements(
    platform: Optional[str] = Query(None, description="Specific platform (all if not specified)"),
    compliance_service: EnhancedPlatformComplianceService = Depends(get_enhanced_compliance_service)
):
    """
    Get authentication requirements for platforms.
    
    Returns:
    - Authentication type (OAuth2, API key, username/password)
    - Required scopes
    - Business account requirements
    - Verification requirements
    - Token refresh requirements
    """
    try:
        if platform:
            requirements = compliance_service.get_platform_requirements(platform)
            if "error" in requirements:
                raise HTTPException(status_code=404, detail=requirements["error"])
            
            auth_requirements = {
                platform: {
                    "display_name": requirements["display_name"],
                    "authentication": requirements["authentication"]
                }
            }
        else:
            summary = compliance_service.get_all_platforms_summary()
            auth_requirements = {}
            
            for platform_id in summary["platforms"]:
                requirements = compliance_service.get_platform_requirements(platform_id)
                auth_requirements[platform_id] = {
                    "display_name": requirements["display_name"],
                    "authentication": requirements["authentication"]
                }
        
        logger.info(f"Authentication requirements retrieved for {len(auth_requirements)} platform(s)")
        
        return {
            "status": "success",
            "authentication_requirements": auth_requirements,
            "last_updated": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting authentication requirements: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving authentication requirements: {str(e)}")


@router.get("/compliance/content-policies")
async def get_content_policies(
    platform: Optional[str] = Query(None, description="Specific platform (all if not specified)"),
    compliance_service: EnhancedPlatformComplianceService = Depends(get_enhanced_compliance_service)
):
    """
    Get content policy requirements for platforms.
    
    Returns:
    - Prohibited content types
    - Required disclosures
    - Age restrictions
    - Geographic restrictions
    - Content moderation requirements
    """
    try:
        if platform:
            requirements = compliance_service.get_platform_requirements(platform)
            if "error" in requirements:
                raise HTTPException(status_code=404, detail=requirements["error"])
            
            content_policies = {
                platform: {
                    "display_name": requirements["display_name"],
                    "content_policy": requirements["content_policy"]
                }
            }
        else:
            summary = compliance_service.get_all_platforms_summary()
            content_policies = {}
            
            for platform_id in summary["platforms"]:
                requirements = compliance_service.get_platform_requirements(platform_id)
                content_policies[platform_id] = {
                    "display_name": requirements["display_name"],
                    "content_policy": requirements["content_policy"]
                }
        
        logger.info(f"Content policies retrieved for {len(content_policies)} platform(s)")
        
        return {
            "status": "success",
            "content_policies": content_policies,
            "last_updated": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting content policies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving content policies: {str(e)}")


@router.get("/compliance/privacy-requirements")
async def get_privacy_requirements(
    platform: Optional[str] = Query(None, description="Specific platform (all if not specified)"),
    compliance_service: EnhancedPlatformComplianceService = Depends(get_enhanced_compliance_service)
):
    """
    Get privacy and data protection requirements for platforms.
    
    Returns:
    - GDPR compliance status
    - CCPA compliance status
    - Data retention policies
    - User consent requirements
    - Audit logging requirements
    """
    try:
        if platform:
            requirements = compliance_service.get_platform_requirements(platform)
            if "error" in requirements:
                raise HTTPException(status_code=404, detail=requirements["error"])
            
            privacy_requirements = {
                platform: {
                    "display_name": requirements["display_name"],
                    "compliance_requirements": requirements["compliance_requirements"]
                }
            }
        else:
            summary = compliance_service.get_all_platforms_summary()
            privacy_requirements = {}
            
            for platform_id in summary["platforms"]:
                requirements = compliance_service.get_platform_requirements(platform_id)
                privacy_requirements[platform_id] = {
                    "display_name": requirements["display_name"],
                    "compliance_requirements": requirements["compliance_requirements"]
                }
        
        logger.info(f"Privacy requirements retrieved for {len(privacy_requirements)} platform(s)")
        
        return {
            "status": "success",
            "privacy_requirements": privacy_requirements,
            "last_updated": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting privacy requirements: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving privacy requirements: {str(e)}")


@router.post("/compliance/validate-content")
async def validate_content_compliance(
    content_data: Dict[str, Any],
    platforms: List[str] = Query(..., description="Platforms to validate against"),
    compliance_service: EnhancedPlatformComplianceService = Depends(get_enhanced_compliance_service)
):
    """
    Validate content against platform-specific compliance requirements.
    
    Validates:
    - Caption length limits
    - Hashtag limits
    - Media file sizes and formats
    - Content policy violations
    - Required disclosures
    
    Returns compliance scores and recommendations for each platform.
    """
    try:
        logger.info(f"Validating content compliance for platforms: {platforms}")
        
        validation_results = {}
        
        for platform in platforms:
            # Get platform requirements
            requirements = compliance_service.get_platform_requirements(platform)
            if "error" in requirements:
                validation_results[platform] = {
                    "is_valid": False,
                    "errors": [requirements["error"]],
                    "compliance_score": 0.0
                }
                continue
            
            # Validate content against platform requirements
            errors = []
            warnings = []
            score_deductions = []
            
            # Check caption length
            caption = content_data.get("caption", "")
            max_caption = requirements["content_requirements"]["max_caption_length"]
            if len(caption) > max_caption:
                errors.append(f"Caption too long: {len(caption)}/{max_caption} characters")
                score_deductions.append(20)
            
            # Check hashtag count
            hashtags = content_data.get("hashtags", [])
            max_hashtags = requirements["content_requirements"]["max_hashtags"]
            if len(hashtags) > max_hashtags:
                errors.append(f"Too many hashtags: {len(hashtags)}/{max_hashtags}")
                score_deductions.append(15)
            
            # Check media requirements
            media_files = content_data.get("media_files", [])
            for media_file in media_files:
                media_type = media_file.get("type", "image")
                file_size_mb = media_file.get("size_mb", 0)
                
                if media_type in requirements["media_requirements"]:
                    max_size = requirements["media_requirements"][media_type]["max_file_size_mb"]
                    if file_size_mb > max_size:
                        errors.append(f"{media_type.title()} file too large: {file_size_mb}MB/{max_size}MB")
                        score_deductions.append(25)
            
            # Calculate compliance score
            total_deduction = sum(score_deductions)
            compliance_score = max(0.0, 100.0 - total_deduction)
            
            validation_results[platform] = {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "compliance_score": compliance_score,
                "platform_name": requirements["display_name"]
            }
        
        logger.info(f"Content validation completed for {len(platforms)} platforms")
        
        return {
            "status": "success",
            "validation_results": validation_results,
            "overall_valid": all(result["is_valid"] for result in validation_results.values()),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error validating content compliance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Content validation failed: {str(e)}")


@router.get("/compliance/health-check")
async def compliance_health_check(
    compliance_service: EnhancedPlatformComplianceService = Depends(get_enhanced_compliance_service)
):
    """
    Perform a quick health check of the compliance system.
    
    Returns:
    - System status
    - Platform availability
    - Configuration status
    - Last update times
    """
    try:
        summary = compliance_service.get_all_platforms_summary()
        
        health_status = {
            "system_status": "healthy",
            "total_platforms": summary["total_platforms"],
            "platforms_configured": len(summary["platforms"]),
            "compliance_overview": summary["compliance_overview"],
            "last_checked": datetime.now().isoformat(),
            "issues": []
        }
        
        # Check for potential issues
        if summary["total_platforms"] == 0:
            health_status["issues"].append("No platforms configured")
            health_status["system_status"] = "warning"
        
        if summary["compliance_overview"]["gdpr_compliant_platforms"] == 0:
            health_status["issues"].append("No GDPR compliant platforms")
            health_status["system_status"] = "warning"
        
        logger.info(f"Compliance health check completed. Status: {health_status['system_status']}")
        
        return {
            "status": "success",
            "health_status": health_status
        }
        
    except Exception as e:
        logger.error(f"Error during compliance health check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")