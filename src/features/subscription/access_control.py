"""
Subscription access control system for Crow's Eye Marketing Platform.
Enforces feature limitations based on user subscription tiers.
"""
import logging
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from functools import wraps

from ...models.user import user_manager, SubscriptionTier

logger = logging.getLogger(__name__)

class FeatureCategory(Enum):
    """Feature categories for access control."""
    CORE = "core"                    # Always available
    FREE = "free"                    # Available in Free tier and above
    CREATOR = "creator"              # Available in Creator tier and above
    PRO = "pro"                      # Available in Pro tier and above
    BUSINESS = "business"            # Business only features

class Feature(Enum):
    """Available features in the platform."""
    # Core features (always available)
    BASIC_UI = "basic_ui"
    SETTINGS = "settings"
    HELP = "help"
    
    # Free tier features
    MEDIA_LIBRARY = "media_library"
    BASIC_IMAGE_EDITING = "basic_image_editing"
    BASIC_ANALYTICS = "basic_analytics"
    COMMUNITY_SUPPORT = "community_support"
    
    # Creator tier features ($19/month)
    SMART_GALLERY_GENERATOR = "smart_gallery_generator"
    POST_FORMATTING = "post_formatting"
    BASIC_VIDEO_PROCESSING = "basic_video_processing"
    EMAIL_SUPPORT = "email_support"
    
    # Pro tier features ($50/month)
    FULL_VIDEO_EDITING_SUITE = "full_video_editing_suite"
    VEO_VIDEO_GENERATOR = "veo_video_generator"
    HIGHLIGHT_REEL_GENERATOR = "highlight_reel_generator"
    STORY_ASSISTANT = "story_assistant"
    BULK_OPERATIONS = "bulk_operations"
    AUDIO_IMPORTER = "audio_importer"
    ADVANCED_ANALYTICS = "advanced_analytics"
    PERFORMANCE_ANALYTICS = "performance_analytics"
    TEAM_COLLABORATION = "team_collaboration"
    PRIORITY_SUPPORT = "priority_support"
    
    # Business tier features (custom pricing)
    ADVANCED_TEAM_COLLABORATION = "advanced_team_collaboration"
    CUSTOM_ANALYTICS = "custom_analytics"
    CUSTOM_BRANDING = "custom_branding"
    API_ACCESS = "api_access"
    DEDICATED_ACCOUNT_MANAGER = "dedicated_account_manager"

# Feature access mapping
FEATURE_ACCESS = {
    # Core features
    Feature.BASIC_UI: FeatureCategory.CORE,
    Feature.SETTINGS: FeatureCategory.CORE,
    Feature.HELP: FeatureCategory.CORE,
    
    # Free tier features
    Feature.MEDIA_LIBRARY: FeatureCategory.FREE,
    Feature.BASIC_IMAGE_EDITING: FeatureCategory.FREE,
    Feature.BASIC_ANALYTICS: FeatureCategory.FREE,
    Feature.COMMUNITY_SUPPORT: FeatureCategory.FREE,
    
    # Creator tier features
    Feature.SMART_GALLERY_GENERATOR: FeatureCategory.CREATOR,
    Feature.POST_FORMATTING: FeatureCategory.CREATOR,
    Feature.BASIC_VIDEO_PROCESSING: FeatureCategory.CREATOR,
    Feature.EMAIL_SUPPORT: FeatureCategory.CREATOR,
    
    # Pro tier features
    Feature.FULL_VIDEO_EDITING_SUITE: FeatureCategory.PRO,
    Feature.VEO_VIDEO_GENERATOR: FeatureCategory.PRO,
    Feature.HIGHLIGHT_REEL_GENERATOR: FeatureCategory.PRO,
    Feature.STORY_ASSISTANT: FeatureCategory.PRO,
    Feature.BULK_OPERATIONS: FeatureCategory.PRO,
    Feature.AUDIO_IMPORTER: FeatureCategory.PRO,
    Feature.ADVANCED_ANALYTICS: FeatureCategory.PRO,
    Feature.PERFORMANCE_ANALYTICS: FeatureCategory.PRO,
    Feature.TEAM_COLLABORATION: FeatureCategory.PRO,
    Feature.PRIORITY_SUPPORT: FeatureCategory.PRO,
    
    # Business tier features
    Feature.ADVANCED_TEAM_COLLABORATION: FeatureCategory.BUSINESS,
    Feature.CUSTOM_ANALYTICS: FeatureCategory.BUSINESS,
    Feature.CUSTOM_BRANDING: FeatureCategory.BUSINESS,
    Feature.API_ACCESS: FeatureCategory.BUSINESS,
    Feature.DEDICATED_ACCOUNT_MANAGER: FeatureCategory.BUSINESS,
}

