"""
Highlight Reel Generator Dialog for Crow's Eye platform.
Allows users to create highlight reels from long videos with natural language prompts.
"""

import os
import logging
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QSpinBox, QTextEdit, QProgressBar, QFileDialog,
    QGroupBox, QFormLayout, QMessageBox
)

from ..base_dialog import BaseDialog
from ...features.media_processing.video_handler import VideoHandler
from ...utils.subscription_utils import (
    check_feature_access_with_dialog, check_usage_limit_with_dialog,
    requires_feature_qt, requires_usage_qt, show_upgrade_dialog
)
from ...features.subscription.access_control import Feature


class HighlightReelWorker(QThread):
    """Worker thread for generating highlight reels."""
    
    progress = Signal(str)
    finished = Signal(bool, str, str)  # success, output_path, message
    
    def __init__(self, video_path: str, target_duration: int, prompt: str):
        super().__init__()
        self.video_path = video_path
        self.target_duration = target_duration
        self.prompt = prompt
        self.video_handler = VideoHandler()
    
    def run(self):
        """Run the highlight reel generation."""
        try:
            self.progress.emit("Analyzing video...")
            success, output_path, message = self.video_handler.generate_highlight_reel(
                self.video_path, self.target_duration, self.prompt
            )
            self.finished.emit(success, output_path, message)
        except Exception as e:
            self.finished.emit(False, "", f"Error: {str(e)}")


class HighlightReelDialog(BaseDialog):
    """Dialog for generating highlight reels from videos."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Highlight Reel Generator")
        self.setFixedSize(600, 500)
        self.video_path = ""
        self.worker = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Create Highlight Reel")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "Generate a highlight reel from a long video. Use natural language prompts to specify "
            "what content to include or exclude (e.g., 'only show missed basketball shots', "
            "'cut everything except crowd cheering moments')."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #CCCCCC; margin-bottom: 15px;")
        layout.addWidget(desc_label)
        
        # Video selection group
        video_group = QGroupBox("Video Selection")
        video_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        video_layout = QVBoxLayout(video_group)
        
        # Video file selection
        file_layout = QHBoxLayout()
        self.video_path_label = QLabel("No video selected")
        self.video_path_label.setStyleSheet("color: #CCCCCC; padding: 5px; border: 1px solid #444; border-radius: 4px;")
        file_layout.addWidget(self.video_path_label)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._browse_video)
        self.browse_button.setStyleSheet("""
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
        file_layout.addWidget(self.browse_button)
        
        video_layout.addLayout(file_layout)
        layout.addWidget(video_group)
        
        # Settings group
        settings_group = QGroupBox("Highlight Reel Settings")
        settings_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        settings_layout = QFormLayout(settings_group)
        
        # Target duration
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(5, 300)  # 5 seconds to 5 minutes
        self.duration_spinbox.setValue(30)
        self.duration_spinbox.setSuffix(" seconds")
        self.duration_spinbox.setStyleSheet("color: #FFFFFF; background-color: #2a2a2a; border: 1px solid #444; padding: 5px;")
        settings_layout.addRow("Target Duration:", self.duration_spinbox)
        
        layout.addWidget(settings_group)
        
        # Prompt group
        prompt_group = QGroupBox("Content Instructions (Optional)")
        prompt_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        prompt_layout = QVBoxLayout(prompt_group)
        
        # Prompt text area
        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText(
            "Enter instructions for what to include or exclude in the highlight reel...\n\n"
            "Examples:\n"
            "• 'only show missed basketball shots'\n"
            "• 'cut everything except crowd cheering moments'\n"
            "• 'focus on the beginning and end'\n"
            "• 'show only the middle section'"
        )
        self.prompt_text.setMaximumHeight(120)
        self.prompt_text.setStyleSheet("""
            QTextEdit {
                color: #FFFFFF;
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        prompt_layout.addWidget(self.prompt_text)
        
        layout.addWidget(prompt_group)
        
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
        
        self.generate_button = QPushButton("Generate Highlight Reel")
        self.generate_button.clicked.connect(self._generate_highlight_reel)
        self.generate_button.setEnabled(False)
        self.generate_button.setStyleSheet("""
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
        button_layout.addWidget(self.generate_button)
        
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
            filename = os.path.basename(file_path)
            self.video_path_label.setText(filename)
            self.generate_button.setEnabled(True)
            
            # Get video info and display
            video_handler = VideoHandler()
            info = video_handler.get_video_info(file_path)
            if "error" not in info:
                duration_min = int(info["duration"] // 60)
                duration_sec = int(info["duration"] % 60)
                self.status_label.setText(
                    f"Video: {info['width']}x{info['height']}, "
                    f"Duration: {duration_min}:{duration_sec:02d}, "
                    f"Size: {info['file_size'] / (1024*1024):.1f} MB"
                )
    
    def _generate_highlight_reel(self):
        """Generate the highlight reel."""
        # Check permissions first
        if not check_feature_access_with_dialog(Feature.HIGHLIGHT_REEL_GENERATOR, self):
            return
        if not check_usage_limit_with_dialog('videos', 1, self):
            return
            
        if not self.video_path:
            QMessageBox.warning(self, "Warning", "Please select a video file first.")
            return
        
        # Disable UI during processing
        self.generate_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Get settings
        target_duration = self.duration_spinbox.value()
        prompt = self.prompt_text.toPlainText().strip()
        
        # Start worker thread
        self.worker = HighlightReelWorker(self.video_path, target_duration, prompt)
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._on_generation_finished)
        self.worker.start()
    
    def _update_progress(self, message: str):
        """Update progress message."""
        self.status_label.setText(message)
    
    def _on_generation_finished(self, success: bool, output_path: str, message: str):
        """Handle generation completion."""
        # Re-enable UI
        self.generate_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText(f"✓ {message}")
            QMessageBox.information(
                self,
                "Success",
                f"Highlight reel generated successfully!\n\nSaved to: {output_path}"
            )
            self.accept()
        else:
            self.status_label.setText(f"✗ {message}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate highlight reel:\n\n{message}"
            )
        
        # Clean up worker
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Cancel Generation",
                "Video processing is in progress. Are you sure you want to cancel?",
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