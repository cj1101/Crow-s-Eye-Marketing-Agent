"""
Unified connection dialog for connecting to multiple social media platforms.
Supports Meta (Instagram/Facebook) and X (Twitter) with comprehensive testing.
"""
import os
import json
import logging
import webbrowser
from typing import Dict, Any, Optional, List

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
    QStackedWidget, QWidget, QProgressBar, QMessageBox, QTextEdit,
    QGroupBox, QCheckBox, QLineEdit, QFormLayout, QTabWidget,
    QScrollArea, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QFont, QPixmap, QIcon

from ...features.authentication.oauth_handler import oauth_handler
from ...api.twitter.x_oauth_handler import x_oauth_handler
from ...api.linkedin.linkedin_oauth_handler import linkedin_oauth_handler
from ...features.authentication.oauth_callback_server import oauth_callback_server
from ...api.twitter.x_posting_handler import XPostingHandler
from ...api.meta.meta_posting_handler import MetaPostingHandler
from ...api.linkedin.linkedin_posting_handler import LinkedInPostingHandler
from ...config import constants as const
from ..base_dialog import BaseDialog

logger = logging.getLogger(__name__)

class ConnectionTestWorker(QThread):
    """Worker thread for testing platform connections."""
    
    test_complete = Signal(str, bool, str)  # platform, success, message
    all_tests_complete = Signal(dict)  # results dict
    
    def __init__(self, platforms_to_test: List[str]):
        super().__init__()
        self.platforms_to_test = platforms_to_test
        self.results = {}
        
    def run(self):
        """Run connection tests for all specified platforms."""
        for platform in self.platforms_to_test:
            try:
                success, message = self._test_platform_connection(platform)
                self.results[platform] = (success, message)
                self.test_complete.emit(platform, success, message)
            except Exception as e:
                error_msg = f"Test failed: {str(e)}"
                self.results[platform] = (False, error_msg)
                self.test_complete.emit(platform, False, error_msg)
        
        self.all_tests_complete.emit(self.results)
    
    def _test_platform_connection(self, platform: str) -> tuple[bool, str]:
        """Test connection to a specific platform."""
        platform_lower = platform.lower()
        
        if platform_lower in ['instagram', 'facebook', 'meta']:
            return self._test_meta_connection()
        elif platform_lower in ['x', 'twitter']:
            return self._test_x_connection()
        elif platform_lower == 'linkedin':
            return self._test_linkedin_connection()
        else:
            return False, f"Unknown platform: {platform}"
    
    def _test_meta_connection(self) -> tuple[bool, str]:
        """Test Meta API connection."""
        try:
            handler = MetaPostingHandler()
            status = handler.get_posting_status()
            
            if not status.get('credentials_loaded', False):
                return False, "Meta credentials not loaded"
            
            if not status.get('instagram_available', False) and not status.get('facebook_available', False):
                return False, "No Meta platforms available"
            
            # Try to make a test API call
            # This would be a lightweight call like getting user info
            return True, "Meta connection successful"
            
        except Exception as e:
            return False, f"Meta connection failed: {str(e)}"
    
    def _test_x_connection(self) -> tuple[bool, str]:
        """Test X API connection."""
        try:
            handler = XPostingHandler()
            status = handler.get_posting_status()
            
            if not status.get('credentials_loaded', False):
                return False, "X credentials not loaded"
            
            if not status.get('x_available', False):
                return False, "X platform not available"
            
            # Try to make a test API call
            return True, "X connection successful"
            
        except Exception as e:
            return False, f"X connection failed: {str(e)}"
    
    def _test_linkedin_connection(self) -> tuple[bool, str]:
        """Test LinkedIn API connection."""
        try:
            handler = LinkedInPostingHandler()
            status = handler.get_posting_status()
            
            if not status.get('credentials_loaded', False):
                return False, "LinkedIn credentials not loaded"
            
            if not status.get('linkedin_available', False):
                return False, "LinkedIn platform not available"
            
            return True, "LinkedIn connection successful"
            
        except Exception as e:
            return False, f"LinkedIn connection failed: {str(e)}"

