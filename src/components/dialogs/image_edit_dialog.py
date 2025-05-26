"""
Dialog for editing images with Gemini.
"""
import os
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QComboBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont

class ImageEditDialog(QDialog):
    """Dialog for editing images with Gemini."""
    
    # Signals
    edit_confirmed = Signal(str, str)  # image_path, instructions
    
    def __init__(self, image_path: str, parent=None):
        """
        Initialize the image edit dialog.
        
        Args:
            image_path: Path to the image to edit
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set up logger
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Store image path
        self.image_path = image_path
        
        # Set up dialog properties
        self.setWindowTitle("Edit Image with Gemini")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        # Set up UI
        self._setup_ui()
        
        # Populate presets
        self._populate_presets()
        
    def _setup_ui(self):
        """Set up the dialog UI components."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header section with image preview
        header_layout = QHBoxLayout()
        
        # Image preview
        preview_frame = QFrame()
        preview_frame.setFrameShape(QFrame.Shape.StyledPanel)
        preview_frame.setMinimumSize(300, 300)
        preview_frame.setMaximumWidth(400)
        
        preview_layout = QVBoxLayout(preview_frame)
        
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet("background-color: #f0f0f0;")
        self.image_preview.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )
        
        # Load and display the image
        if os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    300, 300,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_preview.setPixmap(scaled_pixmap)
            else:
                self.image_preview.setText("Error loading image")
        else:
            self.image_preview.setText("Image not found")
            
        preview_layout.addWidget(self.image_preview)
        
        # Image info
        if os.path.exists(self.image_path):
            info_text = f"File: {os.path.basename(self.image_path)}\n"
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                info_text += f"Dimensions: {pixmap.width()} × {pixmap.height()} px"
            info_label = QLabel(info_text)
            info_label.setStyleSheet("color: #555;")
            preview_layout.addWidget(info_label)
            
        header_layout.addWidget(preview_frame)
        
        # Instructions section
        instructions_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Image Editing Instructions")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        instructions_layout.addWidget(title_label)
        
        # Description
        description = QLabel(
            "Enter instructions for how you want to edit the image. "
            "Gemini can perform various edits like adjusting colors, "
            "applying filters, removing objects, changing backgrounds, etc."
        )
        description.setWordWrap(True)
        instructions_layout.addWidget(description)
        
        # Preset selector
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Preset:")
        preset_layout.addWidget(preset_label)
        
        self.preset_combo = QComboBox()
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        preset_layout.addWidget(self.preset_combo)
        
        instructions_layout.addLayout(preset_layout)
        
        # Text edit for instructions
        self.instructions_edit = QTextEdit()
        self.instructions_edit.setPlaceholderText(
            "Type your editing instructions here...\n\n"
            "Examples:\n"
            "- Convert this image to black and white\n"
            "- Increase brightness and contrast\n"
            "- Add a vintage filter\n"
            "- Enhance colors and sharpen details\n"
            "- Remove the background and replace with a blue gradient\n"
            "- Add a subtle vignette effect"
        )
        self.instructions_edit.setMinimumHeight(200)
        instructions_layout.addWidget(self.instructions_edit)
        
        # Tips
        tips_label = QLabel(
            "<b>Tips:</b><br>"
            "• Be specific about what changes you want<br>"
            "• Mention areas of the image you want to focus on<br>"
            "• Describe the style or mood you're aiming for<br>"
            "• For best results, keep instructions clear and concise"
        )
        tips_label.setStyleSheet("color: #555; background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        instructions_layout.addWidget(tips_label)
        
        header_layout.addLayout(instructions_layout)
        layout.addLayout(header_layout)
        
        # Button section
        button_layout = QHBoxLayout()
        
        # Spacer to push buttons to the right
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # Apply button
        self.apply_btn = QPushButton("Apply Edit")
        self.apply_btn.setStyleSheet("""
            background-color: #2ecc71;
            color: white;
            font-weight: bold;
            padding: 8px 16px;
            border-radius: 4px;
        """)
        self.apply_btn.clicked.connect(self._on_apply)
        button_layout.addWidget(self.apply_btn)
        
        layout.addLayout(button_layout)
        
    def _populate_presets(self):
        """Populate the presets combo box with common editing presets."""
        presets = [
            "-- Select Preset --",
            "Studio Ghibli Style",
            "Oil Painting",
            "Watercolor",
            "Pencil Sketch",
            "Comic Book/Pop Art",
            "Cyberpunk/Neon",
            "Fantasy/Magical",
            "Black and White",
            "Vintage/Retro",
            "High Contrast",
            "Warm Tones",
            "Cool Tones",
            "HDR Effect",
            "Cinematic Look",
            "Soft Portrait",
            "Vibrant Colors",
            "Dreamy/Ethereal",
            "Sharpen Details",
            "Instagram Filter",
            "Polaroid Effect",
            "Tilt-Shift",
            "Remove Background",
            "Product Photography",
            "Food Photography Enhancement"
        ]
        
        self.preset_combo.addItems(presets)
        
    def _on_preset_selected(self, index):
        """
        Handle preset selection.
        
        Args:
            index: Selected preset index
        """
        if index <= 0:
            # Default option, do nothing
            return
            
        preset_text = self.preset_combo.currentText()
        instructions = ""
        
        # New artistic presets
        if preset_text == "Studio Ghibli Style":
            instructions = "Transform this image into Studio Ghibli anime style with enhanced colors, soft aesthetic, and warm tones."
            
        elif preset_text == "Oil Painting":
            instructions = "Apply an oil painting artistic effect with painterly textures and enhanced colors."
            
        elif preset_text == "Watercolor":
            instructions = "Transform this image into a watercolor painting with soft edges and flowing colors."
            
        elif preset_text == "Pencil Sketch":
            instructions = "Convert this image to a pencil sketch drawing with detailed line work."
            
        elif preset_text == "Comic Book/Pop Art":
            instructions = "Apply a comic book or pop art style with high contrast, bold colors, and sharp edges."
            
        elif preset_text == "Cyberpunk/Neon":
            instructions = "Transform this image with a cyberpunk aesthetic featuring neon colors and futuristic tones."
            
        elif preset_text == "Fantasy/Magical":
            instructions = "Apply a magical fantasy effect with enhanced saturation and ethereal lighting."
            
        elif preset_text == "Instagram Filter":
            instructions = "Apply a trendy Instagram-style filter with enhanced colors and social media appeal."
            
        elif preset_text == "Polaroid Effect":
            instructions = "Create a vintage Polaroid instant photo effect with characteristic color tones."
            
        elif preset_text == "Tilt-Shift":
            instructions = "Apply a tilt-shift effect to create a miniature-like appearance with selective focus."
            
        elif preset_text == "Remove Background":
            instructions = "Remove the background from this image, creating a transparent or isolated subject."
        
        # Original presets
        elif preset_text == "Black and White":
            instructions = "Convert this image to black and white with good contrast. Preserve details and create a timeless look."
            
        elif preset_text == "Vintage/Retro":
            instructions = "Apply a vintage filter with slightly faded colors, a warm tint, and subtle film grain. Create a nostalgic, retro aesthetic."
            
        elif preset_text == "High Contrast":
            instructions = "Increase the contrast significantly. Make shadows darker and highlights brighter while preserving mid-tones. Create a bold, dramatic look."
            
        elif preset_text == "Warm Tones":
            instructions = "Enhance the warm tones in the image. Add a subtle amber/golden cast and slightly increase saturation of reds and yellows."
            
        elif preset_text == "Cool Tones":
            instructions = "Enhance the cool tones in the image. Add a subtle blue cast and slightly increase saturation of blues and cyans."
            
        elif preset_text == "HDR Effect":
            instructions = "Create an HDR-like effect by enhancing local contrast, bringing out details in shadows and highlights. Make colors more vibrant but still natural-looking."
            
        elif preset_text == "Cinematic Look":
            instructions = "Give this image a cinematic look with a wider aspect ratio (letterbox), slightly desaturated colors, and a subtle teal-orange color grading."
            
        elif preset_text == "Soft Portrait":
            instructions = "Create a soft, flattering portrait effect with slightly softer focus, enhanced skin tones, and subtle glow on highlights."
            
        elif preset_text == "Vibrant Colors":
            instructions = "Make colors more vibrant and saturated. Increase color contrast while maintaining natural appearance."
            
        elif preset_text == "Dreamy/Ethereal":
            instructions = "Create a dreamy, ethereal effect with a soft glow, slightly reduced contrast, and a subtle light leak effect."
            
        elif preset_text == "Sharpen Details":
            instructions = "Enhance and sharpen all details in the image. Improve clarity and definition while maintaining natural appearance."
            
        elif preset_text == "Night Mode":
            instructions = "Create a night mode effect. Darken the image while enhancing highlights, add a bluish tint to shadows, and create a moody atmosphere."
            
        elif preset_text == "Summer Mood":
            instructions = "Create a bright, warm summer mood. Enhance blues and greens, add warmth to highlights, increase overall brightness, and create a cheerful atmosphere."
            
        elif preset_text == "Winter Mood":
            instructions = "Create a cool, crisp winter mood. Enhance blues and whites, slightly desaturate, and create a clean, frosty atmosphere."
            
        elif preset_text == "Product Photography":
            instructions = "Optimize for product photography. Make colors accurate, enhance details, adjust contrast for clear edges, and make the product stand out."
            
        elif preset_text == "Food Photography Enhancement":
            instructions = "Enhance for food photography. Make colors vibrant but natural, increase saturation slightly, enhance texture details, and make the food look appetizing."
            
        self.instructions_edit.setText(instructions)
        
    def _on_apply(self):
        """Handle apply button click."""
        # Get instructions from text edit
        instructions = self.instructions_edit.toPlainText().strip()
        
        if not instructions:
            self.instructions_edit.setFocus()
            return
            
        # Emit signal with image path and instructions
        self.edit_confirmed.emit(self.image_path, instructions)
        
        # Close dialog
        self.accept() 