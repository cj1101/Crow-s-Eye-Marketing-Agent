"""
FastAPI dependencies for authentication and authorization.
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

from src.models.user import User, SubscriptionTier, user_manager
from src.features.subscription.access_control import SubscriptionAccessControl, Feature

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "crow-eye-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

security = HTTPBearer()
access_control = SubscriptionAccessControl()


def create_access_token(user: User) -> str:
    """Create JWT access token for user."""
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": user.email,
        "user_id": user.user_id,
        "tier": user.subscription.tier.value,
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
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    x_user_api_key: Annotated[Optional[str], Header()] = None
) -> User:
    """Get current authenticated user."""
    
    # Check for BYO API key (Enterprise feature)
    if x_user_api_key:
        # For BYO key users, we need to validate the key and return enterprise user
        # This is a simplified implementation - in production you'd validate against a database
        enterprise_user = User(
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
        return enterprise_user
    
    # Verify JWT token
    payload = verify_token(credentials.credentials)
    email = payload.get("sub")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from user manager
    # For now, we'll create a mock user based on token data
    # In production, you'd fetch from database
    user = User(
        user_id=payload.get("user_id", "mock_user"),
        email=email,
        username=email.split("@")[0],
        created_at=datetime.now().isoformat(),
        subscription=SubscriptionInfo(
            tier=SubscriptionTier(payload.get("tier", "free")),
            start_date=datetime.now().isoformat()
        ),
        usage_stats=UsageStats(),
        preferences={}
    )
    
    return user


def require_tier(required_tier: SubscriptionTier):
    """Dependency factory for tier requirements."""
    def tier_dependency(current_user: User = Depends(get_current_user)) -> User:
        # Check if user has required tier or higher
        tier_hierarchy = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.CREATOR: 1,
            SubscriptionTier.PRO: 2,
            SubscriptionTier.BUSINESS: 3
        }
        
        user_tier_level = tier_hierarchy.get(current_user.subscription.tier, 0)
        required_tier_level = tier_hierarchy.get(required_tier, 0)
        
        if user_tier_level < required_tier_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {required_tier.value} tier or higher"
            )
        
        return current_user
    
    return tier_dependency


def require_feature(feature: Feature):
    """Dependency factory for feature requirements."""
    def feature_dependency(current_user: User = Depends(get_current_user)) -> User:
        # Set current user in user manager for access control
        user_manager._current_user = current_user
        
        if not access_control.has_feature_access(feature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature is not available in your current subscription tier"
            )
        
        return current_user
    
    return feature_dependency


# Common tier dependencies
require_free = require_tier(SubscriptionTier.FREE)
require_creator = require_tier(SubscriptionTier.CREATOR)
require_pro = require_tier(SubscriptionTier.PRO)
require_business = require_tier(SubscriptionTier.BUSINESS)

# Import missing classes
from src.models.user import SubscriptionInfo, UsageStats 