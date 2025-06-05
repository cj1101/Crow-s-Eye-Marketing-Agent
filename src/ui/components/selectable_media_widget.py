"""
Selectable Media Widget for gallery creation in the library tabs.
"""

import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

try:
    from ...utils.video_thumbnail_generator import VideoThumbnailGenerator
    VIDEO_THUMBNAILS_AVAILABLE = True
except ImportError:
    VIDEO_THUMBNAILS_AVAILABLE = False

class SelectableMediaWidget(QWidget):
    """Widget for displaying media thumbnails with selection checkbox."""
    
    # Signals
    selection_changed = Signal(str, bool)  # media_path, is_selected
    media_clicked = Signal(str)  # media_path for options dialog
    
    def __init__(self, media_path: str, media_type: str = "image", parent=None):
        super().__init__(parent)
        self.media_path = media_path
        self.media_type = media_type
        self.is_selected = False
        
        # Initialize video thumbnail generator if available
        self.video_generator = VideoThumbnailGenerator() if VIDEO_THUMBNAILS_AVAILABLE else None
        
        self._setup_ui()
        self._load_thumbnail()
    
    def _setup_ui(self):
        """Setup the widget UI."""
        self.setFixedSize(140, 160)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Checkbox at the top
        checkbox_layout = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: white;
                border: 2px solid #ccc;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #28a745;
                border: 2px solid #28a745;
                border-radius: 3px;
            }
        """)
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        checkbox_layout.addWidget(self.checkbox)
        checkbox_layout.addStretch()
        layout.addLayout(checkbox_layout)
        
        # Thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setFixedSize(120, 90)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                border-radius: 6px;
                background-color: #f8f9fa;
            }
        """)
        layout.addWidget(self.thumbnail_label)
        
        # Filename
        filename = os.path.basename(self.media_path)
        if len(filename) > 18:
            filename = filename[:15] + "..."
        
        self.name_label = QLabel(filename)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 11px;
                font-weight: 500;
                padding: 2px;
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 3px;
            }
        """)
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)
        
        self._update_style()
    
    def _load_thumbnail(self):
        """Load and display the thumbnail."""
        try:
            if self.media_type == "image":
                pixmap = QPixmap(self.media_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        116, 86, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.thumbnail_label.setPixmap(scaled_pixmap)
                else:
                    self.thumbnail_label.setText("📷\nNo Preview")
            else:  # video
                video_thumbnail_loaded = False
                
                if self.video_generator and VIDEO_THUMBNAILS_AVAILABLE:
                    try:
                        thumbnail_pixmap = self.video_generator.generate_thumbnail(
                            self.media_path, 
                            timestamp=1.0, 
                            size=(116, 86)
                        )
                        if thumbnail_pixmap and not thumbnail_pixmap.isNull():
                            self.thumbnail_label.setPixmap(thumbnail_pixmap)
                            video_thumbnail_loaded = True
                    except Exception:
                        pass
                
                if not video_thumbnail_loaded:
                    self.thumbnail_label.setText("🎥\nVIDEO")
                    self.thumbnail_label.setStyleSheet("""
                        QLabel {
                            border: 2px solid #ddd;
                            border-radius: 6px;
                            background-color: #f8f9fa;
                            color: #666;
                            font-size: 12px;
                            font-weight: bold;
                        }
                    """)
        except Exception:
            self.thumbnail_label.setText("❌\nError")
    
    def _update_style(self):
        """Update widget style based on selection state."""
        if self.is_selected:
            self.setStyleSheet("""
                SelectableMediaWidget {
                    background-color: #e3f2fd;
                    border: 2px solid #2196f3;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                SelectableMediaWidget {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                }
                SelectableMediaWidget:hover {
                    background-color: #f5f5f5;
                    border: 1px solid #ccc;
                }
            """)
    
    def _on_checkbox_changed(self, state):
        """Handle checkbox state change."""
        self.is_selected = state == Qt.CheckState.Checked.value
        self._update_style()
        self.selection_changed.emit(self.media_path, self.is_selected)
    
    def set_selected(self, selected: bool):
        """Set selection state programmatically."""
        self.checkbox.setChecked(selected)
    
    def mousePressEvent(self, event):
        """Handle mouse clicks."""
        if event.button() == Qt.MouseButton.RightButton:
            # Right click for options menu
            self.media_clicked.emit(self.media_path)
        elif event.button() == Qt.MouseButton.LeftButton:
            # Check if click is on checkbox area
            checkbox_rect = self.checkbox.geometry()
            click_pos = event.pos()
            
            if checkbox_rect.contains(click_pos):
                # Let the checkbox handle the click naturally
                pass
            else:
                # Left click elsewhere opens media options dialog (not preview)
                # Unedited media needs to be edited before posting
                self.media_clicked.emit(self.media_path)
        
        super().mousePressEvent(event) 