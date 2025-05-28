"""
Firebase Authentication Handler for Crow's Eye Platform

This module provides Firebase authentication that can access the same user database
as the Crow's Eye website, allowing users to log in with their website accounts.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from PySide6.QtCore import QObject, Signal

from ...auth.firebase_admin_auth import get_firebase_admin_auth, get_service_account_instructions
from ...config.firebase_config import get_firebase_config, is_firebase_configured

logger = logging.getLogger(__name__)

class FirebaseAuthSignals(QObject):
    """Signals for Firebase authentication process."""
    auth_started = Signal()
    auth_success = Signal(dict)
    auth_error = Signal(str)
    auth_status_update = Signal(str)
    logged_in = Signal(dict)
    user_profile_loaded = Signal(dict)

class FirebaseAuthHandler:
    """
    Handles Firebase authentication for the Crow's Eye platform.
    Integrates with the same Firebase project as the website.
    """
    
    def __init__(self):
        """Initialize the Firebase authentication handler."""
        self.signals = FirebaseAuthSignals()
        self.current_user = None
        self.user_profile = None
        self.firebase_admin = get_firebase_admin_auth()
        self._setup_status = None
        
    def initialize(self) -> bool:
        """
        Initialize Firebase authentication.
        
        Returns:
            bool: True if initialized successfully
        """
        try:
            # Try to initialize Firebase Admin SDK
            if self.firebase_admin.initialize():
                logger.info("✅ Firebase Admin SDK initialized successfully")
                self._setup_status = "admin_sdk"
                return True
            else:
                logger.warning("⚠️ Firebase Admin SDK not available, checking client config...")
                
                # Fall back to checking client configuration
                if is_firebase_configured():
                    logger.info("✅ Firebase client configuration available")
                    self._setup_status = "client_config"
                    return True
                else:
                    logger.error("❌ Firebase not properly configured")
                    self._setup_status = "not_configured"
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error initializing Firebase: {e}")
            self._setup_status = "error"
            return False
    
    def get_setup_status(self) -> Dict[str, Any]:
        """
        Get the current Firebase setup status.
        
        Returns:
            dict: Setup status information
        """
        return {
            'initialized': self._setup_status is not None,
            'setup_type': self._setup_status,
            'admin_sdk_available': self.firebase_admin._initialized,
            'client_config_available': is_firebase_configured(),
            'firebase_config': get_firebase_config()
        }
    
    def authenticate_with_email(self, email: str, password: str = None) -> bool:
        """
        Authenticate user with email (using Firebase Admin SDK).
        Note: Password is not verified with Admin SDK, only user existence.
        
        Args:
            email: User email address
            password: Password (not used with Admin SDK)
            
        Returns:
            bool: True if user found and authenticated
        """
        try:
            self.signals.auth_started.emit()
            self.signals.auth_status_update.emit("Checking user credentials...")
            
            if not self.firebase_admin._initialized:
                error_msg = "Firebase Admin SDK not initialized. Please set up service account."
                logger.error(error_msg)
                self.signals.auth_error.emit(error_msg)
                return False
            
            # Get user data from Firebase
            user_data = self.firebase_admin.authenticate_user(email, password)
            
            if user_data:
                self.current_user = user_data
                self.user_profile = user_data
                
                logger.info(f"✅ User authenticated: {email}")
                self.signals.auth_success.emit(user_data)
                self.signals.logged_in.emit(user_data)
                self.signals.user_profile_loaded.emit(user_data)
                
                return True
            else:
                error_msg = f"User not found or authentication failed: {email}"
                logger.warning(error_msg)
                self.signals.auth_error.emit(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Authentication error: {str(e)}"
            logger.error(error_msg)
            self.signals.auth_error.emit(error_msg)
            return False
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user information by email address.
        
        Args:
            email: User email address
            
        Returns:
            dict: User data or None if not found
        """
        if not self.firebase_admin._initialized:
            logger.error("Firebase Admin SDK not initialized")
            return None
            
        return self.firebase_admin.get_user_by_email(email)
    
    def list_website_users(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        List users from the website (for debugging/admin purposes).
        
        Args:
            max_results: Maximum number of users to return
            
        Returns:
            list: List of user data
        """
        if not self.firebase_admin._initialized:
            logger.error("Firebase Admin SDK not initialized")
            return []
            
        return self.firebase_admin.list_users(max_results)
    
    def check_auth_status(self) -> bool:
        """
        Check if user is currently authenticated.
        
        Returns:
            bool: True if authenticated
        """
        return self.current_user is not None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get current authenticated user.
        
        Returns:
            dict: Current user data or None
        """
        return self.current_user
    
    def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """
        Get current user profile.
        
        Returns:
            dict: User profile data or None
        """
        return self.user_profile
    
    def logout(self) -> None:
        """Log out the current user."""
        self.current_user = None
        self.user_profile = None
        logger.info("User logged out from Firebase")
    
    def get_setup_instructions(self) -> str:
        """
        Get setup instructions for Firebase authentication.
        
        Returns:
            str: Setup instructions
        """
        if self._setup_status == "admin_sdk":
            return "✅ Firebase Admin SDK is set up and ready to use!"
        elif self._setup_status == "client_config":
            return """
⚠️ Firebase client configuration available but Admin SDK not set up.

For full functionality, please set up Firebase Admin SDK:
""" + get_service_account_instructions()
        elif self._setup_status == "not_configured":
            return """
❌ Firebase not configured.

You have two options:

1. Set up Firebase Admin SDK (Recommended):
""" + get_service_account_instructions() + """

2. Or run the Firebase sync script:
   python setup_firebase_sync.py
"""
        else:
            return """
❌ Firebase setup error.

Please check your Firebase configuration and try again.
"""

# Create a singleton instance
firebase_auth_handler = FirebaseAuthHandler() 