"""
TikTok API handler for posting content using the official TikTok API.
Supports video uploads and photo carousels (up to 35 images).
"""
import os
import json
import logging
import requests
import mimetypes
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from PySide6.QtCore import QObject, Signal

from ...config import constants as const

class TikTokAPISignals(QObject):
    """Signals for TikTok API operations."""
    upload_started = Signal(str)  # platform
    upload_progress = Signal(str, int)  # message, percentage
    upload_success = Signal(str, dict)  # platform, response_data
    upload_error = Signal(str, str)  # platform, error_message
    status_update = Signal(str)

class TikTokAPIHandler:
    """Handler for TikTok API operations."""
    
    def __init__(self):
        """Initialize the TikTok API handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.signals = TikTokAPISignals()
        self.base_url = "https://open.tiktokapis.com/v2"
        self.credentials_file = os.path.join(const.ROOT_DIR, 'tiktok_credentials.json')
        self.credentials = self.load_credentials()
    
    def load_credentials(self) -> Dict[str, Any]:
        """Load TikTok credentials from file."""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"TikTok credentials file not found")
        return {}
    
    def save_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Save TikTok credentials to file."""
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save TikTok credentials: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if TikTok is authenticated."""
        return bool(self.credentials.get('access_token'))
    
    def post_media(self, media_paths: List[str] = None, media_path: str = "", caption: str = "", 
                   is_video: bool = False, **kwargs) -> Tuple[bool, str]:
        """
        Post media to TikTok.
        
        Args:
            media_paths: List of media file paths (for photo carousels, up to 35 images)
            media_path: Single media file path (for backwards compatibility)
            caption: Caption for the post (up to 2200 characters)
            is_video: Whether the media is a video
            **kwargs: Additional parameters like slideshow_title, privacy_level, etc.
            
        Returns:
            Tuple of (success, message)
        """
        try:
            self.signals.upload_started.emit("tiktok")
            self.signals.status_update.emit("Starting TikTok upload...")
            
            if not self.credentials.get('access_token'):
                error_msg = "TikTok not authenticated. Please connect your account first."
                self.signals.upload_error.emit("tiktok", error_msg)
                return False, error_msg
            
            # Handle both single file and multiple files
            if media_paths and len(media_paths) > 1:
                # Photo carousel mode
                return self._post_photo_carousel(media_paths, caption, **kwargs)
            else:
                # Single file mode (video or single photo)
                single_path = media_paths[0] if media_paths else media_path
                
                if not os.path.exists(single_path):
                    error_msg = f"Media file not found: {single_path}"
                    self.signals.upload_error.emit("tiktok", error_msg)
                    return False, error_msg
                
                # Check if it's a photo or video
                file_ext = os.path.splitext(single_path)[1].lower()
                if file_ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                    # Single photo (converted to carousel)
                    return self._post_photo_carousel([single_path], caption, **kwargs)
                else:
                    # Video
                    if not is_video:
                        self.logger.warning("TikTok: Treating non-video file as video based on extension")
                    return self._post_video(single_path, caption, **kwargs)
                
        except Exception as e:
            error_msg = f"Error posting to TikTok: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("tiktok", error_msg)
            return False, error_msg
    
    def _post_photo_carousel(self, media_paths: List[str], caption: str, **kwargs) -> Tuple[bool, str]:
        """Post photo carousel to TikTok (up to 35 images)."""
        try:
            if len(media_paths) > 35:
                return False, "TikTok photo carousels support maximum 35 images"
            
            if len(media_paths) < 1:
                return False, "At least 1 image is required for TikTok carousel"
            
            self.signals.upload_progress.emit("Validating carousel images...", 10)
            
            # Validate all images
            for media_path in media_paths:
                if not os.path.exists(media_path):
                    return False, f"Image file not found: {media_path}"
                
                valid, validation_msg = self.validate_media_file(media_path, is_photo=True)
                if not valid:
                    return False, f"Invalid image {media_path}: {validation_msg}"
            
            access_token = self.credentials['access_token']
            
            self.signals.upload_progress.emit("Initializing TikTok photo carousel...", 20)
            
            # Step 1: Initialize photo carousel upload
            init_url = f"{self.base_url}/post/photo/init/"
            headers = {
                'Authorization': f"Bearer {access_token}",
                'Content-Type': 'application/json'
            }
            
            # Prepare slideshow info
            slideshow_title = kwargs.get('slideshow_title', caption[:90] if caption else "Photo Carousel")
            privacy_level = kwargs.get('privacy_level', 'PUBLIC_TO_EVERYONE')  # Can be SELF_ONLY, MUTUAL_FOLLOW_FRIENDS, etc.
            
            # Prepare image info for each image
            media_info = []
            for i, media_path in enumerate(media_paths):
                file_size = os.path.getsize(media_path)
                media_info.append({
                    'media_type': 'PHOTO',
                    'media_size': file_size
                })
            
            init_data = {
                'post_info': {
                    'title': slideshow_title,
                    'description': caption[:2200] if caption else "Posted via Crow's Eye Marketing Tool",
                    'privacy_level': privacy_level,
                    'disable_duet': kwargs.get('disable_duet', False),
                    'disable_comment': kwargs.get('disable_comment', False),
                    'disable_stitch': kwargs.get('disable_stitch', False),
                    'brand_content_toggle': kwargs.get('brand_content_toggle', False),
                    'brand_organic_toggle': kwargs.get('brand_organic_toggle', False)
                },
                'source_info': {
                    'source': 'PHOTO_UPLOAD',
                    'photo_count': len(media_paths),
                    'media_info': media_info
                }
            }
            
            response = requests.post(init_url, headers=headers, json=init_data, timeout=30)
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Failed to initialize carousel upload')
                return False, f"TikTok carousel initialization failed: {error_msg}"
            
            result = response.json()
            if result.get('error', {}).get('code') != 'ok':
                error_msg = result.get('error', {}).get('message', 'Unknown initialization error')
                return False, f"TikTok carousel initialization failed: {error_msg}"
            
            upload_data = result.get('data', {})
            publish_id = upload_data.get('publish_id')
            upload_urls = upload_data.get('upload_urls', [])
            
            if not publish_id or not upload_urls:
                return False, "TikTok carousel initialization failed: Missing upload data"
            
            if len(upload_urls) != len(media_paths):
                return False, f"Upload URL count mismatch: got {len(upload_urls)}, expected {len(media_paths)}"
            
            # Step 2: Upload each image
            progress_step = 60 // len(media_paths)  # Progress from 20% to 80%
            current_progress = 20
            
            for i, (media_path, upload_url) in enumerate(zip(media_paths, upload_urls)):
                self.signals.upload_progress.emit(f"Uploading image {i+1}/{len(media_paths)}...", current_progress)
                
                with open(media_path, 'rb') as image_file:
                    # Get content type
                    content_type, _ = mimetypes.guess_type(media_path)
                    if not content_type:
                        content_type = 'image/jpeg'
                    
                    file_size = os.path.getsize(media_path)
                    upload_headers = {
                        'Content-Type': content_type,
                        'Content-Length': str(file_size)
                    }
                    
                    upload_response = requests.put(
                        upload_url, 
                        data=image_file, 
                        headers=upload_headers, 
                        timeout=120
                    )
                    
                    if upload_response.status_code not in [200, 201]:
                        return False, f"TikTok image {i+1} upload failed: HTTP {upload_response.status_code}"
                
                current_progress += progress_step
            
            self.signals.upload_progress.emit("Publishing TikTok photo carousel...", 90)
            
            # Step 3: Publish the carousel
            publish_url = f"{self.base_url}/post/photo/publish/"
            publish_data = {
                'post_id': publish_id
            }
            
            publish_response = requests.post(publish_url, headers=headers, json=publish_data, timeout=30)
            
            if publish_response.status_code == 200:
                publish_result = publish_response.json()
                if publish_result.get('error', {}).get('code') == 'ok':
                    self.signals.upload_progress.emit("TikTok photo carousel published successfully!", 100)
                    self.signals.upload_success.emit("tiktok", {
                        'publish_id': publish_id,
                        'platform': 'tiktok',
                        'type': 'photo_carousel',
                        'image_count': len(media_paths)
                    })
                    
                    return True, f"Successfully posted TikTok photo carousel with {len(media_paths)} images (Publish ID: {publish_id})"
                else:
                    error_msg = publish_result.get('error', {}).get('message', 'Unknown publish error')
                    return False, f"Failed to publish TikTok carousel: {error_msg}"
            else:
                return False, f"TikTok carousel publish failed: HTTP {publish_response.status_code}"
                
        except Exception as e:
            error_msg = f"Error in TikTok photo carousel posting: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("tiktok", error_msg)
            return False, error_msg

    def _post_video(self, media_path: str, caption: str, **kwargs) -> Tuple[bool, str]:
        """Post video to TikTok using the Content Posting API."""
        try:
            access_token = self.credentials['access_token']
            
            self.signals.upload_progress.emit("Initializing TikTok video upload...", 10)
            
            # Step 1: Initialize video upload
            init_url = f"{self.base_url}/post/video/init/"
            headers = {
                'Authorization': f"Bearer {access_token}",
                'Content-Type': 'application/json'
            }
            
            # Get video file info
            file_size = os.path.getsize(media_path)
            
            init_data = {
                'post_info': {
                    'title': caption[:150] if caption else "Posted via Crow's Eye Marketing Tool",
                    'privacy_level': kwargs.get('privacy_level', 'PUBLIC_TO_EVERYONE'),
                    'disable_duet': kwargs.get('disable_duet', False),
                    'disable_comment': kwargs.get('disable_comment', False),
                    'disable_stitch': kwargs.get('disable_stitch', False),
                    'video_cover_timestamp_ms': kwargs.get('video_cover_timestamp_ms', 1000)
                },
                'source_info': {
                    'source': 'FILE_UPLOAD',
                    'video_size': file_size,
                    'chunk_size': min(file_size, 10 * 1024 * 1024),  # 10MB chunks
                    'total_chunk_count': 1
                }
            }
            
            response = requests.post(init_url, headers=headers, json=init_data, timeout=30)
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Failed to initialize upload')
                return False, f"TikTok upload initialization failed: {error_msg}"
            
            result = response.json()
            if result.get('error', {}).get('code') != 'ok':
                error_msg = result.get('error', {}).get('message', 'Unknown initialization error')
                return False, f"TikTok upload initialization failed: {error_msg}"
            
            upload_data = result.get('data', {})
            publish_id = upload_data.get('publish_id')
            upload_url = upload_data.get('upload_url')
            
            if not publish_id or not upload_url:
                return False, "TikTok upload initialization failed: Missing upload data"
            
            self.signals.upload_progress.emit("Uploading video to TikTok...", 50)
            
            # Step 2: Upload video file
            with open(media_path, 'rb') as video_file:
                upload_headers = {
                    'Content-Type': 'video/mp4',
                    'Content-Range': f'bytes 0-{file_size-1}/{file_size}'
                }
                
                upload_response = requests.put(
                    upload_url, 
                    data=video_file, 
                    headers=upload_headers, 
                    timeout=300  # 5 minutes for large files
                )
                
                if upload_response.status_code not in [200, 201]:
                    return False, f"TikTok video upload failed: HTTP {upload_response.status_code}"
            
            self.signals.upload_progress.emit("Publishing TikTok video...", 90)
            
            # Step 3: Publish the video
            publish_url = f"{self.base_url}/post/video/publish/"
            publish_data = {
                'post_id': publish_id
            }
            
            publish_response = requests.post(publish_url, headers=headers, json=publish_data, timeout=30)
            
            if publish_response.status_code == 200:
                publish_result = publish_response.json()
                if publish_result.get('error', {}).get('code') == 'ok':
                    self.signals.upload_progress.emit("TikTok video published successfully!", 100)
                    self.signals.upload_success.emit("tiktok", {
                        'publish_id': publish_id,
                        'platform': 'tiktok',
                        'type': 'video'
                    })
                    
                    return True, f"Successfully posted to TikTok (Publish ID: {publish_id})"
                else:
                    error_msg = publish_result.get('error', {}).get('message', 'Unknown publish error')
                    return False, f"Failed to publish TikTok video: {error_msg}"
            else:
                return False, f"TikTok video publish failed: HTTP {publish_response.status_code}"
                
        except Exception as e:
            error_msg = f"Error in TikTok video posting: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("tiktok", error_msg)
            return False, error_msg
    
    def validate_media_file(self, media_path: str, is_photo: bool = False) -> Tuple[bool, str]:
        """Validate media file for TikTok posting."""
        try:
            if not os.path.exists(media_path):
                return False, "Media file does not exist"
            
            file_size = os.path.getsize(media_path)
            file_ext = os.path.splitext(media_path)[1].lower()
            
            if is_photo:
                # Photo validation for carousels
                photo_formats = ['.jpg', '.jpeg', '.png', '.webp']
                if file_ext not in photo_formats:
                    return False, f"Unsupported photo format: {file_ext}. Supported: JPG, JPEG, PNG, WebP"
                
                # TikTok photo size limit: 20MB per image
                if file_size > 20 * 1024 * 1024:
                    return False, "Photo file too large (max 20MB per image)"
                
                return True, "Valid photo file"
            else:
                # Video validation
                video_formats = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.webm']
                if file_ext not in video_formats:
                    return False, f"Unsupported video format: {file_ext}"
                
                # TikTok video size limit: 4GB
                if file_size > 4 * 1024 * 1024 * 1024:
                    return False, "Video file too large (max 4GB)"
                
                return True, "Valid video file"
                
        except Exception as e:
            return False, f"Error validating media file: {str(e)}"
    
    def get_posting_status(self) -> Dict[str, Any]:
        """Get current posting status and capabilities."""
        return {
            'platform': 'tiktok',
            'authenticated': self.is_authenticated(),
            'supports_video': True,
            'supports_photo_carousel': True,
            'supports_single_photo': True,
            'max_carousel_images': 35,
            'max_video_size_gb': 4,
            'max_photo_size_mb': 20,
            'max_caption_length': 2200,
            'supported_video_formats': ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.webm'],
            'supported_photo_formats': ['.jpg', '.jpeg', '.png', '.webp']
        }
    
    def logout(self) -> None:
        """Logout from TikTok (clear credentials)."""
        try:
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
            self.credentials = {}
            self.logger.info("TikTok logout successful")
        except Exception as e:
            self.logger.error(f"Error during TikTok logout: {e}") 