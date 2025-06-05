"""
Library Manager for handling media library items.
Consolidates functionality from library_manager.py and related files.
"""
import os
import json
import uuid
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from PIL import Image

from src.config import constants # Added import
from src.handlers.media_handler import MediaHandler  # Add MediaHandler import
from src.models.app_state import AppState  # Import AppState

# Define a minimal mock AppState for MediaHandler
class MockAppState:
    """Minimal AppState for MediaHandler to use in LibraryManager."""
    def __init__(self):
        self.media_generation_status = {}
        self.selected_media = None
        self.edited_media = None
        self.current_display_media = None
        self.showing_edited = False
        self.current_caption = ""
        self.context_files = []
        
class LibraryManager:
    """Manages the media library functionality."""
    
    def __init__(self):
        """Initialize the library manager."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Define library paths
        self.library_dir = Path("library")
        self.images_dir = self.library_dir / "images"
        self.data_dir = self.library_dir / "data"
        self.library_file = self.data_dir / "library.json"
        
        # Ensure directories exist
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load library data
        self.library_data = self._load_library_data()
        
        # Create a media handler instance with a mock AppState
        mock_app_state = MockAppState()
        self.media_handler = MediaHandler(mock_app_state)
        
    def _load_library_data(self) -> Dict[str, Any]:
        """Load library data from the JSON file."""
        try:
            if self.library_file.exists():
                with open(self.library_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Initialize with empty structure
                initial_data = {
                    "version": "1.0",
                    "items": {},
                    "collections": {}
                }
                self._save_library_data(initial_data)
                return initial_data
                
        except Exception as e:
            self.logger.error(f"Error loading library data: {e}")
            # Return empty structure on error
            return {
                "version": "1.0",
                "items": {},
                "collections": {}
            }
            
    def _save_library_data(self, data: Dict[str, Any]) -> bool:
        """Save library data to the JSON file."""
        try:
            with open(self.library_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Error saving library data: {e}")
            return False
            
    def add_item_from_path(self, file_path: str, caption: str = "", 
                         date_added: str = None, metadata: dict = None, 
                         is_post_ready: bool = False) -> Optional[Dict[str, Any]]:
        """
        Add an item to the library from a file path.
        
        Args:
            file_path: Path to the image file
            caption: Caption text for the image
            date_added: ISO format date string (defaults to now)
            metadata: Additional metadata for the item
            is_post_ready: Flag to mark item as post-ready (photo or video)
            
        Returns:
            dict: Item data of the added item, or None on failure
        """
        try:
            # Determine base item type (photo or video)
            base_item_type = "unknown"
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext in constants.SUPPORTED_IMAGE_FORMATS:
                base_item_type = "photo"
            elif file_ext in constants.SUPPORTED_VIDEO_FORMATS:
                base_item_type = "video"
            else:
                self.logger.warning(f"Unsupported file type for {file_path}: {file_ext}")
                return None

            # Determine final item_type based on is_post_ready
            item_type = "unknown"
            if is_post_ready:
                if base_item_type == "photo":
                    item_type = "post_ready_photo"
                elif base_item_type == "video":
                    item_type = "post_ready_video"
                if not caption:
                    self.logger.warning(f"Adding post-ready item {file_path} without a caption.")
            else:
                if base_item_type == "photo":
                    item_type = "raw_photo"
                elif base_item_type == "video":
                    item_type = "raw_video"
            
            if item_type == "unknown": # Should not happen if base_item_type is photo/video
                self.logger.error(f"Could not determine item type for {file_path}")
                return None

            # Process based on base type (photo or video)
            if base_item_type == "photo":
                with Image.open(file_path) as img:
                    item_id = str(uuid.uuid4())
                    filename = f"{item_id}{file_ext}" 
                    dest_path = self.images_dir / filename
                    shutil.copy2(file_path, dest_path)
                    width, height = img.size
                    item_metadata = {"original_mode": img.mode}
            elif base_item_type == "video":
                item_id = str(uuid.uuid4())
                filename = f"{item_id}{file_ext}" 
                dest_path = self.images_dir / filename
                shutil.copy2(file_path, dest_path)
                width, height = None, None 
                item_metadata = {}
            else: # Should be caught by earlier checks
                self.logger.error(f"Internal error: Unexpected base_item_type {base_item_type}")
                return None

            if metadata and isinstance(metadata, dict):
                item_metadata.update(metadata)
            
            item_data = {
                "id": item_id,
                "type": item_type, # Updated type field
                "filename": filename,
                "path": str(dest_path.absolute()),
                "caption": caption,
                "date_added": date_added or datetime.now().isoformat(),
                "tags": [],
                "dimensions": [width, height],
                "size_str": f"{os.path.getsize(dest_path) / 1024:.1f} KB",
                "metadata": item_metadata
            }
            
            # Add to library data
            self.library_data["items"][item_id] = item_data
            
            # Save library data
            self._save_library_data(self.library_data)
            
            return item_data
                
        except Exception as e:
            self.logger.error(f"Error adding item from path to library: {e}")
            return None
            
    def add_item(self, image: Image.Image, caption: str = "", 
                date_added: str = None, metadata: dict = None, 
                is_post_ready: bool = False) -> Optional[str]:
        """
        Add an item to the library.
        
        Args:
            image: PIL Image object (implies it's a photo)
            caption: Caption text for the image
            date_added: ISO format date string (defaults to now)
            metadata: Additional metadata for the item
            is_post_ready: Flag to mark item as post-ready photo
            
        Returns:
            str: Item ID if successful, None otherwise
        """
        try:
            # Determine item type based on is_post_ready
            item_type = "post_ready_photo" if is_post_ready else "raw_photo"
            
            # Generate unique ID and filename
            item_id = str(uuid.uuid4())
            filename = f"{item_id}.png"  # Save as PNG to preserve quality
            dest_path = self.images_dir / filename
            
            # Save image
            image.save(dest_path, "PNG")
            
            # Get image dimensions
            width, height = image.size
            
            # Prepare metadata
            item_metadata = {"original_mode": image.mode}
            if metadata and isinstance(metadata, dict):
                item_metadata.update(metadata)
            
            # Create item data
            item_data = {
                "id": item_id,
                "type": item_type,
                "filename": filename,
                "path": str(dest_path.absolute()),
                "caption": caption,
                "date_added": date_added or datetime.now().isoformat(),
                "tags": [],
                "dimensions": [width, height],
                "size_str": f"{os.path.getsize(dest_path) / 1024:.1f} KB",
                "metadata": item_metadata
            }
            
            # Add to library data
            self.library_data["items"][item_id] = item_data
            
            # Save library data
            self._save_library_data(self.library_data)
            
            return item_id
                
        except Exception as e:
            self.logger.error(f"Error adding item to library: {e}")
            return None

    def add_image_item(self, image: Image.Image, caption: str = "", 
                      date_added: str = None, metadata: dict = None, 
                      is_post_ready: bool = False) -> Optional[str]:
        """
        Add an image item to the library (alias for add_item for backward compatibility).
        
        Args:
            image: PIL Image object
            caption: Caption text for the image
            date_added: ISO format date string (defaults to now)
            metadata: Additional metadata for the item
            is_post_ready: Flag to mark item as post-ready photo
            
        Returns:
            str: Item ID if successful, None otherwise
        """
        return self.add_item(image, caption, date_added, metadata, is_post_ready)
            
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an item from the library.
        
        Args:
            item_id: ID of the item
            
        Returns:
            dict: Item data, or None if not found
        """
        try:
            item = self.library_data["items"].get(item_id)
            if item:
                # Ensure path is set
                if "path" not in item and "filename" in item:
                    file_path = self.images_dir / item["filename"]
                    item["path"] = str(file_path.absolute())
                
                # Ensure dimensions and size are set
                if "dimensions" not in item and "path" in item:
                    try:
                        with Image.open(item["path"]) as img:
                            item["dimensions"] = [img.width, img.height]
                    except:
                        pass
                        
                if "size_str" not in item and "path" in item:
                    try:
                        size_bytes = os.path.getsize(item["path"])
                        item["size_str"] = f"{size_bytes / 1024:.1f} KB"
                    except:
                        pass
                        
            return item
        except Exception as e:
            self.logger.error(f"Error getting item {item_id}: {e}")
            return None
            
    def get_all_items(self) -> List[Dict[str, Any]]:
        """
        Get all items from the library.
        
        Returns:
            list: List of all item data
        """
        try:
            items = list(self.library_data["items"].values())
            
            # Ensure all items have path, dimensions, and size info
            for item in items:
                # Add path if missing
                if "path" not in item and "filename" in item:
                    file_path = self.images_dir / item["filename"]
                    item["path"] = str(file_path.absolute())
                
                # Add dimensions if missing
                if "dimensions" not in item and "path" in item:
                    try:
                        with Image.open(item["path"]) as img:
                            item["dimensions"] = [img.width, img.height]
                    except:
                        item["dimensions"] = [0, 0]
                
                # Add size if missing
                if "size_str" not in item and "path" in item:
                    try:
                        size_bytes = os.path.getsize(item["path"])
                        item["size_str"] = f"{size_bytes / 1024:.1f} KB"
                    except:
                        item["size_str"] = "Unknown"
            
            # Sort by date added (newest first)
            items.sort(key=lambda x: x.get("date_added", ""), reverse=True)
            return items
        except Exception as e:
            self.logger.error(f"Error getting all items: {e}")
            return []
            
    def update_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an item in the library.
        
        Args:
            item_id: ID of the item
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if item_id in self.library_data["items"]:
                # Update specified fields
                for key, value in updates.items():
                    self.library_data["items"][item_id][key] = value
                
                # Save library data
                return self._save_library_data(self.library_data)
            return False
        except Exception as e:
            self.logger.error(f"Error updating item {item_id}: {e}")
            return False
            
    def remove_item(self, item_id: str) -> bool:
        """
        Remove an item from the library.
        
        Args:
            item_id: ID of the item to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if item exists
            if item_id not in self.library_data["items"]:
                self.logger.warning(f"Item not found: {item_id}")
                return False
                
            # Get the item
            item = self.library_data["items"][item_id]
            
            # Delete the image file if it exists
            if "filename" in item:
                file_path = self.images_dir / item["filename"]
                if file_path.exists():
                    file_path.unlink()
                    self.logger.info(f"Deleted image file: {file_path}")
                    
            # Remove from library data
            del self.library_data["items"][item_id]
            
            # Save library data
            self._save_library_data(self.library_data)
            
            self.logger.info(f"Removed item from library: {item_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing item: {e}")
            return False
            
    def get_image_path(self, item_id: str) -> Optional[str]:
        """
        Get the full path to an item's image.
        
        Args:
            item_id: ID of the item
            
        Returns:
            str: Full path to the image, or None if not found
        """
        try:
            item = self.get_item(item_id)
            if item and "filename" in item:
                return str(self.images_dir / item["filename"])
            return None
        except Exception as e:
            self.logger.error(f"Error getting image path for {item_id}: {e}")
            return None
            
    def get_item_path(self, item_id: str) -> Optional[str]:
        """
        Get the path for an item (alias for get_image_path).
        
        Args:
            item_id: ID of the item
            
        Returns:
            str: Full path to the item, or None if not found
        """
        return self.get_image_path(item_id)
            
    def create_collection(self, name: str, description: str = "") -> Optional[str]:
        """
        Create a new collection.
        
        Args:
            name: Collection name
            description: Collection description
            
        Returns:
            str: ID of the created collection, or None on failure
        """
        try:
            # Generate unique ID
            collection_id = str(uuid.uuid4())
            
            # Create collection entry
            collection_data = {
                "id": collection_id,
                "name": name,
                "description": description,
                "date_created": datetime.now().isoformat(),
                "items": []
            }
            
            # Add to library data
            self.library_data["collections"][collection_id] = collection_data
            
            # Save library data
            self._save_library_data(self.library_data)
            
            return collection_id
            
        except Exception as e:
            self.logger.error(f"Error creating collection: {e}")
            return None
            
    def add_item_to_collection(self, item_id: str, collection_id: str) -> bool:
        """
        Add an item to a collection.
        
        Args:
            item_id: ID of the item
            collection_id: ID of the collection
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if (item_id in self.library_data["items"] and 
                collection_id in self.library_data["collections"]):
                
                # Check if item is already in collection
                if item_id not in self.library_data["collections"][collection_id]["items"]:
                    # Add item to collection
                    self.library_data["collections"][collection_id]["items"].append(item_id)
                    
                    # Save library data
                    return self._save_library_data(self.library_data)
                    
                return True  # Item already in collection
                
            return False
        except Exception as e:
            self.logger.error(f"Error adding item {item_id} to collection {collection_id}: {e}")
            return False 

    # --- Item Retrieval by Type ---
    def _ensure_item_details(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to ensure path, dimensions, and size are set for an item."""
        if "path" not in item and "filename" in item:
            file_path = self.images_dir / item["filename"]
            item["path"] = str(file_path.absolute())
        
        item_type = item.get("type", "unknown")

        if "dimensions" not in item and "path" in item and item_type not in ["raw_video", "post_ready_video"]:
            try:
                with Image.open(item["path"]) as img:
                    item["dimensions"] = [img.width, img.height]
            except Exception:
                item["dimensions"] = [None, None] # Use None for consistency
        elif item_type in ["raw_video", "post_ready_video"] and "dimensions" not in item:
             item["dimensions"] = [None, None] # Videos might not have dimensions initially

        if "size_str" not in item and "path" in item and Path(item["path"]).exists():
            try:
                size_bytes = os.path.getsize(item["path"])
                item["size_str"] = f"{size_bytes / 1024:.1f} KB"
            except Exception:
                item["size_str"] = "Unknown"
        elif "size_str" not in item: # If path doesn't exist or other issue
            item["size_str"] = "Unknown"
            
        return item

    def get_items_by_type(self, item_type_or_types: str | List[str]) -> List[Dict[str, Any]]:
        """Get items filtered by a specific type or list of types."""
        try:
            all_items = list(self.library_data["items"].values())
            
            types_to_match = []
            if isinstance(item_type_or_types, str):
                types_to_match.append(item_type_or_types)
            elif isinstance(item_type_or_types, list):
                types_to_match = item_type_or_types
            else:
                self.logger.warning("Invalid type for item_type_or_types in get_items_by_type")
                return []

            filtered_items = [
                self._ensure_item_details(item.copy()) 
                for item in all_items 
                if item.get("type") in types_to_match
            ]
            
            # Sort by date added (newest first)
            filtered_items.sort(key=lambda x: x.get("date_added", ""), reverse=True)
            return filtered_items
        except Exception as e:
            self.logger.error(f"Error in get_items_by_type: {e}")
            return []

    def get_raw_photos(self) -> List[Dict[str, Any]]:
        """Get all raw photo items."""
        return self.get_items_by_type("raw_photo")

    def get_raw_videos(self) -> List[Dict[str, Any]]:
        """Get all raw video items."""
        return self.get_items_by_type("raw_video")

    def get_post_ready_photos(self) -> List[Dict[str, Any]]:
        """Get all post-ready photo items."""
        return self.get_items_by_type("post_ready_photo")

    def get_post_ready_videos(self) -> List[Dict[str, Any]]:
        """Get all post-ready video items."""
        return self.get_items_by_type("post_ready_video")

    def get_all_post_ready_items(self) -> List[Dict[str, Any]]:
        """Get all post-ready items (both photos and videos)."""
        return self.get_items_by_type(["post_ready_photo", "post_ready_video"]) 