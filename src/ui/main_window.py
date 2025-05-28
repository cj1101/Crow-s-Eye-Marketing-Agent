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
    QSplitter, QMessageBox, QFileDialog, QDialog, QInputDialog, QLineEdit, QPushButton, QStackedWidget, QScrollArea, QLabel, QApplication
)
from PySide6.QtCore import Qt, Signal, Slot, QTranslator, QEvent, QLibraryInfo, QLocale
from PySide6.QtGui import QCloseEvent, QIcon

from ..config import constants as const
from ..models.app_state import AppState
from ..handlers.media_handler import MediaHandler
from ..handlers.library_handler import LibraryManager
from ..api.ai.ai_handler import AIHandler
from ..features.authentication.auth_handler import auth_handler
from ..utils.api_key_manager import key_manager
from ..features.media_processing.image_edit_handler import ImageEditHandler

from .ui_handler import UIHandler
from .components.header_section import HeaderSection
from .components.media_section import MediaSection
from .components.text_sections import TextSections
from .components.button_section import ButtonSection
from .components.status_bar import StatusBarWidget
from .base_window import BaseMainWindow
from .library_window import LibraryWindow
from .scheduling_panel import SchedulingPanel
from .dialogs.scheduling_dialog import ScheduleDialog
from .dialogs.modern_login_dialog import ModernLoginDialog
from .dialogs.unified_connection_dialog import UnifiedConnectionDialog
from .preset_manager import PresetManager
from .dialogs.compliance_dialog import ComplianceDialog
from .dialogs.highlight_reel_dialog import HighlightReelDialog
from .dialogs.story_assistant_dialog import StoryAssistantDialog
from .dialogs.thumbnail_selector_dialog import ThumbnailSelectorDialog
from .dialogs.audio_overlay_dialog import AudioOverlayDialog
from .dialogs.custom_media_upload_dialog import CustomMediaUploadDialog
from .widgets.subscription_status_widget import SubscriptionStatusWidget
from ..utils.subscription_utils import (
    check_feature_access_with_dialog, check_usage_limit_with_dialog,
    requires_feature_qt, requires_usage_qt, show_upgrade_dialog
)
from ..features.subscription.access_control import Feature

