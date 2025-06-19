"""
Google Services Management Dialog
Handles authentication and connection management for YouTube, Google Photos, and Google My Business.
Allows users to use different Google accounts for each service.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTabWidget, QWidget, QTextEdit, QFrame, QScrollArea, QGroupBox,
    QGridLayout, QMessageBox, QProgressBar, QComboBox
)
from PySide6.QtCore import Qt, Signal, QThread, pyqtSignal
from PySide6.QtGui import QFont, QPalette
import sys
import webbrowser
import threading
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from ..base_dialog import BaseDialog

logger = logging.getLogger(__name__)

# Configuration for API base URL - this should match your backend
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
API_TOKEN = None  # Will be set from the app's current user token

def set_api_token(token: str):
    """Set the API token for authentication."""
    global API_TOKEN
    API_TOKEN = token

def get_api_base_url():
    """Get the API base URL."""
    return API_BASE_URL

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callbacks."""
    
    def do_GET(self):
        """Handle GET requests (OAuth callbacks)."""
        try:
            # Parse the callback URL
            parsed_path = urlparse(self.path)
            params = parse_qs(parsed_path.query)
            
            # Store the callback data in the server
            self.server.callback_data = {
                'code': params.get('code', [''])[0],
                'state': params.get('state', [''])[0],
                'error': params.get('error', [''])[0],
                'error_description': params.get('error_description', [''])[0]
            }
            
            # Send a response to the browser
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html_response = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authorization Complete</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .success { color: green; }
                    .error { color: red; }
                </style>
            </head>
            <body>
            """
            
            if self.server.callback_data['error']:
                html_response += f"""
                <h1 class="error">Authorization Failed</h1>
                <p>Error: {self.server.callback_data['error']}</p>
                <p>{self.server.callback_data['error_description']}</p>
                """
            else:
                html_response += """
                <h1 class="success">Authorization Successful!</h1>
                <p>You can now close this window and return to the application.</p>
                """
            
            html_response += """
            </body>
            </html>
            """
            
            self.wfile.write(html_response.encode())
            
            # Signal that we're done
            self.server.callback_received = True
            
        except Exception as e:
            logger.error(f"Error in OAuth callback handler: {e}")
            self.send_response(500)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress log messages."""
        pass

class OAuthCallbackServer:
    """Local HTTP server to handle OAuth callbacks."""
    
    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.thread = None
        self.callback_data = None
        
    def start(self):
        """Start the callback server."""
        try:
            self.server = HTTPServer(('localhost', self.port), OAuthCallbackHandler)
            self.server.callback_received = False
            self.server.callback_data = None
            
            self.thread = threading.Thread(target=self._run_server, daemon=True)
            self.thread.start()
            
            logger.info(f"OAuth callback server started on http://localhost:{self.port}")
            return True
            
        except OSError as e:
            if "Address already in use" in str(e):
                logger.warning(f"Port {self.port} is already in use, trying alternative approach")
                return False
            else:
                logger.error(f"Failed to start callback server: {e}")
                return False
    
    def _run_server(self):
        """Run the server in a separate thread."""
        try:
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"Error running callback server: {e}")
    
    def wait_for_callback(self, timeout=300):
        """Wait for OAuth callback."""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.server and self.server.callback_received:
                self.callback_data = self.server.callback_data
                return True
            time.sleep(0.5)
        
        return False
    
    def stop(self):
        """Stop the callback server."""
        if self.server:
            self.server.shutdown()
            self.server = None
        
        if self.thread:
            self.thread.join(timeout=1)
            self.thread = None

