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
                         date_added: str = None, metadata: dict = None) -> Optional[Dict[str, Any]]:
        """
        Add an item to the library from a file path.
        
        Args:
            file_path: Path to the image file
            caption: Caption text for the image
            date_added: ISO format date string (defaults to now)
            metadata: Additional metadata for the item
            
        Returns:
            dict: Item data of the added item, or None on failure
        """
        try:
            # Open the image to get its data
            with Image.open(file_path) as img:
                # Generate unique ID
                item_id = str(uuid.uuid4())
                
                # Generate filename
                filename = f"{item_id}.png"
                dest_path = self.images_dir / filename
                
                # Copy the file to the library
                shutil.copy2(file_path, dest_path)
                
                # Get image dimensions
                width, height = img.size
                
                # Create item metadata
                item_metadata = {
                    "original_mode": img.mode
                }
                
                # Update with additional metadata if provided
                if metadata and isinstance(metadata, dict):
                    item_metadata.update(metadata)
                
                # Create item entry
                item_data = {
                    "id": item_id,
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
                date_added: str = None, metadata: dict = None) -> Optional[str]:
        """
        Add an item to the library.
        
        Args:
            image: PIL Image object
            caption: Caption text for the image
            date_added: ISO format date string (defaults to now)
            metadata: Additional metadata for the item
            
        Returns:
            str: ID of the added item, or None on failure
        """
        try:
            # Generate unique ID
            item_id = str(uuid.uuid4())
            
            # Generate filename
            filename = f"{item_id}.png"
            file_path = self.images_dir / filename
            
            # Preserve image mode
            original_mode = image.mode
            
            # Save image with high quality settings
            if original_mode == 'RGBA':
                # PNG with maximum compression - lossless
                image.save(file_path, format="PNG", compress_level=0)
            else:
                # Convert to RGB if needed
                if original_mode != 'RGB':
                    image = image.convert('RGB')
                # PNG with maximum compression - lossless
                image.save(file_path, format="PNG", compress_level=0)
            
            # Get image dimensions
            width, height = image.size
            
            # Create item metadata
            item_metadata = {
                "original_mode": original_mode
            }
            
            # Update with additional metadata if provided
            if metadata and isinstance(metadata, dict):
                item_metadata.update(metadata)
            
            # Create item entry
            item_data = {
                "id": item_id,
                "filename": filename,
                "path": str(file_path.absolute()),
                "caption": caption,
                "date_added": date_added or datetime.now().isoformat(),
                "tags": [],
                "dimensions": [width, height],
                "size_str": f"{os.path.getsize(file_path) / 1024:.1f} KB",
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