"""
Subscription status widget for displaying user tier and usage information.
"""
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from ...models.user import user_manager
from ...features.subscription.access_control import access_control
from ..dialogs.user_auth_dialog import UserAuthDialog

logger = logging.getLogger(__name__)

class SubscriptionStatusWidget(QWidget):
    """Widget to display subscription status and usage information."""
    
    upgrade_requested = Signal()
    login_requested = Signal()
    
    def __init__(self, parent=None):
        """Initialize the subscription status widget."""
        super().__init__(parent)
        self._setup_ui()
        self._setup_timer()
        self._update_display()
    
    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Main container
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        container_layout = QVBoxLayout(self.container)
        container_layout.setSpacing(8)
        
        # Header with user info
        header_layout = QHBoxLayout()
        
        self.user_label = QLabel("Not logged in")
        self.user_label.setStyleSheet("font-weight: bold; color: #495057;")
        header_layout.addWidget(self.user_label)
        
        header_layout.addStretch()
        
        self.tier_label = QLabel("Free Tier")
        self.tier_label.setStyleSheet("""
            QLabel {
                background-color: #e9ecef;
                color: #495057;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(self.tier_label)
        
        container_layout.addLayout(header_layout)
        
        # Usage section
        self.usage_frame = QFrame()
        usage_layout = QVBoxLayout(self.usage_frame)
        usage_layout.setSpacing(6)
        
        # Social accounts usage
        self.posts_layout = QHBoxLayout()
        self.posts_label = QLabel("Accounts:")
        self.posts_label.setMinimumWidth(60)
        self.posts_layout.addWidget(self.posts_label)
        
        self.posts_progress = QProgressBar()
        self.posts_progress.setMaximumHeight(16)
        self.posts_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ced4da;
                border-radius: 3px;
                text-align: center;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 2px;
            }
        """)
        self.posts_layout.addWidget(self.posts_progress)
        
        self.posts_count = QLabel("0/10")
        self.posts_count.setMinimumWidth(40)
        self.posts_count.setStyleSheet("font-size: 11px; color: #6c757d;")
        self.posts_layout.addWidget(self.posts_count)
        
        usage_layout.addLayout(self.posts_layout)
        
        # AI Content Credits usage
        self.videos_layout = QHBoxLayout()
        self.videos_label = QLabel("AI Credits:")
        self.videos_label.setMinimumWidth(60)
        self.videos_layout.addWidget(self.videos_label)
        
        self.videos_progress = QProgressBar()
        self.videos_progress.setMaximumHeight(16)
        self.videos_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ced4da;
                border-radius: 3px;
                text-align: center;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #17a2b8;
                border-radius: 2px;
            }
        """)
        self.videos_layout.addWidget(self.videos_progress)
        
        self.videos_count = QLabel("0/0")
        self.videos_count.setMinimumWidth(40)
        self.videos_count.setStyleSheet("font-size: 11px; color: #6c757d;")
        self.videos_layout.addWidget(self.videos_count)
        
        usage_layout.addLayout(self.videos_layout)
        
        # AI Image Edits usage
        self.ai_layout = QHBoxLayout()
        self.ai_label = QLabel("AI Edits:")
        self.ai_label.setMinimumWidth(60)
        self.ai_layout.addWidget(self.ai_label)
        
        self.ai_progress = QProgressBar()
        self.ai_progress.setMaximumHeight(16)
        self.ai_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ced4da;
                border-radius: 3px;
                text-align: center;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #ffc107;
                border-radius: 2px;
            }
        """)
        self.ai_layout.addWidget(self.ai_progress)
        
        self.ai_count = QLabel("0/20")
        self.ai_count.setMinimumWidth(40)
        self.ai_count.setStyleSheet("font-size: 11px; color: #6c757d;")
        self.ai_layout.addWidget(self.ai_count)
        
        usage_layout.addLayout(self.ai_layout)
        
        container_layout.addWidget(self.usage_frame)
        
        # Action button
        self.action_button = QPushButton("Login")
        self.action_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.action_button.clicked.connect(self._handle_action_button)
        container_layout.addWidget(self.action_button)
        
        layout.addWidget(self.container)
        
        # Set maximum height
        self.setMaximumHeight(180)
    
    def _setup_timer(self):
        """Set up timer for periodic updates."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(30000)  # Update every 30 seconds
    
    def _update_display(self):
        """Update the display with current user information."""
        try:
            user = user_manager.get_current_user()
            
            if not user:
                # Not logged in
                self._show_not_logged_in()
                return
            
            # Update user info
            self.user_label.setText(f"Welcome, {user.username}")
            
            # Update tier display based on subscription tier
            tier_name = user.subscription.tier.value.replace("_", " ").title()
            self.tier_label.setText(f"{tier_name} Tier")
            
            # Set tier-specific styling
            if user.subscription.tier.value == "free":
                self.tier_label.setStyleSheet("""
                    QLabel {
                        background-color: #e9ecef;
                        color: #495057;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)
                self.action_button.setText("Upgrade Plan")
                self.action_button.setStyleSheet("""
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-weight: bold;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #218838;
                    }
                """)
            elif user.subscription.tier.value == "creator":
                self.tier_label.setStyleSheet("""
                    QLabel {
                        background-color: #d1ecf1;
                        color: #0c5460;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)
                self.action_button.setText("Manage Account")
            elif user.subscription.tier.value == "pro":
                self.tier_label.setStyleSheet("""
                    QLabel {
                        background-color: #fff3cd;
                        color: #856404;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)
                self.action_button.setText("Manage Account")
            elif user.subscription.tier.value == "business":
                self.tier_label.setStyleSheet("""
                    QLabel {
                        background-color: #d4edda;
                        color: #155724;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)
                self.action_button.setText("Manage Account")
            else:  # business or any other tier
                self.tier_label.setStyleSheet("""
                    QLabel {
                        background-color: #e2e3e5;
                        color: #383d41;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)
                self.action_button.setText("Manage Account")
            
            # Update usage information
            usage_info = access_control.get_usage_info()
            if usage_info:
                self._update_usage_bars(usage_info)
            
            # Show usage frame
            self.usage_frame.setVisible(True)
            
        except Exception as e:
            logger.error(f"Error updating subscription status display: {e}")
            self._show_error_state()
    
    def _show_not_logged_in(self):
        """Show not logged in state."""
        self.user_label.setText("Not logged in")
        self.tier_label.setText("Guest")
        self.tier_label.setStyleSheet("""
            QLabel {
                background-color: #f8d7da;
                color: #721c24;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        self.action_button.setText("Login")
        self.action_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.usage_frame.setVisible(False)
    
    def _show_error_state(self):
        """Show error state."""
        self.user_label.setText("Error loading account")
        self.tier_label.setText("Error")
        self.tier_label.setStyleSheet("""
            QLabel {
                background-color: #f8d7da;
                color: #721c24;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        self.usage_frame.setVisible(False)
    
    def _update_usage_bars(self, usage_info):
        """Update usage progress bars."""
        try:
            # Social Accounts
            if "social_accounts" in usage_info["usage"]:
                accounts_data = usage_info["usage"]["social_accounts"]
                self.posts_progress.setMaximum(max(accounts_data["limit"], 1))
                self.posts_progress.setValue(accounts_data["current"])
                self.posts_count.setText(f"{accounts_data['current']}/{accounts_data['limit']}")
                
                # Color code based on usage
                if accounts_data["percentage"] >= 90:
                    accounts_color = "#dc3545"  # Red
                elif accounts_data["percentage"] >= 75:
                    accounts_color = "#ffc107"  # Yellow
                else:
                    accounts_color = "#28a745"  # Green
                
                self.posts_progress.setStyleSheet(f"""
                    QProgressBar {{
                        border: 1px solid #ced4da;
                        border-radius: 3px;
                        text-align: center;
                        font-size: 10px;
                    }}
                    QProgressBar::chunk {{
                        background-color: {accounts_color};
                        border-radius: 2px;
                    }}
                """)
            
            # AI Content Credits
            if "ai_content_credits_per_month" in usage_info["usage"]:
                ai_data = usage_info["usage"]["ai_content_credits_per_month"]
                self.videos_progress.setMaximum(max(ai_data["limit"], 1))
                self.videos_progress.setValue(ai_data["current"])
                self.videos_count.setText(f"{ai_data['current']}/{ai_data['limit']}")
                
                if ai_data["percentage"] >= 90:
                    ai_color = "#dc3545"  # Red
                elif ai_data["percentage"] >= 75:
                    ai_color = "#ffc107"  # Yellow
                else:
                    ai_color = "#17a2b8"  # Blue
                
                self.videos_progress.setStyleSheet(f"""
                    QProgressBar {{
                        border: 1px solid #ced4da;
                        border-radius: 3px;
                        text-align: center;
                        font-size: 10px;
                    }}
                    QProgressBar::chunk {{
                        background-color: {ai_color};
                        border-radius: 2px;
                    }}
                """)
            
            # AI Image Edits
            if "ai_image_edits_per_month" in usage_info["usage"]:
                edits_data = usage_info["usage"]["ai_image_edits_per_month"]
                self.ai_progress.setMaximum(max(edits_data["limit"], 1))
                self.ai_progress.setValue(edits_data["current"])
                self.ai_count.setText(f"{edits_data['current']}/{edits_data['limit']}")
                
                if edits_data["percentage"] >= 90:
                    edits_color = "#dc3545"  # Red
                elif edits_data["percentage"] >= 75:
                    edits_color = "#ffc107"  # Yellow
                else:
                    edits_color = "#6f42c1"  # Purple
                
                self.ai_progress.setStyleSheet(f"""
                    QProgressBar {{
                        border: 1px solid #ced4da;
                        border-radius: 3px;
                        text-align: center;
                        font-size: 10px;
                    }}
                    QProgressBar::chunk {{
                        background-color: {edits_color};
                        border-radius: 2px;
                    }}
                """)
            
        except Exception as e:
            logger.error(f"Error updating usage bars: {e}")
    
    def _handle_action_button(self):
        """Handle action button click."""
        try:
            user = user_manager.get_current_user()
            
            if not user:
                # Show login dialog
                self._show_auth_dialog()
            elif user.is_pro_user():
                # Show account management
                self._show_auth_dialog()
            else:
                # Show upgrade dialog
                self._show_auth_dialog()
                
        except Exception as e:
            logger.error(f"Error handling action button: {e}")
            QMessageBox.warning(self, "Error", "An error occurred. Please try again.")
    
    def _show_auth_dialog(self):
        """Show the authentication dialog."""
        try:
            dialog = UserAuthDialog(self)
            dialog.login_successful.connect(self._on_auth_success)
            dialog.registration_successful.connect(self._on_auth_success)
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Error showing auth dialog: {e}")
    
    def _on_auth_success(self, user_data):
        """Handle successful authentication."""
        self._update_display()
        logger.info(f"User authenticated: {user_data}")
    
    def refresh(self):
        """Manually refresh the display."""
        self._update_display()
    
    def get_current_user_tier(self) -> str:
        """Get the current user's subscription tier."""
        user = user_manager.get_current_user()
        if not user:
            return "guest"
        
        return user.subscription.tier.value
    
    def is_feature_available(self, feature_name: str) -> bool:
        """Check if a feature is available for the current user."""
        from ...features.subscription.access_control import Feature, access_control
        
        try:
            # Map feature names to Feature enum
            feature_map = {
                "veo_video_generator": Feature.VEO_VIDEO_GENERATOR,
                "highlight_reel_generator": Feature.HIGHLIGHT_REEL_GENERATOR,
                "full_video_processing_suite": Feature.FULL_VIDEO_PROCESSING_SUITE,
                "advanced_ai_features": Feature.ADVANCED_AI_FEATURES,
                "bulk_operations": Feature.BULK_OPERATIONS,
                "custom_branding": Feature.CUSTOM_BRANDING,
                "smart_gallery_generator": Feature.SMART_GALLERY_GENERATOR,
                "post_formatting": Feature.POST_FORMATTING,
                "basic_video_processing": Feature.BASIC_VIDEO_PROCESSING,
                "smart_media_search": Feature.SMART_MEDIA_SEARCH,
                "advanced_analytics": Feature.ADVANCED_ANALYTICS,
                "team_collaboration": Feature.TEAM_COLLABORATION,
                "dedicated_account_manager": Feature.DEDICATED_ACCOUNT_MANAGER,
                "unlimited_team_members": Feature.UNLIMITED_TEAM_MEMBERS,
            }
            
            feature = feature_map.get(feature_name)
            if feature:
                return access_control.has_feature_access(feature)
            
            return True  # Default to available for unknown features
            
        except Exception as e:
            logger.error(f"Error checking feature availability: {e}")
            return True 