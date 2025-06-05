"""
Video Processing Pipeline Dialog - Step-by-step video processing with user interaction.
"""
import os
import logging
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QWidget, QListWidget, QListWidgetItem, QTextEdit,
    QProgressBar, QMessageBox, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QPixmap

from ..base_dialog import BaseDialog
from ...features.media_processing.video_edit_handler import VideoEditHandler
from ...features.media_processing.video_handler import VideoHandler


class VideoProcessingPipelineDialog(BaseDialog):
    """Dialog for step-by-step video processing with user interaction."""
    
    # Signal emitted when processing is complete
    processing_complete = Signal(str)  # final_video_path
    
    def __init__(self, video_path: str, selected_services: Dict[str, bool], parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.video_path = video_path
        self.selected_services = selected_services
        self.processing_queue = []
        self.current_step_index = 0
        self.current_video_path = video_path
        self.video_handler = VideoEditHandler()
        
        self.setWindowTitle("Video Processing Pipeline")
        self.setModal(True)
        self.setFixedSize(1000, 700)
        
        self._setup_processing_queue()
        self._setup_ui()
        
        self.logger.info("Video Processing Pipeline dialog initialized")
    
    def _setup_processing_queue(self):
        """Set up the processing queue based on selected services."""
        service_order = [
            ('color_grading', 'Color Grading & Enhancement'),
            ('stabilization', 'Video Stabilization'),
            ('audio_enhancement', 'Audio Enhancement'),
            ('motion_graphics', 'Motion Graphics & Text'),
            ('transitions', 'Smooth Transitions'),
            ('social_optimization', 'Social Media Optimization'),
            ('captions_subtitles', 'Captions & Subtitles'),
            ('highlight_reel', 'Highlight Reel Creation')
        ]
        
        for service_id, service_name in service_order:
            if self.selected_services.get(service_id, False):
                self.processing_queue.append({
                    'id': service_id,
                    'name': service_name,
                    'status': 'pending',
                    'output_path': None
                })
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        self._create_header(layout)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Queue and progress
        left_widget = self._create_queue_widget()
        splitter.addWidget(left_widget)
        
        # Right side - Current step details
        right_widget = self._create_step_details_widget()
        splitter.addWidget(right_widget)
        
        splitter.setSizes([400, 600])
        layout.addWidget(splitter)
        
        # Control buttons
        self._create_control_buttons(layout)
        
        # Update UI for first step
        self._update_ui_for_current_step()
        
        # Apply styling
        self.setStyleSheet("""
            QDialog {
                background-color: #2a2a2a;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
    
    def _create_header(self, main_layout: QVBoxLayout):
        """Create the header section."""
        # Title
        title_label = QLabel("Video Processing Pipeline")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Process your video step by step with full control over each service")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #cccccc; font-size: 14px; margin-bottom: 15px;")
        main_layout.addWidget(subtitle_label)
        
        # Overall progress
        self.overall_progress = QProgressBar()
        self.overall_progress.setMaximum(len(self.processing_queue))
        self.overall_progress.setValue(0)
        self.overall_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 5px;
                text-align: center;
                color: #ffffff;
                background-color: #333;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.overall_progress)
    
    def _create_queue_widget(self):
        """Create the processing queue widget."""
        group = QGroupBox("Processing Queue")
        layout = QVBoxLayout(group)
        
        # Queue list
        self.queue_list = QListWidget()
        self.queue_list.setStyleSheet("""
            QListWidget {
                background-color: #333;
                border: 1px solid #444;
                border-radius: 5px;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
            }
        """)
        
        # Populate queue list
        for i, step in enumerate(self.processing_queue):
            item = QListWidgetItem(f"{i+1}. {step['name']}")
            item.setData(Qt.ItemDataRole.UserRole, step['id'])
            self.queue_list.addItem(item)
        
        layout.addWidget(self.queue_list)
        
        # Queue info
        queue_info = QLabel(f"Total steps: {len(self.processing_queue)}")
        queue_info.setStyleSheet("color: #cccccc; font-size: 12px;")
        layout.addWidget(queue_info)
        
        return group
    
    def _create_step_details_widget(self):
        """Create the step details widget."""
        group = QGroupBox("Current Step")
        layout = QVBoxLayout(group)
        
        # Step title
        self.step_title = QLabel("Ready to start")
        step_font = QFont()
        step_font.setPointSize(14)
        step_font.setBold(True)
        self.step_title.setFont(step_font)
        self.step_title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(self.step_title)
        
        # Step description
        self.step_description = QLabel("Click 'Start Processing' to begin the first step")
        self.step_description.setWordWrap(True)
        self.step_description.setStyleSheet("color: #cccccc; margin-bottom: 15px;")
        layout.addWidget(self.step_description)
        
        # Video preview (placeholder)
        self.video_preview = QLabel("Video Preview")
        self.video_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_preview.setStyleSheet("""
            QLabel {
                border: 2px dashed #666;
                border-radius: 10px;
                background-color: #333;
                min-height: 200px;
                color: #999;
            }
        """)
        layout.addWidget(self.video_preview)
        
        # Step progress
        self.step_progress = QProgressBar()
        self.step_progress.setVisible(False)
        self.step_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 5px;
                text-align: center;
                color: #ffffff;
                background-color: #333;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.step_progress)
        
        # Step status
        self.step_status = QLabel("Ready")
        self.step_status.setStyleSheet("color: #cccccc; font-size: 12px;")
        layout.addWidget(self.step_status)
        
        # Step options (for user input)
        self.step_options = QFrame()
        self.step_options.setVisible(False)
        options_layout = QVBoxLayout(self.step_options)
        
        # Options will be populated dynamically based on the current step
        self.options_text = QTextEdit()
        self.options_text.setPlaceholderText("Enter any specific instructions for this step...")
        self.options_text.setMaximumHeight(80)
        self.options_text.setStyleSheet("""
            QTextEdit {
                background-color: #333;
                border: 1px solid #444;
                border-radius: 5px;
                color: #ffffff;
                padding: 5px;
            }
        """)
        options_layout.addWidget(self.options_text)
        
        layout.addWidget(self.step_options)
        
        return group
    
    def _create_control_buttons(self, main_layout: QVBoxLayout):
        """Create the control buttons."""
        button_layout = QHBoxLayout()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        # Skip step button
        self.skip_button = QPushButton("Skip This Step")
        self.skip_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        self.skip_button.clicked.connect(self._skip_current_step)
        self.skip_button.setVisible(False)
        button_layout.addWidget(self.skip_button)
        
        # Process step button
        self.process_button = QPushButton("Start Processing")
        self.process_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #666;
                color: #999;
            }
        """)
        self.process_button.clicked.connect(self._process_current_step)
        button_layout.addWidget(self.process_button)
        
        main_layout.addLayout(button_layout)
    
    def _update_ui_for_current_step(self):
        """Update the UI for the current step."""
        if self.current_step_index >= len(self.processing_queue):
            # All steps completed
            self._show_completion_ui()
            return
        
        current_step = self.processing_queue[self.current_step_index]
        
        # Update step details
        self.step_title.setText(current_step['name'])
        self.step_description.setText(self._get_step_description(current_step['id']))
        
        # Update queue list highlighting
        for i in range(self.queue_list.count()):
            item = self.queue_list.item(i)
            if i == self.current_step_index:
                item.setText(f"▶ {i+1}. {self.processing_queue[i]['name']}")
                self.queue_list.setCurrentItem(item)
            elif i < self.current_step_index:
                status = "✓" if self.processing_queue[i]['status'] == 'completed' else "✗"
                item.setText(f"{status} {i+1}. {self.processing_queue[i]['name']}")
            else:
                item.setText(f"{i+1}. {self.processing_queue[i]['name']}")
        
        # Update buttons
        self.skip_button.setVisible(True)
        self.process_button.setText("Process This Step")
        self.process_button.setEnabled(True)
        
        # Show step options
        self.step_options.setVisible(True)
        self.options_text.clear()
        self.options_text.setPlaceholderText(self._get_step_placeholder(current_step['id']))
        
        # Update video preview
        self._update_video_preview()
    
    def _get_step_description(self, step_id: str) -> str:
        """Get description for a processing step."""
        descriptions = {
            'color_grading': 'Apply professional color correction, brightness adjustment, and cinematic color grading for marketing appeal.',
            'stabilization': 'Remove camera shake and smooth out handheld footage for professional appearance.',
            'audio_enhancement': 'Noise reduction, audio leveling, and background music addition for professional sound quality.',
            'motion_graphics': 'Add animated titles, lower thirds, call-to-action overlays, and brand elements.',
            'transitions': 'Professional transitions between scenes, fade effects, and seamless cuts for polished look.',
            'social_optimization': 'Format for different platforms (Instagram, TikTok, YouTube) with proper aspect ratios.',
            'captions_subtitles': 'Auto-generated captions with styling, perfect for silent viewing on social media.',
            'highlight_reel': 'Create short highlight clips optimized for social media platforms (15-30 seconds).'
        }
        return descriptions.get(step_id, 'Process this step to enhance your video.')
    
    def _get_step_placeholder(self, step_id: str) -> str:
        """Get placeholder text for step options."""
        placeholders = {
            'color_grading': 'e.g., "Make it warmer and more cinematic" or "Increase contrast and saturation"',
            'stabilization': 'e.g., "Focus on reducing shake in the middle section" or leave blank for auto',
            'audio_enhancement': 'e.g., "Add subtle background music" or "Reduce wind noise"',
            'motion_graphics': 'e.g., "Add title: My Amazing Video" or "Include call-to-action at the end"',
            'transitions': 'e.g., "Use fade transitions" or leave blank for default smooth transitions',
            'social_optimization': 'e.g., "Optimize for Instagram Stories (9:16)" or "Keep current aspect ratio"',
            'captions_subtitles': 'e.g., "Use white text with black background" or leave blank for auto',
            'highlight_reel': 'e.g., "30 seconds, focus on action scenes" or "15 seconds, best moments only"'
        }
        return placeholders.get(step_id, 'Enter any specific instructions for this step...')
    
    def _update_video_preview(self):
        """Update the video preview."""
        # For now, show video info text
        # In a full implementation, you could show a thumbnail or video player
        try:
            video_handler = VideoHandler()
            video_info = video_handler.get_video_info(self.current_video_path)
            
            if video_info:
                duration_min = int(video_info["duration"] // 60)
                duration_sec = int(video_info["duration"] % 60)
                
                info_text = f"""
                <div style="text-align: center; color: #ffffff;">
                <h3>🎬 Current Video</h3>
                <b>{os.path.basename(self.current_video_path)}</b><br><br>
                Resolution: {video_info['width']}x{video_info['height']}<br>
                Duration: {duration_min}:{duration_sec:02d}<br>
                Size: {video_info['file_size'] / (1024*1024):.1f} MB<br><br>
                <i>Step {self.current_step_index + 1} of {len(self.processing_queue)}</i>
                </div>
                """
                self.video_preview.setText(info_text)
            else:
                self.video_preview.setText(f"🎬 Video: {os.path.basename(self.current_video_path)}")
                
        except Exception as e:
            self.video_preview.setText(f"🎬 Video: {os.path.basename(self.current_video_path)}")
            self.logger.exception(f"Error updating video preview: {e}")
    
    def _process_current_step(self):
        """Process the current step."""
        if self.current_step_index >= len(self.processing_queue):
            return
        
        current_step = self.processing_queue[self.current_step_index]
        user_instructions = self.options_text.toPlainText().strip()
        
        # Disable UI during processing
        self.process_button.setEnabled(False)
        self.skip_button.setEnabled(False)
        self.step_progress.setVisible(True)
        self.step_progress.setRange(0, 0)  # Indeterminate progress
        self.step_status.setText("Processing...")
        
        # Create a single-service dictionary for this step
        step_services = {current_step['id']: True}
        
        try:
            # Process the video with just this service
            success, output_path, message = self.video_handler.process_video_with_services(
                self.current_video_path, step_services
            )
            
            if success:
                # Update step status
                current_step['status'] = 'completed'
                current_step['output_path'] = output_path
                self.current_video_path = output_path
                
                self.step_status.setText(f"✓ Completed: {message}")
                
                # Move to next step
                self.current_step_index += 1
                self.overall_progress.setValue(self.current_step_index)
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Step Completed",
                    f"Step '{current_step['name']}' completed successfully!\n\n{message}"
                )
                
                # Update UI for next step
                self._update_ui_for_current_step()
                
            else:
                # Handle failure
                current_step['status'] = 'failed'
                self.step_status.setText(f"✗ Failed: {message}")
                
                QMessageBox.critical(
                    self,
                    "Step Failed",
                    f"Step '{current_step['name']}' failed:\n\n{message}\n\nYou can skip this step or try again."
                )
                
        except Exception as e:
            current_step['status'] = 'failed'
            self.step_status.setText(f"✗ Error: {str(e)}")
            
            QMessageBox.critical(
                self,
                "Processing Error",
                f"An error occurred while processing '{current_step['name']}':\n\n{str(e)}"
            )
        
        finally:
            # Re-enable UI
            self.process_button.setEnabled(True)
            self.skip_button.setEnabled(True)
            self.step_progress.setVisible(False)
    
    def _skip_current_step(self):
        """Skip the current step."""
        if self.current_step_index >= len(self.processing_queue):
            return
        
        current_step = self.processing_queue[self.current_step_index]
        
        # Confirm skip
        reply = QMessageBox.question(
            self,
            "Skip Step",
            f"Are you sure you want to skip '{current_step['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            current_step['status'] = 'skipped'
            self.current_step_index += 1
            self.overall_progress.setValue(self.current_step_index)
            self._update_ui_for_current_step()
    
    def _show_completion_ui(self):
        """Show the completion UI."""
        self.step_title.setText("Processing Complete!")
        self.step_description.setText("All selected video processing steps have been completed.")
        
        # Update video preview
        self._update_video_preview()
        
        # Update buttons
        self.skip_button.setVisible(False)
        self.process_button.setText("Finish & Use Video")
        self.process_button.setEnabled(True)
        self.process_button.clicked.disconnect()
        self.process_button.clicked.connect(self._finish_processing)
        
        # Hide step options
        self.step_options.setVisible(False)
        
        # Show completion message
        completed_steps = [step['name'] for step in self.processing_queue if step['status'] == 'completed']
        skipped_steps = [step['name'] for step in self.processing_queue if step['status'] == 'skipped']
        
        message = "Video processing pipeline completed!\n\n"
        if completed_steps:
            message += f"Completed steps:\n• " + "\n• ".join(completed_steps) + "\n\n"
        if skipped_steps:
            message += f"Skipped steps:\n• " + "\n• ".join(skipped_steps) + "\n\n"
        message += f"Final video: {os.path.basename(self.current_video_path)}"
        
        QMessageBox.information(self, "Processing Complete", message)
    
    def _finish_processing(self):
        """Finish processing and emit the final video path."""
        self.processing_complete.emit(self.current_video_path)
        self.accept()
    
    def get_final_video_path(self) -> str:
        """Get the final processed video path."""
        return self.current_video_path 