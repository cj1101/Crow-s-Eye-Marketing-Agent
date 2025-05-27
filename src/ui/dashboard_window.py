"""
Dashboard window - Main entry point for the Crow's Eye Marketing Agent.
Provides a clean, tile-based interface for accessing all features.
"""
import os
import logging
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy, QSpacerItem, QComboBox
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QFont, QPixmap, QIcon

from .base_window import BaseMainWindow
from ..models.app_state import AppState
from ..handlers.media_handler import MediaHandler
from ..handlers.library_handler import LibraryManager
from ..i18n import i18n

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
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)
        
        # Description
        self.desc_label = QLabel(description)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(self.desc_label)
        
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
    
    def update_translations(self, title: str, description: str):
        """Update the tile with new translated text."""
        self.title_label.setText(title)
        self.desc_label.setText(description)
        
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
        
        # Connect to i18n system
        self.i18n = i18n
        self.i18n.language_changed.connect(self.retranslateUi)
        
        self.setWindowTitle("Crow's Eye Marketing Agent")
        self.setMinimumSize(1200, 800)
        
        self._setup_ui()
        self._connect_signals()
        
        self.logger.info("Dashboard window initialized")
    
    def tr(self, text, **kwargs):
        """
        Translate text using the I18N system.
        
        Args:
            text: The text to translate
            **kwargs: Format arguments for string formatting
            
        Returns:
            str: The translated text
        """
        return self.i18n.t(text, **kwargs)
    
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
        
        # Language selection dropdown
        self.language_combo = QComboBox()
        self.language_combo.setObjectName("languageCombo")
        self.language_combo.setFixedWidth(150)
        self.language_combo.setStyleSheet("""
            QComboBox {
                background-color: #e0e0e0;
                color: #000000;
                border: 2px solid #505050;
                padding: 5px;
                font-weight: bold;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """)
        
        # Language data: [("Native Name", "code"), ...]
        self.languages = [
            ("English", "en"),
            ("Español", "es"),
            ("中文", "zh"),
            ("हिन्दी", "hi"),
            ("Français", "fr"),
            ("العربية", "ar"),
            ("Português", "pt"),
            ("Русский", "ru"),
            ("日本語", "ja"),
            ("Deutsch", "de")
        ]
        
        for lang_name, lang_code in self.languages:
            self.language_combo.addItem(lang_name, userData=lang_code)
            
        # Set current language
        current_lang = self.i18n.get_current_language()
        for i, (_, lang_code) in enumerate(self.languages):
            if lang_code == current_lang:
                self.language_combo.setCurrentIndex(i)
                break
                
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        header_layout.addWidget(self.language_combo)
        
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
        
        # Store tiles for translation updates
        self.tiles = []
        
        # Define tiles
        tiles_data = [
            {
                'title': self.tr('Create a Post'),
                'description': self.tr('Primary entry for content creation with AI assistance'),
                'feature_name': 'create_post'
            },
            {
                'title': self.tr('Library'),
                'description': self.tr('Manage raw media & finished posts'),
                'feature_name': 'library'
            },
            {
                'title': self.tr('Campaign Manager'),
                'description': self.tr('Handle campaigns & scheduling queues'),
                'feature_name': 'campaign_manager'
            },
            {
                'title': self.tr('Customer Handler'),
                'description': self.tr('Knowledge-base responder system'),
                'feature_name': 'customer_handler'
            },
            {
                'title': self.tr('Data'),
                'description': self.tr('Analytics & compliance monitoring'),
                'feature_name': 'data'
            },
            {
                'title': self.tr('Tools'),
                'description': self.tr('Access video tools, analytics, and utilities'),
                'feature_name': 'tools'
            },
            {
                'title': self.tr('Presets'),
                'description': self.tr('Manage saved presets and campaign settings'),
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
            self.tiles.append(tile)
            
            row = i // 3
            col = i % 3
            tiles_layout.addWidget(tile, row, col)
        
        # Add stretch to center tiles
        tiles_layout.setRowStretch(tiles_layout.rowCount(), 1)
        tiles_layout.setColumnStretch(3, 1)
        
        scroll_area.setWidget(tiles_container)
        main_layout.addWidget(scroll_area, 1)  # Give it stretch factor
    
    def _update_tiles_translations(self):
        """Update all tiles with new translations."""
        # Define the translation keys for each tile
        tiles_translation_data = [
            {
                'title': self.tr('Create a Post'),
                'description': self.tr('Primary entry for content creation with AI assistance'),
                'feature_name': 'create_post'
            },
            {
                'title': self.tr('Library'),
                'description': self.tr('Manage raw media & finished posts'),
                'feature_name': 'library'
            },
            {
                'title': self.tr('Campaign Manager'),
                'description': self.tr('Handle campaigns & scheduling queues'),
                'feature_name': 'campaign_manager'
            },
            {
                'title': self.tr('Customer Handler'),
                'description': self.tr('Knowledge-base responder system'),
                'feature_name': 'customer_handler'
            },
            {
                'title': self.tr('Data'),
                'description': self.tr('Analytics & compliance monitoring'),
                'feature_name': 'data'
            },
            {
                'title': self.tr('Tools'),
                'description': self.tr('Access video tools, analytics, and utilities'),
                'feature_name': 'tools'
            },
            {
                'title': self.tr('Presets'),
                'description': self.tr('Manage saved presets and campaign settings'),
                'feature_name': 'presets'
            }
        ]
        
        # Update each tile with new translations
        for i, tile in enumerate(self.tiles):
            if i < len(tiles_translation_data):
                tile_data = tiles_translation_data[i]
                tile.update_translations(tile_data['title'], tile_data['description'])

    
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
    
    def _on_language_changed(self, index: int):
        """Handle language selection change."""
        if index >= 0:
            selected_lang_code = self.language_combo.itemData(index)
            if selected_lang_code and selected_lang_code != self.i18n.get_current_language():
                self.logger.info(f"Language changed to: {selected_lang_code}")
                self.i18n.switch(selected_lang_code)
    
    def _show_api_key_info(self):
        """Show information about API key usage."""
        from PySide6.QtWidgets import QMessageBox
        from ..config.shared_api_keys import is_using_shared_key
        
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
        
        # Update tiles by recreating them with new translations
        self._update_tiles_translations() 