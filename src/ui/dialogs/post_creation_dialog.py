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
    QListWidget, QListWidgetItem, QMessageBox, QProgressBar, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QPixmap, QFont

from ..base_dialog import BaseDialog
from ...handlers.library_handler import LibraryManager
from ...features.media_processing.image_edit_handler import ImageEditHandler
from ...api.ai.ai_handler import AIHandler
from ...models.app_state import AppState
from ..widgets.loading_screen import CartoonLoadingScreen


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
        
        # Initialize AI handler for caption generation
        self.app_state = AppState()
        if self.media_path:
            self.app_state.selected_media = self.media_path
        self.ai_handler = AIHandler(self.app_state)
        
        # Loading screen will be created when needed
        self.loading_screen = None
        
        # UI components
        self.media_preview = None
        self.caption_edit = None
        self.instructions_edit = None
        self.editing_instructions_edit = None
        self.context_files_list = None
        self.progress_bar = None
        self.keep_caption_checkbox = None  # Initialize checkbox
        self.imagen_overwrite_checkbox = None  # Initialize AI enhancement checkbox
        
        # Data
        self.context_files = []
        self.is_video = False
        self.original_media_path = None  # Store original path
        self.edited_media_path = None    # Store edited path
        self.showing_original = True     # Track which version is displayed
        
        if self.media_path:
            self.original_media_path = self.media_path
            self.is_video = any(self.media_path.lower().endswith(ext) 
                              for ext in ['.mp4', '.mov', '.avi', '.mkv', '.wmv'])
            # Set the original image in the handler
            self.image_edit_handler.set_new_original_image(self.media_path)
        
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
        
        # Generate button (for both images and videos)
        if self.media_path:
            generate_btn = QPushButton("Generate")
            generate_btn.setStyleSheet("""
                QPushButton {
                    background-color: #7c3aed;
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #6d28d9;
                }
            """)
            generate_btn.clicked.connect(self._generate_content)
            button_layout.addWidget(generate_btn)
        
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
        
        # Toggle button for original/edited view (initially hidden)
        self.toggle_button = QPushButton("Show Edited Version")
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.toggle_button.clicked.connect(self._toggle_preview)
        self.toggle_button.setVisible(False)  # Hidden until we have both versions
        layout.addWidget(self.toggle_button)
        
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
        
        # Caption section with keep caption toggle
        caption_group = QGroupBox("Caption")
        caption_layout = QVBoxLayout(caption_group)
        
        # Keep caption toggle
        self.keep_caption_checkbox = QCheckBox("Keep existing caption (don't generate new one)")
        self.keep_caption_checkbox.setStyleSheet("color: #666666; font-size: 12px; margin-bottom: 5px;")
        caption_layout.addWidget(self.keep_caption_checkbox)
        
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
        
        # Image/Video editing instructions section with presets
        editing_group = QGroupBox("Image/Video Editing Instructions")
        editing_layout = QVBoxLayout(editing_group)
        
        # Preset buttons for image editing (only show for images)
        if not self.is_video:
            presets_layout = QHBoxLayout()
            presets_label = QLabel("Marketing Presets:")
            presets_label.setStyleSheet("font-weight: bold; color: #333333; margin-bottom: 5px;")
            editing_layout.addWidget(presets_label)
            
            # Create preset buttons
            presets = [
                ("Professional", "Enhance colors and contrast, sharpen details, apply professional food photography enhancement"),
                ("Warm & Cozy", "Apply warm tone, enhance brightness, add soft lighting for a cozy feel"),
                ("Vibrant", "Boost saturation and vibrancy, enhance colors dramatically for eye-catching social media"),
                ("Vintage", "Apply vintage sepia effect, reduce contrast for retro marketing appeal"),
                ("Studio Ghibli", "Apply anime-style transformation with enhanced colors and soft aesthetic"),
                ("Oil Painting", "Transform into artistic oil painting style for premium brand appeal")
            ]
            
            preset_buttons = []
            for i, (name, instruction) in enumerate(presets):
                if i % 3 == 0:  # New row every 3 buttons
                    if i > 0:
                        editing_layout.addLayout(presets_layout)
                    presets_layout = QHBoxLayout()
                
                preset_btn = QPushButton(name)
                preset_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f8f9fa;
                        color: #495057;
                        border: 1px solid #dee2e6;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #e9ecef;
                        border-color: #adb5bd;
                    }
                    QPushButton:pressed {
                        background-color: #dee2e6;
                    }
                """)
                preset_btn.clicked.connect(lambda checked, instr=instruction: self.editing_instructions_edit.setPlainText(instr))
                presets_layout.addWidget(preset_btn)
                preset_buttons.append(preset_btn)
            
            # Add the last row
            editing_layout.addLayout(presets_layout)
        
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
                "Enter image editing instructions or use presets above...\n\n"
                "Examples:\n"
                "• Enhance colors and contrast\n"
                "• Add a warm filter\n"
                "• Sharpen details\n"
                "• Apply food photography enhancement"
            )
        
        self.editing_instructions_edit.setPlaceholderText(placeholder)
        self.editing_instructions_edit.setMaximumHeight(120)
        editing_layout.addWidget(self.editing_instructions_edit)
        
        # Add toggle for AI image enhancement (only for images)
        if not self.is_video:
            self.imagen_overwrite_checkbox = QCheckBox("✨ Fully enhance with AI (creates stunning new version)")
            self.imagen_overwrite_checkbox.setStyleSheet("""
                QCheckBox {
                    color: #2c3e50; 
                    font-size: 12px; 
                    margin-top: 5px;
                    font-weight: bold;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
                QCheckBox::indicator:unchecked {
                    border: 2px solid #cccccc;
                    background-color: white;
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    border: 2px solid #3498db;
                    background-color: #3498db;
                    border-radius: 3px;
                }
            """)
            self.imagen_overwrite_checkbox.setToolTip(
                "When checked: AI will create a stunning new version of your image based on your instructions\n"
                "When unchecked: Traditional editing will be applied (brightness, contrast, filters, etc.)"
            )
            editing_layout.addWidget(self.imagen_overwrite_checkbox)
        else:
            self.imagen_overwrite_checkbox = None
        
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
                # For videos, try to generate and show a thumbnail
                try:
                    from ...utils.video_thumbnail_generator import VideoThumbnailGenerator
                    thumbnail_generator = VideoThumbnailGenerator()
                    
                    # Try to generate a thumbnail
                    thumbnail = thumbnail_generator.create_video_preview_pixmap(
                        self.media_path, size=(400, 300)
                    )
                    
                    if thumbnail and not thumbnail.isNull():
                        # Scale thumbnail to fit preview area while maintaining aspect ratio
                        scaled_thumbnail = thumbnail.scaled(
                            400, 300, 
                            Qt.AspectRatioMode.KeepAspectRatio, 
                            Qt.TransformationMode.SmoothTransformation
                        )
                        self.media_preview.setPixmap(scaled_thumbnail)
                        self.media_preview.setStyleSheet("""
                            QLabel {
                                border: 2px solid #4CAF50;
                                border-radius: 10px;
                                background-color: #f0f8f0;
                            }
                        """)
                    else:
                        # Fallback to text if thumbnail generation fails
                        self._show_video_text_preview()
                        
                except Exception as e:
                    self.logger.warning(f"Could not generate video thumbnail: {e}")
                    # Fallback to text preview
                    self._show_video_text_preview()
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
            
            # Update media info with version indicator
            file_size = os.path.getsize(self.media_path)
            file_size_mb = file_size / (1024 * 1024)
            
            media_type = "Video" if self.is_video else "Image"
            version_text = ""
            if not self.is_video and self.edited_media_path:
                version_text = f" ({'Original' if self.showing_original else 'Edited'})"
            
            self.media_info_label.setText(
                f"{media_type}: {os.path.basename(self.media_path)}{version_text}\n"
                f"Size: {file_size_mb:.1f} MB"
            )
            
        except Exception as e:
            self.logger.error(f"Error loading media preview: {e}")
            self.media_preview.setText("❌ Error loading media")
    
    def _show_video_text_preview(self):
        """Show a text-based video preview as fallback."""
        try:
            from ...features.media_processing.video_handler import VideoHandler
            video_handler = VideoHandler()
            video_info = video_handler.get_video_info(self.media_path)
            
            if video_info:
                duration_min = int(video_info["duration"] // 60)
                duration_sec = int(video_info["duration"] % 60)
                
                preview_text = f"""🎬 Video File

{os.path.basename(self.media_path)}

Resolution: {video_info['width']}x{video_info['height']}
Duration: {duration_min}:{duration_sec:02d}
Size: {video_info['file_size'] / (1024*1024):.1f} MB

Ready for processing"""
            else:
                preview_text = f"🎬 Video File\n\n{os.path.basename(self.media_path)}"
            
            self.media_preview.setText(preview_text)
            self.media_preview.setStyleSheet("""
                QLabel {
                    border: 2px solid #4CAF50;
                    border-radius: 10px;
                    background-color: #f0f8f0;
                    font-size: 14px;
                    min-height: 300px;
                }
            """)
            
        except Exception as e:
            self.logger.warning(f"Could not get video info: {e}")
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
    
    def _toggle_preview(self):
        """Toggle between original and edited image preview."""
        if not self.original_media_path or not self.edited_media_path:
            return
            
        if self.showing_original:
            # Switch to edited version
            self.media_path = self.edited_media_path
            self.showing_original = False
            self.toggle_button.setText("Show Original Version")
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 12px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
        else:
            # Switch to original version
            self.media_path = self.original_media_path
            self.showing_original = True
            self.toggle_button.setText("Show Edited Version")
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 12px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        
        # Reload the preview with the new image
        self._load_media_preview()
            
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
            self.original_media_path = file_path
            self.edited_media_path = None
            self.showing_original = True
            self.is_video = any(file_path.lower().endswith(ext) 
                              for ext in ['.mp4', '.mov', '.avi', '.mkv', '.wmv'])
            
            # Reset the image edit handler to use the new original image
            self.image_edit_handler.set_new_original_image(file_path)
            
            # Hide toggle button until we have an edited version
            self.toggle_button.setVisible(False)
            
            # Update app state with new media
            self.app_state.selected_media = file_path
            
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
                    "Enter image editing instructions or use presets above...\n\n"
                    "Examples:\n"
                    "• Enhance colors and contrast\n"
                    "• Add a warm filter\n"
                    "• Sharpen details\n"
                    "• Apply food photography enhancement"
                )
            self.editing_instructions_edit.setPlaceholderText(placeholder)
            
    def _generate_content(self):
        """Generate content based on the current post data."""
        if not self.media_path:
            QMessageBox.warning(self, "No Media", "Please select a media file first.")
            return
            
        caption = self.caption_edit.toPlainText().strip()
        instructions = self.instructions_edit.toPlainText().strip()
        editing_instructions = self.editing_instructions_edit.toPlainText().strip()
        keep_caption = self.keep_caption_checkbox.isChecked()
        
        # Disable all UI elements to prevent user interaction
        self.setEnabled(False)
        
        # Create loading screen but don't show it yet
        if not self.loading_screen:
            self.loading_screen = CartoonLoadingScreen(self)
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        try:
            # Update app state with current media
            self.app_state.selected_media = self.media_path
            
            # Generate caption if not keeping existing caption and (instructions provided or caption is empty)
            if not keep_caption and (instructions or not caption):
                self.logger.info("Generating caption with AI...")
                
                # Show loading screen for AI caption generation
                self.loading_screen.show_loading("✨ Crafting the perfect caption...")
                
                # Use instructions or default prompt for caption generation
                caption_instructions = instructions if instructions else "Create an engaging social media caption for this content"
                
                # Generate caption using AI handler
                generated_caption = self.ai_handler.generate_caption(
                    caption_instructions,
                    editing_instructions,
                    self.context_files,
                    keep_existing_caption=False,
                    language_code="en"
                )
                
                # Hide loading screen immediately after caption generation
                self.loading_screen.hide_loading()
                
                if generated_caption:
                    self.caption_edit.setPlainText(generated_caption)
                    self.logger.info("Caption generated successfully")
                else:
                    self.logger.warning("Caption generation failed")
            elif keep_caption:
                self.logger.info("Keeping existing caption as requested")
            
            # Apply image/video editing if instructions are provided
            if editing_instructions:
                if not self.is_video:
                    self.logger.info("Applying image edits...")
                    
                    # Use the original image for editing
                    source_path = self.original_media_path if self.original_media_path else self.media_path
                    
                    # Check if AI image enhancement is enabled
                    use_imagen_overwrite = (self.imagen_overwrite_checkbox and 
                                          self.imagen_overwrite_checkbox.isChecked())
                    
                    if use_imagen_overwrite:
                        # Show loading screen for AI image generation
                        self.loading_screen.show_loading("🎨 Creating your stunning enhanced image...")
                        
                        # Use AI image generation (Imagen) for complete enhancement
                        success, edited_path, message = self.image_edit_handler.edit_image_with_gemini(
                            source_path, 
                            editing_instructions
                        )
                        
                        # Hide loading screen immediately after AI operation
                        self.loading_screen.hide_loading()
                    else:
                        # Use traditional image editing (brightness, contrast, filters, etc.)
                        # No loading screen needed for traditional editing as it's fast
                        success, edited_path, message = self.image_edit_handler.apply_traditional_edits(
                            source_path, 
                            editing_instructions
                        )
                    
                    if success and edited_path and os.path.exists(edited_path):
                        # Store the edited version
                        self.edited_media_path = edited_path
                        
                        # Switch to showing the edited version
                        self.media_path = edited_path
                        self.showing_original = False
                        self.app_state.selected_media = edited_path
                        
                        # Show the toggle button now that we have both versions
                        self.toggle_button.setVisible(True)
                        self.toggle_button.setText("Show Original Version")
                        self.toggle_button.setStyleSheet("""
                            QPushButton {
                                background-color: #FF9800;
                                color: white;
                                border: none;
                                border-radius: 6px;
                                padding: 8px 16px;
                                font-size: 12px;
                                font-weight: bold;
                                margin-bottom: 10px;
                            }
                            QPushButton:hover {
                                background-color: #F57C00;
                            }
                        """)
                        
                        self._load_media_preview()
                        self.logger.info("Image editing completed successfully")
                        
                        # Determine if this was AI generation or traditional editing
                        is_ai_generated = "Imagen 3" in message or "AI image generated" in message
                        generation_type = "AI-generated" if is_ai_generated else "edited"
                        
                        QMessageBox.information(
                            self, 
                            "Content Generation Complete", 
                            f"Content has been generated successfully!\n\n"
                            f"Image {generation_type}: {message}\n"
                            f"Use the toggle button to switch between original and {generation_type} versions.\n"
                            f"{'Caption generated and ' if not keep_caption and (instructions or not caption) else ''}ready for posting."
                        )
                    else:
                        self.logger.warning(f"Image editing failed: {message}")
                        QMessageBox.warning(
                            self, 
                            "Image Editing Failed", 
                            f"Image editing failed: {message}\n\n"
                            f"The original image will be used. "
                            f"{'Caption was ' if not keep_caption and (instructions or not caption) else 'Content is '}still generated successfully."
                        )
                else:
                    self.logger.info("Video editing instructions noted (will be applied during processing)")
                    QMessageBox.information(
                        self, 
                        "Content Generation Complete", 
                        "Content has been generated successfully!\n\n"
                        "Video editing instructions have been saved and will be applied during video processing.\n"
                        f"{'Caption generated and ' if not keep_caption and (instructions or not caption) else ''}ready for posting."
                    )
            else:
                # No editing instructions, just caption generation
                QMessageBox.information(
                    self, 
                    "Content Generation Complete", 
                    f"{'Caption generated successfully!' if not keep_caption and (instructions or not caption) else 'Content is ready!'}\n\n"
                    "You can now add this to your library or make further adjustments."
                )
                
        except Exception as e:
            self.logger.error(f"Error generating content: {e}")
            QMessageBox.critical(
                self, 
                "Content Generation Error", 
                f"An error occurred while generating content: {str(e)}"
            )
        finally:
            # Re-enable UI elements
            self.setEnabled(True)
            
            # Hide loading screen (in case it's still showing due to an error)
            if self.loading_screen:
                self.loading_screen.hide_loading()
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
            "original_media_path": self.original_media_path,
            "edited_media_path": self.edited_media_path,
            "showing_original": self.showing_original,
            "caption": self.caption_edit.toPlainText().strip(),
            "instructions": self.instructions_edit.toPlainText().strip(),
            "editing_instructions": self.editing_instructions_edit.toPlainText().strip(),
            "context_files": self.context_files.copy(),
            "is_video": self.is_video
        } 