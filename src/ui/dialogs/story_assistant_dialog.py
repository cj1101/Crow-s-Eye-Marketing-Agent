"""
Story Assistant Dialog for Crow's Eye platform.
Converts long videos into story-formatted clips (<60s each) with vertical formatting.
"""

import os
import logging
from typing import List

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSpinBox, QProgressBar, QFileDialog, QGroupBox, QFormLayout, 
    QMessageBox, QListWidget, QListWidgetItem
)

from ..base_dialog import BaseDialog
from ...features.media_processing.video_handler import VideoHandler
from ...utils.subscription_utils import (
    check_feature_access_with_dialog, check_usage_limit_with_dialog,
    requires_feature_qt, requires_usage_qt, show_upgrade_dialog
)
from ...features.subscription.access_control import Feature


class StoryAssistantWorker(QThread):
    """Worker thread for creating story clips."""
    
    progress = Signal(str)
    finished = Signal(bool, list, str)  # success, output_paths, message
    
    def __init__(self, video_path: str, max_clip_duration: int):
        super().__init__()
        self.video_path = video_path
        self.max_clip_duration = max_clip_duration
        self.video_handler = VideoHandler()
    
    def run(self):
        """Run the story clip creation."""
        try:
            self.progress.emit("Processing video for stories...")
            success, output_paths, message = self.video_handler.create_story_clips(
                self.video_path, self.max_clip_duration
            )
            self.finished.emit(success, output_paths, message)
        except Exception as e:
            self.finished.emit(False, [], f"Error: {str(e)}")


class StoryAssistantDialog(BaseDialog):
    """Dialog for creating story clips from long videos."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Story Assistant")
        self.setFixedSize(650, 550)
        self.video_path = ""
        self.worker = None
        self.output_paths = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Story Assistant")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "Convert long videos into story-formatted clips. Each clip will be under 60 seconds "
            "and automatically formatted for vertical display (9:16 aspect ratio) perfect for "
            "Instagram and Facebook Stories."
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
        settings_group = QGroupBox("Story Settings")
        settings_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        settings_layout = QFormLayout(settings_group)
        
        # Max clip duration
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(15, 60)  # 15 to 60 seconds
        self.duration_spinbox.setValue(60)
        self.duration_spinbox.setSuffix(" seconds")
        self.duration_spinbox.setStyleSheet("color: #FFFFFF; background-color: #2a2a2a; border: 1px solid #444; padding: 5px;")
        settings_layout.addRow("Max Clip Duration:", self.duration_spinbox)
        
        # Info label
        info_label = QLabel("Each story clip will be automatically formatted to 9:16 aspect ratio (1080x1920)")
        info_label.setStyleSheet("color: #888888; font-size: 11px; font-style: italic;")
        settings_layout.addRow("", info_label)
        
        layout.addWidget(settings_group)
        
        # Results group (initially hidden)
        self.results_group = QGroupBox("Generated Story Clips")
        self.results_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        self.results_group.setVisible(False)
        results_layout = QVBoxLayout(self.results_group)
        
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                color: #FFFFFF;
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:selected {
                background-color: #3b82f6;
            }
        """)
        self.results_list.setMaximumHeight(150)
        results_layout.addWidget(self.results_list)
        
        # Results buttons
        results_button_layout = QHBoxLayout()
        
        self.open_folder_button = QPushButton("Open Output Folder")
        self.open_folder_button.clicked.connect(self._open_output_folder)
        self.open_folder_button.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        results_button_layout.addWidget(self.open_folder_button)
        results_button_layout.addStretch()
        
        results_layout.addLayout(results_button_layout)
        layout.addWidget(self.results_group)
        
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
        
        self.generate_button = QPushButton("Create Story Clips")
        self.generate_button.clicked.connect(self._create_story_clips)
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
                
                # Calculate estimated number of clips
                max_duration = self.duration_spinbox.value()
                estimated_clips = int(info["duration"] // max_duration) + (1 if info["duration"] % max_duration > 0 else 0)
                
                self.status_label.setText(
                    f"Video: {info['width']}x{info['height']}, "
                    f"Duration: {duration_min}:{duration_sec:02d}, "
                    f"Estimated clips: {estimated_clips}"
                )
    
    def _create_story_clips(self):
        """Create the story clips."""
        # Check permissions first
        if not check_feature_access_with_dialog(Feature.STORY_ASSISTANT, self):
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
        max_clip_duration = self.duration_spinbox.value()
        
        # Start worker thread
        self.worker = StoryAssistantWorker(self.video_path, max_clip_duration)
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._on_creation_finished)
        self.worker.start()
    
    def _update_progress(self, message: str):
        """Update progress message."""
        self.status_label.setText(message)
    
    def _on_creation_finished(self, success: bool, output_paths: List[str], message: str):
        """Handle creation completion."""
        # Re-enable UI
        self.generate_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success and output_paths:
            self.output_paths = output_paths
            self.status_label.setText(f"✓ {message}")
            
            # Show results
            self.results_group.setVisible(True)
            self.results_list.clear()
            
            for i, path in enumerate(output_paths, 1):
                filename = os.path.basename(path)
                item = QListWidgetItem(f"Clip {i}: {filename}")
                item.setData(Qt.UserRole, path)
                self.results_list.addItem(item)
            
            # Resize dialog to accommodate results
            self.adjustSize()
            
            QMessageBox.information(
                self,
                "Success",
                f"Story clips created successfully!\n\n{len(output_paths)} clips generated and saved to the output folder."
            )
        else:
            self.status_label.setText(f"✗ {message}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to create story clips:\n\n{message}"
            )
        
        # Clean up worker
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
    
    def _open_output_folder(self):
        """Open the output folder in file explorer."""
        if self.output_paths:
            output_dir = os.path.dirname(self.output_paths[0])
            if os.path.exists(output_dir):
                import subprocess
                import platform
                
                try:
                    if platform.system() == "Windows":
                        subprocess.run(["explorer", output_dir])
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", output_dir])
                    else:  # Linux
                        subprocess.run(["xdg-open", output_dir])
                except Exception as e:
                    QMessageBox.warning(self, "Warning", f"Could not open folder: {str(e)}")
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Cancel Processing",
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