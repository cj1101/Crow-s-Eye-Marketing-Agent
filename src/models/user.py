"""
User model for Crow's Eye Marketing Platform.
Handles user accounts, subscription tiers, and feature access control.
Integrates with Firebase authentication from Crow's Eye Website.
"""
import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

from ..config.firebase_config import is_firebase_configured, get_setup_instructions

logger = logging.getLogger(__name__)

class SubscriptionTier(Enum):
    """Subscription tier enumeration."""
    SPARK = "spark"           # $0 - Students & hobbyists
    CREATOR = "creator"       # $19/month - Solo-preneurs & freelancers
    GROWTH = "growth"         # $49/month - Side-hustles & small teams
    PRO_AGENCY = "pro_agency" # $89/month - Agencies & SMB marketing teams
    ENTERPRISE = "enterprise" # $0 - Large orgs & custom needs

@dataclass
class UsageStats:
    """User usage statistics."""
    social_accounts: int = 0
    ai_content_credits_this_month: int = 0
    ai_image_edits_this_month: int = 0
    storage_used_gb: float = 0.0
    context_files_used: int = 0
    team_members_used: int = 0
    video_processing_used: int = 0
    last_reset_date: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UsageStats':
        """Create from dictionary with backward compatibility."""
        # Handle legacy field names
        mapped_data = {}
        
        # Map legacy fields to new fields
        field_mapping = {
            'posts_created_this_month': 'social_accounts',
            'videos_generated_this_month': 'video_processing_used',
            'ai_requests_this_month': 'ai_content_credits_this_month',
            'storage_used_mb': 'storage_used_gb',
        }
        
        # Copy existing fields and map legacy ones
        for key, value in data.items():
            if key in field_mapping:
                mapped_data[field_mapping[key]] = value
            else:
                mapped_data[key] = value
        
        # Convert storage from MB to GB if needed
        if 'storage_used_mb' in data and 'storage_used_gb' not in mapped_data:
            mapped_data['storage_used_gb'] = data['storage_used_mb'] / 1024.0
        
        # Ensure all required fields have default values
        defaults = {
            'social_accounts': 0,
            'ai_content_credits_this_month': 0,
            'ai_image_edits_this_month': 0,
            'storage_used_gb': 0.0,
            'context_files_used': 0,
            'team_members_used': 0,
            'video_processing_used': 0,
            'last_reset_date': ""
        }
        
        for field, default_value in defaults.items():
            if field not in mapped_data:
                mapped_data[field] = default_value
        
        # Only pass fields that exist in the dataclass
        valid_fields = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in mapped_data.items() if k in valid_fields}
        
        return cls(**filtered_data)

@dataclass
class SubscriptionInfo:
    """Subscription information."""
    tier: SubscriptionTier
    start_date: str
    end_date: Optional[str] = None
    auto_renew: bool = True
    payment_method: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'tier': self.tier.value,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'auto_renew': self.auto_renew,
            'payment_method': self.payment_method
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubscriptionInfo':
        """Create from dictionary with backward compatibility."""
        # Handle legacy tier names
        tier_value = data['tier']
        if tier_value == 'pro':
            tier_value = 'pro_agency'  # Map legacy 'pro' to 'pro_agency'
        elif tier_value == 'free':
            tier_value = 'spark'  # Map legacy 'free' to 'spark'
        
        return cls(
            tier=SubscriptionTier(tier_value),
            start_date=data['start_date'],
            end_date=data.get('end_date'),
            auto_renew=data.get('auto_renew', True),
            payment_method=data.get('payment_method')
        )

