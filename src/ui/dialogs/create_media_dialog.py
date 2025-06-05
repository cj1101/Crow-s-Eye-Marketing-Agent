"""
Create Media Dialog - Choose between AI photo (Imagen) or video (Veo) generation.
"""
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..base_dialog import BaseDialog

class MediaTypeOptionTile(QFrame):
    """Individual option tile for media type selection."""
    
    clicked = Signal(str)  # Emits the media type when clicked
    
    def __init__(self, title: str, description: str, icon: str, media_type: str):
        super().__init__()
        self.media_type = media_type
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(desc_label)
        
        # Styling
        self.setStyleSheet("""
            MediaTypeOptionTile {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 12px;
            }
            MediaTypeOptionTile:hover {
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
        self.setFixedSize(200, 180)
        
    def mousePressEvent(self, event):
        """Handle mouse press to emit clicked signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.media_type)
        super().mousePressEvent(event)

class CreateMediaDialog(BaseDialog):
    """Dialog for choosing between photo and video AI generation."""
    
    def __init__(self, media_type: str = None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.selected_media_type = media_type  # Pre-select if provided
        
        self.setWindowTitle("Create Media with AI")
        self.setModal(True)
        self.setFixedSize(500, 400)
        
        self._setup_ui()
        self._connect_signals()
        self.retranslateUi()  # Apply initial translations
        
        self.logger.info("Create Media dialog initialized")
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        self._create_header(layout)
        
        # Options
        self._create_options(layout)
        
        # Cancel button
        self._create_cancel_button(layout)
        
        # Apply high contrast styling
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #000000;
            }
        """)
    
    def _create_header(self, main_layout: QVBoxLayout):
        """Create the header section."""
        # Title
        title_label = QLabel("Create Media with AI")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #000000; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Choose what type of media to generate")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666666; font-size: 14px; margin-bottom: 20px;")
        main_layout.addWidget(subtitle_label)
    
    def _create_options(self, main_layout: QVBoxLayout):
        """Create the media type options."""
        # Container for options
        options_container = QWidget()
        options_layout = QHBoxLayout(options_container)
        options_layout.setSpacing(20)
        options_layout.setContentsMargins(0, 0, 0, 0)
        
        # Photo option
        photo_tile = MediaTypeOptionTile(
            title="Generate Photo",
            description="Create images using Imagen 3-5",
            icon="🖼️",
            media_type="photo"
        )
        photo_tile.clicked.connect(self._on_media_type_selected)
        options_layout.addWidget(photo_tile)
        
        # Video option
        video_tile = MediaTypeOptionTile(
            title="Generate Video",
            description="Create videos using Veo 3",
            icon="🎬",
            media_type="video"
        )
        video_tile.clicked.connect(self._on_media_type_selected)
        options_layout.addWidget(video_tile)
        
        # Center the options
        options_layout.addStretch()
        
        main_layout.addWidget(options_container, 1)  # Give it stretch factor
    
    def _create_cancel_button(self, main_layout: QVBoxLayout):
        """Create the cancel button."""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """Connect internal signals."""
        pass
    
    def _on_media_type_selected(self, media_type: str):
        """Handle media type selection."""
        self.logger.info(f"Media type selected: {media_type}")
        self.selected_media_type = media_type
        self.accept()
    
    def get_selected_media_type(self) -> Optional[str]:
        """Get the selected media type."""
        return self.selected_media_type
    
    def retranslateUi(self):
        """Update UI text for internationalization."""
        self.setWindowTitle(self.tr("Create Media with AI"))
        # Note: This dialog uses hardcoded tiles, so full translation would require
        # storing references to the tiles and updating them dynamically.
        # For now, the window title is translated. 