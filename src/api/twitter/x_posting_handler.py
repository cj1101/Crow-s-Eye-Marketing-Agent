"""
X (Twitter) API posting handler for uploading content to X.
Handles the complete posting workflow including media upload and publishing.
"""
import os
import json
import logging
import time
import requests
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QThread

from ..config import constants as const

class XPostingSignals(QObject):
    """Signals for X API posting operations."""
    upload_started = Signal(str)  # platform
    upload_progress = Signal(str, int)  # message, percentage
    upload_success = Signal(str, dict)  # platform, response_data
    upload_error = Signal(str, str)  # platform, error_message
    status_update = Signal(str)

class XPostingHandler:
    """Handler for posting content to X (Twitter) via X API v2."""
    
    def __init__(self):
        """Initialize the X posting handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.signals = XPostingSignals()
        self.credentials = None
        self._load_credentials()
        
    def _load_credentials(self) -> bool:
        """Load X API credentials."""
        try:
            credentials_file = os.path.join(const.ROOT_DIR, 'x_credentials.json')
            if os.path.exists(credentials_file):
                with open(credentials_file, 'r', encoding='utf-8') as f:
                    self.credentials = json.load(f)
                return True
            else:
                # Try environment variables
                bearer_token = os.getenv('X_BEARER_TOKEN')
                api_key = os.getenv('X_API_KEY')
                api_secret = os.getenv('X_API_SECRET')
                access_token = os.getenv('X_ACCESS_TOKEN')
                access_token_secret = os.getenv('X_ACCESS_TOKEN_SECRET')
                
                if all([bearer_token, api_key, api_secret, access_token, access_token_secret]):
                    self.credentials = {
                        'bearer_token': bearer_token,
                        'api_key': api_key,
                        'api_secret': api_secret,
                        'access_token': access_token,
                        'access_token_secret': access_token_secret
                    }
                    return True
                    
            self.logger.warning("X credentials not found")
            return False
        except Exception as e:
            self.logger.exception(f"Error loading X credentials: {e}")
            return False
    
    def post_to_x(self, media_path: str = None, caption: str = "", 
                  is_video: bool = False) -> Tuple[bool, str]:
        """
        Post content to X (Twitter).
        
        Args:
            media_path: Path to the media file (optional for text-only posts)
            caption: Caption for the post (tweet text)
            is_video: Whether the media is a video
            
        Returns:
            Tuple of (success, message/error)
        """
        try:
            if not self.credentials:
                if not self._load_credentials():
                    return False, "X credentials not available"
            
            self.signals.upload_started.emit("X")
            self.signals.status_update.emit("Posting to X...")
            
            # X allows text-only posts, so media is optional
            if media_path:
                if is_video:
                    success, message = self._post_x_video(media_path, caption)
                else:
                    success, message = self._post_x_image(media_path, caption)
            else:
                success, message = self._post_x_text(caption)
            
            if success:
                self.signals.upload_success.emit("X", {"message": message})
                self.signals.status_update.emit("Successfully posted to X!")
                return True, "Successfully posted to X"
            else:
                return False, f"Failed to post to X: {message}"
                
        except Exception as e:
            error_msg = f"Error posting to X: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("X", error_msg)
            return False, error_msg
    
    def _post_x_text(self, caption: str) -> Tuple[bool, str]:
        """Post text-only content to X."""
        try:
            url = "https://api.twitter.com/2/tweets"
            
            headers = {
                'Authorization': f"Bearer {self.credentials['bearer_token']}",
                'Content-Type': 'application/json'
            }
            
            # Truncate caption if too long (X has 280 character limit)
            if len(caption) > 280:
                caption = caption[:277] + "..."
            
            post_data = {
                "text": caption
            }
            
            response = requests.post(url, headers=headers, json=post_data, timeout=30)
            
            if response.status_code in [200, 201]:
                return True, "Text post published successfully"
            else:
                error_data = response.json()
                error_msg = error_data.get('detail', 'Unknown error')
                return False, error_msg
                
        except Exception as e:
            return False, str(e)
    
    def _post_x_image(self, media_path: str, caption: str) -> Tuple[bool, str]:
        """Post image to X."""
        try:
            # Step 1: Upload media
            media_id = self._upload_media_v1(media_path)
            if not media_id:
                return False, "Failed to upload media"
            
            # Step 2: Create tweet with media
            return self._create_tweet_with_media(media_id, caption)
                
        except Exception as e:
            return False, str(e)
    
    def _post_x_video(self, media_path: str, caption: str) -> Tuple[bool, str]:
        """Post video to X."""
        try:
            # Step 1: Upload media (chunked for videos)
            media_id = self._upload_video_chunked(media_path)
            if not media_id:
                return False, "Failed to upload video"
            
            # Step 2: Create tweet with media
            return self._create_tweet_with_media(media_id, caption)
                
        except Exception as e:
            return False, str(e)
    
    def _upload_media_v1(self, media_path: str) -> Optional[str]:
        """Upload media using Twitter API v1.1 (required for media upload)."""
        try:
            import requests_oauthlib
            
            # Use OAuth 1.0a for media upload (v1.1 API requirement)
            auth = requests_oauthlib.OAuth1(
                self.credentials['api_key'],
                client_secret=self.credentials['api_secret'],
                resource_owner_key=self.credentials['access_token'],
                resource_owner_secret=self.credentials['access_token_secret']
            )
            
            url = "https://upload.twitter.com/1.1/media/upload.json"
            
            with open(media_path, 'rb') as f:
                files = {'media': f}
                response = requests.post(url, auth=auth, files=files, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return str(result['media_id'])
            else:
                self.logger.error(f"Failed to upload media: {response.text}")
                return None
                
        except ImportError:
            self.logger.error("requests-oauthlib is required for X media upload. Install with: pip install requests-oauthlib")
            return None
        except Exception as e:
            self.logger.exception(f"Error uploading media: {e}")
            return None
    
    def _upload_video_chunked(self, media_path: str) -> Optional[str]:
        """Upload video using chunked upload for larger files."""
        try:
            import requests_oauthlib
            
            auth = requests_oauthlib.OAuth1(
                self.credentials['api_key'],
                client_secret=self.credentials['api_secret'],
                resource_owner_key=self.credentials['access_token'],
                resource_owner_secret=self.credentials['access_token_secret']
            )
            
            file_size = os.path.getsize(media_path)
            
            # Step 1: Initialize upload
            init_url = "https://upload.twitter.com/1.1/media/upload.json"
            init_data = {
                'command': 'INIT',
                'media_type': 'video/mp4',
                'total_bytes': file_size
            }
            
            response = requests.post(init_url, auth=auth, data=init_data, timeout=30)
            if response.status_code != 202:
                self.logger.error(f"Failed to initialize video upload: {response.text}")
                return None
            
            media_id = response.json()['media_id']
            
            # Step 2: Upload chunks
            chunk_size = 1024 * 1024  # 1MB chunks
            segment_id = 0
            
            with open(media_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    append_data = {
                        'command': 'APPEND',
                        'media_id': media_id,
                        'segment_index': segment_id
                    }
                    
                    files = {'media': chunk}
                    response = requests.post(init_url, auth=auth, data=append_data, files=files, timeout=60)
                    
                    if response.status_code != 204:
                        self.logger.error(f"Failed to upload chunk {segment_id}: {response.text}")
                        return None
                    
                    segment_id += 1
            
            # Step 3: Finalize upload
            finalize_data = {
                'command': 'FINALIZE',
                'media_id': media_id
            }
            
            response = requests.post(init_url, auth=auth, data=finalize_data, timeout=30)
            if response.status_code != 201:
                self.logger.error(f"Failed to finalize video upload: {response.text}")
                return None
            
            return str(media_id)
                
        except ImportError:
            self.logger.error("requests-oauthlib is required for X media upload. Install with: pip install requests-oauthlib")
            return None
        except Exception as e:
            self.logger.exception(f"Error uploading video: {e}")
            return None
    
    def _create_tweet_with_media(self, media_id: str, caption: str) -> Tuple[bool, str]:
        """Create tweet with attached media."""
        try:
            url = "https://api.twitter.com/2/tweets"
            
            headers = {
                'Authorization': f"Bearer {self.credentials['bearer_token']}",
                'Content-Type': 'application/json'
            }
            
            # Truncate caption if too long
            if len(caption) > 280:
                caption = caption[:277] + "..."
            
            post_data = {
                "text": caption,
                "media": {
                    "media_ids": [media_id]
                }
            }
            
            response = requests.post(url, headers=headers, json=post_data, timeout=30)
            
            if response.status_code in [200, 201]:
                return True, "Media post published successfully"
            else:
                error_data = response.json()
                error_msg = error_data.get('detail', 'Unknown error')
                return False, error_msg
                
        except Exception as e:
            return False, str(e)
    
    def validate_media_file(self, media_path: str) -> Tuple[bool, str]:
        """Validate media file for X posting."""
        try:
            if not os.path.exists(media_path):
                return False, "File does not exist"
            
            file_size = os.path.getsize(media_path)
            file_ext = os.path.splitext(media_path)[1].lower()
            
            # X media limits
            if file_ext in const.SUPPORTED_IMAGE_FORMATS:
                if file_size > 5 * 1024 * 1024:  # 5MB for images
                    return False, "Image file too large (max 5MB)"
            elif file_ext in const.SUPPORTED_VIDEO_FORMATS:
                if file_size > 512 * 1024 * 1024:  # 512MB for videos
                    return False, "Video file too large (max 512MB)"
            else:
                return False, f"Unsupported file format: {file_ext}"
            
            return True, "File is valid"
            
        except Exception as e:
            return False, f"Error validating file: {str(e)}"
    
    def get_posting_status(self) -> Dict[str, Any]:
        """Get X posting status and availability."""
        return {
            "credentials_loaded": self.credentials is not None,
            "x_available": self.credentials is not None,
            "error_message": None if self.credentials else "X credentials not configured"
        }

class XPostingWorker(QThread):
    """Worker thread for X API posting operations."""
    
    finished = Signal(bool, str, str)  # success, platform, message
    progress = Signal(str, int)  # message, percentage
    
    def __init__(self, handler: XPostingHandler, media_path: str, 
                 caption: str, is_video: bool = False):
        super().__init__()
        self.handler = handler
        self.media_path = media_path
        self.caption = caption
        self.is_video = is_video
        
    def run(self):
        """Run the X posting operation."""
        try:
            self.progress.emit("Starting X post...", 10)
            
            success, message = self.handler.post_to_x(
                self.media_path, self.caption, self.is_video
            )
            
            self.progress.emit("X posting complete", 100)
            self.finished.emit(success, "X", message)
            
        except Exception as e:
            self.finished.emit(False, "X", f"Error in X posting worker: {str(e)}") 