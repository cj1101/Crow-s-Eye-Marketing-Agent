"""
Create Post Dialog - Initial modal for choosing post creation method.
Provides options for Upload Photo, Upload Video, Create Media, or Text Post.
"""
import os
import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QFrame, QWidget, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap

from ..base_dialog import BaseDialog

class CreatePostOptionTile(QFrame):
    """Individual option tile for post creation methods."""
    
    clicked = Signal(str)  # Emits the option type when clicked
    
    def __init__(self, title: str, description: str, icon: str, option_type: str):
        super().__init__()
        self.option_type = option_type
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
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)
        
        # Description
        self.desc_label = QLabel(description)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(self.desc_label)
        
        # Styling
        self.setStyleSheet("""
            CreatePostOptionTile {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 12px;
            }
            CreatePostOptionTile:hover {
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
        
    def update_text(self, title: str, description: str):
        """Update the tile's title and description text."""
        self.title_label.setText(title)
        self.desc_label.setText(description)
    
    def mousePressEvent(self, event):
        """Handle mouse press to emit clicked signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.option_type)
        super().mousePressEvent(event)

class CreatePostDialog(BaseDialog):
    """Dialog for choosing how to create a post."""
    
    # Signals for different creation methods
    upload_photo_requested = Signal(str)  # file_path
    upload_video_requested = Signal(str)  # file_path
    create_media_requested = Signal(str)  # media_type ('photo' or 'video')
    create_gallery_requested = Signal()
    text_post_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.setWindowTitle("Create a Post")
        self.setModal(True)
        self.setFixedSize(700, 550)
        
        self._setup_ui()
        self._connect_signals()
        self.retranslateUi()  # Apply initial translations
        
        self.logger.info("Create Post dialog initialized")
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        self._create_header(layout)
        
        # Options grid
        self._create_options_grid(layout)
        
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
        self.title_label = QLabel()  # Text set in retranslateUi
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #000000; margin-bottom: 10px;")
        main_layout.addWidget(self.title_label)
        
        # Subtitle
        self.subtitle_label = QLabel()  # Text set in retranslateUi
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet("color: #666666; font-size: 14px; margin-bottom: 20px;")
        main_layout.addWidget(self.subtitle_label)
    
    def _create_options_grid(self, main_layout: QVBoxLayout):
        """Create the options grid."""
        # Container for options
        options_container = QWidget()
        options_layout = QGridLayout(options_container)
        options_layout.setSpacing(15)
        options_layout.setContentsMargins(0, 0, 0, 0)
        
        # Define options with translation keys
        self.options_data = [
            {
                'title_key': 'Upload Photo',
                'description_key': 'Upload an existing photo from your device or library',
                'icon': '📷',
                'option_type': 'upload_photo'
            },
            {
                'title_key': 'Upload Video',
                'description_key': 'Upload an existing video with optional processing',
                'icon': '🎥',
                'option_type': 'upload_video'
            },
            {
                'title_key': 'Create Media',
                'description_key': 'Generate new content using AI (Imagen/Veo)',
                'icon': '✨',
                'option_type': 'create_media'
            },
            {
                'title_key': 'Create Gallery',
                'description_key': 'Create a gallery from existing photos and videos',
                'icon': '🖼️',
                'option_type': 'create_gallery'
            },
            {
                'title_key': 'Text Post',
                'description_key': 'Create a text-only post with AI assistance',
                'icon': '📝',
                'option_type': 'text_post'
            }
        ]
        
        # Store option tiles for translation updates
        self.option_tiles = []
        
        # Create option tiles in a grid (3 columns for 5 options)
        for i, option_data in enumerate(self.options_data):
            tile = CreatePostOptionTile(
                title=self.tr(option_data['title_key']),
                description=self.tr(option_data['description_key']),
                icon=option_data['icon'],
                option_type=option_data['option_type']
            )
            tile.clicked.connect(self._on_option_selected)
            self.option_tiles.append(tile)
            
            row = i // 3
            col = i % 3
            options_layout.addWidget(tile, row, col)
        
        # Center the grid
        options_layout.setRowStretch(options_layout.rowCount(), 1)
        options_layout.setColumnStretch(2, 1)
        
        main_layout.addWidget(options_container, 1)  # Give it stretch factor
    
    def _create_cancel_button(self, main_layout: QVBoxLayout):
        """Create the cancel button."""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton()  # Text set in retranslateUi
        self.cancel_button.setStyleSheet("""
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
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """Connect internal signals."""
        pass
    
    def _on_option_selected(self, option_type: str):
        """Handle option selection."""
        self.logger.info(f"Option selected: {option_type}")
        
        if option_type == 'upload_photo':
            self._handle_upload_photo()
        elif option_type == 'upload_video':
            self._handle_upload_video()
        elif option_type == 'create_media':
            self._handle_create_media()
        elif option_type == 'create_gallery':
            self._handle_create_gallery()
        elif option_type == 'text_post':
            self._handle_text_post()
    
    def _handle_upload_photo(self):
        """Handle photo upload option."""
        # Show file dialog for photo selection
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Photo",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*)"
        )
        
        if file_path:
            self.logger.info(f"Photo selected: {file_path}")
            self.upload_photo_requested.emit(file_path)
            self.accept()
        else:
            self.logger.info("Photo upload cancelled")
    
    def _handle_upload_video(self):
        """Handle video upload option."""
        # Show file dialog for video selection
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;All Files (*)"
        )
        
        if file_path:
            self.logger.info(f"Video selected: {file_path}")
            self.upload_video_requested.emit(file_path)
            self.accept()
        else:
            self.logger.info("Video upload cancelled")
    
    def _handle_create_media(self):
        """Handle AI media creation option."""
        # Show dialog to choose between photo and video generation
        from .create_media_dialog import CreateMediaDialog
        
        create_dialog = CreateMediaDialog(parent=self)
        if create_dialog.exec() == QDialog.DialogCode.Accepted:
            media_type = create_dialog.get_selected_media_type()
            self.logger.info(f"AI media creation requested: {media_type}")
            self.create_media_requested.emit(media_type)
            self.accept()
    
    def _handle_create_gallery(self):
        """Handle create gallery option."""
        self.logger.info("Create gallery requested")
        self.create_gallery_requested.emit()
        self.accept()
    
    def _handle_text_post(self):
        """Handle text post option."""
        self.logger.info("Text post creation requested")
        self.text_post_requested.emit()
        self.accept()
    
    def retranslateUi(self):
        """Update UI text for internationalization."""
        self.setWindowTitle(self.tr("Create a Post"))
        
        if hasattr(self, 'title_label'):
            self.title_label.setText(self.tr("Create a Post"))
        
        if hasattr(self, 'subtitle_label'):
            self.subtitle_label.setText(self.tr("Choose how you'd like to create your post"))
        
        if hasattr(self, 'cancel_button'):
            self.cancel_button.setText(self.tr("Cancel"))
        
        # Update option tiles
        if hasattr(self, 'option_tiles') and hasattr(self, 'options_data'):
            for i, tile in enumerate(self.option_tiles):
                if i < len(self.options_data):
                    option_data = self.options_data[i]
                    tile.update_text(
                        self.tr(option_data['title_key']),
                        self.tr(option_data['description_key'])
                    ) 