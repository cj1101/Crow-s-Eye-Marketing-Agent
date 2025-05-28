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
    SPARK = "spark"                  # Available in Spark tier and above
    CREATOR = "creator"              # Available in Creator tier and above
    GROWTH = "growth"                # Available in Growth tier and above
    PRO_AGENCY = "pro_agency"        # Available in Pro Agency tier and above
    ENTERPRISE = "enterprise"        # Enterprise only features

class Feature(Enum):
    """Available features in the platform."""
    # Core features (always available)
    BASIC_UI = "basic_ui"
    SETTINGS = "settings"
    HELP = "help"
    
    # Spark tier features (free tier)
    MEDIA_LIBRARY = "media_library"
    BASIC_IMAGE_ANALYSIS = "basic_image_analysis"
    BASIC_ANALYTICS = "basic_analytics"
    COMMUNITY_SUPPORT = "community_support"
    
    # Creator tier features ($19/month)
    SMART_GALLERY_GENERATOR = "smart_gallery_generator"
    POST_FORMATTING = "post_formatting"
    BASIC_VIDEO_PROCESSING = "basic_video_processing"
    EMAIL_SUPPORT = "email_support"
    
    # Growth tier features ($49/month)
    SMART_MEDIA_SEARCH = "smart_media_search"
    ADVANCED_ANALYTICS = "advanced_analytics"
    PRIORITY_SUPPORT = "priority_support"
    TEAM_COLLABORATION = "team_collaboration"
    
    # Pro Agency tier features ($89/month)
    VEO_VIDEO_GENERATOR = "veo_video_generator"
    HIGHLIGHT_REEL_GENERATOR = "highlight_reel_generator"
    FULL_VIDEO_PROCESSING_SUITE = "full_video_processing_suite"
    ADVANCED_AI_FEATURES = "advanced_ai_features"
    BULK_OPERATIONS = "bulk_operations"
    STORY_ASSISTANT = "story_assistant"
    AUDIO_IMPORTER = "audio_importer"
    
    # Enterprise features (custom)
    CUSTOM_BRANDING = "custom_branding"
    DEDICATED_ACCOUNT_MANAGER = "dedicated_account_manager"
    UNLIMITED_TEAM_MEMBERS = "unlimited_team_members"
    CUSTOM_ANALYTICS = "custom_analytics"

# Feature access mapping
FEATURE_ACCESS = {
    # Core features
    Feature.BASIC_UI: FeatureCategory.CORE,
    Feature.SETTINGS: FeatureCategory.CORE,
    Feature.HELP: FeatureCategory.CORE,
    
    # Spark tier features
    Feature.MEDIA_LIBRARY: FeatureCategory.SPARK,
    Feature.BASIC_IMAGE_ANALYSIS: FeatureCategory.SPARK,
    Feature.BASIC_ANALYTICS: FeatureCategory.SPARK,
    Feature.COMMUNITY_SUPPORT: FeatureCategory.SPARK,
    
    # Creator tier features
    Feature.SMART_GALLERY_GENERATOR: FeatureCategory.CREATOR,
    Feature.POST_FORMATTING: FeatureCategory.CREATOR,
    Feature.BASIC_VIDEO_PROCESSING: FeatureCategory.CREATOR,
    Feature.EMAIL_SUPPORT: FeatureCategory.CREATOR,
    
    # Growth tier features
    Feature.SMART_MEDIA_SEARCH: FeatureCategory.GROWTH,
    Feature.ADVANCED_ANALYTICS: FeatureCategory.GROWTH,
    Feature.PRIORITY_SUPPORT: FeatureCategory.GROWTH,
    Feature.TEAM_COLLABORATION: FeatureCategory.GROWTH,
    
    # Pro Agency tier features
    Feature.VEO_VIDEO_GENERATOR: FeatureCategory.PRO_AGENCY,
    Feature.HIGHLIGHT_REEL_GENERATOR: FeatureCategory.PRO_AGENCY,
    Feature.FULL_VIDEO_PROCESSING_SUITE: FeatureCategory.PRO_AGENCY,
    Feature.ADVANCED_AI_FEATURES: FeatureCategory.PRO_AGENCY,
    Feature.BULK_OPERATIONS: FeatureCategory.PRO_AGENCY,
    Feature.STORY_ASSISTANT: FeatureCategory.PRO_AGENCY,
    Feature.AUDIO_IMPORTER: FeatureCategory.PRO_AGENCY,
    
    # Enterprise features
    Feature.CUSTOM_BRANDING: FeatureCategory.ENTERPRISE,
    Feature.DEDICATED_ACCOUNT_MANAGER: FeatureCategory.ENTERPRISE,
    Feature.UNLIMITED_TEAM_MEMBERS: FeatureCategory.ENTERPRISE,
    Feature.CUSTOM_ANALYTICS: FeatureCategory.ENTERPRISE,
}

