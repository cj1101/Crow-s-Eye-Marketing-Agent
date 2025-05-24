"""
Library Window for displaying and managing library items
"""
import os
import logging
import random
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
    QListWidget, QListWidgetItem, QMessageBox, QMenu, QTabWidget,
    QInputDialog, QFileDialog, QScrollArea, QGridLayout, QSplitter, QFrame,
    QCheckBox, QLineEdit, QGroupBox, QTextEdit, QDialog, QApplication, QPushButton
)
from PySide6.QtCore import Qt, Signal, Slot, QEvent
from PySide6.QtGui import QPixmap, QImage, QIcon, QAction, QCursor

from PIL import Image as PILImage

from ..handlers.library_handler import LibraryManager
from ..handlers.crowseye_handler import CrowsEyeHandler
from ..handlers.media_handler import MediaHandler, pil_to_qpixmap
from ..models.app_state import AppState
from .scheduling_dialog import ScheduleDialog
from .post_options_dialog import PostOptionsDialog
from .components.adjustable_button import AdjustableButton
from .base_widget import BaseWidget
from .base_dialog import BaseDialog
from .base_window import BaseMainWindow

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
            self.thumbnail_label.setText(self._base_filename_for_translation + self.tr("\n(Load Error)"))
        
        layout.addWidget(self.thumbnail_label)

        filename_label = QLabel(os.path.basename(self.media_path))
        filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        filename_label.setWordWrap(True)
        layout.addWidget(filename_label)

        self.edit_btn = AdjustableButton(self.tr("Edit Image")) # Changed to AdjustableButton
        self.edit_btn.setStyleSheet("padding: 5px 10px; font-size: 11px;")
        self.edit_btn.clicked.connect(lambda: self.edit_image_requested.emit(self.media_path))
        layout.addWidget(self.edit_btn)
        self.setFixedWidth(200)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.edit_btn.setText(self.tr("Edit Image"))
        
        # Retranslate thumbnail error messages if one was set
        if hasattr(self, '_current_thumb_error_key') and self._current_thumb_error_key:
            if self._current_thumb_error_key == "ERROR_LOADING":
                self.thumbnail_label.setText(self._base_filename_for_translation + self.tr("\n(Error loading)"))
            elif self._current_thumb_error_key == "CANNOT_DISPLAY":
                self.thumbnail_label.setText(self._base_filename_for_translation + self.tr("\n(Cannot display)"))
            elif self._current_thumb_error_key == "LOAD_ERROR":
                self.thumbnail_label.setText(self._base_filename_for_translation + self.tr("\n(Load Error)"))

class GalleryDetailDialog(BaseDialog):
    """Dialog to view and edit details of a saved gallery."""
    gallery_updated = Signal()
    
    def __init__(self, gallery_data: Dict[str, Any], crowseye_handler: CrowsEyeHandler, media_handler: MediaHandler, parent=None):
        super().__init__(parent)
        self.gallery_data = gallery_data
        self.crowseye_handler = crowseye_handler
        self.media_handler = media_handler
        self.edited_gallery_data = gallery_data.copy()
        
        self.setWindowTitle(self.tr("Gallery Details"))
        self.setMinimumWidth(740)
        self.setMinimumHeight(520)
        
        # Create UI elements that will be accessed in retranslateUi
        self.gallery_name_label = QLabel(self.tr("Gallery Name:"))
        self.gallery_name_input = QLineEdit(gallery_data.get("name", self.tr("Untitled Gallery")))
        self.images_label = QLabel(self.tr("Images in Gallery:"))
        self.caption_label = QLabel(self.tr("Gallery Caption:"))
        self.caption_edit = QTextEdit()
        self.save_button = QPushButton(self.tr("Save Changes"))
        self.close_button = QPushButton(self.tr("Close"))
        
        self._setup_ui()
        self.retranslateUi()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Gallery Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(self.gallery_name_label)
        name_layout.addWidget(self.gallery_name_input)
        layout.addLayout(name_layout)

        # Images Scroll Area
        self.images_in_gallery_label = QLabel() # Changed to instance variable for retranslateUi
        layout.addWidget(self.images_in_gallery_label)
        images_scroll_area = QScrollArea()
        images_scroll_area.setWidgetResizable(True)
        images_scroll_content = QWidget()
        self.images_layout = QHBoxLayout(images_scroll_content) # Horizontal layout for images
        self.images_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        images_scroll_content.setLayout(self.images_layout)
        images_scroll_area.setWidget(images_scroll_content)
        layout.addWidget(images_scroll_area, 1) # Stretch factor

        for media_path in self.gallery_data.get("media_paths", []):
            if self.media_handler:
                img_widget = GalleryImagePreviewWidget(media_path, self.media_handler)
                img_widget.edit_image_requested.connect(self._handle_edit_image_request)
                self.images_layout.addWidget(img_widget)
        
        # Add a spacer to push images to the left if there are few
        self.images_layout.addStretch()

        # Caption section
        self.caption_group = QGroupBox() # Made instance variable, title in retranslateUi
        self.caption_group.setStyleSheet("QGroupBox { color: white; font-weight: bold; }")
        caption_layout = QVBoxLayout(self.caption_group)
        
        self.tone_label = QLabel() # Made instance variable
        caption_layout.addWidget(self.tone_label)
        
        self.tone_input = QLineEdit()
        self.tone_input.setPlaceholderText(self.tr("e.g., Professional and concise"))
        self.tone_input.setStyleSheet("background-color: #333333; color: white; padding: 8px; border-radius: 4px;")
        caption_layout.addWidget(self.tone_input)
        
        self.generate_caption_button = AdjustableButton() # Made instance variable, text in retranslateUi
        self.generate_caption_button.setStyleSheet("""
            background-color: #6d28d9; 
            color: white; 
            padding: 8px 16px;
            border-radius: 4px;
        """)
        self.generate_caption_button.clicked.connect(self._on_generate_caption)
        caption_layout.addWidget(self.generate_caption_button)
        
        self.caption_display = QTextEdit()
        self.caption_display.setPlaceholderText(self.tr("Generated caption will appear here..."))
        self.caption_display.setReadOnly(True)
        self.caption_display.setMinimumHeight(100)
        self.caption_display.setStyleSheet("background-color: #333333; color: white; padding: 8px; border-radius: 4px;")
        caption_layout.addWidget(self.caption_display)
        
        layout.addWidget(self.caption_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        self.save_button = AdjustableButton() # Text set in retranslateUi
        self.save_button.clicked.connect(self._save_gallery_changes)
        button_layout.addWidget(self.save_button)

        self.close_button = AdjustableButton() # Text set in retranslateUi
        self.close_button.clicked.connect(self.accept) 
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)

    def _handle_edit_image_request(self, media_path: str):
        self.logger.info(f"Edit request for image: {media_path}")
        try:
            if sys.platform == "win32":
                os.startfile(media_path)
            elif sys.platform == "darwin": # macOS
                subprocess.call(["open", media_path])
            else: # Linux and other Unix-like
                subprocess.call(["xdg-open", media_path])
            QMessageBox.information(self, self.tr("Edit Image"), self.tr("Attempting to open {filename} with the default system application.").format(filename=os.path.basename(media_path)))
        except Exception as e:
            self.logger.error(f"Could not open image {media_path} for editing: {e}")
            QMessageBox.warning(self, self.tr("Edit Image Error"), self.tr("Could not open image for editing: {error}").format(error=str(e)))

    def _save_gallery_changes(self):
        new_name = self.gallery_name_input.text().strip()
        new_caption = self.caption_edit.toPlainText().strip()

        if not new_name:
            QMessageBox.warning(self, self.tr("Validation Error"), self.tr("Gallery name cannot be empty."))
            return

        if self.crowseye_handler and self.gallery_data.get("filename"):
            success = self.crowseye_handler.update_saved_gallery(self.gallery_data.get("filename"), new_name, new_caption)
            if success:
                QMessageBox.information(self, self.tr("Success"), self.tr("Gallery updated successfully."))
                self.gallery_updated.emit()
                self.accept()
            else:
                QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to update gallery. Check logs."))
        else:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Handler not available or gallery ID missing."))

    def _on_generate_caption(self):
        """Handle caption generation."""
        try:
            if not self.crowseye_handler:
                QMessageBox.warning(self, self.tr("Not Available"), self.tr("Crow's Eye handler is not available."))
                return
                
            if not self.gallery_data.get("media_paths", []):
                QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select media items or generate a gallery first."))
                return
            
            tone_prompt = self.tone_input.text().strip()
            
            # Update status
            self.status_label.setText(self.tr("Generating caption..."))
            
            # Generate caption
            caption = self.crowseye_handler.generate_caption(self.gallery_data.get("media_paths", []), tone_prompt)
            
            # Update caption display
            if caption:
                self.caption_display.setText(caption)
                self.status_label.setText(self.tr("Caption generated successfully"))
            else:
                QMessageBox.warning(self, self.tr("Caption Error"), self.tr("Could not generate caption."))
                
        except Exception as e:
            self.logger.exception(f"Error generating caption: {e}")
            QMessageBox.critical(self, self.tr("Caption Error"), self.tr("Could not generate caption: {error}").format(error=str(e)))

    def retranslateUi(self):
        self.gallery_name_label.setText(self.tr("Gallery Name:"))
        self.images_in_gallery_label.setText(self.tr("Images in Gallery:"))
        self.caption_label.setText(self.tr("Gallery Caption:"))
        self.save_button.setText(self.tr("Save Changes"))
        self.close_button.setText(self.tr("Close"))
        self.caption_group.setTitle(self.tr("Caption Generator"))
        self.tone_label.setText(self.tr("Tone Prompt:"))
        self.tone_input.setPlaceholderText(self.tr("e.g., Professional and concise"))
        self.generate_caption_button.setText(self.tr("Generate Caption"))
        self.caption_display.setPlaceholderText(self.tr("Generated caption will appear here..."))

