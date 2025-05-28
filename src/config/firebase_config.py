"""
Firebase configuration for Crow's Eye Marketing Platform.
Integrates with the Crow's Eye Website authentication system.
"""
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Firebase configuration for Crow's Eye Website integration
FIREBASE_CONFIG = {
    "apiKey": os.getenv("FIREBASE_API_KEY", "your-api-key-here"),
    "authDomain": "crows-eye-website.firebaseapp.com",
    "projectId": "crows-eye-website", 
    "storageBucket": "crows-eye-website.appspot.com",
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", "your-sender-id"),
    "appId": os.getenv("FIREBASE_APP_ID", "your-app-id")
}

def get_firebase_config() -> Dict[str, Any]:
    """
    Get Firebase configuration for authentication.
    
    Returns:
        dict: Firebase configuration
    """
    return FIREBASE_CONFIG.copy()

def is_firebase_configured() -> bool:
    """
    Check if Firebase is properly configured.
    
    Returns:
        bool: True if configured, False otherwise
    """
    config = get_firebase_config()
    
    # Check for placeholder values
    placeholder_values = [
        "your-api-key-here",
        "your-sender-id", 
        "your-app-id"
    ]
    
    for key, value in config.items():
        if value in placeholder_values:
            logger.warning(f"Firebase config has placeholder value for {key}")
            return False
    
    return True

def get_firebase_auth_url() -> str:
    """
    Get the Firebase authentication URL.
    
    Returns:
        str: Authentication URL
    """
    return f"https://{FIREBASE_CONFIG['authDomain']}"

def validate_firebase_connection() -> bool:
    """
    Validate Firebase connection and configuration.
    
    Returns:
        bool: True if connection is valid, False otherwise
    """
    try:
        if not is_firebase_configured():
            logger.error("Firebase is not properly configured")
            return False
        
        # Additional validation could be added here
        # For now, just check configuration
        logger.info("Firebase configuration validated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error validating Firebase connection: {e}")
        return False

# Environment variable mapping for easy setup
REQUIRED_ENV_VARS = {
    "FIREBASE_API_KEY": "Firebase API Key",
    "FIREBASE_MESSAGING_SENDER_ID": "Firebase Messaging Sender ID", 
    "FIREBASE_APP_ID": "Firebase App ID"
}

def check_environment_setup() -> Dict[str, bool]:
    """
    Check if required environment variables are set.
    
    Returns:
        dict: Status of each required environment variable
    """
    status = {}
    
    for env_var, description in REQUIRED_ENV_VARS.items():
        value = os.getenv(env_var)
        status[env_var] = bool(value and value != "your-api-key-here")
        
        if not status[env_var]:
            logger.warning(f"Missing or invalid {description} ({env_var})")
    
    return status

def get_setup_instructions() -> str:
    """
    Get setup instructions for Firebase configuration.
    
    Returns:
        str: Setup instructions
    """
    return """
🔥 Firebase Setup Required

To enable user authentication, please:

1. Go to Firebase Console: https://console.firebase.google.com/
2. Select project: crows-eye-website
3. Get your configuration from Project Settings
4. Set these environment variables:
   - FIREBASE_API_KEY=your_actual_api_key
   - FIREBASE_MESSAGING_SENDER_ID=your_sender_id
   - FIREBASE_APP_ID=your_app_id

5. Or update the Crow's Eye Website .env.local file with real values

See FIREBASE_SETUP_GUIDE.md for detailed instructions.
"""

# Export main configuration
__all__ = [
    'FIREBASE_CONFIG',
    'get_firebase_config', 
    'is_firebase_configured',
    'validate_firebase_connection',
    'check_environment_setup',
    'get_setup_instructions'
] 