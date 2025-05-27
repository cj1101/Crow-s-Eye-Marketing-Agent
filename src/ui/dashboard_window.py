"""
Dashboard window - Main entry point for the Crow's Eye Marketing Agent.
Provides a clean, tile-based interface for accessing all features.
"""
import os
import logging
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QFont, QPixmap, QIcon

from .base_window import BaseMainWindow
from ..models.app_state import AppState
from ..handlers.media_handler import MediaHandler
from ..handlers.library_handler import LibraryManager

class DashboardTile(QFrame):
    """Individual tile widget for dashboard features."""
    
    clicked = Signal(str)  # Emits the feature name when clicked
    
    def __init__(self, title: str, description: str, icon_path: str = None, feature_name: str = None):
        super().__init__()
        self.feature_name = feature_name or title.lower().replace(' ', '_')
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Icon
        if icon_path and os.path.exists(icon_path):
            icon_label = QLabel()
            pixmap = QPixmap(icon_path).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)
        else:
            # Fallback to emoji/text icon
            icon_label = QLabel(self._get_default_icon(self.feature_name))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("font-size: 48px;")
            layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(desc_label)
        
        # Styling
        self.setStyleSheet("""
            DashboardTile {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 12px;
            }
            DashboardTile:hover {
                background-color: #e9ecef;
                border-color: #007bff;
            }
            QLabel {
                color: #000000;
                background: transparent;
                border: none;
            }
        """)
        
        # Set fixed size for consistent grid
        self.setFixedSize(250, 200)
        
    def _get_default_icon(self, feature_name: str) -> str:
        """Get default emoji icon for feature."""
        icons = {
            'create_post': '✏️',
            'library': '📚',
            'campaign_manager': '📅',
            'customer_handler': '💬',
            'data': '📊',
            'tools': '🔧',
            'presets': '⚙️'
        }
        return icons.get(feature_name, '📋')
    
    def mousePressEvent(self, event):
        """Handle mouse press to emit clicked signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.feature_name)
        super().mousePressEvent(event)

class DashboardWindow(BaseMainWindow):
    """Main dashboard window with feature tiles."""
    
    # Signals for navigation
    create_post_requested = Signal()
    library_requested = Signal()
    campaign_manager_requested = Signal()
    customer_handler_requested = Signal()
    data_requested = Signal()
    tools_requested = Signal()
    presets_requested = Signal()
    
    def __init__(self, app_state: AppState, media_handler: MediaHandler, 
                 library_manager: LibraryManager, parent=None):
        super().__init__(parent)
        
        self.app_state = app_state
        self.media_handler = media_handler
        self.library_manager = library_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.setWindowTitle("Crow's Eye Marketing Agent")
        self.setMinimumSize(1200, 800)
        
        self._setup_ui()
        self._connect_signals()
        
        self.logger.info("Dashboard window initialized")
    
    def _setup_ui(self):
        """Set up the dashboard UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)
        
        # Header
        self._create_header(main_layout)
        
        # API Key Status Widget
        from .widgets.api_key_status_widget import APIKeyStatusWidget
        self.api_status_widget = APIKeyStatusWidget()
        self.api_status_widget.learn_more_requested.connect(self._show_api_key_info)
        main_layout.addWidget(self.api_status_widget)
        
        # Dashboard tiles
        self._create_dashboard_tiles(main_layout)
        
        # Presets panel (always visible)
        self._create_presets_panel(main_layout)
        
        # Apply high contrast styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QLabel {
                color: #000000;
            }
        """)
    
    def _create_header(self, main_layout: QVBoxLayout):
        """Create the header section."""
        header_layout = QHBoxLayout()
        
        # App title
        self.title_label = QLabel(self.tr("Crow's Eye Marketing Agent"))
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #000000; margin-bottom: 10px;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Home button (always visible)
        self.home_button = QPushButton(self.tr("🏠 Home"))
        self.home_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.home_button.clicked.connect(self._on_home_clicked)
        header_layout.addWidget(self.home_button)
        
        main_layout.addLayout(header_layout)
        
        # Subtitle
        self.subtitle_label = QLabel(self.tr("Choose an action to get started"))
        self.subtitle_label.setStyleSheet("color: #666666; font-size: 16px; margin-bottom: 20px;")
        main_layout.addWidget(self.subtitle_label)
    
    def _create_dashboard_tiles(self, main_layout: QVBoxLayout):
        """Create the main dashboard tiles."""
        # Scroll area for tiles
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        # Container for tiles
        tiles_container = QWidget()
        tiles_layout = QGridLayout(tiles_container)
        tiles_layout.setSpacing(20)
        tiles_layout.setContentsMargins(0, 0, 0, 0)
        
        # Define tiles
        tiles_data = [
            {
                'title': 'Create a Post',
                'description': 'Primary entry for content creation with AI assistance',
                'feature_name': 'create_post'
            },
            {
                'title': 'Library',
                'description': 'Manage raw media & finished posts',
                'feature_name': 'library'
            },
            {
                'title': 'Campaign Manager',
                'description': 'Handle campaigns & scheduling queues',
                'feature_name': 'campaign_manager'
            },
            {
                'title': 'Customer Handler',
                'description': 'Knowledge-base responder system',
                'feature_name': 'customer_handler'
            },
            {
                'title': 'Data',
                'description': 'Analytics & compliance monitoring',
                'feature_name': 'data'
            },
            {
                'title': 'Tools',
                'description': 'Access video tools, analytics, and utilities',
                'feature_name': 'tools'
            },
            {
                'title': 'Presets',
                'description': 'Manage saved presets and campaign settings',
                'feature_name': 'presets'
            }
        ]
        
        # Create tiles in a 3x2 grid
        for i, tile_data in enumerate(tiles_data):
            tile = DashboardTile(
                title=tile_data['title'],
                description=tile_data['description'],
                feature_name=tile_data['feature_name']
            )
            tile.clicked.connect(self._on_tile_clicked)
            
            row = i // 3
            col = i % 3
            tiles_layout.addWidget(tile, row, col)
        
        # Add stretch to center tiles
        tiles_layout.setRowStretch(tiles_layout.rowCount(), 1)
        tiles_layout.setColumnStretch(3, 1)
        
        scroll_area.setWidget(tiles_container)
        main_layout.addWidget(scroll_area, 1)  # Give it stretch factor
    
    def _create_presets_panel(self, main_layout: QVBoxLayout):
        """Create the presets panel."""
        presets_frame = QFrame()
        presets_frame.setFrameStyle(QFrame.Shape.Box)
        presets_frame.setLineWidth(1)
        presets_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        presets_layout = QVBoxLayout(presets_frame)
        presets_layout.setContentsMargins(15, 15, 15, 15)
        
        # Presets title
        self.presets_title = QLabel(self.tr("Quick Access Presets"))
        self.presets_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #000000; margin-bottom: 10px;")
        presets_layout.addWidget(self.presets_title)
        
        # Presets info
        self.presets_info = QLabel(self.tr("Saved presets and campaign-linked presets will appear here"))
        self.presets_info.setStyleSheet("color: #666666; font-size: 12px;")
        presets_layout.addWidget(self.presets_info)
        
        # Set fixed height for presets panel
        presets_frame.setFixedHeight(100)
        main_layout.addWidget(presets_frame)
    
    def _connect_signals(self):
        """Connect internal signals."""
        pass
    
    def _on_tile_clicked(self, feature_name: str):
        """Handle tile clicks."""
        self.logger.info(f"Tile clicked: {feature_name}")
        
        # Emit appropriate signal based on feature
        if feature_name == 'create_post':
            self.create_post_requested.emit()
        elif feature_name == 'library':
            self.library_requested.emit()
        elif feature_name == 'campaign_manager':
            self.campaign_manager_requested.emit()
        elif feature_name == 'customer_handler':
            self.customer_handler_requested.emit()
        elif feature_name == 'data':
            self.data_requested.emit()
        elif feature_name == 'tools':
            self.tools_requested.emit()
        elif feature_name == 'presets':
            self.presets_requested.emit()
    
    def _on_home_clicked(self):
        """Handle home button click - should return to dashboard."""
        self.logger.info("Home button clicked")
    
    def _show_api_key_info(self):
        """Show information about API key usage."""
        from PySide6.QtWidgets import QMessageBox
        from ...config.shared_api_keys import is_using_shared_key
        
        using_shared_gemini = is_using_shared_key("gemini")
        using_shared_google = is_using_shared_key("google")
        
        if using_shared_gemini and using_shared_google:
            message = """🔑 <b>Using Shared API Keys</b><br><br>
            