class GalleryItemWidget(BaseWidget):
    """Widget to display a single saved gallery in the Finished Galleries tab."""
    view_edit_requested = Signal(dict) # gallery_data

    def __init__(self, gallery_data: Dict[str, Any], media_handler: MediaHandler, parent=None):
        super().__init__(parent)
        self.gallery_data = gallery_data
        self.media_handler = media_handler
        # Logger for this specific widget if needed for thumbnail errors, otherwise use module logger
        # self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_ui()
        self.retranslateUi() # Initial translation

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10,10,10,10)
        self.setStyleSheet("""
            GalleryItemWidget {
                background-color: #333333;
                border: 1px solid #4A4A4A;
                border-radius: 8px;
                margin-bottom: 10px;
            }
            GalleryItemWidget:hover {
                background-color: #3A3A3A;
            }
            QLabel { color: #F0F0F0; }
            AdjustableButton { padding: 6px 12px; font-size: 12px; }
        """)
        self.setFixedHeight(250) # Fixed height for uniformity

        # Gallery Name
        self.name_label = QLabel() # Made instance variable
        self.name_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        main_layout.addWidget(self.name_label)

        # Thumbnails Preview (Horizontal Scroll)
        thumb_scroll_area = QScrollArea()
        thumb_scroll_area.setFixedHeight(120)
        thumb_scroll_area.setWidgetResizable(True)
        thumb_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        thumb_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        thumb_content_widget = QWidget()
        thumb_layout = QHBoxLayout(thumb_content_widget)
        thumb_layout.setContentsMargins(0,0,0,0)
        thumb_layout.setSpacing(5)

        media_paths = self.gallery_data.get("media_paths", [])
        max_thumbs = 4
        for i, path in enumerate(media_paths[:max_thumbs]):
            if self.media_handler:
                thumb_label = QLabel()
                thumb_label.setFixedSize(100, 100)
                thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                thumb_label.setStyleSheet("background-color: #2D2D2D; border: 1px solid #404040; border-radius: 3px;")
                try:
                    img = self.media_handler.load_image(path)
                    if img:
                        img.thumbnail((100,100))
                        pixmap = pil_to_qpixmap(img)
                        if not pixmap.isNull():
                            thumb_label.setPixmap(pixmap)
                        else:
                             thumb_label.setText(self.tr("Err {index}").format(index=i+1))
                    else:
                        thumb_label.setText(self.tr("N/A {index}").format(index=i+1))
                except Exception as e:
                    # Use a general logger if self.logger is not defined for the class
                    logging.error(f"Error loading thumbnail for {path} in GalleryItemWidget: {e}")
                    thumb_label.setText(self.tr("LoadErr {index}").format(index=i+1))
                thumb_layout.addWidget(thumb_label)
        
        thumb_layout.addStretch() # Push thumbnails to the left
        thumb_content_widget.setLayout(thumb_layout)
        thumb_scroll_area.setWidget(thumb_content_widget)
        main_layout.addWidget(thumb_scroll_area)

        # Caption Preview
        self.caption_preview = QLabel() # Made instance variable
        self.caption_preview.setWordWrap(True)
        self.caption_preview.setMaximumHeight(40) # Limit height for preview
        self.caption_preview.setStyleSheet("font-size: 11px; color: #D0D0D0; margin-top: 5px;")
        main_layout.addWidget(self.caption_preview)
        
        main_layout.addStretch(1)

        # View/Edit Button
        self.view_edit_button = AdjustableButton() # Made instance variable
        self.view_edit_button.clicked.connect(lambda: self.view_edit_requested.emit(self.gallery_data))
        main_layout.addWidget(self.view_edit_button, 0, Qt.AlignmentFlag.AlignRight)

    def _on_view_edit_clicked(self):
        self.view_edit_requested.emit(self.gallery_data)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.name_label.setText(self.gallery_data.get("name", self.tr("Untitled Gallery")))
        
        caption_text = self.gallery_data.get("caption", self.tr("No caption."))
        self.caption_preview.setText(caption_text)
        self.caption_preview.setToolTip(caption_text) # Also translate tooltip

        self.view_edit_button.setText(self.tr("View / Edit Gallery"))
        
        # Thumbnail texts (Err, N/A, LoadErr) are set with tr() during _setup_ui.
        # If _setup_ui is not called on language change, these specific dynamic texts
        # within the scroll area won't update automatically by this retranslateUi.
        # This is a common challenge for items in views; often the view needs to be rebuilt or refreshed.
        # For now, focusing on the main static texts of the widget itself.

