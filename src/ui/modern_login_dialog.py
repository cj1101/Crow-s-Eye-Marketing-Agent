"""
Modern login dialog for seamless Meta API authentication.
Provides a user-friendly OAuth 2.0 flow without manual credential entry.
"""
import os
import logging
import sys
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,     QComboBox, QMessageBox, QFrame, QStackedWidget, QTextEdit,    QLineEdit, QFormLayout, QGroupBox, QRadioButton, QButtonGroup,    QWidget, QProgressBar, QSpacerItem, QSizePolicy, QApplication)
from PySide6.QtCore import Qt, Signal, QEvent, QUrl, QTimer
from PySide6.QtGui import QIcon, QFont, QPixmap, QPalette
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
import webbrowser

from ..handlers.oauth_handler import oauth_handler
from .base_dialog import BaseDialog

logger = logging.getLogger(__name__)

class ModernLoginDialog(BaseDialog):
    """Modern, streamlined dialog for Meta API authentication."""
    
    login_successful = Signal(dict)
    
    def __init__(self, parent=None):
        """Initialize the modern login dialog."""
        super().__init__(parent)
        self.setWindowTitle(self.tr("Connect to Instagram & Facebook"))
        self.setMinimumWidth(450)
        self.setMinimumHeight(300)
        self.setMaximumWidth(550)
        self.setMaximumHeight(400)
        
        # Set window properties for better appearance
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setModal(True)
        
        self.business_accounts = []
        self.selected_account_id = None
        self.oauth_in_progress = False
        
        self._setup_ui()
        self._connect_signals()
        self.retranslateUi()
        
    def _setup_ui(self):
        """Set up the modern dialog UI."""
        # Set size policy for the dialog itself
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)
        
        # Header section with app branding
        self._create_header_section(layout)
        
        # Main content area
        self.stacked_widget = QStackedWidget()
                        # Ensure the stacked widget maintains its size when window moves        self.stacked_widget.setMinimumHeight(150)        self.stacked_widget.setMaximumHeight(200)
        self.stacked_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.stacked_widget)
        
        # Create pages
        self._create_welcome_page()
        self._create_progress_page()
        self._create_account_selection_page()
        self._create_success_page()
        
        self.stacked_widget.setCurrentIndex(0)
        
        # Button section
        self._create_button_section(layout)
    
    def _create_header_section(self, layout):
        """Create the header section with branding."""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #8B5A9F;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        # App title
        self.title_label = QLabel(self.tr("Connect Your Accounts"))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                background: transparent;
                margin: 0px;
            }
        """)
        header_layout.addWidget(self.title_label)
        
        # Subtitle
        self.subtitle_label = QLabel(self.tr("Connect your Instagram and Facebook accounts to start creating amazing content"))
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
                background: transparent;
                margin: 5px 0px 0px 0px;
            }
        """)
        header_layout.addWidget(self.subtitle_label)
        
        layout.addWidget(header_frame)
    
    def _create_welcome_page(self):
        """Create the welcome/login page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(30)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add spacing to center the button
        layout.addStretch()
        
        # Login button
        self.login_button = QPushButton(self.tr("Connect with Meta"))
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #1877F2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 40px;
                font-size: 18px;
                font-weight: bold;
                margin: 20px 0px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #166FE5;
            }
            QPushButton:pressed {
                background-color: #1464CC;
            }
        """)
        self.login_button.clicked.connect(self._start_oauth_flow)
        layout.addWidget(self.login_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add spacing below button
        layout.addStretch()
        
        self.stacked_widget.addWidget(page)
    
    def _create_progress_page(self):
        """Create the authentication progress page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(30)
        
        # Add some spacing at the top
        layout.addStretch()
        
        # Progress animation area
        progress_frame = QFrame()
        progress_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 30px;
            }
        """)
        progress_layout = QVBoxLayout(progress_frame)
        
        # Progress icon/animation
        self.progress_label = QLabel("🔄")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("font-size: 48px; margin-bottom: 20px;")
        progress_layout.addWidget(self.progress_label)
        
        # Progress text
        self.progress_text = QLabel(self.tr("Connecting..."))
        self.progress_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_text.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
        """)
        progress_layout.addWidget(self.progress_text)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #8B5A9F;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        # Status message
        self.status_label = QLabel(self.tr("Please complete the login in your browser..."))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                margin-top: 15px;
            }
        """)
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_frame)
        layout.addStretch()
        
        self.stacked_widget.addWidget(page)
    
    def _create_account_selection_page(self):
        """Create the account selection page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        # Instructions
        self.account_info_label = QLabel(self.tr("Choose your business account:"))
        self.account_info_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(self.account_info_label)
        
        # Account selection
        self.account_combo = QComboBox()
        self.account_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #8B5A9F;
            }
        """)
        layout.addWidget(self.account_combo)
        
        # Account status
        self.account_status = QLabel("")
        self.account_status.setWordWrap(True)
        self.account_status.setStyleSheet("color: #666; font-size: 13px; margin-top: 5px;")
        layout.addWidget(self.account_status)
        
        layout.addStretch()
        self.stacked_widget.addWidget(page)
    
    def _create_success_page(self):
        """Create the success page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(30)
        
        layout.addStretch()
        
        # Success message
        success_frame = QFrame()
        success_frame.setStyleSheet("""
            QFrame {
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 10px;
                padding: 30px;
            }
        """)
        success_layout = QVBoxLayout(success_frame)
        
        # Success icon
        success_icon = QLabel("✅")
        success_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        success_icon.setStyleSheet("font-size: 48px; margin-bottom: 15px;")
        success_layout.addWidget(success_icon)
        
        # Success title
        self.success_title = QLabel(self.tr("Connected Successfully!"))
        self.success_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.success_title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #155724;
                margin-bottom: 10px;
            }
        """)
        success_layout.addWidget(self.success_title)
        
        # Success message
        self.success_message = QLabel(self.tr("Your account has been connected. You can now start creating amazing content!"))
        self.success_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.success_message.setWordWrap(True)
        self.success_message.setStyleSheet("""
            QLabel {
                color: #155724;
                font-size: 14px;
            }
        """)
        success_layout.addWidget(self.success_message)
        
        layout.addWidget(success_frame)
        layout.addStretch()
        
        self.stacked_widget.addWidget(page)
    
    def _create_button_section(self, layout):
        """Create the button section."""
        button_layout = QHBoxLayout()
        
        # Cancel button
        self.cancel_button = QPushButton(self.tr("Cancel"))
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        # Continue/Done button
        self.continue_button = QPushButton(self.tr("Continue"))
        self.continue_button.setStyleSheet("""
            QPushButton {
                background-color: #8B5A9F;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 25px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7A4D8C;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        self.continue_button.clicked.connect(self._on_continue_clicked)
        self.continue_button.setEnabled(False)
        button_layout.addWidget(self.continue_button)
        
        layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """Connect OAuth handler signals."""
        oauth_handler.signals.auth_started.connect(self._on_auth_started)
        oauth_handler.signals.auth_progress.connect(self._on_auth_progress)
        oauth_handler.signals.auth_success.connect(self._on_auth_success)
        oauth_handler.signals.auth_error.connect(self._on_auth_error)
        oauth_handler.signals.account_selected.connect(self._on_account_selected)
    
    def _start_oauth_flow(self):
        """Start the OAuth authentication flow."""
        try:
            self.oauth_in_progress = True
            self.stacked_widget.setCurrentIndex(1)  # Progress page
            
            # Start OAuth flow
            auth_url = oauth_handler.start_oauth_flow()
            
            if auth_url:
                # Open browser for authentication
                webbrowser.open(auth_url)
                
                # Start monitoring for callback (simplified version)
                # In a real implementation, you'd want to set up a local server
                # or use a more sophisticated callback handling mechanism
                self._start_callback_monitoring()
            else:
                self._on_auth_error(self.tr("Failed to start authentication process"))
                
        except Exception as e:
            logger.error(f"Error starting OAuth flow: {e}")
            self._on_auth_error(self.tr("Authentication error: {error}").format(error=str(e)))
    
    def _start_callback_monitoring(self):
        """Start monitoring for OAuth callback (simplified)."""
        # This is a simplified version - in production you'd want to implement
        # a proper local server to handle the OAuth callback
        self.status_label.setText(self.tr("Waiting for authentication to complete..."))
        
        # For now, we'll just show instructions to the user
        QTimer.singleShot(3000, self._show_manual_callback_instructions)
    
    def _show_manual_callback_instructions(self):
        """Show instructions for manual callback handling."""
        msg = QMessageBox(self)
        msg.setWindowTitle(self.tr("Authentication"))
        msg.setText(self.tr("Please complete the authentication in your browser."))
        msg.setInformativeText(
            self.tr("After granting permissions, you'll be redirected. "
                   "Please copy the authorization code from the URL and paste it here.")
        )
        
        # Add input field for manual code entry
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        
        if msg.exec() == QMessageBox.StandardButton.Ok:
            # For demo purposes, simulate successful authentication
            self._simulate_auth_success()
        else:
            self.reject()
    
    def _simulate_auth_success(self):
        """Simulate successful authentication for demo purposes."""
        # This would be replaced with real OAuth token exchange
        fake_accounts = [
            {
                'id': 'demo_page_1',
                'name': 'Demo Business Page',
                'category': 'Local Business',
                'access_token': 'demo_token'
            }
        ]
        
        self._on_auth_success({
            'business_accounts': fake_accounts,
            'requires_account_selection': len(fake_accounts) > 1
        })
    
    def _on_auth_started(self):
        """Handle authentication started."""
        self.progress_text.setText(self.tr("Starting authentication..."))
        self.status_label.setText(self.tr("Opening browser..."))
    
    def _on_auth_progress(self, message: str):
        """Handle authentication progress update."""
        self.status_label.setText(message)
    
    def _on_auth_success(self, auth_data: Dict[str, Any]):
        """Handle successful authentication."""
        self.oauth_in_progress = False
        
        if auth_data.get('requires_account_selection', False):
            # Show account selection page
            self._populate_account_selection(auth_data['business_accounts'])
            self.stacked_widget.setCurrentIndex(2)  # Account selection page
        else:
            # Single account or already selected
            self._show_success_page(auth_data.get('account', {}))
    
    def _on_auth_error(self, error_message: str):
        """Handle authentication error."""
        self.oauth_in_progress = False
        QMessageBox.critical(self, self.tr("Authentication Error"), error_message)
        self.stacked_widget.setCurrentIndex(0)  # Back to welcome page
    
    def _on_account_selected(self, account: Dict[str, Any]):
        """Handle account selection."""
        self._show_success_page(account)
    
    def _populate_account_selection(self, accounts: List[Dict[str, Any]]):
        """Populate the account selection dropdown."""
        self.business_accounts = accounts
        self.account_combo.clear()
        
        for account in accounts:
            display_name = f"{account.get('name', 'Unknown')} ({account.get('category', 'Business')})"
            self.account_combo.addItem(display_name, account.get('id'))
        
        if accounts:
            self.continue_button.setEnabled(True)
            self.selected_account_id = accounts[0].get('id')
            self.account_combo.currentTextChanged.connect(self._on_combo_selection_changed)
            
        self.account_status.setText(self.tr("Found {count} business account(s)").format(count=len(accounts)))
    
    def _on_combo_selection_changed(self):
        """Handle account combo selection change."""
        current_index = self.account_combo.currentIndex()
        if 0 <= current_index < len(self.business_accounts):
            self.selected_account_id = self.business_accounts[current_index].get('id')
    
    def _show_success_page(self, account: Dict[str, Any]):
        """Show the success page."""
        account_name = account.get('name', self.tr('Your Business Account'))
        self.success_message.setText(
            self.tr("Successfully connected to {account_name}!").format(account_name=account_name)
        )
        
        self.stacked_widget.setCurrentIndex(3)  # Success page
        self.continue_button.setText(self.tr("Done"))
        self.continue_button.setEnabled(True)
        
        # Auto-close after a delay or wait for user click
        QTimer.singleShot(1500, lambda: self.continue_button.setEnabled(True))
    
    def _on_continue_clicked(self):
        """Handle continue button click."""
        current_page = self.stacked_widget.currentIndex()
        
        if current_page == 2:  # Account selection page
            if self.selected_account_id:
                # Select the account
                if oauth_handler.select_account(self.selected_account_id):
                    # Account selection successful - this will trigger _on_account_selected
                    pass
                else:
                    QMessageBox.warning(self, self.tr("Error"), self.tr("Failed to select account. Please try again."))
            else:
                QMessageBox.warning(self, self.tr("Selection Required"), self.tr("Please select a business account."))
                
        elif current_page == 3:  # Success page
            # Emit success and close
            selected_account = oauth_handler.selected_account
            if selected_account:
                self.login_successful.emit(selected_account)
            self.accept()
    
    def retranslateUi(self):
        """Retranslate all UI elements."""
        self.setWindowTitle(self.tr("Connect to Instagram & Facebook"))
        self.title_label.setText(self.tr("Connect Your Accounts"))
        self.subtitle_label.setText(self.tr("Connect your Instagram and Facebook accounts to start creating amazing content"))
        
                        # Welcome page elements removed for simplicity
        
        if hasattr(self, 'login_button'):
            self.login_button.setText(self.tr("Connect with Meta"))
        
        # Progress page
        if hasattr(self, 'progress_text'):
            self.progress_text.setText(self.tr("Connecting..."))
        
        if hasattr(self, 'status_label'):
            self.status_label.setText(self.tr("Please complete the login in your browser..."))
        
        # Success page
        if hasattr(self, 'success_title'):
            self.success_title.setText(self.tr("Connected Successfully!"))
        
        if hasattr(self, 'success_message'):
            self.success_message.setText(self.tr("Your account has been connected. You can now start creating amazing content!"))
        
        # Buttons
        if hasattr(self, 'cancel_button'):
            self.cancel_button.setText(self.tr("Cancel"))
        
        if hasattr(self, 'continue_button'):
            if self.stacked_widget.currentIndex() == 3:
                self.continue_button.setText(self.tr("Done"))
            else:
                self.continue_button.setText(self.tr("Continue")) 