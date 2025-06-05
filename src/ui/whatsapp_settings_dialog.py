"""
WhatsApp Settings Dialog for configuring WhatsApp Business API and Virtual Assistant.
"""
import os
import json
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QTextEdit, QPushButton, QLabel, QGroupBox,
                               QCheckBox, QSpinBox, QComboBox, QTabWidget, QWidget,
                               QMessageBox, QScrollArea, QFrame)
from PySide6.QtCore import Qt, Signal, QThread, pyqtSignal
from PySide6.QtGui import QFont, QPixmap, QIcon

from ..api.whatsapp.whatsapp_api_handler import WhatsAppAPIHandler
from ..api.whatsapp.whatsapp_virtual_assistant import WhatsAppVirtualAssistant
from ..api.whatsapp.whatsapp_webhook_handler import WhatsAppWebhookHandler

class ConnectionTestThread(QThread):
    """Thread for testing WhatsApp API connection."""
    result_ready = pyqtSignal(bool, str)
    
    def __init__(self, api_handler):
        super().__init__()
        self.api_handler = api_handler
    
    def run(self):
        try:
            success, message = self.api_handler.test_connection()
            self.result_ready.emit(success, message)
        except Exception as e:
            self.result_ready.emit(False, f"Connection test failed: {str(e)}")

