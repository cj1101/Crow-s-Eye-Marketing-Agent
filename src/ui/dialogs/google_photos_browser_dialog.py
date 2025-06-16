"""
Google Photos Browser Dialog - Simple implementation for selecting media items.
"""
import logging
import requests
from typing import List, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QScrollArea, QWidget, QGridLayout, QCheckBox, QMessageBox, QProgressBar,
    QTabWidget, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont

from ..base_dialog import BaseDialog

logger = logging.getLogger(__name__)


class GooglePhotosWorker(QThread):
    """Worker thread for Google Photos operations."""
    
    data_loaded = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, operation: str, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs
        
    def run(self):
        try:
            if self.operation == "load_media":
                response = requests.get("http://localhost:8000/api/v1/google-photos/media")
                if response.status_code == 200:
                    self.data_loaded.emit(response.json())
                else:
                    self.error_occurred.emit(f"Failed to load media: {response.status_code}")
            elif self.operation == "load_albums":
                response = requests.get("http://localhost:8000/api/v1/google-photos/albums")
                if response.status_code == 200:
                    self.data_loaded.emit(response.json())
                else:
                    self.error_occurred.emit(f"Failed to load albums: {response.status_code}")
        except Exception as e:
            self.error_occurred.emit(str(e))


class GooglePhotosBrowserDialog(BaseDialog):
    """Dialog for browsing Google Photos."""
    
    media_selected = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Browse Google Photos")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        self.selected_items = []
        self.media_items = []
        self.worker = None
        
        self._setup_ui()
        self._check_connection()
        
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Select Photos from Google Photos")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Browse tab
        browse_tab = QWidget()
        browse_layout = QVBoxLayout(browse_tab)
        
        # Refresh button
        refresh_btn = QPushButton("Load Recent Photos")
        refresh_btn.clicked.connect(self._load_media)
        browse_layout.addWidget(refresh_btn)
        
        # Media display area
        self.media_display = QTextEdit()
        self.media_display.setReadOnly(True)
        self.media_display.setPlainText("Click 'Load Recent Photos' to see your Google Photos")
        browse_layout.addWidget(self.media_display)
        
        self.tab_widget.addTab(browse_tab, "Recent Photos")
        
        # Albums tab
        albums_tab = QWidget()
        albums_layout = QVBoxLayout(albums_tab)
        
        load_albums_btn = QPushButton("Load Albums")
        load_albums_btn.clicked.connect(self._load_albums)
        albums_layout.addWidget(load_albums_btn)
        
        self.albums_display = QTextEdit()
        self.albums_display.setReadOnly(True)
        self.albums_display.setPlainText("Click 'Load Albums' to see your photo albums")
        albums_layout.addWidget(self.albums_display)
        
        self.tab_widget.addTab(albums_tab, "Albums")
        
        layout.addWidget(self.tab_widget)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Selection info
        self.selection_info = QLabel("No items selected")
        self.selection_info.setStyleSheet("font-weight: bold; color: #666; margin: 5px;")
        layout.addWidget(self.selection_info)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.import_btn = QPushButton("Import Selected")
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285F4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3367D6; }
            QPushButton:disabled { background-color: #ccc; color: #666; }
        """)
        self.import_btn.clicked.connect(self.accept)
        self.import_btn.setEnabled(False)
        button_layout.addWidget(self.import_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _check_connection(self):
        """Check if Google Photos is connected."""
        try:
            response = requests.get("http://localhost:8000/api/v1/google-photos/connection")
            if response.status_code == 200:
                connection_data = response.json()
                if not connection_data:
                    self._show_not_connected()
            else:
                self._show_connection_error()
        except Exception as e:
            self._show_connection_error()
    
    def _show_not_connected(self):
        """Show not connected message."""
        QMessageBox.warning(
            self,
            "Not Connected",
            "Google Photos is not connected. Please connect your account in the Compliance section first."
        )
        self.reject()
    
    def _show_connection_error(self):
        """Show connection error."""
        QMessageBox.critical(
            self,
            "Connection Error", 
            "Could not connect to Google Photos API. Please ensure the API is running."
        )
        self.reject()
    
    def _load_media(self):
        """Load media from Google Photos."""
        if self.worker and self.worker.isRunning():
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.worker = GooglePhotosWorker("load_media")
        self.worker.data_loaded.connect(self._on_media_loaded)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()
    
    def _load_albums(self):
        """Load albums from Google Photos."""
        if self.worker and self.worker.isRunning():
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.worker = GooglePhotosWorker("load_albums")
        self.worker.data_loaded.connect(self._on_albums_loaded)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()
    
    def _on_media_loaded(self, data):
        """Handle loaded media."""
        self.progress_bar.setVisible(False)
        self.media_items = data.get('media_items', [])
        
        if not self.media_items:
            self.media_display.setPlainText("No photos found in your Google Photos account.")
            return
        
        # Display media items as a list for now
        display_text = f"Found {len(self.media_items)} photos:\n\n"
        for i, item in enumerate(self.media_items[:20]):  # Show first 20
            filename = item.get('filename', 'Unknown')
            created_time = item.get('mediaMetadata', {}).get('creationTime', 'Unknown')
            display_text += f"{i+1}. {filename} ({created_time})\n"
        
        if len(self.media_items) > 20:
            display_text += f"\n... and {len(self.media_items) - 20} more photos"
        
        display_text += "\n\nNote: Full thumbnail browser coming soon. For now, click 'Import Selected' to import the first 10 photos."
        
        self.media_display.setPlainText(display_text)
        
        # Auto-select first 10 for demo
        self.selected_items = self.media_items[:10]
        self._update_selection_info()
    
    def _on_albums_loaded(self, data):
        """Handle loaded albums."""
        self.progress_bar.setVisible(False)
        albums = data.get('albums', [])
        
        if not albums:
            self.albums_display.setPlainText("No albums found in your Google Photos account.")
            return
        
        display_text = f"Found {len(albums)} albums:\n\n"
        for album in albums:
            title = album.get('title', 'Untitled Album')
            count = album.get('mediaItemsCount', 0)
            display_text += f"• {title} ({count} items)\n"
        
        self.albums_display.setPlainText(display_text)
    
    def _on_error(self, error_message):
        """Handle errors."""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"Google Photos error: {error_message}")
    
    def _update_selection_info(self):
        """Update selection information."""
        count = len(self.selected_items)
        if count == 0:
            self.selection_info.setText("No items selected")
            self.import_btn.setEnabled(False)
        else:
            self.selection_info.setText(f"{count} item{'s' if count != 1 else ''} selected")
            self.import_btn.setEnabled(True)
    
    def get_selected_items(self):
        """Get selected items."""
        return self.selected_items 