"""
FastAPI dependencies for Crow's Eye Marketing Platform API.
Provides authentication, authorization, and core service dependencies.
"""

import os
import sys
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import core models and handlers
try:
    from src.models.user import User, SubscriptionTier, user_manager, SubscriptionInfo, UsageStats
    from src.features.subscription.access_control import SubscriptionAccessControl, Feature
    from src.models.app_state import AppState
    from src.handlers.media_handler import MediaHandler
    from src.handlers.crowseye_handler import CrowsEyeHandler
    from src.handlers.library_handler import LibraryManager
    from src.handlers.analytics_handler import AnalyticsHandler
    from src.features.media_processing.video_handler import VideoHandler
    from src.features.media_processing.image_edit_handler import ImageEditHandler
    CORE_IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Core imports not available: {e}")
    CORE_IMPORTS_AVAILABLE = False
    
    # Mock classes for when core imports fail
    class MockUser:
        def __init__(self):
            self.user_id = "mock_user"
            self.email = "test@example.com"
            self.username = "Test User"
            self.subscription = MockSubscription()
    
    class MockSubscription:
        def __init__(self):
            self.tier = "CREATOR"
    
    class MockAppState:
        def __init__(self):
            self.media_generation_status = {}
    
    class MockHandler:
        def __init__(self, *args, **kwargs):
            pass
    
    User = MockUser
    AppState = MockAppState
    MediaHandler = MockHandler
    CrowsEyeHandler = MockHandler
    LibraryManager = MockHandler
    AnalyticsHandler = MockHandler
    VideoHandler = MockHandler
    ImageEditHandler = MockHandler

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "crow-eye-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

security = HTTPBearer()

# Global instances (initialized once)
_app_state = None
_media_handler = None
_crowseye_handler = None
_library_manager = None
_analytics_handler = None
_video_handler = None
_image_edit_handler = None
_access_control = None

def get_app_state() -> AppState:
    """Get or create the global app state instance."""
    global _app_state
    if _app_state is None:
        _app_state = AppState()
    return _app_state

def get_media_handler() -> MediaHandler:
    """Get or create the global media handler instance."""
    global _media_handler
    if _media_handler is None:
        app_state = get_app_state()
        _media_handler = MediaHandler(app_state)
    return _media_handler

def get_library_manager() -> LibraryManager:
    """Get or create the global library manager instance."""
    global _library_manager
    if _library_manager is None:
        _library_manager = LibraryManager()
    return _library_manager

def get_crowseye_handler() -> CrowsEyeHandler:
    """Get or create the global Crow's Eye handler instance."""
    global _crowseye_handler
    if _crowseye_handler is None:
        app_state = get_app_state()
        media_handler = get_media_handler()
        library_manager = get_library_manager()
        _crowseye_handler = CrowsEyeHandler(app_state, media_handler, library_manager)
    return _crowseye_handler

def get_analytics_handler() -> AnalyticsHandler:
    """Get or create the global analytics handler instance."""
    global _analytics_handler
    if _analytics_handler is None:
        _analytics_handler = AnalyticsHandler()
    return _analytics_handler

def get_video_handler() -> VideoHandler:
    """Get or create the global video handler instance."""
    global _video_handler
    if _video_handler is None:
        _video_handler = VideoHandler()
    return _video_handler

def get_image_edit_handler() -> ImageEditHandler:
    """Get or create the global image edit handler instance."""
    global _image_edit_handler
    if _image_edit_handler is None:
        _image_edit_handler = ImageEditHandler()
    return _image_edit_handler

def get_access_control() -> "SubscriptionAccessControl":
    """Get or create the global access control instance.""" 
    global _access_control
    if _access_control is None and CORE_IMPORTS_AVAILABLE:
        _access_control = SubscriptionAccessControl()
    return _access_control