class LibraryWindow(BaseMainWindow):
    """Main window for the media library."""
    
    gallery_created = Signal(dict)
    
    def __init__(self, library_manager_instance: LibraryManager, parent=None, scheduler=None):
        """
        Initialize the library window.
        
        Args:
            library_manager_instance: Library manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set up logger
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Store references
        self.library_manager = library_manager_instance
        self.scheduler = scheduler
        
        # Initialize AI handler if not available from library_manager
        if hasattr(self.library_manager, 'ai_handler') and self.library_manager.ai_handler:
            self.ai_handler = self.library_manager.ai_handler
        else:
            from ..handlers.ai_handler import AIHandler
            from ..models.app_state import AppState
            self.ai_handler = AIHandler(AppState())
        
        # Initialize MediaHandler if not available from library_manager
        if hasattr(self.library_manager, 'media_handler') and self.library_manager.media_handler:
            self.media_handler = self.library_manager.media_handler
        else:
            from ..handlers.media_handler import MediaHandler
            from ..models.app_state import AppState
            self.media_handler = MediaHandler(AppState())
            
        # Initialize CrowsEyeHandler if not available from library_manager
        if hasattr(self.library_manager, 'crowseye_handler') and self.library_manager.crowseye_handler:
            self.crowseye_handler = self.library_manager.crowseye_handler
        else:
            from ..handlers.crowseye_handler import CrowsEyeHandler
            from ..models.app_state import AppState
            # Create CrowsEyeHandler with required arguments
            app_state = AppState()
            self.crowseye_handler = CrowsEyeHandler(app_state, self.media_handler, self.library_manager)
        
        # Set window properties
        self.setMinimumSize(1200, 800)
        self.setWindowTitle(self.tr("Media Library"))
        
        # Track selected media
        self.selected_media = []
        
        # Set up UI
        self._create_ui()
        
        # Load library items
        self.refresh_library()
        
        # Force retranslation immediately
        app = QApplication.instance()
        if app:
            current_lang = app.property("current_language") or "en"
            if current_lang != "en":
                self.retranslateUi()
                # Also trigger a LanguageChange event
                event = QEvent(QEvent.Type.LanguageChange)
                app.sendEvent(self, event)

    def _create_ui(self):
        """Create the UI components"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Header section with improved styling
        header_layout = QHBoxLayout()
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #3A3A3A; color: white; padding: 10px;")
        header_widget.setFixedHeight(60)
        
        # Title
        self.title_label = QLabel() # Made instance variable
        self.title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Buttons with improved styling
        button_style = """
            AdjustableButton {
                background-color: #4A4A4A;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 14px;
            }
            AdjustableButton:hover {
                background-color: #5A5A5A;
            }
            AdjustableButton:pressed {
                background-color: #666666;
            }
        """
        
        self.refresh_btn = AdjustableButton(self.tr("Refresh"))
        self.refresh_btn.setStyleSheet(button_style)
        self.refresh_btn.clicked.connect(self.refresh_library)
        header_layout.addWidget(self.refresh_btn)
        
        self.export_btn = AdjustableButton(self.tr("Export"))
        self.export_btn.setStyleSheet(button_style)
        self.export_btn.clicked.connect(self._export_item)
        header_layout.addWidget(self.export_btn)
        
        self.remove_btn = AdjustableButton(self.tr("Remove"))
        self.remove_btn.setStyleSheet(button_style)
        self.remove_btn.clicked.connect(self._remove_item)
        header_layout.addWidget(self.remove_btn)
        
        header_widget.setLayout(header_layout)
        main_layout.addWidget(header_widget)
        
        # Library layout with splitter
        library_splitter = QSplitter(Qt.Orientation.Horizontal)
        library_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #555555;
                width: 2px;
            }
        """)
        
        # Left panel - Media display
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Search and controls
        search_layout = QHBoxLayout()
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("Search media..."))
        self.search_input.setStyleSheet("background-color: #333333; color: white; padding: 8px; border-radius: 4px;")
        search_layout.addWidget(self.search_input)
        
        self.search_button = AdjustableButton() # Made instance variable, text in retranslateUi
        self.search_button.setStyleSheet(button_style)
        self.search_button.clicked.connect(self._on_search_media)
        search_layout.addWidget(self.search_button)
        
        # Refresh button
        self.refresh_media_button = AdjustableButton() # Made instance variable, text in retranslateUi
        self.refresh_media_button.setStyleSheet(button_style)
        self.refresh_media_button.clicked.connect(self._load_crow_media)
        search_layout.addWidget(self.refresh_media_button)
        
        left_layout.addLayout(search_layout)
        
        # Media tabs
        self.media_tabs = QTabWidget()
        
        # Raw Photos Tab
        self.photos_tab = QScrollArea()
        self.photos_tab.setWidgetResizable(True)
        self.photos_content = QWidget()
        self.photos_layout = QHBoxLayout(self.photos_content)
        self.photos_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.photos_layout.setSpacing(10)
        self.photos_tab.setWidget(self.photos_content)
        self.media_tabs.addTab(self.photos_tab, self.tr("Raw Photos"))
        
        # Raw Videos Tab
        self.videos_tab = QScrollArea()
        self.videos_tab.setWidgetResizable(True)
        self.videos_content = QWidget()
        self.videos_layout = QHBoxLayout(self.videos_content)
        self.videos_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.videos_layout.setSpacing(10)
        self.videos_tab.setWidget(self.videos_content)
        self.media_tabs.addTab(self.videos_tab, self.tr("Raw Videos"))
        
        # Finished Posts Tab
        self.posts_tab = QScrollArea()
        self.posts_tab.setWidgetResizable(True)
        self.posts_content = QWidget()
        self.posts_layout = QHBoxLayout(self.posts_content)
        self.posts_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.posts_layout.setSpacing(10)
        self.posts_tab.setWidget(self.posts_content)
        self.media_tabs.addTab(self.posts_tab, self.tr("Finished Posts"))
        
        # Finished Galleries Tab
        self.galleries_tab_scroll = QScrollArea()
        self.galleries_tab_scroll.setWidgetResizable(True)
        self.galleries_content = QWidget()
        # Use QVBoxLayout for galleries_content to stack GalleryItemWidgets vertically
        self.galleries_layout = QVBoxLayout(self.galleries_content)
        self.galleries_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.galleries_layout.setSpacing(10)
        self.galleries_tab_scroll.setWidget(self.galleries_content)
        self.media_tabs.addTab(self.galleries_tab_scroll, self.tr("Finished Galleries"))
        
        left_layout.addWidget(self.media_tabs, 1)  # 1 = stretch factor
        
        # Status label
        self.status_label = QLabel() # Made instance variable, text set dynamically or in retranslateUi
        self.status_label.setStyleSheet("color: #BBBBBB; padding: 5px;")
        left_layout.addWidget(self.status_label)
        
        # Right panel - Gallery generator and tools
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Prompt section
        self.prompt_group = QGroupBox() # Made instance variable, title in retranslateUi
        self.prompt_group.setStyleSheet("QGroupBox { color: white; font-weight: bold; }")
        prompt_layout = QVBoxLayout(self.prompt_group)
        
        self.prompt_label = QLabel() # Made instance variable
        prompt_layout.addWidget(self.prompt_label)
        
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText(self.tr("e.g., Pick the best 5 for a winter campaign"))
        self.prompt_input.setStyleSheet("background-color: #333333; color: white; padding: 8px; border-radius: 4px;")
        prompt_layout.addWidget(self.prompt_input)
        
        self.enhance_checkbox = QCheckBox() # Made instance variable, text in retranslateUi
        self.enhance_checkbox.setChecked(True)
        prompt_layout.addWidget(self.enhance_checkbox)
        
        self.generate_gallery_button = AdjustableButton() # Made instance variable, text in retranslateUi
        self.generate_gallery_button.setStyleSheet("""
            background-color: #4f46e5; 
            color: white; 
            padding: 8px 16px;
            border-radius: 4px;
        """)
        self.generate_gallery_button.clicked.connect(self._on_generate_gallery)
        prompt_layout.addWidget(self.generate_gallery_button)
        
        right_layout.addWidget(self.prompt_group)
        
        # Caption section
        self.caption_group = QGroupBox() # Made instance variable, title in retranslateUi
        self.caption_group.setStyleSheet("QGroupBox { color: white; font-weight: bold; }")
        caption_layout = QVBoxLayout(self.caption_group)
        
        self.tone_label = QLabel() # Made instance variable
        caption_layout.addWidget(self.tone_label)
        
        self.tone_input = QLineEdit()
        self.tone_input.setPlaceholderText(self.tr("e.g., Professional and concise"))
        self.tone_input.setStyleSheet("background-color: #333333; color: white; padding: 8px; border-radius: 4px;")
        caption_layout.addWidget(self.tone_input)
        
        self.generate_caption_button = AdjustableButton() # Made instance variable, text in retranslateUi
        self.generate_caption_button.setStyleSheet("""
            background-color: #6d28d9; 
            color: white; 
            padding: 8px 16px;
            border-radius: 4px;
        """)
        self.generate_caption_button.clicked.connect(self._on_generate_caption)
        caption_layout.addWidget(self.generate_caption_button)
        
        self.caption_display = QTextEdit()
        self.caption_display.setPlaceholderText(self.tr("Generated caption will appear here..."))
        self.caption_display.setReadOnly(True)
        self.caption_display.setMinimumHeight(100)
        self.caption_display.setStyleSheet("background-color: #333333; color: white; padding: 8px; border-radius: 4px;")
        caption_layout.addWidget(self.caption_display)
        
        right_layout.addWidget(self.caption_group)
        
        # Generated gallery section
        self.gallery_group = QGroupBox() # Made instance variable, title in retranslateUi
        self.gallery_group.setStyleSheet("QGroupBox { color: white; font-weight: bold; }")
        gallery_layout = QVBoxLayout(self.gallery_group)
        
        self.gallery_selected_media_label = QLabel() # Made instance variable
        gallery_layout.addWidget(self.gallery_selected_media_label)
        
        self.gallery_list = QListWidget()
        self.gallery_list.setMinimumHeight(150)
        self.gallery_list.setStyleSheet("background-color: #333333; color: white;")
        gallery_layout.addWidget(self.gallery_list)
        
        # Save button
        save_layout = QHBoxLayout()
        
        self.gallery_name_input = QLineEdit()
        self.gallery_name_input.setPlaceholderText(self.tr("Gallery name..."))
        self.gallery_name_input.setStyleSheet("background-color: #333333; color: white; padding: 8px; border-radius: 4px;")
        save_layout.addWidget(self.gallery_name_input)
        
        self.save_gallery_button = AdjustableButton() # Made instance variable, text in retranslateUi
        self.save_gallery_button.setStyleSheet("""
            background-color: #059669; 
            color: white; 
            padding: 8px 16px;
            border-radius: 4px;
        """)
        self.save_gallery_button.clicked.connect(self._on_save_gallery)
        save_layout.addWidget(self.save_gallery_button)
        
        gallery_layout.addLayout(save_layout)
        
        right_layout.addWidget(self.gallery_group)
        
        # Add panels to splitter
        library_splitter.addWidget(left_panel)
        library_splitter.addWidget(right_panel)
        
        # Set initial splitter sizes (60:40)
        library_splitter.setSizes([600, 400])
        
        main_layout.addWidget(library_splitter)
        
        # Status bar with styling
        # self.statusBar().setStyleSheet("background-color: #3A3A3A; color: white;") # Done in main stylesheet potentially
        # self.statusBar().showMessage(self.tr("Ready")) # Set in retranslateUi or dynamically

        self.retranslateUi() # Call here to set initial texts
        
    def refresh_library(self):
        """Refresh the media library with both CrowsEye media and library items."""
        try:
            # Load the media from CrowsEye handler
            self._load_crow_media()
            
            # Now also load items from the library manager into the Finished Posts tab
            self._load_library_items()

            # Load saved galleries
            self._load_finished_galleries()
        except Exception as e:
            self.logger.exception(f"Error refreshing library: {e}")
            QMessageBox.critical(self, self.tr("Library Error"), self.tr("Could not refresh library: {error}").format(error=str(e)))
    
    def _load_library_items(self):
        """Load the items from the library manager into the Finished Posts tab."""
        try:
            # Get all library items
            items = self.library_manager.get_all_items()
            
            if not items:
                self.logger.info("No items in the library manager")
                return
            
            self.logger.info(f"Loading {len(items)} items from library manager")
            
            # Count the number of items added to track for the tab label
            items_added = 0
            
            # For each library item, create a MediaItemWidget and add it to the Finished Posts tab
            for item in items:
                if "path" in item and os.path.exists(item["path"]):
                    # Create a widget for the library item and add it to the Finished Posts tab
                    if self.media_handler:
                        item_widget = MediaItemWidget(item["path"], self.media_handler)
                        
                        # Store the library item ID in the widget for reference
                        item_widget.setProperty("libraryItemId", item["id"])
                        
                        # Connect the selected signal
                        item_widget.selected.connect(self._on_library_item_selected)
                        
                        # Add to the Finished Posts layout
                        self.posts_layout.addWidget(item_widget)
                        items_added += 1
            
            # Update the Finished Posts tab label with the total count
            if hasattr(self, '_finished_posts_count'):
                total_posts = self._finished_posts_count + items_added
                self.media_tabs.setTabText(2, self.tr("Finished Posts ({count})").format(count=total_posts))
                
                # Update status with total count
                self.status_label.setText(self.tr("Loaded {count} finished posts").format(count=total_posts))
        
        except Exception as e:
            self.logger.exception(f"Error loading library items: {e}")
            QMessageBox.critical(self, self.tr("Library Error"), self.tr("Could not load library items: {error}").format(error=str(e)))
    
    def _on_library_item_selected(self, media_path):
        """Handle selection of a library item from the Finished Posts tab."""
        # Find the widget that was selected
        sender = self.sender()
        if not sender or not hasattr(sender, "property"):
            return
            
        # Get the library item ID
        item_id = sender.property("libraryItemId")
        if not item_id:
            return
            
        # Get the item from the library manager
        item = self.library_manager.get_item(item_id)
        if not item:
            return
            
        # Add to or remove from selected media
        if media_path in self.selected_media:
            self.selected_media.remove(media_path)
        else:
            self.selected_media.append(media_path)
            
            # If this is a library item with a caption, also update the caption display
            if "caption" in item and item["caption"]:
                self.caption_display.setText(item["caption"])
        
        # Update status
        self.status_label.setText(self.tr("Selected {count} items").format(count=len(self.selected_media)))
        
        # If the media path is in the selected media, show additional options for library items
        if media_path in self.selected_media:
            self._show_library_item_options(item)
    
    def _show_library_item_options(self, item):
        """Show options for a selected library item."""
        try:
            # Create a context menu
            menu = QMenu(self)
            
            # Add options
            view_action = QAction(self.tr("View Details"), self)
            view_action.triggered.connect(lambda: self._view_library_item(item))
            menu.addAction(view_action)
            
            if self.scheduler:
                schedule_action = QAction(self.tr("Schedule Post"), self)
                schedule_action.triggered.connect(lambda: self._schedule_item(item["id"]))
                menu.addAction(schedule_action)
            
            export_action = QAction(self.tr("Export"), self)
            export_action.triggered.connect(lambda: self._do_export_item(item))
            menu.addAction(export_action)
            
            remove_action = QAction(self.tr("Remove"), self)
            remove_action.triggered.connect(lambda: self._do_remove_item(item))
            menu.addAction(remove_action)
            
            # Show the menu at the cursor position
            menu.exec(QCursor.pos())
            
        except Exception as e:
            self.logger.exception(f"Error showing library item options: {e}")
            QMessageBox.critical(self, self.tr("Error"), self.tr("Could not show options: {error}").format(error=str(e)))
    
    def _view_library_item(self, item):
        """View details of a library item in a dialog."""
        try:
            # Create a dialog to show the item details
            dialog = QDialog(self)
            dialog.setWindowTitle(self.tr("Item Details"))
            dialog.setMinimumSize(600, 500)
            dialog.setStyleSheet("background-color: #222222; color: white;")
            
            # Layout
            layout = QVBoxLayout(dialog)
            
            # Preview image
            preview_label = QLabel()
            preview_label.setMinimumSize(500, 300)
            preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            preview_label.setStyleSheet("border: 1px solid #444; background-color: #333;")
            
            # Load image
            if "path" in item and os.path.exists(item["path"]):
                pixmap = QPixmap(item["path"])
                if not pixmap.isNull():
                    preview_label.setPixmap(pixmap.scaled(
                        500, 300,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))
            
            layout.addWidget(preview_label)
            
            # Caption
            caption_label = QLabel(self.tr("Caption:"))
            caption_label.setStyleSheet("font-weight: bold; color: white;")
            layout.addWidget(caption_label)
            
            caption_text = QTextEdit()
            caption_text.setReadOnly(True)
            caption_text.setPlainText(item.get("caption", self.tr("No caption")))
            caption_text.setStyleSheet("background-color: #333; color: white; border: 1px solid #444;")
            layout.addWidget(caption_text)
            
            # Metadata
            metadata_label = QLabel(self.tr("Metadata:"))
            metadata_label.setStyleSheet("font-weight: bold; color: white;")
            layout.addWidget(metadata_label)
            
            # Format metadata
            meta_str = f"{self.tr('Filename')}: {os.path.basename(item.get('path', ''))}\n"
            if "date_added" in item:
                meta_str += f"{self.tr('Date Added')}: {item['date_added'][:16].replace('T', ' ')}\n"
            if "dimensions" in item:
                meta_str += f"{self.tr('Dimensions')}: {item['dimensions'][0]}x{item['dimensions'][1]}\n"
            if "size_str" in item:
                meta_str += f"{self.tr('Size')}: {item['size_str']}\n"
            
            metadata_text = QTextEdit()
            metadata_text.setReadOnly(True)
            metadata_text.setPlainText(meta_str)
            metadata_text.setStyleSheet("background-color: #333; color: white; border: 1px solid #444;")
            metadata_text.setMaximumHeight(100)
            layout.addWidget(metadata_text)
            
            # Close button
            close_button = AdjustableButton(self.tr("Close"))
            close_button.setStyleSheet("""
                background-color: #4A4A4A;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
            """)
            close_button.clicked.connect(dialog.close)
            
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(close_button)
            layout.addLayout(button_layout)
            
            # Show the dialog
            dialog.exec()
            
        except Exception as e:
            self.logger.exception(f"Error viewing item details: {e}")
            QMessageBox.critical(self, self.tr("Error"), self.tr("Could not view item details: {error}").format(error=str(e)))
    
    def _load_crow_media(self):
        """Load media for the library."""
        try:
            if not self.crowseye_handler:
                QMessageBox.warning(self, self.tr("Not Available"), self.tr("Media handler is not available."))
                return
                
            self.status_label.setText(self.tr("Loading media..."))
            
            # Clear layouts
            self._clear_crow_layouts()
            
            # Get media data
            media_data = self.crowseye_handler.get_all_media()
            
            # Populate tabs
            self._populate_media_tab(self.photos_layout, media_data["raw_photos"])
            self._populate_media_tab(self.videos_layout, media_data["raw_videos"])
            
            # Only populate finished posts from crowseye_handler here
            # (library items will be added by _load_library_items)
            self._populate_media_tab(self.posts_layout, media_data["finished_posts"])
            
            # Update tab labels with counts (will be updated with library items count later)
            self.media_tabs.setTabText(0, self.tr("Raw Photos ({count})").format(count=len(media_data['raw_photos'])))
            self.media_tabs.setTabText(1, self.tr("Raw Videos ({count})").format(count=len(media_data['raw_videos'])))
            
            # Finished Posts count will be updated after adding library items
            self._finished_posts_count = len(media_data["finished_posts"])
            
            # Update status
            total_items = sum(len(items) for items in media_data.values())
            self.status_label.setText(self.tr("Loaded {count} media items").format(count=total_items))
            
        except Exception as e:
            self.logger.exception(f"Error loading media: {e}")
            QMessageBox.critical(self, self.tr("Media Error"), self.tr("Could not load media: {error}").format(error=str(e)))
    
    def _clear_crow_layouts(self):
        """Clear all Crow's Eye media layouts."""
        self._clear_layout(self.photos_layout)
        self._clear_layout(self.videos_layout)
        self._clear_layout(self.posts_layout)
        # Also clear finished galleries layout
        if hasattr(self, 'galleries_layout'):
             self._clear_layout(self.galleries_layout)
    
    def _clear_layout(self, layout):
        """Clear all widgets from a layout."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
    
    def _populate_media_tab(self, layout, media_paths):
        """Populate a media tab with media items."""
        for media_path in media_paths:
            if self.media_handler:
                item_widget = MediaItemWidget(media_path, self.media_handler)
                item_widget.selected.connect(self._on_media_item_selected)
                layout.addWidget(item_widget)
    
    def _on_media_item_selected(self, media_path):
        """Handle media item selection."""
        if media_path in self.selected_media:
            self.selected_media.remove(media_path)
        else:
            self.selected_media.append(media_path)
        
        # Update status
        self.status_label.setText(self.tr("Selected {count} items").format(count=len(self.selected_media)))
    
    def _on_search_media(self):
        """Handle media search."""
        try:
            if not self.crowseye_handler:
                QMessageBox.warning(self, self.tr("Not Available"), self.tr("Crow's Eye handler is not available."))
                return
                
            query = self.search_input.text().strip()
            
            # Clear layouts
            self._clear_crow_layouts()
            
            # Search media
            media_data = self.crowseye_handler.search_media(query)
            
            # Populate tabs
            self._populate_media_tab(self.photos_layout, media_data["raw_photos"])
            self._populate_media_tab(self.videos_layout, media_data["raw_videos"])
            self._populate_media_tab(self.posts_layout, media_data["finished_posts"])
            
            # Update tab labels with counts
            self.media_tabs.setTabText(0, self.tr("Raw Photos ({count})").format(count=len(media_data['raw_photos'])))
            self.media_tabs.setTabText(1, self.tr("Raw Videos ({count})").format(count=len(media_data['raw_videos'])))
            self.media_tabs.setTabText(2, self.tr("Finished Posts ({count})").format(count=len(media_data['finished_posts'])))
            
            # Update status
            total_items = sum(len(items) for items in media_data.values())
            self.status_label.setText(self.tr("Found {count} media items matching '{query}'").format(count=total_items, query=query))
            
        except Exception as e:
            self.logger.exception(f"Error searching media: {e}")
            QMessageBox.critical(self, self.tr("Search Error"), self.tr("Could not search media: {error}").format(error=str(e)))
    
    def _on_generate_gallery(self):
        """Handle gallery generation."""
        try:
            if not self.crowseye_handler:
                QMessageBox.warning(self, self.tr("Not Available"), self.tr("Crow's Eye handler is not available."))
                return
                
            prompt = self.prompt_input.text().strip()
            if not prompt:
                QMessageBox.warning(self, self.tr("Missing Prompt"), self.tr("Please enter a gallery focus for generating the gallery."))
                return
            
            # Get media from raw photos and videos automatically without requiring selection
            media_data = self.crowseye_handler.get_all_media()
            media_to_analyze = media_data["raw_photos"] + media_data["raw_videos"]
            
            if not media_to_analyze:
                QMessageBox.warning(self, self.tr("No Media"), self.tr("No raw photos or videos available to generate gallery."))
                return
            
            # Indicate generation in progress
            self.status_label.setText(self.tr("Generating gallery with focus: '{prompt}'...").format(prompt=prompt))
            
            # Generate gallery
            selected_media = self.crowseye_handler.generate_gallery(
                media_paths=media_to_analyze,
                prompt=prompt
            )
            
            # Process the result
            if selected_media:
                self._on_gallery_generated(selected_media)
            else:
                QMessageBox.warning(self, self.tr("Gallery Generation"), self.tr("No media was selected for the gallery."))
                
        except Exception as e:
            self.logger.exception(f"Error generating gallery: {e}")
            QMessageBox.critical(self, self.tr("Gallery Error"), self.tr("Could not generate gallery: {error}").format(error=str(e)))
    
    def _on_gallery_generated(self, selected_media):
        """Handle gallery generation completion."""
        try:
            # Clear the gallery list
            self.gallery_list.clear()
            
            # Store selected media
            self.selected_media = selected_media
            
            # Add selected media to the gallery list
            for media_path in selected_media:
                filename = os.path.basename(media_path)
                item = QListWidgetItem(filename)
                self.gallery_list.addItem(item)
            
            # Update status
            self.status_label.setText(self.tr("Generated gallery with {count} items").format(count=len(selected_media)))
            
            # Auto-generate a caption
            self._on_generate_caption()
            
        except Exception as e:
            self.logger.exception(f"Error processing gallery: {e}")
            QMessageBox.critical(self, self.tr("Gallery Error"), self.tr("Error processing generated gallery: {error}").format(error=str(e)))
    
    def _on_generate_caption(self):
        """Handle caption generation."""
        try:
            if not self.crowseye_handler:
                QMessageBox.warning(self, self.tr("Not Available"), self.tr("Crow's Eye handler is not available."))
                return
                
            if not self.selected_media:
                QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select media items or generate a gallery first."))
                return
            
            tone_prompt = self.tone_input.text().strip()
            
            # Update status
            self.status_label.setText(self.tr("Generating caption..."))
            
            # Generate caption
            caption = self.crowseye_handler.generate_caption(self.selected_media, tone_prompt)
            
            # Update caption display
            if caption:
                self.caption_display.setText(caption)
                self.status_label.setText(self.tr("Caption generated successfully"))
            else:
                QMessageBox.warning(self, self.tr("Caption Error"), self.tr("Could not generate caption."))
                
        except Exception as e:
            self.logger.exception(f"Error generating caption: {e}")
            QMessageBox.critical(self, self.tr("Caption Error"), self.tr("Could not generate caption: {error}").format(error=str(e)))
    
    def _on_save_gallery(self):
        """Handle gallery saving."""
        try:
            if not self.crowseye_handler:
                QMessageBox.warning(self, self.tr("Not Available"), self.tr("Crow's Eye handler is not available."))
                return
                
            gallery_name = self.gallery_name_input.text().strip()
            if not gallery_name:
                QMessageBox.warning(self, self.tr("Missing Name"), self.tr("Please enter a name for the gallery."))
                return
            
            caption = self.caption_display.toPlainText().strip()
            if not caption:
                reply = QMessageBox.question(
                    self,
                    self.tr("Missing Caption"),
                    self.tr("There is no caption. Do you want to generate one before saving?"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self._on_generate_caption()
                    caption = self.caption_display.toPlainText().strip()
                
                if not caption:
                    return
            
            if not self.selected_media:
                QMessageBox.warning(self, self.tr("No Media"), self.tr("Please select media items or generate a gallery first."))
                return
            
            # Save the gallery
            if self.crowseye_handler.save_gallery(gallery_name, self.selected_media, caption):
                # Clear inputs after saving
                self.gallery_name_input.clear()
                # Update status
                self.status_label.setText(self.tr("Gallery '{gallery_name}' saved successfully").format(gallery_name=gallery_name))
                QMessageBox.information(self, self.tr("Gallery Saved"), self.tr("Gallery '{gallery_name}' has been saved successfully.").format(gallery_name=gallery_name))
                self._load_finished_galleries() # Refresh the finished galleries tab
            else:
                QMessageBox.critical(self, self.tr("Save Error"), self.tr("Could not save the gallery."))
                
        except Exception as e:
            self.logger.exception(f"Error saving gallery: {e}")
            QMessageBox.critical(self, self.tr("Save Error"), self.tr("Could not save gallery: {error}").format(error=str(e)))
        
    def _load_finished_galleries(self):
        self._clear_layout(self.galleries_layout)
        galleries = self.crowseye_handler.load_all_galleries()
        if galleries:
            for idx, gallery_data in enumerate(galleries):
                gallery_widget = GalleryItemWidget(gallery_data, self.media_handler)
                gallery_widget.view_edit_requested.connect(self._on_view_edit_gallery_clicked)
                self.galleries_layout.addWidget(gallery_widget)
        else:
            no_galleries_label = QLabel(self.tr("No finished galleries found."))
            self.galleries_layout.addWidget(no_galleries_label)
        self.status_label.setText(self.tr("Finished galleries loaded."))

    def _on_view_edit_gallery_clicked(self, gallery_data: Dict[str, Any]):
        dialog = GalleryDetailDialog(gallery_data, self.crowseye_handler, self.media_handler, self)
        dialog.gallery_updated.connect(self._load_finished_galleries) # Refresh if gallery is updated
        dialog.retranslateUi() # Directly translate the dialog UI
        
        if dialog.exec():
            self.logger.info(self.tr("Gallery details dialog accepted for '{gallery_name}'.").format(gallery_name=gallery_data.get("name", self.tr("gallery"))))
        else:
            self.logger.info(self.tr("Gallery details dialog cancelled for '{gallery_name}'.").format(gallery_name=gallery_data.get("name", self.tr("gallery"))))

    def _export_item(self):
        if not self.selected_media:
            QMessageBox.warning(self, self.tr("Export Error"), self.tr("No media selected for export."))
            return

        # For simplicity, let's export the first selected item if multiple are selected
        # A more robust solution would handle multiple selections (e.g., zip or individual prompts)
        media_to_export = self.selected_media[0]
        self._do_export_item({"path": media_to_export, "name": os.path.basename(media_to_export)})

    def _do_export_item(self, item_to_export: Dict[str, Any]):
        item_path = item_to_export.get("path")
        item_name = item_to_export.get("name", self.tr("item"))

        if not item_path or not os.path.exists(item_path):
            QMessageBox.warning(self, self.tr("Export Error"), self.tr("Item path not found or invalid: {item_path}").format(item_path=item_path or 'N/A'))
            return

        default_filename = os.path.basename(item_path)
        save_dir = QFileDialog.getExistingDirectory(self, self.tr("Select Export Directory"), os.path.expanduser("~"))

        if not save_dir:
            self.status_label.setText(self.tr("Export cancelled."))
            return

        destination_path = os.path.join(save_dir, default_filename)

        if os.path.exists(destination_path):
            reply = QMessageBox.question(self, self.tr("Confirm Overwrite"),
                                         self.tr("File '{filename}' already exists. Overwrite?").format(filename=default_filename),
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                                         QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Cancel:
                self.status_label.setText(self.tr("Export cancelled."))
                return
            if reply == QMessageBox.StandardButton.No:
                self.status_label.setText(self.tr("Export cancelled (did not overwrite)."))
                return
        
        try:
            # Use library_manager for consistent export if available
            if hasattr(self.library_manager, 'export_media_item'):
                self.library_manager.export_media_item(item_path, destination_path)
            else: # Fallback to simple copy if manager method not present
                import shutil
                shutil.copy2(item_path, destination_path)
            QMessageBox.information(self, self.tr("Export Successful"), self.tr("Item '{item_name}' exported to {destination_path}").format(item_name=item_name, destination_path=destination_path))
            self.status_label.setText(self.tr("Item '{item_name}' exported.").format(item_name=item_name))
        except Exception as e:
            self.logger.error(f"Error exporting item '{item_name}': {e}")
            QMessageBox.critical(self, self.tr("Export Failed"), self.tr("Failed to export item: {error_message}").format(error_message=str(e)))
            self.status_label.setText(self.tr("Export failed for '{item_name}'.").format(item_name=item_name))

    def _remove_item(self):
        if not self.selected_media:
            QMessageBox.warning(self, self.tr("Remove Error"), self.tr("No media selected for removal."))
            return

        # For simplicity, remove the first selected item
        # A more robust solution would iterate or confirm for multiple
        media_to_remove_path = self.selected_media[0]
        item_name = os.path.basename(media_to_remove_path)

        confirm_msg = self.tr("Are you sure you want to remove '{item_name}'? This may also remove it from saved galleries and posts if it's a raw media file.").format(item_name=item_name)
        if QMessageBox.question(self, self.tr("Confirm Removal"), confirm_msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                # Use CrowsEyeHandler to remove, as it might be part of galleries/posts
                if self.crowseye_handler.remove_media_item(media_to_remove_path):
                    QMessageBox.information(self, self.tr("Removal Successful"), self.tr("Item '{item_name}' removed.").format(item_name=item_name))
                    self.status_label.setText(self.tr("Item '{item_name}' removed.").format(item_name=item_name))
                    self.selected_media.remove(media_to_remove_path)
                    self.refresh_library() # Refresh all views
                else:
                    QMessageBox.warning(self, self.tr("Removal Failed"), self.tr("Could not remove '{item_name}'. It might be in use or not found.").format(item_name=item_name))
            except Exception as e:
                self.logger.error(f"Error removing item '{item_name}': {e}")
                QMessageBox.critical(self, self.tr("Removal Failed"), self.tr("Failed to remove item: {error_message}").format(error_message=str(e)))
                self.status_label.setText(self.tr("Removal failed for '{item_name}'.").format(item_name=item_name))
    
    def _do_remove_item(self, item: Dict[str, Any]):
        # This specific _do_remove_item expecting a dict might be from an older structure
        # The current context menu and general remove button operate on self.selected_media (paths)
        # For now, let's adapt it or assume it can be called with a dict constructed from a path.
        item_path = item.get("path")
        item_name = item.get("name", os.path.basename(item_path) if item_path else self.tr("this item"))

        if not item_path:
            QMessageBox.warning(self, self.tr("Remove Error"), self.tr("Cannot identify item to remove (path missing)."))
            return

        confirm_msg = self.tr("Are you sure you want to remove '{item_name}'? This might be irreversible.").format(item_name=item_name)
        if QMessageBox.question(self, self.tr("Confirm Removal"), confirm_msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                if self.crowseye_handler.remove_media_item(item_path):
                    QMessageBox.information(self, self.tr("Removal Successful"), self.tr("Item '{item_name}' removed.").format(item_name=item_name))
                    self.status_label.setText(self.tr("Item '{item_name}' removed.").format(item_name=item_name))
                    if item_path in self.selected_media: # Also remove from current selection list
                        self.selected_media.remove(item_path)
                    self.refresh_library()
                else:
                    QMessageBox.warning(self, self.tr("Removal Failed"), self.tr("Could not remove '{item_name}'.").format(item_name=item_name))
            except Exception as e:
                self.logger.error(f"Error removing item '{item_name}': {e}")
                QMessageBox.critical(self, self.tr("Removal Failed"), self.tr("Failed to remove item: {error_message}").format(error_message=str(e)))

    def _schedule_item(self, item_id: str):
        # This item_id should be a unique identifier for a schedulable item (e.g., post ID from library_manager)
        item_data = self.library_manager.get_item(item_id) # Assuming this returns a dict with path, caption, etc.
        if not item_data:
            QMessageBox.warning(self, self.tr("Schedule Error"), self.tr("Could not find item with ID '{item_id}' to schedule.").format(item_id=item_id))
            return

        if not self.scheduler:
            QMessageBox.critical(self, self.tr("Scheduler Error"), self.tr("Scheduler component not available."))
            return

        # Construct data for ScheduleDialog (media_path, caption, etc.)
        # The ScheduleDialog expects `item_to_schedule` dict
        dialog_item_data = {
            "media_path": item_data.get("path"),
            "caption": item_data.get("caption", ""),
            "item_id": item_id, # Original ID
            "name": item_data.get("name", os.path.basename(item_data.get("path", "Scheduled Item")))
        }

        dialog = ScheduleDialog(self.scheduler, item_to_schedule=dialog_item_data, parent=self)
        
        dialog.retranslateUi() # Directly translate the dialog UI
        
        if dialog.exec():
            self.status_label.setText(self.tr("Item '{item_name}' scheduled.").format(item_name=dialog_item_data["name"]))
        else:
            self.status_label.setText(self.tr("Scheduling cancelled for '{item_name}'.").format(item_name=dialog_item_data["name"]))

    def set_theme(self, is_dark: bool) -> None:
        # This window has its own stylesheet, theme changes from main window might not apply directly
        # or could be overridden. For now, this is a placeholder.
        self.logger.info(f"LibraryWindow set_theme called with is_dark={is_dark}. Current styling is self-contained.")
        # If specific elements needed to change, they would be updated here.

    def closeEvent(self, event: QEvent):
        self.logger.info("Library window closing.")
        super().closeEvent(event)
    
    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.logger.info("LibraryWindow received LanguageChange event.")
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.logger.info("Retranslating LibraryWindow UI.")
        self.setWindowTitle(self.tr("Media Library"))
        
        # Header section
        if hasattr(self, 'title_label'): self.title_label.setText(self.tr("Media Library"))
        if hasattr(self, 'refresh_btn'): self.refresh_btn.setText(self.tr("Refresh"))
        if hasattr(self, 'export_btn'): self.export_btn.setText(self.tr("Export"))
        if hasattr(self, 'remove_btn'): self.remove_btn.setText(self.tr("Remove"))

        # Left panel - search and controls
        if hasattr(self, 'search_input'): self.search_input.setPlaceholderText(self.tr("Search media..."))
        if hasattr(self, 'search_button'): self.search_button.setText(self.tr("Search"))
        if hasattr(self, 'refresh_media_button'): self.refresh_media_button.setText(self.tr("Refresh Media")) # Changed from just "Refresh"

        # Media tabs (Update tab texts by index)
        if hasattr(self, 'media_tabs'):
            if self.media_tabs.count() > 0: self.media_tabs.setTabText(0, self.tr("Raw Photos"))
            if self.media_tabs.count() > 1: self.media_tabs.setTabText(1, self.tr("Raw Videos"))
            if self.media_tabs.count() > 2: self.media_tabs.setTabText(2, self.tr("Finished Posts"))
            if self.media_tabs.count() > 3: self.media_tabs.setTabText(3, self.tr("Finished Galleries"))

        # Status label (default text)
        if hasattr(self, 'status_label') and self.status_label.text() == "Ready": # Check against original English
             self.status_label.setText(self.tr("Ready"))
        if hasattr(self, 'statusBar') and self.statusBar().currentMessage() == "Ready":
            self.statusBar().showMessage(self.tr("Ready"))

        # Right panel - Gallery generator
        if hasattr(self, 'prompt_group'): self.prompt_group.setTitle(self.tr("Gallery Generator"))
        if hasattr(self, 'prompt_label'): self.prompt_label.setText(self.tr("Gallery Focus:"))
        if hasattr(self, 'prompt_input'): self.prompt_input.setPlaceholderText(self.tr("e.g., Pick the best 5 for a winter campaign"))
        if hasattr(self, 'enhance_checkbox'): self.enhance_checkbox.setText(self.tr("Auto-enhance photos"))
        if hasattr(self, 'generate_gallery_button'): self.generate_gallery_button.setText(self.tr("Generate Gallery"))

        # Caption section
        if hasattr(self, 'caption_group'): self.caption_group.setTitle(self.tr("Caption Generator"))
        if hasattr(self, 'tone_label'): self.tone_label.setText(self.tr("Tone Prompt:"))
        if hasattr(self, 'tone_input'): self.tone_input.setPlaceholderText(self.tr("e.g., Professional and concise"))
        if hasattr(self, 'generate_caption_button'): self.generate_caption_button.setText(self.tr("Generate Caption"))
        if hasattr(self, 'caption_display'): self.caption_display.setPlaceholderText(self.tr("Generated caption will appear here..."))

        # Generated gallery section
        if hasattr(self, 'gallery_group'): self.gallery_group.setTitle(self.tr("Generated Gallery"))
        if hasattr(self, 'gallery_selected_media_label'): self.gallery_selected_media_label.setText(self.tr("Selected Media:"))
        if hasattr(self, 'gallery_name_input'): self.gallery_name_input.setPlaceholderText(self.tr("Gallery name..."))
        if hasattr(self, 'save_gallery_button'): self.save_gallery_button.setText(self.tr("Save Gallery"))

        # Dynamic texts within methods like _load_crow_media, QMessageBox, etc., are already using self.tr().
        # Refreshing the library might be needed if item counts in tab texts need updating and are not part of the above.
        # self.refresh_library() # Consider if this is too heavy or if specific parts of it are needed for retranslation.
        self.logger.info("LibraryWindow UI retranslated.")

