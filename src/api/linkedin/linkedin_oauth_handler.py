"""
OAuth handler for LinkedIn API authentication.
Provides a modern, user-friendly login experience using LinkedIn's OAuth 2.0 flow.
"""
import os
import json
import logging
import secrets
import urllib.parse
from typing import Dict, Any, Optional
import requests
from PySide6.QtCore import QObject, Signal
import webbrowser

from ..config import constants as const

logger = logging.getLogger(__name__)

class LinkedInOAuthSignals(QObject):
    """Signals for LinkedIn OAuth authentication process."""
    auth_started = Signal()
    auth_success = Signal(dict)
    auth_error = Signal(str)
    auth_progress = Signal(str)

class LinkedInOAuthHandler:
    """
    Modern OAuth 2.0 handler for LinkedIn API authentication.
    Provides a streamlined login experience without manual credential entry.
    """
    
    def __init__(self):
        """Initialize the LinkedIn OAuth handler."""
        self.signals = LinkedInOAuthSignals()
        self.auth_data = {}
        
        # OAuth configuration - these would be configured per deployment
        self.client_id = os.getenv("LINKEDIN_CLIENT_ID", "your_linkedin_client_id")
        self.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET", "your_linkedin_client_secret")
        self.redirect_uri = "https://localhost:8080/auth/linkedin/callback"
        
        # LinkedIn OAuth URLs
        self.auth_base_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        
        # Required scopes for LinkedIn functionality
        self.required_scopes = [
            "r_liteprofile",
            "r_emailaddress",
            "w_member_social"
        ]
        
        # State parameter for CSRF protection
        self.state = None
        
    def _generate_state(self) -> None:
        """Generate state parameter for CSRF protection."""
        self.state = secrets.token_urlsafe(32)
        
    def start_oauth_flow(self) -> str:
        """
        Start the OAuth flow and return the authorization URL.
        
        Returns:
            str: The authorization URL for the user to visit
        """
        try:
            self._generate_state()
            
            # Build authorization URL
            params = {
                'response_type': 'code',
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'scope': ' '.join(self.required_scopes),
                'state': self.state
            }
            
            auth_url = f"{self.auth_base_url}?{urllib.parse.urlencode(params)}"
            
            self.signals.auth_started.emit()
            self.signals.auth_progress.emit("Starting LinkedIn login...")
            
            logger.info("LinkedIn OAuth flow started")
            return auth_url
            
        except Exception as e:
            logger.error(f"Error starting LinkedIn OAuth flow: {e}")
            self.signals.auth_error.emit(f"Failed to start LinkedIn login: {str(e)}")
            return ""
    
    def handle_callback(self, callback_url: str) -> bool:
        """
        Handle the OAuth callback URL and exchange code for tokens.
        
        Args:
            callback_url: The full callback URL with code and state parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Parse callback URL
            parsed_url = urllib.parse.urlparse(callback_url)
            params = urllib.parse.parse_qs(parsed_url.query)
            
            # Check for error
            if 'error' in params:
                error_msg = params.get('error_description', ['Unknown error'])[0]
                self.signals.auth_error.emit(f"LinkedIn login failed: {error_msg}")
                return False
            
            # Verify state parameter
            if params.get('state', [''])[0] != self.state:
                self.signals.auth_error.emit("Security check failed. Please try again.")
                return False
            
            # Get authorization code
            auth_code = params.get('code', [''])[0]
            if not auth_code:
                self.signals.auth_error.emit("No authorization code received.")
                return False
            
            # Exchange code for access token
            return self._exchange_code_for_token(auth_code)
            
        except Exception as e:
            logger.error(f"Error handling LinkedIn OAuth callback: {e}")
            self.signals.auth_error.emit(f"LinkedIn login error: {str(e)}")
            return False
    
    def _exchange_code_for_token(self, auth_code: str) -> bool:
        """
        Exchange authorization code for access token.
        
        Args:
            auth_code: The authorization code from callback
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.signals.auth_progress.emit("Getting LinkedIn access token...")
            
            # Prepare token request
            token_data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': self.redirect_uri,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Make token request
            response = requests.post(self.token_url, data=token_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                token_response = response.json()
                
                # Store access token
                access_token = token_response.get('access_token')
                if access_token:
                    self.auth_data = {
                        'access_token': access_token,
                        'token_type': token_response.get('token_type', 'Bearer'),
                        'expires_in': token_response.get('expires_in')
                    }
                    
                    # Get user info
                    return self._fetch_user_data(access_token)
                else:
                    self.signals.auth_error.emit("No access token received from LinkedIn.")
                    return False
            else:
                error_msg = response.json().get('error_description', 'Token exchange failed')
                self.signals.auth_error.emit(f"LinkedIn login failed: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error exchanging LinkedIn code for token: {e}")
            self.signals.auth_error.emit(f"LinkedIn login error: {str(e)}")
            return False
    
    def _fetch_user_data(self, access_token: str) -> bool:
        """
        Fetch user data from LinkedIn API.
        
        Args:
            access_token: The access token
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.signals.auth_progress.emit("Getting LinkedIn user information...")
            
            # Get user info
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Get basic profile info
            profile_response = requests.get(
                'https://api.linkedin.com/v2/people/~',
                headers=headers,
                timeout=30
            )
            
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                
                # Get email address
                email_response = requests.get(
                    'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))',
                    headers=headers,
                    timeout=30
                )
                
                email = None
                if email_response.status_code == 200:
                    email_data = email_response.json()
                    elements = email_data.get('elements', [])
                    if elements:
                        email = elements[0].get('handle~', {}).get('emailAddress')
                
                # Extract name information
                first_name = profile_data.get('localizedFirstName', '')
                last_name = profile_data.get('localizedLastName', '')
                full_name = f"{first_name} {last_name}".strip()
                
                # Store user information
                self.auth_data.update({
                    'user_id': profile_data.get('id'),
                    'first_name': first_name,
                    'last_name': last_name,
                    'name': full_name,
                    'email': email,
                    'platform': 'linkedin'
                })
                
                # Save credentials to file
                self._save_credentials()
                
                # Emit success signal
                self.signals.auth_success.emit(self.auth_data)
                logger.info(f"LinkedIn authentication successful for user: {full_name}")
                return True
            else:
                error_msg = profile_response.json().get('message', 'Failed to get user info')
                self.signals.auth_error.emit(f"Failed to get LinkedIn user info: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error fetching LinkedIn user data: {e}")
            self.signals.auth_error.emit(f"Failed to get LinkedIn user info: {str(e)}")
            return False
    
    def _save_credentials(self) -> None:
        """Save credentials to file."""
        try:
            credentials = {
                'access_token': self.auth_data.get('access_token'),
                'user_id': self.auth_data.get('user_id'),
                'name': self.auth_data.get('name'),
                'email': self.auth_data.get('email'),
                'first_name': self.auth_data.get('first_name'),
                'last_name': self.auth_data.get('last_name')
            }
            
            creds_file = os.path.join(const.ROOT_DIR, 'linkedin_credentials.json')
            with open(creds_file, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, indent=4)
            
            logger.info("LinkedIn credentials saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving LinkedIn credentials: {e}")
    
    def get_auth_status(self) -> Dict[str, Any]:
        """
        Get current authentication status.
        
        Returns:
            Dict containing authentication status information
        """
        return {
            'authenticated': bool(self.auth_data.get('access_token')),
            'user_info': {
                'name': self.auth_data.get('name'),
                'email': self.auth_data.get('email'),
                'user_id': self.auth_data.get('user_id')
            } if self.auth_data else None
        }
    
    def logout(self) -> None:
        """Clear authentication data and logout."""
        self.auth_data = {}
        
        # Remove credentials file
        try:
            creds_file = os.path.join(const.ROOT_DIR, 'linkedin_credentials.json')
            if os.path.exists(creds_file):
                os.remove(creds_file)
            logger.info("LinkedIn logout successful")
        except Exception as e:
            logger.error(f"Error during LinkedIn logout: {e}")

# Global instance
linkedin_oauth_handler = LinkedInOAuthHandler() 