#!/usr/bin/env python3
"""
Test script for the Crow's Eye subscription system.
Demonstrates user authentication, subscription tiers, and feature access control.
"""
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QMessageBox
from PySide6.QtCore import Qt

from src.models.user import user_manager, SubscriptionTier
from src.features.subscription.access_control import Feature, access_control
from src.ui.dialogs.user_auth_dialog import UserAuthDialog
from src.ui.widgets.subscription_status_widget import SubscriptionStatusWidget
from src.utils.subscription_utils import (
    check_feature_access_with_dialog,
    check_usage_limit_with_dialog,
    requires_feature_qt,
    requires_usage_qt
)

class SubscriptionTestWindow(QMainWindow):
    """Test window for subscription system."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crow's Eye Subscription System Test")
        self.setMinimumSize(600, 500)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the test UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🐦‍⬛ Crow's Eye Subscription System Test")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # Subscription status widget
        self.status_widget = SubscriptionStatusWidget()
        layout.addWidget(self.status_widget)
        
        # Test buttons
        self._create_test_buttons(layout)
        
        # Current status display
        self.status_label = QLabel("Ready to test subscription features")
        self.status_label.setStyleSheet("padding: 10px; background-color: #f8f9fa; border-radius: 4px;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def _create_test_buttons(self, layout):
        """Create test buttons for different features."""
        
        # Authentication buttons
        auth_label = QLabel("Authentication:")
        auth_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(auth_label)
        
        login_btn = QPushButton("Show Login/Register Dialog")
        login_btn.clicked.connect(self._show_auth_dialog)
        layout.addWidget(login_btn)
        
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self._logout)
        layout.addWidget(logout_btn)
        
        # Free tier features
        free_label = QLabel("Free Tier Features:")
        free_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(free_label)
        
        gallery_btn = QPushButton("Smart Gallery Generator")
        gallery_btn.clicked.connect(self._test_gallery_generator)
        layout.addWidget(gallery_btn)
        
        post_btn = QPushButton("Create Post (Uses Post Quota)")
        post_btn.clicked.connect(self._test_create_post)
        layout.addWidget(post_btn)
        
        # Pro tier features
        pro_label = QLabel("Pro Tier Features:")
        pro_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(pro_label)
        
        video_btn = QPushButton("🎬 Veo Video Generator (Pro)")
        video_btn.setStyleSheet("""
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
        """)
        video_btn.clicked.connect(self._test_video_generator)
        layout.addWidget(video_btn)
        
        analytics_btn = QPushButton("📊 Performance Analytics (Pro)")
        analytics_btn.setStyleSheet("""
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
        """)
        analytics_btn.clicked.connect(self._test_analytics)
        layout.addWidget(analytics_btn)
        
        # Admin buttons
        admin_label = QLabel("Admin/Demo Functions:")
        admin_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(admin_label)
        
        upgrade_btn = QPushButton("Simulate Pro Upgrade")
        upgrade_btn.clicked.connect(self._simulate_upgrade)
        layout.addWidget(upgrade_btn)
        
        reset_btn = QPushButton("Reset Usage Stats")
        reset_btn.clicked.connect(self._reset_usage)
        layout.addWidget(reset_btn)
    
    def _show_auth_dialog(self):
        """Show authentication dialog."""
        dialog = UserAuthDialog(self)
        dialog.login_successful.connect(self._on_auth_success)
        dialog.registration_successful.connect(self._on_auth_success)
        dialog.exec()
    
    def _logout(self):
        """Logout current user."""
        user_manager.logout()
        self.status_widget.refresh()
        self._update_status("Logged out successfully")
    
    def _on_auth_success(self, user_data):
        """Handle successful authentication."""
        self.status_widget.refresh()
        self._update_status(f"Logged in as: {user_data.get('email', 'Unknown')}")
    
    def _test_gallery_generator(self):
        """Test gallery generator (free feature)."""
        if check_feature_access_with_dialog(Feature.SMART_GALLERY_GENERATOR, self):
            if check_usage_limit_with_dialog('ai_requests', 1, self):
                user_manager.increment_usage('ai_requests', 1)
                self.status_widget.refresh()
                self._update_status("Gallery generated successfully! (Used 1 AI request)")
            else:
                self._update_status("AI request limit exceeded")
        else:
            self._update_status("Access denied to gallery generator")
    
    @requires_usage_qt('posts', 1)
    def _test_create_post(self):
        """Test creating a post (uses post quota)."""
        self.status_widget.refresh()
        self._update_status("Post created successfully! (Used 1 post quota)")
    
    @requires_feature_qt(Feature.VEO_VIDEO_GENERATOR)
    @requires_usage_qt('videos', 1)
    def _test_video_generator(self):
        """Test video generator (Pro feature + video quota)."""
        self.status_widget.refresh()
        self._update_status("Video generated successfully! (Used 1 video quota)")
    
    @requires_feature_qt(Feature.PERFORMANCE_ANALYTICS)
    def _test_analytics(self):
        """Test analytics (Pro feature)."""
        self._update_status("Analytics dashboard opened! (Pro feature)")
    
    def _simulate_upgrade(self):
        """Simulate upgrading to Pro."""
        if user_manager.is_authenticated():
            if user_manager.upgrade_to_pro("demo_payment"):
                self.status_widget.refresh()
                self._update_status("Upgraded to Pro tier successfully!")
            else:
                self._update_status("Failed to upgrade to Pro")
        else:
            self._update_status("Please log in first")
    
    def _reset_usage(self):
        """Reset usage statistics."""
        if user_manager.is_authenticated():
            user_manager.reset_monthly_usage()
            self.status_widget.refresh()
            self._update_status("Usage statistics reset")
        else:
            self._update_status("Please log in first")
    
    def _update_status(self, message: str):
        """Update status message."""
        self.status_label.setText(f"Status: {message}")
        print(f"[TEST] {message}")

def main():
    """Main function to run the test."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Crow's Eye Subscription Test")
    app.setApplicationVersion("1.0.0")
    
    # Create and show test window
    window = SubscriptionTestWindow()
    window.show()
    
    # Print initial status
    print("🐦‍⬛ Crow's Eye Subscription System Test")
    print("=" * 50)
    print("This test demonstrates:")
    print("1. User authentication (login/register)")
    print("2. Subscription tier management (Free/Pro)")
    print("3. Feature access control")
    print("4. Usage limit enforcement")
    print("5. Upgrade dialogs and flows")
    print()
    print("Try the different buttons to test various features!")
    print("=" * 50)
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 