class GoogleServiceWorker(QThread):
    """Worker thread for Google service operations."""
    finished = Signal(bool, str, dict)  # success, message, data
    
    def __init__(self, operation: str, service_name: str, data: Dict[str, Any] = None):
        super().__init__()
        self.operation = operation
        self.service_name = service_name
        self.data = data or {}
    
    def run(self):
        """Execute the Google service operation."""
        try:
            if self.operation == "setup_auth":
                success, message, response_data = self._setup_auth()
            elif self.operation == "get_auth_url":
                success, message, response_data = self._get_auth_url()
            elif self.operation == "check_status":
                success, message, response_data = self._check_status()
            elif self.operation == "disconnect":
                success, message, response_data = self._disconnect()
            elif self.operation == "handle_callback":
                success, message, response_data = self._handle_callback()
            else:
                success, message, response_data = False, f"Unknown operation: {self.operation}", {}
            
            self.finished.emit(success, message, response_data)
            
        except Exception as e:
            logger.error(f"Error in Google service worker: {e}")
            self.finished.emit(False, f"Operation failed: {str(e)}", {})

    def _get_headers(self):
        """Get headers for API requests."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Add authorization if token is available
        global API_TOKEN
        if API_TOKEN:
            headers['Authorization'] = f'Bearer {API_TOKEN}'
        
        return headers
    
    def _setup_auth(self) -> tuple[bool, str, Dict[str, Any]]:
        """Setup authentication for a Google service."""
        try:
            # Store credentials in environment variables for the session
            client_id = self.data.get('client_id')
            client_secret = self.data.get('client_secret')
            
            if not client_id or not client_secret:
                return False, "Client ID and Client Secret are required", {}
            
            # Set environment variables temporarily for this session
            os.environ[f'GOOGLE_{self.service_name.upper()}_CLIENT_ID'] = client_id
            os.environ[f'GOOGLE_{self.service_name.upper()}_CLIENT_SECRET'] = client_secret
            
            return True, f"Credentials configured for {self.service_name}", {
                "configured": True
            }
        except Exception as e:
            return False, f"Setup failed: {str(e)}", {}
    
    def _get_auth_url(self) -> tuple[bool, str, Dict[str, Any]]:
        """Get authorization URL for a Google service."""
        try:
            # Map service names to API endpoints
            endpoint_map = {
                'google_photos': 'google-photos',
                'youtube': 'youtube',
                'google_business': 'google-business'
            }
            
            endpoint = endpoint_map.get(self.service_name, self.service_name.replace('_', '-'))
            url = f"{API_BASE_URL}/api/v1/{endpoint}/auth/url"
            
            headers = self._get_headers()
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                auth_url = data.get('auth_url', '')
                state = data.get('state', '')
                
                return True, "Authorization URL generated", {
                    "authorization_url": auth_url,
                    "state": state
                }
            else:
                error_msg = response.json().get('detail', 'Failed to get authorization URL')
                return False, f"API Error: {error_msg}", {}
                
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to API server. Make sure the backend is running.", {}
        except requests.exceptions.Timeout:
            return False, "Request timed out. The API server may be overloaded.", {}
        except Exception as e:
            return False, f"Failed to get auth URL: {str(e)}", {}
    
    def _check_status(self) -> tuple[bool, str, Dict[str, Any]]:
        """Check status of a Google service."""
        try:
            # Map service names to API endpoints
            endpoint_map = {
                'google_photos': 'google-photos',
                'youtube': 'youtube', 
                'google_business': 'google-business'
            }
            
            endpoint = endpoint_map.get(self.service_name, self.service_name.replace('_', '-'))
            url = f"{API_BASE_URL}/api/v1/{endpoint}/connection"
            
            headers = self._get_headers()
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                connected = data is not None
                
                return True, f"{self.service_name} status checked", {
                    "authenticated": connected,
                    "connected": connected,
                    "connection_data": data
                }
            elif response.status_code == 404:
                return True, f"{self.service_name} not connected", {
                    "authenticated": False,
                    "connected": False
                }
            else:
                error_msg = response.json().get('detail', 'Status check failed')
                return False, f"API Error: {error_msg}", {}
                
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to API server. Make sure the backend is running.", {}
        except requests.exceptions.Timeout:
            return False, "Request timed out. The API server may be overloaded.", {}
        except Exception as e:
            return False, f"Status check failed: {str(e)}", {}
    
    def _disconnect(self) -> tuple[bool, str, Dict[str, Any]]:
        """Disconnect a Google service."""
        try:
            # Map service names to API endpoints
            endpoint_map = {
                'google_photos': 'google-photos',
                'youtube': 'youtube',
                'google_business': 'google-business'
            }
            
            endpoint = endpoint_map.get(self.service_name, self.service_name.replace('_', '-'))
            url = f"{API_BASE_URL}/api/v1/{endpoint}/connection"
            
            headers = self._get_headers()
            response = requests.delete(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return True, f"{self.service_name} disconnected successfully", {}
            else:
                error_msg = response.json().get('detail', 'Disconnect failed')
                return False, f"API Error: {error_msg}", {}
                
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to API server. Make sure the backend is running.", {}
        except requests.exceptions.Timeout:
            return False, "Request timed out. The API server may be overloaded.", {}
        except Exception as e:
            return False, f"Disconnect failed: {str(e)}", {}

    def _handle_callback(self) -> tuple[bool, str, Dict[str, Any]]:
        """Handle OAuth callback with authorization code."""
        try:
            # Map service names to API endpoints
            endpoint_map = {
                'google_photos': 'google-photos', 
                'youtube': 'youtube',
                'google_business': 'google-business'
            }
            
            endpoint = endpoint_map.get(self.service_name, self.service_name.replace('_', '-'))
            url = f"{API_BASE_URL}/api/v1/{endpoint}/auth/callback"
            
            headers = self._get_headers()
            payload = {
                'code': self.data.get('code'),
                'state': self.data.get('state')
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return True, f"{self.service_name} connected successfully", {
                    "connection_data": data
                }
            else:
                error_msg = response.json().get('detail', 'Authentication failed')
                return False, f"API Error: {error_msg}", {}
            
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to API server. Make sure the backend is running.", {}
        except requests.exceptions.Timeout:
            return False, "Request timed out. The API server may be overloaded.", {}
        except Exception as e:
            return False, f"Authentication failed: {str(e)}", {}

class GoogleServiceWidget(QWidget):
    """Widget for managing a single Google service."""
    
    status_changed = Signal(str, dict)  # service_name, status_data
    
    def __init__(self, service_name: str, service_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.service_name = service_name
        self.service_info = service_info
        self.authenticated = False
        self.connected = False
        self.callback_server = None
        self.auth_state = None
        
        self.init_ui()
        self.check_status()
    
    def init_ui(self):
        """Initialize the UI for this service."""
        layout = QVBoxLayout(self)
        
        # Service header
        header_layout = QHBoxLayout()
        
        title_label = QLabel(self.service_info["name"])
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel("Checking...")
        self.status_label.setStyleSheet("color: orange;")
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Description
        desc_label = QLabel(self.service_info["description"])
        desc_label.setStyleSheet("color: #666;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Credentials section
        creds_group = QGroupBox("OAuth2 Credentials")
        creds_layout = QGridLayout(creds_group)
        
        creds_layout.addWidget(QLabel("Client ID:"), 0, 0)
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("Your Google OAuth2 Client ID")
        creds_layout.addWidget(self.client_id_input, 0, 1)
        
        creds_layout.addWidget(QLabel("Client Secret:"), 1, 0)
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setEchoMode(QLineEdit.Password)
        self.client_secret_input.setPlaceholderText("Your Google OAuth2 Client Secret")
        creds_layout.addWidget(self.client_secret_input, 1, 1)
        
        layout.addWidget(creds_group)
        
        # Actions section
        actions_layout = QHBoxLayout()
        
        self.setup_button = QPushButton("Setup Credentials")
        self.setup_button.clicked.connect(self.setup_credentials)
        actions_layout.addWidget(self.setup_button)
        
        self.auth_button = QPushButton("Authenticate")
        self.auth_button.clicked.connect(self.authenticate)
        self.auth_button.setEnabled(False)
        actions_layout.addWidget(self.auth_button)
        
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect)
        self.disconnect_button.setEnabled(False)
        actions_layout.addWidget(self.disconnect_button)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        # Status display
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
    
    def setup_credentials(self):
        """Setup OAuth2 credentials for this service."""
        client_id = self.client_id_input.text().strip()
        client_secret = self.client_secret_input.text().strip()
        
        if not client_id or not client_secret:
            QMessageBox.warning(self, "Missing Credentials", 
                              "Please enter both Client ID and Client Secret.")
            return
        
        self.status_text.append(f"Setting up credentials for {self.service_info['name']}...")
        
        # Start worker thread
        self.worker = GoogleServiceWorker("setup_auth", self.service_name, {
            "client_id": client_id,
            "client_secret": client_secret
        })
        self.worker.finished.connect(self.on_setup_complete)
        self.worker.start()
    
    def authenticate(self):
        """Start authentication process for this service."""
        self.status_text.append(f"Getting authorization URL for {self.service_info['name']}...")
        
        self.worker = GoogleServiceWorker("get_auth_url", self.service_name)
        self.worker.finished.connect(self.on_auth_url_received)
        self.worker.start()
    
    def disconnect(self):
        """Disconnect this service."""
        reply = QMessageBox.question(
            self, "Confirm Disconnect",
            f"Are you sure you want to disconnect {self.service_info['name']}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.status_text.append(f"Disconnecting {self.service_info['name']}...")
            
            self.worker = GoogleServiceWorker("disconnect", self.service_name)
            self.worker.finished.connect(self.on_disconnect_complete)
            self.worker.start()
    
    def check_status(self):
        """Check the current status of this service."""
        self.worker = GoogleServiceWorker("check_status", self.service_name)
        self.worker.finished.connect(self.on_status_checked)
        self.worker.start()
    
    def on_setup_complete(self, success: bool, message: str, data: Dict[str, Any]):
        """Handle setup completion."""
        if success:
            self.status_text.append(f"✅ {message}")
            self.auth_button.setEnabled(True)
            QMessageBox.information(self, "Setup Complete", 
                                  f"Credentials saved for {self.service_info['name']}. You can now authenticate.")
        else:
            self.status_text.append(f"❌ {message}")
            QMessageBox.critical(self, "Setup Failed", message)
    
    def on_auth_url_received(self, success: bool, message: str, data: Dict[str, Any]):
        """Handle authorization URL reception."""
        if success:
            auth_url = data.get("authorization_url", "")
            state = data.get("state", "")
            self.auth_state = state  # Store state for callback verification
            
            self.status_text.append(f"✅ {message}")
            self.status_text.append("Starting local callback server...")
            
            # Try to start local callback server
            self.callback_server = OAuthCallbackServer(port=8080)
            if self.callback_server.start():
                self.status_text.append("✅ Callback server started on http://localhost:8080")
                self.status_text.append("Opening authorization URL in browser...")
                
                # Open URL in browser
                webbrowser.open(auth_url)
                
                # Start waiting for callback
                self.wait_for_callback()
            else:
                # Fallback to manual URL entry
                self.status_text.append("⚠️ Could not start callback server, using manual flow...")
                webbrowser.open(auth_url)
                self.show_callback_dialog()
        else:
            self.status_text.append(f"❌ {message}")
            QMessageBox.critical(self, "Authentication Failed", message)
            
    def wait_for_callback(self):
        """Wait for OAuth callback using QTimer to avoid blocking UI."""
        self.status_text.append("⏳ Waiting for authorization... (this may take a few minutes)")
        
        self.callback_timer = QTimer()
        self.callback_timer.timeout.connect(self.check_callback_status)
        self.callback_check_count = 0
        self.callback_timer.start(1000)  # Check every second
        
    def check_callback_status(self):
        """Check if callback has been received."""
        self.callback_check_count += 1
        
        if self.callback_server and self.callback_server.server and self.callback_server.server.callback_received:
            # Callback received, stop timer and process
            self.callback_timer.stop()
            self.callback_server.stop()
            
            callback_data = self.callback_server.callback_data
            
            if callback_data['error']:
                self.status_text.append(f"❌ Authorization failed: {callback_data['error_description']}")
                return
                
            if not callback_data['code']:
                self.status_text.append("❌ No authorization code received")
                return
                
            # Verify state
            if self.auth_state and callback_data['state'] != self.auth_state:
                self.status_text.append("❌ Security check failed. Please try again.")
                return
            
            self.status_text.append("✅ Authorization code received, exchanging for tokens...")
            
            # Start worker to handle callback
            self.worker = GoogleServiceWorker("handle_callback", self.service_name, {
                "code": callback_data['code'],
                "state": callback_data['state']
            })
            self.worker.finished.connect(self.on_callback_handled)
            self.worker.start()
            
        elif self.callback_check_count >= 300:  # 5 minutes timeout
            self.callback_timer.stop()
            if self.callback_server:
                self.callback_server.stop()
            self.status_text.append("❌ Authorization timed out. Please try again.")
            QMessageBox.warning(self, "Timeout", "Authorization timed out. Please try again.")
            
    def show_callback_dialog(self):
        """Show dialog for entering callback URL."""
        from PySide6.QtWidgets import QInputDialog
        
        dialog_text = (
            f"After authorizing {self.service_info['name']} in your browser, "
            "you'll be redirected to a URL that starts with your redirect URI. "
            "Please copy and paste that entire URL here:"
        )
        
        callback_url, ok = QInputDialog.getText(
            self, f"{self.service_info['name']} Authorization", 
            dialog_text,
            text=""
        )
        
        if ok and callback_url.strip():
            self.handle_callback_url(callback_url.strip())
        else:
            self.status_text.append("❌ Authorization cancelled by user")
            
    def handle_callback_url(self, callback_url: str):
        """Handle the callback URL from OAuth flow."""
        try:
            from urllib.parse import urlparse, parse_qs
            
            # Parse the URL
            parsed = urlparse(callback_url)
            params = parse_qs(parsed.query)
            
            # Extract code and state
            code = params.get('code', [''])[0]
            state = params.get('state', [''])[0]
            error = params.get('error', [''])[0]
            
            if error:
                error_desc = params.get('error_description', ['Unknown error'])[0]
                self.status_text.append(f"❌ Authorization failed: {error_desc}")
                return
                
            if not code:
                self.status_text.append("❌ No authorization code found in callback URL")
                return
                
            # Verify state if we have one stored
            if hasattr(self, 'auth_state') and self.auth_state and state != self.auth_state:
                self.status_text.append("❌ Security check failed. Please try again.")
                return
            
            self.status_text.append("✅ Authorization code received, exchanging for tokens...")
            
            # Start worker to handle callback
            self.worker = GoogleServiceWorker("handle_callback", self.service_name, {
                "code": code,
                "state": state
            })
            self.worker.finished.connect(self.on_callback_handled)
            self.worker.start()
            
        except Exception as e:
            self.status_text.append(f"❌ Error parsing callback URL: {str(e)}")
            
    def on_callback_handled(self, success: bool, message: str, data: Dict[str, Any]):
        """Handle callback completion."""
        if success:
            self.status_text.append(f"✅ {message}")
            self.authenticated = True
            self.connected = True
            self.update_ui_state()
            QMessageBox.information(self, "Success", 
                                  f"{self.service_info['name']} has been connected successfully!")
        else:
            self.status_text.append(f"❌ {message}")
            QMessageBox.critical(self, "Authentication Failed", message)
    
    def on_disconnect_complete(self, success: bool, message: str, data: Dict[str, Any]):
        """Handle disconnect completion."""
        if success:
            self.status_text.append(f"✅ {message}")
            self.authenticated = False
            self.connected = False
            self.update_ui_state()
            QMessageBox.information(self, "Disconnected", 
                                  f"{self.service_info['name']} has been disconnected.")
        else:
            self.status_text.append(f"❌ {message}")
            QMessageBox.critical(self, "Disconnect Failed", message)
    
    def on_status_checked(self, success: bool, message: str, data: Dict[str, Any]):
        """Handle status check completion."""
        if success:
            self.authenticated = data.get("authenticated", False)
            self.connected = data.get("connected", False)
            self.update_ui_state()
            
            status_msg = f"Status: {'Connected' if self.connected else 'Not connected'}"
            self.status_text.append(status_msg)
        else:
            self.status_text.append(f"Status check failed: {message}")
        
        # Emit status change signal
        self.status_changed.emit(self.service_name, {
            "authenticated": self.authenticated,
            "connected": self.connected,
            "message": message
        })
    
    def cleanup(self):
        """Clean up resources when widget is destroyed."""
        if hasattr(self, 'callback_timer') and self.callback_timer:
            self.callback_timer.stop()
        
        if self.callback_server:
            self.callback_server.stop()
            self.callback_server = None
    
    def update_ui_state(self):
        """Update UI elements based on current state."""
        if self.connected:
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green;")
            self.auth_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
        elif self.authenticated:
            self.status_label.setText("Authenticated")
            self.status_label.setStyleSheet("color: blue;")
            self.auth_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
        else:
            self.status_label.setText("Not connected")
            self.status_label.setStyleSheet("color: red;")
            self.auth_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)

class GoogleServicesDialog(BaseDialog):
    """Dialog for managing all Google services."""
    
    def __init__(self, parent=None):
        super().__init__(parent, "Google Services Manager", 900, 700)
        
        # Google services configuration
        self.google_services = {
            "youtube": {
                "name": "YouTube",
                "description": "Upload videos and manage your YouTube channel. Supports both regular videos and YouTube Shorts."
            },
            "google_photos": {
                "name": "Google Photos",
                "description": "Access and import photos from your Google Photos library for use in your social media posts."
            },
            "google_business": {
                "name": "Google My Business",
                "description": "Manage your Google My Business posts and locations. Perfect for local businesses."
            }
        }
        
        self.service_widgets = {}
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self.content_widget)
        
        # Header
        header_label = QLabel("Google Services Integration")
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(16)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Description
        desc_label = QLabel(
            "Connect to different Google services using separate accounts. "
            "Each service can use a different Google account for maximum flexibility."
        )
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(desc_label)
        
        # Tab widget for services
        self.tab_widget = QTabWidget()
        
        for service_name, service_info in self.google_services.items():
            # Create service widget
            service_widget = GoogleServiceWidget(service_name, service_info)
            service_widget.status_changed.connect(self.on_service_status_changed)
            
            # Add to tab widget
            self.tab_widget.addTab(service_widget, service_info["name"])
            self.service_widgets[service_name] = service_widget
        
        layout.addWidget(self.tab_widget)
        
        # Overall status
        status_group = QGroupBox("Overall Status")
        status_layout = QVBoxLayout(status_group)
        
        self.overall_status_label = QLabel("Checking services...")
        status_layout.addWidget(self.overall_status_label)
        
        layout.addWidget(status_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Refresh All")
        refresh_button.clicked.connect(self.refresh_all_services)
        buttons_layout.addWidget(refresh_button)
        
        buttons_layout.addStretch()
        
        help_button = QPushButton("Help")
        help_button.clicked.connect(self.show_help)
        buttons_layout.addWidget(help_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(close_button)
        
        layout.addLayout(buttons_layout)
    
    def refresh_all_services(self):
        """Refresh status for all services."""
        for service_widget in self.service_widgets.values():
            service_widget.check_status()
    
    def on_service_status_changed(self, service_name: str, status_data: Dict[str, Any]):
        """Handle status change for a service."""
        # Update overall status
        connected_services = []
        for name, widget in self.service_widgets.items():
            if widget.connected:
                connected_services.append(self.google_services[name]["name"])
        
        if connected_services:
            status_text = f"Connected services: {', '.join(connected_services)}"
        else:
            status_text = "No services connected"
        
        self.overall_status_label.setText(status_text)
    
    def show_help(self):
        """Show help information."""
        help_text = """
<h3>Google Services Integration Help</h3>

<p>This dialog allows you to connect to different Google services using separate Google accounts.</p>

<h4>Setup Process:</h4>
<ol>
<li><b>Get OAuth2 Credentials:</b> Go to the Google Cloud Console and create OAuth2 credentials for each service you want to use.</li>
<li><b>Enter Credentials:</b> For each service tab, enter the Client ID and Client Secret.</li>
<li><b>Setup:</b> Click "Setup Credentials" to save the credentials.</li>
<li><b>Authenticate:</b> Click "Authenticate" to open the Google authorization page.</li>
<li><b>Complete Authorization:</b> Follow the prompts in your browser to grant access.</li>
</ol>

<h4>Benefits of Separate Accounts:</h4>
<ul>
<li>Use your personal account for YouTube</li>
<li>Use your business account for Google My Business</li>
<li>Use a shared account for Google Photos</li>
</ul>

<h4>Required Scopes:</h4>
<ul>
<li><b>YouTube:</b> youtube.upload, youtube, youtube.readonly</li>
<li><b>Google Photos:</b> photoslibrary.readonly</li>
<li><b>Google My Business:</b> business.manage</li>
</ul>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Help - Google Services")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.exec() 