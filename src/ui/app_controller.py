"""
Application Controller - Manages navigation between different UI components.
"""
import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QMessageBox
from PySide6.QtCore import QObject, Signal

from .dashboard_window import DashboardWindow
from .components.library_tabs import LibraryTabs
from .components.campaign_manager import CampaignManager
from .components.tools_container import ToolsContainer
from .dialogs.create_post_dialog import CreatePostDialog
from .dialogs.unified_connection_dialog import UnifiedConnectionDialog
from .dialogs.custom_media_upload_dialog import CustomMediaUploadDialog
from .dialogs.highlight_reel_dialog import HighlightReelDialog
from .dialogs.story_assistant_dialog import StoryAssistantDialog
from .dialogs.thumbnail_selector_dialog import ThumbnailSelectorDialog
from .dialogs.audio_overlay_dialog import AudioOverlayDialog
from .dialogs.analytics_dashboard_dialog import AnalyticsDashboardDialog
from .dialogs.compliance_dialog import ComplianceDialog
from .dialogs.image_edit_dialog import ImageEditDialog
from .dialogs.video_processing_dialog import VideoProcessingDialog
from .dialogs.gallery_creation_dialog import GalleryCreationDialog
from .dialogs.scheduling_dialog import ScheduleDialog
from .knowledge_management import KnowledgeManagementDialog
from .preset_manager import PresetManager
from ..models.app_state import AppState
from ..handlers.media_handler import MediaHandler
from ..handlers.library_handler import LibraryManager