# Usage limits for different tiers based on the new pricing model
USAGE_LIMITS = {
    SubscriptionTier.FREE: {
        "social_accounts": 1,
        "users": 1,
        "ai_content_credits_per_month": 25,
        "scheduled_posts_per_month": 10,
        "storage_gb": 0.5,  # 500MB
        "team_members": 1,
    },
    SubscriptionTier.CREATOR: {
        "social_accounts": 3,
        "users": 1,
        "ai_content_credits_per_month": 150,
        "scheduled_posts_per_month": 100,
        "storage_gb": 5,
        "team_members": 1,
    },
    SubscriptionTier.PRO: {
        "social_accounts": 10,
        "users": 3,
        "ai_content_credits_per_month": 750,
        "scheduled_posts_per_month": -1,  # Unlimited
        "storage_gb": 50,
        "team_members": 3,
    },
    SubscriptionTier.BUSINESS: {
        "social_accounts": -1,  # Custom/High Volume
        "users": -1,  # Custom/More Users
        "ai_content_credits_per_month": -1,  # Custom/High Volume
        "scheduled_posts_per_month": -1,  # Unlimited
        "storage_gb": -1,  # Custom/High Volume
        "team_members": -1,  # Custom
    }
}

class AccessControlError(Exception):
    """Exception raised when access is denied."""
    pass