# Usage limits for different tiers based on the pricing image
USAGE_LIMITS = {
    SubscriptionTier.SPARK: {
        "social_accounts": 1,
        "ai_content_credits_per_month": 50,
        "ai_image_edits_per_month": 5,
        "storage_gb": 1,
        "context_files": 1,
        "team_members": 1,
        "video_processing": False,
    },
    SubscriptionTier.CREATOR: {
        "social_accounts": 3,
        "ai_content_credits_per_month": 300,
        "ai_image_edits_per_month": 30,
        "storage_gb": 10,
        "context_files": 3,
        "team_members": 1,
        "video_processing": True,
    },
    SubscriptionTier.GROWTH: {
        "social_accounts": 6,
        "ai_content_credits_per_month": 600,
        "ai_image_edits_per_month": 60,
        "storage_gb": 50,
        "context_files": 5,
        "team_members": 3,
        "video_processing": True,
    },
    SubscriptionTier.PRO_AGENCY: {
        "social_accounts": 15,
        "ai_content_credits_per_month": 1000,
        "ai_image_edits_per_month": 120,
        "storage_gb": 200,
        "context_files": 10,
        "team_members": 10,
        "video_processing": True,
    },
    SubscriptionTier.ENTERPRISE: {
        "social_accounts": -1,  # Unlimited
        "ai_content_credits_per_month": -1,  # Custom
        "ai_image_edits_per_month": -1,  # Custom
        "storage_gb": -1,  # Custom
        "context_files": -1,  # Custom
        "team_members": -1,  # Unlimited
        "video_processing": True,
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
            feature_category = FEATURE_ACCESS.get(feature, FeatureCategory.PRO_AGENCY)
            
            if feature_category == FeatureCategory.CORE:
                return True
            elif feature_category == FeatureCategory.SPARK:
                return True  # Spark features available to all logged-in users
            elif feature_category == FeatureCategory.CREATOR:
                # Available to Creator tier and above
                return user.subscription.tier in [SubscriptionTier.CREATOR, SubscriptionTier.GROWTH, SubscriptionTier.PRO_AGENCY, SubscriptionTier.ENTERPRISE] and user.is_subscription_active()
            elif feature_category == FeatureCategory.GROWTH:
                # Available to Growth tier and above
                return user.subscription.tier in [SubscriptionTier.GROWTH, SubscriptionTier.PRO_AGENCY, SubscriptionTier.ENTERPRISE] and user.is_subscription_active()
            elif feature_category == FeatureCategory.PRO_AGENCY:
                # Available to Pro Agency tier and above
                return user.subscription.tier in [SubscriptionTier.PRO_AGENCY, SubscriptionTier.ENTERPRISE] and user.is_subscription_active()
            elif feature_category == FeatureCategory.ENTERPRISE:
                # Enterprise only
                return user.subscription.tier == SubscriptionTier.ENTERPRISE and user.is_subscription_active()
            
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
            limits = USAGE_LIMITS.get(user.subscription.tier, USAGE_LIMITS[SubscriptionTier.SPARK])
            
            # Check specific usage type
            if usage_type == "social_accounts":
                current_usage = user.usage_stats.social_accounts
                limit = limits["social_accounts"]
            elif usage_type == "ai_content_credits_per_month":
                current_usage = user.usage_stats.ai_content_credits_this_month
                limit = limits["ai_content_credits_per_month"]
            elif usage_type == "ai_image_edits_per_month":
                current_usage = user.usage_stats.ai_image_edits_this_month
                limit = limits["ai_image_edits_per_month"]
            elif usage_type == "storage_gb":
                current_usage = user.usage_stats.storage_used_gb
                limit = limits["storage_gb"]
            elif usage_type == "context_files":
                current_usage = user.usage_stats.context_files_used
                limit = limits["context_files"]
            elif usage_type == "team_members":
                current_usage = user.usage_stats.team_members_used
                limit = limits["team_members"]
            elif usage_type == "video_processing":
                current_usage = user.usage_stats.video_processing_used
                limit = limits["video_processing"]
            else:
                logger.warning(f"Unknown usage type: {usage_type}")
                return True  # Allow unknown types by default
            
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
            
            limits = USAGE_LIMITS.get(user.subscription.tier, USAGE_LIMITS[SubscriptionTier.SPARK])
            
            return {
                "subscription_tier": user.subscription.tier.value,
                "subscription_status": user.get_subscription_status(),
                "usage": {
                    "social_accounts": {
                        "current": user.usage_stats.social_accounts,
                        "limit": limits["social_accounts"],
                        "percentage": (user.usage_stats.social_accounts / limits["social_accounts"]) * 100
                    },
                    "ai_content_credits_per_month": {
                        "current": user.usage_stats.ai_content_credits_this_month,
                        "limit": limits["ai_content_credits_per_month"],
                        "percentage": (user.usage_stats.ai_content_credits_this_month / limits["ai_content_credits_per_month"]) * 100
                    },
                    "ai_image_edits_per_month": {
                        "current": user.usage_stats.ai_image_edits_this_month,
                        "limit": limits["ai_image_edits_per_month"],
                        "percentage": (user.usage_stats.ai_image_edits_this_month / limits["ai_image_edits_per_month"]) * 100
                    },
                    "storage_gb": {
                        "current": user.usage_stats.storage_used_gb,
                        "limit": limits["storage_gb"],
                        "percentage": (user.usage_stats.storage_used_gb / limits["storage_gb"]) * 100
                    },
                    "context_files": {
                        "current": user.usage_stats.context_files_used,
                        "limit": limits["context_files"],
                        "percentage": (user.usage_stats.context_files_used / limits["context_files"]) * 100
                    },
                    "team_members": {
                        "current": user.usage_stats.team_members_used,
                        "limit": limits["team_members"],
                        "percentage": (user.usage_stats.team_members_used / limits["team_members"]) * 100
                    },
                    "video_processing": {
                        "current": user.usage_stats.video_processing_used,
                        "limit": limits["video_processing"],
                        "percentage": (user.usage_stats.video_processing_used / limits["video_processing"]) * 100
                    }
                },
                "features": {
                    "video_processing": limits["video_processing"],
                    "team_members": limits["team_members"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting usage info: {e}")
            return {}
    
    def get_upgrade_benefits(self, current_tier: SubscriptionTier = SubscriptionTier.SPARK) -> List[str]:
        """
        Get list of benefits for upgrading from current tier.
        
        Args:
            current_tier: User's current subscription tier
            
        Returns:
            list: List of upgrade benefits
        """
        if current_tier == SubscriptionTier.SPARK:
            return [
                "🏢 Creator ($19/month): Up to 3 social accounts, 300 AI credits, basic video tools",
                "📈 Growth ($49/month): Up to 6 accounts, 600 AI credits, advanced analytics, team collaboration",
                "🚀 Pro Agency ($89/month): Up to 15 accounts, 1000 AI credits, full video suite",
                "🏢 Enterprise: Unlimited accounts, custom limits, dedicated support"
            ]
        elif current_tier == SubscriptionTier.CREATOR:
            return [
                "📈 Growth ($49/month): 6 social accounts, 600 AI credits, advanced analytics, team collaboration",
                "🚀 Pro Agency ($89/month): 15 social accounts, 1000 AI credits, full video processing suite",
                "🏢 Enterprise: Unlimited accounts, custom limits, dedicated account manager"
            ]
        elif current_tier == SubscriptionTier.GROWTH:
            return [
                "🚀 Pro Agency ($89/month): 15 social accounts, 1000 AI credits, full video processing suite",
                "🏢 Enterprise: Unlimited accounts, custom limits, dedicated account manager"
            ]
        elif current_tier == SubscriptionTier.PRO_AGENCY:
            return [
                "🏢 Enterprise: Unlimited accounts, custom limits, dedicated account manager, unlimited team members"
            ]
        else:
            return ["Contact sales for custom enterprise solutions"]

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
                    limits = USAGE_LIMITS.get(user.subscription.tier, USAGE_LIMITS[SubscriptionTier.SPARK])
                    limit = limits.get(f"{usage_type}_per_month", 0)
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