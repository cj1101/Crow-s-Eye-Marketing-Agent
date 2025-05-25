"""
Handles all media operations including file I/O, media processing, and status management.
Combines functionality from media_handlers_v4_pyqt.py and io_handlers_v4_pyqt.py.
"""
# Standard Imports
import os
import json
import logging
import time
import math
import io
import shutil
from typing import Optional, Tuple, List, Dict, Any
import re
from datetime import datetime
from pathlib import Path

# Third-Party Imports
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import cv2
import fitz  # PyMuPDF
from PySide6.QtGui import QPixmap, QImage

# Application-Specific Imports
from ..config import constants as const
from ..models.app_state import AppState
from ..handlers.auth_handler import auth_handler

# --- Image Conversion Utilities ---
def pil_to_qpixmap(pil_image: Image.Image) -> QPixmap:
    """Converts a PIL Image to a QPixmap with guaranteed color fidelity and aspect ratio preservation."""
    if pil_image is None:
        return QPixmap()
    
    try:
        # Make a copy to avoid altering the original
        img = pil_image.copy()
        original_width, original_height = img.size
        
        # METHOD 1: Using raw bytes conversion - generally fastest and most reliable
        try:
            if img.mode == 'RGBA':
                qimage = QImage(
                    img.tobytes('raw', 'RGBA'), 
                    original_width, 
                    original_height, 
                    QImage.Format.Format_RGBA8888
                )
            else:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                qimage = QImage(
                    img.tobytes('raw', 'RGB'), 
                    original_width, 
                    original_height, 
                    3 * original_width,
                    QImage.Format.Format_RGB888
                )
            
            if not qimage.isNull():
                pixmap = QPixmap.fromImage(qimage)
                # Set the device pixel ratio to 1.0 to ensure no scaling is applied
                pixmap.setDevicePixelRatio(1.0)
                return pixmap
        except Exception as e:
            logging.warning(f"Direct conversion failed with error: {e}")
        
        # METHOD 2: Using buffer approach (fallback) - ensure lossless conversion
        try:
            # Always use PNG for lossless conversion
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', compress_level=0)
            buffer.seek(0)
            temp_pixmap = QPixmap()
            if temp_pixmap.loadFromData(buffer.getvalue()):
                # Set the device pixel ratio to 1.0 to ensure no scaling is applied
                temp_pixmap.setDevicePixelRatio(1.0)
                return temp_pixmap
        except Exception as e:
            logging.warning(f"Buffer method failed with error: {e}")
        
        logging.error("All PIL to QPixmap conversion methods failed")
        return QPixmap()
    
    except Exception as e:
        logging.exception(f"Unexpected error in PIL to QPixmap conversion: {e}")
        return QPixmap()

