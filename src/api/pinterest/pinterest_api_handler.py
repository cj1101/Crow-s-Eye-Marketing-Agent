"""
Pinterest API handler for posting content using the official Pinterest API v5.
Supports pin creation with images and boards management.
"""
import os
import json
import logging
import requests
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from PySide6.QtCore import QObject, Signal

from ...config import constants as const

class PinterestAPISignals(QObject):
    """Signals for Pinterest API operations."""
    upload_started = Signal(str)  # platform
    upload_progress = Signal(str, int)  # message, percentage
    upload_success = Signal(str, dict)  # platform, response_data
    upload_error = Signal(str, str)  # platform, error_message
    status_update = Signal(str)

class PinterestAPIHandler:
    """Handler for Pinterest API operations."""
    
    def __init__(self):
        """Initialize the Pinterest API handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.signals = PinterestAPISignals()
        self.credentials = {}
        self.base_url = "https://api.pinterest.com/v5"
        
        self._load_credentials()
    
    def _load_credentials(self) -> bool:
        """Load Pinterest credentials from file."""
        try:
            creds_file = os.path.join(const.ROOT_DIR, 'pinterest_credentials.json')
            if os.path.exists(creds_file):
                with open(creds_file, 'r', encoding='utf-8') as f:
                    self.credentials = json.load(f)
                return True
            else:
                self.logger.warning("Pinterest credentials file not found")
                return False
        except Exception as e:
            self.logger.error(f"Error loading Pinterest credentials: {e}")
            return False
    
    def save_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Save Pinterest credentials to file."""
        try:
            creds_file = os.path.join(const.ROOT_DIR, 'pinterest_credentials.json')
            with open(creds_file, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, indent=4)
            
            self.credentials = credentials
            self.logger.info("Pinterest credentials saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error saving Pinterest credentials: {e}")
            return False
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the Pinterest API connection."""
        try:
            if not self.credentials.get('access_token'):
                return False, "No access token found"
            
            # Test with user info endpoint
            url = f"{self.base_url}/user_account"
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}",
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                username = data.get('username', 'Unknown')
                return True, f"Connected to Pinterest account: @{username}"
            elif response.status_code == 401:
                return False, "Pinterest authentication expired"
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('message', 'Unknown error')
                return False, f"Pinterest API error: {error_msg}"
                
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    def post_media(self, media_path: str, caption: str = "", is_video: bool = False) -> Tuple[bool, str]:
        """
        Post media to Pinterest.
        
        Args:
            media_path: Path to the media file
            caption: Caption for the pin
            is_video: Whether the media is a video (Pinterest supports videos)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            self.signals.upload_started.emit("pinterest")
            self.signals.status_update.emit("Starting Pinterest upload...")
            
            if not self.credentials.get('access_token'):
                error_msg = "Pinterest not authenticated. Please connect your account first."
                self.signals.upload_error.emit("pinterest", error_msg)
                return False, error_msg
            
            if not os.path.exists(media_path):
                error_msg = f"Media file not found: {media_path}"
                self.signals.upload_error.emit("pinterest", error_msg)
                return False, error_msg
            
            # Validate media file
            valid, validation_msg = self.validate_media_file(media_path)
            if not valid:
                self.signals.upload_error.emit("pinterest", validation_msg)
                return False, validation_msg
            
            return self._create_pin(media_path, caption, is_video)
                
        except Exception as e:
            error_msg = f"Error posting to Pinterest: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("pinterest", error_msg)
            return False, error_msg
    
    def _create_pin(self, media_path: str, caption: str, is_video: bool) -> Tuple[bool, str]:
        """Create a pin on Pinterest."""
        try:
            access_token = self.credentials['access_token']
            
            self.signals.upload_progress.emit("Creating Pinterest pin...", 25)
            
            headers = {
                'Authorization': f"Bearer {access_token}",
                'Content-Type': 'application/json'
            }
            
            # Get or create a board to pin to
            board_id = self.credentials.get('default_board_id')
            if not board_id:
                # Get the first available board
                boards_result = self._get_boards()
                if not boards_result[0] or not boards_result[1]:
                    return False, "No Pinterest boards found. Please create a board first."
                board_id = boards_result[1][0]['id']
                
                # Save the board ID for future use
                self.credentials['default_board_id'] = board_id
                self.save_credentials(self.credentials)
            
            self.signals.upload_progress.emit("Uploading media to Pinterest...", 50)
            
            # Upload media and create pin
            pin_url = f"{self.base_url}/pins"
            
            # Prepare pin data
            pin_data = {
                'board_id': board_id,
                'title': caption[:100] if caption else "Posted via Breadsmith Marketing Tool",
                'description': caption[:500] if caption else "Posted via Breadsmith Marketing Tool",
                'link': self.credentials.get('website_url', ''),
                'alt_text': caption[:500] if caption else "Image posted via Breadsmith Marketing Tool"
            }
            
            # Upload media file
            with open(media_path, 'rb') as media_file:
                files = {
                    'media': media_file
                }
                
                # Remove Content-Type from headers for multipart upload
                upload_headers = {k: v for k, v in headers.items() if k != 'Content-Type'}
                
                self.signals.upload_progress.emit("Publishing Pinterest pin...", 75)
                
                response = requests.post(pin_url, headers=upload_headers, data=pin_data, files=files, timeout=120)
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    pin_id = result.get('id', 'Unknown')
                    pin_url = result.get('url', '')
                    
                    self.signals.upload_progress.emit("Pinterest pin published successfully!", 100)
                    self.signals.upload_success.emit("pinterest", {
                        'pin_id': pin_id,
                        'pin_url': pin_url,
                        'platform': 'pinterest'
                    })
                    
                    return True, f"Successfully posted to Pinterest (Pin ID: {pin_id})"
                else:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get('message', 'Unknown error')
                    self.signals.upload_error.emit("pinterest", error_msg)
                    return False, f"Failed to create Pinterest pin: {error_msg}"
                
        except Exception as e:
            error_msg = f"Error creating Pinterest pin: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("pinterest", error_msg)
            return False, error_msg
    
    def _get_boards(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """Get user's Pinterest boards."""
        try:
            boards_url = f"{self.base_url}/boards"
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}",
                'Content-Type': 'application/json'
            }
            
            response = requests.get(boards_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                boards = data.get('items', [])
                return True, boards
            else:
                return False, []
                
        except Exception as e:
            self.logger.error(f"Error getting Pinterest boards: {e}")
            return False, []
    
    def create_board(self, name: str, description: str = "") -> Tuple[bool, str]:
        """Create a new Pinterest board."""
        try:
            boards_url = f"{self.base_url}/boards"
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}",
                'Content-Type': 'application/json'
            }
            
            board_data = {
                'name': name,
                'description': description or f"Board created via Breadsmith Marketing Tool",
                'privacy': 'PUBLIC'
            }
            
            response = requests.post(boards_url, headers=headers, json=board_data, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json()
                board_id = result.get('id')
                return True, board_id
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('message', 'Board creation failed')
                return False, error_msg
                
        except Exception as e:
            return False, f"Error creating board: {str(e)}"
    
    def validate_media_file(self, media_path: str) -> Tuple[bool, str]:
        """Validate media file for Pinterest posting."""
        try:
            if not os.path.exists(media_path):
                return False, "Media file does not exist"
            
            file_size = os.path.getsize(media_path)
            file_ext = os.path.splitext(media_path)[1].lower()
            
            # Check file type
            image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            video_formats = ['.mp4', '.mov', '.m4v']
            
            if file_ext in image_formats:
                # Image validation (max 32MB)
                if file_size > 32 * 1024 * 1024:
                    return False, "Image file too large (max 32MB)"
                return True, "Valid image file"
                
            elif file_ext in video_formats:
                # Video validation (max 2GB)
                if file_size > 2 * 1024 * 1024 * 1024:
                    return False, "Video file too large (max 2GB)"
                return True, "Valid video file"
            else:
                return False, f"Unsupported file format: {file_ext}"
                
        except Exception as e:
            return False, f"Error validating media file: {str(e)}"
    
    def get_posting_status(self) -> Dict[str, Any]:
        """Get Pinterest posting status and availability."""
        try:
            has_credentials = bool(self.credentials.get('access_token'))
            
            if not has_credentials:
                return {
                    'pinterest_available': False,
                    'credentials_loaded': False,
                    'error_message': 'Pinterest credentials not configured'
                }
            
            # Test connection
            connection_ok, connection_msg = self.test_connection()
            
            return {
                'pinterest_available': connection_ok,
                'credentials_loaded': True,
                'error_message': None if connection_ok else connection_msg
            }
            
        except Exception as e:
            return {
                'pinterest_available': False,
                'credentials_loaded': False,
                'error_message': f'Error checking Pinterest status: {str(e)}'
            }
    
    def logout(self) -> None:
        """Clear Pinterest credentials and logout."""
        try:
            self.credentials = {}
            creds_file = os.path.join(const.ROOT_DIR, 'pinterest_credentials.json')
            if os.path.exists(creds_file):
                os.remove(creds_file)
            self.logger.info("Pinterest logout successful")
        except Exception as e:
            self.logger.error(f"Error during Pinterest logout: {e}") 