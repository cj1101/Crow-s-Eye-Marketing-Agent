"""
Reel Thumbnail Selector Dialog for Crow's Eye platform.
Generates multiple thumbnail options from videos and allows custom uploads.
"""

import os
import logging
from typing import List, Optional

from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGridLayout, QProgressBar, QFileDialog, QGroupBox, 
    QMessageBox, QScrollArea, QWidget, QFrame, QSpinBox, QFormLayout
)

from ..base_dialog import BaseDialog
from ...handlers.video_handler import VideoHandler


class ThumbnailGeneratorWorker(QThread):
    """Worker thread for generating video thumbnails."""
    
    progress = Signal(str)
    finished = Signal(bool, list, str)  # success, thumbnail_paths, message
    
    def __init__(self, video_path: str, num_thumbnails: int):
        super().__init__()
        self.video_path = video_path
        self.num_thumbnails = num_thumbnails
        self.video_handler = VideoHandler()
    
    def run(self):
        """Run the thumbnail generation."""
        try:
            self.progress.emit("Generating thumbnails...")
            success, thumbnail_paths, message = self.video_handler.generate_video_thumbnails(
                self.video_path, self.num_thumbnails
            )
            self.finished.emit(success, thumbnail_paths, message)
        except Exception as e:
            self.finished.emit(False, [], f"Error: {str(e)}")


class ThumbnailWidget(QFrame):
    """Widget for displaying a selectable thumbnail."""
    
    def __init__(self, image_path: str, index: int, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.index = index
        self.is_selected = False
        self.setFixedSize(160, 120)
        self.setFrameStyle(QFrame.Box)
        self._setup_ui()
        self._update_style()
    
    def _setup_ui(self):
        """Set up the thumbnail UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Thumbnail image
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(150, 100)
        
        # Load and display thumbnail
        try:
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(150, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("No Preview")
        except Exception as e:
            self.image_label.setText("Error")
        
        layout.addWidget(self.image_label)
        
        # Index label
        index_label = QLabel(f"Option {self.index + 1}")
        index_label.setAlignment(Qt.AlignCenter)
        index_label.setStyleSheet("color: #CCCCCC; font-size: 11px; font-weight: bold;")
        layout.addWidget(index_label)
    
    def _update_style(self):
        """Update the widget style based on selection state."""
        if self.is_selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #3b82f6;
                    border: 3px solid #1d4ed8;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #2a2a2a;
                    border: 2px solid #444;
                    border-radius: 8px;
                }
                QFrame:hover {
                    border: 2px solid #666;
                    background-color: #333;
                }
            """)
    
    def set_selected(self, selected: bool):
        """Set the selection state."""
        self.is_selected = selected
        self._update_style()
    
    def mousePressEvent(self, event):
        """Handle mouse press for selection."""
        if event.button() == Qt.LeftButton:
            # Notify parent dialog of selection
            if hasattr(self.parent(), 'parent') and hasattr(self.parent().parent(), '_on_thumbnail_selected'):
                self.parent().parent()._on_thumbnail_selected(self.index)
        super().mousePressEvent(event)