# --- Media Status Management ---
def load_media_status(app_state: Any, signals: Any) -> bool:
    """Loads and validates media status data, with migration support for old formats."""
    filename = const.MEDIA_STATUS_FILE
    loaded_data = {}
    signals.status_update.emit("Loading media status...")
    
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding='utf-8') as f:
                loaded_status_raw = json.load(f)
                
            if not isinstance(loaded_status_raw, dict):
                raise ValueError(f"File '{filename}' root not a dictionary.")

            valid_entries = 0
            invalid_paths = []
            migration_needed = False
            
            for path, data in loaded_status_raw.items():
                if not isinstance(path, str):
                    invalid_paths.append(str(path))
                    continue

                if isinstance(data, dict):
                    normalized_data = const.DEFAULT_MEDIA_STATUS_ENTRY.copy()
                    # Migration Check
                    if "posted" in data or "posted_ts" in data:
                        migration_needed = True
                        if data.get("posted"):
                            normalized_data[const.STATUS_KEY_POSTED_IG] = True
                            normalized_data[const.STATUS_KEY_POSTED_IG_TS] = data.get("posted_ts")
                        data.pop("posted", None)
                        data.pop("posted_ts", None)
                    
                    normalized_data.update(data)
                    loaded_data[path] = normalized_data
                    valid_entries += 1
                elif isinstance(data, str):
                    logging.warning(f"Old string status format for '{os.path.basename(path)}'. Converting.")
                    new_entry = const.DEFAULT_MEDIA_STATUS_ENTRY.copy()
                    if data == const.STATUS_VAL_SUCCESS:
                        new_entry[const.STATUS_KEY_GENERATION] = const.STATUS_VAL_SUCCESS
                    elif data == const.STATUS_VAL_FAILED:
                        new_entry[const.STATUS_KEY_GENERATION] = const.STATUS_VAL_FAILED
                    else:
                        new_entry[const.STATUS_KEY_GENERATION] = const.STATUS_VAL_OK
                    loaded_data[path] = new_entry
                    valid_entries += 1
                    migration_needed = True

            if invalid_paths:
                logging.warning(f"Skipped {len(invalid_paths)} invalid path keys")

            app_state.media_generation_status.clear()
            app_state.media_generation_status.update(loaded_data)
            logging.info(f"Loaded status cache ({valid_entries} valid entries).")

            if migration_needed:
                logging.info("Saving after format migration.")
                save_media_status(app_state, signals)

        else:
            app_state.media_generation_status.clear()
            signals.status_update.emit(f"Status file '{filename}' not found, starting fresh.")
            
        # Ensure defaults for files in library
        _ensure_default_status_entries(app_state, signals)
        signals.status_update.emit("Media status load complete.")
        return True
        
    except Exception as e:
        logging.exception(f"Error loading media status: {e}")
        app_state.media_generation_status.clear()
        signals.error.emit("Cache Error", f"Could not load status file: {str(e)}")
        return False

def save_media_status(app_state: Any, signals: Any) -> bool:
    """Saves the current media status data, pruning non-existent files."""
    filename = const.MEDIA_STATUS_FILE
    
    if not hasattr(app_state, 'media_generation_status') or not isinstance(app_state.media_generation_status, dict):
        logging.error("Media status data invalid, cannot save.")
        signals.error.emit("Save Error", "Internal error: Media status data is invalid.")
        return False

    data_to_save = app_state.media_generation_status.copy()
    
    try:
        # Prune non-existent files
        library_path = const.MEDIA_LIBRARY_DIR
        current_files = set()
        
        try:
            os.makedirs(library_path, exist_ok=True)
            current_files = {
                os.path.join(library_path, f) 
                for f in os.listdir(library_path) 
                if os.path.isfile(os.path.join(library_path, f))
            }
        except OSError as e:
            logging.error(f"Could not list files in '{library_path}': {e}")
            return False

        # Remove entries for non-existent files
        keys_to_remove = {key for key in data_to_save if key not in current_files}
        if keys_to_remove:
            logging.info(f"Pruning {len(keys_to_remove)} entries from status cache")
            for key in keys_to_remove:
                data_to_save.pop(key, None)

        # Normalize data before saving
        final_save_data = {}
        for path, data in data_to_save.items():
            if not isinstance(path, str):
                continue

            if isinstance(data, dict):
                normalized_data = const.DEFAULT_MEDIA_STATUS_ENTRY.copy()
                data.pop("posted", None)
                data.pop("posted_ts", None)
                normalized_data.update(data)
                final_save_data[path] = normalized_data
            else:
                logging.warning(f"Invalid data type for '{path}', repairing")
                new_entry = const.DEFAULT_MEDIA_STATUS_ENTRY.copy()
                if isinstance(data, str) and data in [const.STATUS_VAL_SUCCESS, const.STATUS_VAL_FAILED]:
                    new_entry[const.STATUS_KEY_GENERATION] = data
                final_save_data[path] = new_entry

        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(final_save_data, f, indent=2)
            
        logging.info(f"Successfully saved media status to {filename}")
        return True
        
    except Exception as e:
        logging.exception(f"Error saving media status: {e}")
        signals.error.emit("Save Error", f"Could not save status file: {str(e)}")
        return False

