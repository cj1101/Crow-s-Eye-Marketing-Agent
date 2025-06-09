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
from ..utils.subscription_utils import (
    check_feature_access_with_dialog, check_usage_limit_with_dialog,
    requires_feature_qt, requires_usage_qt, show_upgrade_dialog
)
from ..features.subscription.access_control import Feature

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
        self.setWindowTitle(self.tr("Crow's Eye - Media Library"))
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
        self.title_label = QLabel(self.tr("Media Library"))
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        # Upload button
        self.upload_button = QPushButton(self.tr("File(s) Upload"))
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
        self.status_label = QLabel(self.tr("Ready"))
        self.status_label.setStyleSheet("color: #CCCCCC; padding: 5px;")
        layout.addWidget(self.status_label)
    
    def _setup_tabs(self):
        """Set up all tabs."""
        # Media tab
        self.media_tab = QWidget()
        self._setup_media_tab()
        self.tab_widget.addTab(self.media_tab, self.tr("Media"))
        
        # Other tabs
        tab_configs = [
            ("Finished Posts", self._setup_posts_tab),
            ("Finished Galleries", self._setup_galleries_tab),
            ("Finished Reels", self._setup_reels_tab)
        ]
        
        for tab_name, setup_method in tab_configs:
            tab = QWidget()
            setattr(self, f"{tab_name.lower().replace(' ', '_')}_tab", tab)
            setup_method(tab)
            self.tab_widget.addTab(tab, self.tr(tab_name))
    
    def _setup_media_tab(self):
        """Set up the Media tab with gallery generation."""
        layout = QVBoxLayout(self.media_tab)
        
        # Header controls
        header_layout = QHBoxLayout()
        self.media_search = QLineEdit()
        self.media_search.setPlaceholderText(self.tr("Search media..."))
        header_layout.addWidget(self.media_search)
        
        self.generate_gallery_button = QPushButton(self.tr("Generate Gallery"))
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
        
        self.selection_info = QLabel(self.tr("No items selected"))
        self.selection_info.setStyleSheet("color: #FFFFFF; font-size: 12px;")
        controls_layout.addWidget(self.selection_info)
        controls_layout.addStretch()
        
        # Clear and Create buttons
        self.clear_btn = QPushButton(self.tr("Clear Selection"))
        self.clear_btn.clicked.connect(self._clear_selection)
        self.clear_btn.setStyleSheet("""
            QPushButton { background-color: #6b7280; color: white; border: none;
                         padding: 6px 12px; border-radius: 4px; font-size: 11px; }
            QPushButton:hover { background-color: #6b7280cc; }
        """)
        controls_layout.addWidget(self.clear_btn)
        
        self.create_btn = QPushButton(self.tr("Create Gallery"))
        self.create_btn.clicked.connect(self._on_create_gallery_from_selection)
        self.create_btn.setStyleSheet("""
            QPushButton { background-color: #059669; color: white; border: none;
                         padding: 6px 12px; border-radius: 4px; font-size: 11px; }
            QPushButton:hover { background-color: #059669cc; }
        """)
        controls_layout.addWidget(self.create_btn)
        
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
        
        self.posts_search = QLineEdit()
        self.posts_search.setPlaceholderText(self.tr("Search finished posts..."))
        layout.addWidget(self.posts_search)
        
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
        self.galleries_header = QLabel(self.tr("Saved Galleries"))
        self.galleries_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(self.galleries_header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(10)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        self.galleries_scroll = scroll
        self.galleries_container = container
        self.galleries_layout = grid
    
    def _setup_reels_tab(self, tab):
        """Set up reels tab."""
        layout = QVBoxLayout(tab)
        self.reels_header = QLabel(self.tr("Finished Reels"))
        self.reels_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(self.reels_header)
        
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
            self.status_label.setText(self.tr("Refreshing..."))
            self._load_media_tab()
            self._load_finished_posts()
            self._load_finished_galleries()
            self.status_label.setText(self.tr("Library refreshed"))
        except Exception as e:
            logging.error(f"Error refreshing: {e}")
            if hasattr(self, 'status_label'):
                self.status_label.setText(self.tr("Error refreshing"))
    
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
            self.selection_info.setText(self.tr("No items selected"))
            self.gallery_controls.hide()
        else:
            self.selection_info.setText(self.tr("{count} item(s) selected").format(count=count))
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
    
    @requires_feature_qt(Feature.SMART_GALLERY_GENERATOR)
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
            self.status_label.setText(self.tr("Gallery generated!"))
    
    def _on_create_gallery_from_selection(self):
        """Create gallery from selection."""
        if not self.selected_media:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select media items first."))
            return
        
        from .dialogs.save_gallery_dialog import SaveGalleryDialog
        
        dialog = SaveGalleryDialog(self.selected_media, self.crowseye_handler, self)
        if dialog.exec():
            self._clear_selection()
            self._load_finished_galleries()
            self.tab_widget.setCurrentIndex(2)
            self.status_label.setText(self.tr("Gallery created!"))
    

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
                QMessageBox.information(self, self.tr("No Media"), self.tr("No media available to add. Please upload some media first."))
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
                            self.status_label.setText(self.tr("Added {count} media item(s) to gallery").format(count=len(selected_media)))
                        else:
                            from PySide6.QtWidgets import QMessageBox
                            QMessageBox.warning(self, self.tr("Error"), self.tr("Failed to add media to gallery."))
                    else:
                        from PySide6.QtWidgets import QMessageBox
                        QMessageBox.warning(self, self.tr("Error"), self.tr("Gallery filename not found."))
                
        except Exception as e:
            import logging
            logging.error(f"Error adding media to gallery: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to add media to gallery: {error}").format(error=str(e)))

    def _on_view_edit_gallery_clicked(self, gallery_data):
        """View/edit gallery."""
        from .dialogs.gallery_viewer_dialog import GalleryViewerDialog
        
        dialog = GalleryViewerDialog(gallery_data, self.crowseye_handler, self)
        if dialog.exec():
            self._load_finished_galleries()
    
    def _on_gallery_generated(self, media_paths):
        """Handle gallery generation completion."""
        self.status_label.setText(self.tr("Gallery generated with {count} items").format(count=len(media_paths)))
    
    def _on_generate_post_requested(self, media_path):
        """Handle request to generate post with specific media."""
        try:
            # Emit signal to main window to load this media for post generation
            self.generate_post_requested.emit(media_path)
            
            # Close the library window to return to main window
            self.close()
            
        except Exception as e:
            logging.error(f"Error handling generate post request: {e}")
            QMessageBox.warning(self, self.tr("Error"), self.tr("Could not load media for post generation: {error}").format(error=str(e)))
    
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
            QMessageBox.warning(self, self.tr("Error"), self.tr("Could not show post preview: {error}").format(error=str(e)))
    
    def _on_post_now(self, post_data):
        """Handle post now request."""
        try:
            platforms = post_data.get("platforms", [])
            media_path = post_data.get("media_path", "")
            caption = post_data.get("caption", "")
            
            if not hasattr(self, 'post_publisher'):
                from ..handlers.post_publisher import PostPublisher
                self.post_publisher = PostPublisher()
                
                # Connect signals for feedback
                self.post_publisher.publishing_completed.connect(self._on_publishing_completed)
                self.post_publisher.publishing_failed.connect(self._on_publishing_failed)
            
            # Start publishing
            job_id = self.post_publisher.publish_now(media_path, caption, platforms)
            
            platform_names = ", ".join(platforms)
            QMessageBox.information(
                self, 
                self.tr("Publishing Started"), 
                self.tr("Publishing to {platforms}...\n\nMedia: {media}\nJob ID: {job_id}").format(
                    platforms=platform_names, 
                    media=os.path.basename(media_path),
                    job_id=job_id[:8]
                )
            )
            
        except Exception as e:
            logging.error(f"Error posting now: {e}")
            QMessageBox.warning(self, self.tr("Error"), self.tr("Could not post now: {error}").format(error=str(e)))
    
    def _on_add_to_queue(self, post_data):
        """Handle add to queue request."""
        try:
            platforms = post_data.get("platforms", [])
            media_path = post_data.get("media_path", "")
            caption = post_data.get("caption", "")
            scheduled_at = post_data.get("scheduled_at")
            
            if not hasattr(self, 'post_publisher'):
                from ..handlers.post_publisher import PostPublisher
                self.post_publisher = PostPublisher()
                
                # Connect signals for feedback
                self.post_publisher.publishing_completed.connect(self._on_publishing_completed)
                self.post_publisher.publishing_failed.connect(self._on_publishing_failed)
            
            # Add to queue
            job_id = self.post_publisher.add_to_queue(media_path, caption, platforms, scheduled_at)
            
            QMessageBox.information(
                self, 
                self.tr("Added to Queue"), 
                self.tr("Post added to publishing queue\n\nMedia: {media}\nJob ID: {job_id}").format(
                    media=os.path.basename(media_path),
                    job_id=job_id[:8]
                )
            )
            
        except Exception as e:
            logging.error(f"Error adding to queue: {e}")
            QMessageBox.warning(self, self.tr("Error"), self.tr("Could not add to queue: {error}").format(error=str(e)))
    
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
            QMessageBox.warning(self, self.tr("Error"), self.tr("Could not edit post: {error}").format(error=str(e)))
    
    def _on_delete_post(self, post_data):
        """Handle delete post request."""
        try:
            # Remove from library
            item_id = post_data.get("id", "")
            if item_id and hasattr(self.library_manager, 'remove_item'):
                success = self.library_manager.remove_item(item_id)
                if success:
                    QMessageBox.information(self, self.tr("Post Deleted"), self.tr("Post has been deleted successfully."))
                    self.refresh_library()  # Refresh to update the display
                else:
                    QMessageBox.warning(self, self.tr("Error"), self.tr("Could not delete post from library."))
            else:
                QMessageBox.warning(self, self.tr("Error"), self.tr("Could not find post to delete."))
                
        except Exception as e:
            logging.error(f"Error deleting post: {e}")
            QMessageBox.warning(self, self.tr("Error"), self.tr("Could not delete post: {error}").format(error=str(e)))
    
    def _on_file_upload(self):
        """Handle file upload."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, self.tr("Select Media Files"), "",
            self.tr("Image and Video Files (*.jpg *.jpeg *.png *.gif *.bmp *.mp4 *.mov *.avi *.mkv *.wmv);;All Files (*)")
        )
        
        if file_paths:
            try:
                import shutil
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
                        logging.info(f"Uploaded file: {filename} -> {dest_path}")
                
                self.status_label.setText(self.tr("Uploaded {count} file(s)").format(count=uploaded))
                self.refresh_library()
                
            except Exception as e:
                logging.error(f"Upload error: {e}")
                QMessageBox.critical(self, self.tr("Upload Error"), self.tr("Failed to upload: {error}").format(error=str(e)))
    
    def set_theme(self, is_dark: bool) -> None:
        """Set theme."""
        pass
    
    def closeEvent(self, event: QEvent):
        """Handle close."""
        event.accept()
    
    def _on_publishing_completed(self, job_id: str):
        """Handle publishing completion."""
        try:
            if hasattr(self, 'post_publisher'):
                job = self.post_publisher.get_job_status(job_id)
                if job:
                    successful_platforms = [p for p, r in job.results.items() if r.get("status") == "success"]
                    failed_platforms = [p for p, r in job.results.items() if r.get("status") == "failed"]
                    
                    if successful_platforms:
                        QMessageBox.information(
                            self,
                            self.tr("Publishing Complete"),
                            self.tr("Successfully published to: {platforms}").format(
                                platforms=", ".join(successful_platforms)
                            )
                        )
                    
                    if failed_platforms:
                        QMessageBox.warning(
                            self,
                            self.tr("Publishing Issues"),
                            self.tr("Failed to publish to: {platforms}").format(
                                platforms=", ".join(failed_platforms)
                            )
                        )
        except Exception as e:
            logging.error(f"Error handling publishing completion: {e}")
    
    def _on_publishing_failed(self, job_id: str, platform: str, error: str):
        """Handle publishing failure."""
        try:
            QMessageBox.warning(
                self,
                self.tr("Publishing Failed"),
                self.tr("Failed to publish to {platform}: {error}").format(
                    platform=platform,
                    error=error
                )
            )
        except Exception as e:
            logging.error(f"Error handling publishing failure: {e}")

    def retranslateUi(self):
        """Retranslate UI elements when language changes."""
        # Window title
        self.setWindowTitle(self.tr("Crow's Eye - Media Library"))
        
        # Header elements
        if hasattr(self, 'title_label'):
            self.title_label.setText(self.tr("Media Library"))
        if hasattr(self, 'upload_button'):
            self.upload_button.setText(self.tr("File(s) Upload"))
        
        # Tab names
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setTabText(0, self.tr("Media"))
            self.tab_widget.setTabText(1, self.tr("Finished Posts"))
            self.tab_widget.setTabText(2, self.tr("Finished Galleries"))
            self.tab_widget.setTabText(3, self.tr("Finished Reels"))
        
        # Media tab elements
        if hasattr(self, 'media_search'):
            self.media_search.setPlaceholderText(self.tr("Search media..."))
        if hasattr(self, 'generate_gallery_button'):
            self.generate_gallery_button.setText(self.tr("Generate Gallery"))
        if hasattr(self, 'clear_btn'):
            self.clear_btn.setText(self.tr("Clear Selection"))
        if hasattr(self, 'create_btn'):
            self.create_btn.setText(self.tr("Create Gallery"))
        
        # Posts tab elements
        if hasattr(self, 'posts_search'):
            self.posts_search.setPlaceholderText(self.tr("Search finished posts..."))
        
        # Galleries tab elements
        if hasattr(self, 'galleries_header'):
            self.galleries_header.setText(self.tr("Saved Galleries"))
        
        # Reels tab elements
        if hasattr(self, 'reels_header'):
            self.reels_header.setText(self.tr("Finished Reels"))
        
        # Update selection display
        self._update_selection_display()
        
        # Status label - only update if it shows a static message
        if hasattr(self, 'status_label') and self.status_label.text() in [
            "Ready", "Refreshing...", "Library refreshed", "Error refreshing"
        ]:
            current_text = self.status_label.text()
            if current_text == "Ready":
                self.status_label.setText(self.tr("Ready"))
            elif current_text == "Refreshing...":
                self.status_label.setText(self.tr("Refreshing..."))
            elif current_text == "Library refreshed":
                self.status_label.setText(self.tr("Library refreshed"))
            elif current_text == "Error refreshing":
                self.status_label.setText(self.tr("Error refreshing")) 