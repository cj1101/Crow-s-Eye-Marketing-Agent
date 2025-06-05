"""
Admin router for Crow's Eye API.
"""

import os
import sys
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.models.user import User, SubscriptionTier
from src.features.subscription.access_control import Feature
from ..dependencies import get_current_user, require_enterprise

router = APIRouter()


class AccountResponse(BaseModel):
    """Account response model."""
    id: str
    email: str
    username: str
    subscription_tier: str
    status: str
    created_at: str
    last_active: str
    usage_stats: dict


class AccountListResponse(BaseModel):
    """Account list response model."""
    accounts: List[AccountResponse]
    total: int
    page: int
    per_page: int


class CreateAccountRequest(BaseModel):
    """Create account request model."""
    email: str
    username: str
    subscription_tier: str
    send_invite: bool = True


class UpdateAccountRequest(BaseModel):
    """Update account request model."""
    username: Optional[str] = None
    subscription_tier: Optional[str] = None
    status: Optional[str] = None  # active, suspended, inactive


@router.get("/accounts", response_model=AccountListResponse)
async def list_accounts(
    page: int = 1,
    per_page: int = 50,
    status: Optional[str] = None,
    tier: Optional[str] = None,
    current_user: User = Depends(require_enterprise)
):
    """
    List all accounts in the organization.
    
    **Tier Required:** Enterprise only
    
    Provides comprehensive account management for Enterprise customers:
    - View all team member accounts
    - Filter by status and subscription tier
    - Monitor usage and activity
    - Manage permissions and access
    """
    # This is a simplified implementation
    # In production, you'd query your user database with proper pagination
    
    from datetime import datetime, timedelta
    
    # Mock account data
    mock_accounts = []
    for i in range(min(per_page, 20)):  # Return up to 20 mock accounts
        account_id = f"account_{i + (page - 1) * per_page}"
        mock_accounts.append(AccountResponse(
            id=account_id,
            email=f"user{i}@company.com",
            username=f"User {i + 1}",
            subscription_tier="creator" if i % 3 == 0 else "pro_agency",
            status="active" if i % 4 != 0 else "inactive",
            created_at=(datetime.now() - timedelta(days=i * 10)).isoformat(),
            last_active=(datetime.now() - timedelta(hours=i * 2)).isoformat(),
            usage_stats={
                "posts_created": 15 + i * 3,
                "storage_used_gb": 2.5 + i * 0.5,
                "ai_credits_used": 100 + i * 20
            }
        ))
    
    return AccountListResponse(
        accounts=mock_accounts,
        total=100,  # Mock total
        page=page,
        per_page=per_page
    )


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    current_user: User = Depends(require_enterprise)
):
    """
    Get detailed account information.
    
    **Tier Required:** Enterprise only
    """
    # This is a simplified implementation
    # In production, you'd look up the account by ID in your database
    
    from datetime import datetime, timedelta
    
    return AccountResponse(
        id=account_id,
        email="user@company.com",
        username="Sample User",
        subscription_tier="pro_agency",
        status="active",
        created_at=(datetime.now() - timedelta(days=30)).isoformat(),
        last_active=(datetime.now() - timedelta(hours=2)).isoformat(),
        usage_stats={
            "posts_created": 45,
            "storage_used_gb": 8.2,
            "ai_credits_used": 350,
            "team_members": 3,
            "api_calls_this_month": 1250
        }
    )


@router.post("/accounts", response_model=AccountResponse)
async def create_account(
    request: CreateAccountRequest,
    current_user: User = Depends(require_enterprise)
):
    """
    Create a new team member account.
    
    **Tier Required:** Enterprise only
    """
    # This is a simplified implementation
    # In production, you'd create the account in your database and send invites
    
    import uuid
    from datetime import datetime
    
    account_id = str(uuid.uuid4())
    
    # Mock account creation
    return AccountResponse(
        id=account_id,
        email=request.email,
        username=request.username,
        subscription_tier=request.subscription_tier,
        status="pending" if request.send_invite else "active",
        created_at=datetime.now().isoformat(),
        last_active=datetime.now().isoformat(),
        usage_stats={
            "posts_created": 0,
            "storage_used_gb": 0.0,
            "ai_credits_used": 0
        }
    )