@dataclass
class User:
    """User model for Crow's Eye platform."""
    user_id: str
    email: str
    username: str
    created_at: str
    subscription: SubscriptionInfo
    usage_stats: UsageStats
    preferences: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary."""
        return {
            'user_id': self.user_id,
            'email': self.email,
            'username': self.username,
            'created_at': self.created_at,
            'subscription': self.subscription.to_dict(),
            'usage_stats': self.usage_stats.to_dict(),
            'preferences': self.preferences
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user from dictionary."""
        return cls(
            user_id=data['user_id'],
            email=data['email'],
            username=data['username'],
            created_at=data['created_at'],
            subscription=SubscriptionInfo.from_dict(data['subscription']),
            usage_stats=UsageStats.from_dict(data['usage_stats']),
            preferences=data.get('preferences', {})
        )
    
    def is_pro_user(self) -> bool:
        """Check if user has Pro subscription (Pro Agency or Enterprise)."""
        return self.subscription.tier == SubscriptionTier.PRO_AGENCY or self.subscription.tier == SubscriptionTier.ENTERPRISE
    
    def is_enterprise_user(self) -> bool:
        """Check if user has Enterprise subscription."""
        return self.subscription.tier == SubscriptionTier.ENTERPRISE
    
    def is_paid_user(self) -> bool:
        """Check if user has any paid subscription."""
        return self.subscription.tier in [SubscriptionTier.CREATOR, SubscriptionTier.GROWTH, SubscriptionTier.PRO_AGENCY, SubscriptionTier.ENTERPRISE]
    
    def is_subscription_active(self) -> bool:
        """Check if subscription is currently active."""
        if self.subscription.tier == SubscriptionTier.SPARK:
            return True
        
        if self.subscription.end_date:
            end_date = datetime.fromisoformat(self.subscription.end_date)
            return datetime.now() < end_date
        
        return True
    
    def get_subscription_status(self) -> str:
        """Get human-readable subscription status."""
        if self.subscription.tier == SubscriptionTier.SPARK:
            return "Spark Tier"
        
        if self.is_subscription_active():
            if self.subscription.end_date:
                end_date = datetime.fromisoformat(self.subscription.end_date)
                days_left = (end_date - datetime.now()).days
                return f"{self.subscription.tier.value} Tier (expires in {days_left} days)"
            return f"{self.subscription.tier.value} Tier (Active)"
        else:
            return f"{self.subscription.tier.value} Tier (Expired)"

