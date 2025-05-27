"""
BlueSky API handler for posting content using the official AT Protocol API.
Supports text posts, images, and links.
"""
import os
import json
import logging
import requests
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from PySide6.QtCore import QObject, Signal

from ...config import constants as const

class BlueSkyAPISignals(QObject):
    """Signals for BlueSky API operations."""
    upload_started = Signal(str)  # platform
    upload_progress = Signal(str, int)  # message, percentage
    upload_success = Signal(str, dict)  # platform, response_data
    upload_error = Signal(str, str)  # platform, error_message
    status_update = Signal(str)

class BlueSkyAPIHandler:
    """Handler for BlueSky API operations."""
    
    def __init__(self):
        """Initialize the BlueSky API handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.signals = BlueSkyAPISignals()
        self.credentials = {}
        self.base_url = "https://bsky.social"
        self.session_token = None
        
        self._load_credentials()
    
    def _load_credentials(self) -> bool:
        """Load BlueSky credentials from file."""
        try:
            creds_file = os.path.join(const.ROOT_DIR, 'bluesky_credentials.json')
            if os.path.exists(creds_file):
                with open(creds_file, 'r', encoding='utf-8') as f:
                    self.credentials = json.load(f)
                return True
            else:
                self.logger.warning("BlueSky credentials file not found")
                return False
        except Exception as e:
            self.logger.error(f"Error loading BlueSky credentials: {e}")
            return False
    
    def save_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Save BlueSky credentials to file."""
        try:
            creds_file = os.path.join(const.ROOT_DIR, 'bluesky_credentials.json')
            with open(creds_file, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, indent=4)
            
            self.credentials = credentials
            self.logger.info("BlueSky credentials saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error saving BlueSky credentials: {e}")
            return False
    
    def authenticate(self) -> Tuple[bool, str]:
        """Authenticate with BlueSky using username and password."""
        try:
            if not self.credentials.get('username') or not self.credentials.get('password'):
                return False, "Username and password required"
            
            auth_url = f"{self.base_url}/xrpc/com.atproto.server.createSession"
            auth_data = {
                'identifier': self.credentials['username'],
                'password': self.credentials['password']
            }
            
            response = requests.post(auth_url, json=auth_data, timeout=10)
            
            if response.status_code == 200:
                session_data = response.json()
                self.session_token = session_data.get('accessJwt')
                self.credentials['did'] = session_data.get('did')
                self.credentials['handle'] = session_data.get('handle')
                
                # Save updated credentials
                self.save_credentials(self.credentials)
                
                return True, f"Authenticated as @{session_data.get('handle', 'unknown')}"
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('message', 'Authentication failed')
                return False, f"BlueSky authentication failed: {error_msg}"
                
        except Exception as e:
            return False, f"Authentication error: {str(e)}"
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the BlueSky API connection."""
        try:
            if not self.session_token:
                # Try to authenticate first
                auth_result = self.authenticate()
                if not auth_result[0]:
                    return auth_result
            
            # Test with profile endpoint
            profile_url = f"{self.base_url}/xrpc/com.atproto.repo.getRecord"
            headers = {
                'Authorization': f"Bearer {self.session_token}",
                'Content-Type': 'application/json'
            }
            params = {
                'repo': self.credentials.get('did', ''),
                'collection': 'app.bsky.actor.profile',
                'rkey': 'self'
            }
            
            response = requests.get(profile_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                handle = self.credentials.get('handle', 'Unknown')
                return True, f"Connected to BlueSky account: @{handle}"
            else:
                return False, "BlueSky connection test failed"
                
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    def post_media(self, media_path: str, caption: str = "", is_video: bool = False) -> Tuple[bool, str]:
        """
        Post media to BlueSky.
        
        Args:
            media_path: Path to the media file
            caption: Caption for the post
            is_video: Whether the media is a video (BlueSky doesn't support videos yet)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            self.signals.upload_started.emit("bluesky")
            self.signals.status_update.emit("Starting BlueSky upload...")
            
            if not self.session_token:
                # Try to authenticate first
                auth_result = self.authenticate()
                if not auth_result[0]:
                    self.signals.upload_error.emit("bluesky", auth_result[1])
                    return auth_result
            
            if is_video:
                error_msg = "BlueSky does not currently support video uploads."
                self.signals.upload_error.emit("bluesky", error_msg)
                return False, error_msg
            
            if media_path and not os.path.exists(media_path):
                error_msg = f"Media file not found: {media_path}"
                self.signals.upload_error.emit("bluesky", error_msg)
                return False, error_msg
            
            # Validate media file if provided
            if media_path:
                valid, validation_msg = self.validate_media_file(media_path)
                if not valid:
                    self.signals.upload_error.emit("bluesky", validation_msg)
                    return False, validation_msg
            
            return self._create_post(media_path, caption)
                
        except Exception as e:
            error_msg = f"Error posting to BlueSky: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("bluesky", error_msg)
            return False, error_msg
    
    def _create_post(self, media_path: str, caption: str) -> Tuple[bool, str]:
        """Create a post on BlueSky."""
        try:
            self.signals.upload_progress.emit("Creating BlueSky post...", 25)
            
            headers = {
                'Authorization': f"Bearer {self.session_token}",
                'Content-Type': 'application/json'
            }
            
            # Prepare post record
            post_record = {
                '$type': 'app.bsky.feed.post',
                'text': caption[:300] if caption else "Posted via Breadsmith Marketing Tool",
                'createdAt': datetime.now().isoformat() + 'Z'
            }
            
            # Upload image if provided
            if media_path:
                self.signals.upload_progress.emit("Uploading image to BlueSky...", 50)
                
                blob_result = self._upload_blob(media_path, headers)
                if not blob_result[0]:
                    return blob_result
                
                blob_data = blob_result[1]
                
                # Add image embed to post
                post_record['embed'] = {
                    '$type': 'app.bsky.embed.images',
                    'images': [{
                        'alt': caption[:100] if caption else "Image",
                        'image': blob_data
                    }]
                }
            
            self.signals.upload_progress.emit("Publishing BlueSky post...", 75)
            
            # Create the post
            post_url = f"{self.base_url}/xrpc/com.atproto.repo.createRecord"
            post_data = {
                'repo': self.credentials['did'],
                'collection': 'app.bsky.feed.post',
                'record': post_record
            }
            
            response = requests.post(post_url, headers=headers, json=post_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                post_uri = result.get('uri', 'Unknown')
                
                self.signals.upload_progress.emit("BlueSky post published successfully!", 100)
                self.signals.upload_success.emit("bluesky", {
                    'uri': post_uri,
                    'platform': 'bluesky'
                })
                
                return True, f"Successfully posted to BlueSky (URI: {post_uri})"
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('message', 'Unknown error')
                self.signals.upload_error.emit("bluesky", error_msg)
                return False, f"Failed to create BlueSky post: {error_msg}"
                
        except Exception as e:
            error_msg = f"Error creating BlueSky post: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("bluesky", error_msg)
            return False, error_msg
    
    def _upload_blob(self, media_path: str, headers: Dict[str, str]) -> Tuple[bool, Dict[str, Any]]:
        """Upload a blob (image) to BlueSky."""
        try:
            blob_url = f"{self.base_url}/xrpc/com.atproto.repo.uploadBlob"
            
            # Determine content type
            file_ext = os.path.splitext(media_path)[1].lower()
            content_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            content_type = content_type_map.get(file_ext, 'image/jpeg')
            
            with open(media_path, 'rb') as media_file:
                upload_headers = headers.copy()
                upload_headers['Content-Type'] = content_type
                
                response = requests.post(blob_url, headers=upload_headers, data=media_file, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    return True, result.get('blob', {})
                else:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get('message', 'Blob upload failed')
                    return False, error_msg
                    
        except Exception as e:
            return False, f"Error uploading blob: {str(e)}"
    
    def validate_media_file(self, media_path: str) -> Tuple[bool, str]:
        """Validate media file for BlueSky posting."""
        try:
            if not os.path.exists(media_path):
                return False, "Media file does not exist"
            
            file_size = os.path.getsize(media_path)
            file_ext = os.path.splitext(media_path)[1].lower()
            
            # BlueSky only supports images
            image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            
            if file_ext not in image_formats:
                return False, f"BlueSky only supports image files. Unsupported format: {file_ext}"
            
            # Check file size (max 1MB)
            if file_size > 1 * 1024 * 1024:
                return False, "Image file too large (max 1MB for BlueSky)"
            
            return True, "Valid image file for BlueSky"
                
        except Exception as e:
            return False, f"Error validating media file: {str(e)}"
    
    def get_posting_status(self) -> Dict[str, Any]:
        """Get BlueSky posting status and availability."""
        try:
            has_credentials = bool(self.credentials.get('username') and self.credentials.get('password'))
            
            if not has_credentials:
                return {
                    'bluesky_available': False,
                    'credentials_loaded': False,
                    'error_message': 'BlueSky credentials not configured'
                }
            
            # Test connection
            connection_ok, connection_msg = self.test_connection()
            
            return {
                'bluesky_available': connection_ok,
                'credentials_loaded': True,
                'error_message': None if connection_ok else connection_msg
            }
            
        except Exception as e:
            return {
                'bluesky_available': False,
                'credentials_loaded': False,
                'error_message': f'Error checking BlueSky status: {str(e)}'
            }
    
    def logout(self) -> None:
        """Clear BlueSky credentials and logout."""
        try:
            self.credentials = {}
            self.session_token = None
            creds_file = os.path.join(const.ROOT_DIR, 'bluesky_credentials.json')
            if os.path.exists(creds_file):
                os.remove(creds_file)
            self.logger.info("BlueSky logout successful")
        except Exception as e:
            self.logger.error(f"Error during BlueSky logout: {e}")