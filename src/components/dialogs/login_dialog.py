"""
Login dialog for Meta API authentication.
"""
import os
import logging
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QMessageBox, QFrame, QStackedWidget, QTextEdit,
    QLineEdit, QFormLayout, QGroupBox, QRadioButton, QButtonGroup,
    QWidget
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import QApplication

from ...features.authentication.auth_handler import auth_handler
from ...utils.api_key_manager import key_manager
from ..base_dialog import BaseDialog

logger = logging.getLogger(__name__)

class LoginDialog(BaseDialog):
    """Dialog for Meta API authentication."""
    
    login_successful = Signal(dict)
    
    def __init__(self, parent=None):
        """Initialize the login dialog."""
        super().__init__(parent)
        self.setWindowTitle(self.tr("Meta API Login"))
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.business_accounts = []
        self.selected_account_id = None
        
        # Initialize UI elements that we'll need to access in retranslateUi
        self.title_label = QLabel(self.tr("Meta API Authentication"), self)
        self.stacked_widget = QStackedWidget(self)
        self.back_button = QPushButton(self.tr("Back"), self)
        self.next_button = QPushButton(self.tr("Next"), self)
        self.close_button = QPushButton(self.tr("Close"), self)
        self.api_key_info_label = QLabel("", self)
        self.api_key_app_id_label = QLabel("", self)
        self.app_id_input = QLineEdit(self)
        self.api_key_app_secret_label = QLabel("", self)
        self.app_secret_input = QLineEdit(self)
        self.api_key_access_token_label = QLabel("", self)
        self.access_token_input = QLineEdit(self)
        self.api_key_status = QLabel("", self)
        self.instructions_button = QPushButton("", self)
        self.biz_account_info_label = QLabel("", self)
        self.account_combo = QComboBox(self)
        self.account_status = QLabel("", self)
        self.refresh_accounts_button = QPushButton("", self)
        self.instructions_title_label = QLabel("", self)
        self.instructions_text = QTextEdit(self)

        self._setup_ui()
        self.retranslateUi()
        
        # Check for application translator and current language
        app = QApplication.instance()
        if app:
            # Get the current language from application property
            current_language = app.property("current_language")
            if current_language:
                self.logger.info(f"Dialog created with current language: {current_language}")
            
        self._check_api_keys() # Sets initial status messages
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.title_label)
        
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        self._create_api_key_page()
        self._create_business_account_page()
        self._create_instructions_page()
        
        self.stacked_widget.setCurrentIndex(0)
        
        button_layout = QHBoxLayout()
        
        self.back_button.clicked.connect(self._on_back_clicked)
        self.back_button.setEnabled(False)
        button_layout.addWidget(self.back_button)
        
        button_layout.addStretch()
        
        self.close_button.clicked.connect(self.reject)
        button_layout.addWidget(self.close_button)
        
        self.next_button.clicked.connect(self._on_next_clicked)
        button_layout.addWidget(self.next_button)
        
        layout.addLayout(button_layout)
    
    def _create_api_key_page(self):
        """Create the API key input page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        self.api_key_info_label.setWordWrap(True)
        layout.addWidget(self.api_key_info_label)
        
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(10)
        
        form_layout.addRow(self.api_key_app_id_label, self.app_id_input)
        
        self.app_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow(self.api_key_app_secret_label, self.app_secret_input)
        
        form_layout.addRow(self.api_key_access_token_label, self.access_token_input)
        
        layout.addLayout(form_layout)
        
        self.api_key_status.setStyleSheet("color: red;") # Default, can be overridden
        self.api_key_status.setWordWrap(True)
        layout.addWidget(self.api_key_status)
        
        self.instructions_button.clicked.connect(self._on_instructions_clicked)
        layout.addWidget(self.instructions_button)
        
        layout.addStretch()
        self.stacked_widget.addWidget(page)
    
    def _create_business_account_page(self):
        """Create the business account selection page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        self.biz_account_info_label.setWordWrap(True)
        layout.addWidget(self.biz_account_info_label)
        
        self.account_combo.setMinimumHeight(30)
        layout.addWidget(self.account_combo)
        
        self.account_status.setStyleSheet("color: #444;") # Default
        self.account_status.setWordWrap(True)
        layout.addWidget(self.account_status)
        
        self.refresh_accounts_button.clicked.connect(self._load_business_accounts)
        layout.addWidget(self.refresh_accounts_button)
        
        layout.addStretch()
        self.stacked_widget.addWidget(page)
    
    def _create_instructions_page(self):
        """Create the instructions page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        self.instructions_title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.instructions_title_label)
        
        self.instructions_text.setReadOnly(True)
        layout.addWidget(self.instructions_text)
        
        self.stacked_widget.addWidget(page)
    
    def _check_api_keys(self):
        """Check if API keys are set in environment variables."""
        has_keys = key_manager.has_required_env_variables()
        
        if has_keys:
            creds = key_manager.get_api_credentials_from_env()
            self.app_id_input.setText(creds.get('app_id', ''))
            self.app_secret_input.setText(creds.get('app_secret', ''))
            self.access_token_input.setText(creds.get('access_token', ''))
            self.api_key_status.setText(self.tr("API keys found in environment variables")) # Use tr
            self.api_key_status.setStyleSheet("color: green;")
        else:
            self.api_key_status.setText(self.tr("No API keys found. Please enter your credentials or set environment variables.")) # Use tr
            self.api_key_status.setStyleSheet("color: #666;")
    
    def _load_business_accounts(self):
        """Load and display business accounts."""
        self.account_status.setText(self.tr("Loading business accounts...")) # Use tr
        self.account_status.setStyleSheet("color: #444;")
        
        self.account_combo.clear()
        accounts = auth_handler.get_business_accounts()
        
        if not accounts:
            self.account_status.setText(self.tr("No business accounts found or error fetching accounts.")) # Use tr
            self.account_status.setStyleSheet("color: red;")
            return
        
        self.business_accounts = accounts
        for account in accounts:
            account_name = account.get('name', self.tr('Unknown')) # Use tr
            account_category = account.get('category', '')
            display_text = f"{account_name} ({account_category})"
            self.account_combo.addItem(display_text, account.get('id'))
        
        self.account_status.setText(self.tr("Found {count} business account(s)").format(count=len(accounts))) # Use tr
        self.account_status.setStyleSheet("color: green;")
        
        if accounts:
            self.next_button.setEnabled(True)
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
            app_id = self.app_id_input.text().strip()
            app_secret = self.app_secret_input.text().strip()
            access_token = self.access_token_input.text().strip()
            
            if not (app_id and app_secret and access_token):
                self.api_key_status.setText(self.tr("Please enter all required credentials.")) # Use tr
                self.api_key_status.setStyleSheet("color: red;")
                return
            
            key_manager.set_api_key_to_env(key_manager.ENV_VAR_APP_ID, app_id)
            key_manager.set_api_key_to_env(key_manager.ENV_VAR_APP_SECRET, app_secret)
            key_manager.set_api_key_to_env(key_manager.ENV_VAR_ACCESS_TOKEN, access_token)
            key_manager.update_credentials_from_env()
            
            self.stacked_widget.setCurrentIndex(1)
            self.back_button.setEnabled(True)
            self._load_business_accounts()
            
        elif current_index == 1:  # Business account page
            if not self.selected_account_id:
                self.account_status.setText(self.tr("Please select a business account.")) # Use tr
                self.account_status.setStyleSheet("color: red;")
                return
            
            success = auth_handler.select_business_account(self.selected_account_id)
            if success:
                account = auth_handler.get_selected_account()
                self.login_successful.emit(account)
                self.accept()
            else:
                self.account_status.setText(self.tr("Error selecting business account. Please try again.")) # Use tr
                self.account_status.setStyleSheet("color: red;")
        
        elif current_index == 2:  # Instructions page
            self.stacked_widget.setCurrentIndex(0)
            self.back_button.setEnabled(False)
        self.retranslateUi() # Ensure button text is updated
    
    def _on_instructions_clicked(self):
        """Show instructions page."""
        self.stacked_widget.setCurrentIndex(2)
        self.back_button.setEnabled(True)

    def retranslateUi(self):
        """Retranslate all UI elements in LoginDialog."""
        self.title_label.setText(self.tr("Meta API Authentication"))

        # API Key Page
        self.api_key_info_label.setText(self.tr(
            "Please enter your Meta API credentials. These are required to interact with Instagram and Facebook APIs. "
            "You can usually find these in your Meta Developer Portal."
        ))
        self.api_key_app_id_label.setText(self.tr("App ID:"))
        self.app_id_input.setPlaceholderText(self.tr("Enter your Meta App ID"))
        self.api_key_app_secret_label.setText(self.tr("App Secret:"))
        self.app_secret_input.setPlaceholderText(self.tr("Enter your Meta App Secret"))
        self.api_key_access_token_label.setText(self.tr("Access Token:"))
        self.access_token_input.setPlaceholderText(self.tr("Enter your Meta Access Token"))
        self.instructions_button.setText(self.tr("How to get API keys"))
        # Refresh status messages that might have been set before first translation
        self._check_api_keys() 

        # Business Account Page
        self.biz_account_info_label.setText(self.tr(
            "Select the Business Account and associated Instagram/Facebook page you want to use."
        ))
        self.refresh_accounts_button.setText(self.tr("Refresh Account List"))
        # Refresh account list and its status messages
        current_account_text_before_reload = self.account_combo.currentText() # if any items exist
        self._load_business_accounts() # This will re-populate combo with tr() and set status
        # Try to restore selection if possible based on text (imperfect)
        if current_account_text_before_reload:
            for i in range(self.account_combo.count()):
                if self.account_combo.itemText(i) == current_account_text_before_reload:
                    self.account_combo.setCurrentIndex(i)
                    break

        # Instructions Page
        self.instructions_title_label.setText(self.tr("How to Get Meta API Keys"))
        if hasattr(key_manager, 'get_instructions'): # Check if method exists
            instructions_content = key_manager.get_instructions()
            # If get_instructions returns a single string, it's fine.
            # If it can return a translatable string or key, that logic would go here.
            # For now, assuming it's a pre-formatted, non-translatable help text.
            self.instructions_text.setText(instructions_content)
        else:
            self.instructions_text.setText(self.tr("Instructions on obtaining API keys are not available in this version."))

        # Buttons
        self.back_button.setText(self.tr("Back"))
        self.close_button.setText(self.tr("Close"))
        self.next_button.setText(self.tr("Next"))
        
        # Update window title for current page of stacked widget if necessary (e.g. Instructions)
        current_idx = self.stacked_widget.currentIndex()
        if current_idx == 2: # Assuming 2 is the instructions page
             # Could add a specific title for this page to self.title_label if desired
             pass

        # Retranslate status messages
        if hasattr(self, 'api_key_status'):
            self.api_key_status.setText(self.tr(self.api_key_status.text()))
        if hasattr(self, 'account_status'):
            self.account_status.setText(self.tr(self.account_status.text()))
        
        # Retranslate page titles
        if hasattr(self, 'api_key_page') and self.api_key_page:
            self.api_key_page.setTitle(self.tr("API Key Input"))
        if hasattr(self, 'business_account_page') and self.business_account_page:
            self.business_account_page.setTitle(self.tr("Business Account Selection"))
        if hasattr(self, 'instructions_page') and self.instructions_page:
            self.instructions_page.setTitle(self.tr("Instructions")) 