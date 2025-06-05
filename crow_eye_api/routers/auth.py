"""
Authentication router for Crow's Eye API.
"""

import os
import sys
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.models.user import User, SubscriptionTier, SubscriptionInfo, UsageStats
from ..dependencies import create_access_token, get_current_user
from datetime import datetime

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """User response model."""
    user_id: str
    email: str
    username: str
    subscription_tier: str
    subscription_status: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login endpoint that returns JWT token.
    
    **Tier Required:** None (public endpoint)
    """
    # For demo purposes, we'll accept any email/password combination
    # In production, you'd validate against your user database
    
    # Create a mock user based on email
    # You can customize the tier based on email for testing
    tier = SubscriptionTier.SPARK  # Default to free tier
    
    # Demo tier assignment based on email
    if "creator" in request.email.lower():
        tier = SubscriptionTier.CREATOR
    elif "pro" in request.email.lower():
        tier = SubscriptionTier.PRO_AGENCY
    elif "enterprise" in request.email.lower():
        tier = SubscriptionTier.ENTERPRISE
    
    user = User(
        user_id=f"user_{hash(request.email) % 10000}",
        email=request.email,
        username=request.email.split("@")[0],
        created_at=datetime.now().isoformat(),
        subscription=SubscriptionInfo(
            tier=tier,
            start_date=datetime.now().isoformat()
        ),
        usage_stats=UsageStats(),
        preferences={}
    )
    
    # Create access token
    access_token = create_access_token(user)
    
    return LoginResponse(
        access_token=access_token,
        user=user.to_dict()
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information.
    
    **Tier Required:** Any authenticated user
    """
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        username=current_user.username,
        subscription_tier=current_user.subscription.tier.value,
        subscription_status=current_user.get_subscription_status()
    )


@router.post("/logout")
async def logout():
    """
    Logout endpoint (client-side token removal).
    
    **Tier Required:** None
    """
    return {"message": "Successfully logged out. Please remove the token from client storage."} 