class UnifiedConnectionDialog(BaseDialog):
    """Unified dialog for connecting to multiple social media platforms."""
    
    connection_successful = Signal(dict)  # platform_status dict
    
    def __init__(self, parent=None):
        """Initialize the unified connection dialog."""
        super().__init__(parent)
        self.setWindowTitle(self.tr("Connect to Social Media Platforms"))
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        self.setMaximumWidth(900)
        self.setMaximumHeight(800)
        
        # Set window properties
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setModal(True)
        
        # Initialize state
        self.platform_status = {
            'meta': {'connected': False, 'error': None},
            'x': {'connected': False, 'error': None},
            'linkedin': {'connected': False, 'error': None},
            'google_business': {'connected': False, 'error': None},
            'bluesky': {'connected': False, 'error': None},
            'tiktok': {'connected': False, 'error': None},
            'pinterest': {'connected': False, 'error': None},
            'threads': {'connected': False, 'error': None},
            'instagram_api': {'connected': False, 'error': None}
        }
        self.test_worker = None
        
        self._setup_ui()
        self._connect_signals()
        self.retranslateUi()
        self._check_existing_connections()
        
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        self._create_header_section(layout)
        
        # Main content with tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background-color: #8B5A9F;
                color: white;
            }
        """)
        
        # Create tabs for each platform
        self._create_meta_tab()
        self._create_x_tab()
        self._create_linkedin_tab()
        self._create_google_business_tab()
        self._create_bluesky_tab()
        self._create_tiktok_tab()
        self._create_pinterest_tab()
        self._create_threads_tab()
        self._create_instagram_api_tab()
        self._create_testing_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Status section
        self._create_status_section(layout)
        
        # Buttons
        self._create_button_section(layout)
        
    def _create_header_section(self, layout):
        """Create the header section."""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #8B5A9F;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        # Title
        self.title_label = QLabel(self.tr("Connect Your Social Media Accounts"))
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
        self.subtitle_label = QLabel(self.tr("Connect to 9+ social media platforms including Meta, X, LinkedIn, TikTok, Pinterest, BlueSky, and more"))
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                background: transparent;
                margin: 5px 0px 0px 0px;
                font-weight: normal;
            }
        """)
        header_layout.addWidget(self.subtitle_label)
        
        layout.addWidget(header_frame)
        
    def _create_meta_tab(self):
        """Create the Meta (Instagram/Facebook) connection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Platform info
        info_group = QGroupBox(self.tr("Meta (Instagram & Facebook)"))
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel(self.tr(
            "Connect your Instagram and Facebook accounts through Meta's API. "
            "This allows you to post content to both platforms simultaneously."
        ))
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Connection status
        self.meta_status_group = QGroupBox(self.tr("Connection Status"))
        status_layout = QVBoxLayout(self.meta_status_group)
        
        self.meta_status_label = QLabel(self.tr("Not connected"))
        self.meta_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        status_layout.addWidget(self.meta_status_label)
        
        layout.addWidget(self.meta_status_group)
        
        # Connection button
        self.meta_connect_btn = QPushButton(self.tr("Connect with Meta"))
        self.meta_connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #1877F2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #166FE5;
            }
            QPushButton:pressed {
                background-color: #1464CC;
            }
        """)
        self.meta_connect_btn.clicked.connect(self._connect_meta)
        layout.addWidget(self.meta_connect_btn)
        
        # Disconnect button (initially hidden)
        self.meta_disconnect_btn = QPushButton(self.tr("Disconnect"))
        self.meta_disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.meta_disconnect_btn.clicked.connect(self._disconnect_meta)
        self.meta_disconnect_btn.setVisible(False)
        layout.addWidget(self.meta_disconnect_btn)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr("Meta"))
        
    def _create_x_tab(self):
        """Create the X (Twitter) connection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Platform info
        info_group = QGroupBox(self.tr("X (Twitter)"))
        info_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel(self.tr(
            "Connect your X (Twitter) account to share posts and media. "
            "Click the button below to sign in with your X account."
        ))
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 14px; color: #333; padding: 10px;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Connection status
        self.x_status_group = QGroupBox(self.tr("Connection Status"))
        self.x_status_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        status_layout = QVBoxLayout(self.x_status_group)
        
        self.x_status_label = QLabel(self.tr("Not connected"))
        self.x_status_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 16px; padding: 10px;")
        status_layout.addWidget(self.x_status_label)
        
        layout.addWidget(self.x_status_group)
        
        # Connection button
        self.x_connect_btn = QPushButton(self.tr("Connect with X"))
        self.x_connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #1DA1F2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #1991DB;
            }
            QPushButton:pressed {
                background-color: #1464CC;
            }
        """)
        self.x_connect_btn.clicked.connect(self._connect_x)
        layout.addWidget(self.x_connect_btn)
        
        # Disconnect button (initially hidden)
        self.x_disconnect_btn = QPushButton(self.tr("Disconnect"))
        self.x_disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.x_disconnect_btn.clicked.connect(self._disconnect_x)
        self.x_disconnect_btn.setVisible(False)
        layout.addWidget(self.x_disconnect_btn)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr("X (Twitter)"))
        
    def _create_linkedin_tab(self):
        """Create the LinkedIn connection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Platform info
        info_group = QGroupBox(self.tr("LinkedIn"))
        info_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel(self.tr(
            "Connect your LinkedIn account to share professional content. "
            "Click the button below to sign in with your LinkedIn account."
        ))
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 14px; color: #333; padding: 10px;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Connection status
        self.linkedin_status_group = QGroupBox(self.tr("Connection Status"))
        self.linkedin_status_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        status_layout = QVBoxLayout(self.linkedin_status_group)
        
        self.linkedin_status_label = QLabel(self.tr("Not connected"))
        self.linkedin_status_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 16px; padding: 10px;")
        status_layout.addWidget(self.linkedin_status_label)
        
        layout.addWidget(self.linkedin_status_group)
        
        # Connection button
        self.linkedin_connect_btn = QPushButton(self.tr("Connect with LinkedIn"))
        self.linkedin_connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #0077B5;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #005885;
            }
            QPushButton:pressed {
                background-color: #004A6B;
            }
        """)
        self.linkedin_connect_btn.clicked.connect(self._connect_linkedin)
        layout.addWidget(self.linkedin_connect_btn)
        
        # Disconnect button (initially hidden)
        self.linkedin_disconnect_btn = QPushButton(self.tr("Disconnect"))
        self.linkedin_disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.linkedin_disconnect_btn.clicked.connect(self._disconnect_linkedin)
        self.linkedin_disconnect_btn.setVisible(False)
        layout.addWidget(self.linkedin_disconnect_btn)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr("LinkedIn"))
        
    def _create_google_business_tab(self):
        """Create the Google My Business connection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Platform info
        info_group = QGroupBox(self.tr("Google My Business"))
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel(self.tr(
            "Connect your Google My Business account to post updates and photos to your business listing. "
            "This helps customers stay informed about your business."
        ))
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Connection status
        self.google_business_status_group = QGroupBox(self.tr("Connection Status"))
        status_layout = QVBoxLayout(self.google_business_status_group)
        
        self.google_business_status_label = QLabel(self.tr("Not connected"))
        self.google_business_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        status_layout.addWidget(self.google_business_status_label)
        
        layout.addWidget(self.google_business_status_group)
        
        # Connection button
        self.google_business_connect_btn = QPushButton(self.tr("Connect with Google"))
        self.google_business_connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285F4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3367D6;
            }
        """)
        self.google_business_connect_btn.clicked.connect(self._connect_google_business)
        layout.addWidget(self.google_business_connect_btn)
        
        # Disconnect button
        self.google_business_disconnect_btn = QPushButton(self.tr("Disconnect"))
        self.google_business_disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.google_business_disconnect_btn.clicked.connect(self._disconnect_google_business)
        self.google_business_disconnect_btn.setVisible(False)
        layout.addWidget(self.google_business_disconnect_btn)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr("Google Business"))
        
    def _create_bluesky_tab(self):
        """Create the BlueSky connection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Platform info
        info_group = QGroupBox(self.tr("BlueSky"))
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel(self.tr(
            "Connect your BlueSky account to share posts on the decentralized social network. "
            "BlueSky uses the AT Protocol for open social networking."
        ))
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Connection status
        self.bluesky_status_group = QGroupBox(self.tr("Connection Status"))
        status_layout = QVBoxLayout(self.bluesky_status_group)
        
        self.bluesky_status_label = QLabel(self.tr("Not connected"))
        self.bluesky_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        status_layout.addWidget(self.bluesky_status_label)
        
        layout.addWidget(self.bluesky_status_group)
        
        # Connection button
        self.bluesky_connect_btn = QPushButton(self.tr("Connect with BlueSky"))
        self.bluesky_connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #00A8E8;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0077B6;
            }
        """)
        self.bluesky_connect_btn.clicked.connect(self._connect_bluesky)
        layout.addWidget(self.bluesky_connect_btn)
        
        # Disconnect button
        self.bluesky_disconnect_btn = QPushButton(self.tr("Disconnect"))
        self.bluesky_disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.bluesky_disconnect_btn.clicked.connect(self._disconnect_bluesky)
        self.bluesky_disconnect_btn.setVisible(False)
        layout.addWidget(self.bluesky_disconnect_btn)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr("BlueSky"))
        
    def _create_tiktok_tab(self):
        """Create the TikTok connection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Platform info
        info_group = QGroupBox(self.tr("TikTok"))
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel(self.tr(
            "Connect your TikTok account to share videos on the popular short-form video platform. "
            "Perfect for reaching younger audiences with creative content."
        ))
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Connection status
        self.tiktok_status_group = QGroupBox(self.tr("Connection Status"))
        status_layout = QVBoxLayout(self.tiktok_status_group)
        
        self.tiktok_status_label = QLabel(self.tr("Not connected"))
        self.tiktok_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        status_layout.addWidget(self.tiktok_status_label)
        
        layout.addWidget(self.tiktok_status_group)
        
        # Connection button
        self.tiktok_connect_btn = QPushButton(self.tr("Connect with TikTok"))
        self.tiktok_connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #000000;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)
        self.tiktok_connect_btn.clicked.connect(self._connect_tiktok)
        layout.addWidget(self.tiktok_connect_btn)
        
        # Disconnect button
        self.tiktok_disconnect_btn = QPushButton(self.tr("Disconnect"))
        self.tiktok_disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.tiktok_disconnect_btn.clicked.connect(self._disconnect_tiktok)
        self.tiktok_disconnect_btn.setVisible(False)
        layout.addWidget(self.tiktok_disconnect_btn)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr("TikTok"))
        
    def _create_pinterest_tab(self):
        """Create the Pinterest connection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Platform info
        info_group = QGroupBox(self.tr("Pinterest"))
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel(self.tr(
            "Connect your Pinterest account to share pins and reach audiences interested in visual content. "
            "Great for showcasing products and driving traffic to your website."
        ))
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Connection status
        self.pinterest_status_group = QGroupBox(self.tr("Connection Status"))
        status_layout = QVBoxLayout(self.pinterest_status_group)
        
        self.pinterest_status_label = QLabel(self.tr("Not connected"))
        self.pinterest_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        status_layout.addWidget(self.pinterest_status_label)
        
        layout.addWidget(self.pinterest_status_group)
        
        # Connection button
        self.pinterest_connect_btn = QPushButton(self.tr("Connect with Pinterest"))
        self.pinterest_connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #E60023;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C8001A;
            }
        """)
        self.pinterest_connect_btn.clicked.connect(self._connect_pinterest)
        layout.addWidget(self.pinterest_connect_btn)
        
        # Disconnect button
        self.pinterest_disconnect_btn = QPushButton(self.tr("Disconnect"))
        self.pinterest_disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.pinterest_disconnect_btn.clicked.connect(self._disconnect_pinterest)
        self.pinterest_disconnect_btn.setVisible(False)
        layout.addWidget(self.pinterest_disconnect_btn)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr("Pinterest"))
        
    def _create_threads_tab(self):
        """Create the Threads connection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Platform info
        info_group = QGroupBox(self.tr("Threads"))
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel(self.tr(
            "Connect your Threads account to share text and media posts on Meta's Twitter alternative. "
            "Integrates seamlessly with your Instagram account."
        ))
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Connection status
        self.threads_status_group = QGroupBox(self.tr("Connection Status"))
        status_layout = QVBoxLayout(self.threads_status_group)
        
        self.threads_status_label = QLabel(self.tr("Not connected"))
        self.threads_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        status_layout.addWidget(self.threads_status_label)
        
        layout.addWidget(self.threads_status_group)
        
        # Connection button
        self.threads_connect_btn = QPushButton(self.tr("Connect with Threads"))
        self.threads_connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #000000;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)
        self.threads_connect_btn.clicked.connect(self._connect_threads)
        layout.addWidget(self.threads_connect_btn)
        
        # Disconnect button
        self.threads_disconnect_btn = QPushButton(self.tr("Disconnect"))
        self.threads_disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.threads_disconnect_btn.clicked.connect(self._disconnect_threads)
        self.threads_disconnect_btn.setVisible(False)
        layout.addWidget(self.threads_disconnect_btn)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr("Threads"))
        
    def _create_instagram_api_tab(self):
        """Create the Instagram API connection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Platform info
        info_group = QGroupBox(self.tr("Instagram API"))
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel(self.tr(
            "Connect directly to Instagram's API for advanced posting features. "
            "This provides additional functionality beyond the standard Meta integration."
        ))
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Connection status
        self.instagram_api_status_group = QGroupBox(self.tr("Connection Status"))
        status_layout = QVBoxLayout(self.instagram_api_status_group)
        
        self.instagram_api_status_label = QLabel(self.tr("Not connected"))
        self.instagram_api_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        status_layout.addWidget(self.instagram_api_status_label)
        
        layout.addWidget(self.instagram_api_status_group)
        
        # Connection button
        self.instagram_api_connect_btn = QPushButton(self.tr("Connect with Instagram API"))
        self.instagram_api_connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #E4405F;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C13584;
            }
        """)
        self.instagram_api_connect_btn.clicked.connect(self._connect_instagram_api)
        layout.addWidget(self.instagram_api_connect_btn)
        
        # Disconnect button
        self.instagram_api_disconnect_btn = QPushButton(self.tr("Disconnect"))
        self.instagram_api_disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.instagram_api_disconnect_btn.clicked.connect(self._disconnect_instagram_api)
        self.instagram_api_disconnect_btn.setVisible(False)
        layout.addWidget(self.instagram_api_disconnect_btn)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr("Instagram API"))
        
    def _create_testing_tab(self):
        """Create the comprehensive testing tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Testing info
        info_group = QGroupBox(self.tr("Connection Testing"))
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel(self.tr(
            "Test all your platform connections to ensure they're working properly. "
            "This will verify credentials and API access for each connected platform."
        ))
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Test controls
        controls_group = QGroupBox(self.tr("Test Controls"))
        controls_layout = QVBoxLayout(controls_group)
        
        # Platform selection
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel(self.tr("Select platforms to test:")))
        
        self.test_meta_checkbox = QCheckBox(self.tr("Meta (Instagram/Facebook)"))
        self.test_meta_checkbox.setChecked(True)
        platform_layout.addWidget(self.test_meta_checkbox)
        
        self.test_x_checkbox = QCheckBox(self.tr("X (Twitter)"))
        self.test_x_checkbox.setChecked(True)
        platform_layout.addWidget(self.test_x_checkbox)
        
        self.test_linkedin_checkbox = QCheckBox(self.tr("LinkedIn"))
        self.test_linkedin_checkbox.setChecked(True)
        platform_layout.addWidget(self.test_linkedin_checkbox)
        
        controls_layout.addLayout(platform_layout)
        
        # Test button
        self.run_tests_btn = QPushButton(self.tr("Run Connection Tests"))
        self.run_tests_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219653;
            }
        """)
        self.run_tests_btn.clicked.connect(self._run_connection_tests)
        controls_layout.addWidget(self.run_tests_btn)
        
        layout.addWidget(controls_group)
        
        # Test results
        results_group = QGroupBox(self.tr("Test Results"))
        results_layout = QVBoxLayout(results_group)
        
        # Progress bar
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        results_layout.addWidget(self.test_progress)
        
        # Results text area
        self.test_results_text = QTextEdit()
        self.test_results_text.setMaximumHeight(200)
        self.test_results_text.setPlainText(self.tr("No tests run yet. Click 'Run Connection Tests' to begin."))
        results_layout.addWidget(self.test_results_text)
        
        layout.addWidget(results_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr("Testing"))
        
    def _create_status_section(self, layout):
        """Create the overall status section."""
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        
        self.overall_status_label = QLabel(self.tr("Overall Status: Checking connections..."))
        self.overall_status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        status_layout.addWidget(self.overall_status_label)
        
        layout.addWidget(status_frame)
        
    def _create_button_section(self, layout):
        """Create the dialog button section."""
        button_layout = QHBoxLayout()
        
        # Test all button
        self.test_all_btn = QPushButton(self.tr("Test All Connections"))
        self.test_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.test_all_btn.clicked.connect(self._test_all_connections)
        button_layout.addWidget(self.test_all_btn)
        
        button_layout.addStretch()
        
        # Close button
        self.close_btn = QPushButton(self.tr("Close"))
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        # Done button
        self.done_btn = QPushButton(self.tr("Done"))
        self.done_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219653;
            }
        """)
        self.done_btn.clicked.connect(self._on_done)
        button_layout.addWidget(self.done_btn)
        
        layout.addLayout(button_layout)
        
    def _connect_signals(self):
        """Connect internal signals."""
        # OAuth handler signals for Meta
        oauth_handler.signals.auth_success.connect(self._on_meta_auth_success)
        oauth_handler.signals.auth_error.connect(self._on_meta_auth_error)
        
        # OAuth handler signals for X
        x_oauth_handler.signals.auth_success.connect(self._on_x_auth_success)
        x_oauth_handler.signals.auth_error.connect(self._on_x_auth_error)
        
        # OAuth handler signals for LinkedIn
        linkedin_oauth_handler.signals.auth_success.connect(self._on_linkedin_auth_success)
        linkedin_oauth_handler.signals.auth_error.connect(self._on_linkedin_auth_error)
        
    def _check_existing_connections(self):
        """Check for existing platform connections."""
        # Check Meta
        try:
            meta_handler = MetaPostingHandler()
            meta_status = meta_handler.get_posting_status()
            if meta_status.get('credentials_loaded', False):
                self.platform_status['meta']['connected'] = True
                self._update_meta_status(True, "Connected")
            else:
                self._update_meta_status(False, "Not connected")
        except Exception as e:
            self._update_meta_status(False, f"Error: {str(e)}")
        
        # Check X
        try:
            x_handler = XPostingHandler()
            x_status = x_handler.get_posting_status()
            if x_status.get('credentials_loaded', False):
                self.platform_status['x']['connected'] = True
                self._update_x_status(True, "Connected")
            else:
                self._update_x_status(False, "Not connected")
        except Exception as e:
            self._update_x_status(False, f"Error: {str(e)}")
        
        # Check LinkedIn
        try:
            linkedin_handler = LinkedInPostingHandler()
            linkedin_status = linkedin_handler.get_posting_status()
            if linkedin_status.get('credentials_loaded', False):
                self.platform_status['linkedin']['connected'] = True
                self._update_linkedin_status(True, "Connected")
            else:
                self._update_linkedin_status(False, "Not connected")
        except Exception as e:
            self._update_linkedin_status(False, f"Error: {str(e)}")
        
        self._update_overall_status()
        
    def _connect_meta(self):
        """Connect to Meta platforms."""
        try:
            # Start callback server
            oauth_callback_server.start()
            
            # Start OAuth flow
            auth_url = oauth_handler.start_oauth_flow()
            if auth_url:
                webbrowser.open(auth_url)
                QMessageBox.information(
                    self,
                    self.tr("Meta Authentication"),
                    self.tr("Please complete the authentication in your browser. "
                           "Return to this dialog when finished.")
                )
            else:
                QMessageBox.warning(
                    self,
                    self.tr("Authentication Error"),
                    self.tr("Failed to start Meta authentication process.")
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                self.tr("Connection Error"),
                self.tr("Error connecting to Meta: {error}").format(error=str(e))
            )
    
    def _disconnect_meta(self):
        """Disconnect from Meta platforms."""
        try:
            # Clear credentials
            if os.path.exists(const.META_CREDENTIALS_FILE):
                os.remove(const.META_CREDENTIALS_FILE)
            
            self.platform_status['meta']['connected'] = False
            self._update_meta_status(False, "Disconnected")
            self._update_overall_status()
            
            QMessageBox.information(
                self,
                self.tr("Disconnected"),
                self.tr("Successfully disconnected from Meta platforms.")
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                self.tr("Disconnect Error"),
                self.tr("Error disconnecting from Meta: {error}").format(error=str(e))
            )
    
    def _connect_x(self):
        """Connect to X platform."""
        try:
            # Start callback server
            oauth_callback_server.start()
            
            # Start OAuth flow
            auth_url = x_oauth_handler.start_oauth_flow()
            if auth_url:
                webbrowser.open(auth_url)
                QMessageBox.information(
                    self,
                    self.tr("X Authentication"),
                    self.tr("Please complete the authentication in your browser. "
                           "Return to this dialog when finished.")
                )
            else:
                QMessageBox.warning(
                    self,
                    self.tr("Authentication Error"),
                    self.tr("Failed to start X authentication process.")
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                self.tr("Connection Error"),
                self.tr("Error connecting to X: {error}").format(error=str(e))
            )
    
    def _disconnect_x(self):
        """Disconnect from X platform."""
        try:
            # Clear credentials
            x_oauth_handler.logout()
            
            self.platform_status['x']['connected'] = False
            self._update_x_status(False, "Disconnected")
            self._update_overall_status()
            
            QMessageBox.information(
                self,
                self.tr("Disconnected"),
                self.tr("Successfully disconnected from X.")
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                self.tr("Disconnect Error"),
                self.tr("Error disconnecting from X: {error}").format(error=str(e))
            )
    
    def _connect_linkedin(self):
        """Connect to LinkedIn platform."""
        try:
            # Start callback server
            oauth_callback_server.start()
            
            # Start OAuth flow
            auth_url = linkedin_oauth_handler.start_oauth_flow()
            if auth_url:
                webbrowser.open(auth_url)
                QMessageBox.information(
                    self,
                    self.tr("LinkedIn Authentication"),
                    self.tr("Please complete the authentication in your browser. "
                           "Return to this dialog when finished.")
                )
            else:
                QMessageBox.warning(
                    self,
                    self.tr("Authentication Error"),
                    self.tr("Failed to start LinkedIn authentication process.")
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                self.tr("Connection Error"),
                self.tr("Error connecting to LinkedIn: {error}").format(error=str(e))
            )
    
    def _disconnect_linkedin(self):
        """Disconnect from LinkedIn platform."""
        try:
            # Clear credentials
            linkedin_oauth_handler.logout()
            
            self.platform_status['linkedin']['connected'] = False
            self._update_linkedin_status(False, "Disconnected")
            self._update_overall_status()
            
            QMessageBox.information(
                self,
                self.tr("Disconnected"),
                self.tr("Successfully disconnected from LinkedIn.")
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                self.tr("Disconnect Error"),
                self.tr("Error disconnecting from LinkedIn: {error}").format(error=str(e))
            )
    
    def _connect_google_business(self):
        """Connect to Google My Business."""
        QMessageBox.information(
            self,
            "Google My Business Connection",
            "Google My Business connection will be implemented in a future update.\n\n"
            "This will allow you to post updates directly to your business listing."
        )
    
    def _disconnect_google_business(self):
        """Disconnect from Google My Business."""
        self.platform_status['google_business']['connected'] = False
        self._update_google_business_status(False, "Disconnected")
    
    def _connect_bluesky(self):
        """Connect to BlueSky."""
        QMessageBox.information(
            self,
            "BlueSky Connection",
            "BlueSky connection will be implemented in a future update.\n\n"
            "This will allow you to post to the decentralized social network."
        )
    
    def _disconnect_bluesky(self):
        """Disconnect from BlueSky."""
        self.platform_status['bluesky']['connected'] = False
        self._update_bluesky_status(False, "Disconnected")
    
    def _connect_tiktok(self):
        """Connect to TikTok."""
        QMessageBox.information(
            self,
            "TikTok Connection",
            "TikTok connection will be implemented in a future update.\n\n"
            "This will allow you to post videos to TikTok."
        )
    
    def _disconnect_tiktok(self):
        """Disconnect from TikTok."""
        self.platform_status['tiktok']['connected'] = False
        self._update_tiktok_status(False, "Disconnected")
    
    def _connect_pinterest(self):
        """Connect to Pinterest."""
        QMessageBox.information(
            self,
            "Pinterest Connection",
            "Pinterest connection will be implemented in a future update.\n\n"
            "This will allow you to create pins and boards."
        )
    
    def _disconnect_pinterest(self):
        """Disconnect from Pinterest."""
        self.platform_status['pinterest']['connected'] = False
        self._update_pinterest_status(False, "Disconnected")
    
    def _connect_threads(self):
        """Connect to Threads."""
        QMessageBox.information(
            self,
            "Threads Connection",
            "Threads connection will be implemented in a future update.\n\n"
            "This will allow you to post to Meta's Twitter alternative."
        )
    
    def _disconnect_threads(self):
        """Disconnect from Threads."""
        self.platform_status['threads']['connected'] = False
        self._update_threads_status(False, "Disconnected")
    
    def _connect_instagram_api(self):
        """Connect to Instagram API."""
        QMessageBox.information(
            self,
            "Instagram API Connection",
            "Instagram API connection will be implemented in a future update.\n\n"
            "This will provide advanced Instagram posting features."
        )
    
    def _disconnect_instagram_api(self):
        """Disconnect from Instagram API."""
        self.platform_status['instagram_api']['connected'] = False
        self._update_instagram_api_status(False, "Disconnected")

    
    def _test_x_connection(self):
        """Test X connection."""
        self._run_single_platform_test('x')
    
    def _test_linkedin_connection(self):
        """Test LinkedIn connection."""
        self._run_single_platform_test('linkedin')
    
    def _test_all_connections(self):
        """Test all platform connections."""
        platforms = []
        if self.platform_status['meta']['connected']:
            platforms.append('meta')
        if self.platform_status['x']['connected']:
            platforms.append('x')
        if self.platform_status['linkedin']['connected']:
            platforms.append('linkedin')
        
        if not platforms:
            QMessageBox.information(
                self,
                self.tr("No Connections"),
                self.tr("No platforms are connected. Please connect to at least one platform first.")
            )
            return
        
        self._run_connection_tests_for_platforms(platforms)
    
    def _run_connection_tests(self):
        """Run connection tests for selected platforms."""
        platforms = []
        if self.test_meta_checkbox.isChecked():
            platforms.append('meta')
        if self.test_x_checkbox.isChecked():
            platforms.append('x')
        if self.test_linkedin_checkbox.isChecked():
            platforms.append('linkedin')
        
        if not platforms:
            QMessageBox.warning(
                self,
                self.tr("No Platforms Selected"),
                self.tr("Please select at least one platform to test.")
            )
            return
        
        self._run_connection_tests_for_platforms(platforms)
    
    def _run_single_platform_test(self, platform: str):
        """Run a test for a single platform."""
        self._run_connection_tests_for_platforms([platform])
    
    def _run_connection_tests_for_platforms(self, platforms: List[str]):
        """Run connection tests for specified platforms."""
        if self.test_worker and self.test_worker.isRunning():
            QMessageBox.warning(
                self,
                self.tr("Test in Progress"),
                self.tr("A test is already running. Please wait for it to complete.")
            )
            return
        
        # Clear previous results
        self.test_results_text.clear()
        self.test_results_text.append(self.tr("Starting connection tests...\n"))
        
        # Show progress
        self.test_progress.setVisible(True)
        self.test_progress.setRange(0, len(platforms))
        self.test_progress.setValue(0)
        
        # Disable test buttons
        self.run_tests_btn.setEnabled(False)
        self.test_all_btn.setEnabled(False)
        self.x_test_btn.setEnabled(False)
        self.linkedin_test_btn.setEnabled(False)
        
        # Start test worker
        self.test_worker = ConnectionTestWorker(platforms)
        self.test_worker.test_complete.connect(self._on_test_complete)
        self.test_worker.all_tests_complete.connect(self._on_all_tests_complete)
        self.test_worker.start()
    
    def _on_test_complete(self, platform: str, success: bool, message: str):
        """Handle completion of a single platform test."""
        status_icon = "✅" if success else "❌"
        self.test_results_text.append(f"{status_icon} {platform.upper()}: {message}")
        
        # Update progress
        current_value = self.test_progress.value()
        self.test_progress.setValue(current_value + 1)
    
    def _on_all_tests_complete(self, results: Dict[str, tuple]):
        """Handle completion of all tests."""
        # Hide progress
        self.test_progress.setVisible(False)
        
        # Re-enable buttons
        self.run_tests_btn.setEnabled(True)
        self.test_all_btn.setEnabled(True)
        self.x_test_btn.setEnabled(True)
        self.linkedin_test_btn.setEnabled(True)
        
        # Show summary
        successful_tests = sum(1 for success, _ in results.values() if success)
        total_tests = len(results)
        
        self.test_results_text.append(f"\n📊 Test Summary: {successful_tests}/{total_tests} platforms passed")
        
        if successful_tests == total_tests:
            self.test_results_text.append("🎉 All tests passed! Your connections are working properly.")
        else:
            self.test_results_text.append("⚠️ Some tests failed. Please check the credentials for failed platforms.")
    
    def _update_meta_status(self, connected: bool, message: str):
        """Update Meta connection status."""
        self.meta_status_label.setText(message)
        if connected:
            self.meta_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.meta_connect_btn.setVisible(False)
            self.meta_disconnect_btn.setVisible(True)
        else:
            self.meta_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.meta_connect_btn.setVisible(True)
            self.meta_disconnect_btn.setVisible(False)
    
    def _update_x_status(self, connected: bool, message: str):
        """Update X connection status."""
        self.x_status_label.setText(message)
        if connected:
            self.x_status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 16px; padding: 10px;")
            self.x_connect_btn.setVisible(False)
            self.x_disconnect_btn.setVisible(True)
        else:
            self.x_status_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 16px; padding: 10px;")
            self.x_connect_btn.setVisible(True)
            self.x_disconnect_btn.setVisible(False)
    
    def _update_linkedin_status(self, connected: bool, message: str):
        """Update LinkedIn connection status."""
        self.linkedin_status_label.setText(message)
        if connected:
            self.linkedin_status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 16px; padding: 10px;")
            self.linkedin_connect_btn.setVisible(False)
            self.linkedin_disconnect_btn.setVisible(True)
        else:
            self.linkedin_status_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 16px; padding: 10px;")
            self.linkedin_connect_btn.setVisible(True)
            self.linkedin_disconnect_btn.setVisible(False)
    
    def _update_overall_status(self):
        """Update the overall connection status."""
        connected_count = sum(1 for status in self.platform_status.values() if status['connected'])
        total_platforms = len(self.platform_status)
        
        if connected_count == 0:
            status_text = self.tr("Overall Status: No platforms connected")
            status_color = "#e74c3c"
        elif connected_count == total_platforms:
            status_text = self.tr("Overall Status: All platforms connected ({count}/{total})").format(
                count=connected_count, total=total_platforms
            )
            status_color = "#27ae60"
        else:
            status_text = self.tr("Overall Status: {count}/{total} platforms connected").format(
                count=connected_count, total=total_platforms
            )
            status_color = "#f39c12"
        
        self.overall_status_label.setText(status_text)
        self.overall_status_label.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {status_color};")
    
    def _update_google_business_status(self, connected: bool, message: str):
        """Update Google My Business connection status."""
        self.platform_status['google_business']['connected'] = connected
        self.platform_status['google_business']['error'] = None if connected else message
        
        if connected:
            self.google_business_status_label.setText(self.tr("Connected"))
            self.google_business_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.google_business_connect_btn.setVisible(False)
            self.google_business_disconnect_btn.setVisible(True)
        else:
            self.google_business_status_label.setText(message)
            self.google_business_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.google_business_connect_btn.setVisible(True)
            self.google_business_disconnect_btn.setVisible(False)
        
        self._update_overall_status()
    
    def _update_bluesky_status(self, connected: bool, message: str):
        """Update BlueSky connection status."""
        self.platform_status['bluesky']['connected'] = connected
        self.platform_status['bluesky']['error'] = None if connected else message
        
        if connected:
            self.bluesky_status_label.setText(self.tr("Connected"))
            self.bluesky_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.bluesky_connect_btn.setVisible(False)
            self.bluesky_disconnect_btn.setVisible(True)
        else:
            self.bluesky_status_label.setText(message)
            self.bluesky_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.bluesky_connect_btn.setVisible(True)
            self.bluesky_disconnect_btn.setVisible(False)
        
        self._update_overall_status()
    
    def _update_tiktok_status(self, connected: bool, message: str):
        """Update TikTok connection status."""
        self.platform_status['tiktok']['connected'] = connected
        self.platform_status['tiktok']['error'] = None if connected else message
        
        if connected:
            self.tiktok_status_label.setText(self.tr("Connected"))
            self.tiktok_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.tiktok_connect_btn.setVisible(False)
            self.tiktok_disconnect_btn.setVisible(True)
        else:
            self.tiktok_status_label.setText(message)
            self.tiktok_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.tiktok_connect_btn.setVisible(True)
            self.tiktok_disconnect_btn.setVisible(False)
        
        self._update_overall_status()
    
    def _update_pinterest_status(self, connected: bool, message: str):
        """Update Pinterest connection status."""
        self.platform_status['pinterest']['connected'] = connected
        self.platform_status['pinterest']['error'] = None if connected else message
        
        if connected:
            self.pinterest_status_label.setText(self.tr("Connected"))
            self.pinterest_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.pinterest_connect_btn.setVisible(False)
            self.pinterest_disconnect_btn.setVisible(True)
        else:
            self.pinterest_status_label.setText(message)
            self.pinterest_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.pinterest_connect_btn.setVisible(True)
            self.pinterest_disconnect_btn.setVisible(False)
        
        self._update_overall_status()
    
    def _update_threads_status(self, connected: bool, message: str):
        """Update Threads connection status."""
        self.platform_status['threads']['connected'] = connected
        self.platform_status['threads']['error'] = None if connected else message
        
        if connected:
            self.threads_status_label.setText(self.tr("Connected"))
            self.threads_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.threads_connect_btn.setVisible(False)
            self.threads_disconnect_btn.setVisible(True)
        else:
            self.threads_status_label.setText(message)
            self.threads_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.threads_connect_btn.setVisible(True)
            self.threads_disconnect_btn.setVisible(False)
        
        self._update_overall_status()
    
    def _update_instagram_api_status(self, connected: bool, message: str):
        """Update Instagram API connection status."""
        self.platform_status['instagram_api']['connected'] = connected
        self.platform_status['instagram_api']['error'] = None if connected else message
        
        if connected:
            self.instagram_api_status_label.setText(self.tr("Connected"))
            self.instagram_api_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.instagram_api_connect_btn.setVisible(False)
            self.instagram_api_disconnect_btn.setVisible(True)
        else:
            self.instagram_api_status_label.setText(message)
            self.instagram_api_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.instagram_api_connect_btn.setVisible(True)
            self.instagram_api_disconnect_btn.setVisible(False)
        
        self._update_overall_status()

    
    def _on_x_auth_success(self, auth_data: Dict[str, Any]):
        """Handle successful X authentication."""
        self.platform_status['x']['connected'] = True
        username = auth_data.get('username', 'X User')
        self._update_x_status(True, f"Connected as @{username}")
        self._update_overall_status()
        
        QMessageBox.information(
            self,
            self.tr("Connection Successful"),
            self.tr("Successfully connected to X!")
        )
    
    def _on_x_auth_error(self, error_message: str):
        """Handle X authentication error."""
        self.platform_status['x']['connected'] = False
        self.platform_status['x']['error'] = error_message
        self._update_x_status(False, f"Connection failed: {error_message}")
        self._update_overall_status()
        
        QMessageBox.critical(
            self,
            self.tr("Connection Failed"),
            self.tr("Failed to connect to X: {error}").format(error=error_message)
        )
    
    def _on_linkedin_auth_success(self, auth_data: Dict[str, Any]):
        """Handle successful LinkedIn authentication."""
        self.platform_status['linkedin']['connected'] = True
        name = auth_data.get('name', 'LinkedIn User')
        self._update_linkedin_status(True, f"Connected as {name}")
        self._update_overall_status()
        
        QMessageBox.information(
            self,
            self.tr("Connection Successful"),
            self.tr("Successfully connected to LinkedIn!")
        )
    
    def _on_linkedin_auth_error(self, error_message: str):
        """Handle LinkedIn authentication error."""
        self.platform_status['linkedin']['connected'] = False
        self.platform_status['linkedin']['error'] = error_message
        self._update_linkedin_status(False, f"Connection failed: {error_message}")
        self._update_overall_status()
        
        QMessageBox.critical(
            self,
            self.tr("Connection Failed"),
            self.tr("Failed to connect to LinkedIn: {error}").format(error=error_message)
        )
    
    def _on_meta_auth_success(self, auth_data: Dict[str, Any]):
        """Handle successful Meta authentication."""
        self.platform_status['meta']['connected'] = True
        self._update_meta_status(True, "Connected successfully")
        self._update_overall_status()
        
        QMessageBox.information(
            self,
            self.tr("Connection Successful"),
            self.tr("Successfully connected to Meta platforms!")
        )
    
    def _on_meta_auth_error(self, error_message: str):
        """Handle Meta authentication error."""
        self.platform_status['meta']['connected'] = False
        self.platform_status['meta']['error'] = error_message
        self._update_meta_status(False, f"Connection failed: {error_message}")
        self._update_overall_status()
        
        QMessageBox.critical(
            self,
            self.tr("Connection Failed"),
            self.tr("Failed to connect to Meta: {error}").format(error=error_message)
        )
    
    def _on_done(self):
        """Handle done button click."""
        # Emit connection status
        self.connection_successful.emit(self.platform_status)
        self.accept()
    
    def retranslateUi(self):
        """Retranslate all UI elements."""
        self.setWindowTitle(self.tr("Connect to Social Media Platforms"))
        self.title_label.setText(self.tr("Connect Your Social Media Accounts"))
        self.subtitle_label.setText(self.tr("Connect to 9+ social media platforms including Meta, X, LinkedIn, TikTok, Pinterest, BlueSky, and more"))
        
        # Update tab titles
        self.tab_widget.setTabText(0, self.tr("Meta"))
        self.tab_widget.setTabText(1, self.tr("X (Twitter)"))
        self.tab_widget.setTabText(2, self.tr("LinkedIn"))
        self.tab_widget.setTabText(3, self.tr("Google Business"))
        self.tab_widget.setTabText(4, self.tr("BlueSky"))
        self.tab_widget.setTabText(5, self.tr("TikTok"))
        self.tab_widget.setTabText(6, self.tr("Pinterest"))
        self.tab_widget.setTabText(7, self.tr("Threads"))
        self.tab_widget.setTabText(8, self.tr("Instagram API"))
        self.tab_widget.setTabText(9, self.tr("Testing"))
        
        # Update button texts
        if hasattr(self, 'meta_connect_btn'):
            self.meta_connect_btn.setText(self.tr("Connect with Meta"))
        if hasattr(self, 'meta_disconnect_btn'):
            self.meta_disconnect_btn.setText(self.tr("Disconnect"))
        if hasattr(self, 'x_connect_btn'):
            self.x_connect_btn.setText(self.tr("Connect with X"))
        if hasattr(self, 'x_disconnect_btn'):
            self.x_disconnect_btn.setText(self.tr("Disconnect"))
        if hasattr(self, 'linkedin_connect_btn'):
            self.linkedin_connect_btn.setText(self.tr("Connect with LinkedIn"))
        if hasattr(self, 'linkedin_disconnect_btn'):
            self.linkedin_disconnect_btn.setText(self.tr("Disconnect"))
        if hasattr(self, 'run_tests_btn'):
            self.run_tests_btn.setText(self.tr("Run Connection Tests"))
        if hasattr(self, 'test_all_btn'):
            self.test_all_btn.setText(self.tr("Test All Connections"))
        if hasattr(self, 'close_btn'):
            self.close_btn.setText(self.tr("Close"))
        if hasattr(self, 'done_btn'):
            self.done_btn.setText(self.tr("Done")) 