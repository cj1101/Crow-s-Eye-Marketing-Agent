"""
Media section component for the main application window.
"""
import os
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QFrame, QScrollArea, QGridLayout, QSizePolicy, QHBoxLayout
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QPixmap, QIcon

from src.config import constants as const

class MediaSection(QWidget):
    """Media section for displaying and selecting media."""
    
    # Signals
    media_selected = Signal(str)
    toggle_view = Signal(bool)    # Signal to toggle between original/edited view (True = showing edited)
    
    def __init__(self, parent=None):
        """Initialize the media section."""
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize properties
        self.current_media_path = None
        self.edited_media_path = None
        self.showing_edited = False
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the media section UI components."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("Media Selection")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # Media preview area
        self.media_preview = QLabel("No media selected")
        self.media_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_preview.setMinimumHeight(300)
        self.media_preview.setStyleSheet("""
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 4px;
        """)
        self.media_preview.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.media_preview)
        
        # Button container
        button_layout = QHBoxLayout()
        
        # Media selection button
        self.select_btn = QPushButton("Select Media")
        self.select_btn.setStyleSheet("""
            background-color: #4a86e8;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
        """)
        self.select_btn.clicked.connect(self._on_select_media)
        button_layout.addWidget(self.select_btn)
        
        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet("""
            background-color: #e74c3c;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
        """)
        self.clear_btn.clicked.connect(self._on_clear_media)
        button_layout.addWidget(self.clear_btn)
        
        # Toggle view button (between original and edited)
        self.toggle_btn = QPushButton("Show Original")
        self.toggle_btn.setStyleSheet("""
            background-color: #9b59b6;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
        """)
        self.toggle_btn.clicked.connect(self._on_toggle_view)
        self.toggle_btn.setEnabled(False)  # Disabled until edited version exists
        button_layout.addWidget(self.toggle_btn)
        
        # Add button layout to main layout
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #555; font-style: italic;")
        layout.addWidget(self.status_label)
        
    def _on_select_media(self):
        """Handle media selection button click."""
        try:
            # Open file dialog
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Media",
                os.path.expanduser("~"),
                "Image Files (*.png *.jpg *.jpeg);;Video Files (*.mp4 *.mov);;All Files (*.*)"
            )
            
            if file_path:
                self.set_media(file_path)
                self.media_selected.emit(file_path)
                self.showing_edited = False
                self.toggle_btn.setEnabled(False)
                self._update_toggle_button_text()
            
        except Exception as e:
            self.logger.exception(f"Error selecting media: {e}")
    
    def _on_clear_media(self):
        """Clear selected media."""
        self.current_media_path = None
        self.edited_media_path = None
        self.media_preview.setText("No media selected")
        self.media_preview.setPixmap(QPixmap())  # Clear pixmap
        self.media_selected.emit("")  # Emit empty string to indicate no selection
        self.showing_edited = False
        self._update_toggle_button_text()
        self.status_label.setText("")
    
    def _on_toggle_view(self):
        """Toggle between original and edited image view."""
        if self.edited_media_path and self.current_media_path:
            self.showing_edited = not self.showing_edited
            self._update_toggle_button_text()
            
            # Update the displayed image
            if self.showing_edited and os.path.exists(self.edited_media_path):
                self.set_media_display(self.edited_media_path)
                self.status_label.setText("Showing edited image")
            else:
                self.set_media_display(self.current_media_path)
                self.status_label.setText("Showing original image")
                
            # Emit signal about the change
            self.toggle_view.emit(self.showing_edited)
    
    def _update_toggle_button_text(self):
        """Update the toggle button text based on current state."""
        if self.showing_edited:
            self.toggle_btn.setText("Show Original")
        else:
            self.toggle_btn.setText("Show Edited")
    
    def set_media(self, media_path):
        """
        Set the media to display.
        
        Args:
            media_path: Path to the media file
        """
        if not media_path or not os.path.exists(media_path):
            self._on_clear_media()
            return
            
        self.current_media_path = media_path
        self.set_media_display(media_path)
        
    def set_media_display(self, media_path):
        """
        Set the media display without changing the current media path.
        Used for toggling between original and edited views.
        
        Args:
            media_path: Path to the media file to display
        """
        if not media_path or not os.path.exists(media_path):
            self.media_preview.setText("File not found")
            return
            
        self.logger.info(f"Setting media display to: {media_path}")
            
        # Check file extension to determine media type
        _, ext = os.path.splitext(media_path.lower())
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif']:
            # Clear existing pixmap first
            self.media_preview.clear()
            
            # Force load a fresh copy of the image
            pixmap = QPixmap()
            pixmap.load(media_path)
            
            if not pixmap.isNull():
                # Scale pixmap to fit label while preserving aspect ratio
                scaled_pixmap = pixmap.scaled(
                    self.media_preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.media_preview.setPixmap(scaled_pixmap)
                self.logger.info(f"Displayed image with dimensions: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
            else:
                self.media_preview.setText(f"Error loading image: {os.path.basename(media_path)}")
                self.logger.error(f"Failed to load image: {media_path}")
        else:
            # For other media types, just show the filename
            self.media_preview.setText(f"Selected: {os.path.basename(media_path)}")
    
    def set_edited_media(self, edited_path):
        """
        Set the edited media path and enable toggle functionality.
        
        Args:
            edited_path: Path to the edited media file
        """
        if edited_path and os.path.exists(edited_path):
            self.logger.info(f"Setting edited media path: {edited_path}")
            self.edited_media_path = edited_path
            self.toggle_btn.setEnabled(True)
            
            # Switch to showing the edited version
            self.showing_edited = True
            self._update_toggle_button_text()
            
            # Clear the current image before loading the new one
            self.media_preview.clear()
            
            # Load and display the edited image
            self.set_media_display(edited_path)
            self.status_label.setText("Showing edited image")
            
            # Emit signal about the change
            self.toggle_view.emit(True)
        else:
            self.logger.warning(f"Cannot set edited media - file not found: {edited_path}")
            self.toggle_btn.setEnabled(False)
    
    def get_current_display_path(self):
        """
        Get the path of the currently displayed image (original or edited).
        
        Returns:
            str: Path to the currently displayed image
        """
        if self.showing_edited and self.edited_media_path:
            return self.edited_media_path
        return self.current_media_path
    
    def resizeEvent(self, event):
        """Handle resize events to update the scaled media if needed."""
        super().resizeEvent(event)
        
        # If media is set, rescale it
        if self.showing_edited and self.edited_media_path and os.path.exists(self.edited_media_path):
            self.set_media_display(self.edited_media_path)
        elif self.current_media_path and os.path.exists(self.current_media_path):
            self.set_media_display(self.current_media_path)
            
    def refresh_media(self):
        """Refresh the currently displayed media."""
        current_display = self.get_current_display_path()
        if current_display and os.path.exists(current_display):
            # Force a complete reload
            self.media_preview.clear()
            # Load and display the current image again
            self.set_media_display(current_display) 