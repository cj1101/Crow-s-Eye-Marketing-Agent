#!/usr/bin/env python
"""
Knowledge Base Management Dialog
For adding and managing files in the knowledge base
"""
import os
import sys
import logging
import shutil
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QFileDialog, QMessageBox, QWidget, QApplication,
    QAbstractItemView, QSplitter, QFrame, QTextEdit, QTabWidget
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QIcon

# Import our pending messages tab
from .pending_messages import PendingMessagesTab

# Comment out the insights tab import temporarily
# from insights_tab import InsightsTab

# Initialize logger
logger = logging.getLogger(__name__)

class KnowledgeManagementDialog(QDialog):
    """Dialog for managing knowledge base files."""
    
    def __init__(self, parent=None):
        """Initialize the dialog."""
        super().__init__(parent)
        self.setWindowTitle("Knowledge Base Management")
        self.resize(900, 700)
        
        # Set up knowledge base directory
        self.knowledge_base_dir = "knowledge_base"
        os.makedirs(self.knowledge_base_dir, exist_ok=True)
        
        # List of currently loaded files
        self.knowledge_files = []
        
        # Create UI
        self._create_ui()
        
        # Load existing files
        self._load_existing_files()
        
    def _create_ui(self):
        """Create the dialog UI."""
        main_layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Knowledge Base Management")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)
        
        # Tab widget for different sections
        self.tab_widget = QTabWidget()
        
        # Files tab
        self.files_tab = QWidget()
        self._create_files_tab()
        self.tab_widget.addTab(self.files_tab, "Files")
        
        # Pending Messages tab
        self.pending_messages_tab = PendingMessagesTab()
        self.tab_widget.addTab(self.pending_messages_tab, "Pending Messages")
        
        # Comment out the Insights tab temporarily
        # self.insights_tab = InsightsTab()
        # self.tab_widget.addTab(self.insights_tab, "Insights")
        
        main_layout.addWidget(self.tab_widget)
        
        # Status label
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)
        
    def _create_files_tab(self):
        """Create the Files tab UI."""
        files_layout = QVBoxLayout(self.files_tab)
        
        # Instructions
        instructions = QLabel(
            "Add files containing business information to be used when responding to comments and direct messages. "
            "Supported formats: .txt, .md, .pdf"
        )
        instructions.setWordWrap(True)
        files_layout.addWidget(instructions)
        
        # Create splitter for file list and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # File list section
        file_list_widget = QWidget()
        file_list_layout = QVBoxLayout(file_list_widget)
        
        file_list_label = QLabel("Knowledge Base Files:")
        file_list_layout.addWidget(file_list_label)
        
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.file_list.itemSelectionChanged.connect(self._on_selection_changed)
        file_list_layout.addWidget(self.file_list)
        
        # Buttons for file operations
        file_buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("Add Files")
        add_button.clicked.connect(self._add_files)
        file_buttons_layout.addWidget(add_button)
        
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self._remove_files)
        file_buttons_layout.addWidget(remove_button)
        
        file_list_layout.addLayout(file_buttons_layout)
        
        # Preview section
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        
        preview_label = QLabel("File Preview:")
        preview_layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Select a file to preview its contents...")
        preview_layout.addWidget(self.preview_text)
        
        # Add widgets to splitter
        splitter.addWidget(file_list_widget)
        splitter.addWidget(preview_widget)
        splitter.setSizes([300, 500])  # Initial sizes
        
        files_layout.addWidget(splitter)
        
    def _load_existing_files(self):
        """Load existing files from the knowledge base directory."""
        try:
            self.file_list.clear()
            self.knowledge_files = []
            
            # Get files in knowledge base directory
            for filename in os.listdir(self.knowledge_base_dir):
                if filename.endswith((".txt", ".md", ".pdf")):
                    file_path = os.path.join(self.knowledge_base_dir, filename)
                    self.knowledge_files.append(file_path)
                    
                    # Add to list widget
                    item = QListWidgetItem(filename)
                    item.setData(Qt.ItemDataRole.UserRole, file_path)
                    self.file_list.addItem(item)
            
            # Update status
            if self.knowledge_files:
                self.status_label.setText(f"Loaded {len(self.knowledge_files)} knowledge base file(s).")
            else:
                self.status_label.setText("No knowledge base files found.")
                
            logger.info(f"Loaded {len(self.knowledge_files)} knowledge base files")
            
        except Exception as e:
            logger.exception(f"Error loading knowledge base files: {e}")
            self.status_label.setText(f"Error loading files: {str(e)}")
            
    def _add_files(self):
        """Add files to the knowledge base."""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("Text Files (*.txt *.md);;PDF Files (*.pdf);;All Files (*.*)")
        
        if file_dialog.exec() == QDialog.DialogCode.Accepted:
            files = file_dialog.selectedFiles()
            self._copy_files_to_knowledge_base(files)
            
    def _copy_files_to_knowledge_base(self, file_paths: List[str]):
        """Copy selected files to the knowledge base directory."""
        copied_count = 0
        skipped_count = 0
        
        for file_path in file_paths:
            try:
                filename = os.path.basename(file_path)
                destination = os.path.join(self.knowledge_base_dir, filename)
                
                # Check if file already exists
                if os.path.exists(destination):
                    result = QMessageBox.question(
                        self,
                        "File Already Exists",
                        f"The file '{filename}' already exists in the knowledge base. Replace it?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if result != QMessageBox.StandardButton.Yes:
                        skipped_count += 1
                        continue
                
                # Copy the file
                shutil.copy2(file_path, destination)
                copied_count += 1
                logger.info(f"Copied file to knowledge base: {filename}")
                
            except Exception as e:
                logger.exception(f"Error copying file {file_path}: {e}")
                QMessageBox.warning(
                    self,
                    "Error Copying File",
                    f"Could not copy file '{os.path.basename(file_path)}': {str(e)}"
                )
        
        # Reload file list
        self._load_existing_files()
        
        # Show summary
        if copied_count > 0:
            if skipped_count > 0:
                self.status_label.setText(f"Added {copied_count} file(s), skipped {skipped_count} file(s).")
            else:
                self.status_label.setText(f"Added {copied_count} file(s) to knowledge base.")
        elif skipped_count > 0:
            self.status_label.setText(f"No files added, skipped {skipped_count} file(s).")
        else:
            self.status_label.setText("No files selected.")
            
    def _remove_files(self):
        """Remove selected files from the knowledge base."""
        selected_items = self.file_list.selectedItems()
        
        if not selected_items:
            self.status_label.setText("No files selected for removal.")
            return
            
        # Confirm deletion
        result = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove {len(selected_items)} file(s) from the knowledge base?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result != QMessageBox.StandardButton.Yes:
            return
            
        # Remove files
        removed_count = 0
        error_count = 0
        
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            
            try:
                os.remove(file_path)
                removed_count += 1
                logger.info(f"Removed file from knowledge base: {os.path.basename(file_path)}")
                
            except Exception as e:
                logger.exception(f"Error removing file {file_path}: {e}")
                error_count += 1
                
        # Reload file list
        self._load_existing_files()
        
        # Show summary
        if removed_count > 0:
            if error_count > 0:
                self.status_label.setText(f"Removed {removed_count} file(s), {error_count} error(s).")
            else:
                self.status_label.setText(f"Removed {removed_count} file(s) from knowledge base.")
        else:
            self.status_label.setText(f"No files removed, {error_count} error(s).")
            
    def _on_selection_changed(self):
        """Handle file selection change."""
        selected_items = self.file_list.selectedItems()
        
        if not selected_items:
            # Clear preview
            self.preview_text.clear()
            return
            
        # Show first selected file
        file_path = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self._show_file_preview(file_path)
            
    def _show_file_preview(self, file_path: str):
        """Show preview of selected file."""
        try:
            # Basic file type detection
            if file_path.endswith((".txt", ".md")):
                # Text file
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.preview_text.setPlainText(content)
                
            elif file_path.endswith(".pdf"):
                # PDF file - show message that preview is not available
                self.preview_text.setPlainText("PDF preview not available.")
                
            else:
                # Unsupported file type
                self.preview_text.setPlainText("Preview not available for this file type.")
                
        except Exception as e:
            logger.exception(f"Error previewing file {file_path}: {e}")
            self.preview_text.setPlainText(f"Error loading file: {str(e)}")
            
    def accept(self):
        """Handle dialog acceptance."""
        super().accept()
        
        # Additional cleanup if needed
        self.preview_text.clear()


# For testing purposes
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = KnowledgeManagementDialog()
    dialog.show()
    sys.exit(app.exec()) 