"""
Image editing handler for processing images with Gemini.
"""
import os
import logging
import base64
import tempfile
import io
from typing import Dict, Any, Optional, List, Tuple, Union
from PIL import Image, ImageDraw, ImageFont, ImageStat
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..config import constants as const

# Constants
GEMINI_VISION_MODEL = "gemini-1.5-flash"  # Using flash model which is better suited for image processing
TEMP_DIR = tempfile.gettempdir()

class ImageEditHandler:
    """
    Handles advanced image editing using Gemini's generative capabilities.
    """
    
    def __init__(self):
        """Initialize the image edit handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.original_image_path = None
        self.edited_image_path = None
        self.editing_history = []
        
    def edit_image_with_gemini(self, image_path: str, edit_instructions: str) -> Tuple[bool, str, str]:
        """
        Edit an image using Gemini's generative capabilities.
        
        Args:
            image_path: Path to the image file
            edit_instructions: Instructions for how to edit the image
            
        Returns:
            Tuple[bool, str, str]: Success status, edited image path, and message
        """
        try:
            if not os.path.exists(image_path):
                return False, "", f"Image file not found: {image_path}"
                
            # Store original image path
            self.original_image_path = image_path
            
            # Check if GEMINI_API_KEY is configured
            gemini_key = os.environ.get("GEMINI_API_KEY")
            if not gemini_key:
                return False, "", "Gemini API key not configured. Set the GEMINI_API_KEY environment variable."
            
            # Configure Gemini API
            genai.configure(api_key=gemini_key)
            
            # Open and resize image to ensure it's within Gemini's limits while maintaining quality
            img = Image.open(image_path)
            
            # Determine original size and format for later
            orig_width, orig_height = img.width, img.height
            img_format = img.format if img.format else "JPEG"
            
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            # Ensure we're saving at maximum quality
            img.save(img_byte_arr, format=img_format, quality=100)
            img_byte_arr = img_byte_arr.getvalue()
            
            # Configure Gemini model with higher quality settings
            generation_config = {
                "temperature": 0.1,  # Lower temperature for more predictable results
                "top_p": 0.95,
                "top_k": 32,
                "max_output_tokens": 4096,
            }
            
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            model = genai.GenerativeModel(
                model_name=GEMINI_VISION_MODEL,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Create a prompt for image editing
            prompt = f"""
            I need you to edit this image according to these instructions:
            
            {edit_instructions}
            
            Apply these changes to the image while maintaining a professional, high-quality result.
            Ensure the edited image has the same dimensions and aspect ratio ({orig_width}x{orig_height}) as the original.
            Preserve the overall composition unless specifically instructed otherwise.
            Focus on the specified edits only.
            
            The resulting image should be high-quality and lossless.
            Return ONLY the edited image without any text.
            """
            
            # Prepare the request
            request = model.generate_content([
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": f"image/{img_format.lower()}", "data": base64.b64encode(img_byte_arr).decode()}}
                    ]
                }
            ])
            
            # Process the response and extract the image
            response = request.candidates[0].content
            self.logger.info(f"Received response from Gemini with {len(response.parts)} parts")
            
            # Look for image data in the response
            for i, part in enumerate(response.parts):
                self.logger.info(f"Checking part {i} of type: {type(part)}")
                
                if hasattr(part, "inline_data") and part.inline_data:
                    self.logger.info(f"Found inline data with mime type: {part.inline_data.mime_type}")
                    
                    if part.inline_data.mime_type.startswith("image/"):
                        # Get image data
                        try:
                            image_data = base64.b64decode(part.inline_data.data)
                            
                            # Create a temporary file for the edited image
                            file_name = os.path.basename(image_path)
                            base_name, ext = os.path.splitext(file_name)
                            edited_file_path = os.path.join(TEMP_DIR, f"{base_name}_edited{ext}")
                            
                            # Save the edited image at highest quality
                            with open(edited_file_path, "wb") as f:
                                f.write(image_data)
                            
                            # Verify the saved image
                            try:
                                edited_img = Image.open(edited_file_path)
                                edited_img.verify()  # Verify it's a valid image
                                
                                # Re-save with specific quality settings for better results
                                edited_img = Image.open(edited_file_path)
                                edited_img.save(edited_file_path, quality=100, optimize=True)
                                
                                # Update dimensions if needed to match original
                                if edited_img.size != (orig_width, orig_height):
                                    edited_img = edited_img.resize((orig_width, orig_height), Image.LANCZOS)
                                    edited_img.save(edited_file_path, quality=100, optimize=True)
                                
                                # Store the edited image path
                                self.edited_image_path = edited_file_path
                                
                                # Add to editing history
                                self.editing_history.append({
                                    "instruction": edit_instructions,
                                    "result_path": edited_file_path
                                })
                                
                                self.logger.info(f"Successfully saved edited image to {edited_file_path}")
                                return True, edited_file_path, "Image successfully edited"
                                
                            except Exception as img_error:
                                self.logger.error(f"Error verifying edited image: {img_error}")
                                return False, "", f"Invalid image data received: {str(img_error)}"
                                
                        except Exception as decode_error:
                            self.logger.error(f"Error decoding image data: {decode_error}")
                            continue
            
            # If we get here, we didn't find an image in the response
            self.logger.warning("No valid image found in Gemini response")
            
            # Let's implement a fallback to basic image filters if Gemini didn't return an image
            return self._apply_basic_edit(image_path, edit_instructions)
            
        except Exception as e:
            self.logger.error(f"Error editing image with Gemini: {e}")
            # Fall back to basic edits
            return self._apply_basic_edit(image_path, edit_instructions)
            
    def _apply_basic_edit(self, image_path: str, edit_instructions: str) -> Tuple[bool, str, str]:
        """
        Apply basic edits based on keywords in the instructions when Gemini fails.
        
        Args:
            image_path: Path to the image
            edit_instructions: Original editing instructions
            
        Returns:
            Tuple[bool, str, str]: Success status, edited image path, and message
        """
        try:
            self.logger.info("Falling back to basic image editing")
            filters = []
            
            # Extract keywords from instructions
            instructions_lower = edit_instructions.lower()
            if "black and white" in instructions_lower or "grayscale" in instructions_lower:
                filters.append("grayscale")
            if "warm" in instructions_lower:
                filters.append("warm")
            if "cool" in instructions_lower:
                filters.append("cool")
            if "sepia" in instructions_lower or "vintage" in instructions_lower:
                filters.append("sepia")
            if "contrast" in instructions_lower:
                filters.append("contrast")
            if "bright" in instructions_lower:
                filters.append("brightness")
            if "sharp" in instructions_lower or "detail" in instructions_lower:
                filters.append("sharpness")
            if "vibrant" in instructions_lower or "saturate" in instructions_lower:
                filters.append("saturation")
                
            # If no filters were identified, add contrast and brightness for some visible change
            if not filters:
                filters.extend(["contrast", "brightness"])
                
            return self.edit_image_with_filters(image_path, filters)
            
        except Exception as e:
            self.logger.error(f"Error in fallback editing: {e}")
            return False, "", f"Error applying basic edits: {str(e)}"
            
    def revert_to_original(self) -> str:
        """
        Revert to the original image.
        
        Returns:
            str: Path to the original image
        """
        return self.original_image_path if self.original_image_path else ""
    
    def get_current_edited_image(self) -> str:
        """
        Get the path to the current edited image.
        
        Returns:
            str: Path to the edited image or empty string if none
        """
        return self.edited_image_path if self.edited_image_path else ""
    
    def edit_image_with_filters(self, image_path: str, 
                              filters: List[str]) -> Tuple[bool, str, str]:
        """
        Apply basic filters to an image using PIL.
        This is a fallback when Gemini is not available.
        
        Args:
            image_path: Path to the image file
            filters: List of filter names to apply
            
        Returns:
            Tuple[bool, str, str]: Success status, edited image path, and message
        """
        try:
            if not os.path.exists(image_path):
                return False, "", f"Image file not found: {image_path}"
                
            # Store original image path
            self.original_image_path = image_path
            
            # Open the image with PIL
            img = Image.open(image_path)
            
            # Apply filters
            for filter_name in filters:
                if filter_name.lower() == "grayscale":
                    img = img.convert("L").convert("RGB")
                elif filter_name.lower() == "sepia":
                    # Simple sepia implementation
                    img = img.convert("RGB")
                    width, height = img.size
                    pixels = img.load()
                    for i in range(width):
                        for j in range(height):
                            r, g, b = pixels[i, j]
                            new_r = int(r * 0.393 + g * 0.769 + b * 0.189)
                            new_g = int(r * 0.349 + g * 0.686 + b * 0.168)
                            new_b = int(r * 0.272 + g * 0.534 + b * 0.131)
                            pixels[i, j] = (
                                min(255, new_r),
                                min(255, new_g),
                                min(255, new_b)
                            )
                elif filter_name.lower() == "contrast":
                    from PIL import ImageEnhance
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.5)
                elif filter_name.lower() == "brightness":
                    from PIL import ImageEnhance
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(1.2)
                elif filter_name.lower() == "sharpness":
                    from PIL import ImageEnhance
                    enhancer = ImageEnhance.Sharpness(img)
                    img = enhancer.enhance(1.5)
                elif filter_name.lower() == "saturation":
                    from PIL import ImageEnhance
                    enhancer = ImageEnhance.Color(img)
                    img = enhancer.enhance(1.5)
                elif filter_name.lower() == "warm":
                    # Apply warm tone by enhancing red channel
                    img = img.convert("RGB")
                    r, g, b = img.split()
                    from PIL import ImageEnhance
                    r = ImageEnhance.Brightness(r).enhance(1.2)
                    img = Image.merge("RGB", (r, g, b))
                elif filter_name.lower() == "cool":
                    # Apply cool tone by enhancing blue channel
                    img = img.convert("RGB")
                    r, g, b = img.split()
                    from PIL import ImageEnhance
                    b = ImageEnhance.Brightness(b).enhance(1.2)
                    img = Image.merge("RGB", (r, g, b))
            
            # Create a temporary file for the edited image
            file_name = os.path.basename(image_path)
            base_name, ext = os.path.splitext(file_name)
            edited_file_path = os.path.join(TEMP_DIR, f"{base_name}_edited{ext}")
            
            # Save the edited image with high quality
            img.save(edited_file_path, quality=100, optimize=True)
            
            # Store the edited image path
            self.edited_image_path = edited_file_path
            
            # Add to editing history
            self.editing_history.append({
                "instruction": ", ".join(filters),
                "result_path": edited_file_path
            })
            
            return True, edited_file_path, "Image successfully edited with filters"
            
        except Exception as e:
            self.logger.error(f"Error applying filters to image: {e}")
            return False, "", f"Error during filter application: {str(e)}"

    def optimize_for_story(self, image_path: str, target_aspect_ratio: float = 9/16, background_color=(0,0,0)) -> Tuple[bool, str, str]:
        """
        Optimizes an image for a story format (e.g., 9:16 aspect ratio).
        The image is scaled to fill the target aspect ratio by covering it, 
        and then cropped from the center if necessary. No black bars are added.
        """
        try:
            if not os.path.exists(image_path):
                return False, "", f"Image file not found: {image_path}"

            img = Image.open(image_path).convert("RGB")
            original_width, original_height = img.width, img.height
            original_aspect_ratio = original_width / original_height

            if abs(original_aspect_ratio - target_aspect_ratio) < 0.001:
                self.logger.info(f"Image {image_path} already has target aspect ratio.")
                base_name, ext = os.path.splitext(os.path.basename(image_path))
                optimized_file_path = os.path.join(TEMP_DIR, f"{base_name}_story_optimized{ext}")
                img.save(optimized_file_path, quality=95)
                return True, optimized_file_path, "Image already optimized for story."

            # Determine the dimensions of the crop box based on the target aspect ratio
            if original_aspect_ratio > target_aspect_ratio:
                # Original is wider than target (e.g., landscape for portrait target)
                # Crop the sides: height remains original, width is calculated
                crop_height = original_height
                crop_width = int(crop_height * target_aspect_ratio)
            else:
                # Original is taller or same aspect ratio (but different from target, handled above)
                # Crop the top/bottom: width remains original, height is calculated
                crop_width = original_width
                crop_height = int(crop_width / target_aspect_ratio)

            # Calculate crop box (center crop)
            left = (original_width - crop_width) / 2
            top = (original_height - crop_height) / 2
            right = left + crop_width
            bottom = top + crop_height

            cropped_img = img.crop((left, top, right, bottom))
            
            # Optional: If a specific output resolution is desired (e.g., 1080x1920 for stories)
            # Resize the cropped image here. For now, we maintain the aspect ratio 
            # with the cropped dimensions.
            # Example for fixed output size:
            # target_output_w, target_output_h = 1080, 1920 
            # if cropped_img.width != target_output_w or cropped_img.height != target_output_h:
            #    cropped_img = cropped_img.resize((target_output_w, target_output_h), Image.Resampling.LANCZOS)

            base_name, ext = os.path.splitext(os.path.basename(image_path))
            optimized_file_path = os.path.join(TEMP_DIR, f"{base_name}_story_optimized{ext}")
            cropped_img.save(optimized_file_path, quality=95)
            self.logger.info(f"Successfully saved story-optimized image to {optimized_file_path} with new dimensions {cropped_img.size}")
            return True, optimized_file_path, "Image successfully optimized for story."

        except Exception as e:
            self.logger.error(f"Error optimizing image for story: {e}", exc_info=True)
            return False, "", f"Error optimizing image for story: {str(e)}"

    def add_caption_overlay(self, image_path: str, caption_text: str, 
                              position: str = "bottom",
                              font_path: Optional[str] = None, 
                              font_size_px: int = 0, 
                              padding: int = 20) -> Tuple[bool, str, str]:
        """
        Adds a text caption overlay to an image.
        Text is white with a black outline, no background box.
        """
        try:
            if not os.path.exists(image_path):
                return False, "", f"Image file not found: {image_path}"

            img = Image.open(image_path).convert("RGBA")
            draw = ImageDraw.Draw(img)
            img_width, img_height = img.size

            actual_font_path = font_path if font_path and os.path.exists(font_path) else const.DEFAULT_FONT_PATH
            # dynamic_font_size is already calculated based on image height / settings

            if not os.path.exists(actual_font_path):
                self.logger.warning(
                    f"Custom font not found at {actual_font_path}. Using PIL default. "
                    f"Font sizing will be very limited and may not reflect chosen sizes accurately. "
                    f"Please install a .ttf font (e.g., opensans.ttf) at the specified path for best results."
                )
                # Attempt to use font_size_px as a hint for the default font, results may vary significantly
                try:
                    font = ImageFont.load_default(size=font_size_px)
                except TypeError:
                    # Older PIL versions might not accept size, or it may not be effective
                    font = ImageFont.load_default() 
                # dynamic_font_size is already set from MainWindow, we'll use it for calculations,
                # but the visual rendering with default font might not match.
            else:
                try:
                    font = ImageFont.truetype(actual_font_path, font_size_px)
                except IOError:
                    self.logger.warning(f"Could not load font {actual_font_path}. Using PIL default. Sizing issues may occur.")
                    try:
                        font = ImageFont.load_default(size=font_size_px)
                    except TypeError:
                        font = ImageFont.load_default()
            
            # Ensure dynamic_font_size is at least a minimum usable value for calculations
            # The actual rendered size with default font might still be fixed.
            # dynamic_font_size = max(10, font_size_px) # font_size_px is already calculated and constrained in MainWindow

            lines = []
            words = caption_text.split()
            current_line = ""
            max_text_width = img_width - (2 * padding)

            for word in words:
                # Check width with the current font
                if hasattr(font, 'getbbox'):
                    test_line_bbox = font.getbbox(current_line + word + " ")
                    test_line_width = test_line_bbox[2] - test_line_bbox[0]
                elif hasattr(font, 'getsize'):
                    test_line_width, _ = font.getsize(current_line + word + " ")
                else: 
                    test_line_width = len(current_line + word + " ") * (font_size_px * 0.6)

                if test_line_width <= max_text_width:
                    current_line += word + " "
                else:
                    lines.append(current_line.strip())
                    current_line = word + " "
            lines.append(current_line.strip())

            total_text_height = 0
            line_heights = []
            for line_idx, line_content in enumerate(lines):
                if hasattr(font, 'getbbox'):
                    line_bbox = font.getbbox(line_content)
                    h = line_bbox[3] - line_bbox[1]
                elif hasattr(font, 'getsize'):
                    _, h = font.getsize(line_content)
                else:
                    h = font_size_px 
                line_heights.append(h)
                total_text_height += h
                if line_idx < len(lines) - 1:
                    total_text_height += (font_size_px // 4) 

            if position == "top":
                text_start_y = padding
            elif position == "center":
                text_start_y = (img_height - total_text_height) / 2
            else: # bottom
                text_start_y = img_height - total_text_height - padding
            
            current_y = text_start_y
            # Make outline radius and thickness more substantial for visibility
            # outline_radius = max(1, font_size_px // 15)
            outline_thickness = max(1, int(font_size_px * 0.06)) # e.g., for 30px font, ~2px outline
            outline_thickness = min(outline_thickness, 5) # Cap thickness to avoid excessive blockiness for very large fonts

            # Determine optimal text color based on background
            # Calculate the bounding box of the entire text block
            text_block_x_positions = []
            max_text_block_width = 0
            for line_content_for_bbox in lines:
                if hasattr(font, 'getbbox'):
                    line_bbox_for_calc = font.getbbox(line_content_for_bbox)
                    text_width_for_calc = line_bbox_for_calc[2] - line_bbox_for_calc[0]
                elif hasattr(font, 'getsize'):
                    text_width_for_calc, _ = font.getsize(line_content_for_bbox)
                else:
                    text_width_for_calc = len(line_content_for_bbox) * (font_size_px * 0.6)
                text_block_x_positions.append((img_width - text_width_for_calc) / 2)
                if text_width_for_calc > max_text_block_width:
                    max_text_block_width = text_width_for_calc
            
            text_block_left = min(text_block_x_positions) if text_block_x_positions else padding
            text_block_right = text_block_left + max_text_block_width
            text_block_top = text_start_y
            text_block_bottom = text_start_y + total_text_height

            # Ensure coordinates are within image bounds and are integers
            text_block_left = max(0, int(text_block_left))
            text_block_top = max(0, int(text_block_top))
            text_block_right = min(img_width, int(text_block_right))
            text_block_bottom = min(img_height, int(text_block_bottom))

            text_color = (255, 255, 255, 255) # Default white
            outline_color = (0, 0, 0, 255) # Default black

            if text_block_right > text_block_left and text_block_bottom > text_block_top:
                # Crop the region of the original image where text will be placed
                # Use a copy of the image for analysis to avoid altering the one being drawn on prematurely
                image_for_analysis = img.copy() 
                background_region = image_for_analysis.crop((text_block_left, text_block_top, text_block_right, text_block_bottom))
                
                if background_region.size[0] > 0 and background_region.size[1] > 0:
                    # Convert to grayscale and get average pixel brightness
                    avg_brightness = ImageStat.Stat(background_region.convert('L')).mean[0]
                    self.logger.info(f"Average brightness of background for text: {avg_brightness}")
                    if avg_brightness < 128: # Dark background
                        text_color = (255, 255, 255, 255) # White text
                        outline_color = (0, 0, 0, 255)   # Black outline
                    else: # Light background
                        text_color = (0, 0, 0, 255)       # Black text
                        outline_color = (255, 255, 255, 255) # White outline
                else:
                    self.logger.warning("Background region for text analysis is empty.")        
            else:
                self.logger.warning("Cannot determine text background region, using default text colors.")

            for i, line in enumerate(lines):
                if hasattr(font, 'getbbox'):
                    line_bbox = font.getbbox(line)
                    text_width = line_bbox[2] - line_bbox[0]
                elif hasattr(font, 'getsize'):
                    text_width, _ = font.getsize(line)
                else:
                    text_width = len(line) * (font_size_px*0.6)

                x_position = (img_width - text_width) / 2 

                # Draw thicker outline (black)
                # Iterate for a thicker outline effect by drawing multiple offset texts
                for dx in range(-outline_thickness, outline_thickness + 1):
                    for dy in range(-outline_thickness, outline_thickness + 1):
                        # Optional: for a more rounded/less boxy thick outline, 
                        # you could check if (dx*dx + dy*dy) is within a certain radius squared,
                        # but for simplicity, a square boundary for offsets works well for thickness.
                        if dx != 0 or dy != 0: # Don't redraw at the exact same spot as the main text yet
                           draw.text((x_position + dx, current_y + dy), line, font=font, fill=outline_color) # Use determined outline color
                
                # Draw main text (white) over the outline
                draw.text((x_position, current_y), line, font=font, fill=text_color) # Use determined text color
                
                current_y += line_heights[i] + (font_size_px // 4)

            base_name, ext = os.path.splitext(os.path.basename(image_path))
            overlay_file_path = os.path.join(TEMP_DIR, f"{base_name}_caption_overlay{ext}")
            
            if img.mode == 'RGBA' and ext.lower() in ['.jpg', '.jpeg']:
                final_img = img.convert('RGB')
            else:
                final_img = img

            final_img.save(overlay_file_path, quality=95)
            self.logger.info(f"Successfully saved image with caption overlay to {overlay_file_path}")
            return True, overlay_file_path, "Image successfully updated with caption overlay."

        except Exception as e:
            self.logger.error(f"Error adding caption overlay: {e}", exc_info=True)
            return False, "", f"Error adding caption overlay: {str(e)}" 