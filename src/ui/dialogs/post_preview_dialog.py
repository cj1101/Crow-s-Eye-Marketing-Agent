"""
Post Preview Dialog - Preview finished posts with publishing options.
"""
import os
import logging
from typing import Dict, Any, List
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QGroupBox, QCheckBox, QTextEdit, QSplitter, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont

from ..base_dialog import BaseDialog

class PostPreviewDialog(BaseDialog):
    """Dialog for previewing finished posts with publishing options."""
    
    # Signals
    post_now_requested = Signal(dict)  # post_data with platforms
    add_to_campaign_requested = Signal(dict)  # post_data with platforms
    schedule_post_requested = Signal(dict)  # post_data with platforms
    edit_post_requested = Signal(dict)  # post_data
    
    def __init__(self, post_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.post_data = post_data
        self.media_path = post_data.get("path", "")
        self.is_video = self._detect_video_type()
        
        # Platform compatibility data with aspect ratio requirements
        self.platform_media_requirements = {
            'instagram': {
                'photos': True, 'videos': True, 'text_only': False,
                'aspect_ratios': ['1:1', '4:5', '9:16'], 'preferred': '1:1'
            },
            'facebook': {
                'photos': True, 'videos': True, 'text_only': True,
                'aspect_ratios': ['16:9', '1:1', '4:5'], 'preferred': '16:9'
            },
            'tiktok': {
                'photos': False, 'videos': True, 'text_only': False,
                'aspect_ratios': ['9:16'], 'preferred': '9:16'
            },
            'youtube': {
                'photos': False, 'videos': True, 'text_only': False,
                'aspect_ratios': ['16:9'], 'preferred': '16:9'
            },
            'pinterest': {
                'photos': True, 'videos': True, 'text_only': False,
                'aspect_ratios': ['2:3', '1:1', '3:4'], 'preferred': '2:3'
            },
            'snapchat': {
                'photos': True, 'videos': True, 'text_only': False,
                'aspect_ratios': ['9:16'], 'preferred': '9:16'
            }
        }
        
        self.setWindowTitle("Post Preview")
        self.setMinimumSize(900, 700)
        self.setModal(True)
        
        self._setup_ui()
        self._setup_platform_compatibility()
        
        self.logger.info(f"Post preview opened for: {self.post_data.get('id', 'unknown')}")
    
    def _detect_video_type(self) -> bool:
        """Detect if the media is a video."""
        if not self.media_path:
            return False
        
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.webm']
        file_ext = os.path.splitext(self.media_path)[1].lower()
        return file_ext in video_extensions
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        main_layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Post Preview")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 15px;")
        main_layout.addWidget(title_label)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left side - Media preview
        left_widget = self._create_media_preview_widget()
        splitter.addWidget(left_widget)
        
        # Right side - Post details and controls
        right_widget = self._create_post_details_widget()
        splitter.addWidget(right_widget)
        
        # Set splitter proportions (60% media, 40% details)
        splitter.setSizes([540, 360])
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        # Edit button
        self.edit_btn = QPushButton("Edit Post")
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                margin-right: 10px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.edit_btn.clicked.connect(self._edit_post)
        button_layout.addWidget(self.edit_btn)
        
        button_layout.addStretch()
        
        # Action buttons
        self.post_now_btn = QPushButton("Post Now")
        self.post_now_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                margin-right: 10px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.post_now_btn.clicked.connect(self._post_now)
        button_layout.addWidget(self.post_now_btn)
        
        self.add_to_campaign_btn = QPushButton("Add to Campaign")
        self.add_to_campaign_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                margin-right: 10px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.add_to_campaign_btn.clicked.connect(self._add_to_campaign)
        button_layout.addWidget(self.add_to_campaign_btn)
        
        self.schedule_post_btn = QPushButton("Schedule Post")
        self.schedule_post_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                margin-right: 10px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        self.schedule_post_btn.clicked.connect(self._schedule_post)
        button_layout.addWidget(self.schedule_post_btn)
        
        # Cancel button
        self.cancel_btn = QPushButton("Close")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
    
    def _create_media_preview_widget(self):
        """Create the media preview widget."""
        group = QGroupBox("Media Preview")
        layout = QVBoxLayout(group)
        
        # Media display
        self.media_label = QLabel()
        self.media_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_label.setMinimumHeight(400)
        self.media_label.setStyleSheet("""
            QLabel {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                background-color: #f8f9fa;
            }
        """)
        
        layout.addWidget(self.media_label)
        
        # Media info
        self.media_info_label = QLabel()
        self.media_info_label.setStyleSheet("color: #666666; font-size: 12px; margin-top: 10px;")
        self.media_info_label.setWordWrap(True)
        layout.addWidget(self.media_info_label)
        
        # Load media after both labels are created
        self._load_media_preview()
        
        return group
    
    def _create_post_details_widget(self):
        """Create the post details and controls widget."""
        widget = QScrollArea()
        widget.setWidgetResizable(True)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Post caption
        caption_group = QGroupBox("Caption")
        caption_layout = QVBoxLayout(caption_group)
        
        self.caption_display = QTextEdit()
        self.caption_display.setPlainText(self.post_data.get("caption", "No caption"))
        self.caption_display.setReadOnly(True)
        self.caption_display.setMaximumHeight(120)
        caption_layout.addWidget(self.caption_display)
        
        layout.addWidget(caption_group)
        
        # Platform selection
        platform_group = QGroupBox("Select Platforms")
        platform_layout = QVBoxLayout(platform_group)
        
        # Use a wrapping layout for platform checkboxes
        platforms_widget = QWidget()
        platforms_layout = QGridLayout(platforms_widget)
        platforms_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create all platform checkboxes
        self.instagram_checkbox = QCheckBox("Instagram")
        self.instagram_checkbox.setChecked(True)
        platforms_layout.addWidget(self.instagram_checkbox, 0, 0)
        
        self.facebook_checkbox = QCheckBox("Facebook")
        self.facebook_checkbox.setChecked(True)
        platforms_layout.addWidget(self.facebook_checkbox, 0, 1)
        
        self.tiktok_checkbox = QCheckBox("TikTok")
        platforms_layout.addWidget(self.tiktok_checkbox, 0, 2)
        
        self.youtube_checkbox = QCheckBox("YouTube")
        platforms_layout.addWidget(self.youtube_checkbox, 1, 0)
        
        self.pinterest_checkbox = QCheckBox("Pinterest")
        platforms_layout.addWidget(self.pinterest_checkbox, 1, 1)
        
        self.snapchat_checkbox = QCheckBox("Snapchat")
        platforms_layout.addWidget(self.snapchat_checkbox, 1, 2)
        
        # Add stretch to the right
        platforms_layout.setColumnStretch(3, 1)
        
        platform_layout.addWidget(platforms_widget)
        
        # Aspect ratio warning
        aspect_warning = QLabel("⚠️ Content will be automatically resized to fit each platform's optimal aspect ratio")
        aspect_warning.setStyleSheet("""
            QLabel {
                color: #f39c12;
                font-size: 11px;
                font-style: italic;
                margin-top: 5px;
                padding: 5px;
                background-color: rgba(243, 156, 18, 0.1);
                border-radius: 3px;
            }
        """)
        aspect_warning.setWordWrap(True)
        platform_layout.addWidget(aspect_warning)
        
        layout.addWidget(platform_group)
        
        # Post metadata
        metadata_group = QGroupBox("Post Information")
        metadata_layout = QVBoxLayout(metadata_group)
        
        # Creation date
        date_created = self.post_data.get("date_added", "Unknown")
        if date_created != "Unknown":
            try:
                parsed_date = datetime.fromisoformat(date_created.replace('Z', '+00:00'))
                date_str = parsed_date.strftime("%B %d, %Y at %I:%M %p")
            except:
                date_str = date_created
        else:
            date_str = "Unknown"
        
        date_label = QLabel(f"Created: {date_str}")
        date_label.setStyleSheet("margin-bottom: 5px;")
        metadata_layout.addWidget(date_label)
        
        # Media type
        media_type = "Video" if self.is_video else "Photo"
        type_label = QLabel(f"Type: {media_type}")
        type_label.setStyleSheet("margin-bottom: 5px;")
        metadata_layout.addWidget(type_label)
        
        # File size if available
        if os.path.exists(self.media_path):
            try:
                file_size = os.path.getsize(self.media_path)
                size_mb = file_size / (1024 * 1024)
                size_label = QLabel(f"Size: {size_mb:.1f} MB")
                size_label.setStyleSheet("margin-bottom: 5px;")
                metadata_layout.addWidget(size_label)
            except:
                pass
        
        # Dimensions if available
        dimensions = self.post_data.get("dimensions", [])
        if dimensions and len(dimensions) >= 2 and dimensions[0] and dimensions[1]:
            dim_label = QLabel(f"Dimensions: {dimensions[0]} × {dimensions[1]}")
            dim_label.setStyleSheet("margin-bottom: 5px;")
            metadata_layout.addWidget(dim_label)
        
        layout.addWidget(metadata_group)
        
        layout.addStretch()
        
        widget.setWidget(content)
        return widget
    
    def _load_media_preview(self):
        """Load and display media preview."""
        if not self.media_path or not os.path.exists(self.media_path):
            self.media_label.setText("Media not found")
            self.media_info_label.setText("File path: " + (self.media_path or "None"))
            return
        
        try:
            if self.is_video:
                # For videos, try to show a thumbnail or placeholder
                self.media_label.setText(f"🎬 Video File\n\n{os.path.basename(self.media_path)}")
                self.media_label.setStyleSheet("""
                    QLabel {
                        border: 2px solid #28a745;
                        border-radius: 8px;
                        background-color: #f8f9fa;
                        font-size: 16px;
                        color: #28a745;
                    }
                """)
            else:
                # For images, show the actual image
                pixmap = QPixmap(self.media_path)
                if not pixmap.isNull():
                    # Scale to fit preview area while maintaining aspect ratio
                    scaled_pixmap = pixmap.scaled(
                        500, 400, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.media_label.setPixmap(scaled_pixmap)
                else:
                    self.media_label.setText("Could not load image")
            
            # Update media info
            file_size = os.path.getsize(self.media_path)
            file_size_mb = file_size / (1024 * 1024)
            self.media_info_label.setText(
                f"File: {os.path.basename(self.media_path)}\n"
                f"Size: {file_size_mb:.1f} MB\n"
                f"Path: {self.media_path}"
            )
            
        except Exception as e:
            self.logger.error(f"Error loading media preview: {e}")
            self.media_label.setText("Error loading media")
            self.media_info_label.setText(f"Error: {str(e)}")
    
    def _setup_platform_compatibility(self):
        """Set up platform compatibility based on media type."""
        media_type = 'videos' if self.is_video else 'photos'
        
        # Check each platform's compatibility
        platforms = {
            'instagram': self.instagram_checkbox,
            'facebook': self.facebook_checkbox,
            'tiktok': self.tiktok_checkbox,
            'youtube': self.youtube_checkbox,
            'pinterest': self.pinterest_checkbox,
            'snapchat': self.snapchat_checkbox
        }
        
        for platform_name, checkbox in platforms.items():
            requirements = self.platform_media_requirements.get(platform_name, {})
            is_compatible = requirements.get(media_type, False)
            
            if not is_compatible:
                checkbox.setChecked(False)
                checkbox.setEnabled(False)
                if platform_name == 'tiktok' and not self.is_video:
                    checkbox.setToolTip("TikTok requires video content")
                elif platform_name == 'instagram' and not self.media_path:
                    checkbox.setToolTip("Instagram requires media content")
            else:
                checkbox.setEnabled(True)
                checkbox.setToolTip("")
    
    def _get_selected_platforms(self) -> List[str]:
        """Get list of selected platforms."""
        selected_platforms = []
        
        platform_checkboxes = {
            'instagram': self.instagram_checkbox,
            'facebook': self.facebook_checkbox,
            'tiktok': self.tiktok_checkbox,
            'youtube': self.youtube_checkbox,
            'pinterest': self.pinterest_checkbox,
            'snapchat': self.snapchat_checkbox
        }
        
        for platform, checkbox in platform_checkboxes.items():
            if checkbox.isChecked() and checkbox.isEnabled():
                selected_platforms.append(platform)
        
        return selected_platforms
    
    def _validate_selection(self) -> bool:
        """Validate that at least one platform is selected."""
        selected = self._get_selected_platforms()
        if not selected:
            QMessageBox.warning(self, "No Platforms Selected", 
                              "Please select at least one platform.")
            return False
        return True
    
    def _post_now(self):
        """Handle post now action."""
        if not self._validate_selection():
            return
        
        post_data = self.post_data.copy()
        post_data['platforms'] = self._get_selected_platforms()
        post_data['action'] = 'post_now'
        
        self.post_now_requested.emit(post_data)
        self.accept()
    
    def _add_to_campaign(self):
        """Handle add to campaign action."""
        if not self._validate_selection():
            return
        
        post_data = self.post_data.copy()
        post_data['platforms'] = self._get_selected_platforms()
        post_data['action'] = 'add_to_campaign'
        
        self.add_to_campaign_requested.emit(post_data)
        self.accept()
    
    def _schedule_post(self):
        """Handle schedule post action."""
        if not self._validate_selection():
            return
        
        post_data = self.post_data.copy()
        post_data['platforms'] = self._get_selected_platforms()
        post_data['action'] = 'schedule_post'
        
        self.schedule_post_requested.emit(post_data)
        self.accept()
    
    def _edit_post(self):
        """Handle edit post action."""
        self.edit_post_requested.emit(self.post_data)
        self.accept() 