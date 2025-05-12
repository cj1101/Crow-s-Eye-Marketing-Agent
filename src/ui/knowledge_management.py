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
from .components.pending_messages_tab import PendingMessagesTab

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
                    response = QMessageBox.question(
                        self,
                        "File Already Exists",
                        f"The file '{filename}' already exists in the knowledge base. Do you want to replace it?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if response == QMessageBox.StandardButton.No:
                        skipped_count += 1
                        continue
                
                # Copy file to knowledge base directory
                shutil.copy2(file_path, destination)
                copied_count += 1
                
                # Add to list widget if not already there
                existing_items = [self.file_list.item(i).text() for i in range(self.file_list.count())]
                if filename not in existing_items:
                    item = QListWidgetItem(filename)
                    item.setData(Qt.ItemDataRole.UserRole, destination)
                    self.file_list.addItem(item)
                    self.knowledge_files.append(destination)
                
            except Exception as e:
                logger.exception(f"Error copying file {file_path}: {e}")
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Could not copy file {os.path.basename(file_path)}: {str(e)}"
                )
        
        # Update status
        if copied_count > 0 or skipped_count > 0:
            status = f"Added {copied_count} file(s) to the knowledge base."
            if skipped_count > 0:
                status += f" Skipped {skipped_count} file(s)."
            
            self.status_label.setText(status)
            logger.info(status)
            
    def _remove_files(self):
        """Remove selected files from the knowledge base."""
        selected_items = self.file_list.selectedItems()
        
        if not selected_items:
            return
            
        # Confirm deletion
        count = len(selected_items)
        message = f"Are you sure you want to remove {count} file(s) from the knowledge base?"
        
        response = QMessageBox.question(
            self,
            "Confirm Removal",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if response == QMessageBox.StandardButton.No:
            return
            
        # Remove files
        removed_count = 0
        
        for item in selected_items:
            try:
                file_path = item.data(Qt.ItemDataRole.UserRole)
                
                # Remove file from filesystem
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
                # Remove from list widget
                row = self.file_list.row(item)
                self.file_list.takeItem(row)
                
                # Remove from knowledge files list
                if file_path in self.knowledge_files:
                    self.knowledge_files.remove(file_path)
                    
                removed_count += 1
                
            except Exception as e:
                logger.exception(f"Error removing file {file_path}: {e}")
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Could not remove file {os.path.basename(file_path)}: {str(e)}"
                )
        
        # Update status
        if removed_count > 0:
            self.status_label.setText(f"Removed {removed_count} file(s) from the knowledge base.")
            logger.info(f"Removed {removed_count} files from knowledge base")
            
    def _on_selection_changed(self):
        """Handle selection change in the file list."""
        selected_items = self.file_list.selectedItems()
        
        if len(selected_items) == 1:
            # Show preview for the selected file
            file_path = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self._show_file_preview(file_path)
        else:
            # Clear preview if multiple files or no files are selected
            self.preview_text.clear()
            
    def _show_file_preview(self, file_path: str):
        """Show a preview of the file contents."""
        try:
            if not os.path.exists(file_path):
                self.preview_text.setPlainText("File not found.")
                return
                
            # Check file extension
            if file_path.endswith((".txt", ".md")):
                # Read text file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Show content in preview
                self.preview_text.setPlainText(content)
                
            elif file_path.endswith(".pdf"):
                self.preview_text.setPlainText("PDF preview not available.")
            else:
                self.preview_text.setPlainText("Preview not available for this file type.")
                
        except Exception as e:
            logger.exception(f"Error showing file preview: {e}")
            self.preview_text.setPlainText(f"Error: {str(e)}")
            
    def accept(self):
        """Handle dialog acceptance."""
        super().accept() 