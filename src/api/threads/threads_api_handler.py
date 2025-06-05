"""
Threads API handler for posting content using the official Threads API.
Threads API is part of Meta's Graph API ecosystem.
"""
import os
import json
import logging
import requests
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from PySide6.QtCore import QObject, Signal

from ...config import constants as const

class ThreadsAPISignals(QObject):
    """Signals for Threads API operations."""
    upload_started = Signal(str)  # platform
    upload_progress = Signal(str, int)  # message, percentage
    upload_success = Signal(str, dict)  # platform, response_data
    upload_error = Signal(str, str)  # platform, error_message
    status_update = Signal(str)

class ThreadsAPIHandler:
    """Handler for Threads API operations."""
    
    def __init__(self):
        """Initialize the Threads API handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.signals = ThreadsAPISignals()
        self.credentials = {}
        self.base_url = "https://graph.threads.net/v1.0"
        
        self._load_credentials()
    
    def _load_credentials(self) -> bool:
        """Load Threads credentials from file."""
        try:
            creds_file = os.path.join(const.ROOT_DIR, 'threads_credentials.json')
            if os.path.exists(creds_file):
                with open(creds_file, 'r', encoding='utf-8') as f:
                    self.credentials = json.load(f)
                return True
            else:
                self.logger.warning("Threads credentials file not found")
                return False
        except Exception as e:
            self.logger.error(f"Error loading Threads credentials: {e}")
            return False
    
    def save_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Save Threads credentials to file."""
        try:
            creds_file = os.path.join(const.ROOT_DIR, 'threads_credentials.json')
            with open(creds_file, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, indent=4)
            
            self.credentials = credentials
            self.logger.info("Threads credentials saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error saving Threads credentials: {e}")
            return False
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the Threads API connection."""
        try:
            if not self.credentials.get('access_token'):
                return False, "No access token found"
            
            if not self.credentials.get('threads_user_id'):
                return False, "No Threads user ID found"
            
            # Test with user info endpoint
            user_id = self.credentials['threads_user_id']
            url = f"{self.base_url}/{user_id}"
            params = {
                'fields': 'id,username,name',
                'access_token': self.credentials['access_token']
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                username = data.get('username', 'Unknown')
                return True, f"Connected to Threads account: @{username}"
            elif response.status_code == 401:
                return False, "Threads authentication expired"
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                return False, f"Threads API error: {error_msg}"
                
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    def post_media(self, media_path: str, caption: str = "", is_video: bool = False) -> Tuple[bool, str]:
        """
        Post media to Threads.
        
        Args:
            media_path: Path to the media file
            caption: Caption for the post
            is_video: Whether the media is a video
            
        Returns:
            Tuple of (success, message)
        """
        try:
            self.signals.upload_started.emit("threads")
            self.signals.status_update.emit("Starting Threads upload...")
            
            if not self.credentials.get('access_token'):
                error_msg = "Threads not authenticated. Please connect your account first."
                self.signals.upload_error.emit("threads", error_msg)
                return False, error_msg
            
            if not self.credentials.get('threads_user_id'):
                error_msg = "No Threads user ID found. Please reconnect your account."
                self.signals.upload_error.emit("threads", error_msg)
                return False, error_msg
            
            if media_path and not os.path.exists(media_path):
                error_msg = f"Media file not found: {media_path}"
                self.signals.upload_error.emit("threads", error_msg)
                return False, error_msg
            
            # Validate media file if provided
            if media_path:
                valid, validation_msg = self.validate_media_file(media_path)
                if not valid:
                    self.signals.upload_error.emit("threads", validation_msg)
                    return False, validation_msg
            
            return self._create_thread(media_path, caption, is_video)
                
        except Exception as e:
            error_msg = f"Error posting to Threads: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("threads", error_msg)
            return False, error_msg
    
    def _create_thread(self, media_path: str, caption: str, is_video: bool) -> Tuple[bool, str]:
        """Create a thread on Threads."""
        try:
            user_id = self.credentials['threads_user_id']
            access_token = self.credentials['access_token']
            
            self.signals.upload_progress.emit("Creating Threads post...", 25)
            
            # Step 1: Create media container
            container_url = f"{self.base_url}/{user_id}/threads"
            container_data = {
                'access_token': access_token
            }
            
            # Add text content
            if caption:
                container_data['text'] = caption[:500]  # Threads has a 500 character limit
            
            # Add media if provided
            if media_path:
                self.signals.upload_progress.emit("Uploading media to Threads...", 50)
                
                # For Threads, we need to upload media to a hosting service first
                # This is a simplified approach - in production you'd use a proper media hosting service
                if is_video:
                    container_data['media_type'] = 'VIDEO'
                    container_data['video_url'] = media_path  # This should be a public URL
                else:
                    container_data['media_type'] = 'IMAGE'
                    container_data['image_url'] = media_path  # This should be a public URL
            
            response = requests.post(container_url, data=container_data, timeout=30)
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Container creation failed')
                return False, f"Failed to create Threads container: {error_msg}"
            
            result = response.json()
            container_id = result.get('id')
            
            if not container_id:
                return False, "Failed to get container ID from Threads"
            
            self.signals.upload_progress.emit("Publishing Threads post...", 75)
            
            # Step 2: Publish the thread
            publish_url = f"{self.base_url}/{user_id}/threads_publish"
            publish_data = {
                'creation_id': container_id,
                'access_token': access_token
            }
            
            publish_response = requests.post(publish_url, data=publish_data, timeout=30)
            
            if publish_response.status_code == 200:
                publish_result = publish_response.json()
                thread_id = publish_result.get('id', 'Unknown')
                
                self.signals.upload_progress.emit("Threads post published successfully!", 100)
                self.signals.upload_success.emit("threads", {
                    'thread_id': thread_id,
                    'platform': 'threads'
                })
                
                return True, f"Successfully posted to Threads (Thread ID: {thread_id})"
            else:
                error_data = publish_response.json() if publish_response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown publish error')
                self.signals.upload_error.emit("threads", error_msg)
                return False, f"Failed to publish Threads post: {error_msg}"
                
        except Exception as e:
            error_msg = f"Error creating Threads post: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("threads", error_msg)
            return False, error_msg
    
    def validate_media_file(self, media_path: str) -> Tuple[bool, str]:
        """Validate media file for Threads posting."""
        try:
            if not os.path.exists(media_path):
                return False, "Media file does not exist"
            
            file_size = os.path.getsize(media_path)
            file_ext = os.path.splitext(media_path)[1].lower()
            
            # Check file type
            image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            video_formats = ['.mp4', '.mov', '.avi']
            
            if file_ext in image_formats:
                # Image validation (max 8MB)
                if file_size > 8 * 1024 * 1024:
                    return False, "Image file too large (max 8MB)"
                return True, "Valid image file"
                
            elif file_ext in video_formats:
                # Video validation (max 100MB)
                if file_size > 100 * 1024 * 1024:
                    return False, "Video file too large (max 100MB)"
                return True, "Valid video file"
            else:
                return False, f"Unsupported file format: {file_ext}"
                
        except Exception as e:
            return False, f"Error validating media file: {str(e)}"
    
    def get_posting_status(self) -> Dict[str, Any]:
        """Get Threads posting status and availability."""
        try:
            has_credentials = bool(self.credentials.get('access_token'))
            has_user_id = bool(self.credentials.get('threads_user_id'))
            
            if not has_credentials:
                return {
                    'threads_available': False,
                    'credentials_loaded': False,
                    'error_message': 'Threads credentials not configured'
                }
            
            if not has_user_id:
                return {
                    'threads_available': False,
                    'credentials_loaded': True,
                    'error_message': 'Threads user ID not found'
                }
            
            # Test connection
            connection_ok, connection_msg = self.test_connection()
            
            return {
                'threads_available': connection_ok,
                'credentials_loaded': True,
                'error_message': None if connection_ok else connection_msg
            }
            
        except Exception as e:
            return {
                'threads_available': False,
                'credentials_loaded': False,
                'error_message': f'Error checking Threads status: {str(e)}'
            }
    
    def logout(self) -> None:
        """Clear Threads credentials and logout."""
        try:
            self.credentials = {}
            creds_file = os.path.join(const.ROOT_DIR, 'threads_credentials.json')
            if os.path.exists(creds_file):
                os.remove(creds_file)
            self.logger.info("Threads logout successful")
        except Exception as e:
            self.logger.error(f"Error during Threads logout: {e}") 