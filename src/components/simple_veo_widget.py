"""
Enhanced Veo widget for high-quality video generation
"""
import logging
import os
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QProgressBar, QMessageBox,
    QComboBox, QSpinBox, QCheckBox, QGroupBox, QFormLayout
)

from ..api.ai.veo_handler import VeoHandler
from ..models.app_state import AppState


class VeoWorker(QThread):
    """Worker thread for video generation."""
    
    progress = Signal(str)  # Progress message
    finished = Signal(bool, str, str)  # success, result, message
    
    def __init__(self, prompt: str, duration: int = 10, aspect_ratio: str = "16:9", allow_person_generation: bool = False):
        super().__init__()
        self.prompt = prompt
        self.duration = duration
        self.aspect_ratio = aspect_ratio
        self.allow_person_generation = allow_person_generation
        app_state = AppState()
        self.handler = VeoHandler(app_state)
    
    def run(self):
        """Run video generation in background."""
        try:
            def progress_callback(message):
                self.progress.emit(message)
            
            success, result, message = self.handler.generate_video_with_progress_callback(
                self.prompt,
                duration=self.duration,
                aspect_ratio=self.aspect_ratio,
                allow_person_generation=self.allow_person_generation,
                progress_callback=progress_callback
            )
            self.finished.emit(success, result, message)
        except Exception as e:
            self.finished.emit(False, "", f"Error: {str(e)}")


