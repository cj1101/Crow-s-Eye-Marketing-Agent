"""
Context files section component
"""
import os
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

class ContextFilesSection(QWidget):
    """Section for managing context files"""
    
    add_clicked = Signal()
    remove_clicked = Signal()
    selection_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Create layout
        self._create_layout()
        
    def _create_layout(self) -> None:
        """Create the context files section layout"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Section title
        section_title = QLabel("Context Files")
        section_title.setObjectName("sectionTitle")
        layout.addWidget(section_title)
        
        # Context files list
        self.context_list_widget = QListWidget()
        self.context_list_widget.setObjectName("contextListWidget")
        self.context_list_widget.setMinimumHeight(100)  # Set minimum height
        self.context_list_widget.setAlternatingRowColors(True)  # Better visualization
        self.context_list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.context_list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.context_list_widget)
        
        # Button container
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 5, 0, 0)
        button_layout.setSpacing(10)
        
        # Add button
        self.add_btn = QPushButton("Add")
        self.add_btn.setObjectName("addContextButton")
        self.add_btn.clicked.connect(self._on_add_clicked)
        button_layout.addWidget(self.add_btn)
        
        # Remove button
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setObjectName("removeContextButton")
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        self.remove_btn.setEnabled(False)  # Disabled until selection
        button_layout.addWidget(self.remove_btn)
        
        layout.addLayout(button_layout)
    
    def _on_add_clicked(self):
        """Handle add button click"""
        self.add_clicked.emit()
    
    def _on_remove_clicked(self):
        """Handle remove button click"""
        self.remove_clicked.emit()
    
    def _on_selection_changed(self):
        """Handle list selection changed"""
        self.remove_btn.setEnabled(len(self.context_list_widget.selectedItems()) > 0)
        self.selection_changed.emit()
    
    def add_context_file(self, file_path):
        """Add a context file to the list"""
        if not file_path or not os.path.exists(file_path):
            self.logger.warning(f"Invalid context file path: {file_path}")
            return False
        
        # Check if the file is already in the list
        for i in range(self.context_list_widget.count()):
            item = self.context_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == file_path:
                self.logger.warning(f"Context file already added: {file_path}")
                return False
        
        # Add the file to the list
        item = QListWidgetItem(os.path.basename(file_path))
        item.setData(Qt.ItemDataRole.UserRole, file_path)
        self.context_list_widget.addItem(item)
        self.logger.info(f"Added context file: {file_path}")
        return True
    
    def remove_selected_context_file(self):
        """Remove the selected context file from the list"""
        selected_items = self.context_list_widget.selectedItems()
        if not selected_items:
            return None
            
        # Get the file path
        item = selected_items[0]
        file_path = item.data(Qt.ItemDataRole.UserRole)
        
        # Remove the item
        self.context_list_widget.takeItem(self.context_list_widget.row(item))
        self.logger.info(f"Removed context file: {file_path}")
        
        # Update button state
        self._on_selection_changed()
        
        return file_path
    
    def get_context_files(self):
        """Get the list of context file paths"""
        files = []
        for i in range(self.context_list_widget.count()):
            item = self.context_list_widget.item(i)
            files.append(item.data(Qt.ItemDataRole.UserRole))
        return files
    
    def clear(self):
        """Clear all context files"""
        self.context_list_widget.clear()
        self.remove_btn.setEnabled(False) 