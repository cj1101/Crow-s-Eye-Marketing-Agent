"""
Save Gallery Dialog for saving galleries with custom names and captions.
"""

import logging
from typing import List, Optional
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QTextEdit, QGroupBox, QMessageBox
)

class SaveGalleryDialog(QDialog):
    """Dialog for saving galleries with custom names and captions."""
    
    def __init__(self, media_paths: List[str], crowseye_handler, parent=None, initial_caption: str = ""):
        super().__init__(parent)
        self.media_paths = media_paths
        self.crowseye_handler = crowseye_handler
        self.initial_caption = initial_caption
        
        self.setWindowTitle("Save Gallery")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        self._create_ui()
        self._populate_initial_data()
    
    def _create_ui(self):
        """Create the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Save Gallery")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Gallery info
        info_label = QLabel(f"Gallery contains {len(self.media_paths)} media items")
        info_label.setStyleSheet("color: #CCCCCC; font-size: 12px; margin-bottom: 15px;")
        layout.addWidget(info_label)
        
        # Gallery name input
        name_group = QGroupBox("Gallery Name")
        name_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        name_layout = QVBoxLayout(name_group)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter a name for your gallery...")
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 6px;
                color: #FFFFFF;
                padding: 8px;
                font-size: 12px;
            }
        """)
        name_layout.addWidget(self.name_input)
        
        layout.addWidget(name_group)
        
        # Caption input
        caption_group = QGroupBox("Gallery Caption")
        caption_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        caption_layout = QVBoxLayout(caption_group)
        
        caption_label = QLabel("Edit the caption for your gallery:")
        caption_label.setStyleSheet("color: #CCCCCC; font-size: 11px;")
        caption_layout.addWidget(caption_label)
        
        self.caption_input = QTextEdit()
        self.caption_input.setPlaceholderText("Enter a caption for your gallery...")
        self.caption_input.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 6px;
                color: #FFFFFF;
                padding: 8px;
                font-size: 12px;
            }
        """)
        self.caption_input.setMaximumHeight(120)
        caption_layout.addWidget(self.caption_input)
        
        # Caption generation button
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
        
        save_button = QPushButton("Save Gallery")
        save_button.setStyleSheet("""
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
        save_button.clicked.connect(self._on_save_gallery)
        button_layout.addWidget(save_button)
        
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
    
    def _populate_initial_data(self):
        """Populate the dialog with initial data."""
        # Generate default name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"Gallery_{timestamp}"
        self.name_input.setText(default_name)
        
        # Set initial caption if provided
        if self.initial_caption:
            self.caption_input.setText(self.initial_caption)
        else:
            # Generate a caption
            self._generate_caption()
    
    def _generate_caption(self):
        """Generate a caption for the gallery."""
        try:
            caption = self.crowseye_handler.generate_caption(self.media_paths, "engaging and creative")
            self.caption_input.setText(caption)
        except Exception as e:
            logging.warning(f"Failed to generate caption: {e}")
            self.caption_input.setText("New gallery featuring selected media items.")
    
    def _on_regenerate_caption(self):
        """Handle caption regeneration."""
        try:
            self.regenerate_caption_button.setEnabled(False)
            self.regenerate_caption_button.setText("Generating...")
            
            caption = self.crowseye_handler.generate_caption(self.media_paths, "engaging and creative")
            self.caption_input.setText(caption)
            
        except Exception as e:
            logging.error(f"Error regenerating caption: {e}")
            QMessageBox.warning(self, "Caption Error", "Failed to regenerate caption. Please try again.")
        
        finally:
            self.regenerate_caption_button.setEnabled(True)
            self.regenerate_caption_button.setText("Regenerate Caption")
    
    def _on_save_gallery(self):
        """Save the gallery."""
        name = self.name_input.text().strip()
        caption = self.caption_input.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter a name for the gallery.")
            return
        
        if not caption:
            caption = "New gallery featuring selected media items."
        
        try:
            # Save the gallery using CrowsEye handler
            success = self.crowseye_handler.save_gallery(name, self.media_paths, caption)
            
            if success:
                QMessageBox.information(self, "Gallery Saved", f"Gallery '{name}' has been saved successfully!")
                self.accept()
            else:
                QMessageBox.warning(self, "Save Failed", "Failed to save the gallery. Please try again.")
                
        except Exception as e:
            logging.error(f"Error saving gallery: {e}")
            QMessageBox.critical(self, "Save Error", f"Failed to save gallery: {str(e)}") 