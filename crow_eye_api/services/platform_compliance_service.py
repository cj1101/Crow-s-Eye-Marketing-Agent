"""
Platform Compliance Service

Validates content against platform-specific requirements for all 7 supported platforms.
"""

import re
from typing import Dict, List, Any, Optional


class PlatformComplianceService:
    """Service for validating content against platform requirements."""
    
    def __init__(self):
        self.platforms = {
            "instagram": {
                "display_name": "Instagram",
                "content": {"max_caption_length": 2200, "max_hashtags": 30, "supports_links": False},
                "media": {"image": {"max_file_size_mb": 8}, "video": {"max_file_size_mb": 100}},
                "posting": {"business_account_required": True}
            },
            "facebook": {
                "display_name": "Facebook", 
                "content": {"max_caption_length": 63206, "max_hashtags": 30, "supports_links": True},
                "media": {"image": {"max_file_size_mb": 8}, "video": {"max_file_size_mb": 4000}},
                "posting": {"business_account_required": False}
            },
            "tiktok": {
                "display_name": "TikTok",
                "content": {"max_caption_length": 2200, "max_hashtags": 100, "supports_links": False},
                "media": {"video": {"max_file_size_mb": 4000}},
                "posting": {"business_account_required": True, "verification_required": True}
            },
            "pinterest": {
                "display_name": "Pinterest",
                "content": {"max_caption_length": 500, "max_hashtags": 20, "supports_links": True},
                "media": {"image": {"max_file_size_mb": 32}, "video": {"max_file_size_mb": 2000}},
                "posting": {"business_account_required": True}
            },
            "bluesky": {
                "display_name": "BlueSky",
                "content": {"max_caption_length": 300, "max_hashtags": 10, "supports_links": True},
                "media": {"image": {"max_file_size_mb": 1}},
                "posting": {"business_account_required": False, "supports_scheduling": False}
            },
            "threads": {
                "display_name": "Threads",
                "content": {"max_caption_length": 500, "max_hashtags": 30, "supports_links": True},
                "media": {"image": {"max_file_size_mb": 8}, "video": {"max_file_size_mb": 100}},
                "posting": {"business_account_required": False}
            },
            "google_business": {
                "display_name": "Google My Business",
                "content": {"max_caption_length": 1500, "max_hashtags": 10, "supports_links": True},
                "media": {"image": {"max_file_size_mb": 10}, "video": {"max_file_size_mb": 100}},
                "posting": {"business_account_required": True, "verification_required": True}
            }
        }
    
    def validate_content(self, platform: str, content_type: str, **kwargs) -> Dict[str, Any]:
        """Validate content against platform-specific requirements."""
        if platform not in self.platforms:
            return {
                "platform": platform,
                "is_valid": False,
                "errors": [f"Unsupported platform: {platform}"],
                "warnings": [],
                "suggestions": [],
                "compliance_score": 0.0,
                "optimization_tips": []
            }
        
        platform_config = self.platforms[platform]
        errors = []
        warnings = []
        suggestions = []
        score_deductions = []
        
        # Validate caption
        caption = kwargs.get('caption', '')
        if caption:
            max_length = platform_config['content']['max_caption_length']
            if len(caption) > max_length:
                errors.append(f"Caption exceeds maximum length of {max_length} characters")
                score_deductions.append(20)
            elif len(caption) > max_length * 0.9:
                warnings.append("Caption is close to maximum length limit")
                score_deductions.append(5)
        
        # Validate media size
        media_size_mb = kwargs.get('media_size_mb')
        if media_size_mb and content_type in platform_config['media']:
            max_size = platform_config['media'][content_type]['max_file_size_mb']
            if media_size_mb > max_size:
                errors.append(f"File size {media_size_mb}MB exceeds maximum {max_size}MB")
                score_deductions.append(20)
        
        # Validate hashtags
        hashtags = kwargs.get('hashtags', [])
        if hashtags:
            max_hashtags = platform_config['content']['max_hashtags']
            if len(hashtags) > max_hashtags:
                errors.append(f"Too many hashtags: {len(hashtags)}. Maximum: {max_hashtags}")
                score_deductions.append(10)
        
        # Calculate compliance score
        total_deduction = sum(score_deductions)
        compliance_score = max(0.0, 100.0 - total_deduction)
        
        # Generate optimization tips
        optimization_tips = self._get_optimization_tips(platform, content_type)
        
        return {
            "platform": platform,
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "compliance_score": compliance_score,
            "optimization_tips": optimization_tips
        }
    
    def validate_bulk_content(self, platforms: List[str], content_type: str, **kwargs) -> Dict[str, Any]:
        """Validate content across multiple platforms."""
        platform_results = {}
        total_score = 0.0
        
        for platform in platforms:
            result = self.validate_content(platform, content_type, **kwargs)
            platform_results[platform] = result
            total_score += result['compliance_score']
        
        overall_score = total_score / len(platforms) if platforms else 0.0
        
        # Generate cross-platform suggestions
        cross_platform_suggestions = [
            "Keep captions concise for maximum platform compatibility",
            "Use standard image formats (JPG, PNG) for best support"
        ]
        
        # Recommend best platforms
        recommended_platforms = sorted(
            platforms, 
            key=lambda p: platform_results[p]['compliance_score'], 
            reverse=True
        )[:3]
        
        return {
            "overall_score": overall_score,
            "platform_results": platform_results,
            "cross_platform_suggestions": cross_platform_suggestions,
            "recommended_platforms": recommended_platforms
        }
    
    def _get_optimization_tips(self, platform: str, content_type: str) -> List[str]:
        """Generate platform-specific optimization tips."""
        tips_map = {
            "instagram": [
                "Use high-quality square or vertical images",
                "Include relevant hashtags but avoid banned ones",
                "Post during peak hours for better engagement"
            ],
            "tiktok": [
                "Use vertical 9:16 format for optimal viewing",
                "Hook viewers in the first 3 seconds",
                "Include trending sounds or music"
            ],
            "pinterest": [
                "Use vertical pins for better visibility",
                "Include text overlay on images",
                "Write detailed, keyword-rich descriptions"
            ],
            "facebook": [
                "Videos perform better than images",
                "Add captions for silent autoplay",
                "Ask questions to encourage comments"
            ],
            "threads": [
                "Keep posts conversational and authentic",
                "Engage with replies quickly",
                "Share behind-the-scenes content"
            ],
            "bluesky": [
                "Keep posts concise due to character limit",
                "Engage authentically with the community",
                "Use alt text for images"
            ],
            "google_business": [
                "Include location-relevant keywords",
                "Post regularly to maintain visibility",
                "Use high-quality local images"
            ]
        }
        
        return tips_map.get(platform, ["Optimize content for platform-specific audience"])
    
    def get_platform_info(self, platform: str) -> Optional[Dict]:
        """Get complete platform information."""
        return self.platforms.get(platform)
    
    def get_all_platforms(self) -> List[str]:
        """Get list of all supported platforms."""
        return list(self.platforms.keys())
    
    def get_supported_formats(self, platform: str, content_type: str) -> List[str]:
        """Get supported formats for platform and content type."""
        if platform in self.platforms and content_type in self.platforms[platform]['media']:
            return ["jpg", "jpeg", "png", "mp4", "mov"]  # Common formats
        return [] 