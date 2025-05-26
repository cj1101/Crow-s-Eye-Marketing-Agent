"""
Gallery Preview Widget for displaying images within gallery detail dialogs.
"""
import os
import logging
from PySide6.QtWidgets import QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal, QEvent

from ...features.media_processing.media_handler import MediaHandler, pil_to_qpixmap
from ..base_widget import BaseWidget


class GalleryImagePreviewWidget(BaseWidget):
    """Widget to display a single image within the GalleryDetailDialog, with an edit button."""
    edit_image_requested = Signal(str) # path

    def __init__(self, media_path: str, media_handler: MediaHandler, parent=None):
        super().__init__(parent)
        self.media_path = media_path
        self.media_handler = media_handler
        self._base_filename_for_translation = os.path.basename(self.media_path) # Store for retranslation
        self._setup_ui()
        self.retranslateUi() # Initial translation

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5,5,5,5)
        
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(180, 180)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("background-color: #2D2D2D; border: 1px solid #444; border-radius: 4px;")

        try:
            img = self.media_handler.load_image(self.media_path)
            if img:
                img.thumbnail((180, 180))
                pixmap = pil_to_qpixmap(img)
                if not pixmap.isNull():
                    self.thumbnail_label.setPixmap(pixmap)
                    self.thumbnail_label.setScaledContents(True)
                else:
                    # Store the key for retranslation, filename itself is not translated
                    self._current_thumb_error_key = "ERROR_LOADING"
                    self.thumbnail_label.setText(self._base_filename_for_translation + self.tr("\n(Error loading)"))
            else:
                self._current_thumb_error_key = "CANNOT_DISPLAY"
                self.thumbnail_label.setText(self._base_filename_for_translation + self.tr("\n(Cannot display)"))
        except Exception as e:
            logging.error(f"Error loading gallery image preview for {self.media_path}: {e}")
            self._current_thumb_error_key = "LOAD_ERROR"
            self.thumbnail_label.setText(self._base_filename_for_translation + self.tr("\n(Load error)"))

        layout.addWidget(self.thumbnail_label)

        self.edit_button = QPushButton() # Text set in retranslateUi
        self.edit_button.clicked.connect(lambda: self.edit_image_requested.emit(self.media_path))
        self.edit_button.setStyleSheet("background-color: #6d28d9; color: white; padding: 5px; border-radius: 3px;")
        layout.addWidget(self.edit_button)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.edit_button.setText(self.tr("Edit"))
        
        # Handle thumbnail text retranslation
        if hasattr(self, '_current_thumb_error_key'):
            if self._current_thumb_error_key == "ERROR_LOADING":
                self.thumbnail_label.setText(self._base_filename_for_translation + self.tr("\n(Error loading)"))
            elif self._current_thumb_error_key == "CANNOT_DISPLAY":
                self.thumbnail_label.setText(self._base_filename_for_translation + self.tr("\n(Cannot display)"))
            elif self._current_thumb_error_key == "LOAD_ERROR":
                self.thumbnail_label.setText(self._base_filename_for_translation + self.tr("\n(Load error)")) 