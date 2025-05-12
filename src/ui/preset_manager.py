"""
Preset manager for handling presets
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

class PresetManager:
    """Manages presets for the application"""
    
    def __init__(self, preset_file="presets.json"):
        """
        Initialize the preset manager.
        
        Args:
            preset_file: Path to the preset file
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.preset_file = preset_file
        self.presets = self.load_presets()
        
    def load_presets(self) -> Dict[str, Any]:
        """
        Load presets from the preset file.
        
        Returns:
            Dict: The loaded presets or an empty preset structure if loading fails
        """
        default_presets = {
            "presets": {},
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            if os.path.exists(self.preset_file):
                with open(self.preset_file, "r", encoding="utf-8") as f:
                    loaded_presets = json.load(f)
                self.logger.info("Loaded presets from disk")
                return loaded_presets
            else:
                self.logger.info("No presets file found, using defaults")
                return default_presets
        except Exception as e:
            self.logger.error(f"Error loading presets: {e}")
            return default_presets
            
    def save_presets(self) -> bool:
        """
        Save presets to the preset file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update the last_updated timestamp
            self.presets["last_updated"] = datetime.now().isoformat()
            
            # Write to file
            with open(self.preset_file, "w", encoding="utf-8") as f:
                json.dump(self.presets, f, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving presets: {e}")
            return False
            
    def get_presets(self) -> Dict[str, Any]:
        """
        Get the presets.
        
        Returns:
            Dict: The presets
        """
        return self.presets
        
    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a preset by name.
        
        Args:
            name: The name of the preset
            
        Returns:
            Dict: The preset data or None if not found
        """
        if "presets" in self.presets and name in self.presets["presets"]:
            return self.presets["presets"][name]
        return None
        
    def save_preset(self, name: str, data: Dict[str, Any]) -> bool:
        """
        Save a preset.
        
        Args:
            name: The name of the preset
            data: The preset data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure presets dictionary exists
            if "presets" not in self.presets:
                self.presets["presets"] = {}
            
            # Add timestamp if not present
            if "created" not in data:
                data["created"] = datetime.now().isoformat()
                
            # Save the preset
            self.presets["presets"][name] = data
            
            # Save to disk
            return self.save_presets()
        except Exception as e:
            self.logger.error(f"Error saving preset '{name}': {e}")
            return False
            
    def delete_preset(self, name: str) -> bool:
        """
        Delete a preset.
        
        Args:
            name: The name of the preset
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if the preset exists
            if "presets" in self.presets and name in self.presets["presets"]:
                # Remove the preset
                del self.presets["presets"][name]
                
                # Save to disk
                return self.save_presets()
            else:
                self.logger.warning(f"Preset '{name}' not found for deletion")
                return False
        except Exception as e:
            self.logger.error(f"Error deleting preset '{name}': {e}")
            return False
            
    def get_preset_names(self) -> List[str]:
        """
        Get the list of preset names.
        
        Returns:
            List: The list of preset names
        """
        if "presets" in self.presets:
            return sorted(list(self.presets["presets"].keys())) 