def _ensure_default_status_entries(app_state: Any, signals: Any) -> None:
    """Ensures all files in the media library have status entries."""
    try:
        media_dir = const.MEDIA_LIBRARY_DIR
        os.makedirs(media_dir, exist_ok=True)
        
        current_files = {
            os.path.join(media_dir, f) 
            for f in os.listdir(media_dir) 
            if os.path.isfile(os.path.join(media_dir, f)) 
            and os.path.splitext(f)[1].lower() in const.SUPPORTED_MEDIA_TYPES
        }
        
        added_defaults = 0
        if isinstance(app_state.media_generation_status, dict):
            for f_path in current_files:
                if f_path not in app_state.media_generation_status:
                    app_state.media_generation_status[f_path] = const.DEFAULT_MEDIA_STATUS_ENTRY.copy()
                    added_defaults += 1
                    
            if added_defaults > 0:
                logging.info(f"Added default status for {added_defaults} new files")
                save_media_status(app_state, signals)
                
    except Exception as e:
        logging.error(f"Error ensuring default status entries: {e}")

# --- Media Processing Functions ---
def create_thumbnail(media_path: str) -> Optional[Image.Image]:
    """Creates a PIL thumbnail image for a given media path."""
    filename = os.path.basename(media_path)
    file_ext = os.path.splitext(filename)[1].lower()
    final_thumb_size = const.THUMBNAIL_SIZE
    
    try:
        if file_ext in const.SUPPORTED_IMAGE_TYPES:
            with Image.open(media_path) as img:
                img.thumbnail(final_thumb_size, Image.Resampling.LANCZOS)
                if img.mode == 'RGBA':
                    bg = Image.new('RGB', img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3])
                    return bg
                elif img.mode == 'P':
                    return img.convert('RGBA').convert('RGB')
                elif img.mode != 'RGB':
                    return img.convert('RGB')
                return img
                
        elif file_ext in const.SUPPORTED_VIDEO_TYPES:
            thumb = Image.new('RGB', final_thumb_size, color=(100, 100, 120))
            draw = ImageDraw.Draw(thumb)
            center_x, center_y = final_thumb_size[0] // 2, final_thumb_size[1] // 2
            offset = 15
            draw.polygon([
                (center_x - offset // 2, center_y - offset),
                (center_x - offset // 2, center_y + offset),
                (center_x + offset, center_y)
            ], fill="white")
            return thumb
            
        logging.warning(f"Unsupported media type: {filename}")
        return None
        
    except Exception as e:
        logging.exception(f"Error creating thumbnail for {filename}: {e}")
        return None

def get_video_details(video_path: str) -> Optional[Dict[str, Any]]:
    """Gets video duration and dimensions using OpenCV."""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logging.error(f"OpenCV failed to open video: {video_path}")
            return None
            
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 and frame_count > 0 else 0
        
        cap.release()
        return {
            'width': width,
            'height': height,
            'duration': math.ceil(duration)
        }
        
    except Exception as e:
        logging.exception(f"Error getting video details: {e}")
        return None

# --- Photo Editing Functions ---
def apply_photo_edits(img: Image.Image, instructions: str) -> Tuple[Optional[Image.Image], List[str]]:
    """Applies photo editing effects based on instructions."""
    if not instructions or not isinstance(img, Image.Image):
        return None, ["Invalid input"]
        
    applied_effects = []
    try:
        # Store original mode and size to restore later
        original_mode = img.mode
        original_size = img.size
        
        # Make a copy of the image to preserve the original
        img = img.copy()
        
        # Apply effects based on instructions
        if "warm" in instructions.lower():
            img = apply_warmth(img)
            applied_effects.append("Warmth")
            
        if "sepia" in instructions.lower():
            img = apply_sepia_tone(img)
            applied_effects.append("Sepia")
            
        if "vintage" in instructions.lower():
            img = apply_vintage_effect(img)
            applied_effects.append("Vintage")
            
        if "vignette" in instructions.lower():
            img = apply_vignette(img)
            applied_effects.append("Vignette")
            
        if "clarity" in instructions.lower():
            img = enhance_clarity(img)
            applied_effects.append("Clarity")
            
        if not applied_effects:
            img = apply_default_enhancement(img)
            if img:
                applied_effects.append("Default Enhancement")
        
        # Restore original mode if needed
        if original_mode != img.mode and original_mode in ('RGBA', 'RGB'):
            img = img.convert(original_mode)
                
        # Ensure we haven't lost resolution
        if img.size != original_size:
            img = img.resize(original_size, Image.Resampling.LANCZOS)
                
        return img, applied_effects
        
    except Exception as e:
        logging.exception(f"Error applying photo edits: {e}")
        return None, [f"Error: {str(e)}"]

def apply_warmth(img: Image.Image, factor: float = 1.2) -> Image.Image:
    """Applies a warm tone to the image."""
    # Ensure we're working with a copy
    img = img.copy()
    enhancer = ImageEnhance.Color(img)
    return enhancer.enhance(factor)

def apply_sepia_tone(img: Image.Image) -> Image.Image:
    """Applies a sepia tone effect to the image."""
    # Ensure we're working with a copy
    img = img.copy()
    img = img.convert('RGB')
    width, height = img.size
    pixels = img.load()
    
    for x in range(width):
        for y in range(height):
            r, g, b = pixels[x, y]
            tr = int(0.393*r + 0.769*g + 0.189*b)
            tg = int(0.349*r + 0.686*g + 0.168*b)
            tb = int(0.272*r + 0.534*g + 0.131*b)
            pixels[x, y] = (
                min(tr, 255),
                min(tg, 255),
                min(tb, 255)
            )
    return img

def apply_vintage_effect(img: Image.Image) -> Image.Image:
    """Applies a vintage film effect to the image."""
    import random
    
    # Ensure we're working with a copy
    img = img.copy()
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Apply slight blur
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # Adjust contrast and brightness
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.1)
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.9)
    
    # Add slight noise - with higher quality approach
    width, height = img.size
    noise_img = Image.new('RGB', img.size, (0, 0, 0))
    noise_pixels = noise_img.load()
    
    for x in range(width):
        for y in range(height):
            r = int(255 * (0.5 + 0.05 * (random.random() - 0.5)))
            noise_pixels[x, y] = (r, r, r)
    
    # Use more subtle blending for better quality
    img = Image.blend(img, noise_img, 0.03)
    return img

