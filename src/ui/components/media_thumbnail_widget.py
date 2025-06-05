"""
Media Thumbnail Widget for displaying selectable media thumbnails.
"""

import os
import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QContextMenuEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMenu

try:
    from ...utils.video_thumbnail_generator import VideoThumbnailGenerator
    VIDEO_THUMBNAILS_AVAILABLE = True
except ImportError:
    VIDEO_THUMBNAILS_AVAILABLE = False

class MediaThumbnailWidget(QWidget):
    """Widget for displaying media thumbnails with selection capability."""
    
    clicked = Signal(str)  # Emit the media path when clicked
    generate_post_requested = Signal(str)  # Emit when generate post is requested
    
    def __init__(self, media_path: str, media_type: str = "image", show_generate_post: bool = True, parent=None):
        super().__init__(parent)
        self.media_path = media_path
        self.media_type = media_type
        self.show_generate_post = show_generate_post  # Option to show/hide generate post option
        self.is_selected = False
        self.setFixedSize(120, 120)
        
        # Initialize video thumbnail generator if available
        self.video_generator = VideoThumbnailGenerator() if VIDEO_THUMBNAILS_AVAILABLE else None
        
        self._create_ui()
        self._load_thumbnail()
        self._update_style()
    
    def _create_ui(self):
        """Create the thumbnail UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Thumbnail label
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet("border: 1px solid #444; border-radius: 4px;")
        layout.addWidget(self.thumbnail_label)
        
        # Filename label
        filename = os.path.basename(self.media_path)
        if len(filename) > 15:
            filename = filename[:12] + "..."
        
        self.name_label = QLabel(filename)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("color: #CCCCCC; font-size: 10px;")
        layout.addWidget(self.name_label)
    
    def _load_thumbnail(self):
        """Load and display the thumbnail."""
        try:
            if self.media_type == "image":
                pixmap = QPixmap(self.media_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(110, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.thumbnail_label.setPixmap(scaled_pixmap)
                else:
                    self.thumbnail_label.setText("No Preview")
            elif self.media_type == "video":
                # Try to generate a real video thumbnail
                video_thumbnail_loaded = False
                
                if self.video_generator and VIDEO_THUMBNAILS_AVAILABLE:
                    try:
                        # Generate thumbnail at 1 second into the video
                        thumbnail_pixmap = self.video_generator.generate_thumbnail(
                            self.media_path, 
                            timestamp=1.0, 
                            size=(110, 90)
                        )
                        if thumbnail_pixmap and not thumbnail_pixmap.isNull():
                            self.thumbnail_label.setPixmap(thumbnail_pixmap)
                            # Add video play icon overlay (optional enhancement)
                            self.thumbnail_label.setToolTip(f"Video: {os.path.basename(self.media_path)}")
                            video_thumbnail_loaded = True
                    except Exception as e:
                        logging.warning(f"Could not generate video thumbnail for {self.media_path}: {e}")
                
                # Fallback to generic video display
                if not video_thumbnail_loaded:
                    self.thumbnail_label.setText("🎥 VIDEO")
                    self.thumbnail_label.setStyleSheet(
                        "border: 1px solid #444; border-radius: 4px; "
                        "background-color: #2a2a2a; color: #888; font-size: 12px;"
                    )
        except Exception as e:
            logging.warning(f"Could not load thumbnail for {self.media_path}: {e}")
            self.thumbnail_label.setText("No Preview")
    
    def _update_style(self):
        """Update the widget style based on selection state."""
        if self.is_selected:
            self.setStyleSheet("""
                QWidget {
                    background-color: #3b82f6;
                    border: 2px solid #1d4ed8;
                    border-radius: 6px;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #1a1a1a;
                    border: 1px solid #444;
                    border-radius: 6px;
                }
                QWidget:hover {
                    background-color: #2a2a2a;
                    border: 1px solid #666;
                }
            """)
    
    def set_selected(self, selected: bool):
        """Set the selection state."""
        self.is_selected = selected
        self._update_style()
    
    def mousePressEvent(self, event):
        """Handle mouse click."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.media_path)
        super().mousePressEvent(event)
    
    def contextMenuEvent(self, event: QContextMenuEvent):
        """Handle right-click context menu."""
        if not self.show_generate_post:
            return
            
        context_menu = QMenu(self)
        
        # Generate Post action
        generate_action = context_menu.addAction("Generate Post")
        generate_action.setToolTip("Load this media in the main window for post generation")
        
        # Show the menu and handle selection
        action = context_menu.exec_(event.globalPos())
        if action == generate_action:
            self.generate_post_requested.emit(self.media_path) 