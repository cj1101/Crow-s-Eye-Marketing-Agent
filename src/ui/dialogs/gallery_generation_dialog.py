"""
Gallery Generation Dialog for AI-powered gallery creation.
"""

import logging
import os
from typing import List, Dict, Any, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QTextEdit, QCheckBox, QGroupBox, QScrollArea,
    QWidget, QGridLayout, QMessageBox, QProgressDialog
)

class MediaThumbnailWidget(QWidget):
    """Small thumbnail widget for selected media in the dialog."""
    
    def __init__(self, media_path: str, parent=None):
        super().__init__(parent)
        self.media_path = media_path
        self.setFixedSize(80, 80)
        self._create_ui()
    
    def _create_ui(self):
        """Create the thumbnail UI."""
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
        try:
            if self.media_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                pixmap = QPixmap(self.media_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(70, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.thumbnail_label.setPixmap(scaled_pixmap)
                else:
                    self.thumbnail_label.setText("No Preview")
            else:
                self.thumbnail_label.setText("🎥")
                self.thumbnail_label.setStyleSheet("""
                    QLabel {
                        border: 1px solid #444;
                        border-radius: 4px;
                        background-color: #2a2a2a;
                        color: #888;
                        font-size: 16px;
                    }
                """)
        except Exception as e:
            logging.warning(f"Could not load thumbnail: {e}")
            self.thumbnail_label.setText("❌")
        
        layout.addWidget(self.thumbnail_label)
        
        # Filename
        filename = os.path.basename(self.media_path)
        if len(filename) > 10:
            filename = filename[:7] + "..."
        
        name_label = QLabel(filename)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("color: #CCCCCC; font-size: 8px;")
        layout.addWidget(name_label)

class GalleryGenerationDialog(QDialog):
    """Dialog for generating galleries using AI prompts."""
    
    def __init__(self, crowseye_handler, parent=None):
        super().__init__(parent)
        self.crowseye_handler = crowseye_handler
        self.generated_gallery = None
        self.selected_media_paths = []
        
        self.setWindowTitle("Generate Gallery with AI")
        self.setMinimumSize(700, 600)
        self.setModal(True)
        
        self._create_ui()
        self._connect_signals()
    
    def _create_ui(self):
        """Create the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("AI Gallery Generation")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "1. Enter a prompt to select media  2. Review and edit selection  3. Generate caption  4. Save gallery"
        )
        desc_label.setStyleSheet("color: #CCCCCC; font-size: 12px; margin-bottom: 15px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Step 1: Media Selection Prompt
        selection_group = QGroupBox("Step 1: Media Selection")
        selection_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        selection_layout = QVBoxLayout(selection_group)
        
        self.selection_prompt_input = QTextEdit()
        self.selection_prompt_input.setPlaceholderText(
            "Describe what media you want to select:\n"
            "• Pick the best 5 photos for a winter campaign\n"
            "• Show me photos with people for social media\n"
            "• Find bread and bakery images for our website"
        )
        self.selection_prompt_input.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 6px;
                color: #FFFFFF;
                padding: 8px;
                font-size: 12px;
            }
        """)
        self.selection_prompt_input.setMaximumHeight(80)
        selection_layout.addWidget(self.selection_prompt_input)
        
        # Generate selection button
        self.generate_selection_button = QPushButton("Generate Selection")
        self.generate_selection_button.setStyleSheet("""
            QPushButton {
                background-color: #7c3aed;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6d28d9;
            }
            QPushButton:disabled {
                background-color: #4a4a4a;
                color: #888;
            }
        """)
        self.generate_selection_button.clicked.connect(self._on_generate_selection)
        selection_layout.addWidget(self.generate_selection_button)
        
        layout.addWidget(selection_group)
        
        # Step 2: Selected Media Preview
        self.preview_group = QGroupBox("Step 2: Selected Media (Click to Remove)")
        self.preview_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        self.preview_group.hide()
        
        preview_layout = QVBoxLayout(self.preview_group)
        
        # Header with selection info and add button
        header_layout = QHBoxLayout()
        self.selection_info_label = QLabel()
        self.selection_info_label.setStyleSheet("color: #FFFFFF; font-size: 12px; margin-bottom: 10px;")
        header_layout.addWidget(self.selection_info_label)
        
        header_layout.addStretch()
        
        # Add Media button
        self.add_media_button = QPushButton("Add Media")
        self.add_media_button.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #047857;
            }
        """)
        self.add_media_button.clicked.connect(self._on_add_media)
        header_layout.addWidget(self.add_media_button)
        
        preview_layout.addLayout(header_layout)
        
        # Thumbnails scroll area
        self.thumbnails_scroll = QScrollArea()
        self.thumbnails_scroll.setWidgetResizable(True)
        self.thumbnails_scroll.setMaximumHeight(120)
        self.thumbnails_scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.thumbnails_container = QWidget()
        self.thumbnails_layout = QHBoxLayout(self.thumbnails_container)
        self.thumbnails_layout.setAlignment(Qt.AlignLeft)
        self.thumbnails_scroll.setWidget(self.thumbnails_container)
        preview_layout.addWidget(self.thumbnails_scroll)
        
        layout.addWidget(self.preview_group)
        
        # Step 3: Caption Generation
        caption_group = QGroupBox("Step 3: Caption Generation")
        caption_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        caption_layout = QVBoxLayout(caption_group)
        
        self.caption_prompt_input = QLineEdit()
        self.caption_prompt_input.setPlaceholderText("Caption style (e.g., 'fun and engaging', 'professional', 'casual')...")
        self.caption_prompt_input.setText("engaging and creative")
        self.caption_prompt_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 6px;
                color: #FFFFFF;
                padding: 8px;
                font-size: 12px;
            }
        """)
        caption_layout.addWidget(self.caption_prompt_input)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.enhance_photos_cb = QCheckBox("Enhance photos automatically")
        self.enhance_photos_cb.setStyleSheet("color: #FFFFFF;")
        self.enhance_photos_cb.setChecked(True)
        options_layout.addWidget(self.enhance_photos_cb)
        
        self.generate_caption_cb = QCheckBox("Generate caption")
        self.generate_caption_cb.setStyleSheet("color: #FFFFFF;")
        self.generate_caption_cb.setChecked(True)
        options_layout.addWidget(self.generate_caption_cb)
        
        caption_layout.addLayout(options_layout)
        
        # Generated caption display
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
        self.caption_display.setMaximumHeight(80)
        self.caption_display.setPlaceholderText("Generated caption will appear here...")
        caption_layout.addWidget(self.caption_display)
        
        layout.addWidget(caption_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.generate_gallery_button = QPushButton("Generate Gallery")
        self.generate_gallery_button.setStyleSheet("""
            QPushButton {
                background-color: #7c3aed;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6d28d9;
            }
            QPushButton:disabled {
                background-color: #4a4a4a;
                color: #888;
            }
        """)
        self.generate_gallery_button.clicked.connect(self._on_generate_gallery)
        self.generate_gallery_button.setEnabled(False)
        button_layout.addWidget(self.generate_gallery_button)
        
        self.save_button = QPushButton("Save Gallery")
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
        self.save_button.clicked.connect(self._on_save_gallery)
        self.save_button.hide()
        button_layout.addWidget(self.save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
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
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        self.selection_prompt_input.textChanged.connect(self._on_selection_prompt_changed)
    
    def _on_selection_prompt_changed(self):
        """Handle selection prompt text changes."""
        has_text = bool(self.selection_prompt_input.toPlainText().strip())
        self.generate_selection_button.setEnabled(has_text)
    
    def _on_generate_selection(self):
        """Generate media selection based on prompt."""
        prompt = self.selection_prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "No Prompt", "Please enter a selection prompt.")
            return
        
        # Show progress dialog
        progress = QProgressDialog("Selecting media...", "Cancel", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        try:
            # Get all available media
            all_media = self.crowseye_handler.get_all_media()
            all_paths = []
            for media_list in all_media.values():
                all_paths.extend(media_list)
            
            if not all_paths:
                progress.close()
                QMessageBox.information(self, "No Media", "No media available for selection.")
                return
            
            # Generate selection using CrowsEye handler (without enhancement/caption)
            selected_media = self.crowseye_handler.generate_gallery(all_paths, prompt, enhance_photos=False)
            
            if not selected_media:
                progress.close()
                QMessageBox.information(self, "No Results", "No media matched your prompt. Try a different description.")
                return
            
            # Store selected media
            self.selected_media_paths = selected_media
            
            # Update the preview
            self._update_preview()
            
            # Enable gallery generation
            self.generate_gallery_button.setEnabled(True)
            
            progress.close()
            
        except Exception as e:
            progress.close()
            logging.error(f"Error generating selection: {e}")
            QMessageBox.critical(self, "Selection Error", f"Failed to generate selection: {str(e)}")
    
    def _update_preview(self):
        """Update the preview section with selected media."""
        if not self.selected_media_paths:
            # If no media, hide the preview group
            self.preview_group.hide()
            return
        
        # Clear existing thumbnails
        for i in reversed(range(self.thumbnails_layout.count())):
            child = self.thumbnails_layout.takeAt(i)
            if child.widget():
                child.widget().deleteLater()
        
        # Update info
        self.selection_info_label.setText(f"Selected {len(self.selected_media_paths)} media items (click to remove)")
        
        # Add thumbnails with proper click handlers
        for media_path in self.selected_media_paths:
            thumbnail = MediaThumbnailWidget(media_path)
            # Use a closure to properly capture the media_path value
            thumbnail.mousePressEvent = self._create_remove_handler(media_path)
            thumbnail.setToolTip(f"Click to remove: {os.path.basename(media_path)}")
            thumbnail.setCursor(Qt.PointingHandCursor)
            self.thumbnails_layout.addWidget(thumbnail)
        
        # Show preview group
        self.preview_group.show()
        self.adjustSize()
    
    def _create_remove_handler(self, media_path):
        """Create a proper click handler for removing media."""
        def handler(event):
            self._remove_media(media_path)
        return handler
    
    def _remove_media(self, media_path):
        """Remove media from selection."""
        if media_path in self.selected_media_paths:
            self.selected_media_paths.remove(media_path)
            self._update_preview()
            
            # If no media left, hide preview and disable gallery generation
            if not self.selected_media_paths:
                self.preview_group.hide()
                self.generate_gallery_button.setEnabled(False)
                self.adjustSize()
    
    def _on_generate_gallery(self):
        """Generate the final gallery with caption."""
        if not self.selected_media_paths:
            QMessageBox.warning(self, "No Selection", "No media selected for gallery.")
            return
        
        try:
            # Generate caption if requested
            caption = ""
            if self.generate_caption_cb.isChecked():
                caption_style = self.caption_prompt_input.text().strip() or "engaging and creative"
                caption = self.crowseye_handler.generate_caption(self.selected_media_paths, caption_style)
                self.caption_display.setText(caption)
            
            # Store the generated gallery
            self.generated_gallery = {
                'media_paths': self.selected_media_paths.copy(),
                'caption': caption,
                'selection_prompt': self.selection_prompt_input.toPlainText().strip(),
                'caption_style': self.caption_prompt_input.text().strip(),
                'enhance_photos': self.enhance_photos_cb.isChecked()
            }
            
            # Show save button
            self.save_button.show()
            
        except Exception as e:
            logging.error(f"Error generating gallery: {e}")
            QMessageBox.critical(self, "Generation Error", f"Failed to generate gallery: {str(e)}")
    
    def _on_save_gallery(self):
        """Save the generated gallery."""
        if not self.generated_gallery:
            return
        
        from .save_gallery_dialog import SaveGalleryDialog
        
        # Use the save gallery dialog
        dialog = SaveGalleryDialog(
            self.generated_gallery['media_paths'], 
            self.crowseye_handler, 
            self,
            initial_caption=self.generated_gallery['caption']
        )
        
        if dialog.exec():
            # Gallery was saved successfully
            self.accept()
    
    def get_generated_gallery(self) -> Optional[Dict[str, Any]]:
        """Get the generated gallery data."""
        return self.generated_gallery
    
    def get_selected_media_paths(self) -> List[str]:
        """Get the currently selected media paths for highlighting in main window."""
        return self.selected_media_paths.copy() if self.selected_media_paths else []
    
    def _on_add_media(self):
        """Open media selection dialog to add more media to the gallery."""
        from .media_selection_dialog import MediaSelectionDialog
        
        try:
            # Open media selection dialog with existing media excluded
            dialog = MediaSelectionDialog(
                self.crowseye_handler, 
                existing_media=self.selected_media_paths, 
                parent=self
            )
            
            # Connect signal to handle new media selection
            dialog.media_selected.connect(self._on_additional_media_selected)
            
            # Show dialog
            dialog.exec()
            
        except Exception as e:
            logging.error(f"Error opening media selection dialog: {e}")
            QMessageBox.critical(self, "Dialog Error", f"Failed to open media selection: {str(e)}")
    
    def _on_additional_media_selected(self, new_media_paths):
        """Handle additional media selected from the media selection dialog."""
        if new_media_paths:
            # Add new media to existing selection
            self.selected_media_paths.extend(new_media_paths)
            
            # Update the preview (this will show Step 2 if it wasn't visible)
            self._update_preview()
            
            # Ensure gallery generation is enabled if we have media
            if self.selected_media_paths:
                self.generate_gallery_button.setEnabled(True) 