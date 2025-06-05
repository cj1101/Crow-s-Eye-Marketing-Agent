"""
Snapchat Authentication handler using Login Kit.
"""

import logging
import requests
from typing import Dict, Optional, Any
from datetime import datetime
import urllib.parse


class SnapchatAuth:
    """Handle Snapchat Login Kit authentication."""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initialize Snapchat Auth handler.
        
        Args:
            client_id: Snapchat app client ID
            client_secret: Snapchat app client secret  
            redirect_uri: OAuth redirect URI
        """
        self.logger = logging.getLogger(__name__)
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        
        # Snapchat OAuth endpoints
        self.auth_url = "https://accounts.snapchat.com/login/oauth2/authorize"
        self.token_url = "https://accounts.snapchat.com/login/oauth2/access_token"
        self.profile_url = "https://kit.snapchat.com/v1/me"
        
    def get_authorization_url(self, state: str = None) -> str:
        """
        Generate authorization URL for user login.
        
        Args:
            state: Optional state parameter for security
            
        Returns:
            str: Authorization URL
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'user.display_name user.bitmoji.avatar'
        }
        
        if state:
            params['state'] = state
            
        query_string = urllib.parse.urlencode(params)
        return f"{self.auth_url}?{query_string}"
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from callback
            
        Returns:
            dict: Token response
        """
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri
            }
            
            response = requests.post(self.token_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                return {
                    'success': True,
                    'access_token': token_data.get('access_token'),
                    'refresh_token': token_data.get('refresh_token'),
                    'expires_in': token_data.get('expires_in'),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                self.logger.error(f"Token exchange failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error exchanging code for token: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        """
        Get user profile information.
        
        Args:
            access_token: User's access token
            
        Returns:
            dict: User profile data
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(self.profile_url, headers=headers)
            
            if response.status_code == 200:
                profile_data = response.json()
                return {
                    'success': True,
                    'profile': profile_data,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                self.logger.error(f"Profile fetch failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting user profile: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token.
        
        Args:
            refresh_token: User's refresh token
            
        Returns:
            dict: New token data
        """
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(self.token_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                return {
                    'success': True,
                    'access_token': token_data.get('access_token'),
                    'refresh_token': token_data.get('refresh_token'),
                    'expires_in': token_data.get('expires_in'),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                self.logger.error(f"Token refresh failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error refreshing token: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            } 