def create_access_token(user: User) -> str:
    """Create JWT access token for user."""
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": user.email,
        "user_id": user.user_id,
        "tier": getattr(user.subscription, 'tier', 'FREE'),
        "exp": expire
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)] = None,
    x_user_api_key: Annotated[Optional[str], Header()] = None
) -> User:
    """Get current authenticated user."""
    
    # For demo purposes, create a test user if no auth provided
    if not credentials and not x_user_api_key:
        return User(
            user_id="demo_user",
            email="demo@crowseye.com",
            username="Demo User",
            created_at=datetime.now().isoformat(),
            subscription=SubscriptionInfo(
                tier=SubscriptionTier.CREATOR if CORE_IMPORTS_AVAILABLE else "CREATOR",
                start_date=datetime.now().isoformat()
            ) if CORE_IMPORTS_AVAILABLE else MockSubscription(),
            usage_stats=UsageStats() if CORE_IMPORTS_AVAILABLE else {},
            preferences={}
        )
    
    # Check for BYO API key (Enterprise feature)
    if x_user_api_key:
        return User(
            user_id="enterprise_user",
            email="enterprise@example.com",
            username="Enterprise User",
            created_at=datetime.now().isoformat(),
            subscription=SubscriptionInfo(
                tier=SubscriptionTier.BUSINESS if CORE_IMPORTS_AVAILABLE else "BUSINESS",
                start_date=datetime.now().isoformat()
            ) if CORE_IMPORTS_AVAILABLE else MockSubscription(),
            usage_stats=UsageStats() if CORE_IMPORTS_AVAILABLE else {},
            preferences={}
        )
    
    # Verify JWT token
    if credentials:
        payload = verify_token(credentials.credentials)
        email = payload.get("sub")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Create user from token data
        user = User(
            user_id=payload.get("user_id", "token_user"),
            email=email,
            username=email.split("@")[0],
            created_at=datetime.now().isoformat(),
            subscription=SubscriptionInfo(
                tier=SubscriptionTier(payload.get("tier", "FREE")) if CORE_IMPORTS_AVAILABLE else payload.get("tier", "FREE"),
                start_date=datetime.now().isoformat()
            ) if CORE_IMPORTS_AVAILABLE else MockSubscription(),
            usage_stats=UsageStats() if CORE_IMPORTS_AVAILABLE else {},
            preferences={}
        )
        
        return user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )

def require_tier(required_tier):
    """Dependency factory for tier requirements."""
    def tier_dependency(current_user: User = Depends(get_current_user)) -> User:
        if not CORE_IMPORTS_AVAILABLE:
            return current_user  # Skip tier checking if imports unavailable
            
        # Check if user has required tier or higher
        tier_hierarchy = {
            "FREE": 0,
            "CREATOR": 1, 
            "PRO": 2,
            "BUSINESS": 3
        }
        
        user_tier_level = tier_hierarchy.get(str(current_user.subscription.tier), 0)
        required_tier_level = tier_hierarchy.get(str(required_tier), 0)
        
        if user_tier_level < required_tier_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {required_tier} tier or higher"
            )
        
        return current_user
    
    return tier_dependency

def require_feature(feature):
    """Dependency factory for feature requirements."""
    def feature_dependency(current_user: User = Depends(get_current_user)) -> User:
        if not CORE_IMPORTS_AVAILABLE:
            return current_user  # Skip feature checking if imports unavailable
            
        access_control = get_access_control()
        if access_control:
            # Set current user in user manager for access control
            if hasattr(user_manager, '_current_user'):
                user_manager._current_user = current_user
            
            if not access_control.has_feature_access(feature):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"This feature is not available in your current subscription tier"
                )
        
        return current_user
    
    return feature_dependency

# Common dependencies
def get_current_user_optional() -> Optional[User]:
    """Get current user without requiring authentication."""
    try:
        return get_current_user()
    except:
        return None

# Service dependencies
def get_services():
    """Get all core services as a dependency."""
    return {
        "app_state": get_app_state(),
        "media_handler": get_media_handler(),
        "crowseye_handler": get_crowseye_handler(),
        "library_manager": get_library_manager(),
        "analytics_handler": get_analytics_handler(),
        "video_handler": get_video_handler(),
        "image_edit_handler": get_image_edit_handler(),
        "core_imports_available": CORE_IMPORTS_AVAILABLE
    } 