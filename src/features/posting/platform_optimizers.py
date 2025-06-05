# -*- coding: utf-8 -*-
"""
Platform-specific optimizers for enhancing content for different social media platforms.
Each optimizer applies platform-specific formatting, sizing, and AI enhancements.
"""
import os
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

class BasePlatformOptimizer:
    """Base class for platform optimizers."""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{platform_name}")
    
    def optimize_content(self, media_path: str, caption: str, content_type: str = "auto", **kwargs) -> Dict[str, Any]:
        """
        Optimize content for the specific platform.
        
        Args:
            media_path: Path to the media file
            caption: Original caption
            content_type: Type of content (image, video, auto)
            
        Returns:
            Dict with optimized content paths and metadata
        """
        # Basic implementation - just return the content as-is
        return {
            "optimized_media_path": media_path,
            "optimized_caption": caption,
            "success": True,
            "message": f"Basic optimization for {self.platform_name}",
            "metadata": {"platform": self.platform_name}
        }

class BlueSkyOptimizer(BasePlatformOptimizer):
    """Optimizer for BlueSky (AT Protocol)."""
    
    def __init__(self):
        super().__init__("bluesky")
        self.max_chars = 300
    
    def optimize_content(self, media_path: str, caption: str, content_type: str = "auto", **kwargs) -> Dict[str, Any]:
        """Optimize content for BlueSky."""
        result = {
            "optimized_media_path": media_path,
            "optimized_caption": caption,
            "success": True,
            "message": "",
            "metadata": {}
        }
        
        try:
            # BlueSky doesn't support video
            if content_type == "video":
                result["success"] = False
                result["message"] = "BlueSky doesn't support video content yet"
                return result
            
            # Optimize caption for 300 character limit
            result["optimized_caption"] = self._optimize_caption_for_bluesky(caption)
            
            # Add BlueSky-specific metadata
            result["metadata"] = {
                "platform": "bluesky",
                "character_count": len(result["optimized_caption"]),
                "supports_threads": True,
                "max_images": 4
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error optimizing content for BlueSky: {e}")
            result["success"] = False
            result["message"] = f"Optimization failed: {str(e)}"
            return result
    
    def _optimize_caption_for_bluesky(self, caption: str) -> str:
        """Optimize caption for BlueSky's 300 character limit."""
        if len(caption) <= self.max_chars:
            return caption
        
        # Truncate intelligently at word boundaries
        truncated = caption[:self.max_chars-3]
        last_space = truncated.rfind(' ')
        if last_space > self.max_chars * 0.8:  # Only truncate at word if close to limit
            truncated = truncated[:last_space]
        
        return truncated + "..."

class PinterestOptimizer(BasePlatformOptimizer):
    """Optimizer for Pinterest."""
    
    def __init__(self):
        super().__init__("pinterest")
        self.max_chars = 500
    
    def optimize_content(self, media_path: str, caption: str, content_type: str = "auto", **kwargs) -> Dict[str, Any]:
        """Optimize content for Pinterest."""
        result = {
            "optimized_media_path": media_path,
            "optimized_caption": caption,
            "success": True,
            "message": "",
            "metadata": {}
        }
        
        try:
            # Optimize caption for Pinterest SEO
            result["optimized_caption"] = self._optimize_caption_for_pinterest(caption)
            
            # Add Pinterest-specific metadata
            result["metadata"] = {
                "platform": "pinterest",
                "character_count": len(result["optimized_caption"]),
                "seo_optimized": True,
                "ideal_aspect_ratio": "2:3"
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error optimizing content for Pinterest: {e}")
            result["success"] = False
            result["message"] = f"Optimization failed: {str(e)}"
            return result
    
    def _optimize_caption_for_pinterest(self, caption: str) -> str:
        """Optimize caption for Pinterest SEO."""
        optimized = caption
        
        if len(optimized) > self.max_chars:
            optimized = optimized[:self.max_chars-3] + "..."
        
        # Add Pinterest-specific call-to-action if not present
        if not any(cta in optimized.lower() for cta in ["save", "pin", "click", "shop", "visit"]):
            if len(optimized) < self.max_chars - 20:
                optimized += " Save for later!"
        
        return optimized

class YouTubeOptimizer(BasePlatformOptimizer):
    """Optimizer for YouTube and YouTube Shorts."""
    
    def __init__(self):
        super().__init__("youtube")
        self.max_title_chars = 100
        self.max_description_chars = 5000
    
    def optimize_content(self, media_path: str, caption: str, content_type: str = "auto", 
                        is_short: bool = False, **kwargs) -> Dict[str, Any]:
        """Optimize content for YouTube."""
        result = {
            "optimized_media_path": media_path,
            "optimized_caption": caption,
            "optimized_title": kwargs.get("title", ""),
            "success": True,
            "message": "",
            "metadata": {}
        }
        
        try:
            # YouTube only supports video
            if content_type != "video" and media_path:
                result["success"] = False
                result["message"] = "YouTube only supports video content"
                return result
            
            # Generate optimized title and description
            if not result["optimized_title"]:
                result["optimized_title"] = self._generate_title_from_caption(caption, is_short)
            
            result["optimized_caption"] = self._optimize_description_for_youtube(caption, is_short)
            
            # Add YouTube-specific metadata
            result["metadata"] = {
                "platform": "youtube_shorts" if is_short else "youtube",
                "is_short": is_short,
                "title_length": len(result["optimized_title"]),
                "description_length": len(result["optimized_caption"]),
                "seo_optimized": True
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error optimizing content for YouTube: {e}")
            result["success"] = False
            result["message"] = f"Optimization failed: {str(e)}"
            return result
    
    def _generate_title_from_caption(self, caption: str, is_short: bool = False) -> str:
        """Generate an optimized title from caption."""
        # Extract the first sentence or meaningful phrase
        sentences = caption.split('.')
        title = sentences[0].strip() if sentences else caption[:50]
        
        if is_short and "#Shorts" not in title:
            title += " #Shorts"
        
        return title[:self.max_title_chars]
    
    def _optimize_description_for_youtube(self, description: str, is_short: bool = False) -> str:
        """Optimize description for YouTube SEO."""
        optimized = description
        
        if is_short:
            if "#Shorts" not in optimized:
                optimized += "\n\n#Shorts"
        
        # Add YouTube-friendly call-to-action if not present
        if len(optimized) < self.max_description_chars - 100:
            if not any(cta in optimized.lower() for cta in ["subscribe", "like", "comment", "share"]):
                optimized += "\n\nLike this video if you enjoyed it! Subscribe for more content!"
        
        return optimized[:self.max_description_chars]

# Factory class for getting the right optimizer
class PlatformOptimizerFactory:
    """Factory for creating platform-specific optimizers."""
    
    _optimizers = {
        'bluesky': BlueSkyOptimizer,
        'pinterest': PinterestOptimizer,
        'youtube': YouTubeOptimizer,
        'youtube_shorts': YouTubeOptimizer,
        'tiktok': BasePlatformOptimizer,
        'google_business': BasePlatformOptimizer,
        'google_my_business': BasePlatformOptimizer,
    }
    
    @classmethod
    def get_optimizer(cls, platform: str):
        """Get the appropriate optimizer for a platform."""
        platform_lower = platform.lower()
        optimizer_class = cls._optimizers.get(platform_lower, BasePlatformOptimizer)
        
        if optimizer_class == BasePlatformOptimizer:
            return optimizer_class(platform_lower)
        else:
            return optimizer_class() 