def apply_vignette(img: Image.Image, factor: float = 0.75) -> Image.Image:
    """Applies a vignette effect to the image."""
    # Ensure we're working with a copy
    img = img.copy()
    width, height = img.size
    
    # Create a high quality mask
    mask = Image.new('L', (width, height), 0)
    
    # Calculate vignette parameters
    center_x, center_y = width // 2, height // 2
    max_distance = math.sqrt(center_x**2 + center_y**2)
    
    # Create higher quality radial gradient
    for x in range(width):
        for y in range(height):
            distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            intensity = 255 * (1 - (distance / max_distance) * factor)
            mask.putpixel((x, y), int(intensity))
    
    # Preserve original mode
    original_mode = img.mode
    
    # Apply mask
    output = Image.new(original_mode, img.size)
    output.paste(img, mask=mask)
    return output

def enhance_clarity(img: Image.Image) -> Image.Image:
    """Enhances image clarity using unsharp mask."""
    # Ensure we're working with a copy
    img = img.copy()
    
    # Preserve original mode
    original_mode = img.mode
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Apply unsharp mask with higher quality settings
    img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=140, threshold=2))
    
    # Enhance contrast slightly
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.1)
    
    # Convert back to original mode if needed
    if img.mode != original_mode and original_mode in ('RGBA', 'RGB'):
        img = img.convert(original_mode)
        
    return img

def apply_default_enhancement(img: Image.Image) -> Optional[Image.Image]:
    """Applies default enhancement to improve image quality."""
    try:
        # Ensure we're working with a copy
        img = img.copy()
        
        # Preserve original mode
        original_mode = img.mode
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Enhance contrast with moderate settings
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.08)
        
        # Enhance sharpness with moderate settings
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.15)
        
        # Enhance color with moderate settings
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.08)
        
        # Convert back to original mode if needed
        if img.mode != original_mode and original_mode in ('RGBA', 'RGB'):
            img = img.convert(original_mode)
            
        return img
        
    except Exception as e:
        logging.error(f"Error in default enhancement: {e}")
        return None

