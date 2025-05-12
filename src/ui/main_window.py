"""
Main application window UI.
"""
import os
import sys
import logging
import json
import datetime
from typing import Dict, Any, Optional, List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QMessageBox, QFileDialog, QDialog, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QIcon

from ..config import constants as const
from ..models.app_state import AppState
from ..handlers.media_handler import MediaHandler
from ..handlers.library_handler import LibraryManager
from ..handlers.ai_handler import AIHandler
from ..handlers.auth_handler import auth_handler
from ..utils.api_key_manager import key_manager
from ..handlers.image_edit_handler import ImageEditHandler

from .ui_handler import UIHandler
from .components.header_section import HeaderSection
from .components.media_section import MediaSection
from .components.text_sections import TextSections
from .components.button_section import ButtonSection
from .components.status_bar import StatusBarWidget
from .library_window import LibraryWindow
from .scheduling_panel import SchedulingPanel
from .scheduling_dialog import ScheduleDialog
from .login_dialog import LoginDialog
from .preset_manager import PresetManager

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, app_state: AppState, 
                 media_handler: MediaHandler,
                 library_manager: LibraryManager,
                 scheduler: Optional[Any] = None,
                 parent=None):
        """
        Initialize the main window.
        
        Args:
            app_state: Application state object
            media_handler: Media handler instance
            library_manager: Library manager instance
            scheduler: Optional scheduler instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Store references
        self.app_state = app_state
        self.media_handler = media_handler
        self.library_manager = library_manager
        self.scheduler = scheduler
        
        # Set up logger
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize image editor
        self.image_edit_handler = ImageEditHandler()
        
        # Initialize preset manager
        self.preset_manager = PresetManager(const.PRESETS_FILE)
        
        # Initialize UI handler
        self.ui_handler = UIHandler(self)
        
        # Initialize AI handler
        self.ai_handler = AIHandler(app_state)
        
        # Library window (will be initialized on demand)
        self.library_window = None
        
        # Setup window properties
        self.setWindowTitle("Breadsmith Marketing Tool")
        self.setMinimumSize(1000, 700)
        
        # Build UI
        self._setup_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Load presets
        self._load_presets()
        
        # Log initialization
        self.logger.info("Main window initialized")
        
        # Check authentication status
        self._check_auth_status()
        
        # Initially disable the save preset button
        self._update_preset_button_state(False)
        
    def _setup_ui(self):
        """Set up the main window UI components."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header section
        self.header_section = HeaderSection()
        main_layout.addWidget(self.header_section)
        
        # Content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel (media)
        self.media_section = MediaSection()
        splitter.addWidget(self.media_section)
        
        # Right panel (text sections)
        self.text_sections = TextSections()
        splitter.addWidget(self.text_sections)
        
        # Set initial splitter sizes (40:60)
        splitter.setSizes([400, 600])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter, 1)  # 1 = stretch factor
        
        # Button section
        self.button_section = ButtonSection()
        main_layout.addWidget(self.button_section)
        
        # Status bar
        self.status_bar = StatusBarWidget()
        self.setStatusBar(self.status_bar)
        
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Header section signals
        self.header_section.library_clicked.connect(self._on_open_library)
        self.header_section.knowledge_clicked.connect(self._on_open_knowledge)
        self.header_section.schedule_clicked.connect(self._on_open_schedule)
        self.header_section.login_clicked.connect(self._on_login)
        
        # Preset signals
        self.header_section.preset_selected.connect(self._on_preset_selected)
        self.header_section.save_preset_clicked.connect(self._on_save_preset)
        self.header_section.delete_preset_clicked.connect(self._on_delete_preset)
        
        # Button section signals
        self.button_section.library_clicked.connect(self._on_open_library)
        self.button_section.knowledge_clicked.connect(self._on_open_knowledge)
        self.button_section.generate_clicked.connect(self._on_generate)
        self.button_section.cancel_clicked.connect(self._on_cancel)
        self.button_section.add_to_library_clicked.connect(self._on_add_to_library)
        
        # Media section signals
        self.media_section.media_selected.connect(self._on_media_selected)
        self.media_section.toggle_view.connect(self._on_toggle_image_view)
        
        # Text sections signals
        self.text_sections.context_files_changed.connect(self._on_context_files_changed)
        
        # UI handler signals
        self.ui_handler.signals.status_update.connect(self._on_status_update)
        self.ui_handler.signals.error.connect(self._show_error)
        self.ui_handler.signals.warning.connect(self._show_warning)
        self.ui_handler.signals.info.connect(self._show_info)
        
    def _load_presets(self):
        """Load presets from the preset manager."""
        try:
            # Get preset names
            preset_names = self.preset_manager.get_preset_names()
            
            # Update the header preset dropdown
            self.header_section.set_presets(preset_names)
            
        except Exception as e:
            self.logger.exception(f"Error loading presets: {e}")
            self.status_bar.showMessage("Error loading presets")
            
    def _on_preset_selected(self, index):
        """Handle preset selection from dropdown."""
        try:
            # Check if a real preset is selected (index 0 is the placeholder)
            if index <= 0:
                return
                
            # Get the preset name from the combo box
            preset_name = self.header_section.preset_combo.itemText(index)
            
            # Get the preset data
            preset_data = self.preset_manager.get_preset(preset_name)
            
            if preset_data:
                # Apply the preset data to the UI
                if "instructions" in preset_data:
                    self.text_sections.set_text("instructions", preset_data["instructions"])
                    
                if "photo_editing" in preset_data:
                    self.text_sections.set_text("photo_editing", preset_data["photo_editing"])
                    
                if "context_files" in preset_data and isinstance(preset_data["context_files"], list):
                    # Check if the files still exist and set them
                    valid_files = [f for f in preset_data["context_files"] if os.path.exists(f)]
                    self.text_sections.set_context_files(valid_files)
                    
                # Show success message
                self.status_bar.showMessage(f"Loaded preset: {preset_name}")
            else:
                self._show_warning("Preset Error", f"Could not load preset: {preset_name}")
                
        except Exception as e:
            self.logger.exception(f"Error applying preset: {e}")
            self._show_error("Preset Error", f"Could not apply preset: {str(e)}")
            
    def _on_save_preset(self):
        """Handle save preset button click."""
        try:
            # Get the current state to save
            instructions = self.text_sections.get_text("instructions")
            photo_editing = self.text_sections.get_text("photo_editing")
            context_files = self.text_sections.get_context_files()
            
            # Create preset data
            preset_data = {
                "instructions": instructions,
                "photo_editing": photo_editing,
                "context_files": context_files,
                "created": datetime.datetime.now().isoformat()
            }
            
            # Ask for preset name
            preset_name, ok = QInputDialog.getText(
                self,
                "Save Preset",
                "Enter a name for this preset:",
                QLineEdit.EchoMode.Normal
            )
            
            if ok and preset_name:
                # Check if preset name already exists
                existing_names = self.preset_manager.get_preset_names()
                
                if preset_name in existing_names:
                    # Ask for confirmation to overwrite
                    reply = QMessageBox.question(
                        self,
                        "Overwrite Preset",
                        f"A preset named '{preset_name}' already exists. Do you want to overwrite it?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if reply != QMessageBox.StandardButton.Yes:
                        return
                
                # Save the preset
                if self.preset_manager.save_preset(preset_name, preset_data):
                    # Reload presets
                    self._load_presets()
                    
                    # Show success message
                    self.status_bar.showMessage(f"Preset '{preset_name}' saved successfully")
                else:
                    self._show_error("Preset Error", f"Failed to save preset: {preset_name}")
            
        except Exception as e:
            self.logger.exception(f"Error saving preset: {e}")
            self._show_error("Preset Error", f"Could not save preset: {str(e)}")
            
    def _on_delete_preset(self):
        """Handle delete preset button click."""
        try:
            # Get the currently selected preset
            index = self.header_section.preset_combo.currentIndex()
            
            # Check if a real preset is selected (index 0 is the placeholder)
            if index <= 0:
                self._show_warning("Delete Preset", "Please select a preset to delete")
                return
                
            # Get the preset name
            preset_name = self.header_section.preset_combo.itemText(index)
            
            # Ask for confirmation
            reply = QMessageBox.question(
                self,
                "Delete Preset",
                f"Are you sure you want to delete the preset '{preset_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Delete the preset
                if self.preset_manager.delete_preset(preset_name):
                    # Reload presets
                    self._load_presets()
                    
                    # Show success message
                    self.status_bar.showMessage(f"Preset '{preset_name}' deleted successfully")
                else:
                    self._show_error("Preset Error", f"Failed to delete preset: {preset_name}")
                    
        except Exception as e:
            self.logger.exception(f"Error deleting preset: {e}")
            self._show_error("Preset Error", f"Could not delete preset: {str(e)}")
            
    def _update_preset_button_state(self, enabled: bool):
        """Update the save preset button enabled state."""
        if hasattr(self.header_section, 'save_preset_btn'):
            self.header_section.save_preset_btn.setEnabled(enabled)

    def _check_auth_status(self):
        """Check authentication status and update UI accordingly."""
        try:
            # Check if we have valid authentication
            is_authenticated = auth_handler.check_auth_status()
            
            if is_authenticated:
                # Get the selected account info
                account = auth_handler.get_selected_account()
                if account:
                    # Update login button with account name
                    self.header_section.update_login_button(True, account.get('name', 'Logged In'))
                else:
                    # We're authenticated but no account is selected
                    self.header_section.update_login_button(True, "Logged In")
                
                self.status_bar.showMessage("Authenticated with Meta API")
            else:
                self.header_section.update_login_button(False)
                
                # Check if we have the required API keys
                if not key_manager.has_required_env_variables():
                    self.status_bar.showMessage("Meta API keys not set - login required")
                else:
                    self.status_bar.showMessage("Not authenticated with Meta API")
                
        except Exception as e:
            self.logger.exception(f"Error checking authentication status: {e}")
            self.header_section.update_login_button(False)
            self.status_bar.showMessage("Error checking authentication status")
            
    def _on_login(self):
        """Handle login button click."""
        try:
            # Check if already logged in
            if auth_handler.check_auth_status() and auth_handler.get_selected_account():
                # Show confirmation dialog for logout
                reply = QMessageBox.question(
                    self, 
                    "Logout Confirmation",
                    "You are already logged in. Do you want to log out?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Log out
                    auth_handler.logout()
                    self.header_section.update_login_button(False)
                    self.status_bar.showMessage("Logged out successfully")
                    
                return
            
            # Create and show login dialog
            dialog = LoginDialog(self)
            dialog.login_successful.connect(self._on_login_successful)
            
            if dialog.exec():
                self.logger.info("Login dialog accepted")
                # Login successful signal will handle the rest
            else:
                self.logger.info("Login dialog canceled")
                # Update status bar
                self._check_auth_status()
                
        except Exception as e:
            self.logger.exception(f"Error during login: {e}")
            self._show_error("Login Error", f"An error occurred during login: {str(e)}")
    
    def _on_login_successful(self, account_data):
        """Handle successful login."""
        try:
            account_name = account_data.get('name', 'Business Account')
            self.header_section.update_login_button(True, account_name)
            self.status_bar.showMessage(f"Logged in as {account_name}")
            
            # Update the app state with credentials
            if hasattr(self.app_state, 'meta_credentials'):
                # Load credentials from file
                with open(const.META_CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                    self.app_state.meta_credentials = json.load(f)
                
        except Exception as e:
            self.logger.exception(f"Error handling login success: {e}")
            self._show_error("Login Error", f"An error occurred after login: {str(e)}")
    
    def _on_open_library(self):
        """Open the library window."""
        try:
            if not self.library_window:
                self.library_window = LibraryWindow(
                    library_manager_instance=self.library_manager,
                    parent=self,
                    scheduler=self.scheduler
                )
                
            # Show the window
            self.library_window.show()
            self.library_window.raise_()
            self.library_window.activateWindow()
            
        except Exception as e:
            self.logger.exception(f"Error opening library window: {e}")
            self._show_error("Library Error", f"Could not open library: {str(e)}")
            
    def _on_open_schedule(self):
        """Open the scheduling panel."""
        try:
            if not self.scheduler:
                self._show_warning("Scheduling", "Scheduling is not available in this version.")
                return
                
            # Create scheduling panel dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Post Scheduling")
            dialog.setMinimumSize(800, 600)
            
            layout = QVBoxLayout(dialog)
            scheduling_panel = SchedulingPanel(self.app_state, dialog)
            layout.addWidget(scheduling_panel)
            
            # Show the dialog
            dialog.exec()
            
        except Exception as e:
            self.logger.exception(f"Error opening scheduling panel: {e}")
            self._show_error("Schedule Error", f"Could not open scheduling panel: {str(e)}")
            
    def _on_open_knowledge(self):
        """Open the knowledge management dialog."""
        try:
            # Import here to avoid circular imports
            from knowledge_simulator import KnowledgeSimulatorDialog
            
            # Create and show dialog
            dialog = KnowledgeSimulatorDialog(self)
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
            
        except Exception as e:
            self.logger.exception(f"Error opening knowledge dialog: {e}")
            self._show_error("Knowledge Base Error", f"Could not open knowledge base: {str(e)}")
            
    def _on_media_selected(self, media_path: str):
        """Handle media selection."""
        if media_path and os.path.exists(media_path):
            self.app_state.selected_media = media_path
            self.ui_handler.load_media(media_path)
            self.status_bar.showMessage(f"Media selected: {os.path.basename(media_path)}")
        
    def _on_context_files_changed(self, file_paths):
        """Handle context files list changes."""
        self.logger.info(f"Context files updated: {len(file_paths)} files")
        # Store in app state if needed
        if hasattr(self.app_state, 'context_files'):
            self.app_state.context_files = file_paths
        
    def _on_generate(self):
        """Handle generate button click."""
        try:
            # Get the values from the text sections
            instructions = self.text_sections.get_text("instructions")
            photo_editing = self.text_sections.get_text("photo_editing")
            
            # Get context files
            context_files = self.text_sections.get_context_files()
            
            # Check if we need to keep the existing caption
            keep_caption = self.text_sections.should_keep_caption()
            
            # Check if we need to apply photo editing
            if photo_editing.strip():
                # Apply photo editing first if instructions are provided
                self.status_bar.showMessage("Applying photo edits...")
                
                if self.app_state.selected_media:
                    success, edited_path, message = self.image_edit_handler.edit_image_with_gemini(
                        self.app_state.selected_media, photo_editing
                    )
                    
                    if success and edited_path and os.path.exists(edited_path):
                        # Store the edited image path in app state
                        self.app_state.edited_media = edited_path
                        
                        # Save a reference to the currently showing media
                        self.app_state.current_display_media = edited_path
                        
                        # Update the app state flag
                        self.app_state.showing_edited = True
                        
                        # Update the media section with the edited image
                        self.media_section.set_edited_media(edited_path)
                        
                        self.logger.info(f"Image successfully edited and saved to: {edited_path}")
                    else:
                        self.logger.warning(f"Image edit failed: {message}")
            
            # Update status for caption generation
            self.status_bar.showMessage("Generating caption...")
            self.button_section.set_generating(True)
            
            # Generate the caption using the AI handler
            caption = self.ai_handler.generate_caption(
                instructions=instructions,
                photo_editing=photo_editing,
                context_files=context_files,
                keep_existing_caption=keep_caption
            )
            
            # Update the caption text field if we're not keeping the existing one
            if not keep_caption or not self.app_state.current_caption:
                self.text_sections.set_text("caption", caption)
            
            # Update status
            self.status_bar.showMessage("Caption generated successfully")
            self.button_section.set_generating(False)
            
            # Enable save preset button after generation
            self._update_preset_button_state(True)
            
        except Exception as e:
            self.logger.exception(f"Error during generation: {e}")
            self._show_error("Generation Error", str(e))
            self.button_section.set_generating(False)
            
    def _on_cancel(self):
        """Handle cancel button click."""
        # Implement cancel logic
        pass
        
    def _on_status_update(self, message: str):
        """Handle status update signals."""
        self.status_bar.showMessage(message)
        
    def _on_add_to_library(self):
        """Handle add to library button click."""
        try:
            # Get the currently displayed media path (could be original or edited)
            media_path = self.media_section.get_current_display_path()
            
            if not media_path:
                self._show_warning("Library", "No media selected to add to library")
                return
                
            # Get the caption
            caption = self.text_sections.get_text("caption")
            
            if not caption:
                reply = QMessageBox.question(
                    self,
                    "Missing Caption",
                    "There is no caption for this media. Do you want to add it to the library anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    return
            
            # Get metadata (creation date, dimensions, etc.)
            metadata = {}
            try:
                if hasattr(self.media_handler, 'get_media_metadata'):
                    metadata = self.media_handler.get_media_metadata(media_path)
            except Exception as e:
                self.logger.warning(f"Could not get metadata for {media_path}: {e}")
            
            # Add to library using the new method that accepts a file path
            result = self.library_manager.add_item_from_path(
                file_path=media_path,
                caption=caption,
                metadata=metadata
            )
            
            if result:
                # Show success message
                self._show_info("Library", f"Media added to library with ID: {result['id']}")
                
                # Update last updated timestamp
                if hasattr(self.app_state, 'library_last_updated'):
                    self.app_state.library_last_updated = datetime.datetime.now()
            else:
                self._show_error("Library Error", "Failed to add media to library")
                
        except Exception as e:
            self.logger.exception(f"Error adding to library: {e}")
            self._show_error("Library Error", f"Could not add to library: {str(e)}")
            
    def _show_error(self, title: str, message: str):
        """Show an error message dialog."""
        QMessageBox.critical(self, title, message)
        
    def _show_warning(self, title: str, message: str):
        """Show a warning message dialog."""
        QMessageBox.warning(self, title, message)
        
    def _show_info(self, title: str, message: str):
        """Show an information message dialog."""
        QMessageBox.information(self, title, message)
        
    def closeEvent(self, event: QCloseEvent):
        """Handle window close event."""
        # Perform cleanup if needed
        event.accept()
        
    def _on_toggle_image_view(self, showing_edited: bool):
        """
        Handle toggle between original and edited image views.
        
        Args:
            showing_edited: Whether the edited image is being shown
        """
        try:
            # Get the current display path
            current_path = self.media_section.get_current_display_path()
            
            # Update app state
            self.app_state.current_display_media = current_path
            self.app_state.showing_edited = showing_edited
            
            # Update UI
            if showing_edited:
                self.status_bar.showMessage("Showing edited image")
                self.logger.info("Toggled to edited image view")
            else:
                self.status_bar.showMessage("Showing original image")
                self.logger.info("Toggled to original image view")
                
        except Exception as e:
            self.logger.exception(f"Error toggling image view: {e}")
            self.status_bar.showMessage("Error toggling image view") 