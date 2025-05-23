"""
Media section component for the main application window.
"""
import os
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFileDialog,
    QFrame, QScrollArea, QGridLayout, QSizePolicy, QHBoxLayout,
    QComboBox, QCheckBox, QGroupBox, QMessageBox, QGraphicsScene,
    QGraphicsView, QGraphicsPixmapItem
)
from PySide6.QtCore import Signal, Qt, QSize, QEvent
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QIcon

from src.config import constants as const
from .adjustable_button import AdjustableButton
from ..base_widget import BaseWidget

class MediaSection(BaseWidget):
    """Media section for displaying and selecting media."""
    
    # Signals
    media_selected = Signal(str)
    toggle_view = Signal(bool)    # Signal to toggle between original/edited view (True = showing edited)
    post_format_changed = Signal(dict) # Signal for formatting changes
    
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
        self.retranslateUi() # Initial translation
        
    def _setup_ui(self):
        """Set up the media section UI components."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)
        
        # Media preview area
        self.media_preview = QLabel()
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
        self.select_btn = AdjustableButton()
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
        self.clear_btn = AdjustableButton()
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
        self.toggle_btn = AdjustableButton()
        self.toggle_btn.setStyleSheet("""
            background-color: #fbbc04;
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
        
        # Post Formatting Options
        self._setup_post_formatting_ui(layout)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #555; font-style: italic;")
        layout.addWidget(self.status_label)
        
    def _setup_post_formatting_ui(self, parent_layout: QVBoxLayout):
        """Set up the post formatting UI components."""
        self.formatting_group = QGroupBox()
        formatting_layout = QVBoxLayout()

        # Options (always visible)
        self.vertical_optimization_checkbox = QCheckBox()
        self.vertical_optimization_checkbox.toggled.connect(self._on_format_changed)
        
        self.caption_overlay_checkbox = QCheckBox()
        self.caption_overlay_checkbox.toggled.connect(self._on_format_changed)
        
        # Caption Position (relevant if overlay is checked)
        caption_position_layout = QHBoxLayout()
        self.caption_position_label = QLabel()
        self.caption_position_combo = QComboBox()
        self.caption_position_combo.addItems(["Bottom", "Top", "Center"])
        self.caption_position_combo.currentTextChanged.connect(self._on_format_changed)
        caption_position_layout.addWidget(self.caption_position_label)
        caption_position_layout.addWidget(self.caption_position_combo)

        # Font Size Selection
        font_size_layout = QHBoxLayout()
        self.font_size_label = QLabel()
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems(["Medium", "Small", "Large", "Extra Large"])
        self.font_size_combo.currentTextChanged.connect(self._on_format_changed)
        font_size_layout.addWidget(self.font_size_label)
        font_size_layout.addWidget(self.font_size_combo)

        formatting_layout.addWidget(self.vertical_optimization_checkbox)
        formatting_layout.addWidget(self.caption_overlay_checkbox)
        formatting_layout.addLayout(caption_position_layout)
        formatting_layout.addLayout(font_size_layout)

        self.formatting_group.setLayout(formatting_layout)
        parent_layout.addWidget(self.formatting_group)

    def _on_format_changed(self):
        """Handle changes in formatting options and emit a signal."""
        formatting_details = {
            "vertical_optimization": self.vertical_optimization_checkbox.isChecked(),
            "caption_overlay": self.caption_overlay_checkbox.isChecked(),
            "caption_position": self.caption_position_combo.currentText().lower(),
            "caption_font_size": self.font_size_combo.currentText().lower() # Removed language_overlay
        }
        self.post_format_changed.emit(formatting_details)
        self.logger.info(f"Post format changed: {formatting_details}")

    def _on_select_media(self):
        """Handle media selection button click."""
        try:
            # Open file dialog
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                self.tr("Select Media"),
                os.path.expanduser("~"),
                self.tr("Image Files (*.png *.jpg *.jpeg);;Video Files (*.mp4 *.mov);;All Files (*.*)")
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
        self.media_preview.setText(self.tr("No media selected"))
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
                self.status_label.setText(self.tr("Showing edited image"))
            else:
                self.set_media_display(self.current_media_path)
                self.status_label.setText(self.tr("Showing original image"))
                
            # Emit signal about the change
            self.toggle_view.emit(self.showing_edited)
    
    def _update_toggle_button_text(self):
        """Update the toggle button text based on current state."""
        if self.showing_edited:
            self.toggle_btn.setText(self.tr("Show Original"))
        else:
            self.toggle_btn.setText(self.tr("Show Edited"))
    
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
            self.media_preview.setText(self.tr("File not found"))
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
            self.logger.info(f"Video file selected: {media_path}")
            # For video, you might want to extract a frame or show a placeholder icon
            self.media_preview.setText(self.tr("Video preview not implemented"))
            # Example: Load a generic video icon
            # video_icon = QIcon.fromTheme("video-x-generic", QIcon(":/icons/video_placeholder.png")) 
            # self.media_preview.setPixmap(video_icon.pixmap(self.media_preview.size()))
    
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
            self.status_label.setText(self.tr("Showing edited image"))
            
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
        current_path = self.get_current_display_path()
        if current_path and os.path.exists(current_path):
            self.logger.info(f"Refreshing media display for: {current_path}")
            # Re-set the media display to force a refresh from disk
            original_showing_edited_state = self.showing_edited
            self.set_media_display(current_path) 
            # Restore the showing_edited state if set_media_display reset it (it shouldn't)
            self.showing_edited = original_showing_edited_state 
            self._update_toggle_button_text() # Ensure button text is correct
            if self.showing_edited:
                self.status_label.setText(self.tr("Showing edited image (refreshed)"))
            else:
                self.status_label.setText(self.tr("Showing original image (refreshed)"))
        else:
            self.logger.warning("Attempted to refresh media, but no valid path is currently displayed.")
            self._on_clear_media() # Clear if path is invalid

    def changeEvent(self, event):
        """Handle change events including language changes."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)
        
    def retranslateUi(self):
        """Update all UI text elements to the current language."""
        # Update section title
        if hasattr(self, 'title_label'):
            self.title_label.setText(self.tr("Media Selection"))
            
        # Update buttons
        if hasattr(self, 'select_btn'):
            self.select_btn.setText(self.tr("Select Media"))
        if hasattr(self, 'clear_btn'):
            self.clear_btn.setText(self.tr("Clear"))
        if hasattr(self, 'toggle_btn'):
            # Set the text depending on the current state
            if hasattr(self, 'showing_edited') and self.showing_edited:
                self.toggle_btn.setText(self.tr("Show Original"))
            else:
                self.toggle_btn.setText(self.tr("Show Edited"))
                
        # Update output options
        if hasattr(self, 'formatting_group'):
            self.formatting_group.setTitle(self.tr("Output Options"))
        if hasattr(self, 'vertical_optimization_checkbox'):
            self.vertical_optimization_checkbox.setText(self.tr("Vertical Optimization (for Story)"))
        if hasattr(self, 'caption_overlay_checkbox'):
            self.caption_overlay_checkbox.setText(self.tr("Caption Overlay (Non-distracting)"))
        if hasattr(self, 'caption_position_label'):
            self.caption_position_label.setText(self.tr("Caption Position:"))
        if hasattr(self, 'caption_position_combo'):
            # Save the current index
            current_index = self.caption_position_combo.currentIndex()
            # Clear and re-add translated items
            self.caption_position_combo.clear()
            self.caption_position_combo.addItem(self.tr("Bottom"))
            self.caption_position_combo.addItem(self.tr("Top"))
            self.caption_position_combo.addItem(self.tr("Center"))
            # Restore selection
            self.caption_position_combo.setCurrentIndex(current_index)
            
        if hasattr(self, 'font_size_label'):
            self.font_size_label.setText(self.tr("Caption Font Size:"))
        if hasattr(self, 'font_size_combo'):
            # Save the current index
            current_index = self.font_size_combo.currentIndex()
            # Clear and re-add translated items
            self.font_size_combo.clear()
            self.font_size_combo.addItem(self.tr("Small"))
            self.font_size_combo.addItem(self.tr("Medium"))
            self.font_size_combo.addItem(self.tr("Large"))
            self.font_size_combo.addItem(self.tr("Extra Large"))
            # Restore selection
            self.font_size_combo.setCurrentIndex(current_index)

        # Update status label
        if hasattr(self, 'status_label'):
            current_status = self.status_label.text()
            if "Showing original image" in current_status: # Looser check for refreshed states
                self.status_label.setText(self.tr("Showing original image"))
            elif "Showing edited image" in current_status:
                self.status_label.setText(self.tr("Showing edited image"))
            elif current_status == "File not found":
                self.status_label.setText(self.tr("File not found"))
        # Other status messages are set dynamically with tr() in their respective methods. 