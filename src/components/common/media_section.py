"""
Media section component for the main application window.
"""
import os
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFileDialog,
    QFrame, QScrollArea, QGridLayout, QSizePolicy, QHBoxLayout,
    QComboBox, QCheckBox, QGroupBox, QMessageBox, QGraphicsScene,
    QGraphicsView, QGraphicsPixmapItem, QPushButton
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
    video_selected = Signal(bool)  # Signal when video is selected (True) or image (False)
    
    def __init__(self, parent=None):
        """Initialize the media section."""
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize properties
        self.current_media_path = None
        self.edited_media_path = None
        self.showing_edited = False
        self.current_audio_path = None
        
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
        
        # Audio selection section
        self._setup_audio_selection_ui(layout)
        
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
    
    def _setup_audio_selection_ui(self, parent_layout: QVBoxLayout):
        """Set up the audio selection UI components."""
        self.audio_group = QGroupBox()
        audio_layout = QVBoxLayout()
        
        # Audio file display
        self.audio_display_layout = QHBoxLayout()
        
        self.audio_icon_label = QLabel("🎵")
        self.audio_icon_label.setStyleSheet("font-size: 16px;")
        self.audio_display_layout.addWidget(self.audio_icon_label)
        
        self.audio_filename_label = QLabel()
        self.audio_filename_label.setStyleSheet("color: #666; font-style: italic;")
        self.audio_display_layout.addWidget(self.audio_filename_label)
        
        self.audio_display_layout.addStretch()
        
        # Audio control buttons
        self.select_audio_btn = AdjustableButton()
        self.select_audio_btn.setStyleSheet("""
            background-color: #9c27b0;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
        """)
        self.select_audio_btn.clicked.connect(self._on_select_audio)
        self.audio_display_layout.addWidget(self.select_audio_btn)
        
        self.clear_audio_btn = AdjustableButton()
        self.clear_audio_btn.setStyleSheet("""
            background-color: #f44336;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
        """)
        self.clear_audio_btn.clicked.connect(self._on_clear_audio)
        self.clear_audio_btn.setEnabled(False)
        self.audio_display_layout.addWidget(self.clear_audio_btn)
        
        audio_layout.addLayout(self.audio_display_layout)
        
        # Audio info label
        self.audio_info_label = QLabel()
        self.audio_info_label.setStyleSheet("color: #888; font-size: 11px;")
        audio_layout.addWidget(self.audio_info_label)
        
        self.audio_group.setLayout(audio_layout)
        parent_layout.addWidget(self.audio_group)

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
        self.video_selected.emit(False)  # Reset to image mode when cleared
        self.showing_edited = False
        self._update_toggle_button_text()
        self.status_label.setText("")
        # Also clear audio when media is cleared
        self._on_clear_audio()
    
    def _on_select_audio(self):
        """Handle audio selection button click."""
        try:
            # Open file dialog for audio files
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                self.tr("Select Audio File"),
                os.path.expanduser("~"),
                self.tr("Audio Files (*.mp3 *.wav *.aac *.m4a *.ogg *.flac);;All Files (*.*)")
            )
            
            if file_path:
                self.set_audio(file_path)
            
        except Exception as e:
            self.logger.exception(f"Error selecting audio: {e}")
    
    def _on_clear_audio(self):
        """Clear selected audio."""
        self.current_audio_path = None
        self.audio_filename_label.setText("")
        self.audio_info_label.setText("")
        self.clear_audio_btn.setEnabled(False)
        self._update_audio_display()
    
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
    
    def _handle_video_selection(self, video_path):
        """Handle when a video file is selected."""
        try:
            # Get video info
            from ...features.media_processing.video_handler import VideoHandler
            video_handler = VideoHandler()
            video_info = video_handler.get_video_info(video_path)
            
            if "error" not in video_info:
                # Display video information with video indicator
                duration_min = int(video_info["duration"] // 60)
                duration_sec = int(video_info["duration"] % 60)
                
                info_text = f"""
                <div style="text-align: center;">
                <b>🎬 VIDEO FILE</b><br>
                <b>{os.path.basename(video_path)}</b><br>
                Resolution: {video_info['width']}x{video_info['height']}<br>
                Duration: {duration_min}:{duration_sec:02d}<br>
                Size: {video_info['file_size'] / (1024*1024):.1f} MB<br>
                <br>
                <i>Opening video processing options...</i>
                </div>
                """
                self.media_preview.setText(info_text)
                
                # Open the new video processing dialog
                self._open_video_processing_dialog(video_path)
            else:
                self.media_preview.setText(f"Error reading video: {video_info.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.logger.exception(f"Error handling video selection: {e}")
            self.media_preview.setText(f"Error processing video: {str(e)}")
    
    def _open_video_processing_dialog(self, video_path):
        """Open the new video processing dialog."""
        try:
            from ..dialogs.video_processing_dialog import VideoProcessingDialog
            dialog = VideoProcessingDialog(video_path, self)
            
            # Connect the video processed signal to handle the result
            dialog.video_processed.connect(self._on_video_processed)
            
            dialog.exec()
                
        except Exception as e:
            self.logger.exception(f"Error opening video processing dialog: {e}")
    
    def _on_video_processed(self, final_video_path):
        """Handle when video processing is complete."""
        try:
            # Load the processed video as the current media
            self.set_media(final_video_path)
            
            # Create a thumbnail for display
            self._create_video_thumbnail(final_video_path)
            
            # Emit signal that media has been selected
            self.media_selected.emit(final_video_path)
            
            self.logger.info(f"Video processing complete, loaded: {final_video_path}")
            
        except Exception as e:
            self.logger.exception(f"Error handling processed video: {e}")
    
    def _create_video_thumbnail(self, video_path):
        """Create and display a thumbnail for the video with video indicator."""
        try:
            from ...features.media_processing.video_handler import VideoHandler
            video_handler = VideoHandler()
            
            # Generate thumbnail at 1 second mark
            success, thumbnail_path, message = video_handler.generate_thumbnail(video_path, timestamp=1.0)
            
            if success and thumbnail_path and os.path.exists(thumbnail_path):
                # Load the thumbnail
                pixmap = QPixmap()
                pixmap.load(thumbnail_path)
                
                if not pixmap.isNull():
                    # Add video indicator overlay
                    painter = QPainter(pixmap)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    
                    # Draw semi-transparent overlay
                    overlay_color = QColor(0, 0, 0, 128)
                    painter.fillRect(pixmap.rect(), overlay_color)
                    
                    # Draw play button icon
                    play_size = min(pixmap.width(), pixmap.height()) // 4
                    play_x = (pixmap.width() - play_size) // 2
                    play_y = (pixmap.height() - play_size) // 2
                    
                    painter.setBrush(QColor(255, 255, 255, 200))
                    painter.setPen(QColor(255, 255, 255))
                    
                    # Draw triangle (play button)
                    from PySide6.QtGui import QPolygon
                    from PySide6.QtCore import QPoint
                    triangle = QPolygon([
                        QPoint(play_x, play_y),
                        QPoint(play_x, play_y + play_size),
                        QPoint(play_x + play_size, play_y + play_size // 2)
                    ])
                    painter.drawPolygon(triangle)
                    
                    # Draw "VIDEO" text
                    painter.setFont(painter.font())
                    font = painter.font()
                    font.setPointSize(max(12, play_size // 8))
                    font.setBold(True)
                    painter.setFont(font)
                    
                    text_rect = pixmap.rect()
                    text_rect.setTop(play_y + play_size + 10)
                    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "VIDEO")
                    
                    painter.end()
                    
                    # Scale and display the thumbnail
                    scaled_pixmap = pixmap.scaled(
                        self.media_preview.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.media_preview.setPixmap(scaled_pixmap)
                    
                    # Update status
                    self.status_label.setText(self.tr("Video loaded with thumbnail"))
                    
                    self.logger.info(f"Video thumbnail created and displayed for: {video_path}")
                else:
                    self._show_video_info_text(video_path)
            else:
                self._show_video_info_text(video_path)
                
        except Exception as e:
            self.logger.exception(f"Error creating video thumbnail: {e}")
            self._show_video_info_text(video_path)
    
    def _show_video_info_text(self, video_path):
        """Show video info as text when thumbnail creation fails."""
        try:
            from ...features.media_processing.video_handler import VideoHandler
            video_handler = VideoHandler()
            video_info = video_handler.get_video_info(video_path)
            
            if "error" not in video_info:
                duration_min = int(video_info["duration"] // 60)
                duration_sec = int(video_info["duration"] % 60)
                
                info_text = f"""
                <div style="text-align: center;">
                <b>🎬 VIDEO FILE</b><br>
                <b>{os.path.basename(video_path)}</b><br>
                Resolution: {video_info['width']}x{video_info['height']}<br>
                Duration: {duration_min}:{duration_sec:02d}<br>
                Size: {video_info['file_size'] / (1024*1024):.1f} MB<br>
                <br>
                <i>Processed video ready</i>
                </div>
                """
                self.media_preview.setText(info_text)
            else:
                self.media_preview.setText(f"🎬 Video: {os.path.basename(video_path)}")
                
        except Exception as e:
            self.media_preview.setText(f"🎬 Video: {os.path.basename(video_path)}")
            self.logger.exception(f"Error showing video info: {e}")
    
    def _open_highlight_reel_dialog(self, video_path):
        """Open the highlight reel dialog with the selected video."""
        try:
            from ..dialogs.highlight_reel_dialog import HighlightReelDialog
            dialog = HighlightReelDialog(self)
            dialog.video_path = video_path
            dialog._update_video_info()
            dialog.exec()
        except Exception as e:
            self.logger.exception(f"Error opening highlight reel dialog: {e}")
    
    def _open_story_assistant_dialog(self, video_path):
        """Open the story assistant dialog with the selected video."""
        try:
            from ..dialogs.story_assistant_dialog import StoryAssistantDialog
            dialog = StoryAssistantDialog(self)
            dialog.video_path = video_path
            dialog._update_video_info()
            dialog.exec()
        except Exception as e:
            self.logger.exception(f"Error opening story assistant dialog: {e}")
    
    def _open_thumbnail_selector_dialog(self, video_path):
        """Open the thumbnail selector dialog with the selected video."""
        try:
            from ..dialogs.thumbnail_selector_dialog import ThumbnailSelectorDialog
            dialog = ThumbnailSelectorDialog(video_path, self)
            dialog.exec()
        except Exception as e:
            self.logger.exception(f"Error opening thumbnail selector dialog: {e}")
    
    def _open_audio_overlay_dialog(self, video_path):
        """Open the audio overlay dialog with the selected video."""
        try:
            from ..dialogs.audio_overlay_dialog import AudioOverlayDialog
            dialog = AudioOverlayDialog(video_path, self)
            dialog.exec()
        except Exception as e:
            self.logger.exception(f"Error opening audio overlay dialog: {e}")
    
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
                # Emit image selected signal
                self.video_selected.emit(False)
            else:
                self.media_preview.setText(f"Error loading image: {os.path.basename(media_path)}")
                self.logger.error(f"Failed to load image: {media_path}")
        elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.wmv']:
            self.logger.info(f"Video file selected: {media_path}")
            # Emit video selected signal
            self.video_selected.emit(True)
            # Show video file info and offer video processing options
            self._handle_video_selection(media_path)
        else:
            self.logger.info(f"Unsupported file type selected: {media_path}")
            self.media_preview.setText(self.tr("Unsupported file type"))
    
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

    def set_audio(self, audio_path):
        """Set the audio file for the post."""
        try:
            if not os.path.exists(audio_path):
                self.logger.error(f"Audio file does not exist: {audio_path}")
                return
            
            # Validate audio file
            file_ext = os.path.splitext(audio_path)[1].lower()
            if file_ext not in const.SUPPORTED_AUDIO_FORMATS:
                QMessageBox.warning(
                    self, 
                    self.tr("Unsupported Audio Format"), 
                    self.tr("The selected audio format is not supported. Please select an MP3, WAV, AAC, M4A, OGG, or FLAC file.")
                )
                return
            
            # Check file size
            file_size = os.path.getsize(audio_path)
            if file_size > const.MAX_AUDIO_SIZE:
                size_mb = file_size / (1024 * 1024)
                max_mb = const.MAX_AUDIO_SIZE / (1024 * 1024)
                QMessageBox.warning(
                    self, 
                    self.tr("Audio File Too Large"), 
                    self.tr("The audio file is {size:.1f}MB, which exceeds the maximum size of {max:.1f}MB.").format(
                        size=size_mb, max=max_mb
                    )
                )
                return
            
            self.current_audio_path = audio_path
            self._update_audio_display()
            self.clear_audio_btn.setEnabled(True)
            
            self.logger.info(f"Audio file selected: {audio_path}")
            
        except Exception as e:
            self.logger.exception(f"Error setting audio: {e}")
            QMessageBox.critical(self, self.tr("Audio Error"), self.tr("Failed to load audio file: {error}").format(error=str(e)))
    
    def _update_audio_display(self):
        """Update the audio display area."""
        if self.current_audio_path:
            filename = os.path.basename(self.current_audio_path)
            self.audio_filename_label.setText(filename)
            
            # Get file size
            try:
                file_size = os.path.getsize(self.current_audio_path)
                size_mb = file_size / (1024 * 1024)
                self.audio_info_label.setText(self.tr("Audio: {size:.1f}MB").format(size=size_mb))
            except:
                self.audio_info_label.setText(self.tr("Audio file selected"))
        else:
            self.audio_filename_label.setText(self.tr("No audio selected"))
            self.audio_info_label.setText("")
    
    def get_current_audio_path(self):
        """Get the path of the currently selected audio file."""
        return self.current_audio_path

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

        # Update audio section
        if hasattr(self, 'audio_group'):
            self.audio_group.setTitle(self.tr("Background Audio"))
        if hasattr(self, 'select_audio_btn'):
            self.select_audio_btn.setText(self.tr("Select Audio"))
        if hasattr(self, 'clear_audio_btn'):
            self.clear_audio_btn.setText(self.tr("Clear Audio"))
        
        # Update audio display
        if hasattr(self, 'current_audio_path') and self.current_audio_path:
            self._update_audio_display()
        elif hasattr(self, 'audio_filename_label'):
            self.audio_filename_label.setText(self.tr("No audio selected"))

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