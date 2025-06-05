"""
Post Preview Dialog - Shows the complete post with image, caption, and posting options.
"""

import os
import logging
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QGroupBox, QCheckBox, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont

from ..components.adjustable_button import AdjustableButton

class PostPreviewDialog(QDialog):
    """Dialog showing complete post preview with image, caption, and posting options."""
    
    # Signals
    post_now = Signal(dict)  # Post immediately
    add_to_queue = Signal(dict)  # Add to schedule queue
    edit_post = Signal(dict)  # Edit post
    delete_post = Signal(dict)  # Delete post
    
    def __init__(self, parent=None, post_data: Optional[Dict[str, Any]] = None, media_handler=None):
        super().__init__(parent)
        self.post_data = post_data or {}
        self.media_handler = media_handler
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.setWindowTitle("Post Preview")
        self.setMinimumSize(600, 800)
        self.setMaximumSize(800, 1000)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: white;
            }
            QLabel {
                color: white;
            }
            QCheckBox {
                color: white;
                font-size: 14px;
            }
            QGroupBox {
                border: 1px solid #444444;
                border-radius: 8px;
                margin-top: 15px;
                font-weight: bold;
                color: white;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QScrollArea {
                border: none;
                background-color: #2a2a2a;
            }
            QFrame#postFrame {
                background-color: #2a2a2a;
                border: 1px solid #444444;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header_label = QLabel("Post Preview")
        header_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)
        
        # Scroll area for the post content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Post content widget
        post_widget = QFrame()
        post_widget.setObjectName("postFrame")
        post_layout = QVBoxLayout(post_widget)
        post_layout.setSpacing(15)
        
        # Media preview
        self._create_media_preview(post_layout)
        
        # Caption
        self._create_caption_section(post_layout)
        
        scroll_area.setWidget(post_widget)
        layout.addWidget(scroll_area)
        
        # Posting options
        self._create_posting_options(layout)
        
        # Action buttons
        self._create_action_buttons(layout)
    
    def _create_media_preview(self, layout):
        """Create the media preview section."""
        media_path = self.post_data.get("media_path", "")
        
        if not media_path or not os.path.exists(media_path):
            error_label = QLabel("Media file not found")
            error_label.setStyleSheet("color: #ff6b6b; font-size: 14px; padding: 20px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(error_label)
            return
        
        # Media container
        media_frame = QFrame()
        media_frame.setStyleSheet("background-color: #333333; border-radius: 8px; padding: 10px;")
        media_layout = QVBoxLayout(media_frame)
        
        # Load and display image
        try:
            if self.media_handler:
                pil_image = self.media_handler.load_image(media_path)
                if pil_image:
                    # Convert PIL to QPixmap
                    from ...handlers.media_handler import pil_to_qpixmap
                    pixmap = pil_to_qpixmap(pil_image)
                    
                    if pixmap and not pixmap.isNull():
                        # Scale image to fit nicely in preview
                        max_width = 500
                        max_height = 400
                        
                        scaled_pixmap = pixmap.scaled(
                            max_width, max_height,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        
                        image_label = QLabel()
                        image_label.setPixmap(scaled_pixmap)
                        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        image_label.setStyleSheet("border: 1px solid #555555; border-radius: 4px;")
                        media_layout.addWidget(image_label)
                    else:
                        self._add_error_placeholder(media_layout, "Could not load image")
                else:
                    self._add_error_placeholder(media_layout, "Could not process image")
            else:
                # Fallback: try to load with QPixmap directly
                pixmap = QPixmap(media_path)
                if not pixmap.isNull():
                    max_width = 500
                    max_height = 400
                    
                    scaled_pixmap = pixmap.scaled(
                        max_width, max_height,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    image_label = QLabel()
                    image_label.setPixmap(scaled_pixmap)
                    image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    image_label.setStyleSheet("border: 1px solid #555555; border-radius: 4px;")
                    media_layout.addWidget(image_label)
                else:
                    self._add_error_placeholder(media_layout, "Could not load image file")
                    
        except Exception as e:
            self.logger.error(f"Error loading media preview: {e}")
            self._add_error_placeholder(media_layout, f"Error loading media: {str(e)}")
        
        layout.addWidget(media_frame)
    
    def _add_error_placeholder(self, layout, message):
        """Add an error placeholder when image can't be loaded."""
        error_label = QLabel(message)
        error_label.setStyleSheet("""
            color: #ff6b6b; 
            font-size: 14px; 
            padding: 40px; 
            border: 2px dashed #555555; 
            border-radius: 8px;
            background-color: #2a2a2a;
        """)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(error_label)
    
    def _create_caption_section(self, layout):
        """Create the caption display section."""
        caption = self.post_data.get("caption", "")
        
        caption_frame = QFrame()
        caption_frame.setStyleSheet("background-color: #333333; border-radius: 8px; padding: 15px;")
        caption_layout = QVBoxLayout(caption_frame)
        
        # Caption header
        caption_header = QLabel("Caption")
        caption_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF; margin-bottom: 8px;")
        caption_layout.addWidget(caption_header)
        
        # Caption text
        if caption:
            caption_label = QLabel(caption)
            caption_label.setWordWrap(True)
            caption_label.setStyleSheet("""
                color: #EEEEEE; 
                font-size: 14px; 
                line-height: 1.4;
                padding: 10px;
                background-color: #2a2a2a;
                border-radius: 6px;
                border: 1px solid #444444;
            """)
            caption_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        else:
            caption_label = QLabel("No caption")
            caption_label.setStyleSheet("color: #888888; font-style: italic; font-size: 14px; padding: 10px;")
        
        caption_layout.addWidget(caption_label)
        layout.addWidget(caption_frame)
    
    def _create_posting_options(self, layout):
        """Create the posting options section."""
        # Post Now Section
        post_now_group = QGroupBox("Post Now")
        post_now_layout = QVBoxLayout(post_now_group)
        
        # Create a grid layout for better organization
        platform_grid = QGridLayout()
        
        # Row 1: Meta platforms
        self.fb_checkbox = QCheckBox("Post to Facebook")
        self.fb_checkbox.setChecked(True)
        platform_grid.addWidget(self.fb_checkbox, 0, 0)
        
        self.ig_checkbox = QCheckBox("Post to Instagram")
        self.ig_checkbox.setChecked(True)
        platform_grid.addWidget(self.ig_checkbox, 0, 1)
        
        # Row 2: Professional platforms

        
        # Row 2: New platforms
        self.tiktok_checkbox = QCheckBox("Post to TikTok")
        self.tiktok_checkbox.setChecked(False)
        platform_grid.addWidget(self.tiktok_checkbox, 1, 0)
        
        self.pinterest_checkbox = QCheckBox("Post to Pinterest")
        self.pinterest_checkbox.setChecked(False)
        platform_grid.addWidget(self.pinterest_checkbox, 1, 1)
        
        # Row 3: Additional platforms
        self.bluesky_checkbox = QCheckBox("Post to BlueSky")
        self.bluesky_checkbox.setChecked(False)
        platform_grid.addWidget(self.bluesky_checkbox, 2, 0)
        
        self.threads_checkbox = QCheckBox("Post to Threads")
        self.threads_checkbox.setChecked(False)
        platform_grid.addWidget(self.threads_checkbox, 2, 1)
        
        # Row 4: Business platforms
        self.google_business_checkbox = QCheckBox("Post to Google My Business")
        self.google_business_checkbox.setChecked(False)
        platform_grid.addWidget(self.google_business_checkbox, 3, 0)
        
        post_now_layout.addLayout(platform_grid)
        
        # Post Now button
        self.post_now_btn = AdjustableButton("Post Now")
        self.post_now_btn.setStyleSheet("""
            AdjustableButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            AdjustableButton:hover {
                background-color: #45a049;
            }
        """)
        self.post_now_btn.clicked.connect(self._on_post_now)
        post_now_layout.addWidget(self.post_now_btn)
        
        layout.addWidget(post_now_group)
        
        # Queue Section
        queue_group = QGroupBox("Add to Queue")
        queue_layout = QVBoxLayout(queue_group)
        
        queue_info = QLabel("Add this post to the next available slot in the publishing queue.")
        queue_info.setWordWrap(True)
        queue_info.setStyleSheet("color: #CCCCCC; font-size: 13px; margin-bottom: 10px;")
        queue_layout.addWidget(queue_info)
        
        self.queue_btn = AdjustableButton("Add to Queue")
        self.queue_btn.setStyleSheet("""
            AdjustableButton {
                background-color: #3949AB;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            AdjustableButton:hover {
                background-color: #303F9F;
            }
        """)
        self.queue_btn.clicked.connect(self._on_add_to_queue)
        queue_layout.addWidget(self.queue_btn)
        
        layout.addWidget(queue_group)
    
    def _create_action_buttons(self, layout):
        """Create the action buttons section."""
        # Action buttons layout
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        # Edit button
        edit_btn = AdjustableButton("Edit Post")
        edit_btn.setStyleSheet("""
            AdjustableButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            AdjustableButton:hover {
                background-color: #F57C00;
            }
        """)
        edit_btn.clicked.connect(self._on_edit_post)
        action_layout.addWidget(edit_btn)
        
        # Delete button
        delete_btn = AdjustableButton("Delete Post")
        delete_btn.setStyleSheet("""
            AdjustableButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            AdjustableButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_btn.clicked.connect(self._on_delete_post)
        action_layout.addWidget(delete_btn)
        
        action_layout.addStretch()
        
        # Cancel button
        cancel_btn = AdjustableButton("Cancel")
        cancel_btn.setStyleSheet("""
            AdjustableButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
            }
            AdjustableButton:hover {
                background-color: #6b7280cc;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        action_layout.addWidget(cancel_btn)
        
        layout.addLayout(action_layout)
    
    def _on_post_now(self):
        """Handle post now button click."""
        if not (self.fb_checkbox.isChecked() or self.ig_checkbox.isChecked() or 
                self.tiktok_checkbox.isChecked() or self.pinterest_checkbox.isChecked() or
                self.bluesky_checkbox.isChecked() or self.threads_checkbox.isChecked() or
                self.google_business_checkbox.isChecked()):
            QMessageBox.warning(self, "Post Error", "Please select at least one platform to post to.")
            return
            
        platforms = []
        if self.fb_checkbox.isChecked():
            platforms.append("facebook")
        if self.ig_checkbox.isChecked():
            platforms.append("instagram")

        if self.tiktok_checkbox.isChecked():
            platforms.append("tiktok")
        if self.pinterest_checkbox.isChecked():
            platforms.append("pinterest")
        if self.bluesky_checkbox.isChecked():
            platforms.append("bluesky")
        if self.threads_checkbox.isChecked():
            platforms.append("threads")
        if self.google_business_checkbox.isChecked():
            platforms.append("google_business")
            
        # Add platforms to post data
        post_data = self.post_data.copy()
        post_data["platforms"] = platforms
        
        # Emit signal
        self.post_now.emit(post_data)
        self.accept()
        
    def _on_add_to_queue(self):
        """Handle add to queue button click."""
        self.add_to_queue.emit(self.post_data)
        self.accept()
        
    def _on_edit_post(self):
        """Handle edit post button click."""
        self.edit_post.emit(self.post_data)
        self.accept()
        
    def _on_delete_post(self):
        """Handle delete post button click."""
        result = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this post? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            self.delete_post.emit(self.post_data)
            self.accept() 