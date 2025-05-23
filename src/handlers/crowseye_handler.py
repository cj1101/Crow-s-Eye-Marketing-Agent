"""
Crow's Eye marketing feature handler for advanced media organization and gallery generation.
"""
import os
import sys
import logging
import random
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot, Qt, QSize
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PIL import Image

from ..models.app_state import AppState
from ..config import constants as const
from .media_handler import MediaHandler, pil_to_qpixmap
from .library_handler import LibraryManager

class CrowsEyeSignals(QObject):
    """Signal class for Crow's Eye operations."""
    status_update = Signal(str)
    gallery_generated = Signal(list)  # List of selected media paths
    caption_generated = Signal(str)
    error = Signal(str, str)  # Title, message
    warning = Signal(str, str)  # Title, message
    info = Signal(str, str)  # Title, message

class CrowsEyeHandler:
    """Handler for Crow's Eye marketing features."""
    
    SIMULATED_TAGS_DB = {
        "oip.jpeg": ["bread", "baked goods", "pastry", "food", "bakery", "assortment", "croissant", "roll"],
        "sourdough.jpeg": ["bread", "sourdough", "baked goods", "food", "bakery", "loaf", "sliced bread"],
        "igannouncement.png": ["game", "pixel art", "blimp", "vehicle", "sky", "announcement", "minecraft style", "landscape"],
        "untitled.png": ["art", "character", "fantasy", "warrior", "portrait", "woman", "red hair", "armor", "apex predators", "illustration"],
        # Add more known image filenames and their simulated tags here
    }
    
    def __init__(self, app_state: AppState, media_handler: MediaHandler, library_manager: LibraryManager):
        """
        Initialize the Crow's Eye handler.
        
        Args:
            app_state: Application state object
            media_handler: Media handler instance
            library_manager: Library manager instance
        """
        self.app_state = app_state
        self.media_handler = media_handler
        self.library_manager = library_manager
        self.signals = CrowsEyeSignals()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Directories
        self.media_gallery_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'media_gallery')
        self._ensure_directories()
        
        # Current state
        self.selected_media = []
        self.current_gallery = []
        self.current_caption = ""
        
        self.logger.info("Crow's Eye Handler initialized")
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        os.makedirs(self.media_gallery_dir, exist_ok=True)
        # Ensure a subdirectory for enhanced images exists
        os.makedirs(os.path.join(self.media_gallery_dir, "enhanced"), exist_ok=True)
        self.logger.debug(f"Ensured directory: {self.media_gallery_dir} and its subdirectories")
    
    def get_all_media(self) -> Dict[str, List[str]]:
        """
        Get all media organized by type, using LibraryManager.
        
        Returns:
            Dict with keys 'raw_photos', 'raw_videos', 'finished_posts' and media paths as values.
        """
        result = {
            "raw_photos": [],
            "raw_videos": [],
            "finished_posts": [] # Corresponds to 'post_ready' items
        }
        
        try:
            raw_photos_items = self.library_manager.get_raw_photos()
            result["raw_photos"] = [item["path"] for item in raw_photos_items if "path" in item]
            
            raw_videos_items = self.library_manager.get_raw_videos()
            result["raw_videos"] = [item["path"] for item in raw_videos_items if "path" in item]
            
            post_ready_items = self.library_manager.get_all_post_ready_items()
            result["finished_posts"] = [item["path"] for item in post_ready_items if "path" in item]
            
            self.logger.info(
                f"Retrieved from LibraryManager: "
                f"{len(result['raw_photos'])} raw photos, "
                f"{len(result['raw_videos'])} raw videos, "
                f"{len(result['finished_posts'])} finished posts."
            )
            return result
            
        except Exception as e:
            self.logger.exception(f"Error getting media from LibraryManager: {e}")
            self.signals.error.emit("Media Error", f"Could not retrieve media: {str(e)}")
            return result # Return empty structure on error
    
    def search_media(self, query: str) -> Dict[str, List[str]]:
        """
        Search media by filename or caption.
        
        Args:
            query: Search query
            
        Returns:
            Dict with keys 'raw_photos', 'raw_videos', 'finished_posts' and filtered media paths as values
        """
        all_media = self.get_all_media()
        if not query:
            return all_media
            
        query = query.lower()
        result = {
            "raw_photos": [],
            "raw_videos": [],
            "finished_posts": []
        }
        
        # Simple search implementation - in a real app, this would use more sophisticated NLP
        for category, media_list in all_media.items():
            for media_path in media_list:
                filename = os.path.basename(media_path).lower()
                caption = self.media_handler.get_caption(media_path) or ""
                
                if query in filename or query in caption.lower():
                    result[category].append(media_path)
        
        return result
    
    def _get_simulated_ai_tags(self, media_path: str) -> List[str]:
        """
        Simulates getting AI-generated tags for a media file based on its filename.
        In a real system, this would involve an image analysis model.
        """
        base_filename = os.path.basename(media_path).lower()
        return self.SIMULATED_TAGS_DB.get(base_filename, [])

    def generate_gallery(self, media_paths: List[str], prompt: str, enhance_photos: bool = False) -> List[str]:
        """
        Generate a smart gallery based on media content (simulated) and a focus prompt.
        
        Args:
            media_paths: List of media paths to choose from.
            prompt: Gallery focus for selection criteria (e.g., "best 2 bread images").
            enhance_photos: Whether to apply automatic photo enhancement.
            
        Returns:
            List of selected media paths (potentially pointing to enhanced versions).
        """
        self.signals.status_update.emit("Generating gallery based on content focus...")
        self.logger.info(f"Generating gallery with focus: '{prompt}' from {len(media_paths)} items.")

        prompt_keywords = self._extract_keywords(prompt)
        desired_count = self._extract_count(prompt)

        self.logger.info(f"Prompt keywords: {prompt_keywords}, Desired count: {desired_count}")

        if not prompt_keywords:
            self.logger.warning("No keywords extracted from prompt. Cannot generate content-aware gallery.")
            self.signals.warning.emit("Gallery Generation", "Could not understand the focus. Please be more specific.")
            return []

        scored_media = []
        for path in media_paths:
            score = 0
            ai_tags = self._get_simulated_ai_tags(path)
            caption = self.media_handler.get_caption(path) or ""
            
            # Higher score for matching AI tags
            for keyword in prompt_keywords:
                if keyword in ai_tags:
                    score += 10  # Strong match for AI tag
                    self.logger.debug(f"'{os.path.basename(path)}' AI tag match for '{keyword}'. Score +10.")
                if keyword in caption.lower():
                    score += 1 # Weaker match for caption
                    self.logger.debug(f"'{os.path.basename(path)}' caption match for '{keyword}'. Score +1.")
            
            if score > 0:
                scored_media.append((path, score))
            else:
                self.logger.debug(f"'{os.path.basename(path)}' had no matching keywords or tags for prompt '{prompt}'.")

        # Sort by score in descending order
        scored_media.sort(key=lambda x: x[1], reverse=True)
        self.logger.info(f"Scored media: {[(os.path.basename(p), s) for p, s in scored_media]}")

        selected_media = []
        if not scored_media:
            self.logger.info("No media items scored positively for the given focus.")
            self.signals.warning.emit("Gallery Generation", "No media matched your focus. Try a different focus or add more relevant media.")
            return []

        if desired_count is not None and desired_count > 0:
            selected_media = [item[0] for item in scored_media[:desired_count]]
            self.logger.info(f"Selected top {len(selected_media)} items based on desired count {desired_count}.")
        else:
            # If no specific count, or count was invalid, select all positively scored items
            # Or a sensible default like top 3-5 if many items scored well.
            # For now, let's take all positively scored if no count is specified.
            # This part can be refined if "pick bread images" without a number should default to a small set.
            selected_media = [item[0] for item in scored_media]
            self.logger.info(f"No specific count given or count was invalid. Selecting all {len(selected_media)} positively scored items.")
            if desired_count is None:
                 self.signals.warning.emit("Gallery Generation", f"Could not determine a specific number from your focus, so selected all {len(selected_media)} matches. Try adding a number like 'pick 2 bread images'.")

        final_gallery_paths = []
        if enhance_photos:
            self.signals.status_update.emit("Enhancing photos for the gallery...")
            enhanced_media_dir = Path(self.media_gallery_dir) / "enhanced"
            enhanced_media_dir.mkdir(parents=True, exist_ok=True) # Ensure it exists

            for original_path_str in selected_media:
                original_path = Path(original_path_str)
                file_ext = original_path.suffix.lower()
                # Only attempt to enhance supported image types
                if file_ext in const.SUPPORTED_IMAGE_FORMATS: # Using constants for supported image check
                    try:
                        pil_image = self.media_handler.load_image(original_path_str)
                        if pil_image:
                            enhanced_image = self.media_handler.apply_default_enhancement(pil_image)
                            if enhanced_image:
                                # Save enhanced image to the gallery's enhanced subfolder
                                enhanced_filename = f"{original_path.stem}_enhanced{original_path.suffix}"
                                enhanced_save_path = enhanced_media_dir / enhanced_filename
                                
                                # Use MediaHandler to save, ensuring format consistency if any
                                success = self.media_handler.save_image(enhanced_image, str(enhanced_save_path))
                                if success:
                                    final_gallery_paths.append(str(enhanced_save_path))
                                    self.logger.info(f"Saved enhanced image to {enhanced_save_path}")
                                else:
                                    self.logger.warning(f"Failed to save enhanced image for {original_path_str}. Using original.")
                                    final_gallery_paths.append(original_path_str)
                            else:
                                self.logger.warning(f"Enhancement failed for {original_path_str}. Using original.")
                                final_gallery_paths.append(original_path_str)
                        else:
                            self.logger.warning(f"Could not load image {original_path_str} for enhancement. Using original.")
                            final_gallery_paths.append(original_path_str)
                    except Exception as e:
                        self.logger.exception(f"Error enhancing photo {original_path_str}: {e}. Using original.")
                        final_gallery_paths.append(original_path_str)
                else:
                    # If it's a video or unsupported type, just add original path
                    final_gallery_paths.append(original_path_str)
            self.signals.status_update.emit("Photo enhancement complete.")
        else:
            final_gallery_paths = selected_media # Use original paths if no enhancement

        self.current_gallery = final_gallery_paths
        self.signals.gallery_generated.emit(final_gallery_paths)
        self.signals.status_update.emit(f"Generated gallery with {len(final_gallery_paths)} items based on your focus.")
        
        return final_gallery_paths
    
    def generate_caption(self, media_paths: List[str], tone_prompt: str = "") -> str:
        """
        Generate a caption for selected media, considering content and tone.
        
        Args:
            media_paths: List of media paths.
            tone_prompt: Optional tone guidance for the caption.
            
        Returns:
            Generated caption.
        """
        self.signals.status_update.emit("Generating content-aware caption...")
        self.logger.info(f"Generating caption for {len(media_paths)} items with tone: '{tone_prompt}'")

        if not media_paths:
            self.logger.warning("Cannot generate caption: No media paths provided.")
            self.signals.error.emit("Caption Error", "No media provided for caption generation.")
            return ""

        try:
            # 1. Aggregate AI Tags from all media items
            all_ai_tags = set()
            for path in media_paths:
                tags = self._get_simulated_ai_tags(path)
                for tag in tags:
                    all_ai_tags.add(tag.lower()) # Normalize to lowercase
            
            main_subjects = list(all_ai_tags)[:3] # Take up to 3 prominent subjects
            self.logger.info(f"Aggregated AI tags for caption: {main_subjects}")

            # 2. Determine base sentiment/style from tone_prompt
            tone_keywords = self._extract_keywords(tone_prompt.lower())
            caption_parts = []
            base_phrase = ""

            if "professional" in tone_keywords:
                base_phrase = "Presenting our latest selection."
            elif "casual" in tone_keywords or "friendly" in tone_keywords:
                base_phrase = "Check out these cool shots!"
            elif "funny" in tone_keywords or "humor" in tone_keywords:
                base_phrase = "Had some fun with these! What do you think?"
            elif "inspirational" in tone_keywords:
                base_phrase = "Feeling inspired by these moments."
            elif "excited" in tone_keywords:
                base_phrase = "So excited to share this!"
            elif "sarcastic" in tone_keywords:
                base_phrase = "Oh, just some more amazing stuff. You know how it is."
            else:
                base_phrase = "Sharing some highlights."
            
            caption_parts.append(base_phrase)

            # 3. Weave in content subjects (AI tags)
            if main_subjects:
                subject_phrase = "Featuring " + ", ".join(main_subjects) + "."
                if len(main_subjects) == 1:
                    subject_phrase = f"Focusing on {main_subjects[0]}."
                elif len(main_subjects) == 2:
                    subject_phrase = f"A look at {main_subjects[0]} and {main_subjects[1]}."
                caption_parts.append(subject_phrase)
            else:
                # Fallback if no AI tags identified, rely more on media types or generic phrases
                media_types = []
                for path in media_paths:
                    ext = os.path.splitext(path)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                        media_types.append("photo")
                    elif ext in ['.mp4', '.mov', '.avi', '.wmv']:
                        media_types.append("video")
                unique_media_types = list(set(media_types))
                if len(unique_media_types) == 1 and unique_media_types[0] == "photo":
                    caption_parts.append("A collection of interesting photos.")
                elif len(unique_media_types) == 1 and unique_media_types[0] == "video":
                    caption_parts.append("Some captivating video moments.")
                else:
                    caption_parts.append("A mix of media content.")

            # 4. Add a concluding part based on tone if not already strong
            if "excited" in tone_keywords and "excited" not in base_phrase.lower():
                caption_parts.append("Hope you enjoy it as much as we do!")
            elif ("professional" in tone_keywords or "concise" in tone_keywords) and len(caption_parts) > 1:
                pass # Keep it shorter for professional/concise
            elif not tone_keywords and main_subjects: # Generic call to action if no tone but subjects exist
                 caption_parts.append("What are your thoughts?")

            final_caption = " ".join(caption_parts)

            # 5. Smarter Hashtags
            hashtags = set()
            # Add hashtags from main subjects
            for subject in main_subjects:
                hashtags.add(f"#{subject.replace(' ', '')}") # Remove spaces for hashtags
            
            # Add hashtags from tone (if any specific ones make sense)
            if "bakery" in main_subjects or "bread" in main_subjects:
                hashtags.add("#BakingLove")
            if "food" in main_subjects:
                hashtags.add("#Foodie")
            if "art" in main_subjects:
                hashtags.add("#Artwork")
            
            # Add some generic relevant hashtags
            generic_hashtags = ["#ContentCreation", "#VisualStorytelling", "#Highlights"]
            for i in range(min(2, len(generic_hashtags))): # Add up to 2 generic ones
                hashtags.add(random.choice(generic_hashtags))
            
            # Ensure not too many hashtags (e.g., max 5 for this simulation)
            final_hashtags = list(hashtags)[:5]
            
            if final_hashtags:
                final_caption += " " + " ".join(final_hashtags)
            
            self.current_caption = final_caption.strip()
            self.signals.caption_generated.emit(self.current_caption)
            self.signals.status_update.emit("Content-aware caption generated.")
            self.logger.info(f"Generated caption: {self.current_caption}")
            
            return self.current_caption
            
        except Exception as e:
            self.logger.exception(f"Error generating content-aware caption: {e}")
            self.signals.error.emit("Caption Error", f"Could not generate caption: {str(e)}")
            return "" # Fallback to empty string on error
    
    def save_gallery(self, name: str, media_paths: List[str], caption: str) -> bool:
        """
        Save a generated gallery.
        
        Args:
            name: Gallery name
            media_paths: List of media paths
            caption: Caption for the gallery
            
        Returns:
            True if successful, False otherwise
        """
        self.signals.status_update.emit("Saving gallery...")
        
        try:
            # Create a gallery record
            gallery_data = {
                "name": name,
                "created_at": datetime.now().isoformat(),
                "media_paths": media_paths,
                "caption": caption
            }
            
            # Create a unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gallery_{timestamp}.json"
            filepath = os.path.join(self.media_gallery_dir, filename)
            
            # Save gallery data
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(gallery_data, f, indent=2)
            
            self.signals.status_update.emit(f"Gallery '{name}' saved")
            self.signals.info.emit("Gallery Saved", f"Gallery '{name}' has been saved successfully")
            
            return True
            
        except Exception as e:
            self.logger.exception(f"Error saving gallery: {e}")
            self.signals.error.emit("Save Error", f"Could not save gallery: {str(e)}")
            return False
    
    def get_saved_galleries(self) -> List[Dict[str, Any]]:
        """
        Get all saved galleries from disk.
        
        Returns:
            List of gallery data dictionaries.
        """
        galleries = []
        try:
            gallery_dir = Path(self.media_gallery_dir)
            for f in gallery_dir.glob("*.gallery.json"):
                try:
                    with open(f, 'r', encoding='utf-8') as file:
                        gallery_data = json.load(file)
                        gallery_data["filename"] = f.name  # Store filename for reference
                        galleries.append(gallery_data)
                except Exception as e:
                    self.logger.error(f"Error loading gallery {f}: {e}")
            
            return galleries
        except Exception as e:
            self.logger.exception(f"Error loading galleries: {e}")
            return []
    
    def load_all_galleries(self) -> List[Dict[str, Any]]:
        """
        Load all saved galleries from disk.
        This is an alias for get_saved_galleries for backward compatibility.
        
        Returns:
            List of gallery data dictionaries.
        """
        return self.get_saved_galleries()
    
    def _extract_keywords(self, prompt: str) -> List[str]:
        """Extract keywords from a prompt."""
        # Simple implementation - in a real app, this would use NLP
        excluded_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'of', 'from'}
        words = [word.strip().lower() for word in prompt.split() if word.strip()]
        return [word for word in words if len(word) > 2 and word not in excluded_words]
    
    def _extract_count(self, prompt: str) -> Optional[int]:
        """Extract the number of items to select from the prompt."""
        import re
        # More comprehensive patterns to capture numbers
        # Looks for a number, optionally preceded by words like "pick", "select", "top", "best", "the"
        # and optionally followed by words like "images", "items", "photos"
        patterns = [
            r'(?:pick|select|choose|get|show|the|top|best|find)\s+(\d+)', # e.g., "pick 2", "the 5"
            r'(\d+)\s+(?:images?|items?|photos?|pictures?)', # e.g., "2 images", "3 items"
            r'a\s+few', # interprets "a few" as 3
            r'a\s+couple', # interprets "a couple" as 2
            r'(\d+)' # last resort: any standalone number
        ]
        
        prompt_lower = prompt.lower()

        if 'a few' in prompt_lower:
            self.logger.debug("Extracted count: 3 from 'a few'")
            return 3
        if 'a couple' in prompt_lower:
            self.logger.debug("Extracted count: 2 from 'a couple'")
            return 2

        for pattern in patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                try:
                    # Find the group that captured the number. Some patterns have the number in group 1.
                    # The last pattern r'(\d+)' will always put it in group 1.
                    # For r'(?:pick|select|choose)\s+(\d+)', it's group 1.
                    # Ensure we iterate through groups if necessary, but most should be group(1)
                    num_str = ""
                    if len(match.groups()) > 0: # Check if there are any capturing groups
                        for group in match.groups(): # Iterate through all captured groups
                            if group and group.isdigit(): # Take the first one that's a digit
                                num_str = group
                                break
                    
                    if num_str:
                        val = int(num_str)
                        self.logger.debug(f"Extracted count: {val} from prompt using pattern '{pattern}'")
                        return val
                except ValueError:
                    self.logger.warning(f"Could not parse number from match group: {match.group(1)} with pattern '{pattern}'")
                    continue # Try next pattern
                except Exception as e:
                    self.logger.error(f"Error during count extraction with pattern '{pattern}': {e}")
                    continue
        
        self.logger.debug(f"Could not extract a specific count from prompt: '{prompt}'")
        return None

    def update_saved_gallery(self, gallery_filename: str, new_name: str, new_caption: str) -> bool:
        """
        Update the name and caption of a saved gallery.

        Args:
            gallery_filename: The JSON filename of the gallery to update.
            new_name: The new name for the gallery.
            new_caption: The new caption for the gallery.

        Returns:
            True if successful, False otherwise.
        """
        self.signals.status_update.emit(f"Updating gallery: {gallery_filename}...")
        self.logger.info(f"Attempting to update gallery {gallery_filename} with new name: '{new_name}'")

        gallery_filepath = os.path.join(self.media_gallery_dir, gallery_filename)

        if not os.path.exists(gallery_filepath):
            self.logger.error(f"Cannot update gallery: File not found at {gallery_filepath}")
            self.signals.error.emit("Update Error", f"Gallery file {gallery_filename} not found.")
            return False

        try:
            with open(gallery_filepath, 'r', encoding='utf-8') as f:
                gallery_data = json.load(f)
            
            gallery_data['name'] = new_name
            gallery_data['caption'] = new_caption
            gallery_data['updated_at'] = datetime.now().isoformat() # Add an updated_at timestamp

            with open(gallery_filepath, 'w', encoding='utf-8') as f:
                json.dump(gallery_data, f, indent=2)
            
            self.signals.status_update.emit(f"Gallery '{new_name}' updated successfully.")
            self.signals.info.emit("Gallery Updated", f"Details for gallery '{new_name}' have been updated.")
            self.logger.info(f"Gallery {gallery_filename} updated successfully.")
            return True

        except json.JSONDecodeError as e:
            self.logger.exception(f"Error decoding JSON for gallery {gallery_filename}: {e}")
            self.signals.error.emit("Update Error", f"Could not read gallery data for {gallery_filename}.")
            return False
        except Exception as e:
            self.logger.exception(f"Error updating gallery file {gallery_filename}: {e}")
            self.signals.error.emit("Update Error", f"Could not save updated gallery data for {gallery_filename}.")
            return False 