class AppController(QWidget):
    """Main application controller that manages navigation between features."""
    
    def __init__(self, app_state: AppState, media_handler: MediaHandler, 
                 library_manager: LibraryManager, parent=None):
        super().__init__(parent)
        
        self.app_state = app_state
        self.media_handler = media_handler
        self.library_manager = library_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Current windows/dialogs
        self.current_dialog = None
        
        self._setup_ui()
        self._connect_signals()
        
        self.logger.info("App controller initialized")
        
    def _setup_ui(self):
        """Set up the main UI with stacked widget for navigation."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for different views
        self.stacked_widget = QStackedWidget()
        
        # Create main components
        self._create_dashboard()
        self._create_library_view()
        self._create_campaign_manager_view()
        self._create_tools_view()
        
        layout.addWidget(self.stacked_widget)
        
        # Start with dashboard
        self.show_dashboard()
        
    def _create_dashboard(self):
        """Create the dashboard view."""
        self.dashboard = DashboardWindow(
            self.app_state, 
            self.media_handler, 
            self.library_manager
        )
        self.stacked_widget.addWidget(self.dashboard)
        
    def _create_library_view(self):
        """Create the library view."""
        # Simple wrapper widget for library
        library_widget = QWidget()
        library_layout = QVBoxLayout(library_widget)
        library_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add home button at top
        from PySide6.QtWidgets import QHBoxLayout, QPushButton, QLabel
        from PySide6.QtGui import QFont
        
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Library")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #000000; margin: 20px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        home_btn = QPushButton("🏠 Home")
        home_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                margin: 20px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        home_btn.clicked.connect(self.show_dashboard)
        header_layout.addWidget(home_btn)
        
        library_layout.addLayout(header_layout)
        
        # Add library tabs
        self.library_tabs = LibraryTabs()
        library_layout.addWidget(self.library_tabs)
        
        self.stacked_widget.addWidget(library_widget)
        
    def _create_campaign_manager_view(self):
        """Create the campaign manager view."""
        # Simple wrapper widget for campaign manager
        campaign_widget = QWidget()
        campaign_layout = QVBoxLayout(campaign_widget)
        campaign_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add home button at top
        from PySide6.QtWidgets import QHBoxLayout, QPushButton
        
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        
        home_btn = QPushButton("🏠 Home")
        home_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                margin: 20px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        home_btn.clicked.connect(self.show_dashboard)
        header_layout.addWidget(home_btn)
        
        campaign_layout.addLayout(header_layout)
        
        # Add campaign manager
        self.campaign_manager = CampaignManager()
        campaign_layout.addWidget(self.campaign_manager)
        
        self.stacked_widget.addWidget(campaign_widget)
        
    def _create_tools_view(self):
        """Create the tools view."""
        # Simple wrapper widget for tools
        tools_widget = QWidget()
        tools_layout = QVBoxLayout(tools_widget)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add home button at top
        from PySide6.QtWidgets import QHBoxLayout, QPushButton, QLabel
        from PySide6.QtGui import QFont
        
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Tools")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #000000; margin: 20px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        home_btn = QPushButton("🏠 Home")
        home_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                margin: 20px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        home_btn.clicked.connect(self.show_dashboard)
        header_layout.addWidget(home_btn)
        
        tools_layout.addLayout(header_layout)
        
        # Add tools container
        self.tools_container = ToolsContainer()
        tools_layout.addWidget(self.tools_container)
        
        self.stacked_widget.addWidget(tools_widget)
        
    def _connect_signals(self):
        """Connect signals from components."""
        # Dashboard signals
        self.dashboard.create_post_requested.connect(self._on_create_post_requested)
        self.dashboard.library_requested.connect(self.show_library)
        self.dashboard.campaign_manager_requested.connect(self.show_campaign_manager)
        self.dashboard.tools_requested.connect(self.show_tools)
        self.dashboard.presets_requested.connect(self._on_presets_requested)
        self.dashboard.customer_handler_requested.connect(self._on_customer_handler_requested)
        self.dashboard.data_requested.connect(self._on_data_requested)
        
        # Library signals
        self.library_tabs.create_gallery_requested.connect(self._on_create_gallery_requested)
        self.library_tabs.media_uploaded.connect(self._on_media_uploaded)
        
        # Campaign manager signals
        self.campaign_manager.add_campaign_requested.connect(self._on_add_campaign_requested)
        self.campaign_manager.edit_campaign_requested.connect(self._on_edit_campaign_requested)
        self.campaign_manager.delete_campaign_requested.connect(self._on_delete_campaign_requested)
        
        # Tools signals
        self.tools_container.highlight_reel_requested.connect(self._on_highlight_reel_requested)
        self.tools_container.story_assistant_requested.connect(self._on_story_assistant_requested)
        self.tools_container.thumbnail_selector_requested.connect(self._on_thumbnail_selector_requested)
        self.tools_container.veo_generator_requested.connect(self._on_veo_generator_requested)
        self.tools_container.audio_overlay_requested.connect(self._on_audio_overlay_requested)
        self.tools_container.performance_dashboard_requested.connect(self._on_performance_dashboard_requested)
        self.tools_container.export_data_requested.connect(self._on_export_data_requested)
        self.tools_container.compliance_requested.connect(self._on_compliance_requested)
        self.tools_container.connect_accounts_requested.connect(self._on_connect_accounts_requested)
        self.tools_container.custom_upload_requested.connect(self._on_custom_upload_requested)
        self.tools_container.post_current_media_requested.connect(self._on_post_current_media_requested)
        self.tools_container.knowledge_base_requested.connect(self._on_knowledge_base_requested)
        
    def show_dashboard(self):
        """Show the main dashboard."""
        self.stacked_widget.setCurrentWidget(self.dashboard)
        self.logger.info("Showing dashboard")
        
    def show_library(self):
        """Show the library view."""
        self.stacked_widget.setCurrentIndex(1)  # Library is at index 1
        self.library_tabs.refresh_content()
        self.logger.info("Showing library")
        
    def show_campaign_manager(self):
        """Show the campaign manager view."""
        self.stacked_widget.setCurrentIndex(2)  # Campaign manager is at index 2
        
        # Add some sample campaigns for demonstration
        if not self.campaign_manager.campaigns:
            sample_campaigns = [
                {
                    'name': 'Summer Product Launch',
                    'active': True,
                    'post_count': 12,
                    'schedule': 'Daily at 9 AM'
                },
                {
                    'name': 'Holiday Marketing',
                    'active': False,
                    'post_count': 8,
                    'schedule': 'Twice weekly'
                },
                {
                    'name': 'Brand Awareness',
                    'active': True,
                    'post_count': 5,
                    'schedule': 'Weekly on Mondays'
                }
            ]
            self.campaign_manager.set_campaigns(sample_campaigns)
        
        self.logger.info("Showing campaign manager")
        
    def show_tools(self):
        """Show the tools view."""
        self.stacked_widget.setCurrentIndex(3)  # Tools is at index 3
        self.logger.info("Showing tools")
        
    def _on_create_post_requested(self):
        """Handle create post request."""
        self.logger.info("Create post requested")
        
        # Show create post dialog
        dialog = CreatePostDialog(self)
        dialog.upload_photo_requested.connect(self._on_upload_photo_requested)
        dialog.upload_video_requested.connect(self._on_upload_video_requested)
        dialog.create_media_requested.connect(self._on_create_media_requested)
        dialog.create_gallery_requested.connect(self._on_create_gallery_from_dialog)
        dialog.text_post_requested.connect(self._on_text_post_requested)
        
        self.current_dialog = dialog
        dialog.exec()
        
    def _on_upload_photo_requested(self, file_path: str):
        """Handle photo upload request."""
        self.logger.info(f"Photo upload requested: {file_path}")
        
        # Open the comprehensive post creation dialog
        from .dialogs.post_creation_dialog import PostCreationDialog
        
        dialog = PostCreationDialog(media_path=file_path, parent=self)
        dialog.post_created.connect(self._on_post_created)
        
        if dialog.exec():
            self.logger.info("Post creation completed")
        else:
            self.logger.info("Post creation cancelled")
    
    def _on_post_created(self, item_id: str):
        """Handle post creation completion."""
        self.logger.info(f"Post created: {item_id}")
        
        # Refresh library tabs if they're currently visible
        if hasattr(self, 'library_tabs'):
            self.library_tabs.refresh_content()
        
        # Optionally show the library to see the saved post
        reply = QMessageBox.question(
            self,
            "Post Created",
            "Your post has been created and saved to the library!\n\nWould you like to view the library now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.show_library()
    
    def _on_photo_workflow_completed(self, item_id: str):
        """Handle photo workflow completion."""
        self.logger.info(f"Photo workflow completed: {item_id}")
        
        # Optionally show the library to see the saved image
        reply = QMessageBox.question(
            self,
            "Photo Saved",
            "Your photo has been saved to the library!\n\nWould you like to view the library now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.show_library()
    
    def _on_photo_workflow_cancelled(self):
        """Handle photo workflow cancellation."""
        self.logger.info("Photo workflow cancelled")
    
    def _on_image_edit_confirmed(self, image_path: str, instructions: str):
        """Handle image edit confirmation."""
        try:
            from ..features.media_processing.image_edit_handler import ImageEditHandler
            from ..handlers.library_handler import LibraryManager
            
            # Apply the image edits
            image_handler = ImageEditHandler()
            success, edited_path, message = image_handler.edit_image_with_gemini(image_path, instructions)
            
            if success and edited_path:
                # Save the edited image to library
                library_manager = LibraryManager()
                
                # Load the edited image
                from PIL import Image
                edited_image = Image.open(edited_path)
                
                # Add to library as post-ready
                item_id = library_manager.add_image_item(
                    edited_image, 
                    caption="", 
                    is_post_ready=True,
                    metadata={"original_path": image_path, "edit_instructions": instructions}
                )
                
                if item_id:
                    self.logger.info(f"Edited image saved to library with ID: {item_id}")
                    QMessageBox.information(
                        self,
                        "Image Saved",
                        f"Your edited image has been saved to the library!\n\nYou can find it in the 'Finished Posts' section."
                    )
                else:
                    self.logger.warning("Failed to save edited image to library")
                    QMessageBox.warning(
                        self,
                        "Save Warning", 
                        "Image was edited but could not be saved to library. Please check the library settings."
                    )
            else:
                self.logger.error(f"Image editing failed: {message}")
                QMessageBox.critical(
                    self,
                    "Edit Failed",
                    f"Failed to edit image:\n\n{message}"
                )
                
        except Exception as e:
            self.logger.error(f"Error handling image edit: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while processing the image:\n\n{str(e)}"
            )
        
    def _on_upload_video_requested(self, file_path: str):
        """Handle video upload request."""
        self.logger.info(f"Video upload requested: {file_path}")
        
        # First show video editing services dialog
        from .dialogs.video_editing_services_dialog import VideoEditingServicesDialog
        
        services_dialog = VideoEditingServicesDialog(file_path, self)
        selected_services = {}
        
        if services_dialog.exec():
            # User selected some services
            selected_services = services_dialog.get_selected_services()
            self.logger.info(f"Video services selected: {selected_services}")
        else:
            # User skipped all services
            self.logger.info("Video services skipped")
        
        final_video_path = file_path
        
        # If services were selected, show the step-by-step processing pipeline
        if selected_services and any(selected_services.values()):
            from .dialogs.video_processing_pipeline_dialog import VideoProcessingPipelineDialog
            
            pipeline_dialog = VideoProcessingPipelineDialog(file_path, selected_services, self)
            
            if pipeline_dialog.exec():
                # User completed the pipeline
                final_video_path = pipeline_dialog.get_final_video_path()
                self.logger.info(f"Video processing pipeline completed: {final_video_path}")
            else:
                # User cancelled the pipeline, use original video
                self.logger.info("Video processing pipeline cancelled, using original video")
        
        # Now open the comprehensive post creation dialog with the final video
        from .dialogs.post_creation_dialog import PostCreationDialog
        
        dialog = PostCreationDialog(media_path=final_video_path, parent=self)
        
        # Store the selected services in the dialog for later use
        if hasattr(dialog, 'selected_video_services'):
            dialog.selected_video_services = selected_services
        else:
            # Add the attribute if it doesn't exist
            dialog.selected_video_services = selected_services
        
        dialog.post_created.connect(self._on_post_created)
        
        if dialog.exec():
            self.logger.info("Video post creation completed")
        else:
            self.logger.info("Video post creation cancelled")
        
    def _on_create_media_requested(self, media_type: str):
        """Handle AI media creation request."""
        self.logger.info(f"AI media creation requested: {media_type}")
        
        # Import the create media dialog
        from .dialogs.create_media_dialog import CreateMediaDialog
        
        # Open create media dialog with the specified type
        dialog = CreateMediaDialog(media_type=media_type, parent=self)
        if dialog.exec():
            self.logger.info(f"AI {media_type} creation completed")
        else:
            self.logger.info(f"AI {media_type} creation cancelled")
        
    def _on_create_gallery_from_dialog(self):
        """Handle create gallery request from dialog - redirect to library."""
        self.logger.info("Create gallery requested from dialog - redirecting to library")
        self.show_library()
        
    def _on_text_post_requested(self):
        """Handle text post request."""
        self.logger.info("Text post requested")
        
        # Import the post options dialog for text posts
        from .dialogs.post_options_dialog import PostOptionsDialog
        
        # Open post options dialog for text post
        dialog = PostOptionsDialog(post_type="text", parent=self)
        if dialog.exec():
            self.logger.info("Text post creation completed")
        else:
            self.logger.info("Text post creation cancelled")
        
    def _on_customer_handler_requested(self):
        """Handle customer handler request."""
        self.logger.info("Customer handler requested")
        
        # Open knowledge management system
        dialog = KnowledgeManagementDialog(self)
        dialog.exec()
        
    def _on_data_requested(self):
        """Handle data/analytics request."""
        self.logger.info("Data/analytics requested")
        
        # Open analytics dashboard
        dialog = AnalyticsDashboardDialog(self)
        dialog.exec()
        
    def _on_presets_requested(self):
        """Handle presets management request."""
        self.logger.info("Presets management requested")
        
        # Open preset manager dialog
        from .dialogs.preset_manager_dialog import PresetManagerDialog
        dialog = PresetManagerDialog(self)
        dialog.exec()
        
    def _on_create_gallery_requested(self):
        """Handle create gallery request."""
        self.logger.info("Create gallery requested")
        
        # Open gallery creation dialog
        dialog = GalleryCreationDialog(self)
        if dialog.exec():
            self.logger.info("Gallery creation completed")
        else:
            self.logger.info("Gallery creation cancelled")
        
    def _on_add_campaign_requested(self):
        """Handle add campaign request."""
        self.logger.info("Add campaign requested")
        
        # Open scheduling dialog for campaign creation
        dialog = ScheduleDialog(self)
        if dialog.exec():
            self.logger.info("Campaign creation completed")
            # Refresh campaign manager
            self.campaign_manager.refresh_campaigns()
        else:
            self.logger.info("Campaign creation cancelled")
        
    def _on_edit_campaign_requested(self, campaign_data: Dict[str, Any]):
        """Handle edit campaign request."""
        self.logger.info(f"Edit campaign requested: {campaign_data}")
        
        # Open scheduling dialog for campaign editing
        dialog = ScheduleDialog(self, campaign_data)
        if dialog.exec():
            self.logger.info("Campaign editing completed")
            # Refresh campaign manager
            self.campaign_manager.refresh_campaigns()
        else:
            self.logger.info("Campaign editing cancelled")
        
    def _on_delete_campaign_requested(self, campaign_data: Dict[str, Any]):
        """Handle delete campaign request."""
        self.logger.info(f"Delete campaign requested: {campaign_data}")
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self, 
            "Delete Campaign", 
            f"Are you sure you want to delete the campaign '{campaign_data.get('name', 'Unknown')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.campaign_manager.remove_campaign(campaign_data)
            self.logger.info("Campaign deleted")
            
    # Tool handler methods
    def _on_highlight_reel_requested(self):
        """Handle highlight reel generator request."""
        self.logger.info("Highlight reel generator requested")
        
        # Open highlight reel dialog
        dialog = HighlightReelDialog(self)
        if dialog.exec():
            self.logger.info("Highlight reel generation completed")
        else:
            self.logger.info("Highlight reel generation cancelled")
        
    def _on_story_assistant_requested(self):
        """Handle story assistant request."""
        self.logger.info("Story assistant requested")
        
        # Open story assistant dialog
        dialog = StoryAssistantDialog(self)
        if dialog.exec():
            self.logger.info("Story assistant completed")
        else:
            self.logger.info("Story assistant cancelled")
        
    def _on_thumbnail_selector_requested(self):
        """Handle thumbnail selector request."""
        self.logger.info("Thumbnail selector requested")
        
        # Open thumbnail selector dialog
        dialog = ThumbnailSelectorDialog(self)
        if dialog.exec():
            self.logger.info("Thumbnail selection completed")
        else:
            self.logger.info("Thumbnail selection cancelled")
        
    def _on_veo_generator_requested(self):
        """Handle Veo generator request."""
        self.logger.info("Veo generator requested")
        
        # Open Veo generator dialog
        try:
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
            QMessageBox.critical(self, "Veo Generator Error", f"Could not open Veo video generator: {str(e)}")
        
    def _on_audio_overlay_requested(self):
        """Handle audio overlay request."""
        self.logger.info("Audio overlay requested")
        
        # Open audio overlay dialog
        dialog = AudioOverlayDialog(self)
        if dialog.exec():
            self.logger.info("Audio overlay completed")
        else:
            self.logger.info("Audio overlay cancelled")
        
    def _on_performance_dashboard_requested(self):
        """Handle performance dashboard request."""
        self.logger.info("Performance dashboard requested")
        
        # Open analytics dashboard
        dialog = AnalyticsDashboardDialog(self)
        dialog.exec()
        
    def _on_export_data_requested(self):
        """Handle export data request."""
        self.logger.info("Export data requested")
        
        # Open analytics dashboard with focus on export functionality
        dialog = AnalyticsDashboardDialog(self)
        dialog.exec()
        
    def _on_compliance_requested(self):
        """Handle compliance request."""
        self.logger.info("Compliance requested")
        
        # Open compliance dialog
        dialog = ComplianceDialog(self)
        dialog.exec()
        
    def _on_connect_accounts_requested(self):
        """Handle connect accounts request."""
        self.logger.info("Connect accounts requested")
        
        # Open unified connection dialog
        dialog = UnifiedConnectionDialog(self)
        dialog.exec()
        
    def _on_custom_upload_requested(self):
        """Handle custom upload request."""
        self.logger.info("Custom upload requested")
        
        # Open custom media upload dialog
        dialog = CustomMediaUploadDialog(self)
        if dialog.exec():
            self.logger.info("Custom upload completed")
        else:
            self.logger.info("Custom upload cancelled")
        
    def _on_post_current_media_requested(self):
        """Handle post current media request."""
        self.logger.info("Post current media requested")
        
        # Check if there's current media loaded
        if hasattr(self.app_state, 'selected_media') and self.app_state.selected_media:
            # Import the post options dialog for current media
            from .dialogs.post_options_dialog import PostOptionsDialog
            
            # Open post options dialog for current media
            dialog = PostOptionsDialog(post_type="media", media_path=self.app_state.selected_media, parent=self)
            if dialog.exec():
                self.logger.info("Post current media completed")
            else:
                self.logger.info("Post current media cancelled")
        else:
            QMessageBox.information(
                self, 
                "No Media Selected", 
                "Please select or load media first before posting.\n\n"
                "You can:\n"
                "• Upload media from the Create Post option\n"
                "• Generate media using AI tools\n"
                "• Load media from your library"
            )
        
    def _on_knowledge_base_requested(self):
        """Handle knowledge base request."""
        self.logger.info("Knowledge base requested")
        
        # Open knowledge management system
        dialog = KnowledgeManagementDialog(self)
        dialog.exec()
    
    def _on_media_uploaded(self):
        """Handle media uploaded signal."""
        self.logger.info("Media uploaded signal received")
        self.show_library()
    
    def closeEvent(self, event):
        """Handle close event."""
        self.logger.info("App controller closing")
        event.accept() 