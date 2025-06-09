"""
Instagram API handler for posting content using the official Instagram Graph API.
Supports both Instagram Basic Display API and Instagram Graph API for business accounts.
"""
import os
import json
import logging
import requests
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from PySide6.QtCore import QObject, Signal

from ...config import constants as const

class InstagramAPISignals(QObject):
    """Signals for Instagram API operations."""
    upload_started = Signal(str)  # platform
    upload_progress = Signal(str, int)  # message, percentage
    upload_success = Signal(str, dict)  # platform, response_data
    upload_error = Signal(str, str)  # platform, error_message
    status_update = Signal(str)

class InstagramAPIHandler:
    """Handler for Instagram API operations."""
    
    def __init__(self):
        """Initialize the Instagram API handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.signals = InstagramAPISignals()
        self.credentials = {}
        self.base_url = "https://graph.instagram.com"
        self.graph_url = "https://graph.facebook.com/v18.0"
        
        self._load_credentials()
    
    def _load_credentials(self) -> bool:
        """Load Instagram credentials from file."""
        try:
            creds_file = os.path.join(const.ROOT_DIR, 'instagram_credentials.json')
            if os.path.exists(creds_file):
                with open(creds_file, 'r', encoding='utf-8') as f:
                    self.credentials = json.load(f)
                return True
            else:
                self.logger.warning("Instagram credentials file not found")
                return False
        except Exception as e:
            self.logger.error(f"Error loading Instagram credentials: {e}")
            return False
    
    def save_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Save Instagram credentials to file."""
        try:
            creds_file = os.path.join(const.ROOT_DIR, 'instagram_credentials.json')
            with open(creds_file, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, indent=4)
            
            self.credentials = credentials
            self.logger.info("Instagram credentials saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error saving Instagram credentials: {e}")
            return False
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the Instagram API connection."""
        try:
            if not self.credentials.get('access_token'):
                return False, "No access token found"
            
            # Test with user info endpoint
            url = f"{self.base_url}/me"
            params = {
                'fields': 'id,username',
                'access_token': self.credentials['access_token']
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                username = data.get('username', 'Unknown')
                return True, f"Connected to Instagram account: @{username}"
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                return False, f"Instagram API error: {error_msg}"
                
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    def post_media(self, media_path: str, caption: str = "", is_video: bool = False) -> Tuple[bool, str]:
        """
        Post media to Instagram.
        
        Args:
            media_path: Path to the media file
            caption: Caption for the post
            is_video: Whether the media is a video
            
        Returns:
            Tuple of (success, message)
        """
        try:
            self.signals.upload_started.emit("instagram")
            self.signals.status_update.emit("Starting Instagram upload...")
            
            if not self.credentials.get('access_token'):
                error_msg = "Instagram not authenticated. Please connect your account first."
                self.signals.upload_error.emit("instagram", error_msg)
                return False, error_msg
            
            if not os.path.exists(media_path):
                error_msg = f"Media file not found: {media_path}"
                self.signals.upload_error.emit("instagram", error_msg)
                return False, error_msg
            
            # Validate media file
            valid, validation_msg = self.validate_media_file(media_path)
            if not valid:
                self.signals.upload_error.emit("instagram", validation_msg)
                return False, validation_msg
            
            # Use Instagram Graph API for business accounts
            if self.credentials.get('instagram_business_account_id'):
                return self._post_via_graph_api(media_path, caption, is_video)
            else:
                return False, "Instagram Business Account required for posting"
                
        except Exception as e:
            error_msg = f"Error posting to Instagram: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("instagram", error_msg)
            return False, error_msg
    
    def _post_via_graph_api(self, media_path: str, caption: str, is_video: bool) -> Tuple[bool, str]:
        """Post media using Instagram Graph API."""
        try:
            ig_account_id = self.credentials['instagram_business_account_id']
            access_token = self.credentials['access_token']
            
            self.signals.upload_progress.emit("Uploading media to Instagram...", 25)
            
            # Step 1: Create media container
            if is_video:
                container_response = self._create_video_container(ig_account_id, media_path, caption, access_token)
            else:
                container_response = self._create_image_container(ig_account_id, media_path, caption, access_token)
            
            if not container_response[0]:
                return container_response
            
            container_id = container_response[1]
            
            self.signals.upload_progress.emit("Publishing Instagram post...", 75)
            
            # Step 2: Publish the media
            publish_url = f"{self.graph_url}/{ig_account_id}/media_publish"
            publish_data = {
                'creation_id': container_id,
                'access_token': access_token
            }
            
            publish_response = requests.post(publish_url, data=publish_data, timeout=30)
            
            if publish_response.status_code == 200:
                result = publish_response.json()
                media_id = result.get('id')
                
                self.signals.upload_progress.emit("Instagram post published successfully!", 100)
                self.signals.upload_success.emit("instagram", {
                    'media_id': media_id,
                    'platform': 'instagram'
                })
                
                return True, f"Successfully posted to Instagram (Media ID: {media_id})"
            else:
                error_data = publish_response.json() if publish_response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown publish error')
                self.signals.upload_error.emit("instagram", error_msg)
                return False, f"Failed to publish Instagram post: {error_msg}"
                
        except Exception as e:
            error_msg = f"Error in Instagram Graph API posting: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("instagram", error_msg)
            return False, error_msg
    
    def _create_image_container(self, ig_account_id: str, media_path: str, caption: str, access_token: str) -> Tuple[bool, str]:
        """Create an image container for Instagram posting."""
        try:
            # First, upload image to Facebook's servers
            upload_url = f"{self.graph_url}/{ig_account_id}/media"
            
            # Read the image file
            with open(media_path, 'rb') as image_file:
                files = {
                    'source': image_file
                }
                data = {
                    'caption': caption,
                    'access_token': access_token
                }
                
                response = requests.post(upload_url, files=files, data=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return True, result.get('id')
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown container creation error')
                return False, error_msg
                
        except Exception as e:
            return False, f"Error creating image container: {str(e)}"
    
    def _create_video_container(self, ig_account_id: str, media_path: str, caption: str, access_token: str) -> Tuple[bool, str]:
        """Create a video container for Instagram posting."""
        try:
            upload_url = f"{self.graph_url}/{ig_account_id}/media"
            
            # Read the video file
            with open(media_path, 'rb') as video_file:
                files = {
                    'source': video_file
                }
                data = {
                    'caption': caption,
                    'media_type': 'VIDEO',
                    'access_token': access_token
                }
                
                response = requests.post(upload_url, files=files, data=data, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                return True, result.get('id')
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown container creation error')
                return False, error_msg
                
        except Exception as e:
            return False, f"Error creating video container: {str(e)}"
    
    def validate_media_file(self, media_path: str) -> Tuple[bool, str]:
        """Validate media file for Instagram posting."""
        try:
            if not os.path.exists(media_path):
                return False, "Media file does not exist"
            
            file_size = os.path.getsize(media_path)
            file_ext = os.path.splitext(media_path)[1].lower()
            
            # Check file type
            image_formats = ['.jpg', '.jpeg', '.png']
            video_formats = ['.mp4', '.mov']
            
            if file_ext in image_formats:
                # Image validation
                if file_size > 8 * 1024 * 1024:  # 8MB limit
                    return False, "Image file too large (max 8MB)"
                return True, "Valid image file"
                
            elif file_ext in video_formats:
                # Video validation
                if file_size > 100 * 1024 * 1024:  # 100MB limit
                    return False, "Video file too large (max 100MB)"
                return True, "Valid video file"
            else:
                return False, f"Unsupported file format: {file_ext}"
                
        except Exception as e:
            return False, f"Error validating media file: {str(e)}"
    
    def get_posting_status(self) -> Dict[str, Any]:
        """Get Instagram posting status and availability."""
        try:
            has_credentials = bool(self.credentials.get('access_token'))
            has_business_account = bool(self.credentials.get('instagram_business_account_id'))
            
            if not has_credentials:
                return {
                    'instagram_available': False,
                    'credentials_loaded': False,
                    'error_message': 'Instagram credentials not configured'
                }
            
            if not has_business_account:
                return {
                    'instagram_available': False,
                    'credentials_loaded': True,
                    'error_message': 'Instagram Business Account required for posting'
                }
            
            # Test connection
            connection_ok, connection_msg = self.test_connection()
            
            return {
                'instagram_available': connection_ok,
                'credentials_loaded': True,
                'error_message': None if connection_ok else connection_msg
            }
            
        except Exception as e:
            return {
                'instagram_available': False,
                'credentials_loaded': False,
                'error_message': f'Error checking Instagram status: {str(e)}'
            }
    
    def logout(self) -> None:
        """Clear Instagram credentials and logout."""
        try:
            self.credentials = {}
            creds_file = os.path.join(const.ROOT_DIR, 'instagram_credentials.json')
            if os.path.exists(creds_file):
                os.remove(creds_file)
            self.logger.info("Instagram logout successful")
        except Exception as e:
            self.logger.error(f"Error during Instagram logout: {e}") 