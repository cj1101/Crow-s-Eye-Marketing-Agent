"""
Highlight Reel Generator Dialog for Crow's Eye platform.
Allows users to create highlight reels from long videos with natural language prompts.
"""

import os
import logging
from typing import Dict, Any, Optional

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSpinBox, QTextEdit, QProgressBar, QFileDialog,
    QGroupBox, QFormLayout, QMessageBox, QWidget, QSlider, QCheckBox,
    QDoubleSpinBox, QFrame
)
# Video preview imports removed - using simple timestamp inputs instead

from ..base_dialog import BaseDialog
from ...features.media_processing.video_handler import VideoHandler
from ...utils.subscription_utils import (
    check_feature_access_with_dialog, check_usage_limit_with_dialog,
    requires_feature_qt, requires_usage_qt, show_upgrade_dialog
)
from ...features.subscription.access_control import Feature
# from ...handlers.analytics_handler import AnalyticsHandler


class HighlightReelWorker(QThread):
    """Worker thread for generating highlight reels."""
    
    progress = Signal(str)
    finished = Signal(bool, str, str)  # success, output_path, message
    
    def __init__(self, video_path: str, target_duration: int, prompt: str, example_data: Optional[Dict[str, Any]] = None, use_extended_mode: bool = False):
        super().__init__()
        self.video_path = video_path
        self.target_duration = target_duration
        self.prompt = prompt
        self.example_data = example_data
        self.use_extended_mode = use_extended_mode
        self.video_handler = VideoHandler()
    
    def run(self):
        """Run the highlight reel generation."""
        try:
            if self.use_extended_mode:
                # Use BETA extended video mode for hours-long videos
                self.progress.emit("🚀 BETA Extended Mode: Analyzing long video with cost optimization...")
                success, output_path, message = self.video_handler.generate_extended_highlight_reel_beta(
                    self.video_path, self.target_duration, self.prompt, max_cost=1.0
                )
            elif self.example_data and self.example_data.get('has_segment', False):
                # Use example-based generation
                self.progress.emit("Analyzing video for similar segments...")
                success, output_path, message = self.video_handler.generate_example_based_highlight_reel(
                    self.video_path, self.example_data, self.target_duration, 
                    context_padding=self.example_data.get('context_padding', 2.0),
                    prompt=self.prompt
                )
            else:
                # Use traditional prompt-based generation
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
        self.setFixedSize(900, 700)  # Increased size for video preview
        self.video_path = ""
        self.worker = None
        self.example_start_time = 0.0
        self.example_end_time = 0.0
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
            "Generate a highlight reel from a long video. You can either use text instructions only, "
            "or select an example segment from your video to find similar moments."
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
        
        # Example Segment Selection Group
        example_group = QGroupBox("Example Segment Selection (Optional)")
        example_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        example_layout = QVBoxLayout(example_group)
        
        # Enable example segment checkbox
        self.use_example_cb = QCheckBox("Use example segment to find similar moments")
        self.use_example_cb.setStyleSheet("color: #FFFFFF; font-weight: bold;")
        self.use_example_cb.toggled.connect(self._toggle_example_controls)
        example_layout.addWidget(self.use_example_cb)
        
        # Simple timestamp input (initially hidden)
        self.example_controls_widget = QWidget()
        example_controls_layout = QVBoxLayout(self.example_controls_widget)
        
        # Instructions
        instructions_label = QLabel(
            "Enter the start and end times (in seconds) of a segment that represents what you want to find more of.\n"
            "You can find these timestamps by playing your video in any media player."
        )
        instructions_label.setWordWrap(True)
        instructions_label.setStyleSheet("color: #CCCCCC; font-size: 12px; margin-bottom: 10px;")
        example_controls_layout.addWidget(instructions_label)
        
        # Example segment selection
        segment_layout = QFormLayout()
        
        # Start time
        self.start_time_spinbox = QDoubleSpinBox()
        self.start_time_spinbox.setRange(0.0, 9999.0)
        self.start_time_spinbox.setDecimals(1)
        self.start_time_spinbox.setSuffix(" seconds")
        self.start_time_spinbox.setStyleSheet("color: #FFFFFF; background-color: #2a2a2a; border: 1px solid #444; padding: 5px;")
        self.start_time_spinbox.valueChanged.connect(self._update_example_segment)
        segment_layout.addRow("Start Time:", self.start_time_spinbox)
        
        # End time
        self.end_time_spinbox = QDoubleSpinBox()
        self.end_time_spinbox.setRange(0.0, 9999.0)
        self.end_time_spinbox.setDecimals(1)
        self.end_time_spinbox.setSuffix(" seconds")
        self.end_time_spinbox.setStyleSheet("color: #FFFFFF; background-color: #2a2a2a; border: 1px solid #444; padding: 5px;")
        self.end_time_spinbox.valueChanged.connect(self._update_example_segment)
        segment_layout.addRow("End Time:", self.end_time_spinbox)
        
        example_controls_layout.addLayout(segment_layout)
        
        # Context padding
        self.context_padding_spinbox = QDoubleSpinBox()
        self.context_padding_spinbox.setRange(0.0, 10.0)
        self.context_padding_spinbox.setValue(2.0)
        self.context_padding_spinbox.setDecimals(1)
        self.context_padding_spinbox.setSuffix(" seconds")
        self.context_padding_spinbox.setStyleSheet("color: #FFFFFF; background-color: #2a2a2a; border: 1px solid #444; padding: 5px;")
        segment_layout.addRow("Context Padding:", self.context_padding_spinbox)
        
        # Help text with examples
        help_label = QLabel(
            "Example: If you want to find all basketball shots, find a shot in your video (e.g., from 45.2 to 48.7 seconds) "
            "and enter those times. The AI will find all similar shooting motions throughout the video."
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #888888; font-size: 11px; font-style: italic; margin-top: 10px;")
        example_controls_layout.addWidget(help_label)
        
        # Initially hide example controls
        self.example_controls_widget.setVisible(False)
        example_layout.addWidget(self.example_controls_widget)
        
        layout.addWidget(example_group)
        
        # Settings group
        settings_group = QGroupBox("Highlight Reel Settings")
        settings_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        settings_layout = QFormLayout(settings_group)
        
        # Beta feature toggle
        self.extended_mode_cb = QCheckBox("🚀 BETA: Extended Video Mode (for hours-long videos, <$1 cost)")
        self.extended_mode_cb.setStyleSheet("color: #10b981; font-weight: bold;")
        self.extended_mode_cb.setToolTip("BETA feature for processing very long videos (hours) while keeping AI analysis costs under $1")
        settings_layout.addRow(self.extended_mode_cb)
        
        # Target duration
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(5, 1800)  # 5 seconds to 30 minutes
        self.duration_spinbox.setValue(30)
        self.duration_spinbox.setSuffix(" seconds")
        self.duration_spinbox.setStyleSheet("color: #FFFFFF; background-color: #2a2a2a; border: 1px solid #444; padding: 5px; font-size: 14px;")
        
        # Update range when extended mode is toggled
        self.extended_mode_cb.toggled.connect(self._update_duration_range)
        
        # Add helpful text showing the range
        self.duration_help = QLabel("(5 seconds to 30 minutes)")
        self.duration_help.setStyleSheet("color: #888888; font-size: 11px; font-style: italic;")
        
        duration_layout = QVBoxLayout()
        duration_layout.addWidget(self.duration_spinbox)
        duration_layout.addWidget(self.duration_help)
        duration_layout.setContentsMargins(0, 0, 0, 0)
        duration_layout.setSpacing(2)
        
        duration_widget = QWidget()
        duration_widget.setLayout(duration_layout)
        
        settings_layout.addRow("Target Duration:", duration_widget)
        
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
            from ...features.media_processing.video_handler import VideoHandler
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
                
                # Set reasonable default values for the example segment
                self.start_time_spinbox.setMaximum(info["duration"])
                self.end_time_spinbox.setMaximum(info["duration"])
                self.end_time_spinbox.setValue(min(5.0, info["duration"]))  # Default 5-second segment
    
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
        
        # Validate example segment if enabled
        example_data = None
        if self.use_example_cb.isChecked():
            if self.example_start_time >= self.example_end_time:
                QMessageBox.warning(self, "Warning", "Example segment start time must be less than end time.")
                return
            
            example_data = {
                'has_segment': True,
                'start_time': self.example_start_time,
                'end_time': self.example_end_time,
                'context_padding': self.context_padding_spinbox.value(),
                'description': self.prompt_text.toPlainText().strip()
            }
        
        # Disable UI during processing
        self.generate_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Get settings
        target_duration = self.duration_spinbox.value()
        prompt = self.prompt_text.toPlainText().strip()
        use_extended_mode = self.extended_mode_cb.isChecked()
        
        # Start worker thread
        self.worker = HighlightReelWorker(self.video_path, target_duration, prompt, example_data, use_extended_mode)
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
    
    def _toggle_example_controls(self, checked: bool):
        """Toggle visibility of example segment controls."""
        self.example_controls_widget.setVisible(checked)
    
    def _update_example_segment(self):
        """Update example segment values."""
        self.example_start_time = self.start_time_spinbox.value()
        self.example_end_time = self.end_time_spinbox.value()
        
        # Validate segment
        if self.example_start_time >= self.example_end_time:
            self.status_label.setText("Warning: Start time must be less than end time")
            self.status_label.setStyleSheet("color: #ef4444; font-style: italic;")
        else:
            duration = self.example_end_time - self.example_start_time
            self.status_label.setText(f"Example segment: {duration:.1f} seconds")
            self.status_label.setStyleSheet("color: #10b981; font-style: italic;")
    
    def _update_duration_range(self, checked: bool):
        """Update duration range based on extended mode."""
        if checked:
            self.duration_spinbox.setRange(5, 1800)  # 5 seconds to 30 minutes
        else:
            self.duration_spinbox.setRange(5, 300)  # 5 seconds to 5 minutes
        self.duration_spinbox.setValue(30)  # Reset to default value
        self.duration_help.setText("(5 seconds to 30 minutes)")
        self.duration_help.setStyleSheet("color: #888888; font-size: 11px; font-style: italic;")
        self.duration_spinbox.setStyleSheet("color: #FFFFFF; background-color: #2a2a2a; border: 1px solid #444; padding: 5px; font-size: 14px;") 