class SimpleVeoWidget(QWidget):
    """Enhanced Veo video generation widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.worker = None
        self.app_state = AppState()
        self._setup_ui()
        self._check_veo_status()
    
    def _setup_ui(self):
        """Set up the simple UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🎬 Veo Video Generator")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Status label
        self.status_label = QLabel("Checking Veo status...")
        self.status_label.setStyleSheet("color: #CCCCCC; margin-bottom: 10px;")
        layout.addWidget(self.status_label)
        
        # Prompt input
        prompt_label = QLabel("Video Description:")
        prompt_label.setStyleSheet("color: #FFFFFF; margin-bottom: 5px;")
        layout.addWidget(prompt_label)
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setMaximumHeight(80)
        self.prompt_input.setPlaceholderText("Describe the video you want to generate...")
        self.prompt_input.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                color: #FFFFFF;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.prompt_input)
        
        # Quality presets
        presets_group = QGroupBox("Quality Presets")
        presets_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        presets_layout = QVBoxLayout(presets_group)
        
        self.preset_combo = QComboBox()
        self.preset_combo.setStyleSheet("""
            QComboBox {
                background-color: #2a2a2a;
                color: #FFFFFF;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """)
        
        # Load quality presets
        try:
            app_state = AppState()
            handler = VeoHandler(app_state)
            presets = handler.get_quality_presets()
            for preset_name, preset_data in presets.items():
                display_name = f"{preset_name.replace('_', ' ').title()} - {preset_data['description']}"
                self.preset_combo.addItem(display_name, preset_data)
        except:
            # Fallback presets if handler fails
            self.preset_combo.addItem("Social Media Story - 9:16, 15s", {"aspect_ratio": "9:16", "duration": 15})
            self.preset_combo.addItem("YouTube Short - 9:16, 30s", {"aspect_ratio": "9:16", "duration": 30})
            self.preset_combo.addItem("Landscape Video - 16:9, 30s", {"aspect_ratio": "16:9", "duration": 30})
        
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        presets_layout.addWidget(self.preset_combo)
        layout.addWidget(presets_group)
        
        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        advanced_layout = QFormLayout(advanced_group)
        
        # Duration
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(5, 60)
        self.duration_spin.setValue(10)
        self.duration_spin.setSuffix(" seconds")
        self.duration_spin.setStyleSheet("""
            QSpinBox {
                background-color: #2a2a2a;
                color: #FFFFFF;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        advanced_layout.addRow("Duration:", self.duration_spin)
        
        # Aspect ratio
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems(["16:9 (Landscape)", "9:16 (Portrait)", "1:1 (Square)"])
        self.aspect_combo.setStyleSheet("""
            QComboBox {
                background-color: #2a2a2a;
                color: #FFFFFF;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        advanced_layout.addRow("Aspect Ratio:", self.aspect_combo)
        
        # Allow person generation
        self.allow_person_check = QCheckBox("Allow person generation")
        self.allow_person_check.setStyleSheet("color: #FFFFFF;")
        advanced_layout.addRow("", self.allow_person_check)
        
        layout.addWidget(advanced_group)
        
        # Example prompts
        examples_layout = QHBoxLayout()
        examples = [
            "A cat playing in a garden",
            "Peaceful ocean waves",
            "Coffee being poured"
        ]
        
        for example in examples:
            btn = QPushButton(f"'{example[:15]}...'")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
            """)
            btn.clicked.connect(lambda checked, text=example: self.prompt_input.setPlainText(text))
            examples_layout.addWidget(btn)
        
        layout.addLayout(examples_layout)
        
        # Generate button
        self.generate_btn = QPushButton("🎥 Generate Video")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
                margin: 10px 0;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #6b7280;
            }
        """)
        self.generate_btn.clicked.connect(self._generate_video)
        layout.addWidget(self.generate_btn)
        
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
        
        # Progress label
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #CCCCCC; margin-top: 5px;")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        layout.addStretch()
    
    def _check_veo_status(self):
        """Check if Veo is ready to use."""
        try:
            app_state = AppState()
            handler = VeoHandler(app_state)
            status = handler.get_status()
            
            if status["ready"]:
                self.status_label.setText("✅ Veo is ready!")
                self.status_label.setStyleSheet("color: #10b981; margin-bottom: 10px;")
                self.generate_btn.setEnabled(True)
            else:
                issues = []
                if not status["has_api_key"]:
                    issues.append("Missing GOOGLE_API_KEY")
                if not status["client_initialized"]:
                    issues.append("Client not initialized")
                
                self.status_label.setText(f"❌ Veo not ready: {', '.join(issues)}")
                self.status_label.setStyleSheet("color: #ef4444; margin-bottom: 10px;")
                self.generate_btn.setEnabled(False)
                
        except Exception as e:
            self.status_label.setText(f"❌ Error checking Veo: {str(e)}")
            self.status_label.setStyleSheet("color: #ef4444; margin-bottom: 10px;")
            self.generate_btn.setEnabled(False)
    
    def _on_preset_changed(self):
        """Handle preset selection change."""
        try:
            preset_data = self.preset_combo.currentData()
            if preset_data:
                # Update duration
                self.duration_spin.setValue(preset_data.get("duration", 10))
                
                # Update aspect ratio
                aspect_ratio = preset_data.get("aspect_ratio", "16:9")
                if aspect_ratio == "16:9":
                    self.aspect_combo.setCurrentIndex(0)
                elif aspect_ratio == "9:16":
                    self.aspect_combo.setCurrentIndex(1)
                elif aspect_ratio == "1:1":
                    self.aspect_combo.setCurrentIndex(2)
        except Exception as e:
            self.logger.error(f"Error applying preset: {e}")
    
    def _generate_video(self):
        """Start video generation."""
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Warning", "Please enter a video description")
            return
        
        # Get settings
        duration = self.duration_spin.value()
        aspect_ratio_text = self.aspect_combo.currentText()
        aspect_ratio = aspect_ratio_text.split(" ")[0]  # Extract "16:9" from "16:9 (Landscape)"
        allow_person_generation = self.allow_person_check.isChecked()
        
        # Start generation
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_label.setVisible(True)
        self.progress_label.setText("Starting video generation...")
        
        # Start worker thread
        self.worker = VeoWorker(prompt, duration, aspect_ratio, allow_person_generation)
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._generation_finished)
        self.worker.start()
    
    def _update_progress(self, message: str):
        """Update progress display."""
        self.progress_label.setText(message)
    
    def _generation_finished(self, success: bool, result: str, message: str):
        """Handle generation completion."""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.generate_btn.setEnabled(True)
        
        if success:
            # Update app state with the generated video
            if hasattr(self, 'app_state') and result:
                self.app_state.selected_media = result
            
            # Show success message with option to load in main app
            reply = QMessageBox.question(
                self,
                "🎉 Video Generated Successfully!",
                f"Your high-quality video has been generated!\n\n"
                f"📁 Saved to: {os.path.basename(result)}\n"
                f"📊 {message}\n\n"
                f"Would you like to load this video in the main application for post creation?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Try to load the video in the main application
                try:
                    # Find the main window and load the media
                    main_window = self.window()
                    while main_window.parent():
                        main_window = main_window.parent()
                    
                    if hasattr(main_window, '_on_media_selected'):
                        main_window._on_media_selected(result)
                        # Close the dialog
                        if hasattr(self.parent(), 'accept'):
                            self.parent().accept()
                except Exception as e:
                    self.logger.error(f"Error loading video in main app: {e}")
        else:
            QMessageBox.critical(
                self, 
                "❌ Generation Failed", 
                f"Failed to generate video:\n\n{message}\n\n"
                f"Please check your API key and try again."
            )
        
        # Clean up worker
        if self.worker:
            self.worker.deleteLater()
            self.worker = None 