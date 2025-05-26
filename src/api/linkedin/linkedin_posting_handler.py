"""
LinkedIn API posting handler for uploading content to LinkedIn.
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

class LinkedInPostingSignals(QObject):
    """Signals for LinkedIn API posting operations."""
    upload_started = Signal(str)  # platform
    upload_progress = Signal(str, int)  # message, percentage
    upload_success = Signal(str, dict)  # platform, response_data
    upload_error = Signal(str, str)  # platform, error_message
    status_update = Signal(str)

class LinkedInPostingHandler:
    """Handler for posting content to LinkedIn via LinkedIn API."""
    
    def __init__(self):
        """Initialize the LinkedIn posting handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.signals = LinkedInPostingSignals()
        self.credentials = None
        self._load_credentials()
        
    def _load_credentials(self) -> bool:
        """Load LinkedIn API credentials."""
        try:
            credentials_file = os.path.join(const.ROOT_DIR, 'linkedin_credentials.json')
            if os.path.exists(credentials_file):
                with open(credentials_file, 'r', encoding='utf-8') as f:
                    self.credentials = json.load(f)
                return True
            else:
                # Try environment variables
                access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
                person_id = os.getenv('LINKEDIN_PERSON_ID')
                
                if access_token and person_id:
                    self.credentials = {
                        'access_token': access_token,
                        'person_id': person_id
                    }
                    return True
                    
            self.logger.warning("LinkedIn credentials not found")
            return False
        except Exception as e:
            self.logger.exception(f"Error loading LinkedIn credentials: {e}")
            return False
    
    def post_to_linkedin(self, media_path: str = None, caption: str = "", 
                        is_video: bool = False) -> Tuple[bool, str]:
        """
        Post content to LinkedIn.
        
        Args:
            media_path: Path to the media file (optional for text-only posts)
            caption: Caption for the post
            is_video: Whether the media is a video
            
        Returns:
            Tuple of (success, message/error)
        """
        try:
            if not self.credentials:
                if not self._load_credentials():
                    return False, "LinkedIn credentials not available"
            
            self.signals.upload_started.emit("LinkedIn")
            self.signals.status_update.emit("Posting to LinkedIn...")
            
            # LinkedIn allows text-only posts, so media is optional
            if media_path:
                if is_video:
                    success, message = self._post_linkedin_video(media_path, caption)
                else:
                    success, message = self._post_linkedin_image(media_path, caption)
            else:
                success, message = self._post_linkedin_text(caption)
            
            if success:
                self.signals.upload_success.emit("LinkedIn", {"message": message})
                self.signals.status_update.emit("Successfully posted to LinkedIn!")
                return True, "Successfully posted to LinkedIn"
            else:
                return False, f"Failed to post to LinkedIn: {message}"
                
        except Exception as e:
            error_msg = f"Error posting to LinkedIn: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit("LinkedIn", error_msg)
            return False, error_msg
    
    def _post_linkedin_text(self, caption: str) -> Tuple[bool, str]:
        """Post text-only content to LinkedIn."""
        try:
            url = "https://api.linkedin.com/v2/ugcPosts"
            
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}",
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            post_data = {
                "author": f"urn:li:person:{self.credentials['person_id']}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": caption
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            response = requests.post(url, headers=headers, json=post_data, timeout=30)
            
            if response.status_code in [200, 201]:
                return True, "Text post published successfully"
            else:
                error_msg = response.json().get('message', 'Unknown error')
                return False, error_msg
                
        except Exception as e:
            return False, str(e)
    
    def _post_linkedin_image(self, media_path: str, caption: str) -> Tuple[bool, str]:
        """Post image to LinkedIn."""
        try:
            # Step 1: Register upload
            upload_url = self._register_upload(media_path, "IMAGE")
            if not upload_url:
                return False, "Failed to register upload"
            
            # Step 2: Upload media
            asset_id = self._upload_media(media_path, upload_url)
            if not asset_id:
                return False, "Failed to upload media"
            
            # Step 3: Create post with media
            return self._create_media_post(asset_id, caption, "IMAGE")
                
        except Exception as e:
            return False, str(e)
    
    def _post_linkedin_video(self, media_path: str, caption: str) -> Tuple[bool, str]:
        """Post video to LinkedIn."""
        try:
            # Step 1: Register upload
            upload_url = self._register_upload(media_path, "VIDEO")
            if not upload_url:
                return False, "Failed to register upload"
            
            # Step 2: Upload media
            asset_id = self._upload_media(media_path, upload_url)
            if not asset_id:
                return False, "Failed to upload media"
            
            # Step 3: Create post with media
            return self._create_media_post(asset_id, caption, "VIDEO")
                
        except Exception as e:
            return False, str(e)
    
    def _register_upload(self, media_path: str, media_type: str) -> Optional[str]:
        """Register media upload with LinkedIn."""
        try:
            url = "https://api.linkedin.com/v2/assets?action=registerUpload"
            
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}",
                'Content-Type': 'application/json'
            }
            
            file_size = os.path.getsize(media_path)
            
            register_data = {
                "registerUploadRequest": {
                    "recipes": [f"urn:li:digitalmediaRecipe:feedshare-{media_type.lower()}"],
                    "owner": f"urn:li:person:{self.credentials['person_id']}",
                    "serviceRelationships": [
                        {
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent"
                        }
                    ]
                }
            }
            
            response = requests.post(url, headers=headers, json=register_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                upload_mechanism = result['value']['uploadMechanism']
                upload_url = upload_mechanism['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
                asset_id = result['value']['asset']
                
                # Store asset_id for later use
                self._current_asset_id = asset_id
                return upload_url
            else:
                self.logger.error(f"Failed to register upload: {response.text}")
                return None
                
        except Exception as e:
            self.logger.exception(f"Error registering upload: {e}")
            return None
    
    def _upload_media(self, media_path: str, upload_url: str) -> Optional[str]:
        """Upload media file to LinkedIn."""
        try:
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}"
            }
            
            with open(media_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(upload_url, headers=headers, files=files, timeout=60)
            
            if response.status_code in [200, 201]:
                return getattr(self, '_current_asset_id', None)
            else:
                self.logger.error(f"Failed to upload media: {response.text}")
                return None
                
        except Exception as e:
            self.logger.exception(f"Error uploading media: {e}")
            return None
    
    def _create_media_post(self, asset_id: str, caption: str, media_type: str) -> Tuple[bool, str]:
        """Create LinkedIn post with media."""
        try:
            url = "https://api.linkedin.com/v2/ugcPosts"
            
            headers = {
                'Authorization': f"Bearer {self.credentials['access_token']}",
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            post_data = {
                "author": f"urn:li:person:{self.credentials['person_id']}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": caption
                        },
                        "shareMediaCategory": media_type,
                        "media": [
                            {
                                "status": "READY",
                                "description": {
                                    "text": caption
                                },
                                "media": asset_id,
                                "title": {
                                    "text": "Breadsmith Content"
                                }
                            }
                        ]
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            response = requests.post(url, headers=headers, json=post_data, timeout=30)
            
            if response.status_code in [200, 201]:
                return True, f"{media_type} post published successfully"
            else:
                error_msg = response.json().get('message', 'Unknown error')
                return False, error_msg
                
        except Exception as e:
            return False, str(e)
    
    def validate_media_file(self, media_path: str) -> Tuple[bool, str]:
        """Validate media file for LinkedIn posting."""
        try:
            if not os.path.exists(media_path):
                return False, "File does not exist"
            
            file_size = os.path.getsize(media_path)
            file_ext = os.path.splitext(media_path)[1].lower()
            
            # LinkedIn media limits
            if file_ext in const.SUPPORTED_IMAGE_FORMATS:
                if file_size > 20 * 1024 * 1024:  # 20MB for images
                    return False, "Image file too large (max 20MB)"
            elif file_ext in const.SUPPORTED_VIDEO_FORMATS:
                if file_size > 5 * 1024 * 1024 * 1024:  # 5GB for videos
                    return False, "Video file too large (max 5GB)"
            else:
                return False, f"Unsupported file format: {file_ext}"
            
            return True, "File is valid"
            
        except Exception as e:
            return False, f"Error validating file: {str(e)}"
    
    def get_posting_status(self) -> Dict[str, Any]:
        """Get LinkedIn posting status and availability."""
        return {
            "credentials_loaded": self.credentials is not None,
            "linkedin_available": self.credentials is not None,
            "error_message": None if self.credentials else "LinkedIn credentials not configured"
        }

class LinkedInPostingWorker(QThread):
    """Worker thread for LinkedIn API posting operations."""
    
    finished = Signal(bool, str, str)  # success, platform, message
    progress = Signal(str, int)  # message, percentage
    
    def __init__(self, handler: LinkedInPostingHandler, media_path: str, 
                 caption: str, is_video: bool = False):
        super().__init__()
        self.handler = handler
        self.media_path = media_path
        self.caption = caption
        self.is_video = is_video
        
    def run(self):
        """Run the LinkedIn posting operation."""
        try:
            self.progress.emit("Starting LinkedIn post...", 10)
            
            success, message = self.handler.post_to_linkedin(
                self.media_path, self.caption, self.is_video
            )
            
            self.progress.emit("LinkedIn posting complete", 100)
            self.finished.emit(success, "LinkedIn", message)
            
        except Exception as e:
            self.finished.emit(False, "LinkedIn", f"Error in LinkedIn posting worker: {str(e)}") 