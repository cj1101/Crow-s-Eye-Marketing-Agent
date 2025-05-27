"""
Meta API posting handler for uploading custom media to Instagram and Facebook.
Handles the complete posting workflow including media upload, container creation, and publishing.
"""
import os
import json
import logging
import time
import requests
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QThread

from ...config import constants as const
from ...handlers.media_handler import load_meta_credentials

class MetaPostingSignals(QObject):
    """Signals for Meta API posting operations."""
    upload_started = Signal(str)  # platform
    upload_progress = Signal(str, int)  # message, percentage
    upload_success = Signal(str, dict)  # platform, response_data
    upload_error = Signal(str, str)  # platform, error_message
    status_update = Signal(str)

class MetaPostingHandler:
    """Handler for posting media to Instagram and Facebook via Meta Graph API."""
    
    def __init__(self):
        """Initialize the Meta posting handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.signals = MetaPostingSignals()
        self.credentials = None
        self._load_credentials()
        
    def _load_credentials(self) -> bool:
        """Load Meta API credentials."""
        try:
            self.credentials = load_meta_credentials()
            if not self.credentials:
                self.logger.error("Failed to load Meta credentials")
                return False
            return True
        except Exception as e:
            self.logger.exception(f"Error loading credentials: {e}")
            return False
    
    def post_to_instagram(self, media_path: str, caption: str = "", 
                         is_video: bool = False, audio_path: str = None) -> Tuple[bool, str]:
        """
        Post media to Instagram.
        
        Args:
            media_path: Path to the media file
            caption: Caption for the post
            is_video: Whether the media is a video
            
        Returns:
            Tuple of (success, message/error)
        """
        try:
            if not self.credentials:
                if not self._load_credentials():
                    return False, "Meta credentials not available"
            
            self.signals.upload_started.emit("Instagram")
            self.signals.status_update.emit("Uploading to Instagram...")
            
            # Step 1: Create media container
            container_id = self._create_instagram_container(media_path, caption, is_video)
            if not container_id:
                return False, "Failed to create Instagram media container"
            
            self.signals.upload_progress.emit("Container created, publishing...", 50)
            
            # Step 2: Publish the container
            success, message = self._publish_instagram_container(container_id)
            
            if success:
                self.signals.upload_success.emit("Instagram", {"container_id": container_id})
                self.signals.status_update.emit("Successfully posted to Instagram!")
                return True, "Successfully posted to Instagram"
            else:
                return False, f"Failed to publish to Instagram: {message}"
                
        except Exception as e:
            error_msg = f"Error posting to Instagram: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("Instagram", error_msg)
            return False, error_msg
    
    def post_to_facebook(self, media_path: str, caption: str = "", 
                        is_video: bool = False, audio_path: str = None) -> Tuple[bool, str]:
        """
        Post media to Facebook.
        
        Args:
            media_path: Path to the media file
            caption: Caption for the post
            is_video: Whether the media is a video
            
        Returns:
            Tuple of (success, message/error)
        """
        try:
            if not self.credentials:
                if not self._load_credentials():
                    return False, "Meta credentials not available"
            
            self.signals.upload_started.emit("Facebook")
            self.signals.status_update.emit("Uploading to Facebook...")
            
            # For Facebook, we can post directly
            if is_video:
                success, message = self._post_facebook_video(media_path, caption)
            else:
                success, message = self._post_facebook_photo(media_path, caption)
            
            if success:
                self.signals.upload_success.emit("Facebook", {"message": message})
                self.signals.status_update.emit("Successfully posted to Facebook!")
                return True, "Successfully posted to Facebook"
            else:
                return False, f"Failed to post to Facebook: {message}"
                
        except Exception as e:
            error_msg = f"Error posting to Facebook: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("Facebook", error_msg)
            return False, error_msg
    
    def _create_instagram_container(self, media_path: str, caption: str, 
                                  is_video: bool) -> Optional[str]:
        """Create Instagram media container."""
        try:
            ig_user_id = self.credentials.get('instagram_business_account_id')
            access_token = self.credentials.get('facebook_page_access_token')
            
            if not ig_user_id or not access_token:
                self.logger.error("Missing Instagram credentials")
                return None
            
            # Upload media file first
            media_url = self._upload_media_file(media_path)
            if not media_url:
                return None
            
            # Create container
            url = f"{const.META_API_BASE_URL}/{ig_user_id}/media"
            
            data = {
                'access_token': access_token,
                'caption': caption
            }
            
            if is_video:
                data['media_type'] = 'VIDEO'
                data['video_url'] = media_url
            else:
                data['image_url'] = media_url
            
            response = requests.post(url, data=data, timeout=const.META_API_TIMEOUT)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('id')
            else:
                self.logger.error(f"Failed to create container: {response.text}")
                return None
                
        except Exception as e:
            self.logger.exception(f"Error creating Instagram container: {e}")
            return None
    
    def _publish_instagram_container(self, container_id: str) -> Tuple[bool, str]:
        """Publish Instagram media container."""
        try:
            ig_user_id = self.credentials.get('instagram_business_account_id')
            access_token = self.credentials.get('facebook_page_access_token')
            
            url = f"{const.META_API_BASE_URL}/{ig_user_id}/media_publish"
            
            data = {
                'creation_id': container_id,
                'access_token': access_token
            }
            
            response = requests.post(url, data=data, timeout=const.META_API_TIMEOUT)
            
            if response.status_code == 200:
                return True, "Published successfully"
            else:
                error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                return False, error_msg
                
        except Exception as e:
            return False, str(e)
    
    def _post_facebook_photo(self, media_path: str, caption: str) -> Tuple[bool, str]:
        """Post photo to Facebook page."""
        try:
            page_id = self.credentials.get('facebook_page_id')
            access_token = self.credentials.get('facebook_page_access_token')
            
            url = f"{const.META_API_BASE_URL}/{page_id}/photos"
            
            with open(media_path, 'rb') as media_file:
                files = {'source': media_file}
                data = {
                    'message': caption,
                    'access_token': access_token
                }
                
                response = requests.post(url, files=files, data=data, 
                                       timeout=const.META_API_TIMEOUT)
            
            if response.status_code == 200:
                result = response.json()
                return True, result.get('id', 'Posted successfully')
            else:
                error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                return False, error_msg
                
        except Exception as e:
            return False, str(e)
    
    def _post_facebook_video(self, media_path: str, caption: str) -> Tuple[bool, str]:
        """Post video to Facebook page."""
        try:
            page_id = self.credentials.get('facebook_page_id')
            access_token = self.credentials.get('facebook_page_access_token')
            
            url = f"{const.META_API_BASE_URL}/{page_id}/videos"
            
            with open(media_path, 'rb') as media_file:
                files = {'source': media_file}
                data = {
                    'description': caption,
                    'access_token': access_token
                }
                
                response = requests.post(url, files=files, data=data, 
                                       timeout=const.META_API_TIMEOUT)
            
            if response.status_code == 200:
                result = response.json()
                return True, result.get('id', 'Posted successfully')
            else:
                error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                return False, error_msg
                
        except Exception as e:
            return False, str(e)
    
    def _upload_media_file(self, media_path: str) -> Optional[str]:
        """
        Upload media file to a temporary hosting service.
        In production, this would upload to your own server or cloud storage.
        For now, this is a placeholder that would need to be implemented.
        """
        # This is a placeholder - in a real implementation, you would:
        # 1. Upload the file to your server or cloud storage (AWS S3, etc.)
        # 2. Return the public URL
        # 3. For Instagram, the URL must be publicly accessible
        
        # For development/testing, you might use a service like:
        # - Your own web server
        # - AWS S3 with public access
        # - Cloudinary
        # - ImgBB API
        
        self.logger.warning("Media file upload not implemented - using local path")
        return f"file://{media_path}"  # This won't work with Instagram API
    
    def validate_media_file(self, media_path: str) -> Tuple[bool, str]:
        """
        Validate media file for posting.
        
        Args:
            media_path: Path to the media file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not os.path.exists(media_path):
                return False, "File does not exist"
            
            file_size = os.path.getsize(media_path)
            file_ext = os.path.splitext(media_path)[1].lower()
            
            # Check file type
            if file_ext in const.SUPPORTED_IMAGE_FORMATS:
                # Image validation
                if file_size > const.MAX_IMAGE_SIZE:
                    return False, f"Image file too large (max {const.MAX_IMAGE_SIZE // (1024*1024)}MB)"
            elif file_ext in const.SUPPORTED_VIDEO_FORMATS:
                # Video validation
                if file_size > const.MAX_VIDEO_SIZE:
                    return False, f"Video file too large (max {const.MAX_VIDEO_SIZE // (1024*1024)}MB)"
            else:
                return False, f"Unsupported file type: {file_ext}"
            
            return True, "File is valid"
            
        except Exception as e:
            return False, f"Error validating file: {str(e)}"
    
    def get_posting_status(self) -> Dict[str, Any]:
        """Get current posting status and capabilities."""
        status = {
            "credentials_loaded": self.credentials is not None,
            "instagram_available": False,
            "facebook_available": False,
            "error_message": None
        }
        
        if self.credentials:
            status["instagram_available"] = bool(
                self.credentials.get('instagram_business_account_id') and 
                self.credentials.get('facebook_page_access_token')
            )
            status["facebook_available"] = bool(
                self.credentials.get('facebook_page_id') and 
                self.credentials.get('facebook_page_access_token')
            )
        else:
            status["error_message"] = "Meta credentials not loaded"
        
        return status


