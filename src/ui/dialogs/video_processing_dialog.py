"""
Video Processing Dialog for Crow's Eye platform.
Allows users to select and apply multiple video processing options in sequence.
"""

import os
import logging
from typing import List, Dict, Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QGroupBox, QProgressBar, QTextEdit, QMessageBox,
    QListWidget, QListWidgetItem, QSplitter, QFrame
)

from ..base_dialog import BaseDialog


class VideoProcessingWorker(QThread):
    """Worker thread for processing video through multiple services."""
    
    progress = Signal(str)
    step_completed = Signal(str, bool, str)  # step_name, success, output_path
    finished = Signal(bool, str, str)  # success, final_output_path, message
    
    def __init__(self, video_path: str, processing_steps: List[Dict]):
        super().__init__()
        self.video_path = video_path
        self.processing_steps = processing_steps
        self.current_video_path = video_path
        
    def run(self):
        """Run the video processing pipeline."""
        try:
            for i, step in enumerate(self.processing_steps):
                step_name = step['name']
                self.progress.emit(f"Processing step {i+1}/{len(self.processing_steps)}: {step_name}")
                
                # Process based on step type
                success, output_path, message = self._process_step(step)
                
                self.step_completed.emit(step_name, success, output_path if success else message)
                
                if not success:
                    self.finished.emit(False, "", f"Failed at step '{step_name}': {message}")
                    return
                
                # Update current video path for next step
                if output_path:
                    self.current_video_path = output_path
            
            self.finished.emit(True, self.current_video_path, "Video processing completed successfully")
            
        except Exception as e:
            self.finished.emit(False, "", f"Error during processing: {str(e)}")
    
    def _process_step(self, step: Dict) -> tuple:
        """Process a single step."""
        try:
            from ...handlers.video_handler import VideoHandler
            video_handler = VideoHandler()
            
            step_type = step['type']
            
            if step_type == 'highlight_reel':
                return video_handler.generate_highlight_reel(
                    self.current_video_path, 
                    target_duration=step.get('duration', 30),
                    prompt=step.get('prompt', '')
                )
            elif step_type == 'story_clips':
                return video_handler.create_story_clips(
                    self.current_video_path,
                    max_clip_duration=step.get('max_duration', 60)
                )
            elif step_type == 'thumbnail':
                return video_handler.generate_thumbnail(
                    self.current_video_path,
                    timestamp=step.get('timestamp', 0)
                )
            elif step_type == 'audio_overlay':
                return video_handler.add_audio_overlay(
                    self.current_video_path,
                    step.get('audio_path', ''),
                    volume=step.get('volume', 1.0),
                    start_time=step.get('start_time', 0)
                )
            else:
                return False, "", f"Unknown step type: {step_type}"
                
        except Exception as e:
            return False, "", str(e)


class VideoProcessingDialog(BaseDialog):
    """Dialog for selecting and processing video through multiple services."""
    
    # Signal emitted when video processing is complete
    video_processed = Signal(str)  # final_video_path
    
    def __init__(self, video_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video Processing Pipeline")
        self.setFixedSize(800, 600)
        self.video_path = video_path
        self.worker = None
        self.processing_steps = []
        self._setup_ui()
        self._update_video_info()
        
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Video Processing Pipeline")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "Select the video processing services you want to apply. "
            "They will be executed in the order shown below. "
            "The final processed video will be loaded into the main interface."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #CCCCCC; margin-bottom: 15px;")
        layout.addWidget(desc_label)
        
        # Video info section
        video_info_group = QGroupBox("Current Video")
        video_info_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        video_info_layout = QVBoxLayout(video_info_group)
        
        self.video_info_label = QLabel(os.path.basename(self.video_path))
        self.video_info_label.setStyleSheet("color: #CCCCCC; padding: 5px; border: 1px solid #444; border-radius: 4px;")
        video_info_layout.addWidget(self.video_info_label)
        
        layout.addWidget(video_info_group)
        
        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Service selection
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        
        services_group = QGroupBox("Available Services")
        services_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        services_layout = QVBoxLayout(services_group)
        
        # Service checkboxes
        self.highlight_reel_cb = QCheckBox("Highlight Reel Generator")
        self.highlight_reel_cb.setStyleSheet("color: #FFFFFF;")
        self.highlight_reel_cb.toggled.connect(self._update_processing_queue)
        services_layout.addWidget(self.highlight_reel_cb)
        
        self.story_clips_cb = QCheckBox("Story Assistant")
        self.story_clips_cb.setStyleSheet("color: #FFFFFF;")
        self.story_clips_cb.toggled.connect(self._update_processing_queue)
        services_layout.addWidget(self.story_clips_cb)
        
        self.thumbnail_cb = QCheckBox("Thumbnail Generator")
        self.thumbnail_cb.setStyleSheet("color: #FFFFFF;")
        self.thumbnail_cb.toggled.connect(self._update_processing_queue)
        services_layout.addWidget(self.thumbnail_cb)
        
        self.audio_overlay_cb = QCheckBox("Audio Overlay")
        self.audio_overlay_cb.setStyleSheet("color: #FFFFFF;")
        self.audio_overlay_cb.toggled.connect(self._update_processing_queue)
        services_layout.addWidget(self.audio_overlay_cb)
        
        left_layout.addWidget(services_group)
        left_layout.addStretch()
        
        # Right panel - Processing queue
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        
        queue_group = QGroupBox("Processing Queue")
        queue_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        queue_layout = QVBoxLayout(queue_group)
        
        self.queue_list = QListWidget()
        self.queue_list.setStyleSheet("""
            QListWidget {
                background-color: #2a2a2a;
                color: #FFFFFF;
                border: 1px solid #444;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:selected {
                background-color: #3b82f6;
            }
        """)
        queue_layout.addWidget(self.queue_list)
        
        right_layout.addWidget(queue_group)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 4px;
                text-align: center;
                color: #FFFFFF;
                background-color: #2a2a2a;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready to process")
        self.progress_label.setStyleSheet("color: #CCCCCC;")
        progress_layout.addWidget(self.progress_label)
        
        right_layout.addWidget(progress_group)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
        
        # Button section
        button_layout = QHBoxLayout()
        
        self.process_btn = QPushButton("Start Processing")
        self.process_btn.setEnabled(False)
        self.process_btn.setStyleSheet("""
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
                background-color: #444;
                color: #888;
            }
        """)
        self.process_btn.clicked.connect(self._start_processing)
        button_layout.addWidget(self.process_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
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
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
    def _update_video_info(self):
        """Update the video information display."""
        try:
            from ...handlers.video_handler import VideoHandler
            video_handler = VideoHandler()
            video_info = video_handler.get_video_info(self.video_path)
            
            if "error" not in video_info:
                duration_min = int(video_info["duration"] // 60)
                duration_sec = int(video_info["duration"] % 60)
                
                info_text = f"""
                <b>{os.path.basename(self.video_path)}</b><br>
                Resolution: {video_info['width']}x{video_info['height']}<br>
                Duration: {duration_min}:{duration_sec:02d}<br>
                Size: {video_info['file_size'] / (1024*1024):.1f} MB
                """
                self.video_info_label.setText(info_text)
            else:
                self.video_info_label.setText(f"Error reading video: {video_info.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.video_info_label.setText(f"Error processing video info: {str(e)}")
    
    def _update_processing_queue(self):
        """Update the processing queue based on selected services."""
        self.queue_list.clear()
        self.processing_steps.clear()
        
        # Add selected services to queue in order
        if self.highlight_reel_cb.isChecked():
            self.processing_steps.append({
                'name': 'Highlight Reel Generator',
                'type': 'highlight_reel',
                'duration': 30,
                'prompt': ''
            })
            item = QListWidgetItem("1. Highlight Reel Generator")
            self.queue_list.addItem(item)
        
        if self.story_clips_cb.isChecked():
            self.processing_steps.append({
                'name': 'Story Assistant',
                'type': 'story_clips',
                'max_duration': 60
            })
            item = QListWidgetItem(f"{len(self.processing_steps)}. Story Assistant")
            self.queue_list.addItem(item)
        
        if self.thumbnail_cb.isChecked():
            self.processing_steps.append({
                'name': 'Thumbnail Generator',
                'type': 'thumbnail',
                'timestamp': 0
            })
            item = QListWidgetItem(f"{len(self.processing_steps)}. Thumbnail Generator")
            self.queue_list.addItem(item)
        
        if self.audio_overlay_cb.isChecked():
            self.processing_steps.append({
                'name': 'Audio Overlay',
                'type': 'audio_overlay',
                'audio_path': '',
                'volume': 1.0,
                'start_time': 0
            })
            item = QListWidgetItem(f"{len(self.processing_steps)}. Audio Overlay")
            self.queue_list.addItem(item)
        
        # Enable/disable process button
        self.process_btn.setEnabled(len(self.processing_steps) > 0)
        
        if len(self.processing_steps) == 0:
            self.progress_label.setText("Select at least one service to process")
        else:
            self.progress_label.setText(f"Ready to process {len(self.processing_steps)} step(s)")
    
    def _start_processing(self):
        """Start the video processing pipeline."""
        if not self.processing_steps:
            return
        
        # Disable UI during processing
        self.process_btn.setEnabled(False)
        self.highlight_reel_cb.setEnabled(False)
        self.story_clips_cb.setEnabled(False)
        self.thumbnail_cb.setEnabled(False)
        self.audio_overlay_cb.setEnabled(False)
        
        # Setup progress bar
        self.progress_bar.setRange(0, len(self.processing_steps))
        self.progress_bar.setValue(0)
        
        # Start worker thread
        self.worker = VideoProcessingWorker(self.video_path, self.processing_steps)
        self.worker.progress.connect(self._update_progress)
        self.worker.step_completed.connect(self._on_step_completed)
        self.worker.finished.connect(self._on_processing_finished)
        self.worker.start()
    
    def _update_progress(self, message: str):
        """Update progress display."""
        self.progress_label.setText(message)
    
    def _on_step_completed(self, step_name: str, success: bool, result: str):
        """Handle completion of a processing step."""
        current_value = self.progress_bar.value()
        self.progress_bar.setValue(current_value + 1)
        
        # Update queue list to show completion
        for i in range(self.queue_list.count()):
            item = self.queue_list.item(i)
            if step_name in item.text():
                if success:
                    item.setText(f"✓ {item.text()}")
                    item.setBackground(Qt.GlobalColor.darkGreen)
                else:
                    item.setText(f"✗ {item.text()}")
                    item.setBackground(Qt.GlobalColor.darkRed)
                break
    
    def _on_processing_finished(self, success: bool, final_output_path: str, message: str):
        """Handle completion of all processing."""
        # Re-enable UI
        self.process_btn.setEnabled(True)
        self.highlight_reel_cb.setEnabled(True)
        self.story_clips_cb.setEnabled(True)
        self.thumbnail_cb.setEnabled(True)
        self.audio_overlay_cb.setEnabled(True)
        
        if success:
            self.progress_label.setText("Processing completed successfully!")
            
            # Show success message
            QMessageBox.information(
                self,
                "Processing Complete",
                f"Video processing completed successfully!\n\nFinal video: {os.path.basename(final_output_path)}\n\nThe processed video will now be loaded into the main interface."
            )
            
            # Emit signal with final video path
            self.video_processed.emit(final_output_path)
            
            # Close dialog
            self.accept()
        else:
            self.progress_label.setText(f"Processing failed: {message}")
            
            # Show error message
            QMessageBox.critical(
                self,
                "Processing Failed",
                f"Video processing failed:\n\n{message}"
            )
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Processing in Progress",
                "Video processing is still running. Do you want to cancel it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.terminate()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept() 