"""
Audio Overlay Dialog for Crow's Eye platform.
Allows users to upload audio files and add them as overlays to videos.
"""

import os
import logging
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSlider, QDoubleSpinBox, QProgressBar, QFileDialog, QGroupBox, 
    QFormLayout, QMessageBox, QSpinBox
)

from ..base_dialog import BaseDialog
from ...features.media_processing.video_handler import VideoHandler
from ...utils.subscription_utils import (
    check_feature_access_with_dialog, check_usage_limit_with_dialog,
    requires_feature_qt, requires_usage_qt, show_upgrade_dialog
)
from ...features.subscription.access_control import Feature


class AudioOverlayWorker(QThread):
    """Worker thread for adding audio overlays to videos."""
    
    progress = Signal(str)
    finished = Signal(bool, str, str)  # success, output_path, message
    
    def __init__(self, video_path: str, audio_path: str, volume: float, start_time: float):
        super().__init__()
        self.video_path = video_path
        self.audio_path = audio_path
        self.volume = volume
        self.start_time = start_time
        self.video_handler = VideoHandler()
    
    def run(self):
        """Run the audio overlay process."""
        try:
            self.progress.emit("Adding audio overlay...")
            success, output_path, message = self.video_handler.add_audio_overlay(
                self.video_path, self.audio_path, self.volume, self.start_time
            )
            self.finished.emit(success, output_path, message)
        except Exception as e:
            self.finished.emit(False, "", f"Error: {str(e)}")


