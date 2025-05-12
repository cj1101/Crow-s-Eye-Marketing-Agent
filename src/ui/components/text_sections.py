"""
Text sections component for the main application window.
"""
import logging
import os
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, 
    QGroupBox, QGridLayout, QScrollArea, QSizePolicy,
    QCheckBox, QHBoxLayout, QPushButton, QFileDialog,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal

from ...config import constants as const

class TextSections(QWidget):
    """Text inputs section for the application."""
    
    # Signals for text changes and actions
    text_changed = Signal(str, str)  # section_id, text
    context_files_changed = Signal(list)  # list of file paths
    
    def __init__(self, parent=None):
        """Initialize the text sections component."""
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Text editors dictionary
        self.text_editors = {}
        
        # Keep caption checkbox
        self.keep_caption_checkbox = None
        
        # Context files list
        self.context_files = []
        self.context_list_widget = None
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the text sections UI components."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create a container widget for the scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        # Create instructions section with context files
        self._create_instructions_section(scroll_layout)
        
        # Create photo editing section
        self._create_text_section(scroll_layout, "photo_editing", "Photo Editing", 
            "Enter instructions for photo editing")
        
        # Create caption section with checkbox
        self._create_caption_section(scroll_layout)
        
        # Add stretch to push sections to the top
        scroll_layout.addStretch(1)
        
        # Set scroll content
        scroll_area.setWidget(scroll_content)
        
        # Add scroll area to main layout
        layout.addWidget(scroll_area)
        
    def _create_instructions_section(self, parent_layout):
        """Create the instructions section with context files integration."""
        # Create group box
        group_box = QGroupBox("Instructions & Context Files")
        group_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Preferred
        )
        
        # Group box layout
        group_layout = QVBoxLayout(group_box)
        
        # Text editor for instructions
        instructions_label = QLabel("Instructions:")
        group_layout.addWidget(instructions_label)
        
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Enter general instructions for your social media post")
        text_edit.setMinimumHeight(80)
        
        # Store reference to the text editor
        self.text_editors["instructions"] = text_edit
        
        # Connect text changed signal
        text_edit.textChanged.connect(
            lambda: self.text_changed.emit("instructions", text_edit.toPlainText())
        )
        
        group_layout.addWidget(text_edit)
        
        # Context files section
        context_label = QLabel("Context Files:")
        context_label.setToolTip("Add text or PDF files to provide additional context")
        group_layout.addWidget(context_label)
        
        # Context files list
        self.context_list_widget = QListWidget()
        self.context_list_widget.setAlternatingRowColors(True)
        self.context_list_widget.setMaximumHeight(100)
        group_layout.addWidget(self.context_list_widget)
        
        # Context file buttons
        context_buttons_layout = QHBoxLayout()
        
        add_context_btn = QPushButton("Add Files")
        add_context_btn.clicked.connect(self._add_context_files)
        context_buttons_layout.addWidget(add_context_btn)
        
        remove_context_btn = QPushButton("Remove Selected")
        remove_context_btn.clicked.connect(self._remove_context_file)
        context_buttons_layout.addWidget(remove_context_btn)
        
        group_layout.addLayout(context_buttons_layout)
        
        # Add group box to parent layout
        parent_layout.addWidget(group_box)
        
    def _add_context_files(self):
        """Add context files from a file dialog."""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter(f"{const.CONTEXT_FILTER};;{const.ALL_FILES_FILTER}")
        
        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            files = file_dialog.selectedFiles()
            for file_path in files:
                if os.path.exists(file_path):
                    # Check if already in list
                    if file_path not in self.context_files:
                        self.context_files.append(file_path)
                        item = QListWidgetItem(os.path.basename(file_path))
                        item.setData(Qt.ItemDataRole.UserRole, file_path)
                        self.context_list_widget.addItem(item)
            
            # Emit signal with updated files list
            self.context_files_changed.emit(self.context_files)
            
    def _remove_context_file(self):
        """Remove the selected context file."""
        selected_items = self.context_list_widget.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path in self.context_files:
                self.context_files.remove(file_path)
            
            row = self.context_list_widget.row(item)
            self.context_list_widget.takeItem(row)
        
        # Emit signal with updated files list
        self.context_files_changed.emit(self.context_files)
        
    def _create_text_section(self, parent_layout, section_id, title, placeholder):
        """
        Create a text input section.
        
        Args:
            parent_layout: Parent layout to add the section to
            section_id: Unique identifier for the section
            title: Display title for the section
            placeholder: Placeholder text for the text editor
        """
        # Create group box
        group_box = QGroupBox(title)
        group_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Preferred
        )
        
        # Group box layout
        group_layout = QVBoxLayout(group_box)
        
        # Text editor
        text_edit = QTextEdit()
        text_edit.setPlaceholderText(placeholder)
        text_edit.setMinimumHeight(80)
        
        # Store reference to the text editor
        self.text_editors[section_id] = text_edit
        
        # Connect text changed signal
        text_edit.textChanged.connect(
            lambda: self.text_changed.emit(section_id, text_edit.toPlainText())
        )
        
        # Add to layout
        group_layout.addWidget(text_edit)
        
        # Add group box to parent layout
        parent_layout.addWidget(group_box)
        
    def _create_caption_section(self, parent_layout):
        """Create the caption section with Keep Caption checkbox."""
        # Create group box
        group_box = QGroupBox("Caption")
        group_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Preferred
        )
        
        # Group box layout
        group_layout = QVBoxLayout(group_box)
        
        # Checkbox layout
        checkbox_layout = QHBoxLayout()
        
        # Keep caption checkbox
        self.keep_caption_checkbox = QCheckBox("Keep Caption")
        self.keep_caption_checkbox.setToolTip("Check to preserve existing caption when generating new content")
        checkbox_layout.addWidget(self.keep_caption_checkbox)
        checkbox_layout.addStretch()
        
        # Add checkbox layout to group layout
        group_layout.addLayout(checkbox_layout)
        
        # Text editor
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Caption will be automatically generated and can be edited here")
        text_edit.setMinimumHeight(80)
        
        # Store reference to the text editor
        self.text_editors["caption"] = text_edit
        
        # Connect text changed signal
        text_edit.textChanged.connect(
            lambda: self.text_changed.emit("caption", text_edit.toPlainText())
        )
        
        # Add to layout
        group_layout.addWidget(text_edit)
        
        # Add group box to parent layout
        parent_layout.addWidget(group_box)
        
    def get_text(self, section_id):
        """
        Get the text from a specific section.
        
        Args:
            section_id: ID of the section to get text from
            
        Returns:
            str: The text content of the section, or empty string if not found
        """
        if section_id in self.text_editors:
            return self.text_editors[section_id].toPlainText()
        return ""
        
    def set_text(self, section_id, text):
        """
        Set the text for a specific section.
        
        Args:
            section_id: ID of the section to set text for
            text: Text content to set
        """
        if section_id in self.text_editors:
            self.text_editors[section_id].setPlainText(text)
    
    def should_keep_caption(self):
        """
        Check if the caption should be kept when generating new content.
        
        Returns:
            bool: True if caption should be kept, False otherwise
        """
        return self.keep_caption_checkbox.isChecked()
    
    def get_context_files(self) -> List[str]:
        """
        Get the list of context file paths.
        
        Returns:
            List[str]: List of context file paths
        """
        return self.context_files
    
    def set_context_files(self, file_paths: List[str]):
        """
        Set the context files list.
        
        Args:
            file_paths: List of file paths
        """
        # Clear existing files
        self.context_files = []
        self.context_list_widget.clear()
        
        # Add new files
        for file_path in file_paths:
            if os.path.exists(file_path):
                self.context_files.append(file_path)
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                self.context_list_widget.addItem(item)
        
        # Emit signal with updated files list
        self.context_files_changed.emit(self.context_files)
            
    def clear_all(self):
        """Clear all text inputs and context files."""
        for editor in self.text_editors.values():
            editor.clear()
            
        self.context_files = []
        self.context_list_widget.clear()
        self.context_files_changed.emit(self.context_files) 