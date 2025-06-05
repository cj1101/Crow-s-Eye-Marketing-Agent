"""
Utility functions for subscription and access control integration.
"""
import logging
from typing import Optional, Callable, Any
from functools import wraps

from PySide6.QtWidgets import QMessageBox, QWidget
from PySide6.QtCore import QObject

from ..models.user import user_manager, SubscriptionTier
from ..features.subscription.access_control import (
    access_control, Feature, AccessControlError, 
    requires_feature, requires_usage_limit
)

logger = logging.getLogger(__name__)

def show_upgrade_dialog(parent: Optional[QWidget] = None, feature_name: str = "") -> bool:
    """
    Show upgrade dialog when user tries to access Pro features.
    
    Args:
        parent: Parent widget for the dialog
        feature_name: Name of the feature that requires upgrade
        
    Returns:
        bool: True if user wants to upgrade, False otherwise
    """
    try:
        from ..ui.dialogs.user_auth_dialog import UserAuthDialog
        
        # Get current user's tier for upgrade benefits
        user = user_manager.get_current_user()
        current_tier = user.subscription.tier if user else SubscriptionTier.FREE
        
        # Get upgrade benefits
        benefits = access_control.get_upgrade_benefits(current_tier)
        
        # Create message
        if feature_name:
            title = f"Upgrade Required for {feature_name}"
            message = f"The {feature_name} feature requires a higher subscription tier.\n\nChoose from our flexible plans:"
        else:
            title = "Upgrade Your Plan"
            message = "Choose from our flexible plans to unlock more features:"
        
        # Show message box with upgrade option
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setDetailedText("\n".join(benefits))
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        msg_box.button(QMessageBox.StandardButton.Yes).setText("View Plans")
        msg_box.button(QMessageBox.StandardButton.No).setText("Maybe Later")
        
        result = msg_box.exec()
        
        if result == QMessageBox.StandardButton.Yes:
            # Show auth dialog with upgrade page
            dialog = UserAuthDialog(parent)
            dialog.exec()
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error showing upgrade dialog: {e}")
        return False