class WhatsAppSettingsDialog(QDialog):
    """Dialog for configuring WhatsApp Business API settings."""
    
    settings_saved = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WhatsApp Virtual Help Desk - Settings")
        self.setModal(True)
        self.resize(800, 700)
        
        # Initialize handlers
        self.api_handler = WhatsAppAPIHandler()
        self.virtual_assistant = WhatsAppVirtualAssistant(self.api_handler)
        self.webhook_handler = WhatsAppWebhookHandler(self.api_handler, self.virtual_assistant)
        
        # Connection test thread
        self.test_thread = None
        
        self.setup_ui()
        self.load_settings()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # API Configuration tab
        self.setup_api_tab()
        
        # Virtual Assistant tab
        self.setup_assistant_tab()
        
        # Webhook Configuration tab
        self.setup_webhook_tab()
        
        # Test & Status tab
        self.setup_test_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
        button_layout.addWidget(self.test_connection_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def setup_api_tab(self):
        """Setup API configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Header
        header = QLabel("WhatsApp Business API Configuration")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Description
        desc = QLabel("Configure your WhatsApp Business API credentials to enable virtual help desk functionality.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 20px;")
        layout.addWidget(desc)
        
        # Credentials form
        credentials_group = QGroupBox("API Credentials")
        credentials_layout = QFormLayout(credentials_group)
        
        self.access_token_edit = QLineEdit()
        self.access_token_edit.setEchoMode(QLineEdit.Password)
        self.access_token_edit.setPlaceholderText("Your WhatsApp Business API access token...")
        credentials_layout.addRow("Access Token:", self.access_token_edit)
        
        self.phone_number_id_edit = QLineEdit()
        self.phone_number_id_edit.setPlaceholderText("Your WhatsApp Business phone number ID...")
        credentials_layout.addRow("Phone Number ID:", self.phone_number_id_edit)
        
        self.verify_token_edit = QLineEdit()
        self.verify_token_edit.setPlaceholderText("Webhook verification token...")
        credentials_layout.addRow("Verify Token:", self.verify_token_edit)
        
        layout.addWidget(credentials_group)
        
        # API Settings
        settings_group = QGroupBox("API Settings")
        settings_layout = QFormLayout(settings_group)
        
        self.api_version_combo = QComboBox()
        self.api_version_combo.addItems(["v18.0", "v17.0", "v16.0"])
        settings_layout.addRow("API Version:", self.api_version_combo)
        
        layout.addWidget(settings_group)
        
        # Instructions
        instructions_group = QGroupBox("Setup Instructions")
        instructions_layout = QVBoxLayout(instructions_group)
        
        instructions_text = """
1. Create a Meta Developer Account and Business App
2. Add WhatsApp Business to your app
3. Get your Access Token from the app dashboard
4. Copy your Phone Number ID from WhatsApp Business settings
5. Set up a webhook endpoint (see Webhook tab)
6. Test the connection using the "Test Connection" button

For detailed setup instructions, visit:
https://developers.facebook.com/docs/whatsapp/cloud-api/get-started
        """
        
        instructions_label = QLabel(instructions_text.strip())
        instructions_label.setWordWrap(True)
        instructions_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 15px;
                color: #495057;
            }
        """)
        instructions_layout.addWidget(instructions_label)
        
        layout.addWidget(instructions_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "API Configuration")
    
    def setup_assistant_tab(self):
        """Setup virtual assistant configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Header
        header = QLabel("Virtual Assistant Configuration")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Scroll area for form
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Business Information
        business_group = QGroupBox("Business Information")
        business_layout = QFormLayout(business_group)
        
        self.business_name_edit = QLineEdit()
        self.business_name_edit.setPlaceholderText("Your business name...")
        business_layout.addRow("Business Name:", self.business_name_edit)
        
        self.business_industry_edit = QLineEdit()
        self.business_industry_edit.setPlaceholderText("Your industry...")
        business_layout.addRow("Industry:", self.business_industry_edit)
        
        self.business_description_edit = QTextEdit()
        self.business_description_edit.setMaximumHeight(80)
        self.business_description_edit.setPlaceholderText("Brief description of your business...")
        business_layout.addRow("Description:", self.business_description_edit)
        
        scroll_layout.addWidget(business_group)
        
        # Contact Information
        contact_group = QGroupBox("Contact Information")
        contact_layout = QFormLayout(contact_group)
        
        self.contact_email_edit = QLineEdit()
        self.contact_email_edit.setPlaceholderText("support@yourcompany.com")
        contact_layout.addRow("Support Email:", self.contact_email_edit)
        
        self.contact_phone_edit = QLineEdit()
        self.contact_phone_edit.setPlaceholderText("+1-555-0123")
        contact_layout.addRow("Phone Number:", self.contact_phone_edit)
        
        self.website_edit = QLineEdit()
        self.website_edit.setPlaceholderText("https://yourcompany.com")
        contact_layout.addRow("Website:", self.website_edit)
        
        self.business_hours_edit = QLineEdit()
        self.business_hours_edit.setPlaceholderText("Monday-Friday 9AM-6PM EST")
        contact_layout.addRow("Business Hours:", self.business_hours_edit)
        
        scroll_layout.addWidget(contact_group)
        
        # Assistant Settings
        assistant_group = QGroupBox("Assistant Personality & Behavior")
        assistant_layout = QFormLayout(assistant_group)
        
        self.assistant_name_edit = QLineEdit()
        self.assistant_name_edit.setPlaceholderText("Assistant Name (e.g., 'Alex' or 'Support Bot')")
        assistant_layout.addRow("Assistant Name:", self.assistant_name_edit)
        
        self.personality_edit = QTextEdit()
        self.personality_edit.setMaximumHeight(100)
        self.personality_edit.setPlaceholderText("Describe the assistant's personality (friendly, professional, helpful, etc.)")
        assistant_layout.addRow("Personality:", self.personality_edit)
        
        self.max_response_length_spin = QSpinBox()
        self.max_response_length_spin.setRange(100, 1000)
        self.max_response_length_spin.setValue(300)
        assistant_layout.addRow("Max Response Length:", self.max_response_length_spin)
        
        scroll_layout.addWidget(assistant_group)
        
        # Services offered
        services_group = QGroupBox("Services & Capabilities")
        services_layout = QVBoxLayout(services_group)
        
        services_label = QLabel("List your main services (one per line):")
        services_layout.addWidget(services_label)
        
        self.services_edit = QTextEdit()
        self.services_edit.setMaximumHeight(120)
        self.services_edit.setPlaceholderText("Social Media Management\nContent Creation\nDigital Marketing\n...")
        services_layout.addWidget(self.services_edit)
        
        scroll_layout.addWidget(services_group)
        
        # AI Instructions
        instructions_group = QGroupBox("AI Instructions")
        instructions_layout = QVBoxLayout(instructions_group)
        
        instructions_label = QLabel("Custom instructions for the AI assistant:")
        instructions_layout.addWidget(instructions_label)
        
        self.ai_instructions_edit = QTextEdit()
        self.ai_instructions_edit.setMaximumHeight(150)
        self.ai_instructions_edit.setPlaceholderText(
            "You are a professional customer service assistant. Be helpful, friendly, and always try to solve customer issues. "
            "If you cannot help with something, offer to connect them with a human agent."
        )
        instructions_layout.addWidget(self.ai_instructions_edit)
        
        scroll_layout.addWidget(instructions_group)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, "Virtual Assistant")
    
    def setup_webhook_tab(self):
        """Setup webhook configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Header
        header = QLabel("Webhook Configuration")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Webhook settings
        webhook_group = QGroupBox("Webhook Settings")
        webhook_layout = QFormLayout(webhook_group)
        
        self.webhook_port_spin = QSpinBox()
        self.webhook_port_spin.setRange(1000, 65535)
        self.webhook_port_spin.setValue(5000)
        webhook_layout.addRow("Webhook Port:", self.webhook_port_spin)
        
        self.webhook_host_edit = QLineEdit()
        self.webhook_host_edit.setText("0.0.0.0")
        webhook_layout.addRow("Webhook Host:", self.webhook_host_edit)
        
        self.auto_start_webhook_check = QCheckBox("Auto-start webhook server")
        self.auto_start_webhook_check.setChecked(True)
        webhook_layout.addRow("", self.auto_start_webhook_check)
        
        layout.addWidget(webhook_group)
        
        # Server controls
        controls_group = QGroupBox("Server Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        self.start_webhook_btn = QPushButton("Start Webhook Server")
        self.start_webhook_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        self.stop_webhook_btn = QPushButton("Stop Webhook Server")
        self.stop_webhook_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.stop_webhook_btn.setEnabled(False)
        
        self.webhook_status_label = QLabel("Status: Stopped")
        self.webhook_status_label.setStyleSheet("font-weight: bold; color: #dc3545;")
        
        controls_layout.addWidget(self.start_webhook_btn)
        controls_layout.addWidget(self.stop_webhook_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.webhook_status_label)
        
        layout.addWidget(controls_group)
        
        # Instructions
        instructions_group = QGroupBox("Setup Instructions")
        instructions_layout = QVBoxLayout(instructions_group)
        
        instructions_text = """
Webhook Configuration Steps:

1. Start the webhook server using the controls above
2. If running locally, use a tool like ngrok to create a public URL:
   - Install ngrok: https://ngrok.com/
   - Run: ngrok http 5000
   - Copy the HTTPS URL (e.g., https://abc123.ngrok.io)

3. In your Meta App dashboard:
   - Go to WhatsApp > Configuration
   - Set Webhook URL to: [your-ngrok-url]/webhook
   - Set Verify Token to match the one in API Configuration
   - Subscribe to 'messages' webhook event

4. Test the webhook by sending a message to your WhatsApp Business number

For production deployment, use a proper web server with SSL certificate.
        """
        
        instructions_label = QLabel(instructions_text.strip())
        instructions_label.setWordWrap(True)
        instructions_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 15px;
                color: #495057;
            }
        """)
        instructions_layout.addWidget(instructions_label)
        
        layout.addWidget(instructions_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Webhook Setup")
    
    def setup_test_tab(self):
        """Setup test and status tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Header
        header = QLabel("Test & Status")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Connection status
        status_group = QGroupBox("Connection Status")
        status_layout = QVBoxLayout(status_group)
        
        self.connection_status_label = QLabel("Not tested")
        self.connection_status_label.setStyleSheet("font-size: 14px; padding: 10px;")
        status_layout.addWidget(self.connection_status_label)
        
        layout.addWidget(status_group)
        
        # Test message
        test_group = QGroupBox("Send Test Message")
        test_layout = QFormLayout(test_group)
        
        self.test_phone_edit = QLineEdit()
        self.test_phone_edit.setPlaceholderText("Phone number (e.g., 1234567890)")
        test_layout.addRow("Phone Number:", self.test_phone_edit)
        
        self.test_message_edit = QTextEdit()
        self.test_message_edit.setMaximumHeight(80)
        self.test_message_edit.setPlaceholderText("Test message to send...")
        test_layout.addRow("Message:", self.test_message_edit)
        
        test_button_layout = QHBoxLayout()
        self.send_test_btn = QPushButton("Send Test Message")
        self.send_test_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        test_button_layout.addWidget(self.send_test_btn)
        test_button_layout.addStretch()
        
        test_layout.addRow("", test_button_layout)
        
        layout.addWidget(test_group)
        
        # Configuration summary
        summary_group = QGroupBox("Configuration Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        self.config_summary_label = QLabel("Load settings to see configuration summary...")
        self.config_summary_label.setWordWrap(True)
        self.config_summary_label.setStyleSheet("background-color: #f8f9fa; padding: 15px; border-radius: 4px;")
        summary_layout.addWidget(self.config_summary_label)
        
        layout.addWidget(summary_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Test & Status")
    
    def setup_connections(self):
        """Setup signal connections."""
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn.clicked.connect(self.reject)
        self.test_connection_btn.clicked.connect(self.test_connection)
        self.send_test_btn.clicked.connect(self.send_test_message)
        self.start_webhook_btn.clicked.connect(self.start_webhook_server)
        self.stop_webhook_btn.clicked.connect(self.stop_webhook_server)
    
    def load_settings(self):
        """Load existing settings."""
        try:
            # Load API credentials
            if hasattr(self.api_handler, 'credentials') and self.api_handler.credentials:
                self.access_token_edit.setText(self.api_handler.credentials.get('access_token', ''))
                self.phone_number_id_edit.setText(self.api_handler.credentials.get('phone_number_id', ''))
                self.verify_token_edit.setText(self.api_handler.credentials.get('verify_token', ''))
            
            # Load business info
            if hasattr(self.virtual_assistant, 'business_info'):
                info = self.virtual_assistant.business_info
                self.business_name_edit.setText(info.get('name', ''))
                self.business_industry_edit.setText(info.get('industry', ''))
                
                contact = info.get('contact', {})
                self.contact_email_edit.setText(contact.get('email', ''))
                self.contact_phone_edit.setText(contact.get('phone', ''))
                self.website_edit.setText(contact.get('website', ''))
                self.business_hours_edit.setText(contact.get('hours', ''))
                
                services = info.get('services', [])
                self.services_edit.setPlainText('\n'.join(services))
            
            # Load assistant config
            if hasattr(self.virtual_assistant, 'assistant_config'):
                config = self.virtual_assistant.assistant_config
                self.assistant_name_edit.setText(config.get('name', ''))
                self.personality_edit.setPlainText(config.get('personality', ''))
                self.max_response_length_spin.setValue(config.get('max_response_length', 300))
            
            self.update_config_summary()
            
        except Exception as e:
            QMessageBox.warning(self, "Loading Error", f"Error loading settings: {str(e)}")
    
    def save_settings(self):
        """Save settings and close dialog."""
        try:
            # Validate required fields
            if not self.access_token_edit.text().strip():
                QMessageBox.warning(self, "Validation Error", "Access Token is required!")
                self.tab_widget.setCurrentIndex(0)
                return
            
            if not self.phone_number_id_edit.text().strip():
                QMessageBox.warning(self, "Validation Error", "Phone Number ID is required!")
                self.tab_widget.setCurrentIndex(0)
                return
            
            # Save API credentials
            credentials = {
                'access_token': self.access_token_edit.text().strip(),
                'phone_number_id': self.phone_number_id_edit.text().strip(),
                'verify_token': self.verify_token_edit.text().strip() or 'default_verify_token'
            }
            
            self.api_handler.save_credentials(credentials)
            
            # Save business info and assistant config
            settings = {
                'business_info': {
                    'name': self.business_name_edit.text().strip(),
                    'industry': self.business_industry_edit.text().strip(),
                    'description': self.business_description_edit.toPlainText().strip(),
                    'services': [s.strip() for s in self.services_edit.toPlainText().split('\n') if s.strip()],
                    'contact': {
                        'email': self.contact_email_edit.text().strip(),
                        'phone': self.contact_phone_edit.text().strip(),
                        'website': self.website_edit.text().strip(),
                        'hours': self.business_hours_edit.text().strip()
                    }
                },
                'assistant_config': {
                    'name': self.assistant_name_edit.text().strip() or 'Assistant',
                    'personality': self.personality_edit.toPlainText().strip(),
                    'max_response_length': self.max_response_length_spin.value(),
                    'ai_instructions': self.ai_instructions_edit.toPlainText().strip()
                },
                'webhook_config': {
                    'port': self.webhook_port_spin.value(),
                    'host': self.webhook_host_edit.text().strip(),
                    'auto_start': self.auto_start_webhook_check.isChecked()
                }
            }
            
            self.settings_saved.emit(settings)
            QMessageBox.information(self, "Success", "WhatsApp settings saved successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error saving settings: {str(e)}")
    
    def test_connection(self):
        """Test WhatsApp API connection."""
        try:
            # Update credentials before testing
            credentials = {
                'access_token': self.access_token_edit.text().strip(),
                'phone_number_id': self.phone_number_id_edit.text().strip(),
                'verify_token': self.verify_token_edit.text().strip() or 'default_verify_token'
            }
            
            if not credentials['access_token'] or not credentials['phone_number_id']:
                QMessageBox.warning(self, "Test Error", "Please enter Access Token and Phone Number ID first!")
                return
            
            self.api_handler.credentials = credentials
            
            # Disable button and show testing
            self.test_connection_btn.setEnabled(False)
            self.test_connection_btn.setText("Testing...")
            self.connection_status_label.setText("Testing connection...")
            self.connection_status_label.setStyleSheet("color: #ffc107; font-size: 14px; padding: 10px;")
            
            # Start test thread
            self.test_thread = ConnectionTestThread(self.api_handler)
            self.test_thread.result_ready.connect(self.handle_test_result)
            self.test_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Test Error", f"Error testing connection: {str(e)}")
            self.test_connection_btn.setEnabled(True)
            self.test_connection_btn.setText("Test Connection")
    
    def handle_test_result(self, success: bool, message: str):
        """Handle connection test result."""
        try:
            self.test_connection_btn.setEnabled(True)
            self.test_connection_btn.setText("Test Connection")
            
            if success:
                self.connection_status_label.setText(f"✅ Connected: {message}")
                self.connection_status_label.setStyleSheet("color: #28a745; font-size: 14px; padding: 10px;")
            else:
                self.connection_status_label.setText(f"❌ Connection Failed: {message}")
                self.connection_status_label.setStyleSheet("color: #dc3545; font-size: 14px; padding: 10px;")
            
            self.update_config_summary()
            
        except Exception as e:
            QMessageBox.critical(self, "Test Error", f"Error handling test result: {str(e)}")
    
    def send_test_message(self):
        """Send a test message."""
        try:
            phone = self.test_phone_edit.text().strip()
            message = self.test_message_edit.toPlainText().strip()
            
            if not phone:
                QMessageBox.warning(self, "Test Error", "Please enter a phone number!")
                return
            
            if not message:
                QMessageBox.warning(self, "Test Error", "Please enter a test message!")
                return
            
            # Update credentials
            credentials = {
                'access_token': self.access_token_edit.text().strip(),
                'phone_number_id': self.phone_number_id_edit.text().strip(),
                'verify_token': self.verify_token_edit.text().strip()
            }
            
            if not credentials['access_token'] or not credentials['phone_number_id']:
                QMessageBox.warning(self, "Test Error", "Please configure API credentials first!")
                return
            
            self.api_handler.credentials = credentials
            
            # Send test message
            success, result = self.api_handler.send_text_message(phone, message)
            
            if success:
                QMessageBox.information(self, "Test Success", f"Test message sent successfully! Message ID: {result}")
            else:
                QMessageBox.critical(self, "Test Failed", f"Failed to send test message: {result}")
                
        except Exception as e:
            QMessageBox.critical(self, "Test Error", f"Error sending test message: {str(e)}")
    
    def start_webhook_server(self):
        """Start the webhook server."""
        try:
            port = self.webhook_port_spin.value()
            host = self.webhook_host_edit.text().strip() or "0.0.0.0"
            
            self.webhook_handler.start_server(host, port)
            
            self.start_webhook_btn.setEnabled(False)
            self.stop_webhook_btn.setEnabled(True)
            self.webhook_status_label.setText(f"Status: Running on {host}:{port}")
            self.webhook_status_label.setStyleSheet("font-weight: bold; color: #28a745;")
            
            QMessageBox.information(self, "Webhook Started", f"Webhook server started on {host}:{port}")
            
        except Exception as e:
            QMessageBox.critical(self, "Webhook Error", f"Error starting webhook server: {str(e)}")
    
    def stop_webhook_server(self):
        """Stop the webhook server."""
        try:
            self.webhook_handler.stop_server()
            
            self.start_webhook_btn.setEnabled(True)
            self.stop_webhook_btn.setEnabled(False)
            self.webhook_status_label.setText("Status: Stopped")
            self.webhook_status_label.setStyleSheet("font-weight: bold; color: #dc3545;")
            
            QMessageBox.information(self, "Webhook Stopped", "Webhook server stopped successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Webhook Error", f"Error stopping webhook server: {str(e)}")
    
    def update_config_summary(self):
        """Update configuration summary."""
        try:
            summary_parts = []
            
            # API status
            if self.api_handler.credentials:
                summary_parts.append("✅ API Credentials: Configured")
            else:
                summary_parts.append("❌ API Credentials: Not configured")
            
            # Business info
            if self.business_name_edit.text().strip():
                summary_parts.append(f"✅ Business: {self.business_name_edit.text().strip()}")
            else:
                summary_parts.append("❌ Business: Not configured")
            
            # Services
            services = [s.strip() for s in self.services_edit.toPlainText().split('\n') if s.strip()]
            if services:
                summary_parts.append(f"✅ Services: {len(services)} configured")
            else:
                summary_parts.append("❌ Services: Not configured")
            
            # Webhook
            if hasattr(self.webhook_handler, 'is_running') and self.webhook_handler.is_running:
                summary_parts.append("✅ Webhook: Running")
            else:
                summary_parts.append("❌ Webhook: Not running")
            
            summary_text = "\n".join(summary_parts)
            self.config_summary_label.setText(summary_text)
            
        except Exception as e:
            self.config_summary_label.setText(f"Error updating summary: {str(e)}")
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if hasattr(self.webhook_handler, 'is_running') and self.webhook_handler.is_running:
            reply = QMessageBox.question(
                self, 
                "Webhook Running", 
                "The webhook server is still running. Stop it before closing?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.stop_webhook_server()
        
        event.accept() 