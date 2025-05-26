"""
OAuth handler for X (Twitter) API authentication.
Provides a modern, user-friendly login experience using X's OAuth 2.0 flow.
"""
import os
import json
import logging
import secrets
import hashlib
import base64
import urllib.parse
from typing import Dict, Any, Optional
import requests
from PySide6.QtCore import QObject, Signal
import webbrowser

from ..config import constants as const

logger = logging.getLogger(__name__)

class XOAuthSignals(QObject):
    """Signals for X OAuth authentication process."""
    auth_started = Signal()
    auth_success = Signal(dict)
    auth_error = Signal(str)
    auth_progress = Signal(str)

class XOAuthHandler:
    """
    Modern OAuth 2.0 handler for X (Twitter) API authentication.
    Provides a streamlined login experience without manual credential entry.
    """
    
    def __init__(self):
        """Initialize the X OAuth handler."""
        self.signals = XOAuthSignals()
        self.auth_data = {}
        
        # OAuth configuration - these would be configured per deployment
        self.client_id = os.getenv("X_CLIENT_ID", "your_x_client_id")
        self.client_secret = os.getenv("X_CLIENT_SECRET", "your_x_client_secret")
        self.redirect_uri = "https://localhost:8080/auth/x/callback"
        
        # X OAuth URLs
        self.auth_base_url = "https://twitter.com/i/oauth2/authorize"
        self.token_url = "https://api.twitter.com/2/oauth2/token"
        
        # Required scopes for X functionality
        self.required_scopes = [
            "tweet.read",
            "tweet.write",
            "users.read",
            "offline.access"
        ]
        
        # PKCE parameters for security
        self.code_verifier = None
        self.code_challenge = None
        self.state = None
        
    def _generate_pkce_params(self) -> None:
        """Generate PKCE parameters for secure OAuth flow."""
        # Generate code verifier (random string)
        self.code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Generate code challenge (SHA256 hash of verifier)
        challenge_bytes = hashlib.sha256(self.code_verifier.encode('utf-8')).digest()
        self.code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
        
        # Generate state parameter for CSRF protection
        self.state = secrets.token_urlsafe(32)
        
    def start_oauth_flow(self) -> str:
        """
        Start the OAuth flow and return the authorization URL.
        
        Returns:
            str: The authorization URL for the user to visit
        """
        try:
            self._generate_pkce_params()
            
            # Build authorization URL
            params = {
                'response_type': 'code',
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'scope': ' '.join(self.required_scopes),
                'state': self.state,
                'code_challenge': self.code_challenge,
                'code_challenge_method': 'S256'
            }
            
            auth_url = f"{self.auth_base_url}?{urllib.parse.urlencode(params)}"
            
            self.signals.auth_started.emit()
            self.signals.auth_progress.emit("Starting X login...")
            
            logger.info("X OAuth flow started")
            return auth_url
            
        except Exception as e:
            logger.error(f"Error starting X OAuth flow: {e}")
            self.signals.auth_error.emit(f"Failed to start X login: {str(e)}")
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
                self.signals.auth_error.emit(f"X login failed: {error_msg}")
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
            logger.error(f"Error handling X OAuth callback: {e}")
            self.signals.auth_error.emit(f"X login error: {str(e)}")
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
            self.signals.auth_progress.emit("Getting X access token...")
            
            # Prepare token request
            token_data = {
                'code': auth_code,
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'code_verifier': self.code_verifier
            }
            
            # Prepare headers
            auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            headers = {
                'Authorization': f'Basic {auth_header}',
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
                        'expires_in': token_response.get('expires_in'),
                        'refresh_token': token_response.get('refresh_token')
                    }
                    
                    # Get user info
                    return self._fetch_user_data(access_token)
                else:
                    self.signals.auth_error.emit("No access token received from X.")
                    return False
            else:
                error_msg = response.json().get('error_description', 'Token exchange failed')
                self.signals.auth_error.emit(f"X login failed: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error exchanging X code for token: {e}")
            self.signals.auth_error.emit(f"X login error: {str(e)}")
            return False
    
    def _fetch_user_data(self, access_token: str) -> bool:
        """
        Fetch user data from X API.
        
        Args:
            access_token: The access token
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.signals.auth_progress.emit("Getting X user information...")
            
            # Get user info
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://api.twitter.com/2/users/me',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                user_data = response.json()
                user_info = user_data.get('data', {})
                
                # Store user information
                self.auth_data.update({
                    'user_id': user_info.get('id'),
                    'username': user_info.get('username'),
                    'name': user_info.get('name'),
                    'platform': 'x'
                })
                
                # Save credentials to file
                self._save_credentials()
                
                # Emit success signal
                self.signals.auth_success.emit(self.auth_data)
                logger.info(f"X authentication successful for user: {user_info.get('username')}")
                return True
            else:
                error_msg = response.json().get('detail', 'Failed to get user info')
                self.signals.auth_error.emit(f"Failed to get X user info: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error fetching X user data: {e}")
            self.signals.auth_error.emit(f"Failed to get X user info: {str(e)}")
            return False
    
    def _save_credentials(self) -> None:
        """Save credentials to file."""
        try:
            credentials = {
                'access_token': self.auth_data.get('access_token'),
                'refresh_token': self.auth_data.get('refresh_token'),
                'user_id': self.auth_data.get('user_id'),
                'username': self.auth_data.get('username'),
                'name': self.auth_data.get('name')
            }
            
            creds_file = os.path.join(const.ROOT_DIR, 'x_credentials.json')
            with open(creds_file, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, indent=4)
            
            logger.info("X credentials saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving X credentials: {e}")
    
    def get_auth_status(self) -> Dict[str, Any]:
        """
        Get current authentication status.
        
        Returns:
            Dict containing authentication status information
        """
        return {
            'authenticated': bool(self.auth_data.get('access_token')),
            'user_info': {
                'username': self.auth_data.get('username'),
                'name': self.auth_data.get('name'),
                'user_id': self.auth_data.get('user_id')
            } if self.auth_data else None
        }
    
    def logout(self) -> None:
        """Clear authentication data and logout."""
        self.auth_data = {}
        
        # Remove credentials file
        try:
            creds_file = os.path.join(const.ROOT_DIR, 'x_credentials.json')
            if os.path.exists(creds_file):
                os.remove(creds_file)
            logger.info("X logout successful")
        except Exception as e:
            logger.error(f"Error during X logout: {e}")

# Global instance
x_oauth_handler = XOAuthHandler() 