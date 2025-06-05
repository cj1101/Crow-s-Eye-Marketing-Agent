"""
Modernized Snapchat API interface
Provides clean, simple endpoints for website integration
"""

import logging
from typing import Dict, Any, Optional, List
from .snapchat_client import SnapchatClient
from .snapchat_auth import SnapchatAuth

logger = logging.getLogger(__name__)

class SnapchatAPI:
    """
    Modern Snapchat API interface for website integration
    Provides clean, consistent endpoints for web applications
    """
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = None):
        """
        Initialize Snapchat API
        
        Args:
            client_id: Snapchat app client ID
            client_secret: Snapchat app client secret
            redirect_uri: OAuth redirect URI (for web integration)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth = SnapchatAuth(client_id, client_secret, redirect_uri)
        self.client = None
        
    # Authentication Methods
    def get_auth_url(self, state: str = None) -> Dict[str, Any]:
        """
        Get OAuth authorization URL for website integration
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Dict containing authorization URL and state
        """
        try:
            auth_url = self.auth.get_authorization_url(state=state)
            return {
                "success": True,
                "auth_url": auth_url,
                "state": state,
                "expires_in": 600  # 10 minutes
            }
        except Exception as e:
            logger.error(f"Error getting auth URL: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def exchange_code(self, code: str, state: str = None) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from OAuth callback
            state: State parameter for verification
            
        Returns:
            Dict containing access token and user info
        """
        try:
            token_data = self.auth.exchange_code_for_token(code)
            if token_data.get("success"):
                # Get user profile
                user_info = self.auth.get_user_profile(token_data["access_token"])
                
                return {
                    "success": True,
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_in": token_data.get("expires_in", 3600),
                    "user": user_info.get("user", {}),
                    "connected_at": self._get_timestamp()
                }
            else:
                return token_data
                
        except Exception as e:
            logger.error(f"Error exchanging code: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token
        
        Args:
            refresh_token: Refresh token from previous authentication
            
        Returns:
            Dict containing new access token
        """
        try:
            result = self.auth.refresh_access_token(refresh_token)
            if result.get("success"):
                result["refreshed_at"] = self._get_timestamp()
            return result
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Core API Methods
    def connect(self, access_token: str) -> Dict[str, Any]:
        """
        Connect to Snapchat with access token
        
        Args:
            access_token: Valid Snapchat access token
            
        Returns:
            Dict containing connection status
        """
        try:
            self.client = SnapchatClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                access_token=access_token
            )
            
            # Test connection
            connection_test = self.client.test_connection()
            if connection_test.get("success"):
                return {
                    "success": True,
                    "message": "Connected to Snapchat successfully",
                    "connected_at": self._get_timestamp()
                }
            else:
                return connection_test
                
        except Exception as e:
            logger.error(f"Error connecting to Snapchat: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user_info(self, access_token: str = None) -> Dict[str, Any]:
        """
        Get current user information
        
        Args:
            access_token: Optional access token (uses client token if not provided)
            
        Returns:
            Dict containing user information
        """
        try:
            if access_token:
                temp_client = SnapchatClient(self.client_id, self.client_secret, access_token)
                return temp_client.get_user_info()
            elif self.client:
                return self.client.get_user_info()
            else:
                return {
                    "success": False,
                    "error": "No access token provided and no active connection"
                }
                
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def share_media(self, media_path: str, caption: str = "", access_token: str = None) -> Dict[str, Any]:
        """
        Share media to Snapchat
        
        Args:
            media_path: Path to media file
            caption: Optional caption for the media
            access_token: Optional access token
            
        Returns:
            Dict containing share result
        """
        try:
            if access_token:
                temp_client = SnapchatClient(self.client_id, self.client_secret, access_token)
                return temp_client.share_media(media_path, caption)
            elif self.client:
                return self.client.share_media(media_path, caption)
            else:
                return {
                    "success": False,
                    "error": "No access token provided and no active connection"
                }
                
        except Exception as e:
            logger.error(f"Error sharing media: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_analytics(self, access_token: str = None) -> Dict[str, Any]:
        """
        Get basic analytics/insights
        
        Args:
            access_token: Optional access token
            
        Returns:
            Dict containing analytics data
        """
        try:
            if access_token:
                temp_client = SnapchatClient(self.client_id, self.client_secret, access_token)
                return temp_client.get_insights()
            elif self.client:
                return self.client.get_insights()
            else:
                return {
                    "success": False,
                    "error": "No access token provided and no active connection"
                }
                
        except Exception as e:
            logger.error(f"Error getting analytics: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Utility Methods
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate API configuration
        
        Returns:
            Dict containing validation results
        """
        try:
            validation = {
                "client_id": bool(self.client_id),
                "client_secret": bool(self.client_secret),
                "redirect_uri": bool(self.redirect_uri)
            }
            
            all_valid = all(validation.values())
            
            return {
                "success": all_valid,
                "validation": validation,
                "message": "Configuration valid" if all_valid else "Missing required configuration"
            }
            
        except Exception as e:
            logger.error(f"Error validating config: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_platform_info(self) -> Dict[str, Any]:
        """
        Get platform information for website integration
        
        Returns:
            Dict containing platform details
        """
        return {
            "platform": "snapchat",
            "name": "Snapchat",
            "version": "1.0.0",
            "features": [
                "media_sharing",
                "user_authentication",
                "basic_analytics"
            ],
            "supported_media_types": ["image", "video"],
            "max_file_size": "50MB",
            "api_limits": {
                "requests_per_hour": 1000,
                "requests_per_day": 10000
            }
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

# Convenience functions for quick API access
def get_snapchat_auth_url(client_id: str, client_secret: str, redirect_uri: str, state: str = None) -> Dict[str, Any]:
    """
    Quick function to get Snapchat OAuth URL
    
    Args:
        client_id: Snapchat app client ID
        client_secret: Snapchat app client secret
        redirect_uri: OAuth redirect URI
        state: Optional state parameter
        
    Returns:
        Dict containing authorization URL
    """
    api = SnapchatAPI(client_id, client_secret, redirect_uri)
    return api.get_auth_url(state)

def exchange_snapchat_code(client_id: str, client_secret: str, redirect_uri: str, code: str) -> Dict[str, Any]:
    """
    Quick function to exchange OAuth code for token
    
    Args:
        client_id: Snapchat app client ID
        client_secret: Snapchat app client secret
        redirect_uri: OAuth redirect URI
        code: Authorization code
        
    Returns:
        Dict containing access token and user info
    """
    api = SnapchatAPI(client_id, client_secret, redirect_uri)
    return api.exchange_code(code)

def share_to_snapchat(client_id: str, client_secret: str, access_token: str, media_path: str, caption: str = "") -> Dict[str, Any]:
    """
    Quick function to share media to Snapchat
    
    Args:
        client_id: Snapchat app client ID
        client_secret: Snapchat app client secret
        access_token: User access token
        media_path: Path to media file
        caption: Optional caption
        
    Returns:
        Dict containing share result
    """
    api = SnapchatAPI(client_id, client_secret)
    return api.share_media(media_path, caption, access_token) 