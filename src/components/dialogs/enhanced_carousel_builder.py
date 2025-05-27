"""
Enhanced Carousel Builder Dialog for Crow's Eye platform.
Provides advanced interface for creating multi-image posts with drag-and-drop reordering.
"""

import os
import logging
from typing import List, Dict, Any, Optional

from PySide6.QtCore import Qt, Signal, QMimeData, QPoint, QSize
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QWidget, QGridLayout, QTextEdit, QLineEdit,
    QGroupBox, QMessageBox, QFrame, QSplitter, QSpinBox,
    QFormLayout, QCheckBox, QComboBox
)
from PySide6.QtGui import QPixmap, QDrag, QPainter, QFont, QDragEnterEvent, QDropEvent

from PIL import Image as PILImage

from ..base_dialog import BaseDialog
from ...handlers.crowseye_handler import CrowsEyeHandler


class DraggableImageWidget(QLabel):
    """Widget for displaying draggable images in the carousel builder."""
    
    image_moved = Signal(int, int)  # from_index, to_index
    image_removed = Signal(int)  # index
    
    def __init__(self, image_path: str, index: int, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.index = index
        self.setFixedSize(150, 150)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #444;
                border-radius: 8px;
                background-color: #2a2a2a;
            }
            QLabel:hover {
                border-color: #3b82f6;
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAcceptDrops(True)
        self._load_image()
    
    def _load_image(self):
        """Load and display the image."""
        try:
            if os.path.exists(self.image_path):
                with PILImage.open(self.image_path) as img:
                    if img.mode not in ('RGB', 'L'):
                        img = img.convert('RGB')
                    
                    # Resize to fit widget
                    img_resized = img.resize((140, 140), PILImage.Resampling.LANCZOS)
                    
                    # Convert to QPixmap
                    rgb_image = img_resized.convert('RGB')
                    width, height = rgb_image.size
                    rgb_data = rgb_image.tobytes("raw", "RGB")
                    
                    from PySide6.QtGui import QImage
                    qimg = QImage(rgb_data, width, height, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimg)
                    
                    self.setPixmap(pixmap)
            else:
                self.setText("Image\nNot Found")
        except Exception as e:
            logging.error(f"Error loading image {self.image_path}: {e}")
            self.setText("Error\nLoading\nImage")
    
    def mousePressEvent(self, event):
        """Handle mouse press for drag start."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
        elif event.button() == Qt.MouseButton.RightButton:
            # Right click to remove
            self.image_removed.emit(self.index)
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        
        if ((event.position().toPoint() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
        
        # Start drag
        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setText(str(self.index))
        drag.setMimeData(mimeData)
        
        # Create drag pixmap
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(self.drag_start_position)
        
        # Execute drag
        dropAction = drag.exec(Qt.DropAction.MoveAction)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop."""
        try:
            from_index = int(event.mimeData().text())
            to_index = self.index
            if from_index != to_index:
                self.image_moved.emit(from_index, to_index)
            event.acceptProposedAction()
        except ValueError:
            event.ignore()


class CarouselPreviewWidget(QWidget):
    """Widget for previewing the carousel as it would appear on social media."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_paths = []
        self.current_index = 0
        self.setFixedSize(400, 400)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border: 2px solid #444;
                border-radius: 8px;
            }
        """)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the preview UI."""
        layout = QVBoxLayout(self)
        
        # Preview area
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(380, 300)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.preview_label)
        
        # Navigation
        nav_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("◀")
        self.prev_button.setFixedSize(40, 30)
        self.prev_button.clicked.connect(self._prev_image)
        nav_layout.addWidget(self.prev_button)
        
        self.position_label = QLabel("0 / 0")
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position_label.setStyleSheet("color: #FFFFFF; font-weight: bold;")
        nav_layout.addWidget(self.position_label)
        
        self.next_button = QPushButton("▶")
        self.next_button.setFixedSize(40, 30)
        self.next_button.clicked.connect(self._next_image)
        nav_layout.addWidget(self.next_button)
        
        layout.addLayout(nav_layout)
        
        # Dots indicator
        self.dots_layout = QHBoxLayout()
        self.dots_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(self.dots_layout)
    
    def update_images(self, image_paths: List[str]):
        """Update the preview with new image paths."""
        self.image_paths = image_paths
        self.current_index = 0
        self._update_display()
        self._update_dots()
    
    def _update_display(self):
        """Update the current image display."""
        if not self.image_paths:
            self.preview_label.setText("No images\nselected")
            self.position_label.setText("0 / 0")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            return
        
        # Load current image
        try:
            current_path = self.image_paths[self.current_index]
            if os.path.exists(current_path):
                with PILImage.open(current_path) as img:
                    if img.mode not in ('RGB', 'L'):
                        img = img.convert('RGB')
                    
                    # Resize to fit preview
                    img_resized = img.resize((370, 290), PILImage.Resampling.LANCZOS)
                    
                    # Convert to QPixmap
                    rgb_image = img_resized.convert('RGB')
                    width, height = rgb_image.size
                    rgb_data = rgb_image.tobytes("raw", "RGB")
                    
                    from PySide6.QtGui import QImage
                    qimg = QImage(rgb_data, width, height, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimg)
                    
                    self.preview_label.setPixmap(pixmap)
            else:
                self.preview_label.setText("Image not found")
        except Exception as e:
            logging.error(f"Error loading preview image: {e}")
            self.preview_label.setText("Error loading image")
        
        # Update position
        self.position_label.setText(f"{self.current_index + 1} / {len(self.image_paths)}")
        
        # Update navigation buttons
        self.prev_button.setEnabled(self.current_index > 0)
        self.next_button.setEnabled(self.current_index < len(self.image_paths) - 1)
    
    def _update_dots(self):
        """Update the dots indicator."""
        # Clear existing dots
        for i in reversed(range(self.dots_layout.count())):
            child = self.dots_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add new dots
        for i in range(len(self.image_paths)):
            dot = QLabel("●" if i == self.current_index else "○")
            dot.setStyleSheet(f"color: {'#3b82f6' if i == self.current_index else '#666'}; font-size: 16px;")
            self.dots_layout.addWidget(dot)
    
    def _prev_image(self):
        """Show previous image."""
        if self.current_index > 0:
            self.current_index -= 1
            self._update_display()
            self._update_dots()
    
    def _next_image(self):
        """Show next image."""
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self._update_display()
            self._update_dots()


class EnhancedCarouselBuilder(BaseDialog):
    """Enhanced dialog for building multi-image carousel posts."""
    
    def __init__(self, crowseye_handler: CrowsEyeHandler, initial_images: List[str] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enhanced Carousel Builder")
        self.setMinimumSize(1000, 700)
        self.crowseye_handler = crowseye_handler
        self.image_paths = initial_images or []
        self.image_widgets = []
        self.generated_caption = ""
        self._setup_ui()
        self._update_display()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QHBoxLayout(self)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Image selection and ordering
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Preview and settings
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
    
    def _create_left_panel(self):
        """Create the left panel with image selection and ordering."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title_label = QLabel("🎠 Carousel Builder")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Instructions
        instructions = QLabel(
            "• Drag images to reorder them\n"
            "• Right-click to remove an image\n"
            "• Use the buttons below to add more images"
        )
        instructions.setStyleSheet("color: #CCCCCC; margin-bottom: 15px;")
        layout.addWidget(instructions)
        
        # Image grid area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #444;
                border-radius: 4px;
                background-color: #1a1a1a;
            }
        """)
        
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.grid_widget)
        layout.addWidget(self.scroll_area)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.add_images_button = QPushButton("Add Images")
        self.add_images_button.setStyleSheet("""
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
        self.add_images_button.clicked.connect(self._add_images)
        button_layout.addWidget(self.add_images_button)
        
        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        self.clear_all_button.clicked.connect(self._clear_all)
        button_layout.addWidget(self.clear_all_button)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return panel
    
    def _create_right_panel(self):
        """Create the right panel with preview and settings."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Preview section
        preview_group = QGroupBox("Carousel Preview")
        preview_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_widget = CarouselPreviewWidget()
        preview_layout.addWidget(self.preview_widget)
        
        layout.addWidget(preview_group)
        
        # Settings section
        settings_group = QGroupBox("Carousel Settings")
        settings_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        settings_layout = QFormLayout(settings_group)
        
        # Max images setting
        self.max_images_spinbox = QSpinBox()
        self.max_images_spinbox.setRange(2, 10)
        self.max_images_spinbox.setValue(10)
        self.max_images_spinbox.setStyleSheet("color: #FFFFFF; background-color: #2a2a2a; border: 1px solid #444; padding: 5px;")
        settings_layout.addRow("Max Images:", self.max_images_spinbox)
        
        # Auto-optimize checkbox
        self.auto_optimize_checkbox = QCheckBox("Auto-optimize image sizes")
        self.auto_optimize_checkbox.setChecked(True)
        self.auto_optimize_checkbox.setStyleSheet("color: #FFFFFF;")
        settings_layout.addRow("", self.auto_optimize_checkbox)
        
        layout.addWidget(settings_group)
        
        # Caption section
        caption_group = QGroupBox("Caption Generation")
        caption_group.setStyleSheet("QGroupBox { font-weight: bold; color: #FFFFFF; }")
        caption_layout = QVBoxLayout(caption_group)
        
        # Caption style
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Style:"))
        
        self.caption_style_combo = QComboBox()
        self.caption_style_combo.addItems([
            "Professional", "Casual", "Funny", "Inspirational", 
            "Excited", "Informative", "Creative"
        ])
        self.caption_style_combo.setStyleSheet("color: #FFFFFF; background-color: #2a2a2a; border: 1px solid #444; padding: 5px;")
        style_layout.addWidget(self.caption_style_combo)
        
        self.generate_caption_button = QPushButton("Generate")
        self.generate_caption_button.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.generate_caption_button.clicked.connect(self._generate_caption)
        style_layout.addWidget(self.generate_caption_button)
        
        caption_layout.addLayout(style_layout)
        
        # Caption text area
        self.caption_text = QTextEdit()
        self.caption_text.setMaximumHeight(100)
        self.caption_text.setPlaceholderText("Generated caption will appear here...")
        self.caption_text.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                color: #FFFFFF;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        caption_layout.addWidget(self.caption_text)
        
        layout.addWidget(caption_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.save_carousel_button = QPushButton("Save Carousel")
        self.save_carousel_button.setStyleSheet("""
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
        self.save_carousel_button.clicked.connect(self._save_carousel)
        self.save_carousel_button.setEnabled(False)
        action_layout.addWidget(self.save_carousel_button)
        
        self.cancel_button = QPushButton("Cancel")
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
        self.cancel_button.clicked.connect(self.reject)
        action_layout.addWidget(self.cancel_button)
        
        layout.addLayout(action_layout)
        
        return panel
    
    def _update_display(self):
        """Update the image grid display."""
        # Clear existing widgets
        for widget in self.image_widgets:
            widget.setParent(None)
        self.image_widgets.clear()
        
        # Add image widgets
        for i, image_path in enumerate(self.image_paths):
            widget = DraggableImageWidget(image_path, i)
            widget.image_moved.connect(self._move_image)
            widget.image_removed.connect(self._remove_image)
            
            row = i // 3
            col = i % 3
            self.grid_layout.addWidget(widget, row, col)
            self.image_widgets.append(widget)
        
        # Update preview
        self.preview_widget.update_images(self.image_paths)
        
        # Update save button state
        self.save_carousel_button.setEnabled(len(self.image_paths) >= 2)
        
        # Update indices for all widgets
        for i, widget in enumerate(self.image_widgets):
            widget.index = i
    
    def _add_images(self):
        """Add images to the carousel."""
        try:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Images for Carousel",
                "",
                "Image Files (*.jpg *.jpeg *.png *.gif *.bmp *.webp);;All Files (*)"
            )
            
            if file_paths:
                max_images = self.max_images_spinbox.value()
                available_slots = max_images - len(self.image_paths)
                
                if available_slots <= 0:
                    QMessageBox.warning(
                        self, 
                        "Maximum Images Reached", 
                        f"You can only have {max_images} images in a carousel."
                    )
                    return
                
                # Add images up to the limit
                new_images = file_paths[:available_slots]
                self.image_paths.extend(new_images)
                
                if len(file_paths) > available_slots:
                    QMessageBox.information(
                        self,
                        "Images Limited",
                        f"Only {available_slots} images were added due to the {max_images} image limit."
                    )
                
                self._update_display()
                
        except Exception as e:
            logging.error(f"Error adding images: {e}")
            QMessageBox.critical(self, "Error", f"Could not add images: {str(e)}")
    
    def _clear_all(self):
        """Clear all images from the carousel."""
        if self.image_paths:
            reply = QMessageBox.question(
                self,
                "Clear All Images",
                "Are you sure you want to remove all images from the carousel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.image_paths.clear()
                self._update_display()
    
    def _move_image(self, from_index: int, to_index: int):
        """Move an image from one position to another."""
        try:
            if 0 <= from_index < len(self.image_paths) and 0 <= to_index < len(self.image_paths):
                # Move the image
                image_path = self.image_paths.pop(from_index)
                self.image_paths.insert(to_index, image_path)
                self._update_display()
        except Exception as e:
            logging.error(f"Error moving image: {e}")
    
    def _remove_image(self, index: int):
        """Remove an image from the carousel."""
        try:
            if 0 <= index < len(self.image_paths):
                filename = os.path.basename(self.image_paths[index])
                reply = QMessageBox.question(
                    self,
                    "Remove Image",
                    f"Remove '{filename}' from the carousel?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.image_paths.pop(index)
                    self._update_display()
        except Exception as e:
            logging.error(f"Error removing image: {e}")
    
    def _generate_caption(self):
        """Generate a caption for the carousel."""
        try:
            if not self.image_paths:
                QMessageBox.warning(self, "No Images", "Please add images to the carousel first.")
                return
            
            style = self.caption_style_combo.currentText().lower()
            caption = self.crowseye_handler.generate_caption(self.image_paths, style)
            
            if caption:
                self.caption_text.setPlainText(caption)
                self.generated_caption = caption
            else:
                QMessageBox.warning(self, "Caption Generation", "Failed to generate caption. Please try again.")
                
        except Exception as e:
            logging.error(f"Error generating caption: {e}")
            QMessageBox.critical(self, "Error", f"Could not generate caption: {str(e)}")
    
    def _save_carousel(self):
        """Save the carousel as a gallery."""
        try:
            if len(self.image_paths) < 2:
                QMessageBox.warning(self, "Insufficient Images", "A carousel needs at least 2 images.")
                return
            
            # Get carousel name
            from PySide6.QtWidgets import QInputDialog
            name, ok = QInputDialog.getText(
                self, 
                "Save Carousel", 
                "Enter a name for this carousel:",
                text=f"Carousel_{len(self.image_paths)}_images"
            )
            
            if not ok or not name.strip():
                return
            
            # Get caption
            caption = self.caption_text.toPlainText().strip()
            if not caption:
                caption = f"Carousel with {len(self.image_paths)} images"
            
            # Save using CrowsEye handler
            success = self.crowseye_handler.save_gallery(name.strip(), self.image_paths, caption)
            
            if success:
                QMessageBox.information(
                    self,
                    "Carousel Saved",
                    f"Carousel '{name}' has been saved successfully!"
                )
                self.accept()
            else:
                QMessageBox.critical(self, "Save Error", "Failed to save carousel.")
                
        except Exception as e:
            logging.error(f"Error saving carousel: {e}")
            QMessageBox.critical(self, "Error", f"Could not save carousel: {str(e)}")
    
    def get_carousel_data(self) -> Dict[str, Any]:
        """Get the carousel data."""
        return {
            "image_paths": self.image_paths.copy(),
            "caption": self.caption_text.toPlainText().strip(),
            "auto_optimize": self.auto_optimize_checkbox.isChecked()
        } 