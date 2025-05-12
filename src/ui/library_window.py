"""
Library Window for displaying and managing library items
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QMessageBox, QMenu, 
    QInputDialog, QFileDialog, QScrollArea, QGridLayout, QSplitter, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage, QIcon, QAction

from PIL import Image as PILImage

from ..handlers.library_handler import LibraryManager
from .scheduling_dialog import ScheduleDialog
from .post_options_dialog import PostOptionsDialog

class LibraryWindow(QMainWindow):
    """Window for displaying and managing library items"""
    
    def __init__(self, library_manager_instance: LibraryManager, parent=None, scheduler=None):
        super().__init__(parent)
        self.library_manager = library_manager_instance
        self.logger = logging.getLogger(self.__class__.__name__)
        self.scheduler = scheduler
        
        # UI setup
        self.setWindowTitle("Media Library")
        self.resize(1000, 700)
        
        # Set library window styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #222222;
            }
            QWidget {
                background-color: #222222;
                color: #EEEEEE;
            }
            QLabel {
                color: #EEEEEE;
            }
            QPushButton {
                background-color: #444444;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QScrollBar:vertical {
                background-color: #333333;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #666666;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QMessageBox {
                background-color: #333333;
                color: white;
            }
        """)
        
        # Create central widget and layout
        self._create_ui()
        
        # Load library items
        self.refresh_library()
        
    def _create_ui(self):
        """Create the UI components"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Header section with improved styling
        header_layout = QHBoxLayout()
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #3A3A3A; color: white; padding: 10px;")
        header_widget.setFixedHeight(60)
        
        # Title
        title_label = QLabel("Media Library")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Buttons with improved styling
        button_style = """
            QPushButton {
                background-color: #4A4A4A;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5A5A5A;
            }
            QPushButton:pressed {
                background-color: #666666;
            }
        """
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setStyleSheet(button_style)
        self.refresh_btn.clicked.connect(self.refresh_library)
        header_layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setStyleSheet(button_style)
        self.export_btn.clicked.connect(self._export_item)
        header_layout.addWidget(self.export_btn)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setStyleSheet(button_style)
        self.remove_btn.clicked.connect(self._remove_item)
        header_layout.addWidget(self.remove_btn)
        
        header_widget.setLayout(header_layout)
        main_layout.addWidget(header_widget)
        
        # Content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #555555;
                width: 2px;
            }
        """)
        
        # Create grid for library items
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(15, 15, 15, 15)
        self.grid_layout.setSpacing(15)
        
        # Create scroll area with improved styling
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.grid_widget)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #2A2A2A;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2A2A2A;
                width: 14px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #5A5A5A;
                min-height: 20px;
                border-radius: 7px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Details panel
        details_widget = QWidget()
        details_widget.setStyleSheet("background-color: #2A2A2A; color: white;")
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(15, 15, 15, 15)
        details_layout.setSpacing(10)
        
        # Preview section
        preview_section = QWidget()
        preview_section.setStyleSheet("background-color: #333333; border-radius: 8px; padding: 10px;")
        preview_layout = QVBoxLayout(preview_section)
        
        # Preview label
        preview_title = QLabel("Preview")
        preview_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        preview_layout.addWidget(preview_title)
        
        # Preview image
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(300, 300)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid #444; background-color: #222;")
        preview_layout.addWidget(self.preview_label)
        
        details_layout.addWidget(preview_section)
        
        # Caption section
        caption_section = QWidget()
        caption_section.setStyleSheet("background-color: #333333; border-radius: 8px; padding: 10px;")
        caption_layout = QVBoxLayout(caption_section)
        
        # Caption title
        caption_title = QLabel("Caption")
        caption_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        caption_layout.addWidget(caption_title)
        
        # Caption content
        self.caption_label = QLabel()
        self.caption_label.setWordWrap(True)
        self.caption_label.setStyleSheet("color: #DDD; background-color: #3A3A3A; padding: 10px; border-radius: 5px;")
        caption_layout.addWidget(self.caption_label)
        
        details_layout.addWidget(caption_section)
        
        # Metadata section
        metadata_section = QWidget()
        metadata_section.setStyleSheet("background-color: #333333; border-radius: 8px; padding: 10px;")
        metadata_layout = QVBoxLayout(metadata_section)
        
        # Metadata title
        metadata_title = QLabel("Metadata")
        metadata_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        metadata_layout.addWidget(metadata_title)
        
        # Metadata content
        self.metadata_label = QLabel()
        self.metadata_label.setWordWrap(True)
        self.metadata_label.setStyleSheet("color: #DDD; background-color: #3A3A3A; padding: 10px; border-radius: 5px;")
        metadata_layout.addWidget(self.metadata_label)
        
        details_layout.addWidget(metadata_section)
        
        # Schedule button
        if self.scheduler:
            schedule_btn_layout = QHBoxLayout()
            schedule_btn_layout.addStretch()
            
            self.schedule_btn = QPushButton("📅 Schedule Post")
            self.schedule_btn.setStyleSheet("""
                QPushButton {
                    background-color: #9b59b6;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 10px 15px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #8e44ad;
                }
            """)
            self.schedule_btn.clicked.connect(self._schedule_selected_item)
            schedule_btn_layout.addWidget(self.schedule_btn)
            
            details_layout.addLayout(schedule_btn_layout)
        
        # Add stretch to push everything up
        details_layout.addStretch()
        
        # Add widgets to splitter
        splitter.addWidget(scroll_area)
        splitter.addWidget(details_widget)
        
        # Set initial sizes (70% for grid, 30% for details)
        splitter.setSizes([700, 300])
        
        main_layout.addWidget(splitter)
        
        # Status bar with styling
        self.statusBar().setStyleSheet("background-color: #3A3A3A; color: white;")
        self.statusBar().showMessage("Ready")
        
    def refresh_library(self):
        """Refresh the library items display"""
        try:
            # Clear the grid
            for i in reversed(range(self.grid_layout.count())):
                widget = self.grid_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            
            # Get all items
            items = self.library_manager.get_all_items()
            
            # Update status
            self.statusBar().showMessage(f"Library contains {len(items)} items")
            
            # Add items to grid
            if not items:
                empty_label = QLabel("No items in library")
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_label.setStyleSheet("""
                    font-size: 20px; 
                    color: #AAAAAA; 
                    background-color: #2A2A2A;
                    padding: 30px;
                    border-radius: 10px;
                """)
                self.grid_layout.addWidget(empty_label, 0, 0)
                
                # Clear preview and info panels
                self.preview_label.clear()
                self.preview_label.setText("No items to display")
                self.caption_label.setText("No caption available")
                self.metadata_label.setText("No metadata available")
                
                return
                
            # Add items to grid
            row, col = 0, 0
            max_cols = 4  # Adjust based on window width
            
            for item in items:
                item_widget = self._create_item_widget(item)
                self.grid_layout.addWidget(item_widget, row, col)
                
                # Move to next column
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            
            # If we have items, display the first one
            if items:
                first_item_id = items[0]["id"]
                self._on_item_clicked(first_item_id)
                    
        except Exception as e:
            self.logger.exception(f"Error refreshing library: {e}")
            QMessageBox.critical(
                self,
                "Library Error",
                f"Failed to refresh library: {str(e)}"
            )
            
    def _create_item_widget(self, item: Dict[str, Any]) -> QWidget:
        """Create a widget for a library item"""
        widget = QWidget()
        widget.setProperty("itemId", item["id"])
        widget.setStyleSheet("""
            QWidget {
                background-color: #333333;
                border: 1px solid #444444;
                border-radius: 8px;
            }
            QWidget:hover {
                background-color: #3D3D3D;
                border: 1px solid #555555;
            }
            QLabel {
                color: white;
            }
        """)
        
        # Fixed size for item
        widget.setFixedSize(220, 280)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Thumbnail container with border
        thumbnail_container = QWidget()
        thumbnail_container.setStyleSheet("background-color: #222; border-radius: 6px; border: none;")
        thumbnail_container.setFixedSize(200, 150)
        thumbnail_layout = QVBoxLayout(thumbnail_container)
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)
        
        # Thumbnail
        thumbnail = QLabel()
        thumbnail.setFixedSize(200, 150)
        thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumbnail.setStyleSheet("border: none;")
        thumbnail_layout.addWidget(thumbnail)
        
        # Load thumbnail - first try path directly
        if "path" in item and os.path.exists(item["path"]):
            try:
                pixmap = QPixmap(item["path"])
                if not pixmap.isNull():
                    thumbnail.setPixmap(pixmap.scaled(
                        thumbnail.width(), 
                        thumbnail.height(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))
                else:
                    thumbnail.setText("Image Load Error")
            except Exception as e:
                self.logger.error(f"Error loading image: {e}")
                thumbnail.setText("Error")
        # Then try getting path from filename
        elif "filename" in item:
            try:
                image_path = str(self.library_manager.images_dir / item["filename"])
                if os.path.exists(image_path):
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        thumbnail.setPixmap(pixmap.scaled(
                            thumbnail.width(), 
                            thumbnail.height(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        ))
                        # Update item with correct path
                        item["path"] = image_path
                    else:
                        thumbnail.setText("Image Load Error")
                else:
                    thumbnail.setText("File Not Found")
            except Exception as e:
                self.logger.error(f"Error loading image from filename: {e}")
                thumbnail.setText("Error")
        else:
            thumbnail.setText("No Image")
        
        layout.addWidget(thumbnail_container)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #444444; max-height: 1px;")
        layout.addWidget(separator)
        
        # Item info container
        info_container = QWidget()
        info_container.setStyleSheet("background: transparent; border: none;")
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(5)
        
        # Item name (filename)
        name_label = QLabel(os.path.basename(item.get("path", item.get("filename", "Unknown"))))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-weight: bold; color: white;")
        info_layout.addWidget(name_label)
        
        # Item metadata
        meta_label = QLabel()
        # Format metadata string
        meta_str = f"Size: {item.get('size_str', 'Unknown')}"
        if "dimensions" in item:
            meta_str += f"\nDimensions: {item['dimensions'][0]}x{item['dimensions'][1]}"
        meta_label.setText(meta_str)
        meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        meta_label.setStyleSheet("font-size: 10px; color: #AAAAAA;")
        info_layout.addWidget(meta_label)
        
        layout.addWidget(info_container)
        
        # Add buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 5, 0, 0)
        
        # Add view button with improved styling
        view_btn = QPushButton("View")
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A4A4A;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5A5A5A;
            }
        """)
        view_btn.clicked.connect(lambda: self._on_item_clicked(item["id"]))
        btn_layout.addWidget(view_btn)
        
        # Add schedule button if scheduler is available
        if self.scheduler:
            schedule_btn = QPushButton("📅")
            schedule_btn.setToolTip("Schedule Post")
            schedule_btn.setStyleSheet("""
                QPushButton {
                    background-color: #9b59b6;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #8e44ad;
                }
            """)
            schedule_btn.clicked.connect(lambda: self._schedule_item(item["id"]))
            btn_layout.addWidget(schedule_btn)
            
            # Add context menu
            widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            widget.customContextMenuRequested.connect(
                lambda pos, item_id=item["id"]: self._show_context_menu(pos, item_id)
            )
        
        layout.addLayout(btn_layout)
        
        # Make widget clickable
        widget.mousePressEvent = lambda event, item_id=item["id"]: self._on_item_clicked(item_id)
        
        return widget
    
    def _show_context_menu(self, pos, item_id):
        """Show context menu for library item"""
        if not self.scheduler:
            return
            
        context_menu = QMenu(self)
        
        # Add Schedule action
        schedule_action = QAction("Schedule Post", self)
        schedule_action.triggered.connect(lambda: self._schedule_item(item_id))
        context_menu.addAction(schedule_action)
        
        # Add Export action
        export_action = QAction("Export", self)
        export_action.triggered.connect(lambda: self._export_specific_item(item_id))
        context_menu.addAction(export_action)
        
        # Add Delete action
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self._remove_specific_item(item_id))
        context_menu.addAction(delete_action)
        
        # Show the menu
        context_menu.exec(self.mapToGlobal(pos))
        
    def _schedule_item(self, item_id):
        """Schedule a specific item to be posted"""
        try:
            item = self.library_manager.get_item(item_id)
            if not item:
                QMessageBox.warning(self, "Schedule Error", "Item not found")
                return
                
            self._show_post_options(item)
            
        except Exception as e:
            self.logger.exception(f"Error scheduling item: {e}")
            QMessageBox.critical(
                self,
                "Schedule Error",
                f"Failed to schedule item: {str(e)}"
            )
            
    def _schedule_selected_item(self):
        """Schedule the currently selected item"""
        try:
            # Find selected item
            for i in range(self.grid_layout.count()):
                widget = self.grid_layout.itemAt(i).widget()
                if widget and widget.property("selected"):
                    item_id = widget.property("itemId")
                    self._schedule_item(item_id)
                    return
                    
            QMessageBox.information(self, "Schedule", "Please select an item to schedule")
            
        except Exception as e:
            self.logger.exception(f"Error scheduling selected item: {e}")
            QMessageBox.critical(
                self,
                "Schedule Error",
                f"Failed to schedule selected item: {str(e)}"
            )
            
    def _show_post_options(self, item):
        """Show the post options dialog for an item"""
        try:
            if not self.scheduler:
                QMessageBox.warning(self, "Post Options", "Scheduler not available")
                return
                
            # Check if item has required fields
            if not item or "id" not in item:
                QMessageBox.warning(self, "Post Options Error", "Invalid item selected")
                return
                
            # Get item path safely
            item_path = item.get("path", "")
            if not item_path or not os.path.exists(item_path):
                QMessageBox.warning(self, "Post Options Error", "Media file not found")
                return
                
            # Create post data
            post_data = {
                "item_id": item["id"],
                "media_path": item_path,
                "caption": item.get("caption", "")
            }
            
            # Create and show post options dialog
            dialog = PostOptionsDialog(self, post_data)
            
            # Connect signals
            dialog.post_now.connect(self._on_post_now)
            dialog.add_to_queue.connect(self._on_add_to_queue)
            dialog.edit_post.connect(self._on_edit_post)
            dialog.delete_post.connect(self._on_delete_post)
            
            # Show dialog
            dialog.exec()
            
        except Exception as e:
            self.logger.exception(f"Error showing post options: {e}")
            QMessageBox.critical(
                self,
                "Post Options Error",
                f"Failed to show post options: {str(e)}"
            )
    
    def _on_post_now(self, post_data):
        """Handle post now action"""
        try:
            if not self.scheduler:
                QMessageBox.warning(self, "Post Error", "Scheduler not available")
                return
                
            success = self.scheduler.post_now(post_data)
            if success:
                platforms = post_data.get("platforms", [])
                QMessageBox.information(
                    self,
                    "Post Successful",
                    f"Post sent to {', '.join(platforms)}"
                )
                
        except Exception as e:
            self.logger.exception(f"Error posting now: {e}")
            QMessageBox.critical(
                self,
                "Post Error",
                f"Failed to post: {str(e)}"
            )
            
    def _on_add_to_queue(self, post_data):
        """Handle add to queue action"""
        try:
            if not self.scheduler:
                QMessageBox.warning(self, "Queue Error", "Scheduler not available")
                return
                
            success = self.scheduler.add_to_queue(post_data)
            if success:
                QMessageBox.information(
                    self,
                    "Queue Successful",
                    "Post added to queue successfully"
                )
                
        except Exception as e:
            self.logger.exception(f"Error adding to queue: {e}")
            QMessageBox.critical(
                self,
                "Queue Error",
                f"Failed to add to queue: {str(e)}"
            )
            
    def _on_edit_post(self, post_data):
        """Handle edit post action"""
        try:
            # Get the item from the library
            item_id = post_data.get("item_id")
            if not item_id:
                QMessageBox.warning(self, "Edit Error", "Invalid item")
                return
                
            item = self.library_manager.get_item(item_id)
            if not item:
                QMessageBox.warning(self, "Edit Error", "Item not found")
                return
                
            # Open the main window with this item for editing
            # This would typically open the main editor with the item loaded
            QMessageBox.information(
                self,
                "Edit Post",
                f"Opening item for editing: {os.path.basename(post_data.get('media_path', ''))}"
            )
            
            # NOTE: In a real implementation, this would open the editor
            # For now, we'll just show a message
            
        except Exception as e:
            self.logger.exception(f"Error editing post: {e}")
            QMessageBox.critical(
                self,
                "Edit Error",
                f"Failed to edit post: {str(e)}"
            )
            
    def _on_delete_post(self, post_data):
        """Handle delete post action"""
        try:
            # Get the item from the library
            item_id = post_data.get("item_id")
            if not item_id:
                QMessageBox.warning(self, "Delete Error", "Invalid item")
                return
                
            # Remove the item from the library
            success = self.library_manager.remove_item(item_id)
            if success:
                QMessageBox.information(
                    self,
                    "Delete Successful",
                    "Post deleted from library"
                )
                self.refresh_library()
            else:
                QMessageBox.critical(
                    self,
                    "Delete Error",
                    "Failed to delete post"
                )
                
        except Exception as e:
            self.logger.exception(f"Error deleting post: {e}")
            QMessageBox.critical(
                self,
                "Delete Error",
                f"Failed to delete post: {str(e)}"
            )
    
    def _schedule_post(self, item):
        """Open the scheduling dialog for an item (legacy method)"""
        try:
            if not self.scheduler:
                QMessageBox.warning(self, "Schedule", "Scheduling not available")
                return
                
            # Just call the new method
            self._show_post_options(item)
                
        except Exception as e:
            self.logger.exception(f"Error scheduling post: {e}")
            QMessageBox.critical(
                self,
                "Schedule Error",
                f"Failed to schedule post: {str(e)}"
            )
        
    def _on_item_clicked(self, item_id: str):
        """Handle item click event"""
        try:
            # Clear any previous selection
            for i in range(self.grid_layout.count()):
                widget = self.grid_layout.itemAt(i).widget()
                if widget and hasattr(widget, "setProperty"):
                    widget.setProperty("selected", False)
                    widget.setStyleSheet("""
                        QWidget {
                            background-color: #333333;
                            border: 1px solid #444444;
                            border-radius: 8px;
                        }
                        QWidget:hover {
                            background-color: #3D3D3D;
                            border: 1px solid #555555;
                        }
                        QLabel {
                            color: white;
                        }
                    """)
            
            # Set this item as selected
            for i in range(self.grid_layout.count()):
                widget = self.grid_layout.itemAt(i).widget()
                if widget and hasattr(widget, "property") and widget.property("itemId") == item_id:
                    widget.setProperty("selected", True)
                    widget.setStyleSheet("""
                        QWidget {
                            background-color: #3E4C3E;
                            border: 2px solid #4CAF50;
                            border-radius: 8px;
                        }
                        QLabel {
                            color: white;
                        }
                    """)
                    break
            
            # Get item details
            item = self.library_manager.get_item(item_id)
            if item and "path" in item:
                # Update preview
                image_path = item["path"]
                if os.path.exists(image_path):
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        self.preview_label.setPixmap(pixmap.scaled(
                            self.preview_label.width(), 
                            self.preview_label.height(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        ))
                    else:
                        self.preview_label.setText("Could not load image")
                else:
                    self.preview_label.setText("Image file not found")
                
                # Update caption - get caption directly from item
                caption = item.get("caption", "No caption available")
                self.caption_label.setText(caption)
                
                # Update metadata
                meta_str = f"Filename: {os.path.basename(image_path)}\n"
                
                if "date_added" in item:
                    meta_str += f"Added: {item['date_added'][:16].replace('T', ' ')}\n"
                    
                if "dimensions" in item:
                    meta_str += f"Dimensions: {item['dimensions'][0]}x{item['dimensions'][1]}\n"
                    
                if "size_str" in item:
                    meta_str += f"Size: {item['size_str']}\n"
                    
                self.metadata_label.setText(meta_str)
                
                # Update status bar
                self.statusBar().showMessage(f"Selected: {os.path.basename(image_path)}")
            else:
                self.preview_label.setText("No preview available")
                self.caption_label.setText("No caption available")
                self.metadata_label.setText("No metadata available")
                
        except Exception as e:
            self.logger.exception(f"Error displaying item: {e}")
            QMessageBox.critical(
                self,
                "Item Error",
                f"Failed to display item: {str(e)}"
            )
            
    def _export_specific_item(self, item_id):
        """Export a specific item"""
        try:
            item = self.library_manager.get_item(item_id)
            if not item:
                QMessageBox.warning(self, "Export Error", "Item not found")
                return
                
            self._do_export_item(item)
            
        except Exception as e:
            self.logger.exception(f"Error exporting item: {e}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export item: {str(e)}"
            )
    
    def _export_item(self):
        """Export the selected item"""
        try:
            # Find selected item
            for i in range(self.grid_layout.count()):
                widget = self.grid_layout.itemAt(i).widget()
                if widget and widget.property("selected"):
                    item_id = widget.property("itemId")
                    item = self.library_manager.get_item(item_id)
                    if item:
                        self._do_export_item(item)
                    return
                    
            QMessageBox.information(self, "Export", "Please select an item to export")
            
        except Exception as e:
            self.logger.exception(f"Error exporting item: {e}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export item: {str(e)}"
            )
            
    def _do_export_item(self, item):
        """Perform the actual export of an item"""
        if not item or "path" not in item:
            QMessageBox.warning(self, "Export Error", "Invalid item")
            return
            
        # Get export path
        export_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Item",
            os.path.basename(item["path"]),
            "PNG Image (*.png);;JPEG Image (*.jpg);;All Files (*.*)"
        )
        
        if not export_path:
            return
            
        try:
            # Instead of just copying the file, let's load and save with proper quality settings
            from PIL import Image
            
            # Load the image
            with Image.open(item["path"]) as img:
                # Get the file extension
                _, ext = os.path.splitext(export_path.lower())
                
                # Save with high quality based on format
                if ext in ['.jpg', '.jpeg']:
                    # JPEG with maximum quality
                    img.save(export_path, format='JPEG', quality=100, subsampling=0)
                elif ext == '.png':
                    # PNG with no compression (highest quality)
                    img.save(export_path, format='PNG', compress_level=0)
                else:
                    # For other formats, use PIL's default with original format
                    img_format = 'PNG'  # Default to PNG if the format is not recognized
                    img.save(export_path, format=img_format)
                    
            QMessageBox.information(
                self,
                "Export Successful",
                f"Item exported to: {export_path}"
            )
        except Exception as e:
            self.logger.exception(f"Error exporting file: {e}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export item: {str(e)}"
            )
    
    def _remove_specific_item(self, item_id):
        """Remove a specific item"""
        try:
            item = self.library_manager.get_item(item_id)
            if not item:
                QMessageBox.warning(self, "Remove Error", "Item not found")
                return
                
            self._do_remove_item(item)
            
        except Exception as e:
            self.logger.exception(f"Error removing item: {e}")
            QMessageBox.critical(
                self,
                "Remove Error",
                f"Failed to remove item: {str(e)}"
            )
            
    def _remove_item(self):
        """Remove the selected item"""
        try:
            # Find selected item
            for i in range(self.grid_layout.count()):
                widget = self.grid_layout.itemAt(i).widget()
                if widget and widget.property("selected"):
                    item_id = widget.property("itemId")
                    item = self.library_manager.get_item(item_id)
                    if item:
                        self._do_remove_item(item)
                    return
                    
            QMessageBox.information(self, "Remove", "Please select an item to remove")
            
        except Exception as e:
            self.logger.exception(f"Error removing item: {e}")
            QMessageBox.critical(
                self,
                "Remove Error",
                f"Failed to remove item: {str(e)}"
            )
            
    def _do_remove_item(self, item):
        """Perform the actual removal of an item"""
        if not item or "id" not in item:
            QMessageBox.warning(self, "Remove Error", "Invalid item")
            return
            
        # Confirm deletion
        result = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to remove {os.path.basename(item.get('path', 'this item'))}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            success = self.library_manager.remove_item(item["id"])
            if success:
                QMessageBox.information(
                    self,
                    "Remove Successful",
                    "Item removed from library"
                )
                self.refresh_library()
            else:
                QMessageBox.critical(
                    self,
                    "Remove Error",
                    "Failed to remove item"
                )
    
    def set_theme(self, is_dark: bool) -> None:
        """
        Set the window theme (dark or light).
        
        Args:
            is_dark: Whether to use dark mode
        """
        # No-op as we're always using our custom gray styling
        pass 