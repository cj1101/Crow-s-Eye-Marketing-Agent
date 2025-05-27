"""
TikTok API handler for posting content using the official TikTok for Developers API.
Supports video uploads and content management.
"""
import os
import json
import logging
import requests
from typing import Dict, Any, Optional, Tuple
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
        self.credentials = {}
        self.base_url = "https://open.tiktokapis.com/v2"
        
        self._load_credentials()
    
    def _load_credentials(self) -> bool:
        """Load TikTok credentials from file."""
        try:
            creds_file = os.path.join(const.ROOT_DIR, 'tiktok_credentials.json')
            if os.path.exists(creds_file):
                with open(creds_file, 'r', encoding='utf-8') as f:
                    self.credentials = json.load(f)
                return True
            else:
                self.logger.warning("TikTok credentials file not found")
                return False
        except Exception as e:
            self.logger.error(f"Error loading TikTok credentials: {e}")
            return False
    
    def save_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Save TikTok credentials to file."""
        try:
            creds_file = os.path.join(const.ROOT_DIR, 'tiktok_credentials.json')
            with open(creds_file, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, indent=4)
            
            self.credentials = credentials
            self.logger.info("TikTok credentials saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error saving TikTok credentials: {e}")
            return False
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the TikTok API connection."""
        try:
            if not self.credentials.get('access_token'):
                return False, "No access token found"
            
            # Test with user info endpoint
            url = f"{self.base_url}/user/info/"
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}",
                'Content-Type': 'application/json'
            }
            params = {
                'fields': 'open_id,union_id,avatar_url,display_name'
            }
            
            response = requests.post(url, headers=headers, json=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('error', {}).get('code') == 'ok':
                    user_data = data.get('data', {}).get('user', {})
                    display_name = user_data.get('display_name', 'Unknown')
                    return True, f"Connected to TikTok account: {display_name}"
                else:
                    error_msg = data.get('error', {}).get('message', 'Unknown error')
                    return False, f"TikTok API error: {error_msg}"
            else:
                return False, f"TikTok API connection failed: HTTP {response.status_code}"
                
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    def post_media(self, media_path: str, caption: str = "", is_video: bool = False) -> Tuple[bool, str]:
        """
        Post media to TikTok.
        
        Args:
            media_path: Path to the media file
            caption: Caption for the post
            is_video: Whether the media is a video (TikTok only supports videos)
            
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
            
            if not os.path.exists(media_path):
                error_msg = f"Media file not found: {media_path}"
                self.signals.upload_error.emit("tiktok", error_msg)
                return False, error_msg
            
            # TikTok only supports video content
            if not is_video:
                error_msg = "TikTok only supports video content. Please select a video file."
                self.signals.upload_error.emit("tiktok", error_msg)
                return False, error_msg
            
            # Validate media file
            valid, validation_msg = self.validate_media_file(media_path)
            if not valid:
                self.signals.upload_error.emit("tiktok", validation_msg)
                return False, validation_msg
            
            return self._post_video(media_path, caption)
                
        except Exception as e:
            error_msg = f"Error posting to TikTok: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("tiktok", error_msg)
            return False, error_msg
    
    def _post_video(self, media_path: str, caption: str) -> Tuple[bool, str]:
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
                    'title': caption[:150] if caption else "Posted via Breadsmith Marketing Tool",
                    'privacy_level': 'SELF_ONLY',  # Can be changed to PUBLIC_TO_EVERYONE
                    'disable_duet': False,
                    'disable_comment': False,
                    'disable_stitch': False,
                    'video_cover_timestamp_ms': 1000
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
                        'platform': 'tiktok'
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
    
    def validate_media_file(self, media_path: str) -> Tuple[bool, str]:
        """Validate media file for TikTok posting."""
        try:
            if not os.path.exists(media_path):
                return False, "Media file does not exist"
            
            file_size = os.path.getsize(media_path)
            file_ext = os.path.splitext(media_path)[1].lower()
            
            # TikTok only supports video formats
            video_formats = ['.mp4', '.mov', '.avi', '.webm']
            
            if file_ext not in video_formats:
                return False, f"TikTok only supports video files. Unsupported format: {file_ext}"
            
            # Check file size (max 4GB)
            if file_size > 4 * 1024 * 1024 * 1024:
                return False, "Video file too large (max 4GB)"
            
            # Check minimum file size (1KB)
            if file_size < 1024:
                return False, "Video file too small (min 1KB)"
            
            return True, "Valid video file for TikTok"
                
        except Exception as e:
            return False, f"Error validating media file: {str(e)}"
    
    def get_posting_status(self) -> Dict[str, Any]:
        """Get TikTok posting status and availability."""
        try:
            has_credentials = bool(self.credentials.get('access_token'))
            
            if not has_credentials:
                return {
                    'tiktok_available': False,
                    'credentials_loaded': False,
                    'error_message': 'TikTok credentials not configured'
                }
            
            # Test connection
            connection_ok, connection_msg = self.test_connection()
            
            return {
                'tiktok_available': connection_ok,
                'credentials_loaded': True,
                'error_message': None if connection_ok else connection_msg
            }
            
        except Exception as e:
            return {
                'tiktok_available': False,
                'credentials_loaded': False,
                'error_message': f'Error checking TikTok status: {str(e)}'
            }
    
    def logout(self) -> None:
        """Clear TikTok credentials and logout."""
        try:
            self.credentials = {}
            creds_file = os.path.join(const.ROOT_DIR, 'tiktok_credentials.json')
            if os.path.exists(creds_file):
                os.remove(creds_file)
            self.logger.info("TikTok logout successful")
        except Exception as e:
            self.logger.error(f"Error during TikTok logout: {e}") 