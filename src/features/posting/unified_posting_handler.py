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
from ...api.linkedin.linkedin_posting_handler import LinkedInPostingHandler
from ...api.twitter.x_posting_handler import XPostingHandler
from ...api.instagram.instagram_api_handler import InstagramAPIHandler
from ...api.tiktok.tiktok_api_handler import TikTokAPIHandler
from ...api.google_business.google_business_api_handler import GoogleBusinessAPIHandler
from ...api.bluesky.bluesky_api_handler import BlueSkyAPIHandler
from ...api.pinterest.pinterest_api_handler import PinterestAPIHandler
from ...api.threads.threads_api_handler import ThreadsAPIHandler

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
        self.linkedin_handler = LinkedInPostingHandler()
        self.x_handler = XPostingHandler()
        self.instagram_handler = InstagramAPIHandler()
        self.tiktok_handler = TikTokAPIHandler()
        self.google_business_handler = GoogleBusinessAPIHandler()
        self.bluesky_handler = BlueSkyAPIHandler()
        self.pinterest_handler = PinterestAPIHandler()
        self.threads_handler = ThreadsAPIHandler()
        
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
        
        # LinkedIn signals
        self.linkedin_handler.signals.upload_started.connect(self.signals.upload_started)
        self.linkedin_handler.signals.upload_progress.connect(self.signals.upload_progress)
        self.linkedin_handler.signals.upload_success.connect(self.signals.upload_success)
        self.linkedin_handler.signals.upload_error.connect(self.signals.upload_error)
        self.linkedin_handler.signals.status_update.connect(self.signals.status_update)
        
        # X signals
        self.x_handler.signals.upload_started.connect(self.signals.upload_started)
        self.x_handler.signals.upload_progress.connect(self.signals.upload_progress)
        self.x_handler.signals.upload_success.connect(self.signals.upload_success)
        self.x_handler.signals.upload_error.connect(self.signals.upload_error)
        self.x_handler.signals.status_update.connect(self.signals.status_update)
        
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
                if platform_lower in ['instagram', 'facebook']:
                    if platform_lower == 'instagram':
                        success, message = self.meta_handler.post_to_instagram(
                            media_path, caption, is_video
                        )
                    else:  # facebook
                        success, message = self.meta_handler.post_to_facebook(
                            media_path, caption, is_video
                        )
                elif platform_lower == 'linkedin':
                    success, message = self.linkedin_handler.post_to_linkedin(
                        media_path, caption, is_video
                    )
                elif platform_lower in ['x', 'twitter']:
                    success, message = self.x_handler.post_to_x(
                        media_path, caption, is_video
                    )
                elif platform_lower == 'instagram_api':
                    success, message = self.instagram_handler.post_media(
                        media_path, caption, is_video
                    )
                elif platform_lower == 'tiktok':
                    success, message = self.tiktok_handler.post_media(
                        media_path, caption, is_video
                    )
                elif platform_lower in ['google_business', 'google_my_business']:
                    success, message = self.google_business_handler.post_media(
                        media_path, caption, is_video
                    )
                elif platform_lower == 'bluesky':
                    success, message = self.bluesky_handler.post_media(
                        media_path, caption, is_video
                    )
                elif platform_lower == 'pinterest':
                    success, message = self.pinterest_handler.post_media(
                        media_path, caption, is_video
                    )
                elif platform_lower == 'threads':
                    success, message = self.threads_handler.post_media(
                        media_path, caption, is_video
                    )
                else:
                    success, message = False, f"Unsupported platform: {platform}"
                
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
        linkedin_status = self.linkedin_handler.get_posting_status()
        x_status = self.x_handler.get_posting_status()
        instagram_status = self.instagram_handler.get_posting_status()
        tiktok_status = self.tiktok_handler.get_posting_status()
        google_business_status = self.google_business_handler.get_posting_status()
        bluesky_status = self.bluesky_handler.get_posting_status()
        pinterest_status = self.pinterest_handler.get_posting_status()
        threads_status = self.threads_handler.get_posting_status()
        
        return {
            'instagram': meta_status.get('instagram_available', False),
            'facebook': meta_status.get('facebook_available', False),
            'linkedin': linkedin_status.get('linkedin_available', False),
            'x': x_status.get('x_available', False),
            'instagram_api': instagram_status.get('instagram_available', False),
            'tiktok': tiktok_status.get('tiktok_available', False),
            'google_business': google_business_status.get('google_business_available', False),
            'bluesky': bluesky_status.get('bluesky_available', False),
            'pinterest': pinterest_status.get('pinterest_available', False),
            'threads': threads_status.get('threads_available', False)
        }
    
    def get_platform_errors(self) -> Dict[str, str]:
        """Get error messages for unavailable platforms."""
        meta_status = self.meta_handler.get_posting_status()
        linkedin_status = self.linkedin_handler.get_posting_status()
        x_status = self.x_handler.get_posting_status()
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
        
        if not linkedin_status.get('credentials_loaded', False):
            errors['linkedin'] = linkedin_status.get('error_message', 'LinkedIn credentials not configured')
        
        if not x_status.get('credentials_loaded', False):
            errors['x'] = x_status.get('error_message', 'X credentials not configured')
        
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
            elif platform_lower == 'linkedin':
                success, message = self.linkedin_handler.validate_media_file(media_path)
            elif platform_lower in ['x', 'twitter']:
                success, message = self.x_handler.validate_media_file(media_path)
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
            'linkedin': {
                'max_caption_length': 3000,
                'max_image_size': 20 * 1024 * 1024,  # 20MB
                'max_video_size': 5 * 1024 * 1024 * 1024,  # 5GB
                'max_video_duration': 600,  # seconds
                'requires_media': False
            },
            'x': {
                'max_caption_length': 280,
                'max_image_size': 5 * 1024 * 1024,  # 5MB
                'max_video_size': 512 * 1024 * 1024,  # 512MB
                'max_video_duration': 140,  # seconds
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
                'max_image_size': 0,  # No images supported
                'max_video_size': 4 * 1024 * 1024 * 1024,  # 4GB
                'max_video_duration': 600,  # 10 minutes
                'requires_media': True,
                'video_only': True
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
                'requires_media': True
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
                elif platform_lower == 'linkedin':
                    success, message = self.handler.linkedin_handler.post_to_linkedin(
                        self.media_path, self.caption, self.is_video
                    )
                elif platform_lower in ['x', 'twitter']:
                    success, message = self.handler.x_handler.post_to_x(
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