@router.put("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    request: UpdateAccountRequest,
    current_user: User = Depends(require_enterprise)
):
    """
    Update account information and permissions.
    
    **Tier Required:** Enterprise only
    """
    # This is a simplified implementation
    # In production, you'd update the account in your database
    
    from datetime import datetime, timedelta
    
    return AccountResponse(
        id=account_id,
        email="user@company.com",
        username=request.username or "Updated User",
        subscription_tier=request.subscription_tier or "pro_agency",
        status=request.status or "active",
        created_at=(datetime.now() - timedelta(days=30)).isoformat(),
        last_active=(datetime.now() - timedelta(hours=1)).isoformat(),
        usage_stats={
            "posts_created": 45,
            "storage_used_gb": 8.2,
            "ai_credits_used": 350
        }
    )


@router.delete("/accounts/{account_id}")
async def delete_account(
    account_id: str,
    current_user: User = Depends(require_enterprise)
):
    """
    Delete/deactivate an account.
    
    **Tier Required:** Enterprise only
    """
    # This is a simplified implementation
    # In production, you'd deactivate the account and handle data retention
    
    return {"message": f"Account {account_id} has been deactivated"}


@router.get("/usage/summary")
async def get_usage_summary(
    current_user: User = Depends(require_enterprise)
):
    """
    Get organization-wide usage summary.
    
    **Tier Required:** Enterprise only
    """
    # Mock usage summary
    return {
        "organization": {
            "total_accounts": 25,
            "active_accounts": 22,
            "total_storage_used_gb": 125.5,
            "total_ai_credits_used": 8500,
            "total_posts_created": 1250
        },
        "current_month": {
            "new_accounts": 3,
            "storage_added_gb": 15.2,
            "ai_credits_consumed": 2100,
            "posts_created": 180
        },
        "top_users": [
            {"username": "Marketing Team Lead", "posts_created": 45, "ai_credits_used": 350},
            {"username": "Content Creator 1", "posts_created": 38, "ai_credits_used": 280},
            {"username": "Social Media Manager", "posts_created": 32, "ai_credits_used": 245}
        ]
    }


@router.get("/billing/usage")
async def get_billing_usage(
    current_user: User = Depends(require_enterprise)
):
    """
    Get detailed billing and usage information.
    
    **Tier Required:** Enterprise only
    """
    # Mock billing data
    return {
        "billing_period": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "days_remaining": 15
        },
        "usage_limits": {
            "accounts": {"used": 25, "limit": 100},
            "storage_gb": {"used": 125.5, "limit": 1000},
            "ai_credits": {"used": 8500, "limit": 50000},
            "api_calls": {"used": 15000, "limit": 100000}
        },
        "overage_charges": {
            "storage": 0.0,
            "ai_credits": 0.0,
            "api_calls": 0.0,
            "total": 0.0
        },
        "projected_usage": {
            "accounts": 28,
            "storage_gb": 145.0,
            "ai_credits": 12000,
            "estimated_overage": 0.0
        }
    }


@router.post("/accounts/{account_id}/reset-password")
async def reset_account_password(
    account_id: str,
    current_user: User = Depends(require_enterprise)
):
    """
    Reset password for a team member account.
    
    **Tier Required:** Enterprise only
    """
    # This is a simplified implementation
    # In production, you'd generate a secure password reset token
    
    return {
        "message": f"Password reset email sent to account {account_id}",
        "reset_token": "mock_reset_token_123",
        "expires_at": "2024-01-01T12:00:00Z"
    } 