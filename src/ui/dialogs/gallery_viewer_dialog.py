"""
Gallery Viewer Dialog for viewing and editing existing galleries.
"""

import logging
import os
from typing import Dict, Any, List

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QGroupBox, QMessageBox, QScrollArea, QWidget,
    QGridLayout, QFrame
)

class GalleryItemWidget(QWidget):
    """Widget for displaying a single media item in the gallery."""
    
    def __init__(self, media_path: str, parent=None):
        super().__init__(parent)
        self.media_path = media_path
        self.setFixedSize(100, 100)
        self._create_ui()
    
    def _create_ui(self):
        """Create the UI for the media item."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border: 1px solid #444;
                border-radius: 4px;
                background-color: #2a2a2a;
            }
        """)
        
        # Load thumbnail
        self._load_thumbnail()
        
        layout.addWidget(self.thumbnail_label)
        
        # Filename
        filename = os.path.basename(self.media_path)
        if len(filename) > 12:
            filename = filename[:9] + "..."
        
        name_label = QLabel(filename)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("color: #CCCCCC; font-size: 9px;")
        layout.addWidget(name_label)
    
    def _load_thumbnail(self):
        """Load the thumbnail for the media item."""
        try:
            if os.path.exists(self.media_path):
                if self.media_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                    pixmap = QPixmap(self.media_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(90, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.thumbnail_label.setPixmap(scaled_pixmap)
                    else:
                        self.thumbnail_label.setText("No Preview")
                else:
                    # Video file
                    self.thumbnail_label.setText("🎥")
                    self.thumbnail_label.setStyleSheet("""
                        QLabel {
                            border: 1px solid #444;
                            border-radius: 4px;
                            background-color: #2a2a2a;
                            color: #888;
                            font-size: 20px;
                        }
                    """)
            else:
                self.thumbnail_label.setText("❌")
                self.thumbnail_label.setStyleSheet("""
                    QLabel {
                        border: 1px solid #444;
                        border-radius: 4px;
                        background-color: #2a2a2a;
                        color: #ff6b6b;
                        font-size: 16px;
                    }
                """)
        except Exception as e:
            logging.warning(f"Could not load thumbnail for {self.media_path}: {e}")
            self.thumbnail_label.setText("⚠️")

class GalleryViewerDialog(QDialog):
    """Dialog for viewing and editing galleries."""
    
    def __init__(self, gallery_data: Dict[str, Any], crowseye_handler, parent=None):
        super().__init__(parent)
        self.gallery_data = gallery_data
        self.crowseye_handler = crowseye_handler
        self.is_modified = False
        
        self.setWindowTitle(f"Gallery: {gallery_data.get('name', 'Unnamed')}")
        self.setMinimumSize(700, 600)
        self.setModal(True)
        
        self._create_ui()
        self._load_gallery_data()
    
    def _create_ui(self):
        """Create the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel(f"Gallery: {self.gallery_data.get('name', 'Unnamed')}")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Delete button
        self.delete_button = QPushButton("Delete Gallery")
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
        """)
        self.delete_button.clicked.connect(self._on_delete_gallery)
        header_layout.addWidget(self.delete_button)
        
        layout.addLayout(header_layout)
        
        # Gallery info
        info_layout = QHBoxLayout()
        
        creation_date = self.gallery_data.get('created_at', 'Unknown')
        media_count = len(self.gallery_data.get('media_paths', []))
        
        info_label = QLabel(f"Created: {creation_date} • {media_count} media items")
        info_label.setStyleSheet("color: #CCCCCC; font-size: 12px;")
        info_layout.addWidget(info_label)
        
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        
        # Media gallery
        media_group = QGroupBox("Gallery Media")
        media_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        media_layout = QVBoxLayout(media_group)
        
        # Scroll area for media items
        self.media_scroll = QScrollArea()
        self.media_scroll.setWidgetResizable(True)
        self.media_scroll.setStyleSheet("QScrollArea { border: none; }")
        self.media_scroll.setMaximumHeight(300)
        
        # Container for media items
        self.media_container = QWidget()
        self.media_grid = QGridLayout(self.media_container)
        self.media_grid.setSpacing(10)
        
        self.media_scroll.setWidget(self.media_container)
        media_layout.addWidget(self.media_scroll)
        
        layout.addWidget(media_group)
        
        # Caption section
        caption_group = QGroupBox("Gallery Caption")
        caption_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        caption_layout = QVBoxLayout(caption_group)
        
        self.caption_display = QTextEdit()
        self.caption_display.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 6px;
                color: #FFFFFF;
                padding: 8px;
                font-size: 12px;
            }
        """)
        self.caption_display.setMaximumHeight(100)
        caption_layout.addWidget(self.caption_display)
        
        # Caption buttons
        caption_button_layout = QHBoxLayout()
        caption_button_layout.addStretch()
        
        self.regenerate_caption_button = QPushButton("Regenerate Caption")
        self.regenerate_caption_button.setStyleSheet("""
            QPushButton {
                background-color: #7c3aed;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #6d28d9;
            }
        """)
        self.regenerate_caption_button.clicked.connect(self._on_regenerate_caption)
        caption_button_layout.addWidget(self.regenerate_caption_button)
        
        caption_layout.addLayout(caption_button_layout)
        layout.addWidget(caption_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save Changes")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #047857;
            }
        """)
        self.save_button.clicked.connect(self._on_save_changes)
        self.save_button.setEnabled(False)  # Initially disabled
        button_layout.addWidget(self.save_button)
        
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addWidget(button_layout)
        
        # Connect caption text changes
        self.caption_display.textChanged.connect(self._on_caption_changed)
    
    def _load_gallery_data(self):
        """Load the gallery data into the UI."""
        # Load media items
        media_paths = self.gallery_data.get('media_paths', [])
        
        row, col = 0, 0
        cols_per_row = 6
        
        for media_path in media_paths:
            media_widget = GalleryItemWidget(media_path)
            self.media_grid.addWidget(media_widget, row, col)
            
            col += 1
            if col >= cols_per_row:
                col = 0
                row += 1
        
        # Add stretch to push items to top-left
        self.media_grid.setRowStretch(row + 1, 1)
        self.media_grid.setColumnStretch(cols_per_row, 1)
        
        # Load caption
        caption = self.gallery_data.get('caption', '')
        self.caption_display.setText(caption)
    
    def _on_caption_changed(self):
        """Handle caption text changes."""
        self.is_modified = True
        self.save_button.setEnabled(True)
    
    def _on_regenerate_caption(self):
        """Handle caption regeneration."""
        try:
            self.regenerate_caption_button.setEnabled(False)
            self.regenerate_caption_button.setText("Generating...")
            
            media_paths = self.gallery_data.get('media_paths', [])
            caption = self.crowseye_handler.generate_caption(media_paths, "engaging and creative")
            self.caption_display.setText(caption)
            
        except Exception as e:
            logging.error(f"Error regenerating caption: {e}")
            QMessageBox.warning(self, "Caption Error", "Failed to regenerate caption. Please try again.")
        
        finally:
            self.regenerate_caption_button.setEnabled(True)
            self.regenerate_caption_button.setText("Regenerate Caption")
    
    def _on_save_changes(self):
        """Save changes to the gallery."""
        try:
            gallery_filename = self.gallery_data.get('filename', '')
            new_caption = self.caption_display.toPlainText().strip()
            gallery_name = self.gallery_data.get('name', '')
            
            if not gallery_filename:
                QMessageBox.warning(self, "Save Error", "Cannot save: gallery filename not found.")
                return
            
            # Update the gallery using CrowsEye handler
            success = self.crowseye_handler.update_saved_gallery(gallery_filename, gallery_name, new_caption)
            
            if success:
                QMessageBox.information(self, "Changes Saved", "Gallery has been updated successfully!")
                self.is_modified = False
                self.save_button.setEnabled(False)
                
                # Update local data
                self.gallery_data['caption'] = new_caption
            else:
                QMessageBox.warning(self, "Save Failed", "Failed to save changes. Please try again.")
                
        except Exception as e:
            logging.error(f"Error saving gallery changes: {e}")
            QMessageBox.critical(self, "Save Error", f"Failed to save changes: {str(e)}")
    
    def _on_delete_gallery(self):
        """Handle gallery deletion."""
        gallery_name = self.gallery_data.get('name', 'this gallery')
        
        reply = QMessageBox.question(
            self,
            "Delete Gallery",
            f"Are you sure you want to delete '{gallery_name}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                gallery_filename = self.gallery_data.get('filename', '')
                if gallery_filename:
                    # Delete using CrowsEye handler
                    gallery_path = os.path.join(
                        self.crowseye_handler.media_gallery_dir,
                        gallery_filename
                    )
                    
                    if os.path.exists(gallery_path):
                        os.remove(gallery_path)
                        QMessageBox.information(self, "Gallery Deleted", f"Gallery '{gallery_name}' has been deleted.")
                        self.accept()  # Close the dialog
                    else:
                        QMessageBox.warning(self, "Delete Failed", "Gallery file not found.")
                else:
                    QMessageBox.warning(self, "Delete Failed", "Cannot delete: gallery filename not found.")
                    
            except Exception as e:
                logging.error(f"Error deleting gallery: {e}")
                QMessageBox.critical(self, "Delete Error", f"Failed to delete gallery: {str(e)}")
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.is_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self._on_save_changes()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept() 