class AudioOverlayDialog(BaseDialog):
    """Dialog for adding audio overlays to videos."""
    
    def __init__(self, video_path: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Audio Overlay")
        self.setFixedSize(600, 500)
        self.video_path = video_path
        self.audio_path = ""
        self.worker = None
        self._setup_ui()
        
        # If video path provided, display it
        if self.video_path:
            self._update_video_info()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Audio Overlay")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "Add audio files as overlays to your videos. "
            "Supports MP3, WAV, and other common audio formats. "
            "You can control volume, timing, and duration."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #CCCCCC; margin-bottom: 15px;")
        layout.addWidget(desc_label)
        
        # Video selection group (if no video provided)
        if not self.video_path:
            video_group = QGroupBox("Video Selection")
            video_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
            video_layout = QVBoxLayout(video_group)
            
            file_layout = QHBoxLayout()
            self.video_path_label = QLabel("No video selected")
            self.video_path_label.setStyleSheet("color: #CCCCCC; padding: 5px; border: 1px solid #444; border-radius: 4px;")
            file_layout.addWidget(self.video_path_label)
            
            self.browse_video_button = QPushButton("Browse Video...")
            self.browse_video_button.clicked.connect(self._browse_video)
            self.browse_video_button.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
            """)
            file_layout.addWidget(self.browse_video_button)
            
            video_layout.addLayout(file_layout)
            layout.addWidget(video_group)
        else:
            # Show current video info
            video_info_group = QGroupBox("Current Video")
            video_info_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
            video_info_layout = QVBoxLayout(video_info_group)
            
            self.video_info_label = QLabel(os.path.basename(self.video_path))
            self.video_info_label.setStyleSheet("color: #CCCCCC; padding: 5px; border: 1px solid #444; border-radius: 4px;")
            video_info_layout.addWidget(self.video_info_label)
            
            layout.addWidget(video_info_group)
        
        # Audio selection group
        audio_group = QGroupBox("Audio Selection")
        audio_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        audio_layout = QVBoxLayout(audio_group)
        
        # Audio file selection
        audio_file_layout = QHBoxLayout()
        self.audio_path_label = QLabel("No audio file selected")
        self.audio_path_label.setStyleSheet("color: #CCCCCC; padding: 5px; border: 1px solid #444; border-radius: 4px;")
        audio_file_layout.addWidget(self.audio_path_label)
        
        self.browse_audio_button = QPushButton("Browse Audio...")
        self.browse_audio_button.clicked.connect(self._browse_audio)
        self.browse_audio_button.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        audio_file_layout.addWidget(self.browse_audio_button)
        
        audio_layout.addLayout(audio_file_layout)
        
        # Audio format info
        format_info = QLabel("Supported formats: MP3, WAV, AAC, M4A, OGG")
        format_info.setStyleSheet("color: #888888; font-size: 11px; font-style: italic;")
        audio_layout.addWidget(format_info)
        
        layout.addWidget(audio_group)
        
        # Audio settings group
        settings_group = QGroupBox("Audio Settings")
        settings_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        settings_layout = QFormLayout(settings_group)
        
        # Volume control
        volume_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 200)  # 0% to 200%
        self.volume_slider.setValue(100)  # Default 100%
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #444;
                height: 8px;
                background: #2a2a2a;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3b82f6;
                border: 1px solid #1d4ed8;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #3b82f6;
                border-radius: 4px;
            }
        """)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_spinbox = QSpinBox()
        self.volume_spinbox.setRange(0, 200)
        self.volume_spinbox.setValue(100)
        self.volume_spinbox.setSuffix("%")
        self.volume_spinbox.setStyleSheet("color: #FFFFFF; background-color: #2a2a2a; border: 1px solid #444; padding: 5px;")
        volume_layout.addWidget(self.volume_spinbox)
        
        # Connect volume controls
        self.volume_slider.valueChanged.connect(self.volume_spinbox.setValue)
        self.volume_spinbox.valueChanged.connect(self.volume_slider.setValue)
        
        settings_layout.addRow("Volume:", volume_layout)
        
        # Start time control
        self.start_time_spinbox = QDoubleSpinBox()
        self.start_time_spinbox.setRange(0.0, 3600.0)  # 0 to 1 hour
        self.start_time_spinbox.setValue(0.0)
        self.start_time_spinbox.setSuffix(" seconds")
        self.start_time_spinbox.setDecimals(1)
        self.start_time_spinbox.setSingleStep(0.5)
        self.start_time_spinbox.setStyleSheet("color: #FFFFFF; background-color: #2a2a2a; border: 1px solid #444; padding: 5px;")
        settings_layout.addRow("Start Time:", self.start_time_spinbox)
        
        layout.addWidget(settings_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 4px;
                text-align: center;
                color: #FFFFFF;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #CCCCCC; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        self.apply_button = QPushButton("Add Audio Overlay")
        self.apply_button.clicked.connect(self._add_audio_overlay)
        self.apply_button.setEnabled(False)
        self.apply_button.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #374151;
                color: #6b7280;
            }
        """)
        button_layout.addWidget(self.apply_button)
        
        layout.addLayout(button_layout)
    
    def _browse_video(self):
        """Browse for a video file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.mov *.avi *.mkv *.wmv);;All Files (*)"
        )
        
        if file_path:
            self.video_path = file_path
            self._update_video_info()
    
    def _update_video_info(self):
        """Update video information display."""
        if hasattr(self, 'video_path_label'):
            filename = os.path.basename(self.video_path)
            self.video_path_label.setText(filename)
        
        self._check_ready_state()
        
        # Get video info
        video_handler = VideoHandler()
        info = video_handler.get_video_info(self.video_path)
        if "error" not in info:
            duration_min = int(info["duration"] // 60)
            duration_sec = int(info["duration"] % 60)
            self.status_label.setText(
                f"Video: {info['width']}x{info['height']}, Duration: {duration_min}:{duration_sec:02d}"
            )
            
            # Update start time maximum to video duration
            self.start_time_spinbox.setMaximum(info["duration"])
    
    def _browse_audio(self):
        """Browse for an audio file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            "",
            "Audio Files (*.mp3 *.wav *.aac *.m4a *.ogg *.flac);;All Files (*)"
        )
        
        if file_path:
            self.audio_path = file_path
            filename = os.path.basename(file_path)
            self.audio_path_label.setText(filename)
            self._check_ready_state()
            
            # Get file size info
            try:
                file_size = os.path.getsize(file_path)
                size_mb = file_size / (1024 * 1024)
                self.status_label.setText(f"Audio file: {filename} ({size_mb:.1f} MB)")
            except Exception as e:
                self.status_label.setText(f"Audio file: {filename}")
    
    def _check_ready_state(self):
        """Check if all required inputs are ready."""
        ready = bool(self.video_path and self.audio_path)
        self.apply_button.setEnabled(ready)
    
    def _add_audio_overlay(self):
        """Add audio overlay to the video."""
        # Check permissions first
        if not check_feature_access_with_dialog(Feature.AUDIO_IMPORTER, self):
            return
            
        if not self.video_path or not self.audio_path:
            QMessageBox.warning(self, "Warning", "Please select both video and audio files.")
            return
        
        # Disable UI during processing
        self.apply_button.setEnabled(False)
        self.browse_audio_button.setEnabled(False)
        if hasattr(self, 'browse_video_button'):
            self.browse_video_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Get settings
        volume = self.volume_spinbox.value() / 100.0  # Convert percentage to decimal
        start_time = self.start_time_spinbox.value()
        
        # Start worker thread
        self.worker = AudioOverlayWorker(self.video_path, self.audio_path, volume, start_time)
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._on_overlay_finished)
        self.worker.start()
    
    def _update_progress(self, message: str):
        """Update progress message."""
        self.status_label.setText(message)
    
    def _on_overlay_finished(self, success: bool, output_path: str, message: str):
        """Handle audio overlay completion."""
        # Re-enable UI
        self.apply_button.setEnabled(True)
        self.browse_audio_button.setEnabled(True)
        if hasattr(self, 'browse_video_button'):
            self.browse_video_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText(f"✓ {message}")
            QMessageBox.information(
                self,
                "Success",
                f"Audio overlay added successfully!\n\nSaved to: {output_path}"
            )
            self.accept()
        else:
            self.status_label.setText(f"✗ {message}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to add audio overlay:\n\n{message}"
            )
        
        # Clean up worker
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
    
    def get_output_path(self) -> str:
        """Get the path of the output video (if successful)."""
        return getattr(self, 'output_path', '')
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Cancel Processing",
                "Audio processing is in progress. Are you sure you want to cancel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.terminate()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept() 