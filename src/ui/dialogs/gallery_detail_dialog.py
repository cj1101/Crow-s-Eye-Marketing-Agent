"""
Gallery Detail Dialog for viewing and editing saved galleries.
"""
import logging
from typing import Dict, Any
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, 
    QLineEdit, QScrollArea, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QEvent

from ...handlers.crowseye_handler import CrowsEyeHandler
from ...handlers.media_handler import MediaHandler
from ...handlers.image_edit_handler import ImageEditHandler
from ..components.gallery_preview_widget import GalleryImagePreviewWidget
from ..base_dialog import BaseDialog


class GalleryDetailDialog(BaseDialog):
    """Dialog to view and edit details of a saved gallery."""
    gallery_updated = Signal()

    def __init__(self, gallery_data: Dict[str, Any], crowseye_handler: CrowsEyeHandler, media_handler: MediaHandler, parent=None):
        super().__init__(parent)
        self.gallery_data = gallery_data
        self.crowseye_handler = crowseye_handler
        self.media_handler = media_handler
        self.image_edit_handler = ImageEditHandler()
        
        self.setWindowTitle("Gallery Details")
        self.setModal(True)
        self.resize(800, 600)
        
        self._setup_ui()
        self.retranslateUi() # Initial translation

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Gallery name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Gallery Name:"))
        self.name_edit = QLineEdit(self.gallery_data.get('name', ''))
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Gallery caption
        caption_layout = QVBoxLayout()
        self.caption_label = QLabel() # Text set in retranslateUi
        caption_layout.addWidget(self.caption_label)
        
        self.caption_edit = QTextEdit()
        self.caption_edit.setPlainText(self.gallery_data.get('caption', ''))
        self.caption_edit.setMaximumHeight(100)
        caption_layout.addWidget(self.caption_edit)
        
        # Caption generation button
        self.generate_caption_button = QPushButton() # Text set in retranslateUi
        self.generate_caption_button.clicked.connect(self._on_generate_caption)
        self.generate_caption_button.setStyleSheet("background-color: #6d28d9; color: white; padding: 8px; border-radius: 4px;")
        caption_layout.addWidget(self.generate_caption_button)
        
        layout.addLayout(caption_layout)
        
        # Media preview header
        media_header_layout = QHBoxLayout()
        self.media_label = QLabel() # Text set in retranslateUi
        media_header_layout.addWidget(self.media_label)
        media_header_layout.addStretch()
        
        # Add Media button
        self.add_media_button = QPushButton() # Text set in retranslateUi
        self.add_media_button.clicked.connect(self._on_add_media)
        self.add_media_button.setStyleSheet("""
            QPushButton {
                background-color: #7c3aed; color: white; border: none;
                padding: 6px 12px; border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background-color: #6d28d9; }
        """)
        media_header_layout.addWidget(self.add_media_button)
        
        layout.addLayout(media_header_layout)
        
        # Scrollable area for media
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.media_grid = QGridLayout(scroll_widget)
        
        # Add media preview widgets
        self._refresh_media_preview()
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton() # Text set in retranslateUi
        self.save_button.clicked.connect(self._save_gallery_changes)
        self.save_button.setStyleSheet("background-color: #059669; color: white; padding: 8px 16px; border-radius: 4px;")
        button_layout.addWidget(self.save_button)
        
        button_layout.addStretch()
        
        self.close_button = QPushButton() # Text set in retranslateUi
        self.close_button.clicked.connect(self.close)
        self.close_button.setStyleSheet("background-color: #6b7280; color: white; padding: 8px 16px; border-radius: 4px;")
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)

    def _on_add_media(self):
        """Handle add media button click."""
        try:
            from .media_selection_dialog import MediaSelectionDialog
            
            # Get current media paths to exclude them from selection
            current_media = self.gallery_data.get('media_paths', [])
            
            dialog = MediaSelectionDialog(self.crowseye_handler, current_media, self)
            dialog.media_selected.connect(self._on_media_added)
            
            if dialog.exec():
                # Dialog handled via signal
                pass
                
        except Exception as e:
            logging.error(f"Error opening media selection dialog: {e}")
            QMessageBox.warning(self, "Error", f"Could not open media selection: {str(e)}")

    def _on_media_added(self, new_media_paths):
        """Handle new media being added to the gallery."""
        try:
            # Add new media to gallery data
            current_media = self.gallery_data.get('media_paths', [])
            updated_media = current_media + new_media_paths
            self.gallery_data['media_paths'] = updated_media
            
            # Refresh the preview
            self._refresh_media_preview()
            
            # Show success message
            count = len(new_media_paths)
            QMessageBox.information(
                self, 
                "Media Added", 
                f"Successfully added {count} media item{'s' if count != 1 else ''} to the gallery."
            )
            
        except Exception as e:
            logging.error(f"Error adding media to gallery: {e}")
            QMessageBox.warning(self, "Error", f"Could not add media: {str(e)}")

    def _handle_edit_image_request(self, media_path: str):
        """Handle request to edit an image."""
        try:
            # Open image edit dialog
            from ..image_edit_dialog import ImageEditDialog
            dialog = ImageEditDialog(media_path, self.image_edit_handler, self)
            if dialog.exec() == dialog.DialogCode.Accepted:
                # Refresh the preview if image was edited
                self._refresh_media_preview()
        except Exception as e:
            logging.error(f"Error opening image edit dialog: {e}")
            QMessageBox.warning(self, "Error", f"Could not open image editor: {str(e)}")

    def _save_gallery_changes(self):
        """Save changes to the gallery."""
        try:
            # Update gallery data
            self.gallery_data['name'] = self.name_edit.text()
            self.gallery_data['caption'] = self.caption_edit.toPlainText()
            
            # Save to library manager (assuming it has a method to update galleries)
            # This would need to be implemented in the library manager
            self.gallery_updated.emit()
            
            QMessageBox.information(self, "Success", "Gallery updated successfully!")
            
        except Exception as e:
            logging.error(f"Error saving gallery changes: {e}")
            QMessageBox.warning(self, "Error", f"Could not save changes: {str(e)}")

    def _on_generate_caption(self):
        """Generate a new caption for the gallery."""
        try:
            # Get media paths for context
            media_paths = self.gallery_data.get('media_paths', [])
            if not media_paths:
                QMessageBox.warning(self, "Warning", "No media in gallery to generate caption from.")
                return
            
            # Use AI handler to generate caption
            # This would need to be implemented
            caption = "Generated caption based on gallery content..."
            self.caption_edit.setPlainText(caption)
            
        except Exception as e:
            logging.error(f"Error generating caption: {e}")
            QMessageBox.warning(self, "Error", f"Could not generate caption: {str(e)}")

    def _refresh_media_preview(self):
        """Refresh the media preview grid."""
        # Clear existing widgets
        for i in reversed(range(self.media_grid.count())):
            child = self.media_grid.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Re-add media preview widgets
        media_paths = self.gallery_data.get('media_paths', [])
        for i, media_path in enumerate(media_paths):
            preview_widget = GalleryImagePreviewWidget(media_path, self.media_handler)
            preview_widget.edit_image_requested.connect(self._handle_edit_image_request)
            row = i // 3
            col = i % 3
            self.media_grid.addWidget(preview_widget, row, col)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        self.setWindowTitle(self.tr("Gallery Details"))
        self.caption_label.setText(self.tr("Caption:"))
        self.generate_caption_button.setText(self.tr("Generate Caption"))
        self.media_label.setText(self.tr("Media:"))
        self.add_media_button.setText(self.tr("Add Media"))
        self.save_button.setText(self.tr("Save Changes"))
        self.close_button.setText(self.tr("Close")) 