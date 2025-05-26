"""
Gallery Creation Dialog - Handles the workflow of creating galleries with carousel preview and caption generation
"""
import os
import logging
from typing import List, Dict, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QLineEdit, QScrollArea, QWidget, QMessageBox,
    QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QImage

from PIL import Image as PILImage

from ...api.ai.crowseye_handler import CrowsEyeHandler
from ..base_dialog import BaseDialog


class MediaCarouselWidget(QWidget):
    """Widget for displaying a carousel of selected media items."""
    
    def __init__(self, media_paths: List[str], parent=None):
        super().__init__(parent)
        self.media_paths = media_paths
        self.current_index = 0
        self.setFixedSize(400, 300)
        self._create_ui()
        self._load_current_media()
    
    def _create_ui(self):
        layout = QVBoxLayout(self)
        
        # Navigation header
        nav_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("◀")
        self.prev_button.setFixedSize(30, 30)
        self.prev_button.clicked.connect(self._prev_media)
        nav_layout.addWidget(self.prev_button)
        
        self.media_counter = QLabel()
        self.media_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_counter.setStyleSheet("color: #FFFFFF; font-size: 12px;")
        nav_layout.addWidget(self.media_counter)
        
        self.next_button = QPushButton("▶")
        self.next_button.setFixedSize(30, 30)
        self.next_button.clicked.connect(self._next_media)
        nav_layout.addWidget(self.next_button)
        
        layout.addLayout(nav_layout)
        
        # Media display
        self.media_label = QLabel()
        self.media_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_label.setStyleSheet("border: 2px solid #333; border-radius: 8px; background-color: #1a1a1a;")
        self.media_label.setMinimumSize(380, 250)
        layout.addWidget(self.media_label)
        
        # Update navigation state
        self._update_navigation()
    
    def _update_navigation(self):
        """Update navigation buttons and counter."""
        total = len(self.media_paths)
        if total == 0:
            self.media_counter.setText("No media")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
        else:
            self.media_counter.setText(f"{self.current_index + 1} of {total}")
            self.prev_button.setEnabled(self.current_index > 0)
            self.next_button.setEnabled(self.current_index < total - 1)
    
    def _prev_media(self):
        """Show previous media item."""
        if self.current_index > 0:
            self.current_index -= 1
            self._load_current_media()
            self._update_navigation()
    
    def _next_media(self):
        """Show next media item."""
        if self.current_index < len(self.media_paths) - 1:
            self.current_index += 1
            self._load_current_media()
            self._update_navigation()
    
    def _load_current_media(self):
        """Load and display the current media item."""
        if not self.media_paths or self.current_index >= len(self.media_paths):
            self.media_label.setText("No media to display")
            return
        
        media_path = self.media_paths[self.current_index]
        
        try:
            if media_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                # Video placeholder
                self.media_label.setText("🎥\nVideo Preview\n" + os.path.basename(media_path))
                self.media_label.setStyleSheet("border: 2px solid #333; border-radius: 8px; background-color: #1a1a1a; color: #FFFFFF; font-size: 14px;")
            else:
                # Load image
                with PILImage.open(media_path) as img:
                    if img.mode not in ('RGB', 'L'):
                        img = img.convert('RGB')
                    
                    img_copy = img.copy()
                    
                    # Calculate scaling to fit within 380x250
                    img_width, img_height = img_copy.size
                    target_width, target_height = 380, 250
                    
                    scale_w = target_width / img_width
                    scale_h = target_height / img_height
                    scale = min(scale_w, scale_h)
                    
                    new_width = int(img_width * scale)
                    new_height = int(img_height * scale)
                    
                    img_resized = img_copy.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
                    
                    # Convert to QPixmap
                    rgb_image = img_resized.convert('RGB')
                    width, height = rgb_image.size
                    rgb_data = rgb_image.tobytes("raw", "RGB")
                    
                    qimg = QImage(rgb_data, width, height, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimg)
                    
                    self.media_label.setPixmap(pixmap)
                    
        except Exception as e:
            logging.error(f"Error loading media preview for {media_path}: {e}")
            self.media_label.setText("⚠️\nError loading media")
            self.media_label.setStyleSheet("border: 2px solid #333; border-radius: 8px; background-color: #1a1a1a; color: #FFB347;")


class GalleryCreationDialog(BaseDialog):
    """Dialog for creating galleries with carousel preview and caption generation."""
    
    gallery_created = Signal(dict)  # Emits the created gallery data
    
    def __init__(self, selected_media: List[str], crowseye_handler: CrowsEyeHandler, parent=None):
        super().__init__(parent)
        self.selected_media = selected_media
        self.crowseye_handler = crowseye_handler
        self.generated_caption = ""
        
        self.setWindowTitle("Create Gallery")
        self.setFixedSize(800, 600)
        self._create_ui()
    
    def _create_ui(self):
        """Create the main UI layout."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Create New Gallery")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        # Main content layout
        content_layout = QHBoxLayout()
        
        # Left side - Carousel
        carousel_frame = QFrame()
        carousel_frame.setStyleSheet("QFrame { border: 1px solid #333; border-radius: 8px; }")
        carousel_layout = QVBoxLayout(carousel_frame)
        
        carousel_title = QLabel("Gallery Preview")
        carousel_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF; margin-bottom: 5px;")
        carousel_layout.addWidget(carousel_title)
        
        # Media carousel
        self.carousel = MediaCarouselWidget(self.selected_media)
        carousel_layout.addWidget(self.carousel)
        
        content_layout.addWidget(carousel_frame)
        
        # Right side - Caption generation
        caption_frame = QFrame()
        caption_frame.setStyleSheet("QFrame { border: 1px solid #333; border-radius: 8px; }")
        caption_layout = QVBoxLayout(caption_frame)
        
        caption_title = QLabel("Caption Generation")
        caption_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF; margin-bottom: 5px;")
        caption_layout.addWidget(caption_title)
        
        # Tone/instructions input
        instructions_label = QLabel("Tone & Instructions:")
        instructions_label.setStyleSheet("color: #FFFFFF; font-size: 12px; margin-bottom: 5px;")
        caption_layout.addWidget(instructions_label)
        
        self.instructions_input = QLineEdit()
        self.instructions_input.setPlaceholderText("e.g., 'energetic and conversational', 'professional tone'")
        self.instructions_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                color: #FFFFFF;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #7c3aed;
            }
        """)
        caption_layout.addWidget(self.instructions_input)
        
        # Generate caption button
        self.generate_caption_button = QPushButton("Generate Caption")
        self.generate_caption_button.clicked.connect(self._generate_caption)
        self.generate_caption_button.setStyleSheet("""
            QPushButton {
                background-color: #6d28d9;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                margin: 10px 0;
            }
            QPushButton:hover {
                background-color: #5b21b6;
            }
        """)
        caption_layout.addWidget(self.generate_caption_button)
        
        # Caption display
        caption_display_label = QLabel("Generated Caption:")
        caption_display_label.setStyleSheet("color: #FFFFFF; font-size: 12px; margin-bottom: 5px;")
        caption_layout.addWidget(caption_display_label)
        
        self.caption_display = QTextEdit()
        self.caption_display.setPlaceholderText("Generated caption will appear here...")
        self.caption_display.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                color: #FFFFFF;
                font-size: 12px;
                min-height: 120px;
            }
            QTextEdit:focus {
                border-color: #7c3aed;
            }
        """)
        caption_layout.addWidget(self.caption_display)
        
        # Gallery name
        name_label = QLabel("Gallery Name:")
        name_label.setStyleSheet("color: #FFFFFF; font-size: 12px; margin-bottom: 5px;")
        caption_layout.addWidget(name_label)
        
        self.gallery_name_input = QLineEdit()
        self.gallery_name_input.setText(f"Gallery_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.gallery_name_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                color: #FFFFFF;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #7c3aed;
            }
        """)
        caption_layout.addWidget(self.gallery_name_input)
        
        content_layout.addWidget(caption_frame)
        layout.addLayout(content_layout)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                margin-right: 8px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        # Save gallery button
        self.save_button = QPushButton("Save Gallery")
        self.save_button.clicked.connect(self._save_gallery)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #047857;
            }
        """)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def _generate_caption(self):
        """Generate a caption for the gallery using AI."""
        try:
            instructions = self.instructions_input.text().strip()
            if not instructions:
                instructions = "engaging and creative"
            
            self.generate_caption_button.setText("Generating...")
            self.generate_caption_button.setEnabled(False)
            
            # Use CrowsEye handler to generate caption
            caption = self.crowseye_handler.generate_caption(self.selected_media, instructions)
            
            if caption:
                self.generated_caption = caption
                self.caption_display.setPlainText(caption)
            else:
                QMessageBox.warning(self, "Caption Generation", "Failed to generate caption. Please try again.")
            
        except Exception as e:
            logging.error(f"Error generating caption: {e}")
            QMessageBox.critical(self, "Error", f"Failed to generate caption: {str(e)}")
        finally:
            self.generate_caption_button.setText("Generate Caption")
            self.generate_caption_button.setEnabled(True)
    
    def _save_gallery(self):
        """Save the gallery."""
        try:
            gallery_name = self.gallery_name_input.text().strip()
            if not gallery_name:
                QMessageBox.warning(self, "Invalid Name", "Please enter a gallery name.")
                return
            
            caption = self.caption_display.toPlainText().strip()
            
            # Save using CrowsEye handler
            success = self.crowseye_handler.save_gallery(gallery_name, self.selected_media, caption)
            
            if success:
                # Emit the gallery data
                gallery_data = {
                    'name': gallery_name,
                    'media_paths': self.selected_media.copy(),
                    'caption': caption,
                    'created_at': datetime.now().isoformat()
                }
                self.gallery_created.emit(gallery_data)
                self.accept()
            else:
                QMessageBox.warning(self, "Save Error", "Failed to save gallery. Please try again.")
                
        except Exception as e:
            logging.error(f"Error saving gallery: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save gallery: {str(e)}") 