# --- Meta API Integration ---
def load_meta_credentials() -> Optional[Dict[str, str]]:
    """Loads and validates Meta API credentials from the JSON file."""
    # First check if we're authenticated via the auth_handler
    if auth_handler.check_auth_status():
        try:
            # Load credentials from file which should have been updated during login
            with open(const.META_CREDENTIALS_FILE, "r", encoding='utf-8') as f:
                creds = json.load(f)
                
            # Handle legacy field names
            if creds.get('page_access_token') and not creds.get('facebook_page_access_token'):
                creds['facebook_page_access_token'] = creds['page_access_token']
                logging.info("Mapped 'page_access_token' to 'facebook_page_access_token'")
                
            if creds.get('instagram_user_id') and not creds.get('instagram_business_account_id'):
                creds['instagram_business_account_id'] = creds['instagram_user_id']
                logging.info("Mapped 'instagram_user_id' to 'instagram_business_account_id'")
                
            # Validate required fields
            required_keys = [
                "facebook_page_id",
                "facebook_page_access_token",
                "instagram_business_account_id"
            ]
            
            if not all(creds.get(key) for key in required_keys):
                logging.error(f"Missing required keys in {const.META_CREDENTIALS_FILE}")
                return None
                
            logging.info(f"Meta credentials loaded successfully from {const.META_CREDENTIALS_FILE}")
            return creds
            
        except Exception as e:
            logging.exception(f"Error loading Meta credentials: {e}")
            return None
    
    # Fallback to legacy method if not authenticated via auth_handler
    filename = const.META_CREDENTIALS_FILE
    try:
        if not os.path.exists(filename):
            logging.error(f"Credentials file not found: {filename}")
            return None
            
        with open(filename, "r", encoding='utf-8') as f:
            creds = json.load(f)
            
        # Handle legacy field names
        if creds.get('page_access_token') and not creds.get('facebook_page_access_token'):
            creds['facebook_page_access_token'] = creds['page_access_token']
            logging.info("Mapped 'page_access_token' to 'facebook_page_access_token'")
            
        if creds.get('instagram_user_id') and not creds.get('instagram_business_account_id'):
            creds['instagram_business_account_id'] = creds['instagram_user_id']
            logging.info("Mapped 'instagram_user_id' to 'instagram_business_account_id'")
            
        # Validate required keys
        required_keys = [
            "facebook_page_id",
            "facebook_page_access_token",
            "instagram_business_account_id"
        ]
        
        if not all(creds.get(key) for key in required_keys):
            logging.error(f"Missing required keys in {filename}")
            return None
            
        logging.info(f"Meta credentials loaded successfully from {filename}")
        return creds
        
    except Exception as e:
        logging.exception(f"Error loading Meta credentials: {e}")
        return None

