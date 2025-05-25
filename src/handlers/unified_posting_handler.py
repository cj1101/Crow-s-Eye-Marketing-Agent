"""
Unified posting handler that manages all social media platforms.
Provides a single interface for posting to Instagram, Facebook, LinkedIn, and X.
"""
import os
import json
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QThread

from .meta_posting_handler import MetaPostingHandler
from .linkedin_posting_handler import LinkedInPostingHandler
from .x_posting_handler import XPostingHandler

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
        
        return {
            'instagram': meta_status.get('instagram_available', False),
            'facebook': meta_status.get('facebook_available', False),
            'linkedin': linkedin_status.get('linkedin_available', False),
            'x': x_status.get('x_available', False)
        }
    
    def get_platform_errors(self) -> Dict[str, str]:
        """Get error messages for unavailable platforms."""
        meta_status = self.meta_handler.get_posting_status()
        linkedin_status = self.linkedin_handler.get_posting_status()
        x_status = self.x_handler.get_posting_status()
        
        errors = {}
        
        if not meta_status.get('credentials_loaded', False):
            errors['instagram'] = meta_status.get('error_message', 'Meta credentials not configured')
            errors['facebook'] = meta_status.get('error_message', 'Meta credentials not configured')
        
        if not linkedin_status.get('credentials_loaded', False):
            errors['linkedin'] = linkedin_status.get('error_message', 'LinkedIn credentials not configured')
        
        if not x_status.get('credentials_loaded', False):
            errors['x'] = x_status.get('error_message', 'X credentials not configured')
        
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