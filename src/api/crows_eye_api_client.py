"""
Comprehensive API Client for Crow's Eye Desktop Application
Handles all communication with the FastAPI backend
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List, Union, BinaryIO
from datetime import datetime, timedelta
import asyncio
import aiohttp
from pathlib import Path

from ..config.api_config import APIConfig

logger = logging.getLogger(__name__)

class CrowsEyeAPIClient:
    """
    Comprehensive API client for the Crow's Eye FastAPI backend.
    Handles authentication, media management, AI services, analytics, and more.
    """
    
    def __init__(self):
        """Initialize the API client."""
        self.config = APIConfig()
        self.session = requests.Session()
        self.token = None
        self.user_data = None
        self.session.timeout = self.config.timeout
        
        # Set up session headers
        self.session.headers.update({
            'User-Agent': 'CrowsEye-Desktop/5.0.0',
            'Content-Type': 'application/json'
        })
        
        logger.info(f"API Client initialized with base URL: {self.config.base_url}")
    
    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            'User-Agent': 'CrowsEye-Desktop/5.0.0'
        }
        
        if include_auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
            
        return headers
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and return parsed data."""
        try:
            if response.status_code == 401:
                logger.warning("Authentication token expired or invalid")
                self.token = None
                return {"success": False, "error": "Authentication required"}
            
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', f'HTTP {response.status_code} error')
                except:
                    error_msg = f'HTTP {response.status_code} error'
                
                logger.error(f"API error {response.status_code}: {error_msg}")
                return {"success": False, "error": error_msg}
            
            # Try to parse JSON response
            try:
                data = response.json()
                if isinstance(data, dict):
                    data["success"] = True
                return data
            except:
                return {"success": True, "data": response.text}
                
        except Exception as e:
            logger.error(f"Error handling response: {e}")
            return {"success": False, "error": str(e)}
    
    # Authentication Methods
    def register(self, email: str, password: str, name: str = "") -> Dict[str, Any]:
        """Register a new user account."""
        try:
            url = self.config.get_endpoint("auth/register")
            data = {
                "email": email,
                "password": password,
                "name": name
            }
            
            response = self.session.post(url, json=data)
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {"success": False, "error": str(e)}
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login user and store authentication token."""
        try:
            url = self.config.get_endpoint("auth/login")
            data = {
                "email": email,
                "password": password
            }
            
            response = self.session.post(url, json=data)
            result = self._handle_response(response)
            
            if result.get("success"):
                # Extract data from nested structure
                data_section = result.get("data", {})
                if data_section.get("access_token"):
                    self.token = data_section["access_token"]
                    self.user_data = data_section.get("user")
                    
                    # Update session headers
                    self.session.headers['Authorization'] = f'Bearer {self.token}'
                    
                    # Update result structure for backward compatibility
                    result["access_token"] = self.token
                    result["user_data"] = self.user_data
                    
                    logger.info("User logged in successfully")
                else:
                    logger.error("Login response missing access_token")
                    return {"success": False, "error": "Login response invalid"}
            
            return result
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {"success": False, "error": str(e)}
    
    def logout(self) -> None:
        """Logout user and clear authentication data."""
        self.token = None
        self.user_data = None
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
        logger.info("User logged out")
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get current authenticated user data."""
        try:
            url = self.config.get_endpoint("auth/me")
            response = self.session.get(url, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return {"success": False, "error": str(e)}
    
    # Media Management Methods
    def upload_media(self, file_path: str, caption: str = "", ai_tags: List[str] = None) -> Dict[str, Any]:
        """Upload a media file to the backend."""
        try:
            url = self.config.get_endpoint("media/upload")
            
            with open(file_path, 'rb') as file:
                files = {'file': (os.path.basename(file_path), file)}
                data = {
                    'caption': caption,
                    'ai_tags': json.dumps(ai_tags or [])
                }
                
                # Remove Content-Type header for file upload
                headers = self._get_headers()
                if 'Content-Type' in headers:
                    del headers['Content-Type']
                
                response = self.session.post(url, files=files, data=data, headers=headers)
                return self._handle_response(response)
                
        except Exception as e:
            logger.error(f"Media upload error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_media_items(self, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        """Get user's media items."""
        try:
            url = self.config.get_endpoint("media/")
            params = {"skip": skip, "limit": limit}
            
            response = self.session.get(url, params=params, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error getting media items: {e}")
            return {"success": False, "error": str(e)}
    
    def get_media_item(self, media_id: str) -> Dict[str, Any]:
        """Get specific media item by ID."""
        try:
            url = self.config.get_endpoint(f"media/{media_id}")
            
            response = self.session.get(url, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error getting media item: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_media_item(self, media_id: str) -> Dict[str, Any]:
        """Delete a media item."""
        try:
            url = self.config.get_endpoint(f"media/{media_id}")
            
            response = self.session.delete(url, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error deleting media item: {e}")
            return {"success": False, "error": str(e)}
    
    def download_media(self, media_id: str, save_path: str) -> Dict[str, Any]:
        """Download a media file."""
        try:
            url = self.config.get_endpoint(f"media/{media_id}/download")
            
            response = self.session.get(url, headers=self._get_headers(), stream=True)
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return {"success": True, "file_path": save_path}
            else:
                return self._handle_response(response)
                
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return {"success": False, "error": str(e)}
    
    # AI Services Methods
    def generate_caption(self, media_id: str, style: str = "engaging", tone: str = "professional") -> Dict[str, Any]:
        """Generate AI caption for media."""
        try:
            url = self.config.get_endpoint("ai/captions/generate")
            data = {
                "media_id": media_id,
                "style": style,
                "tone": tone
            }
            
            response = self.session.post(url, json=data, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error generating caption: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_hashtags(self, media_id: str, count: int = 10) -> Dict[str, Any]:
        """Generate AI hashtags for media."""
        try:
            url = self.config.get_endpoint("ai/hashtags/generate")
            data = {
                "media_id": media_id,
                "count": count
            }
            
            response = self.session.post(url, json=data, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error generating hashtags: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_content(self, prompt: str, content_type: str = "caption") -> Dict[str, Any]:
        """Generate AI content from prompt."""
        try:
            url = self.config.get_endpoint("ai/content/generate")
            data = {
                "prompt": prompt,
                "content_type": content_type
            }
            
            response = self.session.post(url, json=data, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return {"success": False, "error": str(e)}
    
    def get_ai_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of AI processing job."""
        try:
            url = self.config.get_endpoint(f"ai/jobs/{job_id}")
            
            response = self.session.get(url, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return {"success": False, "error": str(e)}
    
    # Posts Management Methods
    def create_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new post."""
        try:
            url = self.config.get_endpoint("posts/")
            
            response = self.session.post(url, json=post_data, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return {"success": False, "error": str(e)}
    
    def get_posts(self, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        """Get user's posts."""
        try:
            url = self.config.get_endpoint("posts/")
            params = {"skip": skip, "limit": limit}
            
            response = self.session.get(url, params=params, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error getting posts: {e}")
            return {"success": False, "error": str(e)}
    
    def publish_post(self, post_id: str, platforms: List[str]) -> Dict[str, Any]:
        """Publish post to specified platforms."""
        try:
            url = self.config.get_endpoint(f"posts/{post_id}/publish")
            data = {"platforms": platforms}
            
            response = self.session.post(url, json=data, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error publishing post: {e}")
            return {"success": False, "error": str(e)}
    
    def schedule_post(self, post_id: str, scheduled_time: datetime, platforms: List[str]) -> Dict[str, Any]:
        """Schedule post for future publishing."""
        try:
            url = self.config.get_endpoint(f"posts/{post_id}/schedule")
            data = {
                "scheduled_time": scheduled_time.isoformat(),
                "platforms": platforms
            }
            
            response = self.session.post(url, json=data, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error scheduling post: {e}")
            return {"success": False, "error": str(e)}
    
    # Platform Management Methods
    def get_platform_accounts(self) -> Dict[str, Any]:
        """Get connected platform accounts."""
        try:
            url = self.config.get_endpoint("platforms/accounts")
            
            response = self.session.get(url, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error getting platform accounts: {e}")
            return {"success": False, "error": str(e)}
    
    def connect_platform(self, platform: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Connect to a social media platform."""
        try:
            url = self.config.get_endpoint(f"platforms/{platform}/connect")
            
            response = self.session.post(url, json=credentials, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error connecting platform: {e}")
            return {"success": False, "error": str(e)}
    
    def disconnect_platform(self, platform: str) -> Dict[str, Any]:
        """Disconnect from a social media platform."""
        try:
            url = self.config.get_endpoint(f"platforms/{platform}/disconnect")
            
            response = self.session.post(url, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error disconnecting platform: {e}")
            return {"success": False, "error": str(e)}
    
    # Analytics Methods
    def get_analytics_overview(self, date_range: str = "30d") -> Dict[str, Any]:
        """Get analytics overview."""
        try:
            url = self.config.get_endpoint("analytics/overview")
            params = {"date_range": date_range}
            
            response = self.session.get(url, params=params, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {"success": False, "error": str(e)}
    
    def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get analytics for specific post."""
        try:
            url = self.config.get_endpoint(f"analytics/posts/{post_id}")
            
            response = self.session.get(url, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error getting post analytics: {e}")
            return {"success": False, "error": str(e)}
    
    def get_platform_analytics(self, platform: str, date_range: str = "30d") -> Dict[str, Any]:
        """Get analytics for specific platform."""
        try:
            url = self.config.get_endpoint(f"analytics/platforms/{platform}")
            params = {"date_range": date_range}
            
            response = self.session.get(url, params=params, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error getting platform analytics: {e}")
            return {"success": False, "error": str(e)}
    
    # Google Photos Integration
    def get_google_photos_auth_url(self) -> Dict[str, Any]:
        """Get Google Photos authentication URL."""
        try:
            url = self.config.get_endpoint("google-photos/auth/url")
            
            response = self.session.get(url, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error getting Google Photos auth URL: {e}")
            return {"success": False, "error": str(e)}
    
    def google_photos_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Handle Google Photos OAuth callback."""
        try:
            url = self.config.get_endpoint("google-photos/auth/callback")
            data = {"code": code, "state": state}
            
            response = self.session.post(url, json=data, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error handling Google Photos callback: {e}")
            return {"success": False, "error": str(e)}
    
    def get_google_photos_albums(self) -> Dict[str, Any]:
        """Get Google Photos albums."""
        try:
            url = self.config.get_endpoint("google-photos/albums")
            
            response = self.session.get(url, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error getting Google Photos albums: {e}")
            return {"success": False, "error": str(e)}
    
    def import_from_google_photos(self, media_ids: List[str]) -> Dict[str, Any]:
        """Import media from Google Photos."""
        try:
            url = self.config.get_endpoint("google-photos/import")
            data = {"media_ids": media_ids}
            
            response = self.session.post(url, json=data, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error importing from Google Photos: {e}")
            return {"success": False, "error": str(e)}
    
    # YouTube Integration
    def get_youtube_auth_url(self) -> Dict[str, Any]:
        """Get YouTube authentication URL."""
        try:
            url = self.config.get_endpoint("youtube/auth/url")
            
            response = self.session.get(url, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error getting YouTube auth URL: {e}")
            return {"success": False, "error": str(e)}
    
    def upload_to_youtube(self, media_id: str, title: str, description: str, tags: List[str] = None) -> Dict[str, Any]:
        """Upload video to YouTube."""
        try:
            url = self.config.get_endpoint("youtube/upload")
            data = {
                "media_id": media_id,
                "title": title,
                "description": description,
                "tags": tags or []
            }
            
            response = self.session.post(url, json=data, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error uploading to YouTube: {e}")
            return {"success": False, "error": str(e)}
    
    # Gallery Management
    def create_gallery(self, name: str, media_ids: List[str], description: str = "") -> Dict[str, Any]:
        """Create a media gallery."""
        try:
            url = self.config.get_endpoint("galleries/")
            data = {
                "name": name,
                "media_ids": media_ids,
                "description": description
            }
            
            response = self.session.post(url, json=data, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error creating gallery: {e}")
            return {"success": False, "error": str(e)}
    
    def get_galleries(self, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        """Get user's galleries."""
        try:
            url = self.config.get_endpoint("galleries/")
            params = {"skip": skip, "limit": limit}
            
            response = self.session.get(url, params=params, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error getting galleries: {e}")
            return {"success": False, "error": str(e)}
    
    # Scheduling Methods
    def get_scheduled_posts(self) -> Dict[str, Any]:
        """Get scheduled posts."""
        try:
            url = self.config.get_endpoint("schedules/")
            
            response = self.session.get(url, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error getting scheduled posts: {e}")
            return {"success": False, "error": str(e)}
    
    def cancel_scheduled_post(self, schedule_id: str) -> Dict[str, Any]:
        """Cancel a scheduled post."""
        try:
            url = self.config.get_endpoint(f"schedules/{schedule_id}/cancel")
            
            response = self.session.post(url, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error canceling scheduled post: {e}")
            return {"success": False, "error": str(e)}
    
    # Templates Methods
    def get_templates(self) -> Dict[str, Any]:
        """Get content templates."""
        try:
            url = self.config.get_endpoint("templates/")
            
            response = self.session.get(url, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            return {"success": False, "error": str(e)}
    
    def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new template."""
        try:
            url = self.config.get_endpoint("templates/")
            
            response = self.session.post(url, json=template_data, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return {"success": False, "error": str(e)}
    
    # Subscription Methods
    def get_subscription_status(self) -> Dict[str, Any]:
        """Get user's subscription status."""
        try:
            url = self.config.get_endpoint("subscription/status")
            
            response = self.session.get(url, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error getting subscription status: {e}")
            return {"success": False, "error": str(e)}
    
    def update_subscription(self, plan: str) -> Dict[str, Any]:
        """Update user's subscription plan."""
        try:
            url = self.config.get_endpoint("subscription/update")
            data = {"plan": plan}
            
            response = self.session.post(url, json=data, headers=self._get_headers())
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            return {"success": False, "error": str(e)}
    
    # Health Check
    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        try:
            url = self.config.get_endpoint("health")
            
            response = self.session.get(url, timeout=5)
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"success": False, "error": str(e)}

# Global API client instance
api_client = CrowsEyeAPIClient() 