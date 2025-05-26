"""
Media Selection Dialog for adding additional media to galleries.
"""
import os
import logging
from typing import List, Set
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, 
    QGridLayout, QCheckBox, QWidget, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QEvent

from ...api.ai.crowseye_handler import CrowsEyeHandler
from ..components.media_thumbnail_widget import MediaThumbnailWidget
from ..base_dialog import BaseDialog


class MediaSelectionDialog(BaseDialog):
    """Dialog for selecting media to add to a gallery."""
    
    media_selected = Signal(list)  # Emit list of selected media paths
    
    def __init__(self, crowseye_handler: CrowsEyeHandler, 
                 existing_media: List[str] = None, parent=None):
        super().__init__(parent)
        self.crowseye_handler = crowseye_handler
        self.existing_media = set(existing_media or [])
        self.selected_media = set()
        self.media_thumbnails = {}
        
        self.setWindowTitle("Add Media to Gallery")
        self.setModal(True)
        self.resize(800, 600)
        
        self._setup_ui()
        self._load_media()
        self.retranslateUi()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel("Select Media to Add")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        # Select all checkbox
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.stateChanged.connect(self._on_select_all_changed)
        header_layout.addWidget(self.select_all_checkbox)
        
        layout.addLayout(header_layout)
        
        # Info label
        self.info_label = QLabel("Choose additional media to add to your gallery:")
        self.info_label.setStyleSheet("color: #CCCCCC; margin-bottom: 10px;")
        layout.addWidget(self.info_label)
        
        # Media scroll area
        self.media_scroll = QScrollArea()
        self.media_scroll.setWidgetResizable(True)
        self.media_scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.media_container = QWidget()
        self.media_layout = QGridLayout(self.media_container)
        self.media_layout.setSpacing(10)
        self.media_scroll.setWidget(self.media_container)
        layout.addWidget(self.media_scroll)
        
        # Status label
        self.status_label = QLabel("0 media selected")
        self.status_label.setStyleSheet("color: #CCCCCC; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add Selected")
        self.add_button.clicked.connect(self._on_add_selected)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #059669; color: white; border: none;
                padding: 10px 20px; border-radius: 6px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #047857; }
            QPushButton:disabled { background-color: #6b7280; }
        """)
        self.add_button.setEnabled(False)
        button_layout.addWidget(self.add_button)
        
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6b7280; color: white; border: none;
                padding: 10px 20px; border-radius: 6px; font-size: 14px;
            }
            QPushButton:hover { background-color: #6b7280cc; }
        """)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def _load_media(self):
        """Load available media into the grid."""
        try:
            # Clear existing layout
            self._clear_layout(self.media_layout)
            self.media_thumbnails.clear()
            
            # Get all media from crowseye handler
            all_media = self.crowseye_handler.get_all_media()
            available_media = []
            
            # Collect all raw media that's not already in the gallery
            for media_type in ["raw_photos", "raw_videos"]:
                for media_path in all_media.get(media_type, []):
                    if (os.path.exists(media_path) and 
                        media_path not in self.existing_media):
                        available_media.append((media_path, media_type))
            
            if not available_media:
                self.info_label.setText("No additional media available to add.")
                return
            
            # Add thumbnails to grid
            row, col = 0, 0
            cols_per_row = 6
            
            for media_path, media_type in available_media:
                widget_type = "image" if media_type == "raw_photos" else "video"
                thumbnail = MediaThumbnailWidget(media_path, widget_type)
                thumbnail.clicked.connect(self._on_media_item_selected)
                
                self.media_layout.addWidget(thumbnail, row, col)
                self.media_thumbnails[media_path] = thumbnail
                
                col += 1
                if col >= cols_per_row:
                    col = 0
                    row += 1
            
            self.media_layout.setRowStretch(row + 1, 1)
            self.media_layout.setColumnStretch(cols_per_row, 1)
            
            self.info_label.setText(f"{len(available_media)} media files available to add:")
            
        except Exception as e:
            logging.error(f"Error loading media for selection: {e}")
            self.info_label.setText("Error loading media.")
    
    def _clear_layout(self, layout):
        """Clear all widgets from a layout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _on_media_item_selected(self, media_path):
        """Handle media item selection."""
        if media_path in self.selected_media:
            self.selected_media.remove(media_path)
            self.media_thumbnails[media_path].set_selected(False)
        else:
            self.selected_media.add(media_path)
            self.media_thumbnails[media_path].set_selected(True)
        
        self._update_selection_display()
    
    def _on_select_all_changed(self, state):
        """Handle select all checkbox change."""
        select_all = state == Qt.CheckState.Checked
        
        if select_all:
            self.selected_media = set(self.media_thumbnails.keys())
        else:
            self.selected_media.clear()
        
        # Update all thumbnails
        for media_path, thumbnail in self.media_thumbnails.items():
            thumbnail.set_selected(media_path in self.selected_media)
        
        self._update_selection_display()
    
    def _update_selection_display(self):
        """Update selection display."""
        count = len(self.selected_media)
        self.status_label.setText(f"{count} media selected")
        self.add_button.setEnabled(count > 0)
        
        # Update select all checkbox state
        total_media = len(self.media_thumbnails)
        if count == 0:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
        elif count == total_media:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Checked)
        else:
            self.select_all_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
    
    def _on_add_selected(self):
        """Add selected media and close dialog."""
        if self.selected_media:
            self.media_selected.emit(list(self.selected_media))
            self.accept()
        else:
            QMessageBox.warning(self, "No Selection", "Please select at least one media item.")
    
    def get_selected_media(self):
        """Get the list of selected media paths."""
        return list(self.selected_media)
    
    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)
    
    def retranslateUi(self):
        self.setWindowTitle(self.tr("Add Media to Gallery"))
        self.title_label.setText(self.tr("Select Media to Add"))
        self.select_all_checkbox.setText(self.tr("Select All"))
        self.add_button.setText(self.tr("Add Selected"))
        self.cancel_button.setText(self.tr("Cancel")) 