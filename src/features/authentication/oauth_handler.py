"""
OAuth handler for streamlined Meta API authentication.
Provides a modern, user-friendly login experience using Meta's OAuth 2.0 flow.
"""
import os
import json
import logging
import secrets
import hashlib
import base64
import urllib.parse
from typing import Dict, Any, Optional, Callable
import requests
from PySide6.QtCore import QObject, Signal, QUrl, QTimer
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QProgressBar
from PySide6.QtCore import Qt
import webbrowser

from ...config import constants as const

logger = logging.getLogger(__name__)

class OAuthSignals(QObject):
    """Signals for OAuth authentication process."""
    auth_started = Signal()
    auth_success = Signal(dict)
    auth_error = Signal(str)
    auth_progress = Signal(str)
    account_selected = Signal(dict)

class OAuthHandler:
    """
    Modern OAuth 2.0 handler for Meta Graph API authentication.
    Provides a streamlined login experience without manual credential entry.
    """
    
    def __init__(self):
        """Initialize the OAuth handler."""
        self.signals = OAuthSignals()
        self.auth_data = {}
        self.business_accounts = []
        self.selected_account = None
        
        # OAuth configuration - these would typically be configured per deployment
        self.client_id = os.getenv("META_APP_ID", "your_meta_app_id")
        self.client_secret = os.getenv("META_APP_SECRET", "your_meta_app_secret")
        self.redirect_uri = "https://localhost:8080/auth/callback"  # Local development
        
        # OAuth URLs
        self.auth_base_url = "https://www.facebook.com/v18.0/dialog/oauth"
        self.token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        
        # Required permissions for Crow's Eye functionality
        self.required_scopes = [
            "pages_manage_posts",
            "pages_read_engagement", 
            "instagram_basic",
            "instagram_content_publish",
            "instagram_manage_comments",
            "business_management"
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
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'scope': ','.join(self.required_scopes),
                'response_type': 'code',
                'state': self.state,
                'code_challenge': self.code_challenge,
                'code_challenge_method': 'S256'
            }
            
            auth_url = f"{self.auth_base_url}?{urllib.parse.urlencode(params)}"
            
            self.signals.auth_started.emit()
            self.signals.auth_progress.emit("Starting OAuth flow...")
            
            logger.info("OAuth flow started")
            return auth_url
            
        except Exception as e:
            logger.error(f"Error starting OAuth flow: {e}")
            self.signals.auth_error.emit(f"Failed to start login: {str(e)}")
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
                self.signals.auth_error.emit(f"Login failed: {error_msg}")
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
            logger.error(f"Error handling OAuth callback: {e}")
            self.signals.auth_error.emit(f"Login error: {str(e)}")
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
            self.signals.auth_progress.emit("Exchanging code for access token...")
            
            # Prepare token request
            token_params = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'code': auth_code,
                'code_verifier': self.code_verifier
            }
            
            # Make token request
            response = requests.post(self.token_url, data=token_params, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Store access token
                access_token = token_data.get('access_token')
                if access_token:
                    self.auth_data = {
                        'access_token': access_token,
                        'token_type': token_data.get('token_type', 'Bearer'),
                        'expires_in': token_data.get('expires_in')
                    }
                    
                    # Get user info and business accounts
                    return self._fetch_user_data(access_token)
                else:
                    self.signals.auth_error.emit("No access token received.")
                    return False
            else:
                error_msg = response.json().get('error', {}).get('message', 'Token exchange failed')
                self.signals.auth_error.emit(f"Login failed: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            self.signals.auth_error.emit(f"Token exchange failed: {str(e)}")
            return False
    
    def _fetch_user_data(self, access_token: str) -> bool:
        """
        Fetch user data and business accounts.
        
        Args:
            access_token: The user's access token
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.signals.auth_progress.emit("Loading your business accounts...")
            
            # Get user's pages/business accounts
            pages_url = f"{const.META_API_BASE_URL}/me/accounts"
            params = {
                'access_token': access_token,
                'fields': 'id,name,category,access_token,instagram_business_account'
            }
            
            response = requests.get(pages_url, params=params, timeout=30)
            
            if response.status_code == 200:
                pages_data = response.json()
                self.business_accounts = pages_data.get('data', [])
                
                # Filter to only business pages (not personal)
                self.business_accounts = [
                    page for page in self.business_accounts 
                    if page.get('category') and 'PERSONAL' not in page.get('category', '').upper()
                ]
                
                if self.business_accounts:
                    # Auto-select first account or let user choose
                    if len(self.business_accounts) == 1:
                        return self._select_business_account(self.business_accounts[0])
                    else:
                        # Multiple accounts - let user choose
                        self.signals.auth_success.emit({
                            'user_token': access_token,
                            'business_accounts': self.business_accounts,
                            'requires_account_selection': True
                        })
                        return True
                else:
                    self.signals.auth_error.emit("No business accounts found. Please ensure you have a Facebook Page or Instagram Business account.")
                    return False
            else:
                self.signals.auth_error.emit("Failed to load business accounts.")
                return False
                
        except Exception as e:
            logger.error(f"Error fetching user data: {e}")
            self.signals.auth_error.emit(f"Failed to load account data: {str(e)}")
            return False
    
    def _select_business_account(self, account: Dict[str, Any]) -> bool:
        """
        Select and configure a business account.
        
        Args:
            account: The business account data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.selected_account = account
            page_access_token = account.get('access_token')
            page_id = account.get('id')
            
            # Get Instagram Business Account ID if available
            instagram_account_id = None
            if 'instagram_business_account' in account:
                instagram_account_id = account['instagram_business_account'].get('id')
            
            # Save credentials to file for other parts of the app
            credentials = {
                'app_id': self.client_id,
                'app_secret': self.client_secret,
                'access_token': self.auth_data['access_token'],
                'facebook_page_id': page_id,
                'facebook_page_access_token': page_access_token,
                'page_name': account.get('name', ''),
                'page_category': account.get('category', ''),
                'use_mock_api_for_testing': False
            }
            
            if instagram_account_id:
                credentials['instagram_business_account_id'] = instagram_account_id
            
            # Save to credentials file
            with open(const.META_CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, indent=4)
            
            # Set environment variables for compatibility
            os.environ['BREADSMITH_META_APP_ID'] = self.client_id
            os.environ['BREADSMITH_META_APP_SECRET'] = self.client_secret
            os.environ['BREADSMITH_META_ACCESS_TOKEN'] = self.auth_data['access_token']
            
            # Emit success signal
            self.signals.account_selected.emit(account)
            self.signals.auth_success.emit({
                'account': account,
                'credentials': credentials,
                'requires_account_selection': False
            })
            
            logger.info(f"Successfully authenticated with account: {account.get('name')}")
            return True
            
        except Exception as e:
            logger.error(f"Error selecting business account: {e}")
            self.signals.auth_error.emit(f"Failed to configure account: {str(e)}")
            return False
    
    def select_account(self, account_id: str) -> bool:
        """
        Select a specific business account from the available options.
        
        Args:
            account_id: The ID of the account to select
            
        Returns:
            bool: True if successful, False otherwise
        """
        account = next((acc for acc in self.business_accounts if acc.get('id') == account_id), None)
        if account:
            return self._select_business_account(account)
        else:
            self.signals.auth_error.emit("Selected account not found.")
            return False
    
    def get_auth_status(self) -> Dict[str, Any]:
        """
        Get current authentication status.
        
        Returns:
            dict: Authentication status information
        """
        return {
            'is_authenticated': bool(self.auth_data.get('access_token')),
            'selected_account': self.selected_account,
            'business_accounts': self.business_accounts
        }
    
    def logout(self) -> None:
        """Log out and clear all authentication data."""
        try:
            # Clear OAuth data
            self.auth_data = {}
            self.business_accounts = []
            self.selected_account = None
            
            # Clear PKCE parameters
            self.code_verifier = None
            self.code_challenge = None
            self.state = None
            
            # Reset credentials file
            with open(const.META_CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
                json.dump({'use_mock_api_for_testing': True}, f, indent=4)
            
            # Clear environment variables
            for var in ['BREADSMITH_META_APP_ID', 'BREADSMITH_META_APP_SECRET', 'BREADSMITH_META_ACCESS_TOKEN']:
                if var in os.environ:
                    del os.environ[var]
            
            logger.info("Successfully logged out")
            
        except Exception as e:
            logger.error(f"Error during logout: {e}")

# Create singleton instance
oauth_handler = OAuthHandler() 