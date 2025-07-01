"""
AI Generation Service
Handles image generation with Imagen 3 and video generation with Veo 2
"""

import os
import logging
import asyncio
import time
import uuid
import io
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

try:
    from google import genai
    from google.genai import types
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from ..core.config import settings

logger = logging.getLogger(__name__)

class AIGenerationService:
    """Service for AI-powered image and video generation using Google's APIs."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = None
        self._initialize_client()
        
        # Storage directory for generated content
        self.storage_dir = "/tmp/ai_generated" if os.path.exists("/tmp") else "data/ai_generated"
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def _initialize_client(self):
        """Initialize the Google AI client."""
        if not AI_AVAILABLE:
            self.logger.warning("Google AI not available - google-genai package not installed")
            return
        
        try:
            # Try multiple sources for API key
            api_key = (
                settings.GOOGLE_API_KEY or 
                settings.GEMINI_API_KEY or 
                os.getenv("GOOGLE_API_KEY") or 
                os.getenv("GEMINI_API_KEY")
            )
            
            if not api_key:
                self.logger.warning("No Google API key available for AI generation")
                return
            
            # Configure the client
            self.client = genai.Client(api_key=api_key)
            self.logger.info("AI generation client initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize AI client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if AI generation is available."""
        return AI_AVAILABLE and self.client is not None
    
    async def generate_images(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate images using Imagen 3.
        
        Args:
            request_data: Dictionary containing generation parameters
            
        Returns:
            Dictionary with generation results
        """
        prompt = request_data.get("prompt", "")
        style = request_data.get("style", "photorealistic")
        aspect_ratio = request_data.get("aspect_ratio", "1:1")
        quality = request_data.get("quality", "standard")
        count = min(request_data.get("count", 1), 4)  # Limit to 4 images
        
        self.logger.info(f"Generating {count} images with prompt: {prompt[:100]}...")
        
        start_time = time.time()
        
        # Enhanced prompt based on style
        enhanced_prompt = self._enhance_prompt(prompt, style, quality)
        
        if not self.is_available():
            self.logger.warning("AI service not available, using demo mode")
            return await self._generate_demo_images(request_data, enhanced_prompt, start_time)
        
        try:
            # Convert aspect ratio for Imagen
            imagen_aspect_ratio = self._convert_aspect_ratio(aspect_ratio)
            
            # Generate images using Imagen 3
            response = await asyncio.to_thread(
                self.client.models.generate_images,
                model='imagen-3.0-generate-001',
                prompt=enhanced_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=count,
                    aspect_ratio=imagen_aspect_ratio,
                    safety_filter_level="BLOCK_SOME",
                    person_generation="ALLOW_ADULT"
                )
            )
            
            generation_time = time.time() - start_time
            
            # Process generated images
            generated_images = []
            if response.generated_images:
                for i, generated_image in enumerate(response.generated_images):
                    image_id = f"img_{uuid.uuid4().hex[:8]}"
                    image_url = await self._save_generated_image(generated_image, image_id)
                    
                    # Get image dimensions
                    width, height = self._get_image_dimensions(generated_image)
                    
                    image_data = {
                        "image_url": image_url,
                        "image_id": image_id,
                        "width": width,
                        "height": height,
                        "format": "jpg"
                    }
                    generated_images.append(image_data)
            
            # Calculate cost (placeholder pricing)
            total_cost = 0.04 * count  # $0.04 per image
            
            return {
                "images": generated_images,
                "generation_time": generation_time,
                "total_cost": total_cost,
                "prompt_used": enhanced_prompt,
                "style_applied": style,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Error generating images: {e}")
            # Fall back to demo mode on API errors
            return await self._generate_demo_images(request_data, enhanced_prompt, start_time)
    
    async def generate_video(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate video using Veo 2.
        
        Args:
            request_data: Dictionary containing generation parameters
            
        Returns:
            Dictionary with generation results
        """
        prompt = request_data.get("prompt", "")
        duration = min(request_data.get("duration", 5), 30)  # Limit to 30 seconds
        style = request_data.get("style", "cinematic")
        aspect_ratio = request_data.get("aspect_ratio", "16:9")
        fps = request_data.get("fps", 24)
        
        self.logger.info(f"Generating video with prompt: {prompt[:100]}...")
        
        start_time = time.time()
        
        # Enhanced prompt for video
        enhanced_prompt = self._enhance_video_prompt(prompt, style)
        
        if not self.is_available():
            self.logger.warning("AI service not available, using demo mode")
            return await self._generate_demo_video(request_data, enhanced_prompt, start_time)
        
        try:
            # Generate video using Veo 2
            operation = await asyncio.to_thread(
                self.client.models.generate_videos,
                model='veo-2.0-generate-001',
                prompt=enhanced_prompt,
                config=types.GenerateVideosConfig(
                    number_of_videos=1,
                    duration_seconds=duration,
                    enhance_prompt=True,
                    aspect_ratio=self._convert_video_aspect_ratio(aspect_ratio)
                )
            )
            
            # Poll operation until completion
            video_url = None
            video_id = f"vid_{uuid.uuid4().hex[:8]}"
            
            # Wait for video generation (with timeout)
            timeout = 300  # 5 minutes timeout
            poll_interval = 20  # Check every 20 seconds
            elapsed = 0
            
            while not operation.done and elapsed < timeout:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                operation = await asyncio.to_thread(self.client.operations.get, operation)
            
            generation_time = time.time() - start_time
            
            if operation.done and operation.result and operation.result.generated_videos:
                video = operation.result.generated_videos[0].video
                video_url = await self._save_generated_video(video, video_id)
            else:
                if elapsed >= timeout:
                    raise Exception("Video generation timed out")
                else:
                    raise Exception("Video generation failed")
            
            # Calculate cost (placeholder pricing)
            total_cost = 0.25 * duration  # $0.25 per second
            
            return {
                "video_url": video_url,
                "video_id": video_id,
                "duration": float(duration),
                "generation_time": generation_time,
                "total_cost": total_cost,
                "metadata": {
                    "style": style,
                    "aspect_ratio": aspect_ratio,
                    "fps": fps,
                    "prompt": enhanced_prompt
                },
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Error generating video: {e}")
            # Fall back to demo mode on API errors
            return await self._generate_demo_video(request_data, enhanced_prompt, start_time)
    
    def _enhance_prompt(self, prompt: str, style: str, quality: str) -> str:
        """Enhance the prompt for better image generation."""
        style_modifiers = {
            "photorealistic": "photorealistic, highly detailed, professional photography",
            "artistic": "artistic, creative, masterpiece, high quality art",
            "cartoon": "cartoon style, animated, colorful, clean lines",
            "abstract": "abstract art, modern, artistic interpretation",
            "vintage": "vintage style, retro, classic aesthetic",
            "cinematic": "cinematic lighting, dramatic, high production value"
        }
        
        quality_modifiers = {
            "standard": "high quality",
            "hd": "ultra high definition, 8K resolution, extremely detailed"
        }
        
        enhanced = prompt
        if style in style_modifiers:
            enhanced += f", {style_modifiers[style]}"
        if quality in quality_modifiers:
            enhanced += f", {quality_modifiers[quality]}"
        
        return enhanced
    
    def _enhance_video_prompt(self, prompt: str, style: str) -> str:
        """Enhance the prompt for better video generation."""
        style_modifiers = {
            "cinematic": "cinematic, professional cinematography, smooth camera movement",
            "documentary": "documentary style, realistic, natural lighting",
            "artistic": "artistic, creative camera work, stylized",
            "commercial": "commercial video style, polished, marketing quality",
            "social": "social media optimized, engaging, dynamic"
        }
        
        enhanced = prompt
        if style in style_modifiers:
            enhanced += f", {style_modifiers[style]}"
        
        enhanced += ", high quality video, smooth motion, professional production"
        return enhanced
    
    def _convert_aspect_ratio(self, aspect_ratio: str) -> str:
        """Convert aspect ratio to Imagen format."""
        ratio_map = {
            "1:1": "1:1",
            "4:3": "4:3", 
            "3:4": "3:4",
            "16:9": "16:9",
            "9:16": "9:16",
            "4:5": "4:5",
            "5:4": "5:4"
        }
        return ratio_map.get(aspect_ratio, "1:1")
    
    def _convert_video_aspect_ratio(self, aspect_ratio: str) -> str:
        """Convert aspect ratio to Veo format."""
        ratio_map = {
            "16:9": "16:9",
            "9:16": "9:16", 
            "1:1": "1:1",
            "4:3": "4:3",
            "3:4": "3:4"
        }
        return ratio_map.get(aspect_ratio, "16:9")
    
    async def _save_generated_image(self, generated_image, image_id: str) -> str:
        """Save generated image to storage and return URL."""
        try:
            # Save image data to file
            image_filename = f"{image_id}.jpg"
            image_path = os.path.join(self.storage_dir, image_filename)
            
            # Convert to PIL Image and save
            if PIL_AVAILABLE:
                image_data = generated_image.image.image_bytes
                pil_image = Image.open(io.BytesIO(image_data))
                pil_image.save(image_path, "JPEG", quality=95)
            else:
                # Fallback: save raw bytes
                with open(image_path, 'wb') as f:
                    f.write(generated_image.image.image_bytes)
            
            # Return relative URL (in production, this would be a cloud storage URL)
            return f"/generated/images/{image_filename}"
            
        except Exception as e:
            self.logger.error(f"Error saving generated image: {e}")
            return f"/generated/images/placeholder_{image_id}.jpg"
    
    async def _save_generated_video(self, generated_video, video_id: str) -> str:
        """Save generated video to storage and return URL."""
        try:
            # Save video data to file
            video_filename = f"{video_id}.mp4"
            video_path = os.path.join(self.storage_dir, video_filename)
            
            # Save video bytes
            if hasattr(generated_video, 'video_bytes'):
                with open(video_path, 'wb') as f:
                    f.write(generated_video.video_bytes)
            elif hasattr(generated_video, 'save'):
                await asyncio.to_thread(generated_video.save, video_path)
            else:
                # Try to extract video data
                video_data = getattr(generated_video, 'data', None)
                if video_data:
                    with open(video_path, 'wb') as f:
                        f.write(video_data)
                else:
                    raise Exception("Unable to extract video data")
            
            # Return relative URL (in production, this would be a cloud storage URL)
            return f"/generated/videos/{video_filename}"
            
        except Exception as e:
            self.logger.error(f"Error saving generated video: {e}")
            return f"/generated/videos/placeholder_{video_id}.mp4"
    
    def _get_image_dimensions(self, generated_image) -> Tuple[int, int]:
        """Get dimensions of generated image."""
        try:
            if PIL_AVAILABLE:
                image_data = generated_image.image.image_bytes
                pil_image = Image.open(io.BytesIO(image_data))
                return pil_image.size
            else:
                # Default dimensions
                return (1024, 1024)
        except Exception:
            return (1024, 1024)
    
    async def _generate_demo_images(self, request_data: Dict[str, Any], enhanced_prompt: str, start_time: float) -> Dict[str, Any]:
        """Generate demo images when AI service is not available."""
        try:
            count = min(request_data.get("count", 1), 4)
            style = request_data.get("style", "photorealistic")
            
            # Simulate some processing time
            await asyncio.sleep(2)
            
            # Create demo image placeholders
            generated_images = []
            for i in range(count):
                image_id = f"demo_img_{uuid.uuid4().hex[:8]}"
                
                # Create a simple demo image if PIL is available
                if PIL_AVAILABLE:
                    demo_image_url = await self._create_demo_image(image_id, enhanced_prompt)
                else:
                    demo_image_url = f"/generated/images/demo_{image_id}.jpg"
                
                image_data = {
                    "image_url": demo_image_url,
                    "image_id": image_id,
                    "width": 1024,
                    "height": 1024,
                    "format": "jpg"
                }
                generated_images.append(image_data)
            
            generation_time = time.time() - start_time
            total_cost = 0.04 * count  # Demo pricing
            
            return {
                "images": generated_images,
                "generation_time": generation_time,
                "total_cost": total_cost,
                "prompt_used": enhanced_prompt,
                "style_applied": style,
                "success": True,
                "demo_mode": True
            }
            
        except Exception as e:
            self.logger.error(f"Error in demo image generation: {e}")
            return {
                "success": False,
                "error": f"Demo mode error: {str(e)}",
                "images": [],
                "generation_time": 0,
                "total_cost": 0,
                "prompt_used": enhanced_prompt,
                "style_applied": style
            }
    
    async def _generate_demo_video(self, request_data: Dict[str, Any], enhanced_prompt: str, start_time: float) -> Dict[str, Any]:
        """Generate demo video when AI service is not available."""
        try:
            duration = min(request_data.get("duration", 5), 30)
            style = request_data.get("style", "cinematic")
            aspect_ratio = request_data.get("aspect_ratio", "16:9")
            fps = request_data.get("fps", 24)
            
            # Simulate some processing time
            await asyncio.sleep(3)
            
            video_id = f"demo_vid_{uuid.uuid4().hex[:8]}"
            video_url = f"/generated/videos/demo_{video_id}.mp4"
            
            generation_time = time.time() - start_time
            total_cost = 0.25 * duration  # Demo pricing
            
            return {
                "video_url": video_url,
                "video_id": video_id,
                "duration": float(duration),
                "generation_time": generation_time,
                "total_cost": total_cost,
                "metadata": {
                    "style": style,
                    "aspect_ratio": aspect_ratio,
                    "fps": fps,
                    "prompt": enhanced_prompt
                },
                "success": True,
                "demo_mode": True
            }
            
        except Exception as e:
            self.logger.error(f"Error in demo video generation: {e}")
            return {
                "success": False,
                "error": f"Demo mode error: {str(e)}",
                "video_url": "",
                "video_id": f"demo_vid_{uuid.uuid4().hex[:8]}",
                "duration": 0.0,
                "generation_time": 0.0,
                "total_cost": 0.0,
                "metadata": {}
            }
    
    async def _create_demo_image(self, image_id: str, prompt: str) -> str:
        """Create a simple demo image placeholder."""
        try:
            if not PIL_AVAILABLE:
                return f"/generated/images/demo_{image_id}.jpg"
            
            # Create a simple colored image with text
            from PIL import Image, ImageDraw, ImageFont
            
            # Create image
            img = Image.new('RGB', (1024, 1024), color=(135, 206, 250))  # Sky blue
            draw = ImageDraw.Draw(img)
            
            # Try to load a font, fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            # Add text
            text_lines = [
                "🎨 Demo AI Image",
                "",
                f"Prompt: {prompt[:40]}...",
                "",
                "Generated by Crow's Eye",
                f"Image ID: {image_id}"
            ]
            
            y_offset = 300
            for line in text_lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (1024 - text_width) // 2
                draw.text((x, y_offset), line, fill=(50, 50, 50), font=font)
                y_offset += 60
            
            # Save image
            image_filename = f"demo_{image_id}.jpg"
            image_path = os.path.join(self.storage_dir, image_filename)
            img.save(image_path, "JPEG", quality=90)
            
            return f"/generated/images/{image_filename}"
            
        except Exception as e:
            self.logger.error(f"Error creating demo image: {e}")
            return f"/generated/images/demo_{image_id}.jpg"

# Global service instance
ai_generation_service = AIGenerationService() 