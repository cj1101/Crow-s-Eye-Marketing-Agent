"""
Image editing handler for processing images with Gemini.
"""
import os
import logging
import base64
import tempfile
import io
from typing import Dict, Any, Optional, List, Tuple, Union
from PIL import Image
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