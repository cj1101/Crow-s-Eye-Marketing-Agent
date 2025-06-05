"""
Login Dialog for Crow's Eye Marketing Platform.
Provides user authentication and registration functionality.
"""
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget, QWidget,
    QMessageBox, QCheckBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap

from ...models.user import UserManager, User

class LoginDialog(QDialog):
    """Dialog for user login and registration."""
    
    # Signals
    user_logged_in = Signal(object)  # Emits User object when login successful
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_manager = UserManager()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.setWindowTitle("Crow's Eye - Login")
        self.setFixedSize(450, 600)
        self.setModal(True)
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Set up the login dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        self._create_header(layout)
        
        # Tab widget for Login/Register
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #f5f5f5;
                color: #333333;
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #007bff;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # Login tab
        self._create_login_tab()
        
        # Register tab
        self._create_register_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Footer
        self._create_footer(layout)
        
        # Apply styling
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #333333;
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 14px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
            QPushButton {
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
    
    def _create_header(self, layout: QVBoxLayout):
        """Create the header section."""
        # Logo/Title
        title_label = QLabel("🐦‍⬛ Crow's Eye")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #007bff; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Marketing Platform")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666666; font-size: 16px; margin-bottom: 20px;")
        layout.addWidget(subtitle_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(separator)
    
    def _create_login_tab(self):
        """Create the login tab."""
        login_widget = QWidget()
        layout = QVBoxLayout(login_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Email field
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Enter your email address")
        form_layout.addRow("Email:", self.login_email)
        
        # Password field
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password.setPlaceholderText("Enter your password")
        form_layout.addRow("Password:", self.login_password)
        
        layout.addLayout(form_layout)
        
        # Remember me checkbox
        self.remember_me = QCheckBox("Remember me")
        self.remember_me.setStyleSheet("color: #666666;")
        layout.addWidget(self.remember_me)
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        layout.addWidget(self.login_button)
        
        # Forgot password link
        forgot_label = QLabel('<a href="#" style="color: #007bff; text-decoration: none;">Forgot your password?</a>')
        forgot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        forgot_label.setOpenExternalLinks(False)
        layout.addWidget(forgot_label)
        
        layout.addStretch()
        
        self.tab_widget.addTab(login_widget, "Login")
    
    def _create_register_tab(self):
        """Create the register tab."""
        register_widget = QWidget()
        layout = QVBoxLayout(register_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Username field
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("Choose a username")
        form_layout.addRow("Username:", self.register_username)
        
        # Email field
        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("Enter your email address")
        form_layout.addRow("Email:", self.register_email)
        
        # Password field
        self.register_password = QLineEdit()
        self.register_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_password.setPlaceholderText("Create a password")
        form_layout.addRow("Password:", self.register_password)
        
        # Confirm password field
        self.register_confirm_password = QLineEdit()
        self.register_confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_confirm_password.setPlaceholderText("Confirm your password")
        form_layout.addRow("Confirm Password:", self.register_confirm_password)
        
        layout.addLayout(form_layout)
        
        # Terms checkbox
        self.accept_terms = QCheckBox("I agree to the Terms of Service and Privacy Policy")
        self.accept_terms.setStyleSheet("color: #666666;")
        layout.addWidget(self.accept_terms)
        
        # Register button
        self.register_button = QPushButton("Create Account")
        self.register_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        layout.addWidget(self.register_button)
        
        layout.addStretch()
        
        self.tab_widget.addTab(register_widget, "Register")
    
    def _create_footer(self, layout: QVBoxLayout):
        """Create the footer section."""
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(separator)
        
        # Footer buttons
        footer_layout = QHBoxLayout()
        
        # Continue as guest button
        self.guest_button = QPushButton("Continue as Guest")
        self.guest_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        footer_layout.addWidget(self.guest_button)
        
        footer_layout.addStretch()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        footer_layout.addWidget(self.cancel_button)
        
        layout.addLayout(footer_layout)
    
    def _connect_signals(self):
        """Connect signals to slots."""
        self.login_button.clicked.connect(self._on_login_clicked)
        self.register_button.clicked.connect(self._on_register_clicked)
        self.guest_button.clicked.connect(self._on_guest_clicked)
        self.cancel_button.clicked.connect(self.reject)
        
        # Enter key handling
        self.login_password.returnPressed.connect(self._on_login_clicked)
        self.register_confirm_password.returnPressed.connect(self._on_register_clicked)
    
    def _on_login_clicked(self):
        """Handle login button click."""
        email = self.login_email.text().strip()
        password = self.login_password.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both email and password.")
            return
        
        try:
            if self.user_manager.authenticate_user(email, password):
                user = self.user_manager.get_current_user()
                if user:
                    self.logger.info(f"User logged in successfully: {email}")
                    self.user_logged_in.emit(user)
                    self.accept()
                else:
                    QMessageBox.critical(self, "Login Error", "Authentication succeeded but failed to load user data.")
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid email or password. Please try again.")
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            QMessageBox.critical(self, "Login Error", f"An error occurred during login: {str(e)}")
    
    def _on_register_clicked(self):
        """Handle register button click."""
        username = self.register_username.text().strip()
        email = self.register_email.text().strip()
        password = self.register_password.text()
        confirm_password = self.register_confirm_password.text()
        
        # Validation
        if not all([username, email, password, confirm_password]):
            QMessageBox.warning(self, "Registration Error", "Please fill in all fields.")
            return
        
        if password != confirm_password:
            QMessageBox.warning(self, "Registration Error", "Passwords do not match.")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "Registration Error", "Password must be at least 6 characters long.")
            return
        
        if not self.accept_terms.isChecked():
            QMessageBox.warning(self, "Registration Error", "Please accept the Terms of Service and Privacy Policy.")
            return
        
        try:
            user = self.user_manager.create_user(email, username, password)
            if user:
                self.logger.info(f"User registered successfully: {email}")
                QMessageBox.information(self, "Registration Successful", 
                                      f"Account created successfully! You are now logged in as {username}.")
                self.user_logged_in.emit(user)
                self.accept()
            else:
                QMessageBox.warning(self, "Registration Failed", "Failed to create account. Email may already be in use.")
                
        except Exception as e:
            self.logger.error(f"Registration error: {e}")
            QMessageBox.critical(self, "Registration Error", f"An error occurred during registration: {str(e)}")
    
    def _on_guest_clicked(self):
        """Handle continue as guest button click."""
        self.logger.info("User chose to continue as guest")
        self.reject()  # Close dialog without logging in 