"""
Preset Manager Dialog for managing application presets
"""
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, 
    QListWidgetItem, QTextEdit, QInputDialog, QMessageBox, QSplitter,
    QGroupBox, QFormLayout, QLineEdit, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..base_dialog import BaseDialog
from ..preset_manager import PresetManager


class PresetManagerDialog(BaseDialog):
    """Dialog for managing application presets."""
    
    preset_applied = Signal(str)  # preset_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize preset manager
        self.preset_manager = PresetManager()
        
        # UI components
        self.preset_list = None
        self.preset_details = None
        self.instructions_edit = None
        self.photo_editing_edit = None
        self.context_files_edit = None
        
        self._setup_ui()
        self._load_presets()
        
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Preset Manager")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Preset Manager")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Create splitter for list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left side - Preset list
        left_widget = self._create_preset_list_widget()
        splitter.addWidget(left_widget)
        
        # Right side - Preset details
        right_widget = self._create_preset_details_widget()
        splitter.addWidget(right_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 500])
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Import/Export buttons
        import_btn = QPushButton("Import Presets")
        import_btn.clicked.connect(self._import_presets)
        button_layout.addWidget(import_btn)
        
        export_btn = QPushButton("Export Presets")
        export_btn.clicked.connect(self._export_presets)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
        
    def _create_preset_list_widget(self):
        """Create the preset list widget."""
        group = QGroupBox("Presets")
        layout = QVBoxLayout(group)
        
        # Preset list
        self.preset_list = QListWidget()
        self.preset_list.itemSelectionChanged.connect(self._on_preset_selected)
        layout.addWidget(self.preset_list)
        
        # List buttons
        list_button_layout = QHBoxLayout()
        
        new_btn = QPushButton("New")
        new_btn.clicked.connect(self._new_preset)
        list_button_layout.addWidget(new_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_preset)
        list_button_layout.addWidget(delete_btn)
        
        duplicate_btn = QPushButton("Duplicate")
        duplicate_btn.clicked.connect(self._duplicate_preset)
        list_button_layout.addWidget(duplicate_btn)
        
        layout.addLayout(list_button_layout)
        
        return group
        
    def _create_preset_details_widget(self):
        """Create the preset details widget."""
        group = QGroupBox("Preset Details")
        layout = QVBoxLayout(group)
        
        # Form layout for preset details
        form_layout = QFormLayout()
        
        # Preset name
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_preset_modified)
        form_layout.addRow("Name:", self.name_edit)
        
        layout.addLayout(form_layout)
        
        # Instructions
        instructions_label = QLabel("Instructions:")
        instructions_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(instructions_label)
        
        self.instructions_edit = QTextEdit()
        self.instructions_edit.setPlaceholderText("Enter general instructions for this preset...")
        self.instructions_edit.textChanged.connect(self._on_preset_modified)
        self.instructions_edit.setMaximumHeight(150)
        layout.addWidget(self.instructions_edit)
        
        # Photo editing instructions
        photo_editing_label = QLabel("Photo Editing Instructions:")
        photo_editing_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(photo_editing_label)
        
        self.photo_editing_edit = QTextEdit()
        self.photo_editing_edit.setPlaceholderText("Enter photo editing instructions for this preset...")
        self.photo_editing_edit.textChanged.connect(self._on_preset_modified)
        self.photo_editing_edit.setMaximumHeight(150)
        layout.addWidget(self.photo_editing_edit)
        
        # Context files
        context_files_label = QLabel("Context Files:")
        context_files_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(context_files_label)
        
        self.context_files_edit = QTextEdit()
        self.context_files_edit.setPlaceholderText("Context file paths (one per line)...")
        self.context_files_edit.textChanged.connect(self._on_preset_modified)
        self.context_files_edit.setMaximumHeight(100)
        layout.addWidget(self.context_files_edit)
        
        # Context files buttons
        context_button_layout = QHBoxLayout()
        
        add_file_btn = QPushButton("Add File")
        add_file_btn.clicked.connect(self._add_context_file)
        context_button_layout.addWidget(add_file_btn)
        
        clear_files_btn = QPushButton("Clear Files")
        clear_files_btn.clicked.connect(self._clear_context_files)
        context_button_layout.addWidget(clear_files_btn)
        
        context_button_layout.addStretch()
        
        layout.addLayout(context_button_layout)
        
        # Save and Apply buttons
        action_button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Preset")
        save_btn.clicked.connect(self._save_current_preset)
        action_button_layout.addWidget(save_btn)
        
        apply_btn = QPushButton("Apply Preset")
        apply_btn.clicked.connect(self._apply_current_preset)
        action_button_layout.addWidget(apply_btn)
        
        action_button_layout.addStretch()
        
        layout.addLayout(action_button_layout)
        
        return group
        
    def _load_presets(self):
        """Load presets into the list."""
        self.preset_list.clear()
        
        preset_names = self.preset_manager.get_preset_names()
        for name in preset_names:
            item = QListWidgetItem(name)
            self.preset_list.addItem(item)
            
    def _on_preset_selected(self):
        """Handle preset selection."""
        current_item = self.preset_list.currentItem()
        if not current_item:
            self._clear_details()
            return
            
        preset_name = current_item.text()
        preset_data = self.preset_manager.get_preset(preset_name)
        
        if preset_data:
            self._populate_details(preset_name, preset_data)
        else:
            self._clear_details()
            
    def _populate_details(self, name: str, data: Dict[str, Any]):
        """Populate the details panel with preset data."""
        # Block signals to prevent triggering modification events
        self.name_edit.blockSignals(True)
        self.instructions_edit.blockSignals(True)
        self.photo_editing_edit.blockSignals(True)
        self.context_files_edit.blockSignals(True)
        
        try:
            self.name_edit.setText(name)
            self.instructions_edit.setPlainText(data.get("instructions", ""))
            self.photo_editing_edit.setPlainText(data.get("photo_editing", ""))
            
            # Handle context files
            context_files = data.get("context_files", [])
            if isinstance(context_files, list):
                self.context_files_edit.setPlainText("\n".join(context_files))
            else:
                self.context_files_edit.setPlainText("")
                
        finally:
            # Re-enable signals
            self.name_edit.blockSignals(False)
            self.instructions_edit.blockSignals(False)
            self.photo_editing_edit.blockSignals(False)
            self.context_files_edit.blockSignals(False)
            
    def _clear_details(self):
        """Clear the details panel."""
        self.name_edit.clear()
        self.instructions_edit.clear()
        self.photo_editing_edit.clear()
        self.context_files_edit.clear()
        
    def _on_preset_modified(self):
        """Handle preset modification."""
        # This could be used to mark presets as modified
        pass
        
    def _new_preset(self):
        """Create a new preset."""
        name, ok = QInputDialog.getText(
            self,
            "New Preset",
            "Enter a name for the new preset:",
        )
        
        if ok and name:
            if name in self.preset_manager.get_preset_names():
                QMessageBox.warning(self, "Preset Exists", f"A preset named '{name}' already exists.")
                return
                
            # Create empty preset
            preset_data = {
                "instructions": "",
                "photo_editing": "",
                "context_files": [],
                "created": datetime.now().isoformat()
            }
            
            if self.preset_manager.save_preset(name, preset_data):
                self._load_presets()
                # Select the new preset
                for i in range(self.preset_list.count()):
                    if self.preset_list.item(i).text() == name:
                        self.preset_list.setCurrentRow(i)
                        break
            else:
                QMessageBox.critical(self, "Error", f"Failed to create preset '{name}'.")
                
    def _delete_preset(self):
        """Delete the selected preset."""
        current_item = self.preset_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a preset to delete.")
            return
            
        preset_name = current_item.text()
        
        reply = QMessageBox.question(
            self,
            "Delete Preset",
            f"Are you sure you want to delete the preset '{preset_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.preset_manager.delete_preset(preset_name):
                self._load_presets()
                self._clear_details()
            else:
                QMessageBox.critical(self, "Error", f"Failed to delete preset '{preset_name}'.")
                
    def _duplicate_preset(self):
        """Duplicate the selected preset."""
        current_item = self.preset_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a preset to duplicate.")
            return
            
        original_name = current_item.text()
        preset_data = self.preset_manager.get_preset(original_name)
        
        if not preset_data:
            QMessageBox.critical(self, "Error", f"Could not load preset '{original_name}'.")
            return
            
        new_name, ok = QInputDialog.getText(
            self,
            "Duplicate Preset",
            f"Enter a name for the duplicate of '{original_name}':",
            text=f"{original_name} (Copy)"
        )
        
        if ok and new_name:
            if new_name in self.preset_manager.get_preset_names():
                QMessageBox.warning(self, "Preset Exists", f"A preset named '{new_name}' already exists.")
                return
                
            # Create duplicate with new timestamp
            duplicate_data = preset_data.copy()
            duplicate_data["created"] = datetime.now().isoformat()
            
            if self.preset_manager.save_preset(new_name, duplicate_data):
                self._load_presets()
                # Select the new preset
                for i in range(self.preset_list.count()):
                    if self.preset_list.item(i).text() == new_name:
                        self.preset_list.setCurrentRow(i)
                        break
            else:
                QMessageBox.critical(self, "Error", f"Failed to duplicate preset '{original_name}'.")
                
    def _save_current_preset(self):
        """Save the current preset."""
        current_item = self.preset_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a preset to save.")
            return
            
        preset_name = self.name_edit.text().strip()
        if not preset_name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a valid preset name.")
            return
            
        # Get context files as list
        context_files_text = self.context_files_edit.toPlainText().strip()
        context_files = [line.strip() for line in context_files_text.split('\n') if line.strip()]
        
        preset_data = {
            "instructions": self.instructions_edit.toPlainText(),
            "photo_editing": self.photo_editing_edit.toPlainText(),
            "context_files": context_files,
            "modified": datetime.now().isoformat()
        }
        
        # If name changed, delete old preset
        original_name = current_item.text()
        if preset_name != original_name:
            if preset_name in self.preset_manager.get_preset_names():
                reply = QMessageBox.question(
                    self,
                    "Overwrite Preset",
                    f"A preset named '{preset_name}' already exists. Do you want to overwrite it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
                    
            # Delete old preset if name changed
            self.preset_manager.delete_preset(original_name)
            
        if self.preset_manager.save_preset(preset_name, preset_data):
            self._load_presets()
            # Select the saved preset
            for i in range(self.preset_list.count()):
                if self.preset_list.item(i).text() == preset_name:
                    self.preset_list.setCurrentRow(i)
                    break
            QMessageBox.information(self, "Success", f"Preset '{preset_name}' saved successfully.")
        else:
            QMessageBox.critical(self, "Error", f"Failed to save preset '{preset_name}'.")
            
    def _apply_current_preset(self):
        """Apply the current preset."""
        current_item = self.preset_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a preset to apply.")
            return
            
        preset_name = current_item.text()
        self.preset_applied.emit(preset_name)
        QMessageBox.information(self, "Applied", f"Preset '{preset_name}' has been applied.")
        
    def _add_context_file(self):
        """Add a context file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Context File",
            "",
            "All Files (*)"
        )
        
        if file_path:
            current_text = self.context_files_edit.toPlainText()
            if current_text:
                new_text = current_text + "\n" + file_path
            else:
                new_text = file_path
            self.context_files_edit.setPlainText(new_text)
            
    def _clear_context_files(self):
        """Clear all context files."""
        self.context_files_edit.clear()
        
    def _import_presets(self):
        """Import presets from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Presets",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_data = json.load(f)
                    
                if "presets" in imported_data:
                    imported_presets = imported_data["presets"]
                    count = 0
                    
                    for name, data in imported_presets.items():
                        if self.preset_manager.save_preset(name, data):
                            count += 1
                            
                    self._load_presets()
                    QMessageBox.information(self, "Import Complete", f"Successfully imported {count} presets.")
                else:
                    QMessageBox.warning(self, "Invalid File", "The selected file does not contain valid preset data.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import presets: {str(e)}")
                
    def _export_presets(self):
        """Export presets to a file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Presets",
            "presets_export.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                import json
                export_data = self.preset_manager.get_presets()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                    
                QMessageBox.information(self, "Export Complete", f"Presets exported successfully to {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export presets: {str(e)}") 