"""
Application state model.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class AppState:
    """
    Stores the application state.
    Acts as a central data store for UI and business logic components.
    """
    
    # Selected media file
    selected_media: Optional[str] = None
    
    # Media status information
    media_status: Dict[str, Any] = field(default_factory=dict)
    
    # Operation status
    is_processing: bool = False
    
    # Meta API credentials
    meta_credentials: Optional[Dict[str, str]] = None
    
    # Generation status tracking
    generation_requests: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Scheduling data
    schedules: List[Dict[str, Any]] = field(default_factory=list)
    scheduled_posts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Library settings
    library_last_updated: Optional[datetime] = None
    
    # Current caption
    current_caption: Optional[str] = None
    
    # Photo editing instructions
    photo_editing_instructions: Optional[str] = None
    
    # Context files
    context_files: List[str] = field(default_factory=list)
    
    # Current display media path (could be original or edited)
    current_display_media: Optional[str] = None
    
    # Path to edited version of media
    edited_media: Optional[str] = None
    
    # Flag indicating if edited version is being shown
    showing_edited: bool = False
    
    # Flag for dark mode
    dark_mode: bool = False
    
    # Last directory used for file operations
    last_directory: Optional[str] = None
    
    def __init__(self):
        """Initialize the application state."""
        # Current media path
        self.selected_media = None
        
        # Current display media path (could be original or edited)
        self.current_display_media = None
        
        # Path to edited version of media
        self.edited_media = None
        
        # Flag indicating if edited version is being shown
        self.showing_edited = False
        
        # Current caption
        self.current_caption = ""
        
        # Photo editing instructions
        self.photo_editing_instructions = ""
        
        # Context files
        self.context_files = []
        
        # Meta credentials (if authenticated)
        self.meta_credentials = None
        
        # Library last updated timestamp
        self.library_last_updated = None
        
        # Flag for dark mode
        self.dark_mode = False
        
        # Last directory used for file operations
        self.last_directory = None
        
        # Scheduling data
        self.schedules = []
        self.scheduled_posts = []
        
    def reset(self):
        """Reset application state to defaults."""
        self.selected_media = None
        self.current_display_media = None
        self.edited_media = None
        self.showing_edited = False
        self.current_caption = ""
        self.photo_editing_instructions = ""
        self.context_files = []
        self.last_directory = None
        
    def save_to_file(self, file_path):
        """
        Save application state to a file.
        
        Args:
            file_path: File path to save state to
        """
        # Create a dictionary of all serializable properties
        state_dict = {
            "selected_media": self.selected_media,
            "current_display_media": self.current_display_media,
            "edited_media": self.edited_media,
            "showing_edited": self.showing_edited,
            "current_caption": self.current_caption,
            "photo_editing_instructions": self.photo_editing_instructions,
            "context_files": self.context_files,
            "dark_mode": self.dark_mode,
            "last_directory": self.last_directory
        }
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(state_dict, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving application state: {e}")
            return False
            
    def load_from_file(self, file_path):
        """
        Load application state from a file.
        
        Args:
            file_path: File path to load state from
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                state_dict = json.load(f)
                
            # Update properties from the loaded dictionary
            for key, value in state_dict.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    
            return True
        except Exception as e:
            print(f"Error loading application state: {e}")
            return False
        
    def update_selected_media(self, path: str) -> None:
        """Update the selected media path."""
        self.selected_media = path
        
    def start_processing(self) -> None:
        """Mark the application as processing."""
        self.is_processing = True
        
    def stop_processing(self) -> None:
        """Mark the application as not processing."""
        self.is_processing = False
        
    def add_generation_request(self, request_id: str, data: Dict[str, Any]) -> None:
        """Add a generation request to the tracking dictionary."""
        self.generation_requests[request_id] = {
            **data,
            "start_time": datetime.now().isoformat(),
            "status": "pending"
        }
        
    def update_generation_status(self, request_id: str, status: str, result: Any = None) -> None:
        """Update the status of a generation request."""
        if request_id in self.generation_requests:
            self.generation_requests[request_id].update({
                "status": status,
                "end_time": datetime.now().isoformat() if status in ("completed", "failed") else None,
                "result": result
            })
            
    def reset_state(self) -> None:
        """Reset the application state to defaults."""
        self.selected_media = None
        self.is_processing = False
        self.context_files = []
        self.photo_editing_instructions = None
        self.current_caption = None
        # Keep other data like credentials, schedules, etc. 