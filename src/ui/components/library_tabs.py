"""
Library tabs component - Simple tab structure for the new library layout.
"""
import logging
import os
import shutil
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QLabel, QPushButton, QScrollArea, QGridLayout, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap

from ...handlers.library_handler import LibraryManager

class LibraryTabs(QWidget):
    """Simple library tabs widget following the new specification."""
    
    # Signals
    media_file_selected = Signal(str)  # file_path
    finished_post_selected = Signal(dict)  # post_data
    create_gallery_requested = Signal()
    media_uploaded = Signal()  # Signal when media is uploaded
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize library manager
        self.library_manager = LibraryManager()
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the tabs UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                color: #000000;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #cccccc;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #000000;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # Add main tabs
        self._create_media_files_tab()
        self._create_finished_posts_tab()
        
        layout.addWidget(self.tab_widget)
        
    def _create_media_files_tab(self):
        """Create the Media Files tab with photos and videos side by side."""
        media_tab = QWidget()
        media_layout = QVBoxLayout(media_tab)
        media_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with Create Gallery button
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Media Files")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #000000;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        create_gallery_btn = QPushButton("Create Gallery")
        create_gallery_btn.setStyleSheet("""
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
        """)
        create_gallery_btn.clicked.connect(self.create_gallery_requested.emit)
        header_layout.addWidget(create_gallery_btn)
        
        media_layout.addLayout(header_layout)
        
        # Combined media area with photos and videos side by side
        content_layout = QHBoxLayout()
        
        # Photos section
        photos_section = self._create_media_section("Photos", "📷")
        content_layout.addWidget(photos_section)
        
        # Videos section  
        videos_section = self._create_media_section("Videos", "🎥")
        content_layout.addWidget(videos_section)
        
        media_layout.addLayout(content_layout)
        
        # Add to main tabs
        self.tab_widget.addTab(media_tab, "Media Files")
        
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
        
        # Placeholder for now
        placeholder_label = QLabel(f"No {media_type.lower()} found\n\nDrag & drop files here\nor use upload button")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet("color: #666666; font-size: 12px; padding: 30px;")
        placeholder_label.setWordWrap(True)
        grid_layout.addWidget(placeholder_label, 0, 0)
        
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)
        
        return section
        
    def _create_finished_posts_tab(self):
        """Create the Finished Posts tab with sub-tabs."""
        posts_tab = QWidget()
        posts_layout = QVBoxLayout(posts_tab)
        
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
        post_types = ["Regular", "Galleries", "Videos/Reels", "Text"]
        for post_type in post_types:
            subtab = self._create_posts_subtab(post_type)
            posts_sub_tabs.addTab(subtab, post_type)
        
        posts_layout.addWidget(posts_sub_tabs)
        
        # Add to main tabs
        self.tab_widget.addTab(posts_tab, "Finished Posts")
        
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
            if post_type == "Regular":
                # Load both photos and videos for regular posts
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
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        
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
        
        # Connect click event
        def on_click():
            self.finished_post_selected.emit(post_data)
        
        widget.mousePressEvent = lambda event: on_click() if event.button() == Qt.MouseButton.LeftButton else None
        
        return widget
        
    def refresh_content(self):
        """Refresh all tab content."""
        self.logger.info("Refreshing library content")
        
        # Recreate the finished posts tab to reload content
        try:
            # Remove and recreate the finished posts tab
            self.tab_widget.removeTab(1)  # Remove "Finished Posts" tab
            self._create_finished_posts_tab()
            
            # Switch back to the finished posts tab if it was selected
            if self.tab_widget.currentIndex() == 1:
                self.tab_widget.setCurrentIndex(1)
                
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