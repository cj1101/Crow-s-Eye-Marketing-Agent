"""
AI caption generation handler for Breadsmith Marketing Tool.
"""
import logging
import uuid
import os
import base64
from typing import Dict, Any, Optional, List, Tuple
import random
from PIL import Image, ImageStat, ImageFilter
import google.generativeai as genai
from dotenv import load_dotenv

from ..config import constants as const
from ..models.app_state import AppState
from ..utils.file_reader import extract_context_from_files

# Load API key from environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Define Gemini model names
GEMINI_VISION_MODEL = "gemini-1.5-flash"  # For image analysis
GEMINI_TEXT_MODEL = "gemini-1.5-flash"    # For text generation

class AIHandler:
    """
    Handles AI caption generation functionality.
    """
    
    def __init__(self, app_state: AppState):
        """
        Initialize the AI handler.
        
        Args:
            app_state: Application state object
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.app_state = app_state
    
    def generate_caption(self, instructions: str, photo_editing: str, 
                         context_files: List[str] = None,
                         keep_existing_caption: bool = False) -> str:
        """
        Generate a caption based on instructions, photo editing, and context files.
        
        Args:
            instructions: General instructions for the AI
            photo_editing: Photo editing instructions
            context_files: List of context file paths
            keep_existing_caption: Whether to keep existing caption (if available)
            
        Returns:
            str: Generated caption
        """
        try:
            self.logger.info(f"Generating caption with instructions: {instructions[:50]}...")
            
            # If "keep_existing_caption" is True and we have a current caption, return it
            if keep_existing_caption and hasattr(self.app_state, 'current_caption') and self.app_state.current_caption:
                self.logger.info("Keeping existing caption as requested")
                return self.app_state.current_caption
            
            # Extract context from files if provided
            context_content = ""
            if context_files:
                self.logger.info(f"Extracting context from {len(context_files)} files")
                context_content = extract_context_from_files(context_files)
                if context_content:
                    self.logger.info(f"Extracted {len(context_content)} characters of context")
            
            # Get the selected media file
            selected_media = None
            if hasattr(self.app_state, 'selected_media'):
                selected_media = self.app_state.selected_media
                self.logger.info(f"Selected media for caption generation: {selected_media}")
            
            # Analyze image if it's a supported format
            image_analysis = {}
            content_analysis = {}
            if selected_media and os.path.exists(selected_media):
                _, ext = os.path.splitext(selected_media.lower())
                if ext in const.SUPPORTED_IMAGE_FORMATS:
                    self.logger.info(f"Analyzing image: {selected_media}")
                    
                    # Get technical analysis
                    image_analysis = self._analyze_image(selected_media)
                    self.logger.info(f"Technical image analysis complete")
                    
                    # Get content analysis using Gemini
                    content_analysis = self._analyze_image_content_with_gemini(selected_media)
                    self.logger.info(f"Gemini content analysis complete")
            
            # Generate caption using context files, instructions, and image analysis
            caption = self._generate_caption_with_gemini(
                instructions, 
                photo_editing, 
                context_content,
                image_analysis,
                content_analysis
            )
            
            # Save the generated caption to app state
            self.app_state.current_caption = caption
            
            return caption
            
        except Exception as e:
            self.logger.error(f"Error generating caption: {e}")
            return f"Error generating caption: {str(e)}"
    
    def _analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze an image to identify its technical characteristics.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict: Analysis results
        """
        try:
            analysis = {
                "brightness": "",
                "colors": [],
                "content_type": "",
                "attributes": [],
                "composition": "",
                "dominant_tones": []
            }
            
            # Open the image
            with Image.open(image_path) as img:
                # Convert to RGB for consistent analysis
                if img.mode != "RGB":
                    img = img.convert("RGB")
                
                # Get image statistics
                stats = ImageStat.Stat(img)
                
                # Calculate brightness
                brightness = sum(stats.mean) / 3  # Average of R, G, B channels
                if brightness < 80:
                    analysis["brightness"] = "dark"
                elif brightness > 170:
                    analysis["brightness"] = "bright"
                else:
                    analysis["brightness"] = "balanced"
                
                # Get dominant colors
                r, g, b = stats.mean
                
                # Simplified color analysis
                if r > 180 and g > 180 and b > 180:
                    analysis["colors"].append("white")
                elif r < 60 and g < 60 and b < 60:
                    analysis["colors"].append("black")
                elif r > 150 and g < 100 and b < 100:
                    analysis["colors"].append("red")
                elif r < 100 and g > 150 and b < 100:
                    analysis["colors"].append("green")
                elif r < 100 and g < 100 and b > 150:
                    analysis["colors"].append("blue")
                elif r > 180 and g > 150 and b < 100:
                    analysis["colors"].append("yellow")
                elif r > 150 and g < 100 and b > 150:
                    analysis["colors"].append("purple")
                elif r > 150 and g > 100 and b < 100:
                    analysis["colors"].append("orange")
                elif r > 150 and g > 100 and b > 100:
                    analysis["colors"].append("warm")
                elif r < 100 and g > 100 and b > 100:
                    analysis["colors"].append("cool")
                else:
                    analysis["colors"].append("neutral")
                
                # Identify color temperature
                if r > (g + b) / 2:
                    analysis["dominant_tones"].append("warm tones")
                elif b > (r + g) / 2:
                    analysis["dominant_tones"].append("cool tones")
                else:
                    analysis["dominant_tones"].append("balanced tones")
                
                # Apply edge detection for texture analysis
                edges = img.filter(ImageFilter.FIND_EDGES)
                edge_stats = ImageStat.Stat(edges)
                edge_mean = sum(edge_stats.mean) / 3
                
                # Texture analysis
                if edge_mean > 40:
                    analysis["attributes"].append("detailed")
                    analysis["attributes"].append("textured")
                elif edge_mean > 20:
                    analysis["attributes"].append("moderate detail")
                else:
                    analysis["attributes"].append("smooth")
                    analysis["attributes"].append("minimal texture")
                
                # Variance for complexity
                variance = sum(stats.var) / 3
                if variance > 3000:
                    analysis["attributes"].append("high contrast")
                elif variance < 1000:
                    analysis["attributes"].append("low contrast")
                
                # Composition analysis
                width, height = img.size
                if width > height * 1.5:
                    analysis["composition"] = "wide panoramic shot"
                elif height > width * 1.5:
                    analysis["composition"] = "vertical portrait shot"
                elif abs(width - height) < 50:
                    analysis["composition"] = "square composition"
                else:
                    analysis["composition"] = "standard frame"
                
                # Get focus approximation based on edges
                if max(edge_stats.mean) > 35:
                    analysis["attributes"].append("sharp focus")
                else:
                    analysis["attributes"].append("soft focus")
                
                # Guess content type based on basic image properties
                # This is a very simplified approach - real implementation would use an object detection model
                if edge_mean < 15 and brightness > 200:
                    analysis["content_type"] = "minimalist"
                elif edge_mean > 40 and variance > 3000:
                    analysis["content_type"] = "detailed object"
                elif width > height * 1.5 and variance > 2000:
                    analysis["content_type"] = "landscape"
                elif height > width * 1.2 and edge_mean > 25:
                    analysis["content_type"] = "portrait"
                else:
                    analysis["content_type"] = "general image"
                
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing image: {e}")
            return {"error": str(e)}
            
    def _analyze_image_content_with_gemini(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze an image's content using Google's Gemini model.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dict: Analysis results with content information
        """
        try:
            if not GEMINI_API_KEY:
                self.logger.warning("No Gemini API key found. Skipping content analysis.")
                return {"content_description": "Image content (Gemini API key not provided)"}
            
            # Encode image for Gemini
            with open(image_path, "rb") as img_file:
                image_data = img_file.read()
                image_parts = [{"mime_type": "image/jpeg", "data": base64.b64encode(image_data).decode("utf-8")}]
            
            # Configure Gemini model - using updated model name
            model = genai.GenerativeModel(GEMINI_VISION_MODEL)
            
            # Prompt Gemini to analyze the image content, not the technical aspects
            prompt = """
            Analyze this image and identify:
            1. Main subject matter (what/who is in the image)
            2. Setting or environment
            3. Activities or actions shown
            4. Mood or feeling conveyed
            5. Any themes or concepts represented
            6. Any distinctive visual elements
            
            Focus ONLY on what's actually in the image, not how it was created or edited.
            Format your response as a JSON with these keys: main_subject, setting, activities, mood, themes, distinctive_elements
            """
            
            # Get response from Gemini
            response = model.generate_content([prompt] + image_parts)
            
            # Extract JSON from response
            try:
                # Try to parse as proper JSON if formatted correctly
                import json
                import re
                
                # Clean up response text to extract JSON
                response_text = response.text
                # Look for JSON pattern between code fences or standalone
                json_match = re.search(r'```json\s*(.*?)\s*```|^\s*(\{.*\})\s*$', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1) if json_match.group(1) else json_match.group(2)
                    content_analysis = json.loads(json_str)
                else:
                    # Fallback: create structured result from text
                    content_analysis = {
                        "content_description": response.text,
                        "main_subject": "",
                        "setting": "",
                        "activities": "",
                        "mood": "",
                        "themes": [],
                        "distinctive_elements": []
                    }
            except Exception as parse_err:
                self.logger.warning(f"Could not parse Gemini JSON response: {parse_err}")
                content_analysis = {
                    "content_description": response.text,
                    "main_subject": "",
                    "setting": "",
                    "activities": "",
                    "mood": "",
                    "themes": [],
                    "distinctive_elements": []
                }
            
            self.logger.info(f"Gemini analyzed the image content successfully")
            return content_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing image with Gemini: {e}")
            return {"content_description": f"Error analyzing image content: {str(e)}"}
    
    def _generate_caption_with_gemini(self, instructions: str, photo_editing: str, 
                               context_content: str = "", 
                               image_analysis: Dict[str, Any] = None,
                               content_analysis: Dict[str, Any] = None) -> str:
        """
        Generate a caption using Gemini based on instructions, context, and image content.
        
        Args:
            instructions: General instructions for the caption
            photo_editing: Photo editing instructions
            context_content: Content extracted from context files
            image_analysis: Technical analysis of the image
            content_analysis: Content analysis of the image from Gemini
            
        Returns:
            str: Generated caption
        """
        try:
            if not GEMINI_API_KEY:
                # Fall back to sample caption if no API key
                self.logger.warning("No Gemini API key found. Using sample caption generator.")
                return self._generate_sample_caption(
                    instructions, 
                    photo_editing,
                    context_content, 
                    image_analysis
                )
            
            # Initialize empty analyses if not provided
            if not image_analysis:
                image_analysis = {
                    "brightness": "balanced",
                    "colors": [],
                    "content_type": "general image",
                    "attributes": [],
                    "composition": "",
                    "dominant_tones": []
                }
                
            if not content_analysis:
                content_analysis = {
                    "content_description": "Image content not available",
                    "main_subject": "",
                    "setting": "",
                    "activities": "",
                    "mood": "",
                    "themes": [],
                    "distinctive_elements": []
                }
            
            # Configure Gemini model - using updated model name
            model = genai.GenerativeModel(GEMINI_TEXT_MODEL)
            
            # Format the prompt with all available information
            prompt = f"""
            Generate a social media caption for an image based on the following information:
            
            IMAGE CONTENT:
            {content_analysis.get('content_description', 'Not available')}
            
            Main subject: {content_analysis.get('main_subject', 'Not specified')}
            Setting: {content_analysis.get('setting', 'Not specified')}
            Activities: {content_analysis.get('activities', 'Not specified')}
            Mood: {content_analysis.get('mood', 'Not specified')}
            Themes: {', '.join(content_analysis.get('themes', ['Not specified']))}
            Distinctive elements: {', '.join(content_analysis.get('distinctive_elements', ['Not specified']))}
            
            GENERAL INSTRUCTIONS:
            {instructions}
            
            PHOTO EDITING NOTES:
            {photo_editing}
            
            CONTEXT FROM FILES:
            {context_content}
            
            TECHNICAL IMAGE DETAILS:
            - Brightness: {image_analysis.get('brightness', 'Not specified')}
            - Colors: {', '.join(image_analysis.get('colors', ['Not specified']))}
            - Composition: {image_analysis.get('composition', 'Not specified')}
            - Attributes: {', '.join(image_analysis.get('attributes', ['Not specified']))}
            
            Create an engaging caption that:
            1. Connects the IMAGE CONTENT (not its technical aspects) to the CONTEXT from files
            2. Aligns with the GENERAL INSTRUCTIONS
            3. Includes 3-5 relevant hashtags
            4. Is conversational, engaging, and social media-ready
            5. Is between 1-3 sentences plus hashtags
            
            Do not describe the technical aspects of the image or how it was edited.
            Focus on the content, theme, and subject of the image itself.
            """
            
            # Get response from Gemini
            response = model.generate_content(prompt)
            caption = response.text.strip()
            
            self.logger.info(f"Generated caption with Gemini: {caption[:50]}...")
            return caption
            
        except Exception as e:
            self.logger.error(f"Error generating caption with Gemini: {e}")
            # Fall back to sample caption in case of error
            return self._generate_sample_caption(
                instructions, 
                photo_editing,
                context_content, 
                image_analysis
            )
    
    def _generate_sample_caption(self, instructions: str, photo_editing: str, 
                               context_content: str = "", 
                               image_analysis: Dict[str, Any] = None) -> str:
        """
        Generate a sample caption for demonstration purposes.
        This is used as a fallback when Gemini API is not available.
        
        Args:
            instructions: General instructions for the caption
            photo_editing: Photo editing instructions
            context_content: Content extracted from context files
            image_analysis: Analysis of the image content
            
        Returns:
            str: Sample caption
        """
        # Very basic template-based caption generator
        # This is a fallback when Gemini integration is not available
        
        # Initialize default image_analysis if not provided
        if not image_analysis:
            image_analysis = {
                "brightness": "balanced",
                "colors": [],
                "content_type": "general image",
                "attributes": [],
                "composition": "",
                "dominant_tones": []
            }
        
        # Analyze context content for useful information
        business_keywords = []
        tone_keywords = []
        
        if context_content:
            # Try to identify business type from context
            business_types = [
                "bakery", "restaurant", "cafe", "boutique", "salon", "fitness", 
                "yoga", "retail", "photography", "art", "craft", "jewelry", 
                "clothing", "travel", "hotel", "pet", "realty", "tech"
            ]
            
            tone_types = [
                "professional", "casual", "luxury", "budget-friendly", "artisan", 
                "handcrafted", "traditional", "modern", "vintage", "sustainable", 
                "organic", "vegan", "local", "family-owned", "premium", "customized"
            ]
            
            lower_context = context_content.lower()
            
            for business in business_types:
                if business in lower_context:
                    business_keywords.append(business)
            
            for tone in tone_types:
                if tone in lower_context:
                    tone_keywords.append(tone)
                    
            self.logger.info(f"Found business type: {business_keywords} and tone: {tone_keywords}")
        
        # Default business type if none found
        business_type = business_keywords[0] if business_keywords else ""
        
        # Generate caption based on image analysis and context
        color_desc = image_analysis.get("colors", [""])[0] if image_analysis.get("colors") else ""
        composition = image_analysis.get("composition", "")
        content_type = image_analysis.get("content_type", "")
        attributes = image_analysis.get("attributes", [])
        
        # Choose caption intro based on content type
        caption_intros = [
            f"Captured this {color_desc} {content_type}",
            f"Sharing today's {content_type}",
            f"Check out this {composition}"
        ]
        
        if business_type:
            specific_intros = [
                f"From our {business_type}: a {color_desc} {content_type}",
                f"Today at {business_type.capitalize()}: {content_type}",
                f"Showcasing our {business_type}'s finest"
            ]
            caption_intros.extend(specific_intros)
        
        # Start with a greeting based on image content
        caption = random.choice(caption_intros)
        
        # Add attributes from image analysis
        if attributes:
            selected_attrs = [attr for attr in attributes if attr not in ["detailed", "textured", "smooth"]][:2]
            if selected_attrs:
                caption += " with " + ", ".join(selected_attrs)
        
        # Add tone if available
        if tone_keywords:
            caption += f". Our {tone_keywords[0]} approach shines through"
        
        # Add information about business if available
        if business_keywords and len(business_keywords) > 1:
            caption += f". Perfect for {business_keywords[1]} enthusiasts"
        
        # Add seasonal or promotional reference if in instructions
        for keyword in ["summer", "spring", "fall", "winter", "holiday", "special", "new", "sale"]:
            if keyword.lower() in instructions.lower():
                caption += f". Ideal for your {keyword.title()} needs!"
                break
        else:
            caption += "." # Add period if no seasonal reference
        
        # Add hashtags
        hashtags = []
        
        # Add content type hashtag
        if content_type:
            clean_content = content_type.replace(" ", "").replace("-", "")
            hashtags.append(f"#{clean_content.title()}")
        
        # Add color hashtag
        if color_desc:
            hashtags.append(f"#{color_desc.title()}")
        
        # Add business hashtags
        if business_keywords:
            for keyword in business_keywords[:2]:
                clean_keyword = keyword.replace(" ", "").replace("-", "")
                hashtags.append(f"#{clean_keyword.title()}")
        
        # Add tone hashtags
        if tone_keywords:
            for tone in tone_keywords[:1]:
                clean_tone = tone.replace(" ", "").replace("-", "")
                hashtags.append(f"#{clean_tone.title()}")
        
        # Add attribute hashtags
        if attributes:
            for attr in attributes[:2]:
                clean_attr = attr.replace(" ", "").replace("-", "")
                hashtags.append(f"#{clean_attr.title()}")
        
        # Default hashtags if none generated
        if not hashtags:
            hashtags = ["#PicOfTheDay", "#Photography", "#ShareYourStory"]
        
        # Add instruction-based hashtags
        for term in ["summer", "spring", "fall", "winter", "holiday", "special", "new", "sale"]:
            if term.lower() in instructions.lower():
                hashtags.append(f"#{term.title()}")
                break
        
        # Limit hashtags to a reasonable number
        hashtags = list(set(hashtags))[:6]  # Remove duplicates and limit to 6 hashtags
        
        # Finalize caption with hashtags
        caption += "\n\n" + " ".join(hashtags)
        
        return caption 