"""
Custom media upload dialog for posting directly to Instagram and Facebook.
Allows users to select media, add captions, and choose platforms for posting.
"""
import os
import logging
from typing import List, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QCheckBox, QFileDialog, QProgressBar, QMessageBox, QGroupBox,
    QScrollArea, QWidget, QGridLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QPixmap, QFont, QIcon

from ...config import constants as const
from ...handlers.meta_posting_handler import MetaPostingHandler, MetaPostingWorker
from ..base_dialog import BaseDialog

class CustomMediaUploadDialog(BaseDialog):
    """Dialog for uploading custom media to social platforms."""
    
    upload_completed = Signal(bool, str)  # success, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize components
        self.meta_handler = MetaPostingHandler()
        self.worker_thread = None
        self.selected_media_path = None
        self.selected_audio_path = None
        self.is_video = False
        
        # UI components
        self.media_preview = None
        self.media_path_label = None
        self.caption_text = None
        self.instagram_checkbox = None
        self.facebook_checkbox = None
        self.upload_button = None
        self.progress_bar = None
        self.status_label = None
        
        self._setup_ui()
        self._connect_signals()
        self._check_platform_availability()
        
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Upload Custom Media")
        self.setMinimumSize(600, 700)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Upload Custom Media to Social Platforms")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Media selection section
        media_group = QGroupBox("Select Media")
        media_layout = QVBoxLayout(media_group)
        
        # Media selection button
        select_button = QPushButton("Select Media File")
        select_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        select_button.clicked.connect(self._select_media_file)
        media_layout.addWidget(select_button)
        
        # Media preview area
        preview_frame = QFrame()
        preview_frame.setFrameStyle(QFrame.Shape.Box)
        preview_frame.setMinimumHeight(200)
        preview_frame.setStyleSheet("QFrame { border: 2px dashed #cccccc; background-color: #f9f9f9; }")
        
        preview_layout = QVBoxLayout(preview_frame)
        
        self.media_preview = QLabel("No media selected")
        self.media_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_preview.setStyleSheet("color: #666666; font-size: 14px;")
        self.media_preview.setMinimumHeight(150)
        preview_layout.addWidget(self.media_preview)
        
        self.media_path_label = QLabel("")
        self.media_path_label.setStyleSheet("color: #888888; font-size: 12px;")
        self.media_path_label.setWordWrap(True)
        preview_layout.addWidget(self.media_path_label)
        
        media_layout.addWidget(preview_frame)
        layout.addWidget(media_group)
        
        # Audio selection section
        audio_group = QGroupBox("Background Audio (Optional)")
        audio_layout = QVBoxLayout(audio_group)
        
        # Audio selection button and display
        audio_selection_layout = QHBoxLayout()
        
        select_audio_button = QPushButton("Select Audio File")
        select_audio_button.setStyleSheet("""
            QPushButton {
                background-color: #9c27b0;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7b1fa2;
            }
            QPushButton:pressed {
                background-color: #6a1b9a;
            }
        """)
        select_audio_button.clicked.connect(self._select_audio_file)
        audio_selection_layout.addWidget(select_audio_button)
        
        self.audio_filename_label = QLabel("No audio selected")
        self.audio_filename_label.setStyleSheet("color: #666666; font-style: italic; padding: 8px;")
        audio_selection_layout.addWidget(self.audio_filename_label)
        
        audio_selection_layout.addStretch()
        
        self.clear_audio_button = QPushButton("Clear Audio")
        self.clear_audio_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #ffcdd2;
                color: #ffffff;
            }
        """)
        self.clear_audio_button.clicked.connect(self._clear_audio_file)
        self.clear_audio_button.setEnabled(False)
        audio_selection_layout.addWidget(self.clear_audio_button)
        
        audio_layout.addLayout(audio_selection_layout)
        
        # Audio info
        self.audio_info_label = QLabel("Supported formats: MP3, WAV, AAC, M4A, OGG, FLAC (max 25MB)")
        self.audio_info_label.setStyleSheet("color: #888888; font-size: 11px;")
        audio_layout.addWidget(self.audio_info_label)
        
        layout.addWidget(audio_group)
        
        # Caption section
        caption_group = QGroupBox("Caption")
        caption_layout = QVBoxLayout(caption_group)
        
        self.caption_text = QTextEdit()
        self.caption_text.setPlaceholderText("Enter your caption here...")
        self.caption_text.setMaximumHeight(120)
        self.caption_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
        """)
        caption_layout.addWidget(self.caption_text)
        
        # Character count
        self.char_count_label = QLabel("0 / 2200 characters")
        self.char_count_label.setStyleSheet("color: #666666; font-size: 12px;")
        self.char_count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        caption_layout.addWidget(self.char_count_label)
        
        layout.addWidget(caption_group)
        
        # Platform selection
        platform_group = QGroupBox("Select Platforms")
        platform_layout = QVBoxLayout(platform_group)
        
        self.instagram_checkbox = QCheckBox("Instagram")
        self.instagram_checkbox.setStyleSheet("QCheckBox { font-size: 14px; }")
        platform_layout.addWidget(self.instagram_checkbox)
        
        self.facebook_checkbox = QCheckBox("Facebook")
        self.facebook_checkbox.setStyleSheet("QCheckBox { font-size: 14px; }")
        platform_layout.addWidget(self.facebook_checkbox)
        
        layout.addWidget(platform_group)
        
        # Progress section
        progress_group = QGroupBox("Upload Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to upload")
        self.status_label.setStyleSheet("color: #666666; font-size: 12px;")
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.upload_button = QPushButton("Upload to Selected Platforms")
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px 24px;
                font-weight: bold;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #BBDEFB;
                color: #FFFFFF;
            }
        """)
        self.upload_button.clicked.connect(self._start_upload)
        self.upload_button.setEnabled(False)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                padding: 12px 24px;
                font-weight: bold;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.upload_button)
        
        layout.addLayout(button_layout)
        
    def _connect_signals(self):
        """Connect UI signals."""
        # Caption text change
        self.caption_text.textChanged.connect(self._update_char_count)
        self.caption_text.textChanged.connect(self._validate_form)
        
        # Platform checkboxes
        self.instagram_checkbox.toggled.connect(self._validate_form)
        self.facebook_checkbox.toggled.connect(self._validate_form)
        
        # Meta handler signals
        self.meta_handler.signals.upload_started.connect(self._on_upload_started)
        self.meta_handler.signals.upload_progress.connect(self._on_upload_progress)
        self.meta_handler.signals.upload_success.connect(self._on_upload_success)
        self.meta_handler.signals.upload_error.connect(self._on_upload_error)
        self.meta_handler.signals.status_update.connect(self._on_status_update)
        
    def _select_media_file(self):
        """Open file dialog to select media file."""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select Media File")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        
        # Set file filters
        filters = [
            "All Supported Media (*.jpg *.jpeg *.png *.gif *.bmp *.webp *.mp4 *.mov *.avi *.wmv *.mkv)",
            "Images (*.jpg *.jpeg *.png *.gif *.bmp *.webp)",
            "Videos (*.mp4 *.mov *.avi *.wmv *.mkv)",
            "All Files (*)"
        ]
        file_dialog.setNameFilters(filters)
        
        if file_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self._load_media_file(selected_files[0])
    
    def _load_media_file(self, file_path: str):
        """Load and preview the selected media file."""
        try:
            self.selected_media_path = file_path
            file_ext = os.path.splitext(file_path)[1].lower()
            self.is_video = file_ext in const.SUPPORTED_VIDEO_FORMATS
            
            # Validate file
            is_valid, error_msg = self.meta_handler.validate_media_file(file_path)
            if not is_valid:
                QMessageBox.warning(self, "Invalid File", error_msg)
                return
            
            # Update preview
            if self.is_video:
                self.media_preview.setText(f"🎥 Video File\n{os.path.basename(file_path)}")
                self.media_preview.setStyleSheet("color: #2196F3; font-size: 16px; font-weight: bold;")
            else:
                # Load image preview
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    # Scale to fit preview area
                    scaled_pixmap = pixmap.scaled(
                        200, 150, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.media_preview.setPixmap(scaled_pixmap)
                else:
                    self.media_preview.setText(f"📷 Image File\n{os.path.basename(file_path)}")
                    self.media_preview.setStyleSheet("color: #4CAF50; font-size: 16px; font-weight: bold;")
            
            # Update path label
            self.media_path_label.setText(f"File: {file_path}")
            
            # Validate form
            self._validate_form()
            
        except Exception as e:
            self.logger.exception(f"Error loading media file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load media file: {str(e)}")
    
    def _update_char_count(self):
        """Update character count for caption."""
        text = self.caption_text.toPlainText()
        char_count = len(text)
        self.char_count_label.setText(f"{char_count} / {const.IG_MAX_CAPTION_LENGTH} characters")
        
        # Change color if approaching limit
        if char_count > const.IG_MAX_CAPTION_LENGTH * 0.9:
            self.char_count_label.setStyleSheet("color: #f44336; font-size: 12px;")
        elif char_count > const.IG_MAX_CAPTION_LENGTH * 0.8:
            self.char_count_label.setStyleSheet("color: #ff9800; font-size: 12px;")
        else:
            self.char_count_label.setStyleSheet("color: #666666; font-size: 12px;")
    
    def _select_audio_file(self):
        """Open file dialog to select audio file."""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select Audio File")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        
        # Set audio file filters
        filters = [
            "Audio Files (*.mp3 *.wav *.aac *.m4a *.ogg *.flac)",
            "All Files (*)"
        ]
        file_dialog.setNameFilters(filters)
        
        if file_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self._load_audio_file(selected_files[0])
    
    def _load_audio_file(self, file_path: str):
        """Load and validate the selected audio file."""
        try:
            # Validate audio file
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in const.SUPPORTED_AUDIO_FORMATS:
                QMessageBox.warning(
                    self, 
                    "Unsupported Audio Format", 
                    "The selected audio format is not supported. Please select an MP3, WAV, AAC, M4A, OGG, or FLAC file."
                )
                return
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > const.MAX_AUDIO_SIZE:
                size_mb = file_size / (1024 * 1024)
                max_mb = const.MAX_AUDIO_SIZE / (1024 * 1024)
                QMessageBox.warning(
                    self, 
                    "Audio File Too Large", 
                    f"The audio file is {size_mb:.1f}MB, which exceeds the maximum size of {max_mb:.1f}MB."
                )
                return
            
            self.selected_audio_path = file_path
            filename = os.path.basename(file_path)
            size_mb = file_size / (1024 * 1024)
            
            self.audio_filename_label.setText(f"🎵 {filename} ({size_mb:.1f}MB)")
            self.audio_filename_label.setStyleSheet("color: #9c27b0; font-weight: bold; padding: 8px;")
            self.clear_audio_button.setEnabled(True)
            
            self.logger.info(f"Audio file selected: {file_path}")
            
        except Exception as e:
            self.logger.exception(f"Error loading audio file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load audio file: {str(e)}")
    
    def _clear_audio_file(self):
        """Clear the selected audio file."""
        self.selected_audio_path = None
        self.audio_filename_label.setText("No audio selected")
        self.audio_filename_label.setStyleSheet("color: #666666; font-style: italic; padding: 8px;")
        self.clear_audio_button.setEnabled(False)

    def _validate_form(self):
        """Validate form and enable/disable upload button."""
        has_media = self.selected_media_path is not None
        has_platform = self.instagram_checkbox.isChecked() or self.facebook_checkbox.isChecked()
        caption_valid = len(self.caption_text.toPlainText()) <= const.IG_MAX_CAPTION_LENGTH
        
        self.upload_button.setEnabled(has_media and has_platform and caption_valid)
    
    def _check_platform_availability(self):
        """Check which platforms are available for posting."""
        status = self.meta_handler.get_posting_status()
        
        if not status["credentials_loaded"]:
            self.instagram_checkbox.setEnabled(False)
            self.facebook_checkbox.setEnabled(False)
            self.status_label.setText("Meta credentials not loaded. Please connect your accounts first.")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
            return
        
        self.instagram_checkbox.setEnabled(status["instagram_available"])
        self.facebook_checkbox.setEnabled(status["facebook_available"])
        
        if not status["instagram_available"]:
            self.instagram_checkbox.setText("Instagram (Not Available)")
            self.instagram_checkbox.setStyleSheet("QCheckBox { color: #999999; }")
        
        if not status["facebook_available"]:
            self.facebook_checkbox.setText("Facebook (Not Available)")
            self.facebook_checkbox.setStyleSheet("QCheckBox { color: #999999; }")
        
        if status["error_message"]:
            self.status_label.setText(status["error_message"])
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
    
    def _start_upload(self):
        """Start the upload process."""
        if not self.selected_media_path:
            QMessageBox.warning(self, "No Media", "Please select a media file first.")
            return
        
        # Get selected platforms
        platforms = []
        if self.instagram_checkbox.isChecked():
            platforms.append("Instagram")
        if self.facebook_checkbox.isChecked():
            platforms.append("Facebook")
        
        if not platforms:
            QMessageBox.warning(self, "No Platforms", "Please select at least one platform.")
            return
        
        # Get caption
        caption = self.caption_text.toPlainText().strip()
        
        # Disable UI during upload
        self.upload_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start worker thread
        self.worker_thread = MetaPostingWorker(
            self.meta_handler, 
            self.selected_media_path, 
            caption, 
            platforms,
            self.selected_audio_path
        )
        self.worker_thread.finished.connect(self._on_worker_finished)
        self.worker_thread.progress.connect(self._on_worker_progress)
        self.worker_thread.start()
    
    def _on_upload_started(self, platform: str):
        """Handle upload started signal."""
        self.status_label.setText(f"Starting upload to {platform}...")
        self.status_label.setStyleSheet("color: #2196F3; font-size: 12px;")
    
    def _on_upload_progress(self, message: str, percentage: int):
        """Handle upload progress signal."""
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)
    
    def _on_upload_success(self, platform: str, response_data: dict):
        """Handle upload success signal."""
        self.status_label.setText(f"Successfully uploaded to {platform}!")
        self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
    
    def _on_upload_error(self, platform: str, error_message: str):
        """Handle upload error signal."""
        self.status_label.setText(f"Error uploading to {platform}: {error_message}")
        self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
    
    def _on_status_update(self, message: str):
        """Handle status update signal."""
        self.status_label.setText(message)
    
    def _on_worker_finished(self, success: bool, platform: str, message: str):
        """Handle worker thread completion."""
        self.progress_bar.setVisible(False)
        self.upload_button.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Upload Complete", 
                                  f"Successfully uploaded to {platform}!")
            self.upload_completed.emit(True, f"Uploaded to {platform}")
            self.accept()
        else:
            QMessageBox.critical(self, "Upload Failed", 
                               f"Failed to upload to {platform}: {message}")
            self.upload_completed.emit(False, message)
    
    def _on_worker_progress(self, message: str, percentage: int):
        """Handle worker progress updates."""
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(
                self, "Upload in Progress", 
                "An upload is currently in progress. Are you sure you want to cancel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker_thread.terminate()
                self.worker_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
    
    def retranslateUi(self):
        """Retranslate UI elements."""
        self.setWindowTitle(self.tr("Upload Custom Media"))
        # Add more translations as needed 