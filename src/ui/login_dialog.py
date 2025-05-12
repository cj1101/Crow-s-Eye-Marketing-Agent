"""
Login dialog for Meta API authentication.
"""
import os
import logging
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QMessageBox, QFrame, QStackedWidget, QTextEdit,
    QLineEdit, QFormLayout, QGroupBox, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont

from ..handlers.auth_handler import auth_handler
from ..utils.api_key_manager import key_manager

logger = logging.getLogger(__name__)

class LoginDialog(QDialog):
    """Dialog for Meta API authentication."""
    
    login_successful = Signal(dict)
    
    def __init__(self, parent=None):
        """Initialize the login dialog."""
        super().__init__(parent)
        self.setWindowTitle("Meta API Login")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.business_accounts = []
        self.selected_account_id = None
        
        # Init UI
        self._setup_ui()
        
        # Check if API keys are set
        self._check_api_keys()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Meta API Authentication")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Stacked widget for different states
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # Create pages
        self._create_api_key_page()
        self._create_business_account_page()
        self._create_instructions_page()
        
        # Start with API key page
        self.stacked_widget.setCurrentIndex(0)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self._on_back_clicked)
        self.back_button.setEnabled(False)
        button_layout.addWidget(self.back_button)
        
        button_layout.addStretch()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.reject)
        button_layout.addWidget(self.close_button)
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self._on_next_clicked)
        button_layout.addWidget(self.next_button)
        
        layout.addLayout(button_layout)
    
    def _create_api_key_page(self):
        """Create the API key input page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Information text
        info_label = QLabel(
            "To use this application with Meta API, you need to set up your credentials. "
            "You can either enter them here or set environment variables."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Create a form layout for the inputs
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(10)
        
        # App ID input
        self.app_id_input = QLineEdit()
        self.app_id_input.setPlaceholderText("Enter your Meta App ID")
        form_layout.addRow("App ID:", self.app_id_input)
        
        # App Secret input
        self.app_secret_input = QLineEdit()
        self.app_secret_input.setPlaceholderText("Enter your Meta App Secret")
        self.app_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("App Secret:", self.app_secret_input)
        
        # Access Token input
        self.access_token_input = QLineEdit()
        self.access_token_input.setPlaceholderText("Enter your Meta Access Token")
        form_layout.addRow("Access Token:", self.access_token_input)
        
        # Add the form to the layout
        layout.addLayout(form_layout)
        
        # Validation or error message
        self.api_key_status = QLabel("")
        self.api_key_status.setStyleSheet("color: red;")
        self.api_key_status.setWordWrap(True)
        layout.addWidget(self.api_key_status)
        
        # Button to view instructions
        instructions_button = QPushButton("How to get API keys")
        instructions_button.clicked.connect(self._on_instructions_clicked)
        layout.addWidget(instructions_button)
        
        layout.addStretch()
        
        # Add the page to the stacked widget
        self.stacked_widget.addWidget(page)
    
    def _create_business_account_page(self):
        """Create the business account selection page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Information text
        info_label = QLabel(
            "Select the business account you want to use with this application. "
            "Only business pages are shown, personal accounts are filtered out."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Business account combo box
        self.account_combo = QComboBox()
        self.account_combo.setMinimumHeight(30)
        layout.addWidget(self.account_combo)
        
        # Status message
        self.account_status = QLabel("")
        self.account_status.setStyleSheet("color: #444;")
        self.account_status.setWordWrap(True)
        layout.addWidget(self.account_status)
        
        # Refresh button
        refresh_button = QPushButton("Refresh Account List")
        refresh_button.clicked.connect(self._load_business_accounts)
        layout.addWidget(refresh_button)
        
        layout.addStretch()
        
        # Add the page to the stacked widget
        self.stacked_widget.addWidget(page)
    
    def _create_instructions_page(self):
        """Create the instructions page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Title
        title_label = QLabel("How to Get Meta API Keys")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Instructions text
        instructions_text = QTextEdit()
        instructions_text.setReadOnly(True)
        instructions_text.setText(key_manager.get_instructions())
        layout.addWidget(instructions_text)
        
        # Add the page to the stacked widget
        self.stacked_widget.addWidget(page)
    
    def _check_api_keys(self):
        """Check if API keys are set in environment variables."""
        has_keys = key_manager.has_required_env_variables()
        
        if has_keys:
            # Pre-fill the inputs with values from environment variables
            creds = key_manager.get_api_credentials_from_env()
            self.app_id_input.setText(creds.get('app_id', ''))
            self.app_secret_input.setText(creds.get('app_secret', ''))
            self.access_token_input.setText(creds.get('access_token', ''))
            
            # Update status
            self.api_key_status.setText("API keys found in environment variables")
            self.api_key_status.setStyleSheet("color: green;")
        else:
            self.api_key_status.setText("No API keys found. Please enter your credentials or set environment variables.")
            self.api_key_status.setStyleSheet("color: #666;")
    
    def _load_business_accounts(self):
        """Load and display business accounts."""
        self.account_status.setText("Loading business accounts...")
        self.account_status.setStyleSheet("color: #444;")
        
        # Clear existing accounts
        self.account_combo.clear()
        
        # Get business accounts
        accounts = auth_handler.get_business_accounts()
        
        if not accounts:
            self.account_status.setText("No business accounts found or error fetching accounts.")
            self.account_status.setStyleSheet("color: red;")
            return
        
        # Store and populate combo box
        self.business_accounts = accounts
        
        for account in accounts:
            account_name = account.get('name', 'Unknown')
            account_category = account.get('category', '')
            display_text = f"{account_name} ({account_category})"
            
            self.account_combo.addItem(display_text, account.get('id'))
        
        self.account_status.setText(f"Found {len(accounts)} business account(s)")
        self.account_status.setStyleSheet("color: green;")
        
        if accounts:
            # Enable the next button
            self.next_button.setEnabled(True)
            # Select the first account
            self.selected_account_id = accounts[0].get('id')
            self.account_combo.currentIndexChanged.connect(self._on_account_selected)
    
    def _on_account_selected(self, index):
        """Handle account selection."""
        if index >= 0 and index < len(self.business_accounts):
            self.selected_account_id = self.business_accounts[index].get('id')
    
    def _on_back_clicked(self):
        """Handle back button click."""
        current_index = self.stacked_widget.currentIndex()
        
        if current_index > 0:
            self.stacked_widget.setCurrentIndex(current_index - 1)
            
            # Update button states
            self.next_button.setEnabled(True)
            if self.stacked_widget.currentIndex() == 0:
                self.back_button.setEnabled(False)
    
    def _on_next_clicked(self):
        """Handle next button click."""
        current_index = self.stacked_widget.currentIndex()
        
        if current_index == 0:  # API key page
            # Set environment variables
            app_id = self.app_id_input.text().strip()
            app_secret = self.app_secret_input.text().strip()
            access_token = self.access_token_input.text().strip()
            
            if not (app_id and app_secret and access_token):
                self.api_key_status.setText("Please enter all required credentials.")
                self.api_key_status.setStyleSheet("color: red;")
                return
            
            # Set as environment variables
            key_manager.set_api_key_to_env(key_manager.ENV_VAR_APP_ID, app_id)
            key_manager.set_api_key_to_env(key_manager.ENV_VAR_APP_SECRET, app_secret)
            key_manager.set_api_key_to_env(key_manager.ENV_VAR_ACCESS_TOKEN, access_token)
            
            # Update credentials from environment variables
            key_manager.update_credentials_from_env()
            
            # Move to business account page
            self.stacked_widget.setCurrentIndex(1)
            self.back_button.setEnabled(True)
            
            # Load business accounts
            self._load_business_accounts()
            
        elif current_index == 1:  # Business account page
            if not self.selected_account_id:
                self.account_status.setText("Please select a business account.")
                self.account_status.setStyleSheet("color: red;")
                return
            
            # Select the business account
            success = auth_handler.select_business_account(self.selected_account_id)
            
            if success:
                account = auth_handler.get_selected_account()
                self.login_successful.emit(account)
                self.accept()
            else:
                self.account_status.setText("Error selecting business account. Please try again.")
                self.account_status.setStyleSheet("color: red;")
        
        elif current_index == 2:  # Instructions page
            self.stacked_widget.setCurrentIndex(0)
            self.back_button.setEnabled(False)
    
    def _on_instructions_clicked(self):
        """Show instructions page."""
        self.stacked_widget.setCurrentIndex(2)
        self.back_button.setEnabled(True)
        self.next_button.setText("Back to Login") 