"""
Additional methods for library_window.py to avoid corruption
"""

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

def _on_generate_gallery_fixed(self):
    """Generate gallery with AI."""
    from .dialogs.gallery_generation_dialog import GalleryGenerationDialog
    
    dialog = GalleryGenerationDialog(self.crowseye_handler, self)
    if dialog.exec():
        # Highlight selected media in the media tab
        selected_paths = dialog.get_selected_media_paths()
        self._highlight_media(selected_paths)
        
        # Switch to galleries tab and refresh
        self.tab_widget.setCurrentIndex(2)
        self.refresh_library()
        self.status_label.setText("Gallery generated!")

def _clear_selection_fixed(self):
    """Clear selection."""
    for media_path in self.selected_media:
        if media_path in self.media_thumbnails:
            self.media_thumbnails[media_path].set_selected(False)
    self.selected_media.clear()
    self._update_selection_display() 