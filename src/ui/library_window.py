"""
Library window for media management and gallery creation workflow.
"""

import os
import logging
from typing import List, Dict, Any

from PySide6.QtCore import Qt, QEvent, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QLabel, QPushButton, QLineEdit, QScrollArea, QMessageBox,
    QFileDialog
)

from .base_window import BaseMainWindow
from .components.gallery_item_widget import GalleryItemWidget
from .components.media_thumbnail_widget import MediaThumbnailWidget
from ..handlers.library_handler import LibraryManager

class LibraryWindow(BaseMainWindow):
    """Main window for the media library with complete selection → gallery workflow."""
    
    gallery_created = Signal(dict)
    generate_post_requested = Signal(str)  # Signal to request post generation with media
    
    def __init__(self, library_manager_instance: LibraryManager, parent=None, scheduler=None):
        self.library_manager = library_manager_instance
        self.scheduler = scheduler
        
        # Initialize handlers
        from ..handlers.crowseye_handler import CrowsEyeHandler
        from ..models.app_state import AppState
        from ..handlers.media_handler import MediaHandler
        
        app_state = AppState()
        self.media_handler = MediaHandler(app_state)
        self.crowseye_handler = CrowsEyeHandler(app_state, self.media_handler, library_manager_instance)
        
        # Selection state for gallery creation
        self.selected_media = []
        self.media_thumbnails = {}
        
        super().__init__(parent)
        self.setWindowTitle("Crow's Eye - Media Library")
        self.setMinimumSize(1000, 700)
        
        # Create UI first
        self._create_ui()
        
        # Connect signals
        self.crowseye_handler.signals.gallery_generated.connect(self._on_gallery_generated)
        
        # Load content
        self.refresh_library()
    
    def _create_ui(self):
        """Create the main UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Media Library")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Upload button
        self.upload_button = QPushButton("File(s) Upload")
        self.upload_button.clicked.connect(self._on_file_upload)
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #059669; color: white; border: none;
                padding: 10px 20px; border-radius: 6px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #047857; }
        """)
        header_layout.addWidget(self.upload_button)
        layout.addLayout(header_layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self._setup_tabs()
        layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #CCCCCC; padding: 5px;")
        layout.addWidget(self.status_label)
    
    def _setup_tabs(self):
        """Set up all tabs."""
        # Media tab
        self.media_tab = QWidget()
        self._setup_media_tab()
        self.tab_widget.addTab(self.media_tab, "Media")
        
        # Other tabs
        for tab_name, setup_method in [
            ("Finished Posts", self._setup_posts_tab),
            ("Finished Galleries", self._setup_galleries_tab),
            ("Finished Reels", self._setup_reels_tab)
        ]:
            tab = QWidget()
            setattr(self, f"{tab_name.lower().replace(' ', '_')}_tab", tab)
            setup_method(tab)
            self.tab_widget.addTab(tab, tab_name)
    
    def _setup_media_tab(self):
        """Set up the Media tab with gallery generation."""
        layout = QVBoxLayout(self.media_tab)
        
        # Header controls
        header_layout = QHBoxLayout()
        self.media_search = QLineEdit()
        self.media_search.setPlaceholderText("Search media...")
        header_layout.addWidget(self.media_search)
        
        self.generate_gallery_button = QPushButton("Generate Gallery")
        self.generate_gallery_button.clicked.connect(self._on_generate_gallery)
        self.generate_gallery_button.setStyleSheet("""
            QPushButton { background-color: #7c3aed; color: white; border: none;
                         padding: 8px 16px; border-radius: 4px; font-size: 12px; }
            QPushButton:hover { background-color: #6d28d9; }
        """)
        header_layout.addWidget(self.generate_gallery_button)
        layout.addLayout(header_layout)
        
        # Selection controls
        self.gallery_controls = QWidget()
        controls_layout = QHBoxLayout(self.gallery_controls)
        
        self.selection_info = QLabel("No items selected")
        self.selection_info.setStyleSheet("color: #FFFFFF; font-size: 12px;")
        controls_layout.addWidget(self.selection_info)
        controls_layout.addStretch()
        
        # Clear and Create buttons
        clear_btn = QPushButton("Clear Selection")
        clear_btn.clicked.connect(self._clear_selection)
        clear_btn.setStyleSheet("""
            QPushButton { background-color: #6b7280; color: white; border: none;
                         padding: 6px 12px; border-radius: 4px; font-size: 11px; }
            QPushButton:hover { background-color: #6b7280cc; }
        """)
        controls_layout.addWidget(clear_btn)
        
        create_btn = QPushButton("Create Gallery")
        create_btn.clicked.connect(self._on_create_gallery_from_selection)
        create_btn.setStyleSheet("""
            QPushButton { background-color: #059669; color: white; border: none;
                         padding: 6px 12px; border-radius: 4px; font-size: 11px; }
            QPushButton:hover { background-color: #059669cc; }
        """)
        controls_layout.addWidget(create_btn)
        
        self.gallery_controls.hide()
        layout.addWidget(self.gallery_controls)
        
        # Media scroll area
        self.media_scroll = QScrollArea()
        self.media_scroll.setWidgetResizable(True)
        self.media_scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.media_container = QWidget()
        self.media_layout = QGridLayout(self.media_container)
        self.media_layout.setSpacing(10)
        self.media_scroll.setWidget(self.media_container)
        layout.addWidget(self.media_scroll)
    
    def _setup_posts_tab(self, tab):
        """Set up posts tab."""
        layout = QVBoxLayout(tab)
        
        search = QLineEdit()
        search.setPlaceholderText("Search finished posts...")
        layout.addWidget(search)
        self.posts_search = search
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(10)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        self.posts_scroll = scroll
        self.posts_container = container
        self.posts_layout = grid
    
    def _setup_galleries_tab(self, tab):
        """Set up galleries tab."""
        layout = QVBoxLayout(tab)
        header = QLabel("Saved Galleries")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(header)
        
        self.galleries_scroll = QScrollArea()
        self.galleries_scroll.setWidgetResizable(True)
        self.galleries_container = QWidget()
        self.galleries_layout = QVBoxLayout(self.galleries_container)
        self.galleries_scroll.setWidget(self.galleries_container)
        layout.addWidget(self.galleries_scroll)
    
    def _setup_reels_tab(self, tab):
        """Set up reels tab."""
        layout = QVBoxLayout(tab)
        
        search = QLineEdit()
        search.setPlaceholderText("Search finished reels...")
        layout.addWidget(search)
        self.reels_search = search
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(10)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        self.reels_scroll = scroll
        self.reels_container = container
        self.reels_layout = grid
    
    def refresh_library(self):
        """Refresh all library content."""
        try:
            self.status_label.setText("Refreshing...")
            self._load_media_tab()
            self._load_finished_posts()
            self._load_finished_galleries()
            self.status_label.setText("Library refreshed")
        except Exception as e:
            logging.error(f"Error refreshing: {e}")
            if hasattr(self, 'status_label'):
                self.status_label.setText("Error refreshing")
    
    def _load_media_tab(self):
        """Load media into the media tab."""
        try:
            self._clear_layout(self.media_layout)
            self.media_thumbnails.clear()
            
            all_media = self.crowseye_handler.get_all_media()
            row, col = 0, 0
            cols_per_row = 8
            
            for media_type in ["raw_photos", "raw_videos"]:
                for media_path in all_media.get(media_type, []):
                    if os.path.exists(media_path):
                        widget_type = "image" if media_type == "raw_photos" else "video"
                        thumbnail = MediaThumbnailWidget(media_path, widget_type)
                        thumbnail.clicked.connect(self._on_media_item_selected)
                        thumbnail.generate_post_requested.connect(self._on_generate_post_requested)
                        
                        self.media_layout.addWidget(thumbnail, row, col)
                        self.media_thumbnails[media_path] = thumbnail
                        
                        col += 1
                        if col >= cols_per_row:
                            col = 0
                            row += 1
            
            self.media_layout.setRowStretch(row + 1, 1)
            self.media_layout.setColumnStretch(cols_per_row, 1)
            
        except Exception as e:
            logging.error(f"Error loading media: {e}")
    
    def _load_finished_posts(self):
        """Load finished posts."""
        try:
            self._clear_layout(self.posts_layout)
            posts = self.library_manager.get_all_post_ready_items()
            self._load_thumbnails_to_grid(posts, self.posts_layout)
        except Exception as e:
            logging.error(f"Error loading posts: {e}")
    
    def _load_finished_galleries(self):
        """Load finished galleries."""
        try:
            self._clear_layout(self.galleries_layout)
            galleries = self.crowseye_handler.get_saved_galleries()
            
            for gallery in galleries:
                widget = GalleryItemWidget(gallery, self.media_handler, self)
                widget.view_edit_requested.connect(self._on_view_edit_gallery_clicked)
                widget.add_media_requested.connect(self._on_add_media_to_gallery_clicked)
                self.galleries_layout.addWidget(widget)
        except Exception as e:
            logging.error(f"Error loading galleries: {e}")
    
    def _load_thumbnails_to_grid(self, items, grid_layout):
        """Helper to load thumbnails into a grid."""
        row, col = 0, 0
        cols_per_row = 8
        
        for item in items:
            if 'path' in item and os.path.exists(item['path']):
                media_type = "video" if item['path'].lower().endswith(('.mp4', '.mov', '.avi', '.mkv')) else "image"
                thumbnail = MediaThumbnailWidget(item['path'], media_type, show_generate_post=False)
                
                # Connect finished post click to show post options dialog
                thumbnail.clicked.connect(lambda path=item['path'], item_data=item: self._on_finished_post_clicked(path, item_data))
                
                grid_layout.addWidget(thumbnail, row, col)
                
                col += 1
                if col >= cols_per_row:
                    col = 0
                    row += 1
        
        grid_layout.setRowStretch(row + 1, 1)
        grid_layout.setColumnStretch(cols_per_row, 1)
    
    def _clear_layout(self, layout):
        """Clear all widgets from a layout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _on_media_item_selected(self, media_path):
        """Handle media selection."""
        if media_path in self.selected_media:
            self.selected_media.remove(media_path)
            self.media_thumbnails[media_path].set_selected(False)
        else:
            self.selected_media.append(media_path)
            self.media_thumbnails[media_path].set_selected(True)
        
        self._update_selection_display()
    
    def _update_selection_display(self):
        """Update selection display."""
        count = len(self.selected_media)
        if count == 0:
            self.selection_info.setText("No items selected")
            self.gallery_controls.hide()
        else:
            self.selection_info.setText(f"{count} item{'s' if count != 1 else ''} selected")
            self.gallery_controls.show()
    
    def _clear_selection(self):
        """Clear selection."""
        for media_path in self.selected_media:
            if media_path in self.media_thumbnails:
                self.media_thumbnails[media_path].set_selected(False)
        self.selected_media.clear()
        self._update_selection_display()
    
    def _highlight_media(self, media_paths):
        """Highlight specific media paths in the media tab."""
        # Clear current selection first
        self._clear_selection()
        
        # Select the specified media paths
        for media_path in media_paths:
            if media_path in self.media_thumbnails:
                self.selected_media.append(media_path)
                self.media_thumbnails[media_path].set_selected(True)
        
        # Update display and switch to media tab
        self._update_selection_display()
        self.tab_widget.setCurrentIndex(0)  # Switch to Media tab
    
    def _on_generate_gallery(self):
        """Generate gallery with AI."""
        from .dialogs.gallery_generation_dialog import GalleryGenerationDialog
        
        dialog = GalleryGenerationDialog(self.crowseye_handler, self)
        if dialog.exec():
            # Highlight selected media in the media tab
            selected_paths = dialog.get_selected_media_paths()
            if selected_paths:
                self._highlight_media(selected_paths)
            
            # Switch to galleries tab and refresh
            self.tab_widget.setCurrentIndex(2)
            self.refresh_library()
            self.status_label.setText("Gallery generated!")
    
    def _on_create_gallery_from_selection(self):
        """Create gallery from selection."""
        if not self.selected_media:
            QMessageBox.warning(self, "No Selection", "Please select media items first.")
            return
        
        from .dialogs.save_gallery_dialog import SaveGalleryDialog
        
        dialog = SaveGalleryDialog(self.selected_media, self.crowseye_handler, self)
        if dialog.exec():
            self._clear_selection()
            self._load_finished_galleries()
            self.tab_widget.setCurrentIndex(2)
            self.status_label.setText("Gallery created!")
    

    def _on_add_media_to_gallery_clicked(self, gallery_data):
        """Handle add media to gallery request."""
        from .dialogs.media_selection_dialog import MediaSelectionDialog
        
        try:
            # Get all available media for selection
            all_media = self.crowseye_handler.get_all_media()
            all_media_paths = []
            for media_type, paths in all_media.items():
                all_media_paths.extend(paths)
            
            if not all_media_paths:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "No Media", "No media available to add. Please upload some media first.")
                return
            
            # Open media selection dialog
            dialog = MediaSelectionDialog(all_media_paths, self)
            if dialog.exec():
                selected_media = dialog.get_selected_media()
                if selected_media:
                    # Add selected media to the gallery
                    gallery_filename = gallery_data.get('filename', '')
                    if gallery_filename:
                        success = self.crowseye_handler.add_media_to_gallery(gallery_filename, selected_media)
                        if success:
                            self._load_finished_galleries()  # Refresh galleries
                            self.status_label.setText(f"Added {len(selected_media)} media item(s) to gallery")
                        else:
                            from PySide6.QtWidgets import QMessageBox
                            QMessageBox.warning(self, "Error", "Failed to add media to gallery.")
                    else:
                        from PySide6.QtWidgets import QMessageBox
                        QMessageBox.warning(self, "Error", "Gallery filename not found.")
                
        except Exception as e:
            import logging
            logging.error(f"Error adding media to gallery: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to add media to gallery: {str(e)}")

    def _on_view_edit_gallery_clicked(self, gallery_data):
        """View/edit gallery."""
        from .dialogs.gallery_viewer_dialog import GalleryViewerDialog
        
        dialog = GalleryViewerDialog(gallery_data, self.crowseye_handler, self)
        if dialog.exec():
            self._load_finished_galleries()
    
    def _on_gallery_generated(self, media_paths):
        """Handle gallery generation completion."""
        self.status_label.setText(f"Gallery generated with {len(media_paths)} items")
    
    def _on_generate_post_requested(self, media_path):
        """Handle request to generate post with specific media."""
        try:
            # Emit signal to main window to load this media for post generation
            self.generate_post_requested.emit(media_path)
            
            # Close the library window to return to main window
            self.close()
            
        except Exception as e:
            logging.error(f"Error handling generate post request: {e}")
            QMessageBox.warning(self, "Error", f"Could not load media for post generation: {str(e)}")
    
    def _on_finished_post_clicked(self, media_path, item_data):
        """Handle finished post click to show post preview dialog."""
        try:
            from .dialogs.post_preview_dialog import PostPreviewDialog
            
            # Prepare post data for the dialog
            post_data = {
                "media_path": media_path,
                "caption": item_data.get("caption", ""),
                "id": item_data.get("id", ""),
                "is_post_ready": True
            }
            
            # Show post preview dialog with media handler
            dialog = PostPreviewDialog(self, post_data, self.media_handler)
            
            # Connect dialog signals
            dialog.post_now.connect(self._on_post_now)
            dialog.add_to_queue.connect(self._on_add_to_queue)
            dialog.edit_post.connect(self._on_edit_post)
            dialog.delete_post.connect(self._on_delete_post)
            
            dialog.exec()
            
        except Exception as e:
            logging.error(f"Error showing post preview for {media_path}: {e}")
            QMessageBox.warning(self, "Error", f"Could not show post preview: {str(e)}")
    
    def _on_post_now(self, post_data):
        """Handle post now request."""
        try:
            # TODO: Implement actual posting logic
            platforms = post_data.get("platforms", [])
            media_path = post_data.get("media_path", "")
            
            platform_names = ", ".join(platforms)
            QMessageBox.information(
                self, 
                "Post Scheduled", 
                f"Post will be published to {platform_names}\n\nMedia: {os.path.basename(media_path)}"
            )
            
        except Exception as e:
            logging.error(f"Error posting now: {e}")
            QMessageBox.warning(self, "Error", f"Could not post now: {str(e)}")
    
    def _on_add_to_queue(self, post_data):
        """Handle add to queue request."""
        try:
            # TODO: Implement actual queue logic
            media_path = post_data.get("media_path", "")
            
            QMessageBox.information(
                self, 
                "Added to Queue", 
                f"Post added to publishing queue\n\nMedia: {os.path.basename(media_path)}"
            )
            
        except Exception as e:
            logging.error(f"Error adding to queue: {e}")
            QMessageBox.warning(self, "Error", f"Could not add to queue: {str(e)}")
    
    def _on_edit_post(self, post_data):
        """Handle edit post request."""
        try:
            # Emit signal to main window to load this media for editing
            media_path = post_data.get("media_path", "")
            self.generate_post_requested.emit(media_path)
            
            # Close the library window to return to main window
            self.close()
            
        except Exception as e:
            logging.error(f"Error editing post: {e}")
            QMessageBox.warning(self, "Error", f"Could not edit post: {str(e)}")
    
    def _on_delete_post(self, post_data):
        """Handle delete post request."""
        try:
            # Remove from library
            item_id = post_data.get("id", "")
            if item_id and hasattr(self.library_manager, 'remove_item'):
                success = self.library_manager.remove_item(item_id)
                if success:
                    QMessageBox.information(self, "Post Deleted", "Post has been deleted successfully.")
                    self.refresh_library()  # Refresh to update the display
                else:
                    QMessageBox.warning(self, "Error", "Could not delete post from library.")
            else:
                QMessageBox.warning(self, "Error", "Could not find post to delete.")
                
        except Exception as e:
            logging.error(f"Error deleting post: {e}")
            QMessageBox.warning(self, "Error", f"Could not delete post: {str(e)}")
    
    def _on_file_upload(self):
        """Handle file upload."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Media Files", "",
            "Image and Video Files (*.jpg *.jpeg *.png *.gif *.bmp *.mp4 *.mov *.avi *.mkv *.wmv);;All Files (*)"
        )
        
        if file_paths:
            try:
                import shutil
                uploaded = 0
                media_library_dir = "media_library"
                
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
                        logging.info(f"Uploaded file: {filename} -> {dest_path}")
                
                self.status_label.setText(f"Uploaded {uploaded} file(s)")
                self.refresh_library()
                
            except Exception as e:
                logging.error(f"Upload error: {e}")
                QMessageBox.critical(self, "Upload Error", f"Failed to upload: {str(e)}")
    
    def set_theme(self, is_dark: bool) -> None:
        """Set theme."""
        pass
    
    def closeEvent(self, event: QEvent):
        """Handle close."""
        event.accept()
    
    def retranslateUi(self):
        """Retranslate UI."""
        pass 