class UserManager:
    """Manages user accounts and authentication."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize user manager."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.users_file = self.data_dir / "users.json"
        self.current_user_file = self.data_dir / "current_user.json"
        self.current_user: Optional[User] = None
        
        # Load current user if exists
        self._load_current_user()
    
    def _load_users(self) -> Dict[str, Dict[str, Any]]:
        """Load users from file."""
        if not self.users_file.exists():
            return {}
        
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            return {}
    
    def _save_users(self, users: Dict[str, Dict[str, Any]]) -> None:
        """Save users to file."""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def _load_current_user(self) -> None:
        """Load current user from file."""
        if not self.current_user_file.exists():
            return
        
        try:
            with open(self.current_user_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
                self.current_user = User.from_dict(user_data)
        except Exception as e:
            logger.error(f"Error loading current user: {e}")
    
    def _save_current_user(self) -> None:
        """Save current user to file."""
        if not self.current_user:
            if self.current_user_file.exists():
                self.current_user_file.unlink()
            return
        
        try:
            with open(self.current_user_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_user.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving current user: {e}")
    
    def create_user(self, email: str, username: str, password: str) -> Optional[User]:
        """Create a new user account - deprecated, use Firebase authentication instead."""
        logger.warning("Local user creation is deprecated. Please use Firebase authentication.")
        return None
    
    def login(self, email: str, password: str) -> bool:
        """Login user with email and password. Alias for authenticate_user."""
        return self.authenticate_user(email, password)
    
    def authenticate_user(self, email: str, password: str) -> bool:
        """Authenticate user with email and password - deprecated, use Firebase authentication instead."""
        logger.warning("Local authentication is deprecated. Please use Firebase authentication.")
        return False
    
    def logout(self) -> None:
        """Logout current user."""
        if self.current_user:
            logger.info(f"User logged out: {self.current_user.email}")
        
        self.current_user = None
        if self.current_user_file.exists():
            self.current_user_file.unlink()
    
    def save_user(self, user: User) -> None:
        """Save user data to storage."""
        try:
            # Update current user if it's the same user
            if self.current_user and self.current_user.user_id == user.user_id:
                self.current_user = user
                self._save_current_user()
            
            # Update in users file
            users = self._load_users()
            users[user.user_id] = user.to_dict()
            self._save_users(users)
            
            logger.info(f"User data saved: {user.email}")
            
        except Exception as e:
            logger.error(f"Error saving user: {e}")
    
    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user."""
        return self.current_user
    
    def is_authenticated(self) -> bool:
        """Check if a user is currently authenticated via Firebase."""
        return self.current_user is not None
    
    def upgrade_to_tier(self, tier: SubscriptionTier, payment_method: str = "demo") -> bool:
        """Upgrade current user to specified tier."""
        if not self.current_user:
            return False
        
        try:
            # Update subscription
            self.current_user.subscription = SubscriptionInfo(
                tier=tier,
                start_date=datetime.now().isoformat(),
                end_date=(datetime.now() + timedelta(days=30)).isoformat() if tier != SubscriptionTier.SPARK else None,
                payment_method=payment_method
            )
            
            # Save changes
            self._save_current_user()
            
            # Update in users file
            users = self._load_users()
            if self.current_user.user_id in users:
                users[self.current_user.user_id].update(self.current_user.to_dict())
                self._save_users(users)
            
            logger.info(f"User upgraded to {tier.value}: {self.current_user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error upgrading user to {tier.value}: {e}")
            return False
    
    def upgrade_to_pro(self, payment_method: str = "demo") -> bool:
        """Upgrade current user to Pro Agency tier (legacy method for compatibility)."""
        return self.upgrade_to_tier(SubscriptionTier.PRO_AGENCY, payment_method)
    
    def reset_monthly_usage(self) -> None:
        """Reset monthly usage statistics."""
        if not self.current_user:
            return
        
        try:
            now = datetime.now()
            reset_date = now.replace(day=1)
            
            # Check if we need to reset
            if self.current_user.usage_stats.last_reset_date:
                last_reset = datetime.fromisoformat(self.current_user.usage_stats.last_reset_date)
                if last_reset.month == now.month and last_reset.year == now.year:
                    return  # Already reset this month
            
            # Reset usage stats
            self.current_user.usage_stats = UsageStats(
                last_reset_date=reset_date.isoformat()
            )
            
            self._save_current_user()
            logger.info("Monthly usage statistics reset")
            
        except Exception as e:
            logger.error(f"Error resetting monthly usage: {e}")
    
    def increment_usage(self, usage_type: str, amount: int = 1) -> None:
        """Increment usage statistics."""
        if not self.current_user:
            return
        
        try:
            # Reset monthly usage if needed
            self.reset_monthly_usage()
            
            # Increment usage
            if usage_type == "social_accounts":
                self.current_user.usage_stats.social_accounts += amount
            elif usage_type == "ai_content_credits_per_month":
                self.current_user.usage_stats.ai_content_credits_this_month += amount
            elif usage_type == "ai_image_edits_per_month":
                self.current_user.usage_stats.ai_image_edits_this_month += amount
            elif usage_type == "storage_gb":
                self.current_user.usage_stats.storage_used_gb += amount
            elif usage_type == "context_files":
                self.current_user.usage_stats.context_files_used += amount
            elif usage_type == "team_members":
                self.current_user.usage_stats.team_members_used += amount
            elif usage_type == "video_processing":
                self.current_user.usage_stats.video_processing_used += amount
            
            self._save_current_user()
            
        except Exception as e:
            logger.error(f"Error incrementing usage: {e}")
    
    def create_or_update_from_firebase(self, firebase_user_data: Dict[str, Any]) -> Optional[User]:
        """
        Create or update a local user account from Firebase user data.
        Prioritizes Firebase data when merging accounts.
        
        Args:
            firebase_user_data: User data from Firebase
            
        Returns:
            User: Created or updated user object
        """
        try:
            email = firebase_user_data.get('email')
            if not email:
                logger.error("No email in Firebase user data")
                return None
            
            # Check if user already exists locally
            users = self._load_users()
            existing_user_id = None
            existing_user_data = None
            
            for user_id, user_data in users.items():
                if user_data.get('email') == email:
                    existing_user_id = user_id
                    existing_user_data = user_data
                    break
            
            # Determine subscription tier from Firebase data (prioritize Firebase)
            subscription_tier = SubscriptionTier.SPARK
            subscription_end_date = None
            
            if firebase_user_data.get('subscription', {}).get('plan') == 'creator':
                subscription_tier = SubscriptionTier.CREATOR
                # Try to get end date from Firebase
                if firebase_user_data.get('subscription', {}).get('end_date'):
                    subscription_end_date = firebase_user_data['subscription']['end_date']
            elif firebase_user_data.get('subscription', {}).get('plan') == 'growth':
                subscription_tier = SubscriptionTier.GROWTH
                # Try to get end date from Firebase
                if firebase_user_data.get('subscription', {}).get('end_date'):
                    subscription_end_date = firebase_user_data['subscription']['end_date']
            elif firebase_user_data.get('subscription', {}).get('plan') == 'pro_agency':
                subscription_tier = SubscriptionTier.PRO_AGENCY
                # Try to get end date from Firebase
                if firebase_user_data.get('subscription', {}).get('end_date'):
                    subscription_end_date = firebase_user_data['subscription']['end_date']
            elif firebase_user_data.get('subscription', {}).get('plan') == 'enterprise':
                subscription_tier = SubscriptionTier.ENTERPRISE
                # Try to get end date from Firebase
                if firebase_user_data.get('subscription', {}).get('end_date'):
                    subscription_end_date = firebase_user_data['subscription']['end_date']
            
            # Extract creation date from Firebase (prioritize Firebase)
            created_at = datetime.now().isoformat()
            if firebase_user_data.get('createdAt'):
                try:
                    # Handle Firebase DatetimeWithNanoseconds
                    created_at_value = firebase_user_data['createdAt']
                    if hasattr(created_at_value, 'isoformat'):
                        created_at = created_at_value.isoformat()
                    else:
                        created_at = str(created_at_value)
                except:
                    pass
            elif firebase_user_data.get('creation_timestamp'):
                try:
                    # Handle Firebase timestamp (milliseconds)
                    timestamp = firebase_user_data['creation_timestamp']
                    if hasattr(timestamp, 'timestamp'):
                        # Firebase Timestamp object
                        created_at = datetime.fromtimestamp(timestamp.timestamp()).isoformat()
                    else:
                        # Regular timestamp
                        created_at = datetime.fromtimestamp(timestamp / 1000).isoformat()
                except:
                    pass
            elif existing_user_data and existing_user_data.get('created_at'):
                # Fall back to existing local creation date if available
                created_at = existing_user_data['created_at']
            
            # Use Firebase UID if available, otherwise generate one
            user_id = firebase_user_data.get('uid', hashlib.sha256(f"{email}{datetime.now().isoformat()}".encode()).hexdigest()[:16])
            
            # Prioritize Firebase username, fall back to existing local username, then email prefix
            username = (firebase_user_data.get('display_name') or 
                       firebase_user_data.get('displayName') or
                       (existing_user_data.get('username') if existing_user_data else None) or
                       email.split('@')[0])
            
            # Preserve local usage stats if they exist
            usage_stats = UsageStats(last_reset_date=datetime.now().replace(day=1).isoformat())
            if existing_user_data and existing_user_data.get('usage_stats'):
                try:
                    usage_stats = UsageStats.from_dict(existing_user_data['usage_stats'])
                except:
                    pass
            
            # Preserve local preferences if they exist
            preferences = firebase_user_data.get('preferences', {})
            if existing_user_data and existing_user_data.get('preferences'):
                # Merge preferences, prioritizing Firebase
                local_prefs = existing_user_data.get('preferences', {})
                local_prefs.update(preferences)
                preferences = local_prefs
            
            # Create user object with prioritized Firebase data
            user = User(
                user_id=user_id,
                email=email,
                username=username,
                created_at=created_at,
                subscription=SubscriptionInfo(
                    tier=subscription_tier,
                    start_date=created_at,
                    end_date=subscription_end_date
                ),
                usage_stats=usage_stats,
                preferences=preferences
            )
            
            # Remove old user entry if it exists and has different ID
            if existing_user_id and existing_user_id != user_id:
                users.pop(existing_user_id, None)
                logger.info(f"Removed old local user entry: {existing_user_id}")
            
            # Save user (without password hash since using Firebase auth)
            user_dict = user.to_dict()
            user_dict.pop('password_hash', None)  # Ensure no password hash
            
            # Sanitize any Firebase-specific objects for JSON serialization
            user_dict = self._sanitize_for_json(user_dict)
            users[user_id] = user_dict
            self._save_users(users)
            
            if existing_user_id:
                logger.info(f"Updated existing user from Firebase (prioritizing Firebase data): {email}")
            else:
                logger.info(f"Created new user from Firebase: {email}")
            
            return user
                
        except Exception as e:
            logger.error(f"Error creating/updating user from Firebase: {e}")
            return None
    
    def _sanitize_for_json(self, data: Any) -> Any:
        """
        Sanitize data for JSON serialization, handling Firebase-specific objects.
        
        Args:
            data: Data to sanitize
            
        Returns:
            JSON-serializable data
        """
        if isinstance(data, dict):
            return {key: self._sanitize_for_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_for_json(item) for item in data]
        elif hasattr(data, 'isoformat'):
            # Handle datetime objects (including Firebase DatetimeWithNanoseconds)
            return data.isoformat()
        elif hasattr(data, 'timestamp'):
            # Handle Firebase Timestamp objects
            return datetime.fromtimestamp(data.timestamp()).isoformat()
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            # Convert unknown objects to string
            return str(data)

# Global user manager instance
user_manager = UserManager() 