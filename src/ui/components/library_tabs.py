"""
Library tabs component - Simple tab structure for the new library layout.
"""
import logging
import os
import shutil
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QLabel, QPushButton, QScrollArea, QGridLayout, QFileDialog, QMessageBox, QInputDialog, QListWidget, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap

from ...handlers.library_handler import LibraryManager
from ...models.app_state import AppState
from ...handlers.media_handler import MediaHandler
from ...handlers.crowseye_handler import CrowsEyeHandler
from .media_thumbnail_widget import MediaThumbnailWidget

class LibraryTabs(QWidget):
    """Simple library tabs widget following the new specification."""
    
    # Signals
    media_file_selected = Signal(str)  # file_path
    finished_post_selected = Signal(dict)  # post_data
    create_gallery_requested = Signal()
    media_uploaded = Signal()  # Signal when media is uploaded
    create_post_with_media_requested = Signal(str)  # Signal to create post with pre-loaded media
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize library manager
        self.library_manager = LibraryManager()
        
        # Initialize media handlers
        self.app_state = AppState()
        self.media_handler = MediaHandler(self.app_state)
        self.crowseye_handler = CrowsEyeHandler(self.app_state, self.media_handler, self.library_manager)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                color: #000000;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #cccccc;
                border-bottom: none;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #000000;
                font-weight: bold;
            }
        """)
        
        # Create tabs
        media_tab = self._create_media_files_tab()
        self.tab_widget.addTab(media_tab, "Unedited Media")
        
        posts_tab = self._create_finished_posts_tab()
        self.tab_widget.addTab(posts_tab, "Finished Posts")
        
        layout.addWidget(self.tab_widget)
        
    def _create_media_files_tab(self):
        """Create the Media Files tab for raw media uploads and management."""
        media_tab = QWidget()
        layout = QVBoxLayout(media_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with upload options
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Raw Media Library")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #000000; margin-bottom: 10px;")
        header_layout.addWidget(title_label)
        
        # Info label
        info_label = QLabel("Upload and manage your raw photos and videos for bulk processing")
        info_label.setStyleSheet("font-size: 12px; color: #666666; margin-left: 20px;")
        header_layout.addWidget(info_label)
        
        header_layout.addStretch()
        
        # Bulk upload buttons
        upload_photos_btn = QPushButton("📷 Upload Photos")
        upload_photos_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                margin-right: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        upload_photos_btn.clicked.connect(self._upload_photos)
        header_layout.addWidget(upload_photos_btn)
        
        upload_videos_btn = QPushButton("🎥 Upload Videos")
        upload_videos_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        upload_videos_btn.clicked.connect(self._upload_videos)
        header_layout.addWidget(upload_videos_btn)
        
        layout.addLayout(header_layout)
        
        # Content area with side-by-side sections
        content_layout = QHBoxLayout()
        
        # Photos section
        photos_section = self._create_media_section("Photos", "📷")
        content_layout.addWidget(photos_section)
        
        # Videos section  
        videos_section = self._create_media_section("Videos", "🎥")
        content_layout.addWidget(videos_section)
        
        layout.addLayout(content_layout)
        
        return media_tab
        
    def _create_media_section(self, media_type: str, icon: str):
        """Create a media section (Photos or Videos) for side-by-side layout."""
        section = QWidget()
        section.setStyleSheet("""
            QWidget {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Section header
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(f"{media_type}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #000000; margin-left: 8px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Upload button
        upload_btn = QPushButton(f"Upload {media_type}")
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        if media_type == "Photos":
            upload_btn.clicked.connect(self._upload_photos)
        else:  # Videos
            upload_btn.clicked.connect(self._upload_videos)
        header_layout.addWidget(upload_btn)
        
        layout.addLayout(header_layout)
        
        # Scroll area for media items
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        # Container for media grid
        container = QWidget()
        grid_layout = QGridLayout(container)
        grid_layout.setSpacing(8)
        
        # Load actual media instead of placeholder
        self._load_media_to_grid(grid_layout, media_type)
        
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)
        
        return section
        
    def _create_finished_posts_tab(self):
        """Create the Finished Posts tab with sub-tabs."""
        posts_tab = QWidget()
        posts_layout = QVBoxLayout(posts_tab)
        
        # Header with Create Gallery button
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Finished Posts")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #000000; margin-bottom: 10px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Selection info
        self.selection_info = QLabel("No items selected")
        self.selection_info.setStyleSheet("font-size: 12px; color: #666666; margin-right: 15px;")
        header_layout.addWidget(self.selection_info)
        
        # Clear selection button
        self.clear_selection_btn = QPushButton("Clear Selection")
        self.clear_selection_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                margin-right: 10px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        self.clear_selection_btn.clicked.connect(self._clear_finished_posts_selection)
        self.clear_selection_btn.hide()  # Initially hidden
        header_layout.addWidget(self.clear_selection_btn)
        
        # Create Gallery button
        self.create_gallery_btn = QPushButton("Create Gallery")
        self.create_gallery_btn.setStyleSheet("""
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
                background-color: #9ca3af;
                color: #6b7280;
            }
        """)
        self.create_gallery_btn.clicked.connect(self._create_gallery_from_finished_posts)
        self.create_gallery_btn.setEnabled(False)  # Initially disabled
        header_layout.addWidget(self.create_gallery_btn)
        
        posts_layout.addLayout(header_layout)
        
        # Initialize selection tracking
        self.selected_finished_posts = []
        
        # Sub-tabs for different post types
        posts_sub_tabs = QTabWidget()
        posts_sub_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dddddd;
                background-color: #fafafa;
            }
            QTabBar::tab {
                background-color: #e8e8e8;
                color: #000000;
                padding: 6px 12px;
                margin-right: 1px;
                border: 1px solid #dddddd;
                border-bottom: none;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background-color: #fafafa;
                color: #000000;
                font-weight: bold;
            }
        """)
        
        # Create sub-tabs for different post types
        post_types = ["Photo Posts", "Galleries", "Videos/Reels", "Text"]
        for post_type in post_types:
            subtab = self._create_posts_subtab(post_type)
            posts_sub_tabs.addTab(subtab, post_type)
        
        posts_layout.addWidget(posts_sub_tabs)
        
        return posts_tab
        
    def _create_posts_subtab(self, post_type: str):
        """Create a finished posts sub-tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        title_label = QLabel(f"{post_type} Posts")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #000000; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Scroll area for posts
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        # Container for posts grid
        container = QWidget()
        grid_layout = QGridLayout(container)
        grid_layout.setSpacing(10)
        
        # Load actual finished posts from library manager
        self._load_finished_posts_to_grid(grid_layout, post_type)
        
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)
        
        return tab
        
    def _load_finished_posts_to_grid(self, grid_layout, post_type):
        """Load finished posts from library manager into the grid."""
        try:
            # Get finished posts from library manager
            if post_type == "Photo Posts":
                # Load both photos and videos for photo posts
                posts = self.library_manager.get_all_post_ready_items()
            elif post_type == "Videos/Reels":
                # Load only videos
                posts = self.library_manager.get_post_ready_videos()
            else:
                # For now, other types show empty
                posts = []
            
            if not posts:
                # Show placeholder if no posts
                display_name = post_type.lower().replace(" posts", "") if "posts" in post_type.lower() else post_type.lower()
                placeholder_label = QLabel(f"No {display_name} found\n\nCreate content using the 'Create Post' feature")
                placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                placeholder_label.setStyleSheet("color: #666666; font-size: 14px; padding: 40px;")
                placeholder_label.setWordWrap(True)
                grid_layout.addWidget(placeholder_label, 0, 0)
                return
            
            # Add posts to grid
            row, col = 0, 0
            max_cols = 4
            
            for post in posts:
                post_widget = self._create_post_thumbnail(post)
                grid_layout.addWidget(post_widget, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
                    
        except Exception as e:
            self.logger.error(f"Error loading finished posts: {e}")
            # Show error message
            error_label = QLabel(f"Error loading posts: {str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: #ff0000; font-size: 14px; padding: 40px;")
            grid_layout.addWidget(error_label, 0, 0)
    
    def _create_post_thumbnail(self, post_data):
        """Create a thumbnail widget for a finished post."""
        widget = QWidget()
        widget.setFixedSize(200, 250)
        widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QWidget:hover {
                border-color: #007bff;
                background-color: #f8f9fa;
            }
        """)
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Store post data and selection state
        widget.post_data = post_data
        widget.is_selected = False
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        
        # Selection indicator (checkbox)
        widget.checkbox = QPushButton("☐")
        widget.checkbox.setFixedSize(20, 20)
        widget.checkbox.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ccc;
                border-radius: 3px;
                font-size: 14px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        widget.checkbox.clicked.connect(lambda: self._toggle_finished_post_selection(widget))
        
        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(widget.checkbox)
        checkbox_layout.addStretch()
        layout.addLayout(checkbox_layout)
        
        # Media preview
        preview_label = QLabel()
        preview_label.setFixedSize(180, 135)
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setStyleSheet("border: 1px solid #ddd; border-radius: 4px; background-color: #f5f5f5;")
        
        # Try to load thumbnail
        media_path = post_data.get("path", "")
        if media_path and os.path.exists(media_path):
            try:
                pixmap = QPixmap(media_path)
                if not pixmap.isNull():
                    # Scale pixmap to fit
                    scaled_pixmap = pixmap.scaled(180, 135, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    preview_label.setPixmap(scaled_pixmap)
                else:
                    preview_label.setText("📷\nPreview\nUnavailable")
            except Exception as e:
                self.logger.warning(f"Could not load thumbnail for {media_path}: {e}")
                preview_label.setText("📷\nPreview\nError")
        else:
            preview_label.setText("📷\nNo Preview")
        
        layout.addWidget(preview_label)
        
        # Caption preview
        caption = post_data.get("caption", "No caption")
        caption_label = QLabel(caption[:50] + "..." if len(caption) > 50 else caption)
        caption_label.setWordWrap(True)
        caption_label.setStyleSheet("font-size: 11px; color: #333; padding: 2px;")
        caption_label.setMaximumHeight(40)
        layout.addWidget(caption_label)
        
        # Date
        date_added = post_data.get("date_added", "")
        if date_added:
            try:
                from datetime import datetime
                date_obj = datetime.fromisoformat(date_added.replace('Z', '+00:00'))
                date_str = date_obj.strftime("%m/%d/%Y")
            except:
                date_str = "Unknown date"
        else:
            date_str = "Unknown date"
            
        date_label = QLabel(date_str)
        date_label.setStyleSheet("font-size: 10px; color: #666; font-style: italic;")
        layout.addWidget(date_label)
        
        # Type indicator
        post_type = post_data.get("type", "unknown")
        type_icon = "📷" if "photo" in post_type else "🎥" if "video" in post_type else "📄"
        type_label = QLabel(f"{type_icon} Ready to Post")
        type_label.setStyleSheet("font-size: 10px; color: #007bff; font-weight: bold;")
        layout.addWidget(type_label)
        
        # Connect click event for post viewing (right-click or double-click)
        def on_click(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self._toggle_finished_post_selection(widget)
            elif event.button() == Qt.MouseButton.RightButton:
                self.finished_post_selected.emit(post_data)
        
        widget.mousePressEvent = on_click
        
        return widget
        
    def _load_media_to_grid(self, grid_layout, media_type):
        """Load media files into the grid layout."""
        try:
            # Get all media from CrowsEye handler
            all_media = self.crowseye_handler.get_all_media()
            
            # Determine which media type to load
            if media_type == "Photos":
                media_paths = all_media.get("raw_photos", [])
                widget_type = "image"
            else:  # Videos
                media_paths = all_media.get("raw_videos", [])
                widget_type = "video"
            
            if not media_paths:
                # Show placeholder if no media
                placeholder_label = QLabel(f"No {media_type.lower()} found\n\nUse the upload button above\nto add {media_type.lower()}")
                placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                placeholder_label.setStyleSheet("color: #666666; font-size: 12px; padding: 30px;")
                placeholder_label.setWordWrap(True)
                grid_layout.addWidget(placeholder_label, 0, 0)
                return
            
            # Add media to grid
            row, col = 0, 0
            max_cols = 4
            
            for media_path in media_paths:
                if os.path.exists(media_path):
                    thumbnail = MediaThumbnailWidget(media_path, widget_type)
                    thumbnail.clicked.connect(self._on_media_selected)
                    grid_layout.addWidget(thumbnail, row, col)
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
                        
        except Exception as e:
            self.logger.error(f"Error loading {media_type}: {e}")
            # Show error message
            error_label = QLabel(f"Error loading {media_type.lower()}: {str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: #ff0000; font-size: 12px; padding: 30px;")
            grid_layout.addWidget(error_label, 0, 0)
    
    def _on_media_selected(self, media_path):
        """Handle media selection by showing options dialog."""
        self.logger.info(f"Media selected: {media_path}")
        
        # Show options dialog for the selected media
        self._show_media_options_dialog(media_path)
    
    def _show_media_options_dialog(self, media_path):
        """Show options dialog for selected media."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QPixmap, QFont
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Media Options")
        dialog.setFixedSize(500, 600)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header with media preview
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        # Media preview
        preview_label = QLabel()
        preview_label.setFixedSize(200, 150)
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setStyleSheet("border: 1px solid #ddd; border-radius: 4px; background-color: #f5f5f5;")
        
        # Load thumbnail
        try:
            media_type = "video" if any(ext in media_path.lower() for ext in ['.mp4', '.mov', '.avi', '.mkv']) else "image"
            if media_type == "image":
                pixmap = QPixmap(media_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(200, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    preview_label.setPixmap(scaled_pixmap)
                else:
                    preview_label.setText("📷\nPreview\nUnavailable")
            else:
                # For videos, try to use video thumbnail generator
                if hasattr(self, 'video_generator') and self.video_generator:
                    try:
                        thumbnail = self.video_generator.generate_thumbnail(media_path, timestamp=1.0, size=(200, 150))
                        if thumbnail and not thumbnail.isNull():
                            preview_label.setPixmap(thumbnail)
                        else:
                            preview_label.setText("🎥\nVideo\nPreview")
                    except:
                        preview_label.setText("🎥\nVideo\nPreview")
                else:
                    preview_label.setText("🎥\nVideo\nPreview")
        except Exception as e:
            preview_label.setText("📷\nPreview\nError")
        
        header_layout.addWidget(preview_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Media name
        media_name = os.path.basename(media_path)
        name_label = QLabel(media_name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_font = QFont()
        name_font.setPointSize(12)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #2c3e50; margin-top: 10px;")
        header_layout.addWidget(name_label)
        
        layout.addWidget(header_frame)
        
        # Options section
        options_label = QLabel("What would you like to do with this media?")
        options_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        options_label.setStyleSheet("font-size: 14px; color: #34495e; font-weight: bold; margin: 10px 0;")
        layout.addWidget(options_label)
        
        # Option buttons
        options = [
            ("🎨 Create Post", "Create a social media post with this media", self._create_post_with_media),
            ("✂️ Edit Media", "Edit or enhance this media", self._edit_media),
            ("🖼️ Add to Gallery", "Add this media to a new or existing gallery", self._add_to_gallery),
            ("📱 Generate Post Variants", "Create multiple post variations", self._generate_variants),
            ("🎯 Quick Share", "Share directly to social platforms", self._quick_share),
            ("🏷️ Add Tags/Caption", "Add metadata and captions", self._add_metadata),
            ("📊 Analyze Media", "Get AI insights about this media", self._analyze_media),
            ("🗂️ Move to Folder", "Organize this media", self._organize_media)
        ]
        
        for icon_title, description, action in options:
            option_frame = self._create_option_button(icon_title, description, lambda a=action, p=media_path: self._execute_option(dialog, a, p))
            layout.addWidget(option_frame)
        
        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        close_btn = QPushButton("Cancel")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        close_btn.clicked.connect(dialog.reject)
        close_layout.addWidget(close_btn)
        
        layout.addLayout(close_layout)
        
        dialog.exec()
    
    def _create_option_button(self, title, description, action):
        """Create an option button with title and description."""
        from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
        from PySide6.QtCore import Qt
        
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px;
            }
            QFrame:hover {
                border-color: #007bff;
                background-color: #f8f9fa;
            }
        """)
        frame.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Make frame clickable
        frame.mousePressEvent = lambda event: action() if event.button() == Qt.MouseButton.LeftButton else None
        
        return frame
    
    def _execute_option(self, dialog, action, media_path):
        """Execute the selected option and close dialog."""
        dialog.accept()
        action(media_path)
    
    def _create_post_with_media(self, media_path):
        """Create a post with the selected media pre-loaded."""
        self.logger.info(f"Creating post with media: {media_path}")
        
        # Emit signal to app controller to open post creation with pre-loaded media
        self.create_post_with_media_requested.emit(media_path)
    
    def _edit_media(self, media_path):
        """Edit the selected media."""
        self.logger.info(f"Editing media: {media_path}")
        
        # Open image editor dialog for photos, or show video editing options for videos
        if any(ext in media_path.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            # For images, open the image edit dialog
            instructions, ok = QInputDialog.getText(
                self,
                "Edit Image",
                "Enter editing instructions (e.g., 'make brighter', 'add vintage filter', 'remove background'):",
                text="Enhance the image"
            )
            
            if ok and instructions:
                # Here you would call the image editing service
                QMessageBox.information(
                    self,
                    "Image Edit",
                    f"Processing image with instructions: '{instructions}'\n\n"
                    f"File: {os.path.basename(media_path)}\n\n"
                    "(Image editing will be processed and saved to Finished Posts)"
                )
        else:
            # For videos, show video editing options
            QMessageBox.information(
                self,
                "Video Edit",
                f"Video editing options for:\n{os.path.basename(media_path)}\n\n"
                "(Video editing features coming soon)"
            )
    
    def _add_to_gallery(self, media_path):
        """Add media to a gallery."""
        self.logger.info(f"Adding to gallery: {media_path}")
        
        # Get existing galleries
        galleries = self.crowseye_handler.get_saved_galleries()
        
        if not galleries:
            # No existing galleries, create new one
            gallery_name, ok = QInputDialog.getText(
                self,
                "Create New Gallery",
                "Enter a name for the new gallery:",
                text="New Gallery"
            )
            
            if ok and gallery_name:
                caption = f"Gallery created with {os.path.basename(media_path)}"
                success = self.crowseye_handler.save_gallery(gallery_name, [media_path], caption)
                
                if success:
                    QMessageBox.information(
                        self,
                        "Gallery Created",
                        f"Created new gallery '{gallery_name}' with selected media!"
                    )
                    self.refresh_content()
                else:
                    QMessageBox.critical(
                        self,
                        "Gallery Creation Failed",
                        "Failed to create gallery. Please try again."
                    )
        else:
            # Show dialog to choose existing gallery or create new
            dialog = QDialog(self)
            dialog.setWindowTitle("Add to Gallery")
            dialog.setFixedSize(400, 300)
            
            layout = QVBoxLayout(dialog)
            
            label = QLabel("Choose an existing gallery or create a new one:")
            layout.addWidget(label)
            
            # List of existing galleries
            gallery_list = QListWidget()
            for gallery in galleries:
                gallery_list.addItem(gallery.get('name', 'Unnamed Gallery'))
            layout.addWidget(gallery_list)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            new_btn = QPushButton("Create New Gallery")
            new_btn.clicked.connect(lambda: self._create_new_gallery_with_media(dialog, media_path))
            button_layout.addWidget(new_btn)
            
            add_btn = QPushButton("Add to Selected")
            add_btn.clicked.connect(lambda: self._add_to_selected_gallery(dialog, gallery_list, media_path, galleries))
            button_layout.addWidget(add_btn)
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            
            dialog.exec()
    
    def _create_new_gallery_with_media(self, parent_dialog, media_path):
        """Create a new gallery with the selected media."""
        gallery_name, ok = QInputDialog.getText(
            parent_dialog,
            "Create New Gallery",
            "Enter a name for the new gallery:",
            text="New Gallery"
        )
        
        if ok and gallery_name:
            caption = f"Gallery created with {os.path.basename(media_path)}"
            success = self.crowseye_handler.save_gallery(gallery_name, [media_path], caption)
            
            if success:
                QMessageBox.information(
                    parent_dialog,
                    "Gallery Created",
                    f"Created new gallery '{gallery_name}' with selected media!"
                )
                parent_dialog.accept()
                self.refresh_content()
            else:
                QMessageBox.critical(
                    parent_dialog,
                    "Gallery Creation Failed",
                    "Failed to create gallery. Please try again."
                )
    
    def _add_to_selected_gallery(self, parent_dialog, gallery_list, media_path, galleries):
        """Add media to the selected existing gallery."""
        current_item = gallery_list.currentItem()
        if not current_item:
            QMessageBox.warning(parent_dialog, "No Selection", "Please select a gallery first.")
            return
        
        gallery_index = gallery_list.currentRow()
        if 0 <= gallery_index < len(galleries):
            gallery = galleries[gallery_index]
            gallery_filename = gallery.get('filename', '')
            
            if gallery_filename:
                success = self.crowseye_handler.add_media_to_gallery(gallery_filename, [media_path])
                
                if success:
                    QMessageBox.information(
                        parent_dialog,
                        "Media Added",
                        f"Added media to gallery '{gallery.get('name', 'Unnamed Gallery')}'!"
                    )
                    parent_dialog.accept()
                    self.refresh_content()
                else:
                    QMessageBox.critical(
                        parent_dialog,
                        "Addition Failed",
                        "Failed to add media to gallery. Please try again."
                    )
    
    def _generate_variants(self, media_path):
        """Generate post variants."""
        self.logger.info(f"Generating variants for: {media_path}")
        QMessageBox.information(
            self,
            "Generate Variants",
            f"Generating variants for:\n{os.path.basename(media_path)}\n\n(AI variant generation coming soon)"
        )
    
    def _quick_share(self, media_path):
        """Quick share to platforms."""
        self.logger.info(f"Quick sharing: {media_path}")
        QMessageBox.information(
            self,
            "Quick Share",
            f"Quick sharing:\n{os.path.basename(media_path)}\n\n(Direct platform sharing coming soon)"
        )
    
    def _add_metadata(self, media_path):
        """Add metadata and tags."""
        self.logger.info(f"Adding metadata to: {media_path}")
        QMessageBox.information(
            self,
            "Add Metadata",
            f"Adding metadata to:\n{os.path.basename(media_path)}\n\n(Metadata editor coming soon)"
        )
    
    def _analyze_media(self, media_path):
        """Analyze media with AI."""
        self.logger.info(f"Analyzing media: {media_path}")
        QMessageBox.information(
            self,
            "Analyze Media",
            f"AI analyzing:\n{os.path.basename(media_path)}\n\n(AI analysis feature coming soon)"
        )
    
    def _organize_media(self, media_path):
        """Organize media into folders."""
        self.logger.info(f"Organizing media: {media_path}")
        QMessageBox.information(
            self,
            "Organize Media",
            f"Organizing:\n{os.path.basename(media_path)}\n\n(Media organization feature coming soon)"
        )
    
    def refresh_content(self):
        """Refresh all tab content."""
        self.logger.info("Refreshing library content")
        
        try:
            current_index = self.tab_widget.currentIndex()
            
            # Initialize selection tracking if not exists
            if not hasattr(self, 'selected_finished_posts'):
                self.selected_finished_posts = []
            
            # Refresh raw media files tab (unedited media for bulk uploads)
            self.tab_widget.removeTab(0)  # Remove "Media Files" tab
            media_tab = self._create_media_files_tab()
            self.tab_widget.insertTab(0, media_tab, "Unedited Media")
            
            # Refresh finished posts tab (completed content)
            self.tab_widget.removeTab(1)  # Remove "Finished Posts" tab
            posts_tab = self._create_finished_posts_tab()
            self.tab_widget.insertTab(1, posts_tab, "Finished Posts")
            
            # Maintain current tab selection if possible
            if current_index < self.tab_widget.count():
                self.tab_widget.setCurrentIndex(current_index)
                
        except Exception as e:
            self.logger.error(f"Error refreshing content: {e}")
        
    def _upload_photos(self):
        """Handle photo upload."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Photos",
            "",
            "Image Files (*.jpg *.jpeg *.png *.gif *.bmp *.webp);;All Files (*)"
        )
        
        if file_paths:
            self._process_uploads(file_paths, "photos")
            
    def _upload_videos(self):
        """Handle video upload."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Videos", 
            "",
            "Video Files (*.mp4 *.mov *.avi *.mkv *.wmv);;All Files (*)"
        )
        
        if file_paths:
            self._process_uploads(file_paths, "videos")
            
    def _process_uploads(self, file_paths, media_type):
        """Process uploaded files."""
        try:
            uploaded = 0
            media_library_dir = "data/media"
            
            # Ensure media_library directory exists
            os.makedirs(media_library_dir, exist_ok=True)
            
            for file_path in file_paths:
                if os.path.exists(file_path):
                    # Copy file to media_library directory
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(media_library_dir, filename)
                    
                    # Handle duplicate filenames
                    counter = 1
                    base_name, ext = os.path.splitext(filename)
                    while os.path.exists(dest_path):
                        new_filename = f"{base_name}_{counter}{ext}"
                        dest_path = os.path.join(media_library_dir, new_filename)
                        counter += 1
                    
                    shutil.copy2(file_path, dest_path)
                    uploaded += 1
                    self.logger.info(f"Uploaded file: {filename} -> {dest_path}")
            
            QMessageBox.information(
                self, 
                "Upload Complete", 
                f"Successfully uploaded {uploaded} {media_type}!"
            )
            
            # Emit signal to refresh content
            self.media_uploaded.emit()
            
        except Exception as e:
            self.logger.error(f"Upload error: {e}")
            QMessageBox.critical(self, "Upload Error", f"Failed to upload: {str(e)}")
        
    def retranslateUi(self):
        """Update UI text for internationalization."""
        # TODO: Implement when i18n is needed
        pass 

    def _toggle_finished_post_selection(self, widget):
        """Toggle selection state of a finished post."""
        if widget.is_selected:
            # Deselect
            widget.is_selected = False
            widget.checkbox.setText("☐")
            widget.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                }
                QWidget:hover {
                    border-color: #007bff;
                    background-color: #f8f9fa;
                }
            """)
            if widget.post_data in self.selected_finished_posts:
                self.selected_finished_posts.remove(widget.post_data)
        else:
            # Select
            widget.is_selected = True
            widget.checkbox.setText("☑")
            widget.setStyleSheet("""
                QWidget {
                    background-color: #e3f2fd;
                    border: 2px solid #2196f3;
                    border-radius: 8px;
                }
                QWidget:hover {
                    background-color: #bbdefb;
                }
            """)
            if widget.post_data not in self.selected_finished_posts:
                self.selected_finished_posts.append(widget.post_data)
        
        self._update_finished_posts_selection_ui()
    
    def _update_finished_posts_selection_ui(self):
        """Update the selection UI elements."""
        count = len(self.selected_finished_posts)
        
        if count == 0:
            self.selection_info.setText("No items selected")
            self.clear_selection_btn.hide()
            self.create_gallery_btn.setEnabled(False)
        else:
            self.selection_info.setText(f"{count} item(s) selected")
            self.clear_selection_btn.show()
            self.create_gallery_btn.setEnabled(count >= 2)  # Need at least 2 items for gallery
    
    def _clear_finished_posts_selection(self):
        """Clear all selections in finished posts."""
        for post_data in self.selected_finished_posts.copy():
            # Find the widget and deselect it
            # Note: This is a simplified approach; in a real implementation, 
            # you'd want to keep track of widgets properly
            pass
        
        self.selected_finished_posts.clear()
        self._update_finished_posts_selection_ui()
        
        # Refresh the tab to reset visual states
        self.refresh_content()
    
    def _create_gallery_from_finished_posts(self):
        """Create a gallery from selected finished posts with platform validation."""
        if len(self.selected_finished_posts) < 2:
            QMessageBox.warning(
                self,
                "Insufficient Selection",
                "Please select at least 2 items to create a gallery."
            )
            return
        
        # Analyze selected media types
        has_photos = False
        has_videos = False
        
        for post_data in self.selected_finished_posts:
            post_type = post_data.get("type", "").lower()
            media_path = post_data.get("path", "").lower()
            
            if "photo" in post_type or any(ext in media_path for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                has_photos = True
            elif "video" in post_type or any(ext in media_path for ext in ['.mp4', '.mov', '.avi', '.mkv']):
                has_videos = True
        
        # Platform validation warnings
        warnings = []
        
        if has_photos and has_videos:
            warnings.append("Mixed media galleries (photos + videos) may not be supported on all platforms:")
            warnings.append("• Instagram: Supports mixed carousels (photos + videos)")
            warnings.append("• TikTok: Supports photo carousels but videos must be separate")
            warnings.append("• Pinterest: Primarily supports photo galleries")
            warnings.append("• Twitter/X: Supports mixed media in threads")
            warnings.append("• LinkedIn: Limited mixed media support")
        
        if len(self.selected_finished_posts) > 10:
            warnings.append("Large galleries may have platform limitations:")
            warnings.append("• Instagram: Max 10 items per carousel")
            warnings.append("• TikTok: Max 35 photos per carousel")
            warnings.append("• Pinterest: No strict limit but performance may vary")
        
        # Show warnings if any
        if warnings:
            warning_message = "\n".join(warnings)
            warning_message += "\n\nDo you want to continue creating the gallery?"
            
            reply = QMessageBox.question(
                self,
                "Platform Compatibility Warning",
                warning_message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Proceed with gallery creation
        self.logger.info(f"Creating gallery from {len(self.selected_finished_posts)} selected posts")
        
        # Extract media paths
        media_paths = []
        for post_data in self.selected_finished_posts:
            media_path = post_data.get("path")
            if media_path and os.path.exists(media_path):
                media_paths.append(media_path)
        
        if media_paths:
            # Open gallery creation dialog (you may need to implement this)
            from PySide6.QtWidgets import QInputDialog
            
            gallery_name, ok = QInputDialog.getText(
                self,
                "Gallery Name",
                "Enter a name for your gallery:",
                text=f"Gallery_{len(media_paths)}_items"
            )
            
            if ok and gallery_name:
                # Save the gallery using crowseye handler
                caption = f"Gallery with {len(media_paths)} items"
                success = self.crowseye_handler.save_gallery(gallery_name, media_paths, caption)
                
                if success:
                    QMessageBox.information(
                        self,
                        "Gallery Created",
                        f"Gallery '{gallery_name}' created successfully with {len(media_paths)} items!"
                    )
                    self._clear_finished_posts_selection()
                    self.refresh_content()
                else:
                    QMessageBox.critical(
                        self,
                        "Gallery Creation Failed",
                        "Failed to create gallery. Please try again."
                    )
        
    def _load_finished_posts_to_grid(self, grid_layout, post_type):
        """Load finished posts from library manager into the grid."""
        try:
            # Get finished posts from library manager
            if post_type == "Photo Posts":
                # Load both photos and videos for photo posts
                posts = self.library_manager.get_all_post_ready_items()
            elif post_type == "Videos/Reels":
                # Load only videos
                posts = self.library_manager.get_post_ready_videos()
            else:
                # For now, other types show empty
                posts = []
            
            if not posts:
                # Show placeholder if no posts
                placeholder_label = QLabel(f"No {post_type.lower()} posts found\n\nCreate posts using the 'Create Post' feature")
                placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                placeholder_label.setStyleSheet("color: #666666; font-size: 14px; padding: 40px;")
                placeholder_label.setWordWrap(True)
                grid_layout.addWidget(placeholder_label, 0, 0)
                return
            
            # Add posts to grid
            row, col = 0, 0
            max_cols = 4
            
            for post in posts:
                post_widget = self._create_post_thumbnail(post)
                grid_layout.addWidget(post_widget, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
                    
        except Exception as e:
            self.logger.error(f"Error loading finished posts: {e}")
            # Show error message
            error_label = QLabel(f"Error loading posts: {str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: #ff0000; font-size: 14px; padding: 40px;")
            grid_layout.addWidget(error_label, 0, 0) 