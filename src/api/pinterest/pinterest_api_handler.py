"""
Pinterest API handler for posting content using the official Pinterest API v5.
Supports pin creation with images, carousel pins, and comprehensive board management.
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
        self.base_url = "https://api.pinterest.com/v5"
        self.credentials_file = os.path.join(const.ROOT_DIR, 'pinterest_credentials.json')
        self.credentials = self.load_credentials()
    
    def load_credentials(self) -> Dict[str, Any]:
        """Load Pinterest credentials from file."""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    credentials = json.load(f)
                    self.logger.info("Pinterest credentials loaded successfully")
                    return credentials
        except Exception as e:
            self.logger.warning(f"Pinterest credentials file not found")
        return {}
    
    def save_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Save Pinterest credentials to file."""
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            self.logger.info("Pinterest credentials saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save Pinterest credentials: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if Pinterest is authenticated."""
        return bool(self.credentials.get('access_token'))
    
    def post_media(self, media_paths: List[str] = None, media_path: str = "", caption: str = "", 
                   is_video: bool = False, board_id: str = None, **kwargs) -> Tuple[bool, str]:
        """
        Post media to Pinterest.
        
        Args:
            media_paths: List of media file paths (for carousel pins, up to 5 images)
            media_path: Single media file path (for backwards compatibility)
            caption: Caption for the pin (title and description)
            is_video: Whether the media is a video (Pinterest supports videos)
            board_id: Specific board ID to pin to (optional)
            **kwargs: Additional parameters like board_name, link, alt_text, etc.
            
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
            
            # Handle both single file and multiple files
            if media_paths and len(media_paths) > 1:
                # Carousel pin mode (Pinterest ads feature)
                return self._create_carousel_pin(media_paths, caption, board_id, **kwargs)
            else:
                # Single pin mode
                single_path = media_paths[0] if media_paths else media_path
                
                if not os.path.exists(single_path):
                    error_msg = f"Media file not found: {single_path}"
                    self.signals.upload_error.emit("pinterest", error_msg)
                    return False, error_msg
                
                # Validate media file
                valid, validation_msg = self.validate_media_file(single_path)
                if not valid:
                    self.signals.upload_error.emit("pinterest", validation_msg)
                    return False, validation_msg
                
                return self._create_pin(single_path, caption, is_video, board_id, **kwargs)
                
        except Exception as e:
            error_msg = f"Error posting to Pinterest: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("pinterest", error_msg)
            return False, error_msg
    
    def _create_carousel_pin(self, media_paths: List[str], caption: str, board_id: str = None, **kwargs) -> Tuple[bool, str]:
        """Create a carousel pin on Pinterest (for ads and business accounts)."""
        try:
            if len(media_paths) > 5:
                return False, "Pinterest carousel pins support maximum 5 images"
            
            if len(media_paths) < 2:
                return False, "At least 2 images are required for Pinterest carousel pins"
            
            self.signals.upload_progress.emit("Validating carousel images...", 10)
            
            # Validate all images
            for media_path in media_paths:
                if not os.path.exists(media_path):
                    return False, f"Image file not found: {media_path}"
                
                valid, validation_msg = self.validate_media_file(media_path)
                if not valid:
                    return False, f"Invalid image {media_path}: {validation_msg}"
            
            # Get or create board
            if not board_id:
                board_id = self._get_or_create_board(kwargs.get('board_name', 'Carousel Pins'))
                if not board_id:
                    return False, "Failed to get or create Pinterest board for carousel"
            
            self.signals.upload_progress.emit("Creating Pinterest carousel pin...", 25)
            
            access_token = self.credentials['access_token']
            headers = {
                'Authorization': f"Bearer {access_token}",
                'Content-Type': 'application/json'
            }
            
            # For now, create individual pins in sequence as Pinterest organic carousel support is limited
            # This creates a "gallery effect" by posting to the same board
            created_pins = []
            progress_step = 60 // len(media_paths)  # Progress from 25% to 85%
            current_progress = 25
            
            for i, media_path in enumerate(media_paths):
                self.signals.upload_progress.emit(f"Creating pin {i+1}/{len(media_paths)}...", current_progress)
                
                # Create individual pin with carousel indication
                pin_title = f"{caption[:90]} (Part {i+1}/{len(media_paths)})" if caption else f"Gallery Image {i+1}/{len(media_paths)}"
                pin_description = f"{caption[:450]}... 📌 Part {i+1} of {len(media_paths)} - See full gallery on my board!" if caption else f"Gallery image {i+1} of {len(media_paths)}"
                
                success, result = self._create_pin(
                    media_path, 
                    pin_title,
                    False,  # Not video for carousel
                    board_id,
                    description=pin_description,
                    **kwargs
                )
                
                if success:
                    created_pins.append(result)
                else:
                    # If one fails, note it but continue with others
                    self.logger.warning(f"Failed to create pin {i+1}: {result}")
                
                current_progress += progress_step
            
            if created_pins:
                self.signals.upload_progress.emit("Pinterest gallery created successfully!", 100)
                self.signals.upload_success.emit("pinterest", {
                    'pins': created_pins,
                    'platform': 'pinterest',
                    'type': 'gallery',
                    'pin_count': len(created_pins),
                    'board_id': board_id
                })
                
                return True, f"Successfully created Pinterest gallery with {len(created_pins)} pins"
            else:
                return False, "Failed to create any pins in the gallery"
                
        except Exception as e:
            error_msg = f"Error creating Pinterest carousel: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("pinterest", error_msg)
            return False, error_msg
    
    def _create_pin(self, media_path: str, caption: str, is_video: bool, board_id: str = None, **kwargs) -> Tuple[bool, str]:
        """Create a single pin on Pinterest."""
        try:
            access_token = self.credentials['access_token']
            
            self.signals.upload_progress.emit("Creating Pinterest pin...", 25)
            
            headers = {
                'Authorization': f"Bearer {access_token}",
                'Content-Type': 'application/json'
            }
            
            # Get or create a board to pin to
            if not board_id:
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
            
            # Prepare pin data with enhanced metadata
            title = caption[:100] if caption else "Posted via Crow's Eye Marketing Tool"
            description = kwargs.get('description', caption[:500] if caption else "Posted via Crow's Eye Marketing Tool")
            
            # Add Pinterest-optimized call-to-action if not present
            if not any(cta in description.lower() for cta in ["save", "pin", "shop", "click", "visit"]):
                description += " 📌 Save for later!"
            
            pin_data = {
                'board_id': board_id,
                'title': title,
                'description': description,
                'link': kwargs.get('link', self.credentials.get('website_url', '')),
                'alt_text': kwargs.get('alt_text', caption[:500] if caption else "Image posted via Crow's Eye Marketing Tool")
            }
            
            # Add video-specific data if applicable
            if is_video:
                pin_data['media_source'] = {
                    'source_type': 'video',
                    'content_type': 'video/mp4'
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
                    error_msg = error_data.get('message', f'HTTP {response.status_code}')
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
            access_token = self.credentials['access_token']
            headers = {
                'Authorization': f"Bearer {access_token}"
            }
            
            boards_url = f"{self.base_url}/boards"
            response = requests.get(boards_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                boards = result.get('items', [])
                return True, boards
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('message', 'Failed to get boards')
                self.logger.error(f"Failed to get Pinterest boards: {error_msg}")
                return False, []
                
        except Exception as e:
            self.logger.exception(f"Error getting Pinterest boards: {e}")
            return False, []
    
    def _get_or_create_board(self, board_name: str = "My Gallery") -> Optional[str]:
        """Get existing board or create a new one for gallery posts."""
        try:
            # First, try to get existing boards
            success, boards = self._get_boards()
            if success:
                # Look for existing board with similar name
                for board in boards:
                    if board_name.lower() in board.get('name', '').lower():
                        return board.get('id')
            
            # Create new board if not found
            return self._create_board(board_name, f"Gallery created via Crow's Eye Marketing Tool")
            
        except Exception as e:
            self.logger.exception(f"Error getting or creating board: {e}")
            return None
    
    def _create_board(self, name: str, description: str = "") -> Optional[str]:
        """Create a new Pinterest board."""
        try:
            access_token = self.credentials['access_token']
            headers = {
                'Authorization': f"Bearer {access_token}",
                'Content-Type': 'application/json'
            }
            
            board_data = {
                'name': name,
                'description': description or f"Board created via Crow's Eye Marketing Tool",
                'privacy': 'PUBLIC'
            }
            
            boards_url = f"{self.base_url}/boards"
            response = requests.post(boards_url, headers=headers, json=board_data, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json()
                board_id = result.get('id')
                self.logger.info(f"Created Pinterest board '{name}' with ID: {board_id}")
                return board_id
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('message', 'Failed to create board')
                self.logger.error(f"Failed to create Pinterest board: {error_msg}")
                return None
                
        except Exception as e:
            self.logger.exception(f"Error creating Pinterest board: {e}")
            return None
    
    def create_board_gallery(self, media_paths: List[str], board_name: str, board_description: str = "", **kwargs) -> Tuple[bool, str]:
        """Create a dedicated board with a gallery of images."""
        try:
            if len(media_paths) < 2:
                return False, "At least 2 images are required for a gallery board"
            
            self.signals.upload_progress.emit("Creating Pinterest gallery board...", 10)
            
            # Create dedicated board for this gallery
            board_id = self._create_board(board_name, board_description)
            if not board_id:
                return False, "Failed to create Pinterest board for gallery"
            
            # Add all images to the board
            return self._create_carousel_pin(media_paths, board_description, board_id, **kwargs)
            
        except Exception as e:
            error_msg = f"Error creating Pinterest board gallery: {str(e)}"
            self.logger.exception(error_msg)
            return False, error_msg
    
    def validate_media_file(self, media_path: str) -> Tuple[bool, str]:
        """Validate media file for Pinterest posting."""
        try:
            if not os.path.exists(media_path):
                return False, "Media file does not exist"
            
            file_size = os.path.getsize(media_path)
            file_ext = os.path.splitext(media_path)[1].lower()
            
            # Check file type
            image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            video_formats = ['.mp4', '.mov', '.m4v', '.webm']
            
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
                return False, f"Unsupported file format: {file_ext}. Supported: {image_formats + video_formats}"
                
        except Exception as e:
            return False, f"Error validating media file: {str(e)}"
    
    def get_posting_status(self) -> Dict[str, Any]:
        """Get current posting status and capabilities."""
        return {
            'platform': 'pinterest',
            'authenticated': self.is_authenticated(),
            'supports_image': True,
            'supports_video': True,
            'supports_gallery': True,
            'supports_carousel': True,
            'supports_boards': True,
            'max_carousel_images': 5,
            'max_image_size_mb': 32,
            'max_video_size_gb': 2,
            'max_title_length': 100,
            'max_description_length': 500,
            'supported_image_formats': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
            'supported_video_formats': ['.mp4', '.mov', '.m4v', '.webm']
        }
    
    def logout(self) -> None:
        """Logout from Pinterest (clear credentials)."""
        try:
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
            self.credentials = {}
            self.logger.info("Pinterest logout successful")
        except Exception as e:
            self.logger.error(f"Error during Pinterest logout: {e}") 