class SubscriptionAccessControl:
    """Manages subscription-based access control."""
    
    def __init__(self):
        """Initialize access control."""
        self.user_manager = user_manager
    
    def has_feature_access(self, feature: Feature) -> bool:
        """
        Check if current user has access to a feature.
        
        Args:
            feature: The feature to check access for
            
        Returns:
            bool: True if user has access, False otherwise
        """
        try:
            # Get current user
            user = self.user_manager.get_current_user()
            if not user:
                # No user logged in - only allow core features
                return FEATURE_ACCESS.get(feature) == FeatureCategory.CORE
            
            # Check feature category
            feature_category = FEATURE_ACCESS.get(feature, FeatureCategory.PRO)
            
            if feature_category == FeatureCategory.CORE:
                return True
            elif feature_category == FeatureCategory.FREE:
                return True  # Free features available to all logged-in users
            elif feature_category == FeatureCategory.CREATOR:
                # Available to Creator tier and above
                return user.subscription.tier in [SubscriptionTier.CREATOR, SubscriptionTier.PRO, SubscriptionTier.BUSINESS] and user.is_subscription_active()
            elif feature_category == FeatureCategory.PRO:
                # Available to Pro tier and above
                return user.subscription.tier in [SubscriptionTier.PRO, SubscriptionTier.BUSINESS] and user.is_subscription_active()
            elif feature_category == FeatureCategory.BUSINESS:
                # Business only
                return user.subscription.tier == SubscriptionTier.BUSINESS and user.is_subscription_active()
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking feature access: {e}")
            return False
    
    def check_usage_limit(self, usage_type: str, requested_amount: int = 1) -> bool:
        """
        Check if user can perform an action based on usage limits.
        
        Args:
            usage_type: Type of usage (posts, videos, ai_requests, etc.)
            requested_amount: Amount being requested
            
        Returns:
            bool: True if within limits, False otherwise
        """
        try:
            user = self.user_manager.get_current_user()
            if not user:
                return False
            
            # Get limits for user's tier
            limits = USAGE_LIMITS.get(user.subscription.tier, USAGE_LIMITS[SubscriptionTier.FREE])
            
            # Check specific usage type
            if usage_type == "social_accounts":
                current_usage = user.usage_stats.social_accounts
                limit = limits["social_accounts"]
            elif usage_type == "users":
                current_usage = user.usage_stats.team_members_used  # users = team members
                limit = limits["users"]
            elif usage_type == "ai_content_credits_per_month":
                current_usage = user.usage_stats.ai_content_credits_this_month
                limit = limits["ai_content_credits_per_month"]
            elif usage_type == "scheduled_posts_per_month":
                # We'll track this in a new field if needed, for now use existing post tracking
                current_usage = getattr(user.usage_stats, 'scheduled_posts_this_month', 0)
                limit = limits["scheduled_posts_per_month"]
            elif usage_type == "storage_gb":
                current_usage = user.usage_stats.storage_used_gb
                limit = limits["storage_gb"]
            elif usage_type == "team_members":
                current_usage = user.usage_stats.team_members_used
                limit = limits["team_members"]
            else:
                logger.warning(f"Unknown usage type: {usage_type}")
                return True  # Allow unknown types by default
            
            # Check for unlimited (-1) limits
            if limit == -1:
                return True
            
            return (current_usage + requested_amount) <= limit
            
        except Exception as e:
            logger.error(f"Error checking usage limit: {e}")
            return False
    
    def get_usage_info(self) -> Dict[str, Any]:
        """
        Get current usage information for the user.
        
        Returns:
            dict: Usage information including current usage and limits
        """
        try:
            user = self.user_manager.get_current_user()
            if not user:
                return {}
            
            limits = USAGE_LIMITS.get(user.subscription.tier, USAGE_LIMITS[SubscriptionTier.FREE])
            
            def safe_percentage(current, limit):
                """Calculate percentage, handling unlimited limits (-1)."""
                if limit == -1:
                    return 0  # Unlimited usage
                if limit == 0:
                    return 100 if current > 0 else 0
                return (current / limit) * 100
            
            return {
                "subscription_tier": user.subscription.tier.value,
                "subscription_status": user.get_subscription_status(),
                "usage": {
                    "social_accounts": {
                        "current": user.usage_stats.social_accounts,
                        "limit": limits["social_accounts"],
                        "percentage": safe_percentage(user.usage_stats.social_accounts, limits["social_accounts"])
                    },
                    "users": {
                        "current": user.usage_stats.team_members_used,
                        "limit": limits["users"],
                        "percentage": safe_percentage(user.usage_stats.team_members_used, limits["users"])
                    },
                    "ai_content_credits_per_month": {
                        "current": user.usage_stats.ai_content_credits_this_month,
                        "limit": limits["ai_content_credits_per_month"],
                        "percentage": safe_percentage(user.usage_stats.ai_content_credits_this_month, limits["ai_content_credits_per_month"])
                    },
                    "scheduled_posts_per_month": {
                        "current": getattr(user.usage_stats, 'scheduled_posts_this_month', 0),
                        "limit": limits["scheduled_posts_per_month"],
                        "percentage": safe_percentage(getattr(user.usage_stats, 'scheduled_posts_this_month', 0), limits["scheduled_posts_per_month"])
                    },
                    "storage_gb": {
                        "current": user.usage_stats.storage_used_gb,
                        "limit": limits["storage_gb"],
                        "percentage": safe_percentage(user.usage_stats.storage_used_gb, limits["storage_gb"])
                    },
                    "team_members": {
                        "current": user.usage_stats.team_members_used,
                        "limit": limits["team_members"],
                        "percentage": safe_percentage(user.usage_stats.team_members_used, limits["team_members"])
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting usage info: {e}")
            return {}
    
    def get_upgrade_benefits(self, current_tier: SubscriptionTier = SubscriptionTier.FREE) -> List[str]:
        """
        Get list of benefits for upgrading from current tier.
        
        Args:
            current_tier: User's current subscription tier
            
        Returns:
            list: List of upgrade benefits
        """
        if current_tier == SubscriptionTier.FREE:
            return [
                "✨ Creator ($19/month): 3 social accounts, 150 AI credits, 100 scheduled posts, basic video tools",
                "🚀 Pro ($50/month): 10 social accounts, 750 AI credits, unlimited posts, full video suite, team collaboration",
                "🏢 Business (Custom): Unlimited accounts, custom limits, advanced team features, dedicated support"
            ]
        elif current_tier == SubscriptionTier.CREATOR:
            return [
                "🚀 Pro ($50/month): 10 social accounts, 750 AI credits, unlimited posts, full video processing suite, team collaboration",
                "🏢 Business (Custom): Unlimited accounts, custom limits, advanced team features, dedicated account manager"
            ]
        elif current_tier == SubscriptionTier.PRO:
            return [
                "🏢 Business (Custom): Unlimited accounts, custom limits, advanced team collaboration, API access, dedicated account manager"
            ]
        else:
            return ["Contact sales for custom business solutions"]

# Decorator for feature access control
def requires_feature(feature: Feature):
    """
    Decorator to enforce feature access control.
    
    Args:
        feature: The feature required to access the function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not access_control.has_feature_access(feature):
                raise AccessControlError(f"Access denied: {feature.value} requires Pro subscription")
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Decorator for usage limit checking
def requires_usage_limit(usage_type: str, amount: int = 1):
    """
    Decorator to enforce usage limits.
    
    Args:
        usage_type: Type of usage to check
        amount: Amount being used
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not access_control.check_usage_limit(usage_type, amount):
                user = user_manager.get_current_user()
                if user:
                    limits = USAGE_LIMITS.get(user.subscription.tier, USAGE_LIMITS[SubscriptionTier.FREE])
                    limit = limits.get(f"{usage_type}_per_month", limits.get(usage_type, 0))
                    if limit == -1:
                        raise AccessControlError(f"Usage error: {usage_type} checking failed")
                    else:
                        raise AccessControlError(f"Usage limit exceeded: {usage_type} limit is {limit} per month")
                else:
                    raise AccessControlError("Please log in to use this feature")
            
            # Execute function and increment usage
            result = func(*args, **kwargs)
            user_manager.increment_usage(usage_type, amount)
            return result
        return wrapper
    return decorator

# Global access control instance
access_control = SubscriptionAccessControl() 