"""
UI handler module for managing all UI-related operations and signals.
Consolidates functionality from various UI handler files.
"""
import logging
import os
from typing import Any, Optional, List, Dict, Callable
from PySide6.QtWidgets import (
    QWidget, QMessageBox, QFileDialog, QProgressBar,
    QLabel, QPushButton, QComboBox, QCheckBox, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt, QObject, Signal, QTimer
from PySide6.QtGui import QPixmap, QImage

from ..config import constants as const
from ..handlers.media_handler import (
    load_media_status, save_media_status,
    create_thumbnail, apply_photo_edits
)

class UISignals(QObject):
    """Signal definitions for UI updates."""
    status_update = Signal(str)  # General status updates
    error = Signal(str, str)  # Error title, message
    info = Signal(str, str)  # Info title, message
    warning = Signal(str, str)  # Warning title, message
    preview_ready = Signal(QPixmap)  # Preview image ready
    refresh_needed = Signal()  # Request UI refresh
    media_selected = Signal(str)  # Media file selected
    edit_applied = Signal(str, list)  # Edit type, applied effects
    media_refreshed = Signal()  # Signal to refresh media views after editing

class UIHandler:
    """Handles all UI-related operations and state management."""
    
    def __init__(self, main_window: QWidget):
        self.main_window = main_window
        self.signals = UISignals()
        self.app_state = None
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self) -> None:
        """Initialize UI components and their default states."""
        # Main window setup
        self.main_window.setWindowTitle("Breadsmith Marketing Tool")
        self.main_window.setMinimumSize(800, 600)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.main_window.statusBar().addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.main_window.statusBar().addPermanentWidget(self.progress_bar)
        
        # Media preview
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setStyleSheet("background-color: #f0f0f0;")
        
        # Control buttons
        self.refresh_button = QPushButton("Refresh")
        self.upload_button = QPushButton("Upload Media")
        self.edit_button = QPushButton("Edit Media")
        self.post_button = QPushButton("Post to Instagram")
        
        # Edit options
        self.edit_options = QComboBox()
        self.edit_options.addItems([
            "Default Enhancement",
            "Warm Tone",
            "Sepia",
            "Vintage",
            "Vignette",
            "Clarity"
        ])
        
        # Auto-refresh toggle
        self.auto_refresh = QCheckBox("Auto-refresh")
        self.auto_refresh.setChecked(const.FEATURES["enable_auto_refresh"])
        
        # Setup refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(const.UI_REFRESH_INTERVAL)
        self.refresh_timer.timeout.connect(self._auto_refresh)
        
    def _connect_signals(self) -> None:
        """Connect UI signals to their respective handlers."""
        # Button connections
        self.refresh_button.clicked.connect(self._handle_refresh)
        self.upload_button.clicked.connect(self._handle_upload)
        self.edit_button.clicked.connect(self._handle_edit)
        self.post_button.clicked.connect(self._handle_post)
        
        # Edit options
        self.edit_options.currentTextChanged.connect(self._handle_edit_option_change)
        
        # Auto-refresh
        self.auto_refresh.stateChanged.connect(self._handle_auto_refresh_toggle)
        
        # Custom signals
        self.signals.status_update.connect(self._handle_status_update)
        self.signals.error.connect(self._show_error)
        self.signals.info.connect(self._show_info)
        self.signals.warning.connect(self._show_warning)
        self.signals.preview_ready.connect(self._update_preview)
        self.signals.media_selected.connect(self._handle_media_selection)
        self.signals.edit_applied.connect(self._handle_edit_applied)
        self.signals.media_refreshed.connect(lambda: self._handle_media_refresh())
        
    def set_app_state(self, app_state: Any) -> None:
        """Set the application state object."""
        self.app_state = app_state
        
    def _handle_status_update(self, message: str) -> None:
        """
        Handle status update signal.
        
        Args:
            message: Status message
        """
        # Update status bar if available
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'status_bar'):
            self.main_window.status_bar.showMessage(message)
        else:
            print(f"Status: {message}")  # Fallback to console
        
    def _show_error(self, title: str, message: str) -> None:
        """Show an error message dialog."""
        QMessageBox.critical(self.main_window, title, message)
        
    def _show_info(self, title: str, message: str) -> None:
        """Show an information message dialog."""
        QMessageBox.information(self.main_window, title, message)
        
    def _show_warning(self, title: str, message: str) -> None:
        """Show a warning message dialog."""
        QMessageBox.warning(self.main_window, title, message)
        
    def _update_preview(self, pixmap: QPixmap) -> None:
        """Update the media preview with a new pixmap."""
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled_pixmap)
        else:
            self.preview_label.clear()
            self.preview_label.setText("No preview available")
            
    def _handle_refresh(self) -> None:
        """Handle refresh button click."""
        if not self.app_state:
            self._show_error("Error", "Application state not initialized")
            return
            
        self.refresh_button.setEnabled(False)
        self.signals.status_update.emit("Refreshing...")
        
        try:
            if load_media_status(self.app_state, self.signals):
                self.signals.refresh_needed.emit()
                self.signals.info.emit("Refresh Complete", "Media status updated successfully")
            else:
                self._show_error("Refresh Error", "Failed to refresh media status")
        finally:
            self.refresh_button.setEnabled(True)
            
    def _handle_upload(self) -> None:
        """Handle upload button click."""
        if not self.app_state:
            self._show_error("Error", "Application state not initialized")
            return
            
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter(
            f"Media Files ({' '.join('*' + ext for ext in const.SUPPORTED_MEDIA_TYPES)})"
        )
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self._process_upload(selected_files)
                
    def _process_upload(self, file_paths: List[str]) -> None:
        """Process the selected files for upload."""
        self.upload_button.setEnabled(False)
        self.signals.status_update.emit("Processing upload...")
        
        try:
            # TODO: Implement actual upload logic
            self.signals.info.emit(
                "Upload Complete",
                f"Successfully processed {len(file_paths)} files"
            )
        except Exception as e:
            self._show_error("Upload Error", str(e))
        finally:
            self.upload_button.setEnabled(True)
            
    def _handle_edit(self) -> None:
        """Handle edit button click."""
        if not self.app_state or not hasattr(self.app_state, 'selected_media'):
            self._show_error("Error", "No media selected for editing")
            return
            
        selected_media = self.app_state.selected_media
        if not selected_media:
            self._show_error("Error", "Please select a media file to edit")
            return
            
        self.edit_button.setEnabled(False)
        self.signals.status_update.emit("Applying edits...")
        
        try:
            # TODO: Implement actual edit logic
            self.signals.info.emit("Edit Complete", "Media edited successfully")
        except Exception as e:
            self._show_error("Edit Error", str(e))
        finally:
            self.edit_button.setEnabled(True)
            
    def _handle_post(self) -> None:
        """Handle post button click."""
        if not self.app_state or not hasattr(self.app_state, 'selected_media'):
            self._show_error("Error", "No media selected for posting")
            return
            
        selected_media = self.app_state.selected_media
        if not selected_media:
            self._show_error("Error", "Please select a media file to post")
            return
            
        self.post_button.setEnabled(False)
        self.signals.status_update.emit("Posting to Instagram...")
        
        try:
            # TODO: Implement actual posting logic
            self.signals.info.emit("Post Complete", "Media posted successfully")
        except Exception as e:
            self._show_error("Post Error", str(e))
        finally:
            self.post_button.setEnabled(True)
            
    def _handle_edit_option_change(self, option: str) -> None:
        """Handle edit option selection change."""
        if not self.app_state or not hasattr(self.app_state, 'selected_media'):
            return
            
        # Update UI to reflect the selected edit option
        self.signals.status_update.emit(f"Edit option: {option}")
        
    def _handle_auto_refresh_toggle(self, state: int) -> None:
        """Handle auto-refresh checkbox state change."""
        if state == Qt.CheckState.Checked.value:
            self.refresh_timer.start()
        else:
            self.refresh_timer.stop()
            
    def _auto_refresh(self) -> None:
        """Handle automatic refresh timer tick."""
        if self.auto_refresh.isChecked():
            self._handle_refresh()
            
    def _handle_media_selection(self, media_path: str) -> None:
        """
        Handle media selection signal.
        
        Args:
            media_path: Path to the selected media file
        """
        # Update app state if available
        if hasattr(self, 'app_state') and self.app_state:
            self.app_state.selected_media = media_path
            
    def _handle_edit_applied(self, edit_type: str, effects: list) -> None:
        """
        Handle edit applied signal.
        
        Args:
            edit_type: Type of edit applied
            effects: List of effects applied
        """
        # Update UI if needed
        effects_str = ", ".join(effects)
        self.signals.status_update.emit(f"{edit_type} effects applied: {effects_str}")
        
    def cleanup(self) -> None:
        """Clean up resources before closing."""
        self.refresh_timer.stop()
        # TODO: Add any additional cleanup needed

    def load_media(self, media_path: str) -> None:
        """
        Load media from file and display it.
        
        Args:
            media_path: Path to the media file
        """
        if not media_path or not os.path.exists(media_path):
            self.signals.status_update.emit("Media file not found")
            return
            
        self.signals.status_update.emit(f"Loading media: {os.path.basename(media_path)}")
        
        # Check if it's an image file
        _, ext = os.path.splitext(media_path.lower())
        if ext in const.SUPPORTED_IMAGE_FORMATS:
            try:
                # Create a QPixmap from the file
                pixmap = QPixmap(media_path)
                
                if not pixmap.isNull():
                    # Scale for preview
                    pixmap = pixmap.scaled(
                        800, 600, 
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    # Update UI with the loaded media
                    self.signals.preview_ready.emit(pixmap)
                    self.signals.status_update.emit(f"Loaded image: {os.path.basename(media_path)}")
                    
                    # Notify that media is selected
                    self.signals.media_selected.emit(media_path)
                    
                    # Trigger a media refresh to ensure views are updated
                    self.signals.media_refreshed.emit()
                else:
                    self.signals.error.emit("Media Error", "Could not load the selected media file")
            except Exception as e:
                self.signals.error.emit("Media Error", f"Error loading media: {str(e)}")
        else:
            self.signals.warning.emit("Media Type", "Unsupported media format")

    def refresh_media_display(self, media_path: str) -> None:
        """
        Refresh the media display after editing.
        
        Args:
            media_path: Path to the media file to display
        """
        if not media_path or not os.path.exists(media_path):
            self.signals.status_update.emit("Media file not found for refresh")
            return
            
        try:
            # Force reload the image from disk
            pixmap = QPixmap()
            pixmap.load(media_path)
            
            if not pixmap.isNull():
                # Scale for preview 
                pixmap = pixmap.scaled(
                    800, 600, 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Update UI with the reloaded media
                self.signals.preview_ready.emit(pixmap)
                self.signals.status_update.emit(f"Refreshed image display: {os.path.basename(media_path)}")
                
                # Signal that media has been refreshed
                self.signals.media_refreshed.emit()
            else:
                self.signals.error.emit("Media Error", "Could not refresh the media display")
        except Exception as e:
            self.signals.error.emit("Media Error", f"Error refreshing media: {str(e)}")

    def _handle_media_refresh(self):
        """Handle media refresh signal - refreshes the current media display."""
        if hasattr(self, 'app_state') and self.app_state and self.app_state.current_display_media:
            self.refresh_media_display(self.app_state.current_display_media)
        elif hasattr(self, 'app_state') and self.app_state and self.app_state.selected_media:
            self.refresh_media_display(self.app_state.selected_media) 