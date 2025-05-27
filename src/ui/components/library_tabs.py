"""
Library tabs component - Simple tab structure for the new library layout.
"""
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QLabel, QPushButton, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class LibraryTabs(QWidget):
    """Simple library tabs widget following the new specification."""
    
    # Signals
    media_file_selected = Signal(str)  # file_path
    finished_post_selected = Signal(dict)  # post_data
    create_gallery_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
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
        
        # Placeholder for now
        placeholder_label = QLabel(f"No {post_type.lower()} posts found")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet("color: #666666; font-size: 14px; padding: 40px;")
        grid_layout.addWidget(placeholder_label, 0, 0)
        
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)
        
        return tab
        
    def refresh_content(self):
        """Refresh all tab content."""
        self.logger.info("Refreshing library content")
        # TODO: Implement content loading
        pass
        
    def retranslateUi(self):
        """Update UI text for internationalization."""
        # TODO: Implement when i18n is needed
        pass 