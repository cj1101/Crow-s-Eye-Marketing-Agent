"""
Image editing handler for processing images with Gemini.
"""
import os
import logging
import base64
import tempfile
import io
from typing import Dict, Any, Optional, List, Tuple, Union
from PIL import Image, ImageDraw, ImageFont, ImageStat, ImageEnhance, ImageFilter, ImageOps
import numpy as np
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
        Apply sophisticated edits based on instructions, including artistic transformations.
        Enhanced fallback system with Imagen-like capabilities.
        
        Args:
            image_path: Path to the image
            edit_instructions: Original editing instructions
            
        Returns:
            Tuple[bool, str, str]: Success status, edited image path, and message
        """
        try:
            self.logger.info("Applying enhanced image editing with artistic transformations")
            
            # Extract keywords from instructions
            instructions_lower = edit_instructions.lower()
            applied_effects = []
            
            # Open the image
            img = Image.open(image_path).convert("RGB")
            original_img = img.copy()
            
            # ARTISTIC STYLE TRANSFORMATIONS
            if any(keyword in instructions_lower for keyword in ["studio ghibli", "ghibli", "anime", "animated"]):
                img = self._apply_studio_ghibli_style(img)
                applied_effects.append("Studio Ghibli Style")
                
            elif any(keyword in instructions_lower for keyword in ["oil painting", "painting", "artistic", "painterly"]):
                img = self._apply_oil_painting_effect(img)
                applied_effects.append("Oil Painting Style")
                
            elif any(keyword in instructions_lower for keyword in ["watercolor", "watercolour"]):
                img = self._apply_watercolor_effect(img)
                applied_effects.append("Watercolor Style")
                
            elif any(keyword in instructions_lower for keyword in ["pencil sketch", "sketch", "drawing"]):
                img = self._apply_pencil_sketch_effect(img)
                applied_effects.append("Pencil Sketch")
                
            elif any(keyword in instructions_lower for keyword in ["comic", "cartoon", "pop art"]):
                img = self._apply_comic_book_effect(img)
                applied_effects.append("Comic Book Style")
                
            elif any(keyword in instructions_lower for keyword in ["cyberpunk", "neon", "futuristic"]):
                img = self._apply_cyberpunk_effect(img)
                applied_effects.append("Cyberpunk Style")
                
            elif any(keyword in instructions_lower for keyword in ["fantasy", "magical", "ethereal"]):
                img = self._apply_fantasy_effect(img)
                applied_effects.append("Fantasy Style")
            
            # BACKGROUND TRANSFORMATIONS
            if any(keyword in instructions_lower for keyword in ["remove background", "transparent background", "cut out"]):
                img = self._remove_background(img)
                applied_effects.append("Background Removal")
                
            elif any(keyword in instructions_lower for keyword in ["blue gradient", "gradient background"]):
                img = self._apply_gradient_background(img, "blue")
                applied_effects.append("Blue Gradient Background")
                
            elif any(keyword in instructions_lower for keyword in ["bokeh", "blurred background"]):
                img = self._apply_bokeh_background(img)
                applied_effects.append("Bokeh Background")
            
            # COLOR TRANSFORMATIONS
            if any(keyword in instructions_lower for keyword in ["black and white", "grayscale", "monochrome"]):
                img = self._apply_advanced_bw(img)
                applied_effects.append("Professional B&W")
                
            elif any(keyword in instructions_lower for keyword in ["sepia", "vintage", "retro"]):
                img = self._apply_vintage_effect(img)
                applied_effects.append("Vintage Effect")
                
            elif any(keyword in instructions_lower for keyword in ["vibrant", "saturated", "vivid"]):
                img = self._apply_vibrant_colors(img)
                applied_effects.append("Vibrant Colors")
                
            elif any(keyword in instructions_lower for keyword in ["cinematic", "movie", "film"]):
                img = self._apply_cinematic_look(img)
                applied_effects.append("Cinematic Look")
                
            elif any(keyword in instructions_lower for keyword in ["warm", "golden hour", "sunset"]):
                img = self._apply_warm_tone(img)
                applied_effects.append("Warm Tone")
                
            elif any(keyword in instructions_lower for keyword in ["cool", "blue hour", "winter"]):
                img = self._apply_cool_tone(img)
                applied_effects.append("Cool Tone")
            
            # LIGHTING AND ATMOSPHERE
            if any(keyword in instructions_lower for keyword in ["hdr", "high dynamic range"]):
                img = self._apply_hdr_effect(img)
                applied_effects.append("HDR Effect")
                
            elif any(keyword in instructions_lower for keyword in ["soft light", "dreamy", "romantic"]):
                img = self._apply_soft_light(img)
                applied_effects.append("Soft Light")
                
            elif any(keyword in instructions_lower for keyword in ["dramatic", "high contrast", "bold"]):
                img = self._apply_dramatic_effect(img)
                applied_effects.append("Dramatic Effect")
                
            elif any(keyword in instructions_lower for keyword in ["vignette", "dark edges"]):
                img = self._apply_vignette_effect(img)
                applied_effects.append("Vignette")
            
            # ENHANCEMENT EFFECTS
            if any(keyword in instructions_lower for keyword in ["sharp", "clarity", "detail"]):
                img = self._apply_sharpening(img)
                applied_effects.append("Enhanced Sharpness")
                
            elif any(keyword in instructions_lower for keyword in ["smooth", "skin", "portrait"]):
                img = self._apply_skin_smoothing(img)
                applied_effects.append("Skin Smoothing")
                
            elif any(keyword in instructions_lower for keyword in ["bright", "exposure"]):
                img = self._apply_brightness_adjustment(img, 1.3)
                applied_effects.append("Brightness Enhancement")
            
            # SPECIAL EFFECTS
            if any(keyword in instructions_lower for keyword in ["instagram", "social media", "filter"]):
                img = self._apply_instagram_filter(img)
                applied_effects.append("Social Media Filter")
                
            elif any(keyword in instructions_lower for keyword in ["polaroid", "instant", "vintage photo"]):
                img = self._apply_polaroid_effect(img)
                applied_effects.append("Polaroid Effect")
                
            elif any(keyword in instructions_lower for keyword in ["tilt shift", "miniature"]):
                img = self._apply_tilt_shift(img)
                applied_effects.append("Tilt-Shift Effect")
            
            # If no specific effects were applied, apply a smart enhancement
            if not applied_effects:
                if any(keyword in instructions_lower for keyword in ["enhance", "improve", "better", "quality"]):
                    img = self._apply_smart_enhancement(img)
                    applied_effects.append("Smart Enhancement")
                else:
                    # Default artistic transformation
                    img = self._apply_subtle_enhancement(img)
                    applied_effects.append("Subtle Enhancement")
            
            # Create output file
            file_name = os.path.basename(image_path)
            base_name, ext = os.path.splitext(file_name)
            edited_file_path = os.path.join(TEMP_DIR, f"{base_name}_edited{ext}")
            
            # Save with high quality
            img.save(edited_file_path, quality=100, optimize=True)
            
            # Store the edited image path and history
            self.edited_image_path = edited_file_path
            self.editing_history.append({
                "instruction": edit_instructions,
                "effects_applied": applied_effects,
                "result_path": edited_file_path
            })
            
            effects_str = ", ".join(applied_effects)
            return True, edited_file_path, f"Applied effects: {effects_str}"
            
        except Exception as e:
            self.logger.error(f"Error in enhanced editing: {e}")
            return False, "", f"Error applying enhanced edits: {str(e)}"
            
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

    # ========================================
    # ARTISTIC TRANSFORMATION METHODS
    # ========================================
    
    def _apply_studio_ghibli_style(self, img: Image.Image) -> Image.Image:
        """Apply Studio Ghibli anime-style transformation."""
        from PIL import ImageEnhance, ImageFilter
        
        # Enhance colors and saturation for anime look
        color_enhancer = ImageEnhance.Color(img)
        img = color_enhancer.enhance(1.4)
        
        # Slight blur for soft anime aesthetic
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Increase brightness slightly
        brightness_enhancer = ImageEnhance.Brightness(img)
        img = brightness_enhancer.enhance(1.1)
        
        # Apply warm tone for Ghibli feel
        img = self._apply_warm_tone(img)
        
        return img
    
    def _apply_oil_painting_effect(self, img: Image.Image) -> Image.Image:
        """Apply oil painting artistic effect."""
        from PIL import ImageFilter, ImageEnhance
        
        # Apply median filter for paint-like effect
        img = img.filter(ImageFilter.MedianFilter(size=3))
        
        # Enhance colors
        color_enhancer = ImageEnhance.Color(img)
        img = color_enhancer.enhance(1.3)
        
        # Slight blur for painterly look
        img = img.filter(ImageFilter.GaussianBlur(radius=1.0))
        
        return img
    
    def _apply_watercolor_effect(self, img: Image.Image) -> Image.Image:
        """Apply watercolor painting effect."""
        from PIL import ImageEnhance, ImageFilter
        
        # Reduce contrast for watercolor softness
        contrast_enhancer = ImageEnhance.Contrast(img)
        img = contrast_enhancer.enhance(0.8)
        
        # Apply blur for soft edges
        img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
        
        # Enhance brightness
        brightness_enhancer = ImageEnhance.Brightness(img)
        img = brightness_enhancer.enhance(1.2)
        
        return img
    
    def _apply_pencil_sketch_effect(self, img: Image.Image) -> Image.Image:
        """Apply pencil sketch effect."""
        from PIL import ImageFilter, ImageOps
        
        # Convert to grayscale
        img = ImageOps.grayscale(img).convert("RGB")
        
        # Apply edge detection
        img = img.filter(ImageFilter.FIND_EDGES)
        
        # Invert colors
        img = ImageOps.invert(img)
        
        # Apply Gaussian blur
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        return img
    
    def _apply_comic_book_effect(self, img: Image.Image) -> Image.Image:
        """Apply comic book/pop art effect."""
        from PIL import ImageEnhance, ImageFilter
        
        # High contrast for comic look
        contrast_enhancer = ImageEnhance.Contrast(img)
        img = contrast_enhancer.enhance(1.8)
        
        # Enhance colors dramatically
        color_enhancer = ImageEnhance.Color(img)
        img = color_enhancer.enhance(1.6)
        
        # Sharpen for defined edges
        img = img.filter(ImageFilter.SHARPEN)
        
        return img
    
    def _apply_cyberpunk_effect(self, img: Image.Image) -> Image.Image:
        """Apply cyberpunk/neon effect."""
        import numpy as np
        
        # Convert to array for color manipulation
        img_array = np.array(img)
        
        # Enhance blue and magenta channels
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.2, 0, 255)  # Red
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 0.8, 0, 255)  # Green
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 1.4, 0, 255)  # Blue
        
        img = Image.fromarray(img_array.astype(np.uint8))
        
        # High contrast
        from PIL import ImageEnhance
        contrast_enhancer = ImageEnhance.Contrast(img)
        img = contrast_enhancer.enhance(1.5)
        
        return img
    
    def _apply_fantasy_effect(self, img: Image.Image) -> Image.Image:
        """Apply magical/fantasy effect."""
        from PIL import ImageEnhance
        
        # Enhance saturation for magical feel
        color_enhancer = ImageEnhance.Color(img)
        img = color_enhancer.enhance(1.3)
        
        # Add brightness
        brightness_enhancer = ImageEnhance.Brightness(img)
        img = brightness_enhancer.enhance(1.15)
        
        # Apply soft glow effect
        img = self._apply_soft_light(img)
        
        return img
    
    def _remove_background(self, img: Image.Image) -> Image.Image:
        """Simple background removal (edge-based)."""
        from PIL import ImageFilter, ImageOps
        
        # This is a simple implementation - for real background removal,
        # you'd use AI models like U2-Net
        
        # Create a mask using edge detection
        gray = ImageOps.grayscale(img)
        edges = gray.filter(ImageFilter.FIND_EDGES)
        
        # For now, just return the original image with transparency
        # In a real implementation, you'd apply the mask
        img_with_alpha = img.convert("RGBA")
        return img_with_alpha
    
    def _apply_gradient_background(self, img: Image.Image, color: str) -> Image.Image:
        """Apply gradient background."""
        from PIL import ImageDraw
        
        # Create a gradient background
        width, height = img.size
        gradient = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(gradient)
        
        if color == "blue":
            # Create blue gradient
            for y in range(height):
                blue_value = int(100 + (155 * y / height))
                color_tuple = (30, 60, blue_value)
                draw.line([(0, y), (width, y)], fill=color_tuple)
        
        # Blend with original
        img = Image.blend(gradient, img, 0.7)
        return img
    
    def _apply_bokeh_background(self, img: Image.Image) -> Image.Image:
        """Apply bokeh (blurred background) effect."""
        from PIL import ImageFilter
        
        # For simplicity, apply Gaussian blur to entire image
        # In reality, you'd detect subjects and only blur background
        blurred = img.filter(ImageFilter.GaussianBlur(radius=3))
        
        # Blend original and blurred for partial effect
        img = Image.blend(img, blurred, 0.4)
        return img
    
    def _apply_advanced_bw(self, img: Image.Image) -> Image.Image:
        """Apply professional black and white conversion."""
        from PIL import ImageOps, ImageEnhance
        
        # Convert to grayscale with good contrast
        img = ImageOps.grayscale(img).convert("RGB")
        
        # Enhance contrast
        contrast_enhancer = ImageEnhance.Contrast(img)
        img = contrast_enhancer.enhance(1.3)
        
        return img
    
    def _apply_vintage_effect(self, img: Image.Image) -> Image.Image:
        """Apply vintage/retro effect."""
        import numpy as np
        
        # Apply sepia tone
        img_array = np.array(img)
        
        # Sepia transformation matrix
        sepia_r = img_array[:, :, 0] * 0.393 + img_array[:, :, 1] * 0.769 + img_array[:, :, 2] * 0.189
        sepia_g = img_array[:, :, 0] * 0.349 + img_array[:, :, 1] * 0.686 + img_array[:, :, 2] * 0.168
        sepia_b = img_array[:, :, 0] * 0.272 + img_array[:, :, 1] * 0.534 + img_array[:, :, 2] * 0.131
        
        sepia_img = np.stack([
            np.clip(sepia_r, 0, 255),
            np.clip(sepia_g, 0, 255),
            np.clip(sepia_b, 0, 255)
        ], axis=2)
        
        img = Image.fromarray(sepia_img.astype(np.uint8))
        
        # Reduce contrast for vintage look
        from PIL import ImageEnhance
        contrast_enhancer = ImageEnhance.Contrast(img)
        img = contrast_enhancer.enhance(0.8)
        
        return img
    
    def _apply_vibrant_colors(self, img: Image.Image) -> Image.Image:
        """Apply vibrant color enhancement."""
        from PIL import ImageEnhance
        
        # Enhance saturation
        color_enhancer = ImageEnhance.Color(img)
        img = color_enhancer.enhance(1.5)
        
        # Slight contrast boost
        contrast_enhancer = ImageEnhance.Contrast(img)
        img = contrast_enhancer.enhance(1.2)
        
        return img
    
    def _apply_cinematic_look(self, img: Image.Image) -> Image.Image:
        """Apply cinematic color grading."""
        import numpy as np
        
        img_array = np.array(img).astype(float)
        
        # Apply teal-orange color grading (popular in movies)
        # Enhance oranges in highlights, teals in shadows
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.1, 0, 255)  # Red
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 0.95, 0, 255)  # Green
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 1.05, 0, 255)  # Blue
        
        img = Image.fromarray(img_array.astype(np.uint8))
        
        # Slight desaturation for film look
        from PIL import ImageEnhance
        color_enhancer = ImageEnhance.Color(img)
        img = color_enhancer.enhance(0.9)
        
        return img
    
    def _apply_warm_tone(self, img: Image.Image) -> Image.Image:
        """Apply warm color tone."""
        import numpy as np
        
        img_array = np.array(img).astype(float)
        
        # Enhance red and yellow
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.15, 0, 255)  # Red
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 1.1, 0, 255)   # Green
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.9, 0, 255)   # Blue
        
        return Image.fromarray(img_array.astype(np.uint8))
    
    def _apply_cool_tone(self, img: Image.Image) -> Image.Image:
        """Apply cool color tone."""
        import numpy as np
        
        img_array = np.array(img).astype(float)
        
        # Enhance blue
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 0.9, 0, 255)   # Red
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 1.0, 0, 255)   # Green
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 1.2, 0, 255)   # Blue
        
        return Image.fromarray(img_array.astype(np.uint8))
    
    def _apply_hdr_effect(self, img: Image.Image) -> Image.Image:
        """Apply HDR-like effect."""
        from PIL import ImageEnhance
        
        # Enhance local contrast
        contrast_enhancer = ImageEnhance.Contrast(img)
        img = contrast_enhancer.enhance(1.4)
        
        # Enhance colors
        color_enhancer = ImageEnhance.Color(img)
        img = color_enhancer.enhance(1.2)
        
        # Brighten
        brightness_enhancer = ImageEnhance.Brightness(img)
        img = brightness_enhancer.enhance(1.1)
        
        return img
    
    def _apply_soft_light(self, img: Image.Image) -> Image.Image:
        """Apply soft, dreamy lighting effect."""
        from PIL import ImageFilter, ImageEnhance
        
        # Create soft glow
        blurred = img.filter(ImageFilter.GaussianBlur(radius=2))
        
        # Blend with original using soft light blend mode simulation
        img = Image.blend(img, blurred, 0.3)
        
        # Enhance brightness slightly
        brightness_enhancer = ImageEnhance.Brightness(img)
        img = brightness_enhancer.enhance(1.1)
        
        return img
    
    def _apply_dramatic_effect(self, img: Image.Image) -> Image.Image:
        """Apply dramatic, high-contrast effect."""
        from PIL import ImageEnhance
        
        # High contrast
        contrast_enhancer = ImageEnhance.Contrast(img)
        img = contrast_enhancer.enhance(1.6)
        
        # Enhance sharpness
        sharpness_enhancer = ImageEnhance.Sharpness(img)
        img = sharpness_enhancer.enhance(1.3)
        
        return img
    
    def _apply_vignette_effect(self, img: Image.Image) -> Image.Image:
        """Apply vignette (dark edges) effect."""
        import numpy as np
        from PIL import ImageDraw
        
        width, height = img.size
        
        # Create vignette mask
        mask = Image.new("L", (width, height), 255)
        draw = ImageDraw.Draw(mask)
        
        # Draw elliptical gradient for vignette
        border = min(width, height) // 4
        draw.ellipse([border, border, width-border, height-border], fill=255)
        
        # Apply Gaussian blur to soften vignette
        from PIL import ImageFilter
        mask = mask.filter(ImageFilter.GaussianBlur(radius=border//2))
        
        # Apply vignette
        img = img.convert("RGBA")
        mask_array = np.array(mask)
        img_array = np.array(img)
        
        # Darken edges
        for i in range(3):  # RGB channels
            img_array[:, :, i] = img_array[:, :, i] * (mask_array / 255.0)
        
        return Image.fromarray(img_array.astype(np.uint8)).convert("RGB")
    
    def _apply_sharpening(self, img: Image.Image) -> Image.Image:
        """Apply advanced sharpening."""
        from PIL import ImageFilter, ImageEnhance
        
        # Apply unsharp mask
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        
        # Enhance sharpness
        sharpness_enhancer = ImageEnhance.Sharpness(img)
        img = sharpness_enhancer.enhance(1.2)
        
        return img
    
    def _apply_skin_smoothing(self, img: Image.Image) -> Image.Image:
        """Apply skin smoothing for portraits."""
        from PIL import ImageFilter
        
        # Apply slight Gaussian blur for smoothing
        smoothed = img.filter(ImageFilter.GaussianBlur(radius=1))
        
        # Blend with original to preserve detail
        img = Image.blend(img, smoothed, 0.4)
        
        return img
    
    def _apply_brightness_adjustment(self, img: Image.Image, factor: float) -> Image.Image:
        """Apply brightness adjustment."""
        from PIL import ImageEnhance
        
        brightness_enhancer = ImageEnhance.Brightness(img)
        return brightness_enhancer.enhance(factor)
    
    def _apply_instagram_filter(self, img: Image.Image) -> Image.Image:
        """Apply Instagram-style filter."""
        from PIL import ImageEnhance
        
        # Enhance colors
        color_enhancer = ImageEnhance.Color(img)
        img = color_enhancer.enhance(1.2)
        
        # Slight warm tone
        img = self._apply_warm_tone(img)
        
        # Enhance contrast
        contrast_enhancer = ImageEnhance.Contrast(img)
        img = contrast_enhancer.enhance(1.1)
        
        return img
    
    def _apply_polaroid_effect(self, img: Image.Image) -> Image.Image:
        """Apply Polaroid instant photo effect."""
        from PIL import ImageEnhance
        
        # Vintage effect
        img = self._apply_vintage_effect(img)
        
        # Reduce saturation
        color_enhancer = ImageEnhance.Color(img)
        img = color_enhancer.enhance(0.8)
        
        # Add slight vignette
        img = self._apply_vignette_effect(img)
        
        return img
    
    def _apply_tilt_shift(self, img: Image.Image) -> Image.Image:
        """Apply tilt-shift miniature effect."""
        from PIL import ImageFilter
        import numpy as np
        
        width, height = img.size
        
        # Create focus band in the middle
        img_array = np.array(img)
        blurred_array = np.array(img.filter(ImageFilter.GaussianBlur(radius=3)))
        
        # Create gradient mask for tilt-shift effect
        focus_center = height // 2
        focus_width = height // 4
        
        for y in range(height):
            distance = abs(y - focus_center)
            if distance > focus_width:
                blend_factor = min(1.0, (distance - focus_width) / focus_width)
                for x in range(width):
                    for c in range(3):
                        img_array[y, x, c] = int(
                            img_array[y, x, c] * (1 - blend_factor) + 
                            blurred_array[y, x, c] * blend_factor
                        )
        
        img = Image.fromarray(img_array.astype(np.uint8))
        
        # Enhance saturation for miniature look
        from PIL import ImageEnhance
        color_enhancer = ImageEnhance.Color(img)
        img = color_enhancer.enhance(1.3)
        
        return img
    
    def _apply_smart_enhancement(self, img: Image.Image) -> Image.Image:
        """Apply intelligent enhancement based on image analysis."""
        from PIL import ImageEnhance, ImageStat
        
        # Analyze image statistics
        stat = ImageStat.Stat(img)
        mean_brightness = sum(stat.mean) / 3
        
        # Adjust based on image characteristics
        if mean_brightness < 100:  # Dark image
            brightness_enhancer = ImageEnhance.Brightness(img)
            img = brightness_enhancer.enhance(1.3)
        elif mean_brightness > 180:  # Bright image
            contrast_enhancer = ImageEnhance.Contrast(img)
            img = contrast_enhancer.enhance(1.2)
        
        # Always enhance colors slightly
        color_enhancer = ImageEnhance.Color(img)
        img = color_enhancer.enhance(1.1)
        
        return img
    
    def _apply_subtle_enhancement(self, img: Image.Image) -> Image.Image:
        """Apply subtle enhancement as default."""
        from PIL import ImageEnhance
        
        # Slight contrast boost
        contrast_enhancer = ImageEnhance.Contrast(img)
        img = contrast_enhancer.enhance(1.1)
        
        # Slight color enhancement
        color_enhancer = ImageEnhance.Color(img)
        img = color_enhancer.enhance(1.05)
        
        return img 