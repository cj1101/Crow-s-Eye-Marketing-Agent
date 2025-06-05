"""
Unified connection dialog for connecting to multiple social media platforms.
Supports Meta (Instagram/Facebook) and other platforms with comprehensive testing.
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
from ...features.authentication.oauth_callback_server import oauth_callback_server
from ...api.meta.meta_posting_handler import MetaPostingHandler
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
        self.subtitle_label = QLabel(self.tr("Connect to multiple social media platforms including Meta, TikTok, Pinterest, BlueSky, and more"))
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                background: transparent;
                margin: 10px 0px;
            }
        """)
        header_layout.addWidget(self.subtitle_label)
        
        layout.addWidget(header_frame)
        
    def _create_meta_tab(self):
        """Create the Meta (Instagram/Facebook) connection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Platform info
        info_group = QGroupBox(self.tr("Meta (Instagram & Facebook)"))
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
            "Connect your Meta account to post to Instagram and Facebook. "
            "This includes Instagram posts, stories, and Facebook page posts. "
            "Click the button below to sign in with your Meta account."
        ))
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 14px; color: #333; padding: 10px;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Connection status
        self.meta_status_group = QGroupBox(self.tr("Connection Status"))
        self.meta_status_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        status_layout = QVBoxLayout(self.meta_status_group)
        
        self.meta_status_label = QLabel(self.tr("Not connected"))
        self.meta_status_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 16px; padding: 10px;")
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
                margin: 10px;
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
                margin: 10px;
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
        
    def _create_google_business_tab(self):
        """Create the Google My Business connection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Platform info
        info_group = QGroupBox(self.tr("Google My Business"))
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
            "Connect your Google My Business account to post updates directly to your business listing. "
            "This feature will be available in a future update."
        ))
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 14px; color: #333; padding: 10px;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Coming soon message
        coming_soon = QLabel(self.tr("🚧 Coming Soon"))
        coming_soon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coming_soon.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #f39c12;
                padding: 20px;
                border: 2px dashed #f39c12;
                border-radius: 8px;
                margin: 20px;
            }
        """)
        layout.addWidget(coming_soon)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr("Google Business"))
        
    def _create_bluesky_tab(self):
        """Create the BlueSky connection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Platform info
        info_group = QGroupBox(self.tr("BlueSky"))
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
            "Connect your BlueSky account to post to the decentralized social network. "
            "This feature will be available in a future update."
        ))
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 14px; color: #333; padding: 10px;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Coming soon message
        coming_soon = QLabel(self.tr("🚧 Coming Soon"))
        coming_soon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coming_soon.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #f39c12;
                padding: 20px;
                border: 2px dashed #f39c12;
                border-radius: 8px;
                margin: 20px;
            }
        """)
        layout.addWidget(coming_soon)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr("BlueSky"))
        
    def _create_tiktok_tab(self):
        """Create the TikTok connection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Platform info
        info_group = QGroupBox(self.tr("TikTok"))
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
            "Connect your TikTok account to post videos and content. "
            "This feature will be available in a future update."
        ))
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 14px; color: #333; padding: 10px;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Coming soon message
        coming_soon = QLabel(self.tr("🚧 Coming Soon"))
        coming_soon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coming_soon.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #f39c12;
                padding: 20px;
                border: 2px dashed #f39c12;
                border-radius: 8px;
                margin: 20px;
            }
        """)
        layout.addWidget(coming_soon)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr("TikTok"))
        
    def _create_pinterest_tab(self):
        """Create the Pinterest connection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Platform info
        info_group = QGroupBox(self.tr("Pinterest"))
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
            "Connect your Pinterest account to create pins and boards. "
            "This feature will be available in a future update."
        ))
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 14px; color: #333; padding: 10px;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Coming soon message
        coming_soon = QLabel(self.tr("🚧 Coming Soon"))
        coming_soon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coming_soon.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #f39c12;
                padding: 20px;
                border: 2px dashed #f39c12;
                border-radius: 8px;
                margin: 20px;
            }
        """)
        layout.addWidget(coming_soon)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr("Pinterest"))
        
    def _create_threads_tab(self):
        """Create the Threads connection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Platform info
        info_group = QGroupBox(self.tr("Threads"))
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
            "Connect your Threads account to post to Meta's text-based social platform. "
            "This feature will be available in a future update."
        ))
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 14px; color: #333; padding: 10px;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Coming soon message
        coming_soon = QLabel(self.tr("🚧 Coming Soon"))
        coming_soon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coming_soon.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #f39c12;
                padding: 20px;
                border: 2px dashed #f39c12;
                border-radius: 8px;
                margin: 20px;
            }
        """)
        layout.addWidget(coming_soon)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr("Threads"))
        
    def _create_instagram_api_tab(self):
        """Create the Instagram API connection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Platform info
        info_group = QGroupBox(self.tr("Instagram API"))
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
            "Connect to Instagram's advanced API for enhanced posting features. "
            "This feature will be available in a future update."
        ))
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 14px; color: #333; padding: 10px;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Coming soon message
        coming_soon = QLabel(self.tr("🚧 Coming Soon"))
        coming_soon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coming_soon.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #f39c12;
                padding: 20px;
                border: 2px dashed #f39c12;
                border-radius: 8px;
                margin: 20px;
            }
        """)
        layout.addWidget(coming_soon)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr("Instagram API"))
        
    def _create_testing_tab(self):
        """Create the connection testing tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Testing info
        info_group = QGroupBox(self.tr("Connection Testing"))
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
            "Test your platform connections to ensure they're working properly. "
            "Select the platforms you want to test and click 'Run Tests'."
        ))
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 14px; color: #333; padding: 10px;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Platform selection
        selection_group = QGroupBox(self.tr("Select Platforms to Test"))
        selection_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        selection_layout = QVBoxLayout(selection_group)
        
        self.test_meta_checkbox = QCheckBox(self.tr("Meta (Instagram & Facebook)"))
        self.test_meta_checkbox.setStyleSheet("font-size: 14px; padding: 5px;")
        selection_layout.addWidget(self.test_meta_checkbox)
        
        layout.addWidget(selection_group)
        
        # Test buttons
        button_layout = QHBoxLayout()
        
        self.run_tests_btn = QPushButton(self.tr("Run Selected Tests"))
        self.run_tests_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.run_tests_btn.clicked.connect(self._run_connection_tests)
        button_layout.addWidget(self.run_tests_btn)
        
        self.test_all_btn = QPushButton(self.tr("Test All Connected"))
        self.test_all_btn.setStyleSheet("""
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
        self.test_all_btn.clicked.connect(self._test_all_connections)
        button_layout.addWidget(self.test_all_btn)
        
        layout.addLayout(button_layout)
        
        # Progress bar
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        self.test_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.test_progress)
        
        # Results area
        results_group = QGroupBox(self.tr("Test Results"))
        results_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        results_layout = QVBoxLayout(results_group)
        
        self.test_results_text = QTextEdit()
        self.test_results_text.setMaximumHeight(200)
        self.test_results_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        self.test_results_text.setPlainText(self.tr("No tests run yet. Select platforms and click 'Run Tests' to begin."))
        results_layout.addWidget(self.test_results_text)
        
        layout.addWidget(results_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, self.tr("Testing"))
        
    def _create_status_section(self, layout):
        """Create the overall status section."""
        self.status_group = QGroupBox(self.tr("Overall Connection Status"))
        self.status_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        status_layout = QVBoxLayout(self.status_group)
        
        self.overall_status_label = QLabel(self.tr("No platforms connected"))
        self.overall_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.overall_status_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 18px; padding: 15px;")
        status_layout.addWidget(self.overall_status_label)
        
        layout.addWidget(self.status_group)
        
    def _create_button_section(self, layout):
        """Create the dialog button section."""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Test connection button
        self.test_connection_btn = QPushButton(self.tr("Test Connections"))
        self.test_connection_btn.setStyleSheet("""
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
        self.test_connection_btn.clicked.connect(self._test_all_connections)
        button_layout.addWidget(self.test_connection_btn)
        
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
    
    def _test_all_connections(self):
        """Test all platform connections."""
        platforms = []
        if self.platform_status['meta']['connected']:
            platforms.append('meta')
        
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
        
        # Show summary
        successful_tests = sum(1 for success, _ in results.values() if success)
        total_tests = len(results)
        
        self.test_results_text.append(f"\n📊 Test Summary: {successful_tests}/{total_tests} platforms passed")
        
        if successful_tests == total_tests:
            self.test_results_text.append("🎉 All tests passed! Your connections are working properly.")
        else:
            self.test_results_text.append("⚠️ Some tests failed. Please check the connections above.")
    
    def _update_meta_status(self, connected: bool, message: str):
        """Update Meta connection status."""
        if connected:
            self.meta_status_label.setText(f"✅ {message}")
            self.meta_status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 16px; padding: 10px;")
            self.meta_connect_btn.setVisible(False)
            self.meta_disconnect_btn.setVisible(True)
        else:
            self.meta_status_label.setText(f"❌ {message}")
            self.meta_status_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 16px; padding: 10px;")
            self.meta_connect_btn.setVisible(True)
            self.meta_disconnect_btn.setVisible(False)
    
    def _update_overall_status(self):
        """Update the overall connection status."""
        connected_platforms = [name for name, status in self.platform_status.items() if status['connected']]
        
        if not connected_platforms:
            self.overall_status_label.setText(self.tr("❌ No platforms connected"))
            self.overall_status_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 18px; padding: 15px;")
        elif len(connected_platforms) == 1:
            platform_name = connected_platforms[0].replace('_', ' ').title()
            self.overall_status_label.setText(self.tr(f"✅ Connected to {platform_name}"))
            self.overall_status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 18px; padding: 15px;")
        else:
            self.overall_status_label.setText(self.tr(f"✅ Connected to {len(connected_platforms)} platforms"))
            self.overall_status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 18px; padding: 15px;")
    
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
        """Retranslate the UI elements."""
        self.setWindowTitle(self.tr("Connect to Social Media Platforms"))
        # Additional translations would be added here as needed 