class MediaHandler:
    """Handles media operations like loading, processing, and status tracking."""
    
    def __init__(self, app_state: AppState):
        """
        Initialize the media handler.
        
        Args:
            app_state: Application state object
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.app_state = app_state
        
        # Ensure media directories exist
        self._ensure_directories()
        
        # Load media status
        self.media_status = self._load_media_status()
        
    def _ensure_directories(self) -> None:
        """Ensure necessary directories exist."""
        os.makedirs(const.MEDIA_LIBRARY_DIR, exist_ok=True)
        os.makedirs(const.OUTPUT_DIR, exist_ok=True)
        
    def _load_media_status(self) -> Dict[str, Any]:
        """
        Load media status from JSON file.
        
        Returns:
            Dict: Media status data
        """
        try:
            if os.path.exists(const.MEDIA_STATUS_FILE):
                with open(const.MEDIA_STATUS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # Return empty structure if file doesn't exist
            return {
                "captions": {},
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error loading media status: {e}")
            # Return empty structure on error
            return {
                "captions": {},
                "last_updated": datetime.now().isoformat()
            }
            
    def save_media_status(self) -> bool:
        """
        Save media status to JSON file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update timestamp
            self.media_status["last_updated"] = datetime.now().isoformat()
            
            # Save to file
            with open(const.MEDIA_STATUS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.media_status, f, indent=2)
                
            return True
        except Exception as e:
            self.logger.error(f"Error saving media status: {e}")
            return False
            
    def get_media_files(self) -> List[str]:
        """
        Get a list of media files in the media library.
        
        Returns:
            List[str]: List of media file paths
        """
        try:
            media_files = []
            for filename in os.listdir(const.MEDIA_LIBRARY_DIR):
                filepath = os.path.join(const.MEDIA_LIBRARY_DIR, filename)
                if os.path.isfile(filepath):
                    _, ext = os.path.splitext(filename)
                    if ext.lower() in const.SUPPORTED_MEDIA_FORMATS:
                        media_files.append(filepath)
                        
            # Sort by modification time (newest first)
            media_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            return media_files
        except Exception as e:
            self.logger.error(f"Error getting media files: {e}")
            return []
            
    def load_image(self, filepath: str) -> Optional[Image.Image]:
        """
        Load an image file.
        
        Args:
            filepath: Path to the image file
            
        Returns:
            PIL.Image or None: Loaded image or None on error
        """
        try:
            if os.path.exists(filepath):
                # Open the image
                img = Image.open(filepath)
                
                # Create a copy to ensure the file isn't locked and with full quality
                img_copy = img.copy()
                
                # Make sure we're not accidentally loading a thumbnail
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    if exif and 40962 in exif and 40963 in exif:  # Check for width and height in EXIF
                        # If the loaded dimensions are smaller than EXIF, reload at full resolution
                        if img.width < exif[40962] or img.height < exif[40963]:
                            self.logger.warning(f"Image {filepath} was loaded at reduced size. Reloading at full resolution.")
                            # Try to reload at full resolution
                            img_copy = Image.open(filepath)
                            img_copy.load()  # Force loading of full image
                            img_copy = img_copy.copy()  # Make a copy to ensure file is closed
                
                return img_copy
            return None
        except Exception as e:
            self.logger.error(f"Error loading image {filepath}: {e}")
            return None
            
    def save_image(self, image: Image.Image, filepath: str, format: str = None) -> bool:
        """
        Save an image to a file.
        
        Args:
            image: PIL Image to save
            filepath: Path to save to
            format: Image format (if None, determined from filename)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate the filepath
            if not filepath or not isinstance(filepath, str):
                self.logger.error("Invalid filepath provided")
                return False
            
            # Get directory path
            directory = os.path.dirname(filepath)
            
            # Check if directory path is valid and can be created
            if directory:
                try:
                    os.makedirs(directory, exist_ok=True)
                except (OSError, PermissionError) as e:
                    self.logger.error(f"Cannot create directory {directory}: {e}")
                    return False
            
            # Determine format from filename if not provided
            if not format:
                _, ext = os.path.splitext(filepath.lower())
                if ext in ('.jpg', '.jpeg'):
                    format = 'JPEG'
                elif ext in ('.png'):
                    format = 'PNG'
                elif ext in ('.webp'):
                    format = 'WEBP'
                elif ext in ('.bmp'):
                    format = 'BMP'
                elif ext in ('.gif'):
                    format = 'GIF'
                else:
                    format = 'PNG'  # Default to PNG for best quality
            
            # Save with high quality settings based on format
            if format == 'JPEG':
                image.save(filepath, format=format, quality=100, subsampling=0)
            elif format == 'PNG':
                # PNG with minimum compression (lossless, best quality)
                image.save(filepath, format=format, compress_level=0)
            elif format == 'WEBP':
                image.save(filepath, format=format, quality=100, lossless=True)
            else:
                # Default save for other formats
                image.save(filepath, format=format)
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving image to {filepath}: {e}")
            return False
            
    def get_caption(self, media_path: str) -> Optional[str]:
        """
        Get the caption for a media file.
        
        Args:
            media_path: Path to the media file
            
        Returns:
            str or None: Caption if found, None otherwise
        """
        try:
            if "captions" in self.media_status and media_path in self.media_status["captions"]:
                return self.media_status["captions"][media_path]
            return None
        except Exception as e:
            self.logger.error(f"Error getting caption for {media_path}: {e}")
            return None
            
    def save_caption(self, media_path: str, caption: str) -> bool:
        """
        Save a caption for a media file.
        
        Args:
            media_path: Path to the media file
            caption: Caption text
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not "captions" in self.media_status:
                self.media_status["captions"] = {}
                
            self.media_status["captions"][media_path] = caption
            return self.save_media_status()
        except Exception as e:
            self.logger.error(f"Error saving caption for {media_path}: {e}")
            return False
            
    def get_image_dimensions(self, filepath: str) -> Optional[Tuple[int, int]]:
        """
        Get the dimensions of an image.
        
        Args:
            filepath: Path to the image file
            
        Returns:
            Tuple[int, int] or None: (width, height) or None on error
        """
        try:
            with Image.open(filepath) as img:
                return img.size
        except Exception as e:
            self.logger.error(f"Error getting image dimensions for {filepath}: {e}")
            return None
            
    def is_supported_media(self, filepath: str) -> bool:
        """
        Check if a file is a supported media type.
        
        Args:
            filepath: Path to the file
            
        Returns:
            bool: True if supported, False otherwise
        """
        try:
            if not os.path.isfile(filepath):
                return False
                
            _, ext = os.path.splitext(filepath)
            return ext.lower() in const.SUPPORTED_MEDIA_FORMATS
        except Exception:
            return False
            
    def get_media_info(self, filepath: str) -> Dict[str, Any]:
        """
        Get information about a media file.
        
        Args:
            filepath: Path to the media file
            
        Returns:
            Dict: Media information
        """
        try:
            if not os.path.exists(filepath):
                return {"error": "File not found"}
                
            info = {
                "path": filepath,
                "filename": os.path.basename(filepath),
                "size": os.path.getsize(filepath),
                "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                "type": "unknown"
            }
            
            # Determine file type
            _, ext = os.path.splitext(filepath)
            if ext.lower() in const.SUPPORTED_IMAGE_FORMATS:
                info["type"] = "image"
                with Image.open(filepath) as img:
                    info["dimensions"] = img.size
                    info["format"] = img.format
            elif ext.lower() in const.SUPPORTED_VIDEO_FORMATS:
                info["type"] = "video"
                # We could add more video info here if needed
            
            # Add caption if available
            caption = self.get_caption(filepath)
            if caption:
                info["caption"] = caption
                
            return info
        except Exception as e:
            self.logger.error(f"Error getting media info for {filepath}: {e}")
            return {"error": str(e)}

    def get_current_image(self) -> Optional[Image.Image]:
        """
        Get the current image with any applied edits.
        
        Returns:
            PIL.Image or None: Current image with edits or None on error
        """
        try:
            if not self.app_state.selected_media:
                return None
                
            # Load the original image with high quality settings
            original_image = self.load_image(self.app_state.selected_media)
            if not original_image:
                return None
                
            # Keep track of original mode and size
            original_mode = original_image.mode
            original_size = original_image.size
            
            # Check if we have photo editing instructions
            photo_editing = getattr(self.app_state, 'photo_editing_instructions', None)
            
            # If we have photo editing instructions, apply them
            if photo_editing:
                # Apply edits based on instructions
                edited_image, _ = apply_photo_edits(original_image, photo_editing)
                result = edited_image if edited_image else original_image
            else:
                # Return the original image if no edits
                result = original_image
            
            # Ensure we're returning an image with the correct mode and size
            if result.mode != original_mode and original_mode in ('RGBA', 'RGB'):
                result = result.convert(original_mode)
            
            if result.size != original_size:
                result = result.resize(original_size, Image.Resampling.LANCZOS)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting current image: {e}")
            return None 