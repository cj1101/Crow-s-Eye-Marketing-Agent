"""
Firebase Admin SDK Authentication for Crow's Eye Platform

This module provides server-side authentication using Firebase Admin SDK,
allowing the Python application to access the same user database as the website.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import firebase_admin
    from firebase_admin import credentials, auth, firestore
    FIREBASE_ADMIN_AVAILABLE = True
except ImportError:
    FIREBASE_ADMIN_AVAILABLE = False
    firebase_admin = None
    credentials = None
    auth = None
    firestore = None

logger = logging.getLogger(__name__)

class FirebaseAdminAuth:
    """Firebase Admin SDK authentication manager"""
    
    def __init__(self):
        self.app = None
        self.db = None
        self._initialized = False
        
    def initialize(self, service_account_path: Optional[str] = None) -> bool:
        """
        Initialize Firebase Admin SDK
        
        Args:
            service_account_path: Path to service account JSON file
            
        Returns:
            bool: True if initialized successfully
        """
        if not FIREBASE_ADMIN_AVAILABLE:
            logger.error("Firebase Admin SDK not installed. Run: pip install firebase-admin")
            return False
            
        if self._initialized:
            logger.info("Firebase Admin already initialized")
            return True
            
        try:
            # Try to find service account file
            if not service_account_path:
                service_account_path = self._find_service_account_file()
                
            if service_account_path and Path(service_account_path).exists():
                # Initialize with service account
                cred = credentials.Certificate(service_account_path)
                self.app = firebase_admin.initialize_app(cred, {
                    'projectId': 'crows-eye-website'
                })
                logger.info(f"✅ Firebase Admin initialized with service account: {service_account_path}")
            else:
                # Try to initialize with default credentials (if running on Google Cloud)
                try:
                    cred = credentials.ApplicationDefault()
                    self.app = firebase_admin.initialize_app(cred, {
                        'projectId': 'crows-eye-website'
                    })
                    logger.info("✅ Firebase Admin initialized with default credentials")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize with default credentials: {e}")
                    return False
                    
            # Initialize Firestore
            self.db = firestore.client()
            self._initialized = True
            
            logger.info("🔥 Firebase Admin SDK initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firebase Admin: {e}")
            return False
    
    def _find_service_account_file(self) -> Optional[str]:
        """Find service account JSON file in common locations"""
        possible_paths = [
            "service-account.json",
            "firebase-service-account.json", 
            "crows-eye-website-service-account.json",
            "crows-eye-website-firebase-adminsdk-fbsvc-c8b8b7cac4.json",  # Actual service account file
            os.path.expanduser("~/.config/firebase/service-account.json"),
            os.path.join(os.getcwd(), "config", "service-account.json")
        ]
        
        # Also check for any file matching the pattern *firebase-adminsdk*.json
        import glob
        adminsdk_files = glob.glob("*firebase-adminsdk*.json")
        possible_paths.extend(adminsdk_files)
        
        for path in possible_paths:
            if Path(path).exists():
                logger.info(f"Found service account file: {path}")
                return path
                
        logger.warning("No service account file found in common locations")
        return None
    
    def verify_user_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Firebase ID token
        
        Args:
            id_token: Firebase ID token
            
        Returns:
            dict: Decoded token data or None if invalid
        """
        if not self._initialized:
            logger.error("Firebase Admin not initialized")
            return None
            
        try:
            decoded_token = auth.verify_id_token(id_token)
            logger.info(f"✅ Token verified for user: {decoded_token.get('uid')}")
            return decoded_token
        except Exception as e:
            logger.error(f"❌ Token verification failed: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email address
        
        Args:
            email: User email address
            
        Returns:
            dict: User data or None if not found
        """
        if not self._initialized:
            logger.error("Firebase Admin not initialized")
            return None
            
        try:
            user = auth.get_user_by_email(email)
            return {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'photo_url': user.photo_url,
                'email_verified': user.email_verified,
                'disabled': user.disabled,
                'creation_timestamp': user.user_metadata.creation_timestamp,
                'last_sign_in_timestamp': user.user_metadata.last_sign_in_timestamp
            }
        except Exception as e:
            logger.error(f"❌ Failed to get user by email {email}: {e}")
            return None
    
    def get_user_profile(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile from Firestore
        
        Args:
            uid: User ID
            
        Returns:
            dict: User profile data or None if not found
        """
        if not self._initialized or not self.db:
            logger.error("Firebase Admin not initialized")
            return None
            
        try:
            doc_ref = self.db.collection('users').document(uid)
            doc = doc_ref.get()
            
            if doc.exists:
                profile = doc.to_dict()
                logger.info(f"✅ Retrieved profile for user: {uid}")
                return profile
            else:
                logger.warning(f"❌ No profile found for user: {uid}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get user profile {uid}: {e}")
            return None
    
    def authenticate_user(self, email: str, password: str = None) -> Optional[Dict[str, Any]]:
        """
        Authenticate user (for admin purposes)
        Note: This doesn't verify password, just checks if user exists
        
        Args:
            email: User email
            password: Password (not used in admin SDK)
            
        Returns:
            dict: User data if found
        """
        if not self._initialized:
            logger.error("Firebase Admin not initialized")
            return None
            
        # Get user from Firebase Auth
        user_auth = self.get_user_by_email(email)
        if not user_auth:
            return None
            
        # Get user profile from Firestore
        user_profile = self.get_user_profile(user_auth['uid'])
        
        if user_profile:
            # Combine auth and profile data
            return {
                **user_auth,
                **user_profile
            }
        else:
            # Return just auth data if no profile
            return user_auth
    
    def list_users(self, max_results: int = 10) -> list:
        """
        List users (for debugging)
        
        Args:
            max_results: Maximum number of users to return
            
        Returns:
            list: List of user data
        """
        if not self._initialized:
            logger.error("Firebase Admin not initialized")
            return []
            
        try:
            users = []
            page = auth.list_users(max_results=max_results)
            
            for user in page.users:
                users.append({
                    'uid': user.uid,
                    'email': user.email,
                    'display_name': user.display_name,
                    'email_verified': user.email_verified
                })
                
            logger.info(f"✅ Listed {len(users)} users")
            return users
            
        except Exception as e:
            logger.error(f"❌ Failed to list users: {e}")
            return []

# Global instance
firebase_admin_auth = FirebaseAdminAuth()

def get_firebase_admin_auth() -> FirebaseAdminAuth:
    """Get the global Firebase Admin Auth instance"""
    return firebase_admin_auth

def setup_firebase_admin() -> bool:
    """Setup Firebase Admin SDK"""
    return firebase_admin_auth.initialize()

# Service account setup instructions
def get_service_account_instructions() -> str:
    """Get instructions for setting up service account"""
    return """
🔑 Firebase Service Account Setup

To use Firebase Admin SDK, you need a service account:

1. Go to Firebase Console: https://console.firebase.google.com/
2. Select project: crows-eye-website
3. Go to Project Settings (⚙️) → Service accounts
4. Click "Generate new private key"
5. Download the JSON file
6. Save it as one of these names in your project:
   - service-account.json
   - firebase-service-account.json
   - crows-eye-website-service-account.json

Or set the path in your code:
firebase_admin_auth.initialize('/path/to/service-account.json')

This will allow the Python app to access the same user database as your website!
""" 