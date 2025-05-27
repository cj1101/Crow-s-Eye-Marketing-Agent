"""
Google My Business API handler for posting content using the official Google My Business API.
Supports posts, photos, and business updates.
"""
import os
import json
import logging
import requests
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from PySide6.QtCore import QObject, Signal

from ...config import constants as const

class GoogleBusinessAPISignals(QObject):
    """Signals for Google My Business API operations."""
    upload_started = Signal(str)  # platform
    upload_progress = Signal(str, int)  # message, percentage
    upload_success = Signal(str, dict)  # platform, response_data
    upload_error = Signal(str, str)  # platform, error_message
    status_update = Signal(str)

class GoogleBusinessAPIHandler:
    """Handler for Google My Business API operations."""
    
    def __init__(self):
        """Initialize the Google My Business API handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.signals = GoogleBusinessAPISignals()
        self.credentials = {}
        self.base_url = "https://mybusinessbusinessinformation.googleapis.com/v1"
        self.posts_url = "https://mybusiness.googleapis.com/v4"
        
        self._load_credentials()
    
    def _load_credentials(self) -> bool:
        """Load Google My Business credentials from file."""
        try:
            creds_file = os.path.join(const.ROOT_DIR, 'google_business_credentials.json')
            if os.path.exists(creds_file):
                with open(creds_file, 'r', encoding='utf-8') as f:
                    self.credentials = json.load(f)
                return True
            else:
                self.logger.warning("Google My Business credentials file not found")
                return False
        except Exception as e:
            self.logger.error(f"Error loading Google My Business credentials: {e}")
            return False
    
    def save_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Save Google My Business credentials to file."""
        try:
            creds_file = os.path.join(const.ROOT_DIR, 'google_business_credentials.json')
            with open(creds_file, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, indent=4)
            
            self.credentials = credentials
            self.logger.info("Google My Business credentials saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error saving Google My Business credentials: {e}")
            return False
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the Google My Business API connection."""
        try:
            if not self.credentials.get('access_token'):
                return False, "No access token found"
            
            # Test with accounts list endpoint
            url = f"{self.base_url}/accounts"
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}",
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                accounts = data.get('accounts', [])
                if accounts:
                    account_name = accounts[0].get('accountName', 'Unknown')
                    return True, f"Connected to Google My Business: {account_name}"
                else:
                    return False, "No Google My Business accounts found"
            elif response.status_code == 401:
                return False, "Google My Business authentication expired"
            else:
                return False, f"Google My Business API error: HTTP {response.status_code}"
                
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    def post_media(self, media_path: str, caption: str = "", is_video: bool = False) -> Tuple[bool, str]:
        """
        Post media to Google My Business.
        
        Args:
            media_path: Path to the media file
            caption: Caption for the post
            is_video: Whether the media is a video
            
        Returns:
            Tuple of (success, message)
        """
        try:
            self.signals.upload_started.emit("google_business")
            self.signals.status_update.emit("Starting Google My Business upload...")
            
            if not self.credentials.get('access_token'):
                error_msg = "Google My Business not authenticated. Please connect your account first."
                self.signals.upload_error.emit("google_business", error_msg)
                return False, error_msg
            
            if not self.credentials.get('location_name'):
                error_msg = "No Google My Business location selected. Please configure your location."
                self.signals.upload_error.emit("google_business", error_msg)
                return False, error_msg
            
            if not os.path.exists(media_path):
                error_msg = f"Media file not found: {media_path}"
                self.signals.upload_error.emit("google_business", error_msg)
                return False, error_msg
            
            # Validate media file
            valid, validation_msg = self.validate_media_file(media_path)
            if not valid:
                self.signals.upload_error.emit("google_business", validation_msg)
                return False, validation_msg
            
            return self._create_post(media_path, caption, is_video)
                
        except Exception as e:
            error_msg = f"Error posting to Google My Business: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("google_business", error_msg)
            return False, error_msg
    
    def _create_post(self, media_path: str, caption: str, is_video: bool) -> Tuple[bool, str]:
        """Create a post on Google My Business."""
        try:
            access_token = self.credentials['access_token']
            location_name = self.credentials['location_name']
            
            self.signals.upload_progress.emit("Creating Google My Business post...", 25)
            
            headers = {
                'Authorization': f"Bearer {access_token}",
                'Content-Type': 'application/json'
            }
            
            # Step 1: Upload media if provided
            media_data = None
            if media_path:
                self.signals.upload_progress.emit("Uploading media to Google My Business...", 50)
                media_upload_result = self._upload_media(media_path, is_video, headers)
                if not media_upload_result[0]:
                    return media_upload_result
                media_data = media_upload_result[1]
            
            self.signals.upload_progress.emit("Publishing Google My Business post...", 75)
            
            # Step 2: Create the post
            post_url = f"{self.posts_url}/{location_name}/localPosts"
            
            post_data = {
                'languageCode': 'en-US',
                'summary': caption[:1500] if caption else "Posted via Breadsmith Marketing Tool",
                'callToAction': {
                    'actionType': 'LEARN_MORE'
                }
            }
            
            # Add media if uploaded
            if media_data:
                if is_video:
                    post_data['media'] = [{
                        'mediaFormat': 'VIDEO',
                        'sourceUrl': media_data['url']
                    }]
                else:
                    post_data['media'] = [{
                        'mediaFormat': 'PHOTO',
                        'sourceUrl': media_data['url']
                    }]
            
            response = requests.post(post_url, headers=headers, json=post_data, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json()
                post_name = result.get('name', 'Unknown')
                
                self.signals.upload_progress.emit("Google My Business post published successfully!", 100)
                self.signals.upload_success.emit("google_business", {
                    'post_name': post_name,
                    'platform': 'google_business'
                })
                
                return True, f"Successfully posted to Google My Business (Post: {post_name})"
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                self.signals.upload_error.emit("google_business", error_msg)
                return False, f"Failed to create Google My Business post: {error_msg}"
                
        except Exception as e:
            error_msg = f"Error creating Google My Business post: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("google_business", error_msg)
            return False, error_msg
    
    def _upload_media(self, media_path: str, is_video: bool, headers: Dict[str, str]) -> Tuple[bool, Dict[str, Any]]:
        """Upload media to Google My Business."""
        try:
            location_name = self.credentials['location_name']
            
            # Upload media to Google My Business Media API
            media_url = f"{self.posts_url}/{location_name}/media"
            
            with open(media_path, 'rb') as media_file:
                files = {
                    'media': media_file
                }
                
                # Remove Content-Type from headers for multipart upload
                upload_headers = {k: v for k, v in headers.items() if k != 'Content-Type'}
                
                response = requests.post(media_url, headers=upload_headers, files=files, timeout=120)
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    return True, {
                        'url': result.get('googleUrl', ''),
                        'name': result.get('name', '')
                    }
                else:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get('error', {}).get('message', 'Media upload failed')
                    return False, error_msg
                    
        except Exception as e:
            return False, f"Error uploading media: {str(e)}"
    
    def validate_media_file(self, media_path: str) -> Tuple[bool, str]:
        """Validate media file for Google My Business posting."""
        try:
            if not os.path.exists(media_path):
                return False, "Media file does not exist"
            
            file_size = os.path.getsize(media_path)
            file_ext = os.path.splitext(media_path)[1].lower()
            
            # Check file type
            image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            video_formats = ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.webm']
            
            if file_ext in image_formats:
                # Image validation (max 10MB)
                if file_size > 10 * 1024 * 1024:
                    return False, "Image file too large (max 10MB)"
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
    
    def get_locations(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """Get list of Google My Business locations."""
        try:
            if not self.credentials.get('access_token'):
                return False, []
            
            # Get accounts first
            accounts_url = f"{self.base_url}/accounts"
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}",
                'Content-Type': 'application/json'
            }
            
            accounts_response = requests.get(accounts_url, headers=headers, timeout=10)
            
            if accounts_response.status_code != 200:
                return False, []
            
            accounts_data = accounts_response.json()
            accounts = accounts_data.get('accounts', [])
            
            if not accounts:
                return False, []
            
            # Get locations for the first account
            account_name = accounts[0].get('name')
            locations_url = f"{self.base_url}/{account_name}/locations"
            
            locations_response = requests.get(locations_url, headers=headers, timeout=10)
            
            if locations_response.status_code == 200:
                locations_data = locations_response.json()
                locations = locations_data.get('locations', [])
                return True, locations
            else:
                return False, []
                
        except Exception as e:
            self.logger.error(f"Error getting Google My Business locations: {e}")
            return False, []
    
    def get_posting_status(self) -> Dict[str, Any]:
        """Get Google My Business posting status and availability."""
        try:
            has_credentials = bool(self.credentials.get('access_token'))
            has_location = bool(self.credentials.get('location_name'))
            
            if not has_credentials:
                return {
                    'google_business_available': False,
                    'credentials_loaded': False,
                    'error_message': 'Google My Business credentials not configured'
                }
            
            if not has_location:
                return {
                    'google_business_available': False,
                    'credentials_loaded': True,
                    'error_message': 'No Google My Business location selected'
                }
            
            # Test connection
            connection_ok, connection_msg = self.test_connection()
            
            return {
                'google_business_available': connection_ok,
                'credentials_loaded': True,
                'error_message': None if connection_ok else connection_msg
            }
            
        except Exception as e:
            return {
                'google_business_available': False,
                'credentials_loaded': False,
                'error_message': f'Error checking Google My Business status: {str(e)}'
            }
    
    def logout(self) -> None:
        """Clear Google My Business credentials and logout."""
        try:
            self.credentials = {}
            creds_file = os.path.join(const.ROOT_DIR, 'google_business_credentials.json')
            if os.path.exists(creds_file):
                os.remove(creds_file)
            self.logger.info("Google My Business logout successful")
        except Exception as e:
            self.logger.error(f"Error during Google My Business logout: {e}") 