class MetaPostingWorker(QThread):
    """Worker thread for Meta API posting operations."""
    
    finished = Signal(bool, str, str)  # success, platform, message
    progress = Signal(str, int)  # message, percentage
    
    def __init__(self, handler: MetaPostingHandler, media_path: str, 
                 caption: str, platforms: List[str], audio_path: str = None):
        super().__init__()
        self.handler = handler
        self.media_path = media_path
        self.caption = caption
        self.platforms = platforms
        self.audio_path = audio_path
        self.is_video = any(media_path.lower().endswith(ext) 
                           for ext in const.SUPPORTED_VIDEO_FORMATS)
    
    def run(self):
        """Run the posting operation in a separate thread."""
        try:
            total_platforms = len(self.platforms)
            
            for i, platform in enumerate(self.platforms):
                self.progress.emit(f"Posting to {platform}...", 
                                 int((i / total_platforms) * 100))
                
                if platform.lower() == "instagram":
                    success, message = self.handler.post_to_instagram(
                        self.media_path, self.caption, self.is_video, self.audio_path
                    )
                elif platform.lower() == "facebook":
                    success, message = self.handler.post_to_facebook(
                        self.media_path, self.caption, self.is_video, self.audio_path
                    )
                else:
                    success, message = False, f"Unsupported platform: {platform}"
                
                self.finished.emit(success, platform, message)
                
                if not success:
                    break
                    
                # Small delay between posts
                time.sleep(1)
            
            self.progress.emit("Posting complete", 100)
            
        except Exception as e:
            self.finished.emit(False, "Unknown", f"Error in posting worker: {str(e)}") 