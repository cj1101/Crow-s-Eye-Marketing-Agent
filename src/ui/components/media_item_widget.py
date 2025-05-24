"""
Media Item Widget for displaying individual media items in the gallery.
"""
import os
import logging
from PySide6.QtWidgets import QVBoxLayout, QLabel, QCheckBox
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QCursor

from ...handlers.media_handler import MediaHandler, pil_to_qpixmap
from ..base_widget import BaseWidget


class MediaItemWidget(BaseWidget):
    """Custom widget for displaying a media item in the gallery."""
    
    selected = Signal(str)  # Media path
    
    def __init__(self, media_path: str, media_handler: MediaHandler, parent=None):
        super().__init__(parent)
        self.media_path = media_path
        self.media_handler = media_handler
        self.is_selected = False
        
        self._setup_ui()
        self.retranslateUi() # Initial translation
    
    def _setup_ui(self):
        """Set up the UI for the media item widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Create thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(160, 160)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 4px;
            }
        """)
        
        # Try to load thumbnail
        try:
            img = self.media_handler.load_image(self.media_path)
            if img:
                # Resize for thumbnail
                img.thumbnail((160, 160))
                pixmap = pil_to_qpixmap(img)
                if not pixmap.isNull():
                    self.thumbnail_label.setPixmap(pixmap)
                    self.thumbnail_label.setScaledContents(True)
            else:
                # Fallback text
                ext = os.path.splitext(self.media_path)[1].lower()
                if ext in ['.mp4', '.mov', '.avi', '.wmv']:
                    self.thumbnail_label.setText(self.tr("Video"))
                else:
                    self.thumbnail_label.setText(self.tr("Media"))
        except Exception as e:
            logging.exception(f"Error loading thumbnail: {e}")
            self.thumbnail_label.setText(self.tr("Error"))
        
        layout.addWidget(self.thumbnail_label)
        
        # File name label
        filename = os.path.basename(self.media_path)
        name_label = QLabel(filename)
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 11px; color: #DDDDDD;")
        layout.addWidget(name_label)
        
        # Selection indicator
        self.select_checkbox = QCheckBox() # Text set in retranslateUi
        self.select_checkbox.setChecked(self.is_selected)
        self.select_checkbox.stateChanged.connect(self._on_select_changed)
        self.select_checkbox.setStyleSheet("color: #DDDDDD;")
        layout.addWidget(self.select_checkbox)
        
        # Style for selected state
        self.setStyleSheet("""
            MediaItemWidget[selected="true"] {
                background-color: #4a148c;
                border: 2px solid #9c27b0;
                border-radius: 6px;
            }
            MediaItemWidget[selected="false"] {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 6px;
            }
        """)
        self.setProperty("selected", self.is_selected)
        
        # Make widget clickable
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def _on_select_changed(self, state):
        """Handle selection state change."""
        self.is_selected = bool(state)
        self.setProperty("selected", self.is_selected)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        
        if self.is_selected:
            self.selected.emit(self.media_path)
    
    def mousePressEvent(self, event):
        """Handle mouse press event for selection."""
        self.select_checkbox.setChecked(not self.select_checkbox.isChecked())
        super().mousePressEvent(event)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.select_checkbox.setText(self.tr("Select"))
        current_thumb_text = self.thumbnail_label.text()
        # Check against original English text to avoid re-translating already translated text
        if hasattr(self, '_original_thumb_text_map') and current_thumb_text in self._original_thumb_text_map:
             self.thumbnail_label.setText(self.tr(self._original_thumb_text_map[current_thumb_text]))
        elif current_thumb_text == "Video": # Fallback for initial setup or if map not present
            self.thumbnail_label.setText(self.tr("Video"))
            if not hasattr(self, '_original_thumb_text_map'): self._original_thumb_text_map = {}
            self._original_thumb_text_map[self.thumbnail_label.text()] = "Video"
        elif current_thumb_text == "Media":
            self.thumbnail_label.setText(self.tr("Media"))
            if not hasattr(self, '_original_thumb_text_map'): self._original_thumb_text_map = {}
            self._original_thumb_text_map[self.thumbnail_label.text()] = "Media"
        elif current_thumb_text == "Error":
            self.thumbnail_label.setText(self.tr("Error"))
            if not hasattr(self, '_original_thumb_text_map'): self._original_thumb_text_map = {}
            self._original_thumb_text_map[self.thumbnail_label.text()] = "Error" 