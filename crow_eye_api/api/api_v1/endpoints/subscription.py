"""
Subscription management endpoints for the Crow's Eye API.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from crow_eye_api.api.api_v1.dependencies import get_current_active_user
from crow_eye_api.database import get_db
from crow_eye_api import models
from crow_eye_api.core import security

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/subscription",
            tags=["Subscription"],
            summary="Get subscription data",
            description="Get current subscription information for authenticated user")
async def get_subscription_data(
    request: Request = None,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get subscription data - Frontend expects this endpoint.
    Returns comprehensive subscription information.
    """
    request_id = getattr(request.state, 'request_id', 'unknown')[:8] if request else 'unknown'
    
    try:
        # Get subscription tier from user (defaulting to free)
        subscription_tier = getattr(current_user, 'subscription_tier', 'free')
        
        # Define subscription plans
        subscription_plans = {
            'free': {
                'name': 'Free Plan',
                'price': 0,
                'billing_cycle': 'monthly',
                'features': {
                    'posts_per_month': 10,
                    'ai_generations': 50,
                    'storage_mb': 100,
                    'platforms': ['twitter', 'linkedin'],
                    'analytics': False,
                    'team_collaboration': False,
                    'priority_support': False
                }
            },
            'pro': {
                'name': 'Pro Plan',
                'price': 29.99,
                'billing_cycle': 'monthly',
                'features': {
                    'posts_per_month': 100,
                    'ai_generations': 500,
                    'storage_mb': 1000,
                    'platforms': ['twitter', 'linkedin', 'facebook', 'instagram'],
                    'analytics': True,
                    'team_collaboration': False,
                    'priority_support': False
                }
            },
            'business': {
                'name': 'Business Plan',
                'price': 99.99,
                'billing_cycle': 'monthly',
                'features': {
                    'posts_per_month': 500,
                    'ai_generations': 2000,
                    'storage_mb': 5000,
                    'platforms': ['twitter', 'linkedin', 'facebook', 'instagram', 'tiktok', 'youtube'],
                    'analytics': True,
                    'team_collaboration': True,
                    'priority_support': True
                }
            }
        }
        
        current_plan = subscription_plans.get(subscription_tier, subscription_plans['free'])
        
        # Calculate subscription dates
        start_date = current_user.created_at if current_user.created_at else datetime.now()
        if subscription_tier == 'free':
            end_date = None
            next_billing_date = None
        else:
            # For paid plans, calculate next billing (dummy logic for now)
            end_date = start_date + timedelta(days=30)
            next_billing_date = end_date
        
        subscription_data = {
            'id': f"sub_{current_user.id}",
            'user_id': str(current_user.id),
            'plan': {
                'id': subscription_tier,
                'name': current_plan['name'],
                'price': current_plan['price'],
                'billing_cycle': current_plan['billing_cycle'],
                'features': current_plan['features']
            },
            'status': 'active',
            'trial': subscription_tier == 'free',
            'subscription_tier': subscription_tier,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'next_billing_date': next_billing_date.isoformat() if next_billing_date else None,
            'auto_renew': subscription_tier != 'free',
            'payment_method': {
                'type': 'free' if subscription_tier == 'free' else 'credit_card',
                'last_four': None if subscription_tier == 'free' else '****',
                'expires': None
            },
            'usage': {
                'posts_this_month': 0,
                'ai_generations_this_month': 0,
                'storage_used_mb': 0
            },
            'limits': current_plan['features']
        }
        
        logger.info(f"Subscription data retrieved successfully [ID: {request_id}] [User: {current_user.id}] [Tier: {subscription_tier}]")
        return {"success": True, "subscription": subscription_data}
        
    except Exception as e:
        logger.error(f"Error getting subscription data [ID: {request_id}]: {str(e)}")
        return {"success": False, "error": "Failed to retrieve subscription information"}

@router.get("/subscription/plans",
            tags=["Subscription"],
            summary="Get available subscription plans",
            description="Get all available subscription plans and their features")
async def get_subscription_plans(request: Request = None):
    """
    Get available subscription plans.
    """
    request_id = getattr(request.state, 'request_id', 'unknown')[:8] if request else 'unknown'
    
    try:
        plans = [
            {
                'id': 'free',
                'name': 'Free Plan',
                'price': 0,
                'billing_cycle': 'monthly',
                'description': 'Perfect for getting started',
                'features': {
                    'posts_per_month': 10,
                    'ai_generations': 50,
                    'storage_mb': 100,
                    'platforms': 2,
                    'analytics': False,
                    'team_collaboration': False,
                    'priority_support': False
                },
                'popular': False
            },
            {
                'id': 'pro',
                'name': 'Pro Plan',
                'price': 29.99,
                'billing_cycle': 'monthly',
                'description': 'For growing content creators',
                'features': {
                    'posts_per_month': 100,
                    'ai_generations': 500,
                    'storage_mb': 1000,
                    'platforms': 4,
                    'analytics': True,
                    'team_collaboration': False,
                    'priority_support': False
                },
                'popular': True
            },
            {
                'id': 'business',
                'name': 'Business Plan',
                'price': 99.99,
                'billing_cycle': 'monthly',
                'description': 'For teams and agencies',
                'features': {
                    'posts_per_month': 500,
                    'ai_generations': 2000,
                    'storage_mb': 5000,
                    'platforms': 6,
                    'analytics': True,
                    'team_collaboration': True,
                    'priority_support': True
                },
                'popular': False
            }
        ]
        
        logger.info(f"Subscription plans retrieved successfully [ID: {request_id}]")
        return {"success": True, "plans": plans}
        
    except Exception as e:
        logger.error(f"Error getting subscription plans [ID: {request_id}]: {str(e)}")
        return {"success": False, "error": "Failed to retrieve subscription plans"} 