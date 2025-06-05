"""
Photo Post Workflow Manager
Handles the complete photo posting workflow in a simple, modular way.
"""

import os
import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import QObject, Signal

from ..dialogs.image_edit_dialog import ImageEditDialog
from ...handlers.library_handler import LibraryManager


class PhotoPostWorkflow(QObject):
    """Simple workflow manager for photo posting."""
    
    # Signals
    workflow_completed = Signal(str)  # item_id
    workflow_cancelled = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent_widget = parent
        
    def start_workflow(self, image_path: str):
        """
        Start the photo post workflow.
        
        Args:
            image_path: Path to the image file
        """
        try:
            if not os.path.exists(image_path):
                self._show_error("File Not Found", f"Image file not found: {image_path}")
                return
            
            self.logger.info(f"Starting photo post workflow for: {image_path}")
            
            # Step 1: Open image edit dialog
            self._open_image_edit_dialog(image_path)
            
        except Exception as e:
            self.logger.error(f"Error starting photo workflow: {e}")
            self._show_error("Workflow Error", f"Failed to start photo workflow: {str(e)}")
    
    def _open_image_edit_dialog(self, image_path: str):
        """Open the image edit dialog."""
        try:
            dialog = ImageEditDialog(image_path, self.parent_widget)
            dialog.edit_confirmed.connect(self._on_image_processed)
            
            # Show the dialog
            result = dialog.exec()
            
            if result != dialog.DialogCode.Accepted:
                self.logger.info("Image editing cancelled")
                self.workflow_cancelled.emit()
                
        except Exception as e:
            self.logger.error(f"Error opening image edit dialog: {e}")
            self._show_error("Dialog Error", f"Failed to open image editor: {str(e)}")
    
    def _on_image_processed(self, image_path: str, instructions: str):
        """Handle when image processing is complete."""
        try:
            self.logger.info(f"Image processed successfully: {image_path}")
            
            # The image edit dialog already handles saving to library
            # We just need to emit completion signal
            self.workflow_completed.emit("image_saved")
            
            # Show completion message
            self._show_info(
                "Workflow Complete",
                "Your photo has been processed and saved to the library!\n\n"
                "You can now find it in the 'Finished Posts' section of the library.\n\n"
                "From there, you can:\n"
                "• Generate captions\n"
                "• Post to social media\n"
                "• Add to galleries"
            )
            
        except Exception as e:
            self.logger.error(f"Error handling image processing completion: {e}")
            self._show_error("Processing Error", f"Error completing workflow: {str(e)}")
    
    def _show_error(self, title: str, message: str):
        """Show error message."""
        if self.parent_widget:
            QMessageBox.critical(self.parent_widget, title, message)
        else:
            self.logger.error(f"{title}: {message}")
    
    def _show_info(self, title: str, message: str):
        """Show info message."""
        if self.parent_widget:
            QMessageBox.information(self.parent_widget, title, message)
        else:
            self.logger.info(f"{title}: {message}")


class PhotoPostWorkflowManager:
    """Static manager for photo post workflows."""
    
    @staticmethod
    def start_photo_workflow(image_path: str, parent_widget: Optional[QWidget] = None):
        """
        Start a photo post workflow.
        
        Args:
            image_path: Path to the image file
            parent_widget: Parent widget for dialogs
        """
        workflow = PhotoPostWorkflow(parent_widget)
        workflow.start_workflow(image_path)
        return workflow
