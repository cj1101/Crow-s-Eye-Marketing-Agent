"""
User authentication dialog for Crow's Eye Marketing Platform.
Handles user login, registration, and subscription management.
"""
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QStackedWidget, QWidget, QFormLayout, QMessageBox, QFrame,
    QTextEdit, QCheckBox, QProgressBar, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QPalette

from ...models.user import user_manager, User
from ...features.subscription.access_control import access_control
from ...features.authentication.firebase_auth_handler import firebase_auth_handler
from ..base_dialog import BaseDialog

logger = logging.getLogger(__name__)

class UserAuthDialog(BaseDialog):
    """Dialog for user authentication and subscription management."""
    
    login_successful = Signal(dict)
    registration_successful = Signal(dict)
    
    def __init__(self, parent=None):
        """Initialize the user authentication dialog."""
        super().__init__(parent)
        self.setWindowTitle("Crow's Eye - Account")
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
        
        self._setup_ui()
        self._check_current_user()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        self._create_header(layout)
        
        # Stacked widget for different pages
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # Create pages
        self._create_welcome_page()
        self._create_login_page()
        self._create_account_page()
        self._create_upgrade_page()
        
        # Button layout
        self._create_buttons(layout)
        
        # Start with welcome page
        self.stacked_widget.setCurrentIndex(0)
    
    def _create_header(self, layout):
        """Create the header section."""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8B5A9F, stop:1 #6D28D9);
                border-radius: 10px;
                padding: 20px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        # Title
        title_label = QLabel("🐦‍⬛ Crow's Eye")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                background: transparent;
            }
        """)
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Smart Marketing Automation Platform")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
                background: transparent;
            }
        """)
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_frame)
    
    def _create_welcome_page(self):
        """Create the welcome page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        # Welcome message
        welcome_label = QLabel("Welcome to Crow's Eye!")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 20px; color: black;")
        layout.addWidget(welcome_label)
        
        # Description
        desc_label = QLabel(
            "Create amazing social media content with AI-powered tools.\n"
            "Login with your Crow's Eye website account to get started."
        )
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 14px; color: black; margin: 10px;")
        layout.addWidget(desc_label)
        
        # Action buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        self.login_btn = QPushButton("Login to Your Account")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5A9F;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7A4F8E;
            }
        """)
        self.login_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        button_layout.addWidget(self.login_btn)
        
        # Info about account creation
        info_label = QLabel("Don't have an account? Visit crowseye.com to create one.")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("font-size: 12px; color: #666; margin: 10px;")
        button_layout.addWidget(info_label)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.stacked_widget.addWidget(page)
    
    def _create_login_page(self):
        """Create the login page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Login to Your Account")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px; color: black;")
        layout.addWidget(title_label)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Style for form labels
        form_label_style = "color: black; font-weight: bold;"
        
        email_label = QLabel("Email:")
        email_label.setStyleSheet(form_label_style)
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Enter your email")
        self.login_email.setStyleSheet("padding: 8px; border: 1px solid #ddd; border-radius: 4px; color: black;")
        form_layout.addRow(email_label, self.login_email)
        
        password_label = QLabel("Password:")
        password_label.setStyleSheet(form_label_style)
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Enter your password")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password.setStyleSheet("padding: 8px; border: 1px solid #ddd; border-radius: 4px; color: black;")
        form_layout.addRow(password_label, self.login_password)
        
        layout.addLayout(form_layout)
        
        # Single login button (Firebase only)
        login_button_layout = QVBoxLayout()
        login_button_layout.setSpacing(10)
        
        self.firebase_login_btn = QPushButton("Login")
        self.firebase_login_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5A9F;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7A4F8E;
            }
        """)
        self.firebase_login_btn.clicked.connect(self._handle_firebase_login)
        login_button_layout.addWidget(self.firebase_login_btn)
        
        layout.addLayout(login_button_layout)
        
        # Status label
        self.login_status = QLabel("")
        self.login_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.login_status.setStyleSheet("color: red; margin: 10px;")
        layout.addWidget(self.login_status)
        
        layout.addStretch()
        
        self.stacked_widget.addWidget(page)
    

    
    def _create_account_page(self):
        """Create the account management page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        # Title
        self.account_title = QLabel("Account Dashboard")
        self.account_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.account_title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px; color: black;")
        layout.addWidget(self.account_title)
        
        # User info
        self.user_info_label = QLabel("")
        self.user_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_info_label.setStyleSheet("font-size: 14px; margin: 10px; color: black;")
        layout.addWidget(self.user_info_label)
        
        # Subscription info
        self.subscription_info = QLabel("")
        self.subscription_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subscription_info.setStyleSheet("font-size: 14px; color: black; margin: 10px;")
        layout.addWidget(self.subscription_info)
        
        # Usage stats
        self.usage_stats = QTextEdit()
        self.usage_stats.setMaximumHeight(150)
        self.usage_stats.setReadOnly(True)
        self.usage_stats.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                background-color: #f9f9f9;
            }
        """)
        layout.addWidget(self.usage_stats)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.upgrade_btn = QPushButton("Upgrade to Pro")
        self.upgrade_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.upgrade_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(4))
        button_layout.addWidget(self.upgrade_btn)
        
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        self.logout_btn.clicked.connect(self._handle_logout)
        button_layout.addWidget(self.logout_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.stacked_widget.addWidget(page)
    
    def _create_upgrade_page(self):
        """Create the upgrade to Pro page."""
        page = QWidget()
        page.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                color: #000000;
            }
        """)
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Upgrade to Pro")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 20px; color: black;")
        layout.addWidget(title_label)
        
        # Price
        price_label = QLabel("$5/month")
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #10B981; margin: 10px;")
        layout.addWidget(price_label)
        
        # Benefits
        benefits_text = QTextEdit()
        benefits_text.setMaximumHeight(200)
        benefits_text.setReadOnly(True)
        benefits_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 15px;
                background-color: #ffffff;
                color: #000000;
                font-size: 14px;
                font-weight: normal;
            }
        """)
        
        benefits = access_control.get_upgrade_benefits()
        benefits_text.setPlainText("\n".join(benefits))
        layout.addWidget(benefits_text)
        
        # Upgrade button (demo)
        self.do_upgrade_btn = QPushButton("Upgrade Now (Demo)")
        self.do_upgrade_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                padding: 15px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.do_upgrade_btn.clicked.connect(self._handle_upgrade)
        layout.addWidget(self.do_upgrade_btn)
        
        # Note
        note_label = QLabel("Note: This is a demo upgrade. In production, this would integrate with a payment processor.")
        note_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note_label.setWordWrap(True)
        note_label.setStyleSheet("font-size: 12px; color: #333333; margin: 10px; font-weight: normal;")
        layout.addWidget(note_label)
        
        layout.addStretch()
        
        self.stacked_widget.addWidget(page)
    
    def _create_buttons(self, layout):
        """Create the bottom buttons."""
        button_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(self._handle_back)
        button_layout.addWidget(self.back_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def _check_current_user(self):
        """Check if user is already logged in."""
        if user_manager.is_authenticated():
            self._update_account_page()
            self.stacked_widget.setCurrentIndex(3)  # Account page
    
    def _update_account_page(self):
        """Update the account page with current user info."""
        user = user_manager.get_current_user()
        if not user:
            return
        
        # Update user info
        self.user_info_label.setText(f"Welcome, {user.username}!")
        self.subscription_info.setText(user.get_subscription_status())
        
        # Update usage stats
        usage_info = access_control.get_usage_info()
        if usage_info:
            stats_text = f"Monthly Usage:\n\n"
            for category, data in usage_info["usage"].items():
                stats_text += f"{category.title()}: {data['current']}/{data['limit']} ({data['percentage']:.1f}%)\n"
            
            self.usage_stats.setPlainText(stats_text)
        
        # Show/hide upgrade button
        self.upgrade_btn.setVisible(not user.is_pro_user())
    
    def _handle_firebase_login(self):
        """Handle Firebase login attempt."""
        email = self.login_email.text().strip()
        password = self.login_password.text().strip()
        
        if not email or not password:
            self.login_status.setText("Please enter both email and password.")
            return
        
        # Initialize Firebase if not already done
        if not firebase_auth_handler.initialize():
            setup_instructions = firebase_auth_handler.get_setup_instructions()
            QMessageBox.information(self, "Firebase Setup Required", setup_instructions)
            return
        
        # Try to authenticate with Firebase
        self.login_status.setText("Authenticating...")
        
        if firebase_auth_handler.authenticate_with_email(email, password):
            user_data = firebase_auth_handler.get_current_user()
            
            # Create or update local user based on Firebase data, prioritizing Firebase data
            local_user = user_manager.create_or_update_from_firebase(user_data)
            if local_user:
                user_manager.current_user = local_user
                user_manager._save_current_user()
                
                self.login_status.setText("")
                self._update_account_page()
                self.stacked_widget.setCurrentIndex(3)  # Account page
                self.login_successful.emit({"email": email, "source": "firebase"})
            else:
                self.login_status.setText("Failed to create user account.")
        else:
            self.login_status.setText("Invalid email or password, or Firebase not configured.")
    
    def _handle_register(self):
        """Handle registration attempt - redirect to website."""
        import webbrowser
        webbrowser.open("https://crowseye.com/register")
        QMessageBox.information(self, "Account Creation", 
                              "Please create your account on the Crow's Eye website. "
                              "Once created, you can login here with those credentials.")
    
    def _handle_upgrade(self):
        """Handle upgrade to Pro."""
        if user_manager.upgrade_to_pro("demo_payment"):
            QMessageBox.information(self, "Upgrade Successful", 
                                  "Congratulations! You've been upgraded to Pro tier.")
            self._update_account_page()
            self.stacked_widget.setCurrentIndex(3)  # Back to account page
        else:
            QMessageBox.warning(self, "Upgrade Failed", 
                              "Failed to upgrade account. Please try again.")
    
    def _handle_logout(self):
        """Handle user logout."""
        user_manager.logout()
        self.stacked_widget.setCurrentIndex(0)  # Back to welcome page
        
        # Clear form fields
        self.login_email.clear()
        self.login_password.clear()
        self.login_status.setText("")
    
    def _handle_back(self):
        """Handle back button."""
        current_index = self.stacked_widget.currentIndex()
        
        if current_index == 1 or current_index == 2:  # Login or register page
            self.stacked_widget.setCurrentIndex(0)  # Welcome page
        elif current_index == 4:  # Upgrade page
            self.stacked_widget.setCurrentIndex(3)  # Account page
        elif current_index == 3:  # Account page
            self.accept()  # Close dialog
        else:
            self.stacked_widget.setCurrentIndex(0)  # Default to welcome 