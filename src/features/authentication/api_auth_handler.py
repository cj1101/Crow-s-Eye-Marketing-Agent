"""
API Authentication Handler
Handles authentication with the Crow's Eye backend API
"""

import logging
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QMessageBox

from ...api.crows_eye_api_client import api_client
from ...config import constants as const

logger = logging.getLogger(__name__)

class APIAuthHandler(QObject):
    """
    Handles authentication with the Crow's Eye backend API.
    """
    
    # Signals
    auth_started = Signal()
    auth_success = Signal(dict)
    auth_error = Signal(str)
    auth_status_update = Signal(str)
    logged_in = Signal(dict)
    logged_out = Signal()
    subscription_updated = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.auth_token = None
        self.is_authenticated = False
        
        # Auto-refresh timer for token validation
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.validate_session)
        
        # Load saved authentication if available
        self.load_saved_auth()
    
    def login(self, email: str, password: str) -> None:
        """
        Login user with email and password.
        
        Args:
            email: User's email address
            password: User's password
        """
        try:
            self.auth_started.emit()
            self.auth_status_update.emit("Authenticating...")
            
            # Call API login
            result = api_client.login(email, password)
            
            if result.get("success"):
                # Extract user data and token
                self.auth_token = result.get("access_token")
                self.current_user = result.get("user_data", {})
                self.is_authenticated = True
                
                # Validate user data
                if not self.current_user or not self.current_user.get("email"):
                    logger.error("Login successful but user data is missing")
                    self.auth_error.emit("Login successful but user data is missing")
                    return
                
                # Save authentication data
                self.save_auth_data()
                
                # Start refresh timer (validate session every 30 minutes)
                self.refresh_timer.start(30 * 60 * 1000)
                
                # Emit success signals
                self.auth_success.emit(self.current_user)
                self.logged_in.emit(self.current_user)
                
                logger.info(f"User logged in successfully: {self.current_user.get('email')}")
                
            else:
                error_msg = result.get("error", "Login failed")
                self.auth_error.emit(error_msg)
                logger.error(f"Login failed: {error_msg}")
                
        except Exception as e:
            error_msg = f"Login error: {str(e)}"
            self.auth_error.emit(error_msg)
            logger.error(error_msg)
    
    def register(self, email: str, password: str, name: str = "") -> None:
        """
        Register a new user account.
        
        Args:
            email: User's email address
            password: User's password
            name: User's full name (optional)
        """
        try:
            self.auth_started.emit()
            self.auth_status_update.emit("Creating account...")
            
            # Call API register
            result = api_client.register(email, password, name)
            
            if result.get("success"):
                # Auto-login after successful registration
                self.login(email, password)
                
            else:
                error_msg = result.get("error", "Registration failed")
                self.auth_error.emit(error_msg)
                logger.error(f"Registration failed: {error_msg}")
                
        except Exception as e:
            error_msg = f"Registration error: {str(e)}"
            self.auth_error.emit(error_msg)
            logger.error(error_msg)
    
    def logout(self) -> None:
        """Logout the current user."""
        try:
            # Clear authentication data
            self.current_user = None
            self.auth_token = None
            self.is_authenticated = False
            
            # Stop refresh timer
            self.refresh_timer.stop()
            
            # Clear API client token
            api_client.logout()
            
            # Clear saved auth data
            self.clear_saved_auth()
            
            # Emit logout signal
            self.logged_out.emit()
            
            logger.info("User logged out successfully")
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
    
    def validate_session(self) -> None:
        """Validate the current session with the API."""
        if not self.is_authenticated:
            return
        
        try:
            result = api_client.get_current_user()
            
            if result.get("success"):
                # Update user data
                self.current_user = result
                logger.debug("Session validated successfully")
                
                # Check for subscription updates
                self.check_subscription_status()
                
            else:
                # Session is invalid, logout
                logger.warning("Session validation failed, logging out")
                self.logout()
                
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
    
    def check_subscription_status(self) -> None:
        """Check and update subscription status."""
        try:
            result = api_client.get_subscription_status()
            
            if result.get("success"):
                subscription_data = result.get("subscription", {})
                
                # Update current user with subscription info
                if self.current_user:
                    self.current_user["subscription"] = subscription_data
                
                # Emit subscription update signal
                self.subscription_updated.emit(subscription_data)
                
        except Exception as e:
            logger.error(f"Subscription check error: {str(e)}")
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user data."""
        return self.current_user
    
    def get_auth_token(self) -> Optional[str]:
        """Get current authentication token."""
        return self.auth_token
    
    def is_user_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return self.is_authenticated
    
    def get_user_subscription_tier(self) -> str:
        """Get user's subscription tier."""
        if not self.current_user:
            return "unenrolled"
        
        subscription = self.current_user.get("subscription", {})
        return subscription.get("tier", "unenrolled")
    
    def update_subscription(self, plan: str) -> None:
        """
        Update user's subscription plan.
        
        Args:
            plan: New subscription plan (payg, creator, growth, pro)
        """
        try:
            self.auth_status_update.emit(f"Updating subscription to {plan}...")
            
            result = api_client.update_subscription(plan)
            
            if result.get("success"):
                # Refresh user data and subscription status
                self.validate_session()
                self.auth_status_update.emit("Subscription updated successfully!")
                
            else:
                error_msg = result.get("error", "Subscription update failed")
                self.auth_error.emit(error_msg)
                
        except Exception as e:
            error_msg = f"Subscription update error: {str(e)}"
            self.auth_error.emit(error_msg)
            logger.error(error_msg)
    
    def save_auth_data(self) -> None:
        """Save authentication data to local storage."""
        try:
            auth_data = {
                "token": self.auth_token,
                "user": self.current_user,
                "timestamp": datetime.now().isoformat()
            }
            
            auth_file = os.path.join(const.DATA_DIR, "auth_session.json")
            os.makedirs(os.path.dirname(auth_file), exist_ok=True)
            
            with open(auth_file, "w", encoding="utf-8") as f:
                json.dump(auth_data, f, indent=2)
                
            logger.debug("Authentication data saved")
            
        except Exception as e:
            logger.error(f"Failed to save auth data: {str(e)}")
    
    def load_saved_auth(self) -> None:
        """Load saved authentication data."""
        try:
            auth_file = os.path.join(const.DATA_DIR, "auth_session.json")
            
            if not os.path.exists(auth_file):
                return
            
            with open(auth_file, "r", encoding="utf-8") as f:
                auth_data = json.load(f)
            
            # Check if auth data is recent (within 24 hours)
            timestamp_str = auth_data.get("timestamp")
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str)
                if (datetime.now() - timestamp).total_seconds() > 24 * 60 * 60:
                    logger.info("Saved auth data is too old, ignoring")
                    return
            
            # Restore authentication state
            self.auth_token = auth_data.get("token")
            self.current_user = auth_data.get("user")
            
            if self.auth_token and self.current_user:
                # Set token in API client
                api_client.token = self.auth_token
                api_client.session.headers['Authorization'] = f'Bearer {self.auth_token}'
                
                self.is_authenticated = True
                
                # Validate session
                self.validate_session()
                
                # Start refresh timer
                self.refresh_timer.start(30 * 60 * 1000)
                
                # Emit logged in signal
                self.logged_in.emit(self.current_user)
                
                logger.info("Restored authentication session")
            
        except Exception as e:
            logger.error(f"Failed to load saved auth data: {str(e)}")
            self.clear_saved_auth()
    
    def clear_saved_auth(self) -> None:
        """Clear saved authentication data."""
        try:
            auth_file = os.path.join(const.DATA_DIR, "auth_session.json")
            if os.path.exists(auth_file):
                os.remove(auth_file)
                logger.debug("Cleared saved auth data")
                
        except Exception as e:
            logger.error(f"Failed to clear saved auth data: {str(e)}")
    
    def show_subscription_required_dialog(self, parent=None) -> bool:
        """
        Show subscription required dialog.
        
        Returns:
            bool: True if user wants to upgrade, False otherwise
        """
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle("Subscription Required")
        msg_box.setText("This feature requires a subscription.")
        msg_box.setDetailedText(
            "Available plans:\n\n"
            "💳 Pay-As-You-Go ($5 minimum): Pay only for what you use\n"
            "✨ Creator Plan ($15/month): For content creators\n"
            "🚀 Growth Plan ($20/month): For growing businesses\n"
            "💎 Pro Plan ($30/month): For professionals\n"
            "\nWould you like to upgrade your subscription?"
        )
        
        upgrade_btn = msg_box.addButton("Upgrade", QMessageBox.ButtonRole.AcceptRole)
        cancel_btn = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        
        msg_box.exec()
        
        return msg_box.clickedButton() == upgrade_btn

# Global authentication handler instance
api_auth_handler = APIAuthHandler() 