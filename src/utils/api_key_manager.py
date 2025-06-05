"""
API Key Manager for handling Meta Graph API keys securely as environment variables.
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from ..config import constants as const

logger = logging.getLogger(__name__)

class APIKeyManager:
    """
    Manages API keys and credentials for the Meta Graph API.
    Handles setting and getting API keys from environment variables.
    """
    
    ENV_VAR_APP_ID = "BREADSMITH_META_APP_ID"
    ENV_VAR_APP_SECRET = "BREADSMITH_META_APP_SECRET"
    ENV_VAR_ACCESS_TOKEN = "BREADSMITH_META_ACCESS_TOKEN"
    
    def __init__(self):
        """Initialize the API key manager."""
        self._load_credentials_file()
    
    def _load_credentials_file(self) -> None:
        """Load any existing credentials from file into memory."""
        try:
            if os.path.exists(const.META_CREDENTIALS_FILE):
                with open(const.META_CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                    self.credentials = json.load(f)
                logger.info("Loaded Meta credentials from file")
            else:
                self.credentials = {}
                logger.info("No Meta credentials file found, starting with empty credentials")
        except Exception as e:
            logger.error(f"Error loading credentials file: {e}")
            self.credentials = {}
    
    def _save_credentials_file(self) -> None:
        """Save credentials to file."""
        try:
            with open(const.META_CREDENTIALS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.credentials, f, indent=4)
            logger.info("Saved Meta credentials to file")
        except Exception as e:
            logger.error(f"Error saving credentials file: {e}")
    
    def get_api_key_from_env(self, key_name: str) -> Optional[str]:
        """Get an API key from environment variables."""
        return os.environ.get(key_name)
    
    def set_api_key_to_env(self, key_name: str, value: str) -> None:
        """Set an API key as an environment variable."""
        os.environ[key_name] = value
        logger.info(f"Set environment variable: {key_name}")
    
    def has_required_env_variables(self) -> bool:
        """Check if all required environment variables are set."""
        required_vars = [
            self.ENV_VAR_APP_ID,
            self.ENV_VAR_APP_SECRET,
            self.ENV_VAR_ACCESS_TOKEN
        ]
        return all(var in os.environ for var in required_vars)
    
    def get_api_credentials_from_env(self) -> Dict[str, str]:
        """Get all API credentials from environment variables."""
        return {
            "app_id": self.get_api_key_from_env(self.ENV_VAR_APP_ID),
            "app_secret": self.get_api_key_from_env(self.ENV_VAR_APP_SECRET),
            "access_token": self.get_api_key_from_env(self.ENV_VAR_ACCESS_TOKEN)
        }
    
    def update_credentials_from_env(self) -> None:
        """Update credentials dictionary from environment variables."""
        env_creds = self.get_api_credentials_from_env()
        if all(env_creds.values()):
            # Update credentials with environment values
            self.credentials.update({
                "app_id": env_creds["app_id"],
                "app_secret": env_creds["app_secret"],
                "access_token": env_creds["access_token"]
            })
            # Save to file
            self._save_credentials_file()
            logger.info("Updated credentials from environment variables")
    
    def get_instructions(self) -> str:
        """Get instructions for setting up the API key."""
        return """
To use the Meta Graph API with this application, you need to:

1. Create a Meta Developer Account at https://developers.facebook.com/
2. Register a new app for your business
3. Add products: Instagram Graph API and Facebook Login
4. Configure app settings and permissions
5. Generate an access token with the required permissions

Once you have your API keys, set them as environment variables:

On Windows:
setx BREADSMITH_META_APP_ID "your_app_id"
setx BREADSMITH_META_APP_SECRET "your_app_secret"
setx BREADSMITH_META_ACCESS_TOKEN "your_access_token"

On macOS/Linux:
export BREADSMITH_META_APP_ID="your_app_id"
export BREADSMITH_META_APP_SECRET="your_app_secret"
export BREADSMITH_META_ACCESS_TOKEN="your_access_token"

Then restart the application.
"""

# Create a singleton instance
key_manager = APIKeyManager() 