<b>What this means:</b><br>
• You're using the application's built-in API keys<br>
• No setup required - everything works out of the box!<br>
• Perfect for getting started and testing features<br><br>

<b>Services included:</b><br>
• ✨ Gemini AI for caption generation and image editing<br>
• 🎬 Veo for video generation<br>
• 🖼️ Imagen 3 for AI image enhancement<br><br>

<b>Want to use your own API keys?</b><br>
Set these environment variables:<br>
• GEMINI_API_KEY=your_key_here<br>
• GOOGLE_API_KEY=your_key_here<br><br>

The app will automatically use your keys if provided!"""
        else:
            message = """🔐 <b>Using Personal API Keys</b><br><br>
            
<b>What this means:</b><br>
• You're using your own Google API keys<br>
• Full control over usage and billing<br>
• Higher rate limits available<br><br>

<b>Current setup:</b><br>"""
            if not using_shared_gemini:
                message += "• ✅ Personal Gemini API key<br>"
            else:
                message += "• 🔑 Shared Gemini API key<br>"
                
            if not using_shared_google:
                message += "• ✅ Personal Google API key<br>"
            else:
                message += "• 🔑 Shared Google API key<br>"
                
            message += "<br>To switch back to shared keys, remove your environment variables."
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("API Key Information")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()
        # This window IS the home, so just ensure we're showing the main view
        self.show()
        self.raise_()
        self.activateWindow()
    
    def retranslateUi(self):
        """Update UI text for internationalization."""
        self.setWindowTitle(self.tr("Crow's Eye Marketing Agent"))
        self.title_label.setText(self.tr("Crow's Eye Marketing Agent"))
        self.home_button.setText(self.tr("🏠 Home"))
        self.subtitle_label.setText(self.tr("Choose an action to get started"))
        self.presets_title.setText(self.tr("Quick Access Presets"))
        self.presets_info.setText(self.tr("Saved presets and campaign-linked presets will appear here")) 