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
from ...api.meta.meta_posting_handler import MetaPostingHandler, MetaPostingWorker
from ...features.posting.unified_posting_handler import UnifiedPostingHandler, UnifiedPostingWorker
from ..base_dialog import BaseDialog

class CustomMediaUploadDialog(BaseDialog):
    """Dialog for uploading custom media to social platforms."""
    
    upload_completed = Signal(bool, str)  # success, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize components
        self.meta_handler = MetaPostingHandler()
        self.unified_handler = UnifiedPostingHandler()
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
        
        # Create a grid layout for better organization
        platform_grid = QGridLayout()
        
        # Row 1: Meta platforms
        self.instagram_checkbox = QCheckBox("Instagram")
        self.instagram_checkbox.setStyleSheet("QCheckBox { font-size: 14px; }")
        platform_grid.addWidget(self.instagram_checkbox, 0, 0)
        
        self.facebook_checkbox = QCheckBox("Facebook")
        self.facebook_checkbox.setStyleSheet("QCheckBox { font-size: 14px; }")
        platform_grid.addWidget(self.facebook_checkbox, 0, 1)
        
        # Row 2: Professional platforms

        
        # Row 2: New platforms
        self.tiktok_checkbox = QCheckBox("TikTok")
        self.tiktok_checkbox.setStyleSheet("QCheckBox { font-size: 14px; }")
        platform_grid.addWidget(self.tiktok_checkbox, 1, 0)
        
        self.pinterest_checkbox = QCheckBox("Pinterest")
        self.pinterest_checkbox.setStyleSheet("QCheckBox { font-size: 14px; }")
        platform_grid.addWidget(self.pinterest_checkbox, 1, 1)
        
        # Row 3: Additional platforms
        self.bluesky_checkbox = QCheckBox("BlueSky")
        self.bluesky_checkbox.setStyleSheet("QCheckBox { font-size: 14px; }")
        platform_grid.addWidget(self.bluesky_checkbox, 2, 0)
        
        self.threads_checkbox = QCheckBox("Threads")
        self.threads_checkbox.setStyleSheet("QCheckBox { font-size: 14px; }")
        platform_grid.addWidget(self.threads_checkbox, 2, 1)
        
        # Row 4: Business platforms
        self.snapchat_checkbox = QCheckBox("Snapchat")
        self.snapchat_checkbox.setStyleSheet("QCheckBox { font-size: 14px; }")
        platform_grid.addWidget(self.snapchat_checkbox, 3, 0)
        
        self.google_business_checkbox = QCheckBox("Google My Business")
        self.google_business_checkbox.setStyleSheet("QCheckBox { font-size: 14px; }")
        platform_grid.addWidget(self.google_business_checkbox, 3, 1)
        
        platform_layout.addLayout(platform_grid)
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
        self.tiktok_checkbox.toggled.connect(self._validate_form)
        self.pinterest_checkbox.toggled.connect(self._validate_form)
        self.bluesky_checkbox.toggled.connect(self._validate_form)
        self.threads_checkbox.toggled.connect(self._validate_form)
        self.snapchat_checkbox.toggled.connect(self._validate_form)
        self.google_business_checkbox.toggled.connect(self._validate_form)
        
        # Unified handler signals
        self.unified_handler.signals.upload_started.connect(self._on_upload_started)
        self.unified_handler.signals.upload_progress.connect(self._on_upload_progress)
        self.unified_handler.signals.upload_success.connect(self._on_upload_success)
        self.unified_handler.signals.upload_error.connect(self._on_upload_error)
        self.unified_handler.signals.status_update.connect(self._on_status_update)
        
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
        has_platform = (self.instagram_checkbox.isChecked() or 
                       self.facebook_checkbox.isChecked() or 
                       self.tiktok_checkbox.isChecked() or
                       self.pinterest_checkbox.isChecked() or
                       self.bluesky_checkbox.isChecked() or
                       self.threads_checkbox.isChecked() or
                       self.google_business_checkbox.isChecked())
        
        # Check if any text-only platforms are selected
        text_only_platforms = (self.facebook_checkbox.isChecked() or
                              self.bluesky_checkbox.isChecked() or
                              self.threads_checkbox.isChecked() or
                              self.google_business_checkbox.isChecked())
        
        # Platforms that require media
        media_required_platforms = (self.instagram_checkbox.isChecked() or
                                   self.tiktok_checkbox.isChecked() or
                                   self.pinterest_checkbox.isChecked())
        
        # Form is valid if:
        # 1. At least one platform is selected
        # 2. If media-required platforms are selected, media must be provided
        # 3. If only text-only platforms are selected, caption must be provided
        caption = self.caption_text.toPlainText().strip()
        caption_valid = len(caption) <= const.IG_MAX_CAPTION_LENGTH
        
        form_valid = (has_platform and caption_valid and 
                     ((media_required_platforms and has_media) or 
                      (not media_required_platforms and (has_media or (text_only_platforms and caption)))))
        
        self.upload_button.setEnabled(form_valid)
    
    def _check_platform_availability(self):
        """Check which platforms are available for posting."""
        available_platforms = self.unified_handler.get_available_platforms()
        platform_errors = self.unified_handler.get_platform_errors()
        
        # Platform checkbox mapping
        platform_checkboxes = {
            'instagram': (self.instagram_checkbox, "Instagram"),
            'facebook': (self.facebook_checkbox, "Facebook"),
            'tiktok': (self.tiktok_checkbox, "TikTok"),
            'pinterest': (self.pinterest_checkbox, "Pinterest"),
            'bluesky': (self.bluesky_checkbox, "BlueSky"),
            'threads': (self.threads_checkbox, "Threads"),
            'google_business': (self.google_business_checkbox, "Google My Business")
        }
        
        # Set platform availability
        for platform_key, (checkbox, display_name) in platform_checkboxes.items():
            is_available = available_platforms.get(platform_key, False)
            checkbox.setEnabled(is_available)
            
            if not is_available:
                checkbox.setText(f"{display_name} (Not Available)")
                checkbox.setStyleSheet("QCheckBox { color: #999999; font-size: 14px; }")
            else:
                checkbox.setText(display_name)
                checkbox.setStyleSheet("QCheckBox { font-size: 14px; }")
        
        # Show error message if any platforms are unavailable
        error_messages = []
        for platform, error in platform_errors.items():
            if error:
                error_messages.append(f"{platform.title()}: {error}")
        
        if error_messages:
            self.status_label.setText("Some platforms unavailable. Check credentials.")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
        else:
            self.status_label.setText("All platforms available")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
    
    def _start_upload(self):
        """Start the upload process."""
        # Get selected platforms
        platforms = []
        if self.instagram_checkbox.isChecked():
            platforms.append("Instagram")
        if self.facebook_checkbox.isChecked():
            platforms.append("Facebook")

        if self.tiktok_checkbox.isChecked():
            platforms.append("TikTok")
        if self.pinterest_checkbox.isChecked():
            platforms.append("Pinterest")
        if self.bluesky_checkbox.isChecked():
            platforms.append("BlueSky")
        if self.threads_checkbox.isChecked():
            platforms.append("Threads")
        if self.google_business_checkbox.isChecked():
            platforms.append("Google My Business")
        
        if not platforms:
            QMessageBox.warning(self, "No Platforms", "Please select at least one platform.")
            return
        
        # Get caption
        caption = self.caption_text.toPlainText().strip()
        
        # Check if media-required platforms are selected and require media
        media_required_platforms = [p for p in platforms if p in ["Instagram", "TikTok", "Pinterest"]]
        if media_required_platforms and not self.selected_media_path:
            QMessageBox.warning(self, "No Media", f"{', '.join(media_required_platforms)} require(s) a media file. Please select a media file or uncheck these platforms.")
            return
        
        # Check if we have either media or caption for text-only platforms
        text_only_platforms = [p for p in platforms if p in ["Facebook", "BlueSky", "Threads", "Google My Business"]]
        if text_only_platforms and not self.selected_media_path and not caption:
            QMessageBox.warning(self, "No Content", "Please provide either a media file or caption text.")
            return
        
        # Disable UI during upload
        self.upload_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start worker thread
        self.worker_thread = UnifiedPostingWorker(
            self.unified_handler, 
            platforms,
            self.selected_media_path, 
            caption,
            self.is_video
        )
        self.worker_thread.finished.connect(self._on_worker_finished)
        self.worker_thread.progress.connect(self._on_worker_progress)
        self.worker_thread.platform_complete.connect(self._on_platform_complete)
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
    
    def _on_worker_finished(self, success: bool, results: dict):
        """Handle worker thread completion."""
        self.progress_bar.setVisible(False)
        self.upload_button.setEnabled(True)
        
        if success:
            successful_platforms = [platform for platform, (success, _) in results.items() if success]
            QMessageBox.information(self, "Upload Complete", 
                                  f"Successfully uploaded to {', '.join(successful_platforms)}!")
            self.upload_completed.emit(True, f"Uploaded to {', '.join(successful_platforms)}")
            self.accept()
        else:
            failed_platforms = []
            for platform, (success, message) in results.items():
                if not success:
                    failed_platforms.append(f"{platform}: {message}")
            
            error_msg = "\n".join(failed_platforms)
            QMessageBox.critical(self, "Upload Failed", f"Upload failed:\n{error_msg}")
            self.upload_completed.emit(False, error_msg)
    
    def _on_platform_complete(self, platform: str, success: bool, message: str):
        """Handle individual platform completion."""
        if success:
            self.status_label.setText(f"✓ {platform} completed successfully")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
        else:
            self.status_label.setText(f"✗ {platform} failed: {message}")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
    
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