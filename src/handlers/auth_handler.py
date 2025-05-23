"""
Authentication handler for Meta API login functionality.
"""
import os
import json
import logging
import webbrowser
import urllib.parse
from typing import Dict, Any, Optional, Callable, List
import requests
from PySide6.QtCore import QObject, Signal
from dotenv import load_dotenv

from ..config import constants as const
from ..utils.api_key_manager import key_manager

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AuthSignals(QObject):
    """Signals for authentication process."""
    auth_started = Signal()
    auth_success = Signal(dict)
    auth_error = Signal(str)
    auth_status_update = Signal(str)
    logged_in = Signal(dict)

class AuthHandler:
    """
    Handles authentication with the Meta Graph API.
    Manages login flow and token retrieval.
    Also checks for Gemini API key.
    """
    
    def __init__(self):
        """Initialize the authentication handler."""
        self.signals = AuthSignals()
        self.auth_data = {}
        self.business_accounts = []
        self.selected_account = None
        self.has_gemini_key = self._check_gemini_key()
    
    def _check_gemini_key(self) -> bool:
        """
        Check if Gemini API key is available.
        
        Returns:
            bool: True if Gemini API key is set, False otherwise
        """
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            logger.warning("No Gemini API key found in environment variables")
            return False
        
        # Check if key is not just a placeholder
        if gemini_key == "your_gemini_api_key_here":
            logger.warning("Gemini API key is set to default placeholder value")
            return False
            
        logger.info("Gemini API key found in environment variables")
        return True
    
    def check_auth_status(self) -> bool:
        """
        Check if the user is authenticated.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        # First check if OAuth authentication exists
        try:
            from .oauth_handler import oauth_handler
            oauth_status = oauth_handler.get_auth_status()
            if oauth_status['is_authenticated'] and oauth_status['selected_account']:
                logger.info("OAuth authentication detected and valid")
                return True
        except Exception as e:
            logger.debug(f"OAuth check failed: {e}")
        
        # Fall back to legacy environment variable check
        if not key_manager.has_required_env_variables():
            # Commenting out the warning to stop the log spam
            # logger.warning("Missing required API keys in environment variables")
            return False
        
        # Check if we can validate the access token
        try:
            # Get credentials from environment variables
            creds = key_manager.get_api_credentials_from_env()
            access_token = creds.get('access_token')
            
            if not access_token:
                logger.warning("No access token available")
                return False
            
            # Validate the token
            if self._validate_access_token(access_token):
                logger.info("Authentication successful - token is valid")
                return True
            else:
                logger.warning("Authentication failed - invalid token")
                return False
        
        except Exception as e:
            logger.error(f"Error checking authentication status: {e}")
            return False
    
    def has_gemini_api_key(self) -> bool:
        """
        Check if Gemini API key is available.
        
        Returns:
            bool: True if Gemini API key is set, False otherwise
        """
        # Refresh check in case it was added since init
        self.has_gemini_key = self._check_gemini_key()
        return self.has_gemini_key
    
    def _validate_access_token(self, access_token: str) -> bool:
        """
        Validate the access token with the Meta Graph API.
        
        Args:
            access_token: The access token to validate
            
        Returns:
            bool: True if the token is valid, False otherwise
        """
        try:
            # Make a request to the debug_token endpoint
            url = f"{const.META_API_BASE_URL}/debug_token"
            params = {
                "input_token": access_token,
                "access_token": access_token
            }
            
            response = requests.get(url, params=params, timeout=const.META_API_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if the token is valid
                if data.get("data", {}).get("is_valid", False):
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error validating access token: {e}")
            return False
    
    def get_business_accounts(self) -> List[Dict[str, Any]]:
        """
        Get list of business accounts associated with the user.
        
        Returns:
            List of business account dictionaries
        """
        try:
            # Get credentials from environment variables
            creds = key_manager.get_api_credentials_from_env()
            access_token = creds.get('access_token')
            
            if not access_token:
                logger.warning("No access token available to get business accounts")
                return []
            
            # Make a request to get user's accounts
            url = f"{const.META_API_BASE_URL}/me/accounts"
            params = {"access_token": access_token}
            
            response = requests.get(url, params=params, timeout=const.META_API_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                accounts = data.get("data", [])
                
                # Filter to only business accounts (pages)
                business_accounts = [
                    account for account in accounts 
                    if account.get("category") and "PERSONAL" not in account.get("category", "").upper()
                ]
                
                self.business_accounts = business_accounts
                return business_accounts
            else:
                logger.error(f"Error getting business accounts: {response.text}")
                return []
        
        except Exception as e:
            logger.error(f"Error getting business accounts: {e}")
            return []
    
    def select_business_account(self, account_id: str) -> bool:
        """
        Select a business account to use.
        
        Args:
            account_id: The ID of the business account to select
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find the account in our list
            account = next((a for a in self.business_accounts if a.get("id") == account_id), None)
            
            if not account:
                logger.error(f"Business account with ID {account_id} not found")
                return False
            
            # Store the selected account
            self.selected_account = account
            
            # Get page access token and update credentials
            page_token = account.get("access_token")
            
            if page_token:
                # Update credentials file with page access token and ID
                with open(const.META_CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                    creds = json.load(f)
                
                creds.update({
                    "facebook_page_id": account_id,
                    "facebook_page_access_token": page_token,
                    "page_name": account.get("name", ""),
                    "page_category": account.get("category", "")
                })
                
                # Save updated credentials
                with open(const.META_CREDENTIALS_FILE, "w", encoding="utf-8") as f:
                    json.dump(creds, f, indent=4)
                
                logger.info(f"Selected business account: {account.get('name')}")
                return True
            else:
                logger.error("Selected account has no page access token")
                return False
        
        except Exception as e:
            logger.error(f"Error selecting business account: {e}")
            return False
    
    def get_selected_account(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected business account."""
        # First check OAuth
        try:
            from .oauth_handler import oauth_handler
            oauth_account = oauth_handler.selected_account
            if oauth_account:
                return oauth_account
        except Exception as e:
            logger.debug(f"OAuth account check failed: {e}")
        
        # Fall back to legacy selected account
        return self.selected_account
    
    def logout(self) -> None:
        """Log out the current user."""
        # Clear OAuth session if it exists
        try:
            from .oauth_handler import oauth_handler
            oauth_handler.logout()
        except Exception as e:
            logger.debug(f"OAuth logout failed: {e}")
        
        # Clear legacy selected account
        self.selected_account = None
        self.business_accounts = []
        
        # Reset credentials file
        try:
            # Don't delete the file, just reset it to default values
            with open(const.META_CREDENTIALS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "use_mock_api_for_testing": True
                }, f, indent=4)
            
            logger.info("Logged out successfully")
        except Exception as e:
            logger.error(f"Error during logout: {e}")

# Create a singleton instance
auth_handler = AuthHandler() 