def show_login_required_dialog(parent: Optional[QWidget] = None) -> bool:
    """
    Show login required dialog.
    
    Args:
        parent: Parent widget for the dialog
        
    Returns:
        bool: True if user logged in, False otherwise
    """
    try:
        from ..ui.dialogs.user_auth_dialog import UserAuthDialog
        
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle("Login Required")
        msg_box.setText("You need to be logged in to use this feature.")
        msg_box.setInformativeText("Would you like to log in or create an account?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        msg_box.button(QMessageBox.StandardButton.Yes).setText("Login/Register")
        msg_box.button(QMessageBox.StandardButton.No).setText("Cancel")
        
        result = msg_box.exec()
        
        if result == QMessageBox.StandardButton.Yes:
            dialog = UserAuthDialog(parent)
            dialog.exec()
            return user_manager.is_authenticated()
        
        return False
        
    except Exception as e:
        logger.error(f"Error showing login dialog: {e}")
        return False

def show_usage_limit_dialog(parent: Optional[QWidget] = None, usage_type: str = "", limit: int = 0) -> bool:
    """
    Show usage limit exceeded dialog.
    
    Args:
        parent: Parent widget for the dialog
        usage_type: Type of usage that was exceeded
        limit: The limit that was exceeded
        
    Returns:
        bool: True if user wants to upgrade, False otherwise
    """
    try:
        user = user_manager.get_current_user()
        if not user:
            return show_login_required_dialog(parent)
        
        if user.is_pro_user():
            # Pro user hit limit - just inform them
            QMessageBox.information(
                parent,
                "Usage Limit Reached",
                f"You've reached your monthly limit of {limit} {usage_type}.\n"
                f"Your limit will reset at the beginning of next month."
            )
            return False
        else:
            # Free user - offer upgrade
            msg_box = QMessageBox(parent)
            msg_box.setWindowTitle("Usage Limit Reached")
            msg_box.setText(f"You've reached your monthly limit of {limit} {usage_type}.")
            msg_box.setInformativeText("Upgrade to a higher tier for increased limits and more features!")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            msg_box.button(QMessageBox.StandardButton.Yes).setText("View Plans")
            msg_box.button(QMessageBox.StandardButton.No).setText("Maybe Later")
            
            result = msg_box.exec()
            
            if result == QMessageBox.StandardButton.Yes:
                return show_upgrade_dialog(parent, f"{usage_type} limit increase")
            
            return False
        
    except Exception as e:
        logger.error(f"Error showing usage limit dialog: {e}")
        return False

def check_feature_access_with_dialog(feature: Feature, parent: Optional[QWidget] = None) -> bool:
    """
    Check feature access and show appropriate dialog if access is denied.
    
    Args:
        feature: The feature to check
        parent: Parent widget for dialogs
        
    Returns:
        bool: True if access is granted, False otherwise
    """
    try:
        if access_control.has_feature_access(feature):
            return True
        
        # Check if user is logged in
        if not user_manager.is_authenticated():
            return show_login_required_dialog(parent)
        
        # User is logged in but doesn't have access - show upgrade dialog
        feature_name = feature.value.replace("_", " ").title()
        return show_upgrade_dialog(parent, feature_name)
        
    except Exception as e:
        logger.error(f"Error checking feature access: {e}")
        return False

def check_usage_limit_with_dialog(usage_type: str, amount: int = 1, parent: Optional[QWidget] = None) -> bool:
    """
    Check usage limit and show appropriate dialog if limit is exceeded.
    
    Args:
        usage_type: Type of usage to check
        amount: Amount being requested
        parent: Parent widget for dialogs
        
    Returns:
        bool: True if within limits, False otherwise
    """
    try:
        if access_control.check_usage_limit(usage_type, amount):
            return True
        
        # Check if user is logged in
        if not user_manager.is_authenticated():
            return show_login_required_dialog(parent)
        
        # Get the limit for this usage type
        user = user_manager.get_current_user()
        if user:
            from ..features.subscription.access_control import USAGE_LIMITS
            limits = USAGE_LIMITS.get(user.subscription.tier)
            if limits:
                limit = limits.get(f"{usage_type}_per_month", 0)
                return show_usage_limit_dialog(parent, usage_type, limit)
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking usage limit: {e}")
        return False

def safe_feature_execution(feature: Feature, func: Callable, parent: Optional[QWidget] = None, *args, **kwargs) -> Any:
    """
    Safely execute a function that requires a specific feature.
    
    Args:
        feature: The required feature
        func: Function to execute
        parent: Parent widget for dialogs
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        The result of the function, or None if access was denied
    """
    try:
        if not check_feature_access_with_dialog(feature, parent):
            return None
        
        return func(*args, **kwargs)
        
    except AccessControlError as e:
        logger.warning(f"Access control error: {e}")
        show_upgrade_dialog(parent, feature.value)
        return None
    except Exception as e:
        logger.error(f"Error in safe feature execution: {e}")
        QMessageBox.critical(parent, "Error", f"An error occurred: {str(e)}")
        return None

def safe_usage_execution(usage_type: str, func: Callable, parent: Optional[QWidget] = None, amount: int = 1, *args, **kwargs) -> Any:
    """
    Safely execute a function that consumes usage quota.
    
    Args:
        usage_type: Type of usage being consumed
        func: Function to execute
        parent: Parent widget for dialogs
        amount: Amount of usage being consumed
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        The result of the function, or None if limit was exceeded
    """
    try:
        if not check_usage_limit_with_dialog(usage_type, amount, parent):
            return None
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Increment usage on success
        user_manager.increment_usage(usage_type, amount)
        
        return result
        
    except AccessControlError as e:
        logger.warning(f"Usage limit error: {e}")
        user = user_manager.get_current_user()
        if user:
            from ..features.subscription.access_control import USAGE_LIMITS
            limits = USAGE_LIMITS.get(user.subscription.tier)
            if limits:
                limit = limits.get(f"{usage_type}_per_month", 0)
                show_usage_limit_dialog(parent, usage_type, limit)
        return None
    except Exception as e:
        logger.error(f"Error in safe usage execution: {e}")
        QMessageBox.critical(parent, "Error", f"An error occurred: {str(e)}")
        return None

def get_user_tier_display() -> str:
    """
    Get a display-friendly string for the current user's tier.
    
    Returns:
        str: User tier display string
    """
    user = user_manager.get_current_user()
    if not user:
        return "Not logged in"
    
    return user.get_subscription_status()

def get_feature_availability_message(feature: Feature) -> str:
    """
    Get a message explaining feature availability.
    
    Args:
        feature: The feature to check
        
    Returns:
        str: Availability message
    """
    if access_control.has_feature_access(feature):
        return "Available"
    
    if not user_manager.is_authenticated():
        return "Login required"
    
    return "Pro subscription required"

def create_pro_feature_button_style() -> str:
    """
    Get CSS style for buttons that require Pro features.
    
    Returns:
        str: CSS style string
    """
    return """
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #FFD700, stop:1 #FFA500);
            color: #8B4513;
            border: 2px solid #DAA520;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #FFA500, stop:1 #FF8C00);
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
            border: 1px solid #999999;
        }
    """

def create_usage_warning_style(percentage: float) -> str:
    """
    Get CSS style based on usage percentage.
    
    Args:
        percentage: Usage percentage (0-100)
        
    Returns:
        str: CSS style string
    """
    if percentage >= 90:
        return "color: #dc3545; font-weight: bold;"  # Red
    elif percentage >= 75:
        return "color: #ffc107; font-weight: bold;"  # Yellow
    else:
        return "color: #28a745;"  # Green

# Decorator for Qt widget methods that require features
def requires_feature_qt(feature: Feature):
    """
    Decorator for Qt widget methods that require specific features.
    Shows appropriate dialogs if access is denied.
    
    Args:
        feature: The required feature
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get parent widget
            parent = self if isinstance(self, QWidget) else None
            
            if not check_feature_access_with_dialog(feature, parent):
                return None
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

# Decorator for Qt widget methods that consume usage
def requires_usage_qt(usage_type: str, amount: int = 1):
    """
    Decorator for Qt widget methods that consume usage quota.
    Shows appropriate dialogs if limits are exceeded.
    
    Args:
        usage_type: Type of usage being consumed
        amount: Amount of usage being consumed
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get parent widget
            parent = self if isinstance(self, QWidget) else None
            
            if not check_usage_limit_with_dialog(usage_type, amount, parent):
                return None
            
            # Execute function
            result = func(self, *args, **kwargs)
            
            # Increment usage on success
            user_manager.increment_usage(usage_type, amount)
            
            return result
        return wrapper
    return decorator 