"""
Comprehensive Post Creation Dialog
Provides a complete interface for creating posts with media preview, captions, instructions, and context files.
"""
import os
import logging
from typing import List, Optional, Dict, Any

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, 
    QScrollArea, QWidget, QFrame, QSplitter, QGroupBox, QFileDialog,
    QListWidget, QListWidgetItem, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QPixmap, QFont

from ..base_dialog import BaseDialog
from ...handlers.library_handler import LibraryManager
from ...features.media_processing.image_edit_handler import ImageEditHandler


class PostCreationDialog(BaseDialog):
    """Comprehensive dialog for creating posts with full editing capabilities."""
    
    # Signals
    post_created = Signal(str)  # item_id
    add_to_library_requested = Signal(dict)  # post_data
    
    def __init__(self, media_path: str = None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize components
        self.media_path = media_path
        self.library_manager = LibraryManager()
        self.image_edit_handler = ImageEditHandler()
        
        # UI components
        self.media_preview = None
        self.caption_edit = None
        self.instructions_edit = None
        self.editing_instructions_edit = None
        self.context_files_list = None
        self.progress_bar = None
        
        # Data
        self.context_files = []
        self.is_video = False
        
        if self.media_path:
            self.is_video = any(self.media_path.lower().endswith(ext) 
                              for ext in ['.mp4', '.mov', '.avi', '.mkv', '.wmv'])
        
        self._setup_ui()
        if self.media_path:
            self._load_media_preview()
            
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Create Post")
        self.setMinimumSize(1200, 800)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Create Post")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 15px;")
        main_layout.addWidget(title_label)
        
        # Create main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left side - Media preview
        left_widget = self._create_media_preview_widget()
        main_splitter.addWidget(left_widget)
        
        # Right side - Content editing
        right_widget = self._create_content_editing_widget()
        main_splitter.addWidget(right_widget)
        
        # Set splitter proportions (40% media, 60% content)
        main_splitter.setSizes([480, 720])
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Media selection button
        if not self.media_path:
            select_media_btn = QPushButton("Select Media")
            select_media_btn.clicked.connect(self._select_media)
            button_layout.addWidget(select_media_btn)
        else:
            change_media_btn = QPushButton("Change Media")
            change_media_btn.clicked.connect(self._select_media)
            button_layout.addWidget(change_media_btn)
        
        # Process image button (only for images)
        if self.media_path and not self.is_video:
            process_btn = QPushButton("Process Image")
            process_btn.clicked.connect(self._process_image)
            button_layout.addWidget(process_btn)
        
        button_layout.addStretch()
        
        # Add to Library button
        add_to_library_btn = QPushButton("Add to Library")
        add_to_library_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        add_to_library_btn.clicked.connect(self._add_to_library)
        button_layout.addWidget(add_to_library_btn)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(button_layout)
        
    def _create_media_preview_widget(self):
        """Create the media preview widget."""
        group = QGroupBox("Media Preview")
        layout = QVBoxLayout(group)
        
        # Scroll area for preview
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(400)
        
        # Preview widget
        self.media_preview = QLabel()
        self.media_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_preview.setStyleSheet("""
            QLabel {
                border: 2px dashed #cccccc;
                border-radius: 10px;
                background-color: #f9f9f9;
                min-height: 300px;
            }
        """)
        
        if not self.media_path:
            self.media_preview.setText("No media selected\n\nClick 'Select Media' to choose a file")
        
        scroll_area.setWidget(self.media_preview)
        layout.addWidget(scroll_area)
        
        # Media info
        self.media_info_label = QLabel()
        self.media_info_label.setStyleSheet("font-size: 12px; color: #666666; margin-top: 10px;")
        layout.addWidget(self.media_info_label)
        
        return group
        
    def _create_content_editing_widget(self):
        """Create the content editing widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Caption section
        caption_group = QGroupBox("Caption")
        caption_layout = QVBoxLayout(caption_group)
        
        self.caption_edit = QTextEdit()
        self.caption_edit.setPlaceholderText(
            "Write your post caption here...\n\n"
            "Tips:\n"
            "• Keep it engaging and relevant to your audience\n"
            "• Use hashtags strategically\n"
            "• Include a call-to-action if appropriate"
        )
        self.caption_edit.setMaximumHeight(150)
        caption_layout.addWidget(self.caption_edit)
        
        layout.addWidget(caption_group)
        
        # Instructions section
        instructions_group = QGroupBox("General Instructions")
        instructions_layout = QVBoxLayout(instructions_group)
        
        self.instructions_edit = QTextEdit()
        self.instructions_edit.setPlaceholderText(
            "Enter general instructions for this post...\n\n"
            "Examples:\n"
            "• Target audience: food enthusiasts\n"
            "• Tone: casual and friendly\n"
            "• Focus on the artisanal bread-making process"
        )
        self.instructions_edit.setMaximumHeight(120)
        instructions_layout.addWidget(self.instructions_edit)
        
        layout.addWidget(instructions_group)
        
        # Image/Video editing instructions section
        editing_group = QGroupBox("Image/Video Editing Instructions")
        editing_layout = QVBoxLayout(editing_group)
        
        self.editing_instructions_edit = QTextEdit()
        if self.is_video:
            placeholder = (
                "Enter video editing instructions...\n\n"
                "Examples:\n"
                "• Add warm color grading\n"
                "• Increase brightness slightly\n"
                "• Add subtle background music\n"
                "• Create a 15-second highlight reel"
            )
        else:
            placeholder = (
                "Enter image editing instructions...\n\n"
                "Examples:\n"
                "• Enhance colors and contrast\n"
                "• Add a warm filter\n"
                "• Sharpen details\n"
                "• Apply food photography enhancement"
            )
        
        self.editing_instructions_edit.setPlaceholderText(placeholder)
        self.editing_instructions_edit.setMaximumHeight(120)
        editing_layout.addWidget(self.editing_instructions_edit)
        
        layout.addWidget(editing_group)
        
        # Context files section
        context_group = QGroupBox("Context Files")
        context_layout = QVBoxLayout(context_group)
        
        # Context files list
        self.context_files_list = QListWidget()
        self.context_files_list.setMaximumHeight(120)
        context_layout.addWidget(self.context_files_list)
        
        # Context files buttons
        context_buttons_layout = QHBoxLayout()
        
        add_file_btn = QPushButton("Add File")
        add_file_btn.clicked.connect(self._add_context_file)
        context_buttons_layout.addWidget(add_file_btn)
        
        remove_file_btn = QPushButton("Remove Selected")
        remove_file_btn.clicked.connect(self._remove_context_file)
        context_buttons_layout.addWidget(remove_file_btn)
        
        clear_files_btn = QPushButton("Clear All")
        clear_files_btn.clicked.connect(self._clear_context_files)
        context_buttons_layout.addWidget(clear_files_btn)
        
        context_buttons_layout.addStretch()
        
        context_layout.addLayout(context_buttons_layout)
        layout.addWidget(context_group)
        
        return widget
        
    def _load_media_preview(self):
        """Load and display media preview."""
        if not self.media_path or not os.path.exists(self.media_path):
            return
            
        try:
            if self.is_video:
                # For videos, show a placeholder with video info
                self.media_preview.setText(f"🎬 Video File\n\n{os.path.basename(self.media_path)}")
                self.media_preview.setStyleSheet("""
                    QLabel {
                        border: 2px solid #4CAF50;
                        border-radius: 10px;
                        background-color: #f0f8f0;
                        font-size: 16px;
                        min-height: 300px;
                    }
                """)
            else:
                # For images, show the actual image
                pixmap = QPixmap(self.media_path)
                if not pixmap.isNull():
                    # Scale to fit preview area while maintaining aspect ratio
                    scaled_pixmap = pixmap.scaled(
                        400, 400, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.media_preview.setPixmap(scaled_pixmap)
                    self.media_preview.setStyleSheet("""
                        QLabel {
                            border: 2px solid #4CAF50;
                            border-radius: 10px;
                            background-color: #f0f8f0;
                        }
                    """)
                else:
                    self.media_preview.setText("❌ Could not load image")
            
            # Update media info
            file_size = os.path.getsize(self.media_path)
            file_size_mb = file_size / (1024 * 1024)
            
            media_type = "Video" if self.is_video else "Image"
            self.media_info_label.setText(
                f"{media_type}: {os.path.basename(self.media_path)}\n"
                f"Size: {file_size_mb:.1f} MB"
            )
            
        except Exception as e:
            self.logger.error(f"Error loading media preview: {e}")
            self.media_preview.setText("❌ Error loading media")
            
    def _select_media(self):
        """Select a media file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Media File",
            "",
            "Media Files (*.jpg *.jpeg *.png *.gif *.bmp *.mp4 *.mov *.avi *.mkv *.wmv);;All Files (*)"
        )
        
        if file_path:
            self.media_path = file_path
            self.is_video = any(file_path.lower().endswith(ext) 
                              for ext in ['.mp4', '.mov', '.avi', '.mkv', '.wmv'])
            self._load_media_preview()
            
            # Update editing instructions placeholder
            if self.is_video:
                placeholder = (
                    "Enter video editing instructions...\n\n"
                    "Examples:\n"
                    "• Add warm color grading\n"
                    "• Increase brightness slightly\n"
                    "• Add subtle background music\n"
                    "• Create a 15-second highlight reel"
                )
            else:
                placeholder = (
                    "Enter image editing instructions...\n\n"
                    "Examples:\n"
                    "• Enhance colors and contrast\n"
                    "• Add a warm filter\n"
                    "• Sharpen details\n"
                    "• Apply food photography enhancement"
                )
            self.editing_instructions_edit.setPlaceholderText(placeholder)
            
    def _process_image(self):
        """Process the image with editing instructions."""
        if not self.media_path or self.is_video:
            return
            
        editing_instructions = self.editing_instructions_edit.toPlainText().strip()
        if not editing_instructions:
            QMessageBox.information(
                self, 
                "No Instructions", 
                "Please enter image editing instructions before processing."
            )
            return
            
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        try:
            # Process image with Gemini
            self.logger.info(f"Processing image with instructions: {editing_instructions}")
            
            # This would typically be done in a separate thread
            # For now, we'll simulate the process
            processed_path = self.image_edit_handler.edit_image(
                self.media_path, 
                editing_instructions
            )
            
            if processed_path and os.path.exists(processed_path):
                self.media_path = processed_path
                self._load_media_preview()
                QMessageBox.information(
                    self, 
                    "Processing Complete", 
                    "Image has been processed successfully!"
                )
            else:
                QMessageBox.warning(
                    self, 
                    "Processing Failed", 
                    "Image processing failed. The original image will be used."
                )
                
        except Exception as e:
            self.logger.error(f"Error processing image: {e}")
            QMessageBox.critical(
                self, 
                "Processing Error", 
                f"An error occurred while processing the image: {str(e)}"
            )
        finally:
            self.progress_bar.setVisible(False)
            
    def _add_context_file(self):
        """Add a context file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Context File",
            "",
            "All Files (*)"
        )
        
        if file_path and file_path not in self.context_files:
            self.context_files.append(file_path)
            item = QListWidgetItem(os.path.basename(file_path))
            item.setToolTip(file_path)
            self.context_files_list.addItem(item)
            
    def _remove_context_file(self):
        """Remove selected context file."""
        current_row = self.context_files_list.currentRow()
        if current_row >= 0:
            self.context_files.pop(current_row)
            self.context_files_list.takeItem(current_row)
            
    def _clear_context_files(self):
        """Clear all context files."""
        self.context_files.clear()
        self.context_files_list.clear()
        
    def _add_to_library(self):
        """Add the post to the library."""
        if not self.media_path:
            QMessageBox.warning(self, "No Media", "Please select a media file first.")
            return
            
        caption = self.caption_edit.toPlainText().strip()
        instructions = self.instructions_edit.toPlainText().strip()
        editing_instructions = self.editing_instructions_edit.toPlainText().strip()
        
        # Create post data
        post_data = {
            "media_path": self.media_path,
            "caption": caption,
            "instructions": instructions,
            "editing_instructions": editing_instructions,
            "context_files": self.context_files.copy(),
            "is_video": self.is_video
        }
        
        try:
            # Add to library as post-ready item
            metadata = {
                "instructions": instructions,
                "editing_instructions": editing_instructions,
                "context_files": self.context_files
            }
            
            item_id = self.library_manager.add_item_from_path(
                self.media_path,
                caption=caption,
                metadata=metadata,
                is_post_ready=True
            )
            
            if item_id:
                self.post_created.emit(item_id)
                QMessageBox.information(
                    self, 
                    "Success", 
                    "Post has been added to your library!\n\n"
                    "You can now find it in the 'Finished Posts' section."
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self, 
                    "Error", 
                    "Failed to add post to library. Please try again."
                )
                
        except Exception as e:
            self.logger.error(f"Error adding post to library: {e}")
            QMessageBox.critical(
                self, 
                "Error", 
                f"An error occurred while adding the post to library: {str(e)}"
            )
            
    def get_post_data(self) -> Dict[str, Any]:
        """Get the current post data."""
        return {
            "media_path": self.media_path,
            "caption": self.caption_edit.toPlainText().strip(),
            "instructions": self.instructions_edit.toPlainText().strip(),
            "editing_instructions": self.editing_instructions_edit.toPlainText().strip(),
            "context_files": self.context_files.copy(),
            "is_video": self.is_video
        } 