class MainWindow(BaseMainWindow):
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
        self.translator = QTranslator(self)
        
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
        
        # Store current formatting options
        self.current_formatting_options = {
            "vertical_optimization": False,
            "caption_overlay": False,
            "caption_position": "bottom",
            "caption_font_size": "medium"
        }
        
        # Library window (will be initialized on demand)
        self.library_window = None
        self._current_image_for_overlay_base = None # Initialize here
        
        # Setup window properties
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
        
        # Subscription status widget
        self.subscription_widget = SubscriptionStatusWidget()
        main_layout.addWidget(self.subscription_widget)
        
        # Add tabs for different features
        self.tab_widget = QSplitter(Qt.Orientation.Vertical)
        
        # Original content area with splitter
        self.original_content = QWidget()
        original_layout = QVBoxLayout(self.original_content)
        original_layout.setContentsMargins(0, 0, 0, 0)
        
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
        
        # Add splitter to original content layout
        original_layout.addWidget(splitter, 1)  # 1 = stretch factor
        
        # Button section
        self.button_section = ButtonSection()
        original_layout.addWidget(self.button_section)
        
        # Create tab widget for switching between features
        self.feature_tabs = QWidget()
        self.feature_tabs_layout = QVBoxLayout(self.feature_tabs)
        self.feature_tabs_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tab_container = QWidget()
        self.tab_layout = QHBoxLayout(self.tab_container)
        self.tab_layout.setContentsMargins(10, 5, 10, 0)
        
        # Add tab buttons
        # self.caption_tab_button = QPushButton("Caption Generator") # Removed
        # self.caption_tab_button.setCheckable(True) # Removed
        # self.caption_tab_button.setChecked(True) # Removed
        # self.caption_tab_button.clicked.connect(lambda: self._switch_tab(0)) # Removed
        
        # self.tab_layout.addWidget(self.caption_tab_button) # Removed
        self.tab_layout.addStretch(1)
        
        self.feature_tabs_layout.addWidget(self.tab_container)
        
        # Tab content container
        self.tab_content = QWidget()
        self.tab_content_layout = QVBoxLayout(self.tab_content)
        self.tab_content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add original content to tab content
        self.tab_content_layout.addWidget(self.original_content)
        
        self.feature_tabs_layout.addWidget(self.tab_content)
        
        # Add tabs to main layout
        main_layout.addWidget(self.feature_tabs, 1)
        
        # Status bar
        self.status_bar = StatusBarWidget()
        self.setStatusBar(self.status_bar)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Style the tab buttons
        self._style_tab_buttons()
        
    def _style_tab_buttons(self):
        """Apply styles to tab buttons."""
        base_style = """
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-bottom: 2px solid transparent;
                background-color: transparent;
                font-weight: normal;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
            QPushButton:checked {
                border-bottom: 2px solid #6d28d9;
                font-weight: bold;
            }
        """
        
        # self.caption_tab_button.setStyleSheet(base_style) # Removed
    
    def _switch_tab(self, tab_index):
        """Switch between tabs."""
        # Update button states
        # self.caption_tab_button.setChecked(tab_index == 0) # Removed
        
        # Show/hide content
        self.original_content.setVisible(True) # Always visible as it's the only content now
        
        # Log the tab switch
        # tab_name = "Caption Generator" # Removed
        # self.logger.info(f"Switched to {tab_name} tab") # Removed
        self.logger.info("Main content area is active") # Updated log
        
        # Rest of the implementation...
        # ... existing code ...
        
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Header section signals
        self.header_section.library_clicked.connect(self._on_open_library)
        # self.header_section.knowledge_clicked.connect(self._on_open_knowledge) # This line should be removed or remain commented
        self.header_section.schedule_clicked.connect(self._on_open_schedule)
        self.header_section.login_clicked.connect(self._on_login)
        self.header_section.language_changed.connect(self._on_language_selected) # Ensure this is present
        
        # Preset signals
        self.header_section.preset_selected.connect(self._on_preset_selected)
        self.header_section.save_preset_clicked.connect(self._on_save_preset)
        self.header_section.delete_preset_clicked.connect(self._on_delete_preset)
        
        # Button section signals
        self.button_section.library_clicked.connect(self._on_open_library)
        self.button_section.knowledge_clicked.connect(self._on_open_knowledge) # Ensure this line is NOT commented
        self.button_section.generate_clicked.connect(self._on_generate)
        self.button_section.cancel_clicked.connect(self._on_cancel)
        self.button_section.add_to_library_clicked.connect(self._on_add_to_library)
        
        # Media section signals
        self.media_section.media_selected.connect(self._on_media_selected)
        self.media_section.toggle_view.connect(self._on_toggle_image_view)
        self.media_section.post_format_changed.connect(self._on_post_format_changed)
        self.media_section.video_selected.connect(self._on_video_selected)
        
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
                self.tr("Save Preset"),
                self.tr("Enter a name for this preset:"),
                QLineEdit.EchoMode.Normal
            )
            
            if ok and preset_name:
                # Check if preset name already exists
                existing_names = self.preset_manager.get_preset_names()
                
                if preset_name in existing_names:
                    # Ask for confirmation to overwrite
                    reply = QMessageBox.question(
                        self,
                        self.tr("Overwrite Preset"),
                        self.tr("A preset named '{preset_name}' already exists. Do you want to overwrite it?").format(preset_name=preset_name),
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
                    self.status_bar.showMessage(self.tr("Preset '{preset_name}' saved successfully").format(preset_name=preset_name))
                else:
                    self._show_error(self.tr("Preset Error"), self.tr("Failed to save preset: {preset_name}").format(preset_name=preset_name))
            
        except Exception as e:
            self.logger.exception(f"Error saving preset: {e}")
            self._show_error(self.tr("Preset Error"), self.tr("Could not save preset: {error_message}").format(error_message=str(e)))
            
    def _on_delete_preset(self):
        """Handle delete preset button click."""
        try:
            # Get the currently selected preset
            index = self.header_section.preset_combo.currentIndex()
            
            # Check if a real preset is selected (index 0 is the placeholder)
            if index <= 0:
                self._show_warning(self.tr("Delete Preset"), self.tr("Please select a preset to delete"))
                return
                
            # Get the preset name
            preset_name = self.header_section.preset_combo.itemText(index)
            
            # Ask for confirmation
            reply = QMessageBox.question(
                self,
                self.tr("Delete Preset"),
                self.tr("Are you sure you want to delete the preset '{preset_name}'?").format(preset_name=preset_name),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Delete the preset
                if self.preset_manager.delete_preset(preset_name):
                    # Reload presets
                    self._load_presets()
                    
                    # Show success message
                    self.status_bar.showMessage(self.tr("Preset '{preset_name}' deleted successfully").format(preset_name=preset_name))
                else:
                    self._show_error(self.tr("Preset Error"), self.tr("Failed to delete preset: {preset_name}").format(preset_name=preset_name))
                    
        except Exception as e:
            self.logger.exception(f"Error deleting preset: {e}")
            self._show_error(self.tr("Preset Error"), self.tr("Could not delete preset: {error_message}").format(error_message=str(e)))
            
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
                    self.header_section.update_login_button(True, account.get('name', self.tr('Logged In')))
                else:
                    # We're authenticated but no account is selected
                    self.header_section.update_login_button(True, self.tr("Logged In"))
                
                self.status_bar.showMessage(self.tr("Authenticated with Meta API"))
            else:
                self.header_section.update_login_button(False)
                
                # Check if we have the required API keys
                if not key_manager.has_required_env_variables():
                    self.status_bar.showMessage(self.tr("Meta API keys not set - login required"))
                else:
                    self.status_bar.showMessage(self.tr("Not authenticated with Meta API"))
                
        except Exception as e:
            self.logger.exception(f"Error checking authentication status: {e}")
            self.header_section.update_login_button(False)
            self.status_bar.showMessage(self.tr("Error checking authentication status"))
            
    def _on_login(self):
        """Handle login button click."""
        try:
            # Check if already logged in
            if auth_handler.check_auth_status() and auth_handler.get_selected_account():
                # Show confirmation dialog for logout
                reply = QMessageBox.question(
                    self, 
                    self.tr("Logout Confirmation"),
                    self.tr("You are already logged in. Do you want to log out?"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Log out
                    auth_handler.logout()
                    self.header_section.update_login_button(False)
                    self.status_bar.showMessage(self.tr("Logged out successfully"))
                    
                return
            
            # Create and show unified connection dialog
            dialog = UnifiedConnectionDialog(self)
            dialog.connection_successful.connect(self._on_connection_successful)
            
            # The dialog will handle its own translation in __init__
            
            if dialog.exec():
                self.logger.info("Connection dialog accepted")
                # Connection successful signal will handle the rest
            else:
                self.logger.info("Connection dialog canceled")
                # Update status bar
                self._check_auth_status()
                
        except Exception as e:
            self.logger.exception(f"Error during login: {e}")
            self._show_error(self.tr("Login Error"), self.tr("An error occurred during login: {error_message}").format(error_message=str(e)))
    
    def _on_connection_successful(self, platform_status):
        """Handle successful platform connections."""
        try:
            connected_platforms = []
            for platform, status in platform_status.items():
                if status.get('connected', False):
                    connected_platforms.append(platform.upper())
            
            if connected_platforms:
                platforms_text = ", ".join(connected_platforms)
                self.header_section.update_login_button(True, f"Connected: {platforms_text}")
                self.status_bar.showMessage(self.tr("Connected to: {platforms}").format(platforms=platforms_text))
            else:
                self.header_section.update_login_button(False)
                self.status_bar.showMessage(self.tr("No platforms connected"))
            
            # Update the app state with credentials
            if hasattr(self.app_state, 'meta_credentials') and platform_status.get('meta', {}).get('connected', False):
                # Load Meta credentials from file
                try:
                    with open(const.META_CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                        self.app_state.meta_credentials = json.load(f)
                except FileNotFoundError:
                    self.logger.warning("Meta credentials file not found after connection")
                
        except Exception as e:
            self.logger.exception(f"Error handling connection success: {e}")
            self._show_error(self.tr("Connection Error"), self.tr("An error occurred after connection: {error_message}").format(error_message=str(e)))
    
    def _on_login_successful(self, account_data):
        """Handle successful login (legacy method for compatibility)."""
        try:
            account_name = account_data.get('name', self.tr('Business Account'))
            self.header_section.update_login_button(True, account_name)
            self.status_bar.showMessage(self.tr("Logged in as {account_name}").format(account_name=account_name))
            
            # Update the app state with credentials
            if hasattr(self.app_state, 'meta_credentials'):
                # Load credentials from file
                with open(const.META_CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                    self.app_state.meta_credentials = json.load(f)
                
        except Exception as e:
            self.logger.exception(f"Error handling login success: {e}")
            self._show_error(self.tr("Login Error"), self.tr("An error occurred after login: {error_message}").format(error_message=str(e)))
    
    @requires_feature_qt(Feature.MEDIA_LIBRARY)
    def _on_open_library(self):
        """Open the library window with media and Crow's Eye functionality."""
        try:
            if not self.library_window:
                self.library_window = LibraryWindow(
                    library_manager_instance=self.library_manager,
                    parent=self,
                    scheduler=self.scheduler
                )
                # Connect the generate post signal
                self.library_window.generate_post_requested.connect(self._on_generate_post_from_library)
                
            # Show the window
            self.library_window.show()
            self.library_window.raise_()
            self.library_window.activateWindow()
            
        except Exception as e:
            self.logger.exception(f"Error opening library window: {e}")
            self._show_error(self.tr("Library Error"), self.tr("Could not open library window: {error_message}").format(error_message=e))
            
    def _on_open_schedule(self):
        """Open the scheduling panel."""
        try:
            if not self.scheduler:
                # Create the scheduler instance if it doesn't exist yet
                from src.handlers.schedule_handler import Scheduler
                self.scheduler = Scheduler()
                
            # Create a scheduling dialog
            from src.ui.dialogs.scheduling_dialog import ScheduleDialog
            dialog = ScheduleDialog(parent=self)
            
            # Connect signals
            dialog.schedule_saved.connect(self.scheduler.add_or_update_schedule)
            
            # Show the dialog
            dialog.exec()
            
        except Exception as e:
            self.logger.exception(f"Error opening scheduling panel: {e}")
            self._show_error(self.tr("Schedule Error"), self.tr("Could not open scheduling panel: {error_message}").format(error_message=str(e)))
            
    def _on_open_knowledge(self):
        """Open the knowledge management dialog."""
        try:
            # Import here to avoid circular imports
            from .knowledge_simulator import KnowledgeSimulatorDialog
            
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
            self._current_image_for_overlay_base = media_path # Set base for overlay
            self.ui_handler.load_media(media_path)
            self.status_bar.showMessage(f"Media selected: {os.path.basename(media_path)}")
            # Reset formatting options when new media is selected
            self.current_formatting_options = {
                "vertical_optimization": False, 
                "caption_overlay": False,
                "caption_position": "bottom",
                "caption_font_size": "medium"
            }
            # Potentially reset UI elements in MediaSection to their defaults here
            if hasattr(self.media_section, 'post_type_combo'): # Example, adapt to actual UI elements
                 # self.media_section.vertical_optimization_checkbox.setChecked(False)
                 # self.media_section.caption_overlay_checkbox.setChecked(False)
                 # self.media_section.caption_position_combo.setCurrentText("Bottom")
                 # self.media_section.font_size_combo.setCurrentText("Medium")
                 pass # Add actual UI reset if MediaSection doesn't handle it
        
    def _on_context_files_changed(self, file_paths):
        """Handle context files list changes."""
        self.logger.info(f"Context files updated: {len(file_paths)} files")
        # Store in app state if needed
        if hasattr(self.app_state, 'context_files'):
            self.app_state.context_files = file_paths
        
    @requires_feature_qt(Feature.BASIC_POSTING)
    @requires_usage_qt('posts', 1)
    def _on_generate(self):
        """Handle generate button click."""
        self.logger.info("Generate button clicked")
        self.status_bar.showMessage(self.tr("Processing request..."))

        # Get all inputs
        instructions = self.text_sections.get_instructions()
        photo_editing = self.text_sections.get_photo_editing_instructions()
        context_files = self.app_state.context_files
        keep_caption = self.text_sections.get_keep_caption_state()
        current_image_path_for_processing = self.app_state.selected_media
        current_audio_path = self.media_section.get_current_audio_path()

        # Get current language code from app_state, default to 'en'
        current_language = getattr(self.app_state, 'current_language_code', 'en')
        if not current_language: # Handle case where it might be None or empty
            current_language = 'en'
        self.logger.info(f"Current language for generation: {current_language}")

        # Reset to original before potential edits
        self._current_image_for_overlay_base = self.app_state.selected_media

        self.button_section.set_generating(True)

        # Determine the caption to use
        caption_to_use = ""
        if self.app_state.selected_media or context_files: # Only generate if there's media or context
            self.logger.info("Calling AI handler to generate caption.")
            # Pass the current language to the caption generator
            caption_to_use = self.ai_handler.generate_caption(
                instructions, 
                photo_editing, 
                context_files,
                keep_caption, # Pass the keep_caption state
                language_code=current_language # Pass the language code
            )
            self.logger.info(f"Caption generated: {caption_to_use[:50]}...")
            # Set the generated caption in the UI
            if caption_to_use:
                self.text_sections.set_text("caption", caption_to_use)
                self.app_state.current_caption = caption_to_use
        elif keep_caption and self.app_state.current_caption: # If keeping caption and one exists
            caption_to_use = self.app_state.current_caption
            self.logger.info(f"Keeping existing caption: {caption_to_use[:50]}...")

        # Check if we need to apply photo editing
        if photo_editing.strip():
            # Apply photo editing first if instructions are provided
            self.status_bar.showMessage(self.tr("Applying photo edits..."))
            
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
                    
                    current_image_path_for_processing = edited_path # Update path for subsequent steps
                    self._current_image_for_overlay_base = edited_path # Update base for overlay
                    self.logger.info(f"Image successfully edited and saved to: {edited_path}")
                else:
                    self.logger.warning(f"Image edit failed: {message}")
        
        # Update status for caption generation
        self.status_bar.showMessage(self.tr("Generating caption..."))
        self.button_section.set_generating(True)
        
        # Apply post-caption generation formatting options
        final_image_path = current_image_path_for_processing

        if self.current_formatting_options.get("vertical_optimization"):
            self.status_bar.showMessage(self.tr("Applying vertical optimization..."))
            self.logger.info(f"Applying vertical optimization to: {final_image_path}")
            success, optimized_path, msg = self.image_edit_handler.optimize_for_story(final_image_path)
            if success and optimized_path and os.path.exists(optimized_path):
                final_image_path = optimized_path
                self.logger.info(f"Vertical optimization successful: {final_image_path}")
            else:
                self.logger.warning(f"Vertical optimization failed: {msg}")
                self._show_warning(self.tr("Optimization Error"), self.tr("Could not apply vertical optimization: {error_message}").format(error_message=msg))

        if self.current_formatting_options.get("caption_overlay") and caption_to_use:
            self.status_bar.showMessage(self.tr("Applying caption overlay..."))
            caption_pos = self.current_formatting_options.get("caption_position", "bottom")
            font_size_str = self.current_formatting_options.get("caption_font_size", "medium")
            
            # Map string size to pixel value (approximate)
            # These can be tuned for better visual results
            font_size_map = {
                "small": int(self.media_section.media_preview.height() / 40) if self.media_section.media_preview.height() > 0 else 12,
                "medium": int(self.media_section.media_preview.height() / 25) if self.media_section.media_preview.height() > 0 else 20,
                "large": int(self.media_section.media_preview.height() / 15) if self.media_section.media_preview.height() > 0 else 32,
                "extra large": int(self.media_section.media_preview.height() / 10) if self.media_section.media_preview.height() > 0 else 44
            }
            font_size_px = font_size_map.get(font_size_str, font_size_map["medium"]) # Default to medium if string unknown
            font_size_px = max(10, font_size_px) # Ensure a minimum font size

            self.logger.info(f"Applying caption overlay to: {final_image_path} at position: {caption_pos}, font size: {font_size_str} ({font_size_px}px)")
            success, overlay_path, msg = self.image_edit_handler.add_caption_overlay(
                final_image_path, 
                caption_to_use, # Use the determined caption
                position=caption_pos,
                font_size_px=font_size_px # Pass pixel font size
            )
            if success and overlay_path and os.path.exists(overlay_path):
                final_image_path = overlay_path
                self.logger.info(f"Caption overlay successful: {final_image_path}")
            else:
                self.logger.warning(f"Caption overlay failed: {msg}")
                self._show_warning(self.tr("Overlay Error"), self.tr("Could not apply caption overlay: {error_message}").format(error_message=msg))
        
        # Update app_state and media_section with the final image
        if final_image_path != current_image_path_for_processing: # If any additional processing happened
            self.app_state.edited_media = final_image_path
            self.app_state.current_display_media = final_image_path
            self.app_state.showing_edited = True
            self.media_section.set_edited_media(final_image_path) # This will refresh the preview

        # Store audio path in app state for later use
        if current_audio_path:
            self.app_state.current_audio = current_audio_path
            self.logger.info(f"Audio file attached to post: {os.path.basename(current_audio_path)}")
        
        # Update status
        self.status_bar.showMessage(self.tr("Caption generated successfully"))
        self.button_section.set_generating(False)
        
        # Enable save preset button after generation
        self._update_preset_button_state(True)
        
    def _on_cancel(self):
        """Handle cancel button click."""
        # Implement cancel logic
        pass
        
    def _on_status_update(self, message: str):
        """Handle status update signals."""
        self.status_bar.showMessage(message)
        
    def _on_add_to_library(self):
        """Handle finish post button click (formerly add to library)."""
        try:
            # Get the currently displayed media path (could be original or edited)
            media_path = self.media_section.get_current_display_path()
            
            if not media_path:
                self._show_warning(self.tr("Finish Post"), self.tr("No media selected to finish"))
                return
                
            # Get the caption
            caption = self.text_sections.get_text("caption")
            
            if not caption:
                reply = QMessageBox.question(
                    self,
                    self.tr("Missing Caption"),
                    self.tr("There is no caption for this media. Do you want to finish the post anyway?"),
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
                
                # Add audio information to metadata if available
                if hasattr(self.app_state, 'current_audio') and self.app_state.current_audio:
                    metadata['audio_file'] = self.app_state.current_audio
                    metadata['has_audio'] = True
                    self.logger.info(f"Including audio file in post metadata: {os.path.basename(self.app_state.current_audio)}")
                else:
                    metadata['has_audio'] = False
                    
            except Exception as e:
                self.logger.warning(f"Could not get metadata for {media_path}: {e}")
            
            # Add to library using the new method that accepts a file path
            result = self.library_manager.add_item_from_path(
                file_path=media_path,
                caption=caption,
                metadata=metadata,
                is_post_ready=True
            )
            
            if result:
                # Show success message
                self._show_info(self.tr("Post Finished"), self.tr("Post has been finalized and saved as: {filename}").format(filename=os.path.basename(media_path)))
                
                # Update last updated timestamp
                if hasattr(self.app_state, 'library_last_updated'):
                    self.app_state.library_last_updated = datetime.datetime.now()
                
                # Refresh library window if it's open
                if hasattr(self, 'library_window') and self.library_window and self.library_window.isVisible():
                    self.library_window.refresh_library()
                if hasattr(self, 'library_window_instance') and self.library_window_instance and self.library_window_instance.isVisible():
                    self.library_window_instance.refresh_library()
                    
                # Switch to the Crow's Eye Marketing tab to see the finished post
                # self._switch_tab(1) # Remove this line - perhaps switch to library or stay on current tab
            else:
                self._show_error(self.tr("Finish Post Error"), self.tr("Failed to finish post"))
                
        except Exception as e:
            self.logger.exception(f"Error finishing post: {e}")
            self._show_error(self.tr("Finish Post Error"), self.tr("Could not finish post: {error_message}").format(error_message=str(e)))
            
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
                self.status_bar.showMessage(self.tr("Showing edited image"))
                self.logger.info("Toggled to edited image view")
            else:
                self.status_bar.showMessage(self.tr("Showing original image"))
                self.logger.info("Toggled to original image view")
                
        except Exception as e:
            self.logger.exception(f"Error toggling image view: {e}")
            self.status_bar.showMessage(self.tr("Error toggling image view"))

    @Slot()
    def open_library_window(self):
        """Opens the media library window."""
        try:
            if not hasattr(self, 'library_window_instance') or not self.library_window_instance.isVisible():
                # Pass library_manager_instance to LibraryWindow
                self.library_window_instance = LibraryWindow(library_manager_instance=self.library_manager, parent=self, scheduler=self.scheduler)
                self.logger.info("Showing LibraryWindow.")
                self.library_window_instance.show()
            else:
                self.library_window_instance.activateWindow()
                self.logger.info("LibraryWindow already visible, activating.")
        except Exception as e:
            self.logger.exception(f"Error opening library window: {e}")
            QMessageBox.critical(self, self.tr("Error"), self.tr("Could not open library window: {error_message}").format(error_message=e))

    @Slot()
    def show_crowseye_tab(self):
        # This method might now be obsolete or needs to be re-evaluated
        # For now, let's comment it out or remove it if it's no longer used.
        # self.logger.info("Attempting to show Crow's Eye tab (now removed).")
        # self._switch_tab(0) # Or handle appropriately
        pass # Placeholder, to be reviewed if this slot is still connected 

    def _on_post_format_changed(self, formatting_details: dict):
        """Handle changes in post formatting options from MediaSection."""
        self.current_formatting_options = formatting_details
        self.logger.info(f"Main window received formatting options: {self.current_formatting_options}")
        
        # All preview logic removed. Generate button will handle final application.
        
        # Rest of the method remains unchanged (which is nothing in this simplified version)
    
    def _on_video_selected(self, is_video: bool):
        """Handle when video is selected to enable/disable photo editing."""
        try:
            # Enable/disable photo editing section based on media type
            self.text_sections.set_photo_editing_enabled(not is_video)
            
            if is_video:
                self.logger.info("Video selected - photo editing section disabled")
                self.status_bar.showMessage("Video selected - photo editing disabled")
            else:
                self.logger.info("Image selected - photo editing section enabled")
                self.status_bar.showMessage("Image selected - photo editing enabled")
                
        except Exception as e:
            self.logger.exception(f"Error handling video selection: {e}") 

    def _on_language_selected(self, lang_code: str):
        """Handle language selection change (Currently disabled)"""
        self.logger.info(f"Language selection received: {lang_code} (functionality disabled)")
        # All language switching functionality has been disabled
        # Language dropdown is kept in the UI for future implementation

    def changeEvent(self, event: QEvent) -> None:
        """Handle events, specifically LanguageChange for re-translation."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        """Retranslate all UI elements in MainWindow and its direct custom components."""
        self.setWindowTitle(self.tr("Crow's Eye"))
        
        # Retranslate custom child components
        if hasattr(self, 'header_section') and self.header_section:
            self.header_section.retranslateUi()
        if hasattr(self, 'media_section') and self.media_section:
            self.media_section.retranslateUi()
        if hasattr(self, 'text_sections') and self.text_sections:
            self.text_sections.retranslateUi()
        if hasattr(self, 'button_section') and self.button_section:
            self.button_section.retranslateUi()
        if hasattr(self, 'status_bar') and self.status_bar:
            self.status_bar.retranslateUi()
            
        # Retranslate any dynamically created dialogs if they are stored and accessible
        # For example, if self.library_window exists and is visible:
        if self.library_window and self.library_window.isVisible():
            self.library_window.retranslateUi() # Assuming LibraryWindow has retranslateUi
        
        # Recreate menu bar with translated text
        if hasattr(self, 'menuBar'):
            self._create_menu_bar()
        
        # Add any other direct text updates for MainWindow itself here
        # Example: self.some_main_window_label.setText(self.tr("Main Window Specific Text"))

        # Note: Messages shown via QMessageBox, QInputDialog, QFileDialog are typically
        # translated at the point they are shown, using self.tr() there.

    def _create_menu_bar(self):
        """Create the menu bar with compliance features."""
        try:
            menubar = self.menuBar()
            menubar.clear()  # Clear existing menus for retranslation
            
            # File menu
            file_menu = menubar.addMenu(self.tr('&File'))
            
            # Add export action
            export_action = file_menu.addAction(self.tr('Export Data...'))
            export_action.setShortcut('Ctrl+E')
            export_action.triggered.connect(self._quick_export_data)
            
            file_menu.addSeparator()
            
            # Add exit action
            exit_action = file_menu.addAction(self.tr('E&xit'))
            exit_action.setShortcut('Ctrl+Q')
            exit_action.triggered.connect(self.close)
            
            # Social Media menu
            social_menu = menubar.addMenu(self.tr('&Social Media'))
            
            # Add custom media upload action
            upload_action = social_menu.addAction(self.tr('Upload Custom Media...'))
            upload_action.setShortcut('Ctrl+U')
            upload_action.triggered.connect(self._on_open_custom_upload)
            
            social_menu.addSeparator()
            
            # Add post to platforms action (for current media)
            post_current_action = social_menu.addAction(self.tr('Post Current Media...'))
            post_current_action.setShortcut('Ctrl+Shift+P')
            post_current_action.triggered.connect(self._on_post_current_media)
            
            # Video menu
            video_menu = menubar.addMenu(self.tr('&Video'))
            
            # Add highlight reel generator
            highlight_reel_action = video_menu.addAction(self.tr('Highlight Reel Generator...'))
            highlight_reel_action.setShortcut('Ctrl+H')
            highlight_reel_action.triggered.connect(self._on_open_highlight_reel)
            
            # Add story assistant
            story_assistant_action = video_menu.addAction(self.tr('Story Assistant...'))
            story_assistant_action.setShortcut('Ctrl+S')
            story_assistant_action.triggered.connect(self._on_open_story_assistant)
            
            # Add thumbnail selector
            thumbnail_selector_action = video_menu.addAction(self.tr('Reel Thumbnail Selector...'))
            thumbnail_selector_action.setShortcut('Ctrl+T')
            thumbnail_selector_action.triggered.connect(self._on_open_thumbnail_selector)
            
            video_menu.addSeparator()
            
            # Add Veo video generator
            veo_generator_action = video_menu.addAction(self.tr('🎬 Veo Video Generator...'))
            veo_generator_action.setShortcut('Ctrl+V')
            veo_generator_action.triggered.connect(self._on_open_veo_generator)
            
            # Add audio overlay
            audio_overlay_action = video_menu.addAction(self.tr('Audio Overlay...'))
            audio_overlay_action.setShortcut('Ctrl+A')
            audio_overlay_action.triggered.connect(self._on_open_audio_overlay)
            
            # Analytics menu
            analytics_menu = menubar.addMenu(self.tr('&Analytics'))
            
            # Add analytics dashboard
            analytics_action = analytics_menu.addAction(self.tr('Performance Dashboard...'))
            analytics_action.setShortcut('Ctrl+D')
            analytics_action.triggered.connect(self._on_open_analytics_dashboard)
            
            # Privacy menu
            privacy_menu = menubar.addMenu(self.tr('&Privacy'))
            
            # Add compliance dialog action
            compliance_action = privacy_menu.addAction(self.tr('Privacy & Compliance...'))
            compliance_action.setShortcut('Ctrl+P')
            compliance_action.triggered.connect(self._on_open_compliance)
            
            privacy_menu.addSeparator()
            
            # Add quick factory reset action
            factory_reset_action = privacy_menu.addAction(self.tr('Factory Reset...'))
            factory_reset_action.triggered.connect(self._quick_factory_reset)
            
            # Help menu
            help_menu = menubar.addMenu(self.tr('&Help'))
            
            # Add privacy policy action
            privacy_policy_action = help_menu.addAction(self.tr('Privacy Policy'))
            privacy_policy_action.triggered.connect(self._open_privacy_policy)
            
            # Add about action
            about_action = help_menu.addAction(self.tr('About'))
            about_action.triggered.connect(self._show_about)
            
            self.logger.info("Menu bar created successfully")
            
        except Exception as e:
            self.logger.error(f"Error creating menu bar: {e}")
    
    def _on_open_compliance(self):
        """Open the compliance and privacy dialog."""
        try:
            dialog = ComplianceDialog(self)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Error opening compliance dialog: {e}")
            self._show_error("Compliance Error", f"Could not open compliance dialog: {str(e)}")
    
    def _quick_export_data(self):
        """Quick data export action from menu."""
        try:
            from ..handlers.compliance_handler import compliance_handler
            
            reply = QMessageBox.question(
                self,
                "Export User Data",
                "This will create a comprehensive export of all your data. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                export_path = compliance_handler.export_user_data()
                self._show_info("Export Complete", f"Data exported successfully to:\n{export_path}")
                
        except Exception as e:
            self.logger.error(f"Error during quick export: {e}")
            self._show_error("Export Error", f"Failed to export data: {str(e)}")
    
    def _quick_factory_reset(self):
        """Quick factory reset action from menu."""
        try:
            reply = QMessageBox.critical(
                self,
                "⚠️ FACTORY RESET WARNING ⚠️",
                "This will PERMANENTLY DELETE ALL YOUR DATA!\n\n"
                "This includes all media files, presets, settings, and cached data.\n\n"
                "THIS CANNOT BE UNDONE!\n\n"
                "For a more detailed view of what will be deleted,\n"
                "please use Privacy & Compliance dialog instead.\n\n"
                "Are you absolutely sure you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Open the compliance dialog to the factory reset tab
                dialog = ComplianceDialog(self)
                dialog.tab_widget.setCurrentIndex(4)  # Factory reset tab is index 4
                dialog.exec()
                
        except Exception as e:
            self.logger.error(f"Error during factory reset: {e}")
            self._show_error("Factory Reset Error", f"Failed to initiate factory reset: {str(e)}")
    
    def _open_privacy_policy(self):
        """Open the privacy policy URL."""
        try:
            import webbrowser
            webbrowser.open("https://www.breadsmithbakery.com/privacy-policy")
        except Exception as e:
            self.logger.error(f"Error opening privacy policy: {e}")
            self._show_error("Privacy Policy Error", "Could not open privacy policy in browser")
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """
        <h3>Crow's Eye - Social Media Marketing Tool</h3>
        <p><b>Version:</b> 5.0</p>
        <p><b>Meta Developer Platform Compliant</b></p>
        <br>
        <p>A smart marketing automation platform for creators and small businesses.</p>
        <br>
        <p><b>Privacy & Compliance Features:</b></p>
        <ul>
        <li>✅ Data Deletion Request Handling</li>
        <li>✅ GDPR/CCPA Compliant Data Export</li>
        <li>✅ Factory Reset Capability</li>
        <li>✅ Privacy Policy Integration</li>
        <li>✅ Security Incident Reporting</li>
        </ul>
        <br>
        <p>For privacy concerns: privacy@breadsmithbakery.com</p>
        """
        
        QMessageBox.about(self, "About Crow's Eye", about_text)
    
    def _on_generate_post_from_library(self, media_path: str):
        """Handle generate post request from library window."""
        try:
            # Load the media into the main window
            self._on_media_selected(media_path)
            
            # Show a status message
            self.status_bar.showMessage(f"Loaded media for post generation: {os.path.basename(media_path)}")
            
            # Bring main window to front
            self.show()
            self.raise_()
            self.activateWindow()
            
        except Exception as e:
            self.logger.error(f"Error loading media from library: {e}")
            self._show_error("Load Error", f"Could not load media for post generation: {str(e)}")
    
    @requires_feature_qt(Feature.HIGHLIGHT_REEL_GENERATOR)
    def _on_open_highlight_reel(self):
        """Open the highlight reel generator dialog."""
        try:
            dialog = HighlightReelDialog(self)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Error opening highlight reel dialog: {e}")
            self._show_error("Highlight Reel Error", f"Could not open highlight reel generator: {str(e)}")
    
    @requires_feature_qt(Feature.STORY_ASSISTANT)
    def _on_open_story_assistant(self):
        """Open the story assistant dialog."""
        try:
            dialog = StoryAssistantDialog(self)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Error opening story assistant dialog: {e}")
            self._show_error("Story Assistant Error", f"Could not open story assistant: {str(e)}")
    
    def _on_open_thumbnail_selector(self):
        """Open the thumbnail selector dialog."""
        try:
            dialog = ThumbnailSelectorDialog(parent=self)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Error opening thumbnail selector dialog: {e}")
            self._show_error("Thumbnail Selector Error", f"Could not open thumbnail selector: {str(e)}")
    
    @requires_feature_qt(Feature.VEO_VIDEO_GENERATOR)
    @requires_usage_qt('videos', 1)
    def _on_open_veo_generator(self):
        """Open the Veo video generator."""
        try:
            # For now, open the simple Veo widget in a message box style dialog
            from PySide6.QtWidgets import QDialog, QVBoxLayout
            from ..components.simple_veo_widget import SimpleVeoWidget
            
            dialog = QDialog(self)
            dialog.setWindowTitle("🎬 Veo Video Generator")
            dialog.setFixedSize(600, 500)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #1a1a1a;
                    color: #FFFFFF;
                }
            """)
            
            layout = QVBoxLayout(dialog)
            veo_widget = SimpleVeoWidget()
            layout.addWidget(veo_widget)
            
            dialog.exec()
            
        except Exception as e:
            self.logger.error(f"Error opening Veo generator: {e}")
            self._show_error("Veo Generator Error", f"Could not open Veo video generator: {str(e)}")
    
    @requires_feature_qt(Feature.AUDIO_IMPORTER)
    def _on_open_audio_overlay(self):
        """Open the audio overlay dialog."""
        try:
            dialog = AudioOverlayDialog(parent=self)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Error opening audio overlay dialog: {e}")
            self._show_error("Audio Overlay Error", f"Could not open audio overlay: {str(e)}")
    
    @requires_feature_qt(Feature.PERFORMANCE_ANALYTICS)
    def _on_open_analytics_dashboard(self):
        """Open the analytics dashboard dialog."""
        try:
            from .dialogs.analytics_dashboard_dialog import AnalyticsDashboardDialog
            dialog = AnalyticsDashboardDialog(self)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Error opening analytics dashboard: {e}")
            self._show_error("Analytics Error", f"Could not open analytics dashboard: {str(e)}")
    
    def _on_open_custom_upload(self):
        """Open the custom media upload dialog."""
        try:
            dialog = CustomMediaUploadDialog(self)
            dialog.upload_completed.connect(self._on_custom_upload_completed)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Error opening custom upload dialog: {e}")
            self._show_error("Upload Error", f"Could not open custom media upload: {str(e)}")
    
    def _on_custom_upload_completed(self, success: bool, message: str):
        """Handle completion of custom media upload."""
        try:
            if success:
                self.status_bar.showMessage(f"Upload successful: {message}", 5000)
                self._show_info("Upload Complete", message)
            else:
                self.status_bar.showMessage(f"Upload failed: {message}", 5000)
                self._show_error("Upload Failed", message)
        except Exception as e:
            self.logger.error(f"Error handling upload completion: {e}")
    
    def _on_post_current_media(self):
        """Post the currently selected media to social platforms."""
        try:
            # Get the currently displayed media path
            media_path = self.media_section.get_current_display_path()
            
            if not media_path:
                self._show_warning("No Media", "No media is currently selected. Please select media first or use 'Upload Custom Media' to upload new content.")
                return
            
            # Get the current caption
            caption = self.text_sections.get_text("caption")
            
            # Open custom upload dialog with pre-filled data
            dialog = CustomMediaUploadDialog(self)
            
            # Pre-load the current media and caption
            dialog._load_media_file(media_path)
            if caption:
                dialog.caption_text.setPlainText(caption)
            
            dialog.upload_completed.connect(self._on_custom_upload_completed)
            dialog.exec()
            
        except Exception as e:
            self.logger.error(f"Error posting current media: {e}")
            self._show_error("Post Error", f"Could not post current media: {str(e)}")