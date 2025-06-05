"""
Unified posting handler that manages all social media platforms.
Provides a single interface for posting to all supported platforms.
"""
import os
import json
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QThread

from ...api.meta.meta_posting_handler import MetaPostingHandler
from ...api.instagram.instagram_api_handler import InstagramAPIHandler
from ...api.tiktok.tiktok_api_handler import TikTokAPIHandler
from ...api.google_business.google_business_api_handler import GoogleBusinessAPIHandler
from ...api.bluesky.bluesky_api_handler import BlueSkyAPIHandler
from ...api.pinterest.pinterest_api_handler import PinterestAPIHandler
from ...api.threads.threads_api_handler import ThreadsAPIHandler
from ...api.youtube.youtube_api_handler import YouTubeAPIHandler
from .platform_optimizers import PlatformOptimizerFactory

class UnifiedPostingSignals(QObject):
    """Signals for unified posting operations."""
    upload_started = Signal(str)  # platform
    upload_progress = Signal(str, int)  # message, percentage
    upload_success = Signal(str, dict)  # platform, response_data
    upload_error = Signal(str, str)  # platform, error_message
    status_update = Signal(str)
    all_uploads_complete = Signal(bool, list)  # success, results

class UnifiedPostingHandler:
    """Handler for posting content to all supported social media platforms."""
    
    def __init__(self):
        """Initialize the unified posting handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.signals = UnifiedPostingSignals()
        
        # Initialize platform handlers
        self.meta_handler = MetaPostingHandler()
        self.instagram_handler = InstagramAPIHandler()
        self.tiktok_handler = TikTokAPIHandler()
        self.google_business_handler = GoogleBusinessAPIHandler()
        self.bluesky_handler = BlueSkyAPIHandler()
        self.pinterest_handler = PinterestAPIHandler()
        self.threads_handler = ThreadsAPIHandler()
        self.youtube_handler = YouTubeAPIHandler()
        
        # Initialize platform optimizer factory
        self.optimizer_factory = PlatformOptimizerFactory()
        
        # Connect signals
        self._connect_signals()
        
    def _connect_signals(self):
        """Connect signals from individual platform handlers."""
        # Meta signals
        self.meta_handler.signals.upload_started.connect(self.signals.upload_started)
        self.meta_handler.signals.upload_progress.connect(self.signals.upload_progress)
        self.meta_handler.signals.upload_success.connect(self.signals.upload_success)
        self.meta_handler.signals.upload_error.connect(self.signals.upload_error)
        self.meta_handler.signals.status_update.connect(self.signals.status_update)
        

        
        # Instagram signals
        self.instagram_handler.signals.upload_started.connect(self.signals.upload_started)
        self.instagram_handler.signals.upload_progress.connect(self.signals.upload_progress)
        self.instagram_handler.signals.upload_success.connect(self.signals.upload_success)
        self.instagram_handler.signals.upload_error.connect(self.signals.upload_error)
        self.instagram_handler.signals.status_update.connect(self.signals.status_update)
        
        # TikTok signals
        self.tiktok_handler.signals.upload_started.connect(self.signals.upload_started)
        self.tiktok_handler.signals.upload_progress.connect(self.signals.upload_progress)
        self.tiktok_handler.signals.upload_success.connect(self.signals.upload_success)
        self.tiktok_handler.signals.upload_error.connect(self.signals.upload_error)
        self.tiktok_handler.signals.status_update.connect(self.signals.status_update)
        
        # Google Business signals
        self.google_business_handler.signals.upload_started.connect(self.signals.upload_started)
        self.google_business_handler.signals.upload_progress.connect(self.signals.upload_progress)
        self.google_business_handler.signals.upload_success.connect(self.signals.upload_success)
        self.google_business_handler.signals.upload_error.connect(self.signals.upload_error)
        self.google_business_handler.signals.status_update.connect(self.signals.status_update)
        
        # BlueSky signals
        self.bluesky_handler.signals.upload_started.connect(self.signals.upload_started)
        self.bluesky_handler.signals.upload_progress.connect(self.signals.upload_progress)
        self.bluesky_handler.signals.upload_success.connect(self.signals.upload_success)
        self.bluesky_handler.signals.upload_error.connect(self.signals.upload_error)
        self.bluesky_handler.signals.status_update.connect(self.signals.status_update)
        
        # Pinterest signals
        self.pinterest_handler.signals.upload_started.connect(self.signals.upload_started)
        self.pinterest_handler.signals.upload_progress.connect(self.signals.upload_progress)
        self.pinterest_handler.signals.upload_success.connect(self.signals.upload_success)
        self.pinterest_handler.signals.upload_error.connect(self.signals.upload_error)
        self.pinterest_handler.signals.status_update.connect(self.signals.status_update)
        
        # Threads signals
        self.threads_handler.signals.upload_started.connect(self.signals.upload_started)
        self.threads_handler.signals.upload_progress.connect(self.signals.upload_progress)
        self.threads_handler.signals.upload_success.connect(self.signals.upload_success)
        self.threads_handler.signals.upload_error.connect(self.signals.upload_error)
        self.threads_handler.signals.status_update.connect(self.signals.status_update)
        
        # YouTube signals
        self.youtube_handler.signals.upload_started.connect(self.signals.upload_started)
        self.youtube_handler.signals.upload_progress.connect(self.signals.upload_progress)
        self.youtube_handler.signals.upload_success.connect(self.signals.upload_success)
        self.youtube_handler.signals.upload_error.connect(self.signals.upload_error)
        self.youtube_handler.signals.status_update.connect(self.signals.status_update)
    
    def post_to_platforms_optimized(self, platforms: List[str], media_paths: List[str] = None, 
                                   media_path: str = None, caption: str = "", is_video: bool = False, 
                                   optimize_content: bool = True, **kwargs) -> Dict[str, Tuple[bool, str]]:
        """
        Post content to multiple platforms with platform-specific optimizations.
        Supports single media posts and gallery/carousel posts.
        
        Args:
            platforms: List of platform names to post to
            media_paths: List of media file paths (for galleries/carousels)
            media_path: Single media file path (for backwards compatibility)
            caption: Caption for the post
            is_video: Whether the media is a video
            optimize_content: Whether to apply platform-specific optimizations
            **kwargs: Additional parameters (title for YouTube, etc.)
            
        Returns:
            Dictionary mapping platform names to (success, message) tuples
        """
        results = {}
        
        # Handle media paths (support both single and multiple files)
        effective_media_paths = media_paths if media_paths else ([media_path] if media_path else [])
        effective_media_path = effective_media_paths[0] if effective_media_paths else None
        is_gallery = len(effective_media_paths) > 1
        
        for platform in platforms:
            platform_lower = platform.lower()
            
            try:
                # Apply platform-specific optimizations if enabled
                optimized_media_paths = effective_media_paths
                optimized_media_path = effective_media_path
                optimized_caption = caption
                optimized_kwargs = kwargs.copy()
                
                if optimize_content and effective_media_path:
                    optimizer = self.optimizer_factory.get_optimizer(platform_lower)
                    
                    # Special handling for YouTube Shorts
                    is_short = platform_lower == 'youtube_shorts'
                    if platform_lower in ['youtube', 'youtube_shorts']:
                        optimization_result = optimizer.optimize_content(
                            effective_media_path, caption, "auto", is_short=is_short, **kwargs
                        )
                    else:
                        optimization_result = optimizer.optimize_content(
                            effective_media_path, caption, "auto"
                        )
                    
                    if optimization_result["success"]:
                        optimized_media_path = optimization_result["optimized_media_path"]
                        optimized_caption = optimization_result["optimized_caption"]
                        
                        # For YouTube, also get the optimized title
                        if platform_lower in ['youtube', 'youtube_shorts'] and "optimized_title" in optimization_result:
                            optimized_kwargs["title"] = optimization_result["optimized_title"]
                        
                        self.logger.info(f"Content optimized for {platform}: {optimization_result['metadata']}")
                    else:
                        self.logger.warning(f"Optimization failed for {platform}: {optimization_result['message']}")
                
                # Post to the specific platform (support galleries where available)
                if is_gallery and platform_lower in ['tiktok', 'pinterest']:
                    # Platforms that support galleries/carousels
                    success, message = self._post_gallery_to_platform(
                        platform_lower, optimized_media_paths, optimized_caption, is_video, **optimized_kwargs
                    )
                else:
                    # Single media post
                    success, message = self._post_to_single_platform(
                        platform_lower, optimized_media_path, optimized_caption, is_video, **optimized_kwargs
                    )
                
                results[platform] = (success, message)
                
                # Small delay between posts to avoid rate limiting
                if len(platforms) > 1:
                    time.sleep(1)
                    
            except Exception as e:
                error_msg = f"Error posting to {platform}: {str(e)}"
                self.logger.exception(error_msg)
                results[platform] = (False, error_msg)
        
        # Emit completion signal
        all_success = all(result[0] for result in results.values())
        self.signals.all_uploads_complete.emit(all_success, list(results.items()))
        
        return results
    
    def _post_to_single_platform(self, platform_lower: str, media_path: str, caption: str, 
                                is_video: bool, **kwargs) -> Tuple[bool, str]:
        """Post to a single platform with the given parameters."""
        if platform_lower in ['instagram', 'facebook']:
            if platform_lower == 'instagram':
                return self.meta_handler.post_to_instagram(media_path, caption, is_video)
            else:  # facebook
                return self.meta_handler.post_to_facebook(media_path, caption, is_video)
        elif platform_lower == 'instagram_api':
            return self.instagram_handler.post_media(media_path, caption, is_video)
        elif platform_lower == 'tiktok':
            return self.tiktok_handler.post_media(media_path=media_path, caption=caption, is_video=is_video)
        elif platform_lower in ['google_business', 'google_my_business']:
            return self.google_business_handler.post_media(media_path, caption, is_video)
        elif platform_lower == 'bluesky':
            return self.bluesky_handler.post_media(media_path, caption, is_video)
        elif platform_lower == 'pinterest':
            return self.pinterest_handler.post_media(media_path=media_path, caption=caption, is_video=is_video)
        elif platform_lower == 'threads':
            return self.threads_handler.post_media(media_path, caption, is_video)
        elif platform_lower == 'youtube':
            return self.youtube_handler.post_media(media_path, caption, is_video, is_short=False, **kwargs)
        elif platform_lower == 'youtube_shorts':
            return self.youtube_handler.post_media(media_path, caption, is_video, is_short=True, **kwargs)
        else:
            return False, f"Unsupported platform: {platform_lower}"
    
    def _post_gallery_to_platform(self, platform_lower: str, media_paths: List[str], caption: str, 
                                  is_video: bool, **kwargs) -> Tuple[bool, str]:
        """Post a gallery/carousel to platforms that support it."""
        if platform_lower == 'tiktok':
            # TikTok photo carousels (up to 35 images)
            return self.tiktok_handler.post_media(media_paths=media_paths, caption=caption, is_video=False, **kwargs)
        elif platform_lower == 'pinterest':
            # Pinterest gallery/carousel pins
            return self.pinterest_handler.post_media(media_paths=media_paths, caption=caption, is_video=is_video, **kwargs)
        else:
            # Fallback to single image for platforms that don't support galleries
            return self._post_to_single_platform(platform_lower, media_paths[0], caption, is_video, **kwargs)
    
    def post_to_platforms(self, platforms: List[str], media_path: str = None, 
                         caption: str = "", is_video: bool = False) -> Dict[str, Tuple[bool, str]]:
        """
        Post content to multiple platforms.
        
        Args:
            platforms: List of platform names to post to
            media_path: Path to the media file (optional for text-only posts)
            caption: Caption for the post
            is_video: Whether the media is a video
            
        Returns:
            Dictionary mapping platform names to (success, message) tuples
        """
        results = {}
        
        for platform in platforms:
            platform_lower = platform.lower()
            
            try:
                success, message = self._post_to_single_platform(
                    platform_lower, media_path, caption, is_video
                )
                
                results[platform] = (success, message)
                
                # Small delay between posts to avoid rate limiting
                if len(platforms) > 1:
                    time.sleep(1)
                    
            except Exception as e:
                error_msg = f"Error posting to {platform}: {str(e)}"
                self.logger.exception(error_msg)
                results[platform] = (False, error_msg)
        
        # Emit completion signal
        all_success = all(result[0] for result in results.values())
        self.signals.all_uploads_complete.emit(all_success, list(results.items()))
        
        return results
    
    def get_available_platforms(self) -> Dict[str, bool]:
        """Get availability status for all platforms."""
        meta_status = self.meta_handler.get_posting_status()
        instagram_status = self.instagram_handler.get_posting_status()
        tiktok_status = self.tiktok_handler.get_posting_status()
        google_business_status = self.google_business_handler.get_posting_status()
        bluesky_status = self.bluesky_handler.get_posting_status()
        pinterest_status = self.pinterest_handler.get_posting_status()
        threads_status = self.threads_handler.get_posting_status()
        youtube_status = self.youtube_handler.get_posting_status()
        
        return {
            'instagram': meta_status.get('instagram_available', False),
            'facebook': meta_status.get('facebook_available', False),
            'instagram_api': instagram_status.get('instagram_available', False),
            'tiktok': tiktok_status.get('tiktok_available', False),
            'google_business': google_business_status.get('google_business_available', False),
            'bluesky': bluesky_status.get('bluesky_available', False),
            'pinterest': pinterest_status.get('pinterest_available', False),
            'threads': threads_status.get('threads_available', False),
            'youtube': youtube_status.get('authenticated', False),
            'youtube_shorts': youtube_status.get('authenticated', False)
        }
    
    def get_platform_errors(self) -> Dict[str, str]:
        """Get error messages for unavailable platforms."""
        meta_status = self.meta_handler.get_posting_status()
        instagram_status = self.instagram_handler.get_posting_status()
        tiktok_status = self.tiktok_handler.get_posting_status()
        google_business_status = self.google_business_handler.get_posting_status()
        bluesky_status = self.bluesky_handler.get_posting_status()
        pinterest_status = self.pinterest_handler.get_posting_status()
        threads_status = self.threads_handler.get_posting_status()
        
        errors = {}
        
        if not meta_status.get('credentials_loaded', False):
            errors['instagram'] = meta_status.get('error_message', 'Meta credentials not configured')
            errors['facebook'] = meta_status.get('error_message', 'Meta credentials not configured')
        
        if not instagram_status.get('credentials_loaded', False):
            errors['instagram_api'] = instagram_status.get('error_message', 'Instagram API credentials not configured')
        
        if not tiktok_status.get('credentials_loaded', False):
            errors['tiktok'] = tiktok_status.get('error_message', 'TikTok credentials not configured')
        
        if not google_business_status.get('credentials_loaded', False):
            errors['google_business'] = google_business_status.get('error_message', 'Google My Business credentials not configured')
        
        if not bluesky_status.get('credentials_loaded', False):
            errors['bluesky'] = bluesky_status.get('error_message', 'BlueSky credentials not configured')
        
        if not pinterest_status.get('credentials_loaded', False):
            errors['pinterest'] = pinterest_status.get('error_message', 'Pinterest credentials not configured')
        
        if not threads_status.get('credentials_loaded', False):
            errors['threads'] = threads_status.get('error_message', 'Threads credentials not configured')
        
        return errors
    
    def validate_media_for_platforms(self, media_path: str, platforms: List[str]) -> Dict[str, Tuple[bool, str]]:
        """Validate media file for specific platforms."""
        results = {}
        
        for platform in platforms:
            platform_lower = platform.lower()
            
            if platform_lower in ['instagram', 'facebook']:
                success, message = self.meta_handler.validate_media_file(media_path)

            elif platform_lower == 'instagram_api':
                success, message = self.instagram_handler.validate_media_file(media_path)
            elif platform_lower == 'tiktok':
                success, message = self.tiktok_handler.validate_media_file(media_path)
            elif platform_lower in ['google_business', 'google_my_business']:
                success, message = self.google_business_handler.validate_media_file(media_path)
            elif platform_lower == 'bluesky':
                success, message = self.bluesky_handler.validate_media_file(media_path)
            elif platform_lower == 'pinterest':
                success, message = self.pinterest_handler.validate_media_file(media_path)
            elif platform_lower == 'threads':
                success, message = self.threads_handler.validate_media_file(media_path)
            else:
                success, message = False, f"Unsupported platform: {platform}"
            
            results[platform] = (success, message)
        
        return results
    
    def get_platform_limits(self) -> Dict[str, Dict[str, Any]]:
        """Get posting limits for each platform."""
        return {
            'instagram': {
                'max_caption_length': 2200,
                'max_image_size': 8 * 1024 * 1024,  # 8MB
                'max_video_size': 100 * 1024 * 1024,  # 100MB
                'max_video_duration': 60,  # seconds
                'requires_media': True
            },
            'facebook': {
                'max_caption_length': 63206,
                'max_image_size': 8 * 1024 * 1024,  # 8MB
                'max_video_size': 100 * 1024 * 1024,  # 100MB
                'max_video_duration': 240,  # seconds
                'requires_media': False
            },

            'instagram_api': {
                'max_caption_length': 2200,
                'max_image_size': 8 * 1024 * 1024,  # 8MB
                'max_video_size': 100 * 1024 * 1024,  # 100MB
                'max_video_duration': 60,  # seconds
                'requires_media': True
            },
            'tiktok': {
                'max_caption_length': 2200,
                'max_image_size': 20 * 1024 * 1024,  # 20MB per image
                'max_video_size': 4 * 1024 * 1024 * 1024,  # 4GB
                'max_video_duration': 600,  # 10 minutes
                'max_carousel_images': 35,  # Photo carousels supported
                'requires_media': True,
                'supports_photo_carousel': True,
                'supports_video': True
            },
            'google_business': {
                'max_caption_length': 1500,
                'max_image_size': 10 * 1024 * 1024,  # 10MB
                'max_video_size': 100 * 1024 * 1024,  # 100MB
                'max_video_duration': 30,  # seconds
                'requires_media': False
            },
            'bluesky': {
                'max_caption_length': 300,
                'max_image_size': 1 * 1024 * 1024,  # 1MB
                'max_video_size': 0,  # No video support
                'max_video_duration': 0,
                'requires_media': False,
                'image_only': True
            },
            'pinterest': {
                'max_caption_length': 500,
                'max_image_size': 32 * 1024 * 1024,  # 32MB
                'max_video_size': 2 * 1024 * 1024 * 1024,  # 2GB
                'max_video_duration': 900,  # 15 minutes
                'max_carousel_images': 5,  # Gallery/carousel pins supported
                'requires_media': True,
                'supports_gallery': True,
                'supports_carousel': True,
                'supports_boards': True
            },
            'threads': {
                'max_caption_length': 500,
                'max_image_size': 8 * 1024 * 1024,  # 8MB
                'max_video_size': 100 * 1024 * 1024,  # 100MB
                'max_video_duration': 60,  # seconds
                'requires_media': False
            }
        }

class UnifiedPostingWorker(QThread):
    """Worker thread for unified posting operations."""
    
    finished = Signal(bool, dict)  # success, results
    progress = Signal(str, int)  # message, percentage
    platform_complete = Signal(str, bool, str)  # platform, success, message
    
    def __init__(self, handler: UnifiedPostingHandler, platforms: List[str], 
                 media_path: str, caption: str, is_video: bool = False):
        super().__init__()
        self.handler = handler
        self.platforms = platforms
        self.media_path = media_path
        self.caption = caption
        self.is_video = is_video
        
    def run(self):
        """Run the unified posting operation."""
        try:
            total_platforms = len(self.platforms)
            results = {}
            
            for i, platform in enumerate(self.platforms):
                self.progress.emit(f"Posting to {platform}...", 
                                 int((i / total_platforms) * 100))
                
                platform_lower = platform.lower()
                
                if platform_lower in ['instagram', 'facebook']:
                    if platform_lower == 'instagram':
                        success, message = self.handler.meta_handler.post_to_instagram(
                            self.media_path, self.caption, self.is_video
                        )
                    else:  # facebook
                        success, message = self.handler.meta_handler.post_to_facebook(
                            self.media_path, self.caption, self.is_video
                        )

                elif platform_lower == 'instagram_api':
                    success, message = self.handler.instagram_handler.post_media(
                        self.media_path, self.caption, self.is_video
                    )
                elif platform_lower == 'tiktok':
                    success, message = self.handler.tiktok_handler.post_media(
                        self.media_path, self.caption, self.is_video
                    )
                elif platform_lower in ['google_business', 'google_my_business']:
                    success, message = self.handler.google_business_handler.post_media(
                        self.media_path, self.caption, self.is_video
                    )
                elif platform_lower == 'bluesky':
                    success, message = self.handler.bluesky_handler.post_media(
                        self.media_path, self.caption, self.is_video
                    )
                elif platform_lower == 'pinterest':
                    success, message = self.handler.pinterest_handler.post_media(
                        self.media_path, self.caption, self.is_video
                    )
                elif platform_lower == 'threads':
                    success, message = self.handler.threads_handler.post_media(
                        self.media_path, self.caption, self.is_video
                    )
                else:
                    success, message = False, f"Unsupported platform: {platform}"
                
                results[platform] = (success, message)
                self.platform_complete.emit(platform, success, message)
                
                # Small delay between posts
                if i < total_platforms - 1:
                    time.sleep(1)
            
            self.progress.emit("All posts complete", 100)
            all_success = all(result[0] for result in results.values())
            self.finished.emit(all_success, results)
            
        except Exception as e:
            error_msg = f"Error in unified posting worker: {str(e)}"
            self.finished.emit(False, {"error": (False, error_msg)}) 