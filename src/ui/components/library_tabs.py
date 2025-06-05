"""
Library tabs component - Simple tab structure for the new library layout.
"""
import logging
import os
import shutil
from datetime import datetime
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
from .selectable_media_widget import SelectableMediaWidget

class LibraryTabs(QWidget):
    """Simple library tabs widget following the new specification."""
    
    # Signals
    media_file_selected = Signal(str)  # file_path
    finished_post_selected = Signal(dict)  # post_data
    create_gallery_requested = Signal()
    media_uploaded = Signal()  # Signal when media is uploaded
    create_post_with_media_requested = Signal(str)  # Signal to create post with pre-loaded media
    
    def __init__(self, library_manager: LibraryManager = None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Use provided library manager or create new one
        self.library_manager = library_manager if library_manager else LibraryManager()
        
        # Initialize media handlers
        self.app_state = AppState()
        self.media_handler = MediaHandler(self.app_state)
        self.crowseye_handler = CrowsEyeHandler(self.app_state, self.media_handler, self.library_manager)
        
        # Track selected media for gallery creation
        self.selected_media = set()
        self.media_widgets = {}  # Map media_path to widget for selection tracking
        
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
        
        # Selection controls (initially hidden)
        self.selection_controls = QWidget()
        selection_layout = QHBoxLayout(self.selection_controls)
        selection_layout.setContentsMargins(0, 10, 0, 0)
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.select_all_btn.clicked.connect(self._select_all_media_combined)
        selection_layout.addWidget(self.select_all_btn)
        
        self.clear_selection_btn = QPushButton("Clear Selection")
        self.clear_selection_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        self.clear_selection_btn.clicked.connect(self._clear_selection)
        selection_layout.addWidget(self.clear_selection_btn)
        
        self.selected_count_label = QLabel("0 selected")
        self.selected_count_label.setStyleSheet("color: #666; font-size: 12px; margin-left: 10px;")
        selection_layout.addWidget(self.selected_count_label)
        
        selection_layout.addStretch()
        
        # Action buttons
        self.create_gallery_btn = QPushButton("Create Gallery")
        self.create_gallery_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.create_gallery_btn.clicked.connect(self._create_gallery_from_selection)
        self.create_gallery_btn.setEnabled(False)
        selection_layout.addWidget(self.create_gallery_btn)
        
        self.delete_selected_btn = QPushButton("Delete Selected")
        self.delete_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.delete_selected_btn.clicked.connect(self._delete_selected_media)
        self.delete_selected_btn.setEnabled(False)
        selection_layout.addWidget(self.delete_selected_btn)
        
        self.selection_controls.setVisible(False)
        layout.addWidget(self.selection_controls)
        
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
        """Create the finished posts tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header with title only (removed Create Gallery button)
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Finished Posts")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333333;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Info text
        info_label = QLabel("Ready-to-post content organized by type")
        info_label.setStyleSheet("color: #666666; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # Subtabs for different post types
        self.finished_posts_subtabs = QTabWidget()
        self.finished_posts_subtabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                color: #333333;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # Create subtabs
        post_types = ["Photo Posts", "Videos/Reels", "Stories", "Carousels"]
        for post_type in post_types:
            subtab = self._create_posts_subtab(post_type)
            self.finished_posts_subtabs.addTab(subtab, post_type)
        
        layout.addWidget(self.finished_posts_subtabs)
        
        return tab
        
    def _create_posts_subtab(self, post_type: str):
        """Create a subtab for a specific post type."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create scroll area for posts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: white; }")
        
        scroll_content = QWidget()
        scroll_layout = QGridLayout(scroll_content)
        scroll_layout.setSpacing(10)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        
        # Load posts for this type
        self._load_finished_posts_to_grid(scroll_layout, post_type)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def _load_finished_posts_to_grid(self, grid_layout, post_type):
        """Load finished posts from library manager into the grid."""
        try:
            # Get finished posts from library manager
            if post_type == "Photo Posts":
                # Load both photos and videos for photo posts
                posts = self.library_manager.get_all_post_ready_items() if self.library_manager else []
            elif post_type == "Videos/Reels":
                # Load only videos
                posts = self.library_manager.get_post_ready_videos() if self.library_manager else []
            else:
                # For now, other types show empty
                posts = []
            
            if not posts:
                # Show placeholder if no posts
                placeholder_label = QLabel(f"No {post_type.lower()} found\n\nCreate posts using the 'Create Post' feature")
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

        # Store post data
        widget.post_data = post_data
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        
        # Media preview
        preview_label = QLabel()
        preview_label.setFixedSize(180, 150)
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setStyleSheet("border: 1px solid #ddd; border-radius: 4px; background-color: #f5f5f5;")
        
        # Try to load thumbnail
        media_path = post_data.get("path", "")
        if media_path and os.path.exists(media_path):
            try:
                pixmap = QPixmap(media_path)
                if not pixmap.isNull():
                    # Scale pixmap to fit
                    scaled_pixmap = pixmap.scaled(180, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
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
        
        # Connect click event to open post preview
        def on_widget_click(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self._open_post_preview(post_data)
        
        widget.mousePressEvent = on_widget_click
        
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
                    # Use selectable widget for the media tab
                    thumbnail = SelectableMediaWidget(media_path, widget_type)
                    thumbnail.selection_changed.connect(self._on_media_selection_changed)
                    thumbnail.media_clicked.connect(self._on_media_selected)  # Both clicks show options dialog
                    
                    # Store widget reference for selection management
                    self.media_widgets[media_path] = thumbnail
                    
                    grid_layout.addWidget(thumbnail, row, col)
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
            
            # Show selection controls if we have any media in either section
            all_media = self.crowseye_handler.get_all_media()
            has_any_media = (all_media.get("raw_photos", []) or all_media.get("raw_videos", []))
            if has_any_media:
                self.selection_controls.setVisible(True)
                        
        except Exception as e:
            self.logger.error(f"Error loading {media_type}: {e}")
            # Show error message
            error_label = QLabel(f"Error loading {media_type.lower()}: {str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: #ff0000; font-size: 12px; padding: 30px;")
            grid_layout.addWidget(error_label, 0, 0)
    
    def _on_media_selected(self, media_path):
        """Handle media click by showing options dialog for unedited media."""
        self.logger.info(f"Unedited media clicked: {media_path}")
        
        # Debug logging
        self.logger.debug(f"About to show media options dialog for: {media_path}")
        
        # Show options dialog for unedited media (needs editing before posting)
        self._show_media_options_dialog(media_path)
    

    
    def _show_media_options_dialog(self, media_path):
        """Show options dialog for selected media."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QPixmap, QFont
        
        self.logger.debug(f"Creating media options dialog for: {media_path}")
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Media Options")
        dialog.setFixedSize(500, 600)
        dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)
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
        
        # Option buttons - Updated to include "Create Gallery" option
        options = [
            ("🎨 Create Post", "Create a social media post with this media", self._create_post_with_media),
            ("✂️ Edit Media", "Edit or enhance this media", self._edit_media),
            ("🖼️ Create Gallery", "Create a new gallery starting with this media", self._create_gallery_with_media),
            ("🖼️ Add to Gallery", "Add this media to an existing gallery", self._add_to_gallery),
            ("📱 Generate Post Variants", "Create multiple post variations", self._generate_variants),
            ("🎯 Quick Share", "Share directly to social platforms", self._quick_share),
            ("🏷️ Add Tags/Caption", "Add metadata and captions", self._add_metadata),
            ("📊 Analyze Media", "Get AI insights about this media", self._analyze_media),
            ("📋 Move to Campaign", "Move this media to a campaign", self._organize_media)
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
        
        self.logger.debug(f"Executing media options dialog for: {media_path}")
        result = dialog.exec()
        self.logger.debug(f"Media options dialog result: {result}")
    
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
        """Add media to an existing gallery."""
        self.logger.info(f"Adding media to gallery: {media_path}")
        
        # Get existing galleries
        try:
            galleries = self.crowseye_handler.get_all_galleries()
            
            if not galleries:
                # No galleries exist - offer to create one
                from PySide6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self,
                    "No Galleries Found",
                    "No galleries exist yet. Would you like to create a new gallery with this media?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self._create_new_gallery_with_media(None, media_path)
                return
            
            # Show gallery selection dialog
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QLabel
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Select Gallery")
            dialog.setFixedSize(400, 300)
            
            layout = QVBoxLayout(dialog)
            
            label = QLabel("Select a gallery to add this media to:")
            layout.addWidget(label)
            
            gallery_list = QListWidget()
            for gallery in galleries:
                gallery_name = gallery.get("name", "Unnamed Gallery")
                gallery_list.addItem(gallery_name)
            layout.addWidget(gallery_list)
            
            buttons_layout = QHBoxLayout()
            
            add_btn = QPushButton("Add to Selected")
            add_btn.clicked.connect(lambda: self._add_to_selected_gallery(dialog, gallery_list, media_path, galleries))
            buttons_layout.addWidget(add_btn)
            
            new_btn = QPushButton("Create New Gallery")
            new_btn.clicked.connect(lambda: self._create_new_gallery_with_media(dialog, media_path))
            buttons_layout.addWidget(new_btn)
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(dialog.reject)
            buttons_layout.addWidget(cancel_btn)
            
            layout.addLayout(buttons_layout)
            
            dialog.exec()
            
        except Exception as e:
            self.logger.error(f"Error adding to gallery: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Could not add to gallery: {str(e)}")
    
    def _create_gallery_with_media(self, media_path):
        """Create a new gallery starting with the selected media."""
        self.logger.info(f"Creating new gallery with media: {media_path}")
        
        from PySide6.QtWidgets import QInputDialog, QMessageBox
        
        # Get gallery name
        gallery_name, ok = QInputDialog.getText(
            self,
            "Create Gallery",
            "Enter a name for your new gallery:",
            text=f"Gallery_{os.path.basename(media_path).split('.')[0]}"
        )
        
        if ok and gallery_name:
            try:
                # Create gallery with the media
                caption = f"Gallery created with {os.path.basename(media_path)}"
                success = self.crowseye_handler.save_gallery(gallery_name, [media_path], caption)
                
                if success:
                    QMessageBox.information(
                        self,
                        "Gallery Created",
                        f"Gallery '{gallery_name}' created successfully with the selected media!"
                    )
                    self.refresh_content()
                else:
                    QMessageBox.critical(
                        self,
                        "Gallery Creation Failed",
                        "Failed to create gallery. Please try again."
                    )
            except Exception as e:
                self.logger.error(f"Error creating gallery: {e}")
                QMessageBox.critical(self, "Error", f"Could not create gallery: {str(e)}")
    
    def _create_new_gallery_with_media(self, parent_dialog, media_path):
        """Create a new gallery with the selected media."""
        from PySide6.QtWidgets import QInputDialog, QMessageBox
        
        gallery_name, ok = QInputDialog.getText(
            parent_dialog or self,
            "Create New Gallery",
            "Enter a name for the new gallery:",
            text="New Gallery"
        )
        
        if ok and gallery_name:
            try:
                caption = f"Gallery created with {os.path.basename(media_path)}"
                success = self.crowseye_handler.save_gallery(gallery_name, [media_path], caption)
                
                if success:
                    QMessageBox.information(
                        parent_dialog or self,
                        "Gallery Created",
                        f"Created new gallery '{gallery_name}' with selected media!"
                    )
                    if parent_dialog:
                        parent_dialog.accept()
                    self.refresh_content()
                else:
                    QMessageBox.critical(
                        parent_dialog or self,
                        "Gallery Creation Failed",
                        "Failed to create gallery. Please try again."
                    )
            except Exception as e:
                self.logger.error(f"Error creating new gallery: {e}")
                QMessageBox.critical(parent_dialog or self, "Error", f"Could not create gallery: {str(e)}")
    
    def _add_to_selected_gallery(self, parent_dialog, gallery_list, media_path, galleries):
        """Add media to the selected existing gallery."""
        from PySide6.QtWidgets import QMessageBox
        
        current_item = gallery_list.currentItem()
        if not current_item:
            QMessageBox.warning(parent_dialog, "No Selection", "Please select a gallery first.")
            return
        
        gallery_index = gallery_list.currentRow()
        if 0 <= gallery_index < len(galleries):
            gallery = galleries[gallery_index]
            gallery_filename = gallery.get('filename', '')
            
            if gallery_filename:
                try:
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
                except Exception as e:
                    self.logger.error(f"Error adding to selected gallery: {e}")
                    QMessageBox.critical(parent_dialog, "Error", f"Could not add to gallery: {str(e)}")
    
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
        """Move media to a campaign."""
        self.logger.info(f"Moving media to campaign: {media_path}")
        
        # For now, show placeholder for campaign management
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Move to Campaign",
            f"Campaign management for:\n{os.path.basename(media_path)}\n\n"
            "(Campaign organization features coming soon)"
        )
    
    def refresh_content(self):
        """Refresh all tab content."""
        self.logger.info("Refreshing library content")
        
        try:
            current_index = self.tab_widget.currentIndex()
            
            # Clear selection tracking
            self.selected_media.clear()
            self.media_widgets.clear()
            
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

    def _open_post_preview(self, post_data):
        """Open the post preview dialog for a finished post."""
        try:
            from ..dialogs.post_preview_dialog import PostPreviewDialog
            
            dialog = PostPreviewDialog(post_data, parent=self)
            
            # Connect signals
            dialog.post_now_requested.connect(self._handle_post_now)
            dialog.add_to_campaign_requested.connect(self._handle_add_to_campaign)
            dialog.schedule_post_requested.connect(self._handle_schedule_post)
            dialog.edit_post_requested.connect(self._handle_edit_post)
            
            dialog.exec()
            
        except Exception as e:
            self.logger.error(f"Error opening post preview: {e}")
            QMessageBox.critical(self, "Error", f"Could not open post preview: {str(e)}")
    
    def _handle_post_now(self, post_data):
        """Handle post now request from preview dialog."""
        try:
            platforms = ", ".join(post_data.get('platforms', []))
            self.logger.info(f"Post now requested for platforms: {platforms}")
            
            # TODO: Implement actual posting logic
            QMessageBox.information(
                self, 
                "Post Now", 
                f"Post would be published immediately to: {platforms}\n\n"
                "(Publishing integration coming soon)"
            )
            
        except Exception as e:
            self.logger.error(f"Error in post now: {e}")
            QMessageBox.critical(self, "Error", f"Could not post now: {str(e)}")
    
    def _handle_add_to_campaign(self, post_data):
        """Handle add to campaign request from preview dialog."""
        try:
            platforms = ", ".join(post_data.get('platforms', []))
            self.logger.info(f"Add to campaign requested for platforms: {platforms}")
            
            # TODO: Implement campaign selection/creation dialog
            QMessageBox.information(
                self, 
                "Add to Campaign", 
                f"Post would be added to a campaign for: {platforms}\n\n"
                "(Campaign management coming next)"
            )
            
        except Exception as e:
            self.logger.error(f"Error adding to campaign: {e}")
            QMessageBox.critical(self, "Error", f"Could not add to campaign: {str(e)}")
    
    def _handle_schedule_post(self, post_data):
        """Handle schedule post request from preview dialog."""
        try:
            platforms = ", ".join(post_data.get('platforms', []))
            self.logger.info(f"Schedule post requested for platforms: {platforms}")
            
            # TODO: Implement scheduling dialog
            QMessageBox.information(
                self, 
                "Schedule Post", 
                f"Post would be scheduled for: {platforms}\n\n"
                "(Scheduling interface coming soon)"
            )
            
        except Exception as e:
            self.logger.error(f"Error scheduling post: {e}")
            QMessageBox.critical(self, "Error", f"Could not schedule post: {str(e)}")
    
    def _handle_edit_post(self, post_data):
        """Handle edit post request from preview dialog."""
        try:
            media_path = post_data.get('path', '')
            self.logger.info(f"Edit post requested for: {media_path}")
            
            # Emit signal to trigger post editing
            self.create_post_with_media_requested.emit(media_path)
            
        except Exception as e:
            self.logger.error(f"Error editing post: {e}")
            QMessageBox.critical(self, "Error", f"Could not edit post: {str(e)}")
    
    def _on_media_selection_changed(self, media_path: str, is_selected: bool):
        """Handle media selection change."""
        if is_selected:
            self.selected_media.add(media_path)
        else:
            self.selected_media.discard(media_path)
        
        self._update_selection_ui()
    
    def _update_selection_ui(self):
        """Update the selection UI based on current selection."""
        count = len(self.selected_media)
        self.selected_count_label.setText(f"{count} selected")
        
        # Enable/disable action buttons based on selection
        has_selection = count > 0
        self.create_gallery_btn.setEnabled(has_selection)
        self.delete_selected_btn.setEnabled(has_selection)
    
    def _select_all_media_combined(self):
        """Select all media (both photos and videos)."""
        try:
            all_media = self.crowseye_handler.get_all_media()
            
            # Select all photos and videos
            all_media_paths = all_media.get("raw_photos", []) + all_media.get("raw_videos", [])
            
            for media_path in all_media_paths:
                if media_path in self.media_widgets:
                    widget = self.media_widgets[media_path]
                    widget.set_selected(True)
                    
        except Exception as e:
            self.logger.error(f"Error selecting all media: {e}")
    
    def _select_all_media(self, media_type: str):
        """Select all media of the specified type."""
        try:
            all_media = self.crowseye_handler.get_all_media()
            
            if media_type == "Photos":
                media_paths = all_media.get("raw_photos", [])
            else:  # Videos
                media_paths = all_media.get("raw_videos", [])
            
            for media_path in media_paths:
                if media_path in self.media_widgets:
                    widget = self.media_widgets[media_path]
                    widget.set_selected(True)
                    
        except Exception as e:
            self.logger.error(f"Error selecting all media: {e}")
    
    def _clear_selection(self):
        """Clear all media selection."""
        for widget in self.media_widgets.values():
            widget.set_selected(False)
        
        self.selected_media.clear()
        self._update_selection_ui()
    
    def _create_gallery_from_selection(self):
        """Create a gallery from selected media."""
        if not self.selected_media:
            QMessageBox.warning(self, "No Selection", "Please select media files to create a gallery.")
            return
        
        try:
            # Get gallery name from user
            gallery_name, ok = QInputDialog.getText(
                self, 
                "Create Gallery", 
                "Enter gallery name:",
                text=f"Gallery {len(self.selected_media)} items"
            )
            
            if not ok or not gallery_name.strip():
                return
            
            # Create gallery data
            gallery_data = {
                'name': gallery_name.strip(),
                'media_files': list(self.selected_media),
                'created_date': datetime.now().isoformat(),
                'type': 'mixed' if self._has_mixed_media_types() else self._get_media_type_from_selection()
            }
            
            # Create gallery as a collection
            gallery_id = self.library_manager.create_collection(
                name=gallery_name.strip(),
                description=f"Gallery with {len(self.selected_media)} media items"
            )
            
            if gallery_id:
                QMessageBox.information(
                    self, 
                    "Gallery Created", 
                    f"Gallery '{gallery_name}' created successfully with {len(self.selected_media)} items."
                )
                
                # Clear selection
                self._clear_selection()
                
                # Refresh content
                self.refresh_content()
                
                self.logger.info(f"Gallery created: {gallery_name} with {len(self.selected_media)} items")
            else:
                QMessageBox.warning(self, "Error", "Failed to create gallery.")
                
        except Exception as e:
            self.logger.error(f"Error creating gallery: {e}")
            QMessageBox.warning(self, "Error", f"Could not create gallery: {str(e)}")
    
    def _delete_selected_media(self):
        """Delete selected media files."""
        if not self.selected_media:
            QMessageBox.warning(self, "No Selection", "Please select media files to delete.")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(self.selected_media)} selected media files?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            deleted_count = 0
            failed_files = []
            
            for media_path in list(self.selected_media):
                try:
                    if os.path.exists(media_path):
                        os.remove(media_path)
                        deleted_count += 1
                        self.logger.info(f"Deleted media file: {media_path}")
                    else:
                        self.logger.warning(f"Media file not found: {media_path}")
                except Exception as e:
                    self.logger.error(f"Failed to delete {media_path}: {e}")
                    failed_files.append(os.path.basename(media_path))
            
            # Clear selection and refresh
            self._clear_selection()
            self.refresh_content()
            
            # Show result message
            if failed_files:
                QMessageBox.warning(
                    self,
                    "Deletion Complete",
                    f"Deleted {deleted_count} files successfully.\n\n"
                    f"Failed to delete {len(failed_files)} files:\n" + "\n".join(failed_files)
                )
            else:
                QMessageBox.information(
                    self,
                    "Deletion Complete",
                    f"Successfully deleted {deleted_count} media files."
                )
                
        except Exception as e:
            self.logger.error(f"Error deleting selected media: {e}")
            QMessageBox.warning(self, "Error", f"Could not delete media: {str(e)}")
    
    def _has_mixed_media_types(self) -> bool:
        """Check if selection contains both photos and videos."""
        has_photos = False
        has_videos = False
        
        for media_path in self.selected_media:
            if any(ext in media_path.lower() for ext in ['.mp4', '.mov', '.avi', '.mkv', '.wmv']):
                has_videos = True
            else:
                has_photos = True
            
            if has_photos and has_videos:
                return True
        
        return False
    
    def _get_media_type_from_selection(self) -> str:
        """Get the media type from current selection."""
        if not self.selected_media:
            return 'mixed'
        
        # Check first file to determine type
        first_file = next(iter(self.selected_media))
        if any(ext in first_file.lower() for ext in ['.mp4', '.mov', '.avi', '.mkv', '.wmv']):
            return 'video'
        else:
            return 'photo'
 