class ThumbnailSelectorDialog(BaseDialog):
    """Dialog for selecting video thumbnails."""
    
    def __init__(self, video_path: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reel Thumbnail Selector")
        self.setFixedSize(700, 600)
        self.video_path = video_path
        self.worker = None
        self.thumbnail_paths = []
        self.thumbnail_widgets = []
        self.selected_thumbnail_index = -1
        self.custom_thumbnail_path = ""
        self._setup_ui()
        
        # If video path provided, start generation immediately
        if self.video_path:
            self._update_video_info()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Reel Thumbnail Selector")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "Select a thumbnail for your reel from auto-generated options or upload a custom image. "
            "The thumbnail will be used as the cover image when your reel is displayed."
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
        settings_group = QGroupBox("Thumbnail Generation Settings")
        settings_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        settings_layout = QFormLayout(settings_group)
        
        # Number of thumbnails
        self.num_thumbnails_spinbox = QSpinBox()
        self.num_thumbnails_spinbox.setRange(3, 12)
        self.num_thumbnails_spinbox.setValue(6)
        self.num_thumbnails_spinbox.setStyleSheet("color: #FFFFFF; background-color: #2a2a2a; border: 1px solid #444; padding: 5px;")
        settings_layout.addRow("Number of Options:", self.num_thumbnails_spinbox)
        
        # Generate button
        self.generate_button = QPushButton("Generate Thumbnails")
        self.generate_button.clicked.connect(self._generate_thumbnails)
        self.generate_button.setEnabled(bool(self.video_path))
        self.generate_button.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #374151;
                color: #6b7280;
            }
        """)
        settings_layout.addRow("", self.generate_button)
        
        layout.addWidget(settings_group)
        
        # Thumbnails group
        self.thumbnails_group = QGroupBox("Generated Thumbnails")
        self.thumbnails_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        self.thumbnails_group.setVisible(False)
        thumbnails_layout = QVBoxLayout(self.thumbnails_group)
        
        # Scroll area for thumbnails
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        scroll_area.setStyleSheet("QScrollArea { border: 1px solid #444; border-radius: 4px; }")
        
        self.thumbnails_widget = QWidget()
        self.thumbnails_grid = QGridLayout(self.thumbnails_widget)
        self.thumbnails_grid.setSpacing(10)
        
        scroll_area.setWidget(self.thumbnails_widget)
        thumbnails_layout.addWidget(scroll_area)
        
        layout.addWidget(self.thumbnails_group)
        
        # Custom thumbnail group
        custom_group = QGroupBox("Custom Thumbnail (Optional)")
        custom_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        custom_layout = QHBoxLayout(custom_group)
        
        self.custom_path_label = QLabel("No custom thumbnail selected")
        self.custom_path_label.setStyleSheet("color: #CCCCCC; padding: 5px; border: 1px solid #444; border-radius: 4px;")
        custom_layout.addWidget(self.custom_path_label)
        
        self.browse_custom_button = QPushButton("Browse Image...")
        self.browse_custom_button.clicked.connect(self._browse_custom_thumbnail)
        self.browse_custom_button.setStyleSheet("""
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
        custom_layout.addWidget(self.browse_custom_button)
        
        layout.addWidget(custom_group)
        
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
        
        self.select_button = QPushButton("Use Selected Thumbnail")
        self.select_button.clicked.connect(self._use_selected_thumbnail)
        self.select_button.setEnabled(False)
        self.select_button.setStyleSheet("""
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
        button_layout.addWidget(self.select_button)
        
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
        
        self.generate_button.setEnabled(True)
        
        # Get video info
        video_handler = VideoHandler()
        info = video_handler.get_video_info(self.video_path)
        if "error" not in info:
            duration_min = int(info["duration"] // 60)
            duration_sec = int(info["duration"] % 60)
            self.status_label.setText(
                f"Video: {info['width']}x{info['height']}, Duration: {duration_min}:{duration_sec:02d}"
            )
    
    def _browse_custom_thumbnail(self):
        """Browse for a custom thumbnail image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Thumbnail Image",
            "",
            "Image Files (*.jpg *.jpeg *.png *.bmp *.gif);;All Files (*)"
        )
        
        if file_path:
            self.custom_thumbnail_path = file_path
            filename = os.path.basename(file_path)
            self.custom_path_label.setText(filename)
            
            # Clear auto-generated selection and enable use button
            self._clear_thumbnail_selection()
            self.select_button.setEnabled(True)
            self.status_label.setText("Custom thumbnail selected")
    
    def _generate_thumbnails(self):
        """Generate thumbnails from the video."""
        if not self.video_path:
            QMessageBox.warning(self, "Warning", "Please select a video file first.")
            return
        
        # Disable UI during processing
        self.generate_button.setEnabled(False)
        if hasattr(self, 'browse_button'):
            self.browse_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Get settings
        num_thumbnails = self.num_thumbnails_spinbox.value()
        
        # Start worker thread
        self.worker = ThumbnailGeneratorWorker(self.video_path, num_thumbnails)
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._on_generation_finished)
        self.worker.start()
    
    def _update_progress(self, message: str):
        """Update progress message."""
        self.status_label.setText(message)
    
    def _on_generation_finished(self, success: bool, thumbnail_paths: List[str], message: str):
        """Handle thumbnail generation completion."""
        # Re-enable UI
        self.generate_button.setEnabled(True)
        if hasattr(self, 'browse_button'):
            self.browse_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success and thumbnail_paths:
            self.thumbnail_paths = thumbnail_paths
            self.status_label.setText(f"✓ {message}")
            self._display_thumbnails()
        else:
            self.status_label.setText(f"✗ {message}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate thumbnails:\n\n{message}"
            )
        
        # Clean up worker
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
    
    def _display_thumbnails(self):
        """Display the generated thumbnails."""
        # Clear existing thumbnails
        for widget in self.thumbnail_widgets:
            widget.deleteLater()
        self.thumbnail_widgets.clear()
        
        # Add new thumbnails
        cols = 3
        for i, thumbnail_path in enumerate(self.thumbnail_paths):
            row = i // cols
            col = i % cols
            
            thumbnail_widget = ThumbnailWidget(thumbnail_path, i, self.thumbnails_widget)
            self.thumbnail_widgets.append(thumbnail_widget)
            self.thumbnails_grid.addWidget(thumbnail_widget, row, col)
        
        # Show thumbnails group
        self.thumbnails_group.setVisible(True)
        self.adjustSize()
    
    def _on_thumbnail_selected(self, index: int):
        """Handle thumbnail selection."""
        # Clear previous selection
        for widget in self.thumbnail_widgets:
            widget.set_selected(False)
        
        # Set new selection
        if 0 <= index < len(self.thumbnail_widgets):
            self.thumbnail_widgets[index].set_selected(True)
            self.selected_thumbnail_index = index
            self.custom_thumbnail_path = ""  # Clear custom selection
            self.custom_path_label.setText("No custom thumbnail selected")
            self.select_button.setEnabled(True)
            self.status_label.setText(f"Thumbnail option {index + 1} selected")
    
    def _clear_thumbnail_selection(self):
        """Clear all thumbnail selections."""
        for widget in self.thumbnail_widgets:
            widget.set_selected(False)
        self.selected_thumbnail_index = -1
    
    def _use_selected_thumbnail(self):
        """Use the selected thumbnail."""
        if self.custom_thumbnail_path:
            # Custom thumbnail selected
            QMessageBox.information(
                self,
                "Thumbnail Selected",
                f"Custom thumbnail will be used:\n{os.path.basename(self.custom_thumbnail_path)}"
            )
            self.accept()
        elif self.selected_thumbnail_index >= 0:
            # Auto-generated thumbnail selected
            selected_path = self.thumbnail_paths[self.selected_thumbnail_index]
            QMessageBox.information(
                self,
                "Thumbnail Selected",
                f"Thumbnail option {self.selected_thumbnail_index + 1} will be used:\n{os.path.basename(selected_path)}"
            )
            self.accept()
        else:
            QMessageBox.warning(self, "Warning", "Please select a thumbnail first.")
    
    def get_selected_thumbnail(self) -> Optional[str]:
        """Get the path of the selected thumbnail."""
        if self.custom_thumbnail_path:
            return self.custom_thumbnail_path
        elif self.selected_thumbnail_index >= 0 and self.selected_thumbnail_index < len(self.thumbnail_paths):
            return self.thumbnail_paths[self.selected_thumbnail_index]
        return None
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Cancel Generation",
                "Thumbnail generation is in progress. Are you sure you want to cancel?",
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