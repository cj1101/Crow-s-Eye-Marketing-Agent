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

# Try to import core functionality - use mocks if not available
CORE_IMPORTS_AVAILABLE = False
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
    print("✅ Core dependencies loaded successfully")
except ImportError as e:
    print(f"⚠️  Core imports not available, using mocks: {e}")
    
    # Mock classes for demonstration/fallback purposes
    class MockUser:
        def __init__(self, user_id="demo_user", email="demo@crowseye.com", username="Demo User"):
            self.user_id = user_id
            self.email = email
            self.username = username
            self.subscription = MockSubscription()
            self.created_at = datetime.now().isoformat()
            self.usage_stats = {}
            self.preferences = {}
    
    class MockSubscription:
        def __init__(self, tier="CREATOR"):
            self.tier = tier
            self.start_date = datetime.now().isoformat()
    
    class MockAppState:
        def __init__(self):
            self.media_generation_status = {}
            self.user_sessions = {}
    
    class MockHandler:
        def __init__(self, *args, **kwargs):
            self.initialized = True
    
    # Use mock classes
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

security = HTTPBearer(auto_error=False)

# Global service instances (singleton pattern)
_service_instances = {
    "app_state": None,
    "media_handler": None,
    "crowseye_handler": None,
    "library_manager": None,
    "analytics_handler": None,
    "video_handler": None,
    "image_edit_handler": None,
    "access_control": None
}

def get_app_state() -> AppState:
    """Get or create the global app state instance."""
    if _service_instances["app_state"] is None:
        _service_instances["app_state"] = AppState()
    return _service_instances["app_state"]

def get_media_handler() -> MediaHandler:
    """Get or create the global media handler instance."""
    if _service_instances["media_handler"] is None:
        app_state = get_app_state()
        _service_instances["media_handler"] = MediaHandler(app_state)
    return _service_instances["media_handler"]

def get_library_manager() -> LibraryManager:
    """Get or create the global library manager instance."""
    if _service_instances["library_manager"] is None:
        _service_instances["library_manager"] = LibraryManager()
    return _service_instances["library_manager"]

def get_crowseye_handler() -> CrowsEyeHandler:
    """Get or create the global Crow's Eye handler instance."""
    if _service_instances["crowseye_handler"] is None:
        app_state = get_app_state()
        media_handler = get_media_handler()
        library_manager = get_library_manager()
        _service_instances["crowseye_handler"] = CrowsEyeHandler(app_state, media_handler, library_manager)
    return _service_instances["crowseye_handler"]

def get_analytics_handler() -> AnalyticsHandler:
    """Get or create the global analytics handler instance."""
    if _service_instances["analytics_handler"] is None:
        _service_instances["analytics_handler"] = AnalyticsHandler()
    return _service_instances["analytics_handler"]

def get_video_handler() -> VideoHandler:
    """Get or create the global video handler instance."""
    if _service_instances["video_handler"] is None:
        _service_instances["video_handler"] = VideoHandler()
    return _service_instances["video_handler"]

def get_image_edit_handler() -> ImageEditHandler:
    """Get or create the global image edit handler instance."""
    if _service_instances["image_edit_handler"] is None:
        _service_instances["image_edit_handler"] = ImageEditHandler()
    return _service_instances["image_edit_handler"]

def get_access_control() -> "SubscriptionAccessControl":
    """Get or create the global access control instance.""" 
    if _service_instances["access_control"] is None and CORE_IMPORTS_AVAILABLE:
        _service_instances["access_control"] = SubscriptionAccessControl()
    return _service_instances["access_control"]

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
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)] = None,
    x_user_api_key: Annotated[Optional[str], Header()] = None
) -> User:
    """Get current authenticated user with flexible authentication."""
    
    # For demo/development purposes, create a test user if no auth provided
    if not credentials and not x_user_api_key:
        return User(
            user_id="demo_user",
            email="demo@crowseye.com",
            username="Demo User"
        ) if not CORE_IMPORTS_AVAILABLE else User(
            user_id="demo_user",
            email="demo@crowseye.com",
            username="Demo User",
            created_at=datetime.now().isoformat(),
            subscription=SubscriptionInfo(
                tier=SubscriptionTier.CREATOR,
                start_date=datetime.now().isoformat()
            ),
            usage_stats=UsageStats(),
            preferences={}
        )
    
    # Handle BYO API key (Enterprise feature)
    if x_user_api_key:
        return User(
            user_id="enterprise_user",
            email="enterprise@example.com",
            username="Enterprise User"
        ) if not CORE_IMPORTS_AVAILABLE else User(
            user_id="enterprise_user",
            email="enterprise@example.com", 
            username="Enterprise User",
            created_at=datetime.now().isoformat(),
            subscription=SubscriptionInfo(
                tier=SubscriptionTier.BUSINESS,
                start_date=datetime.now().isoformat()
            ),
            usage_stats=UsageStats(),
            preferences={}
        )
    
    # Handle JWT token authentication
    if credentials:
        token = credentials.credentials
        payload = verify_token(token)
        
        # Get user from token payload
        user_id = payload.get("user_id")
        email = payload.get("sub")
        tier = payload.get("tier", "FREE")
        
        return User(
            user_id=user_id,
            email=email,
            username=f"User_{user_id[-8:]}"
        ) if not CORE_IMPORTS_AVAILABLE else User(
            user_id=user_id,
            email=email,
            username=f"User_{user_id[-8:]}",
            created_at=datetime.now().isoformat(),
            subscription=SubscriptionInfo(
                tier=getattr(SubscriptionTier, tier, SubscriptionTier.FREE),
                start_date=datetime.now().isoformat()
            ),
            usage_stats=UsageStats(),
            preferences={}
        )
    
    # Fallback to demo user
    return User(
        user_id="fallback_user",
        email="fallback@crowseye.com",
        username="Fallback User"
    )

async def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)] = None
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None."""
    try:
        if credentials:
            return await get_current_user(credentials)
        return None
    except HTTPException:
        return None

def require_tier(required_tier: str):
    """Dependency to require a specific subscription tier."""
    async def tier_dependency(current_user: User = Depends(get_current_user)) -> User:
        user_tier = getattr(current_user.subscription, 'tier', 'FREE')
        
        # Define tier hierarchy for comparison
        tier_hierarchy = {
            'FREE': 0,
            'CREATOR': 1,
            'BUSINESS': 2,
            'ENTERPRISE': 3
        }
        
        required_level = tier_hierarchy.get(required_tier, 0)
        user_level = tier_hierarchy.get(user_tier, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {required_tier} tier or higher"
            )
        
        return current_user
    
    return tier_dependency

def require_feature(feature_name: str):
    """Dependency to require access to a specific feature."""
    async def feature_dependency(current_user: User = Depends(get_current_user)) -> User:
        # In demo mode, allow all features
        if not CORE_IMPORTS_AVAILABLE:
            return current_user
            
        access_control = get_access_control()
        if access_control and not access_control.has_access(current_user, feature_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access to {feature_name} is not available in your subscription tier"
            )
        
        return current_user
    
    return feature_dependency

def get_services():
    """Get all initialized service instances."""
    return {
        "app_state": get_app_state(),
        "media_handler": get_media_handler(),
        "crowseye_handler": get_crowseye_handler(),
        "library_manager": get_library_manager(),
        "analytics_handler": get_analytics_handler(),
        "video_handler": get_video_handler(),
        "image_edit_handler": get_image_edit_handler(),
        "access_control": get_access_control(),
        "core_available": CORE_IMPORTS_AVAILABLE
    } 