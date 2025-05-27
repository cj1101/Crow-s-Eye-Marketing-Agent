"""
Advanced Veo 3 Video Generation Handler for Crow's Eye platform.
Provides high-quality video generation with advanced settings and options.
"""
import logging
import os
import time
import base64
from typing import Dict, Any, Optional, List, Tuple
import google.generativeai as genai
from google import genai as google_genai
from google.genai import types
from dotenv import load_dotenv
from datetime import datetime

from ...config import constants as const
from ...models.app_state import AppState

# Load API key from environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class VeoHandler:
    """
    Advanced Veo 3 handler with high-quality settings and comprehensive options.
    """
    
    def __init__(self, app_state: AppState):
        """
        Initialize the Veo handler.
        
        Args:
            app_state: Application state object
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.app_state = app_state
        
        # Initialize Google Gen AI client
        try:
            self.client = google_genai.Client()
            self.logger.info("✅ Veo client initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Veo client: {e}")
            self.client = None
    
    def is_ready(self) -> bool:
        """Check if the handler is ready to generate videos."""
        api_key = os.getenv("GOOGLE_API_KEY")
        return self.client is not None and api_key is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information."""
        return {
            "ready": self.is_ready(),
            "has_api_key": os.getenv("GOOGLE_API_KEY") is not None,
            "client_initialized": self.client is not None,
            "model": "veo-2.0-generate-001",
            "max_duration": 60,
            "supported_aspect_ratios": ["16:9", "9:16", "1:1"],
            "supported_durations": [5, 10, 15, 30, 60]
        }
    
    def generate_video(
        self,
        prompt: str,
        duration: int = 10,
        aspect_ratio: str = "16:9",
        allow_person_generation: bool = False,
        output_dir: str = "output",
        filename_prefix: str = "veo_video"
    ) -> Tuple[bool, str, str]:
        """
        Generate a high-quality video with advanced settings.
        
        Args:
            prompt: Text description of the video
            duration: Video duration in seconds (5, 10, 15, 30, or 60)
            aspect_ratio: Video aspect ratio ("16:9", "9:16", or "1:1")
            allow_person_generation: Whether to allow person generation
            output_dir: Directory to save the video
            filename_prefix: Prefix for the output filename
            
        Returns:
            Tuple[bool, str, str]: (success, video_path_or_error, message)
        """
        if not self.is_ready():
            return False, "", "Veo handler not ready - check API key and setup"
        
        # Validate inputs
        if duration not in [5, 10, 15, 30, 60]:
            return False, "", f"Invalid duration: {duration}. Must be 5, 10, 15, 30, or 60 seconds"
        
        if aspect_ratio not in ["16:9", "9:16", "1:1"]:
            return False, "", f"Invalid aspect ratio: {aspect_ratio}. Must be 16:9, 9:16, or 1:1"
        
        try:
            self.logger.info(f"🎬 Generating {duration}s video ({aspect_ratio}): {prompt[:50]}...")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Use high-quality settings
            operation = self.client.models.generate_videos(
                model="veo-2.0-generate-001",
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio=aspect_ratio,
                    person_generation="allow" if allow_person_generation else "dont_allow",
                    number_of_videos=1,
                    duration_seconds=duration
                )
            )
            
            # Wait for completion with progress updates
            self.logger.info("⏳ Waiting for video generation...")
            start_time = time.time()
            
            while not operation.done:
                elapsed = time.time() - start_time
                if elapsed > 900:  # 15 minute timeout for longer videos
                    return False, "", "Video generation timed out (15 minutes)"
                
                # Log progress every 30 seconds
                if int(elapsed) % 30 == 0 and elapsed > 0:
                    self.logger.info(f"⏳ Still generating... ({int(elapsed)}s elapsed)")
                
                time.sleep(20)
                operation = self.client.operations.get(operation)
            
            # Handle result
            if operation.response and operation.response.generated_videos:
                video = operation.response.generated_videos[0]
                
                # Generate descriptive filename
                timestamp = int(time.time())
                safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_prompt = safe_prompt.replace(' ', '_')
                output_filename = f"{filename_prefix}_{safe_prompt}_{duration}s_{aspect_ratio.replace(':', 'x')}_{timestamp}.mp4"
                output_path = os.path.join(output_dir, output_filename)
                
                # Download and save
                self.client.files.download(file=video.video)
                video.video.save(output_path)
                
                self.logger.info(f"✅ Video saved: {output_path}")
                return True, output_path, f"High-quality {duration}s video generated successfully"
            else:
                return False, "", "No video was generated"
                
        except Exception as e:
            self.logger.error(f"❌ Error generating video: {e}")
            return False, "", f"Error: {str(e)}"
    
    def generate_video_with_progress_callback(
        self,
        prompt: str,
        duration: int = 10,
        aspect_ratio: str = "16:9",
        allow_person_generation: bool = False,
        output_dir: str = "output",
        filename_prefix: str = "veo_video",
        progress_callback=None
    ) -> Tuple[bool, str, str]:
        """
        Generate video with progress callback for UI updates.
        
        Args:
            prompt: Text description of the video
            duration: Video duration in seconds
            aspect_ratio: Video aspect ratio
            allow_person_generation: Whether to allow person generation
            output_dir: Directory to save the video
            filename_prefix: Prefix for the output filename
            progress_callback: Function to call with progress updates
            
        Returns:
            Tuple[bool, str, str]: (success, video_path_or_error, message)
        """
        if not self.is_ready():
            return False, "", "Veo handler not ready - check API key and setup"
        
        try:
            self.logger.info(f"🎬 Generating {duration}s video ({aspect_ratio}): {prompt[:50]}...")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Use high-quality settings
            operation = self.client.models.generate_videos(
                model="veo-2.0-generate-001",
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio=aspect_ratio,
                    person_generation="allow" if allow_person_generation else "dont_allow",
                    number_of_videos=1,
                    duration_seconds=duration
                )
            )
            
            if progress_callback:
                progress_callback("⏳ Video generation in progress...")
            
            # Wait for completion with progress updates
            start_time = time.time()
            last_update = 0
            
            while not operation.done:
                elapsed = time.time() - start_time
                if elapsed > 900:  # 15 minute timeout
                    return False, "", "Video generation timed out (15 minutes)"
                
                # Update progress every 30 seconds
                if elapsed - last_update >= 30:
                    if progress_callback:
                        progress_callback(f"⏳ Generating... ({int(elapsed)}s elapsed)")
                    last_update = elapsed
                
                time.sleep(20)
                operation = self.client.operations.get(operation)
            
            if progress_callback:
                progress_callback("💾 Downloading and saving video...")
            
            # Handle result
            if operation.response and operation.response.generated_videos:
                video = operation.response.generated_videos[0]
                
                # Generate descriptive filename
                timestamp = int(time.time())
                safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_prompt = safe_prompt.replace(' ', '_')
                output_filename = f"{filename_prefix}_{safe_prompt}_{duration}s_{aspect_ratio.replace(':', 'x')}_{timestamp}.mp4"
                output_path = os.path.join(output_dir, output_filename)
                
                # Download and save
                self.client.files.download(file=video.video)
                video.video.save(output_path)
                
                if progress_callback:
                    progress_callback("✅ Video generation complete!")
                
                self.logger.info(f"✅ Video saved: {output_path}")
                return True, output_path, f"High-quality {duration}s video generated successfully"
            else:
                return False, "", "No video was generated"
                
        except Exception as e:
            self.logger.error(f"❌ Error generating video: {e}")
            return False, "", f"Error: {str(e)}"
    
    def get_quality_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get predefined quality presets for different use cases."""
        return {
            "social_media_story": {
                "aspect_ratio": "9:16",
                "duration": 15,
                "description": "Perfect for Instagram/Facebook Stories"
            },
            "social_media_post": {
                "aspect_ratio": "1:1",
                "duration": 10,
                "description": "Square format for social media posts"
            },
            "youtube_short": {
                "aspect_ratio": "9:16",
                "duration": 30,
                "description": "Vertical format for YouTube Shorts"
            },
            "landscape_video": {
                "aspect_ratio": "16:9",
                "duration": 30,
                "description": "Traditional landscape format"
            },
            "quick_preview": {
                "aspect_ratio": "16:9",
                "duration": 5,
                "description": "Quick 5-second preview"
            },
            "long_form": {
                "aspect_ratio": "16:9",
                "duration": 60,
                "description": "Maximum length video"
            }
        }
    
    def get_prompt_suggestions(self) -> Dict[str, list]:
        """Get categorized prompt suggestions for inspiration."""
        return {
            "Nature & Landscapes": [
                "A serene mountain lake reflecting snow-capped peaks at sunrise",
                "Ocean waves gently lapping against a sandy beach",
                "A forest path with sunlight filtering through tall trees",
                "Cherry blossoms falling in a peaceful Japanese garden",
                "Northern lights dancing across a starry sky"
            ],
            "Urban & Architecture": [
                "A bustling city street with neon lights at night",
                "Modern skyscrapers reaching toward cloudy skies",
                "A cozy coffee shop with warm lighting and steam rising from cups",
                "Rain falling on empty city streets with reflective puddles",
                "A vintage train station with people walking by"
            ],
            "Food & Lifestyle": [
                "Steam rising from a freshly baked loaf of bread",
                "Coffee being poured into a white ceramic cup",
                "Fresh ingredients being chopped for a colorful salad",
                "A candle flickering in a dimly lit room",
                "Books stacked on a wooden table next to a window"
            ],
            "Abstract & Artistic": [
                "Colorful paint mixing and swirling together",
                "Geometric shapes morphing and transforming",
                "Light patterns dancing on a wall",
                "Smoke curling upward in elegant spirals",
                "Water droplets creating ripples in slow motion"
            ],
            "Animals & Wildlife": [
                "A cat stretching and yawning in morning sunlight",
                "Birds flying in formation across a sunset sky",
                "A dog running through a field of tall grass",
                "Fish swimming gracefully in clear blue water",
                "A butterfly landing on a colorful flower"
            ]
        }
    
    def generate_marketing_video(self, prompt: str, 
                               image_path: Optional[str] = None,
                               aspect_ratio: str = "16:9",
                               duration: int = 8,
                               include_audio: bool = True,
                               negative_prompt: str = "",
                               style_preset: str = "cinematic") -> Tuple[bool, str, str]:
        """
        Generate a marketing video using Veo 3.
        
        Args:
            prompt: Text description of the video to generate
            image_path: Optional image to use as starting frame
            aspect_ratio: "16:9" for landscape or "9:16" for portrait
            duration: Video duration in seconds (5-8)
            include_audio: Whether to generate audio/speech
            negative_prompt: What to avoid in the video
            style_preset: Style preset for the video
            
        Returns:
            Tuple[bool, str, str]: (success, video_path, message)
        """
        try:
            if not self.client:
                return False, "", "Veo handler not properly initialized"
            
            self.logger.info(f"Generating video with prompt: {prompt[:100]}...")
            
            # Enhance prompt with style and marketing context
            enhanced_prompt = self._enhance_marketing_prompt(prompt, style_preset)
            
            # Prepare generation config
            config = types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                person_generation="allow_adult",  # Allow adults for marketing content
                number_of_videos=1,
                duration_seconds=duration
            )
            
            # Generate video
            if image_path and os.path.exists(image_path):
                # Image-to-video generation
                self.logger.info(f"Using base image: {image_path}")
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                
                operation = self.client.models.generate_videos(
                    model="veo-2.0-generate-001",  # Using stable version for now
                    prompt=enhanced_prompt,
                    image=types.Image(
                        image_bytes=image_data,
                        mime_type=self._get_mime_type(image_path)
                    ),
                    config=config
                )
            else:
                # Text-to-video generation
                operation = self.client.models.generate_videos(
                    model="veo-2.0-generate-001",
                    prompt=enhanced_prompt,
                    config=config
                )
            
            # Wait for completion with progress updates
            start_time = time.time()
            while not operation.done:
                elapsed = time.time() - start_time
                self.logger.info(f"Video generation in progress... ({elapsed:.0f}s elapsed)")
                time.sleep(20)
                operation = self.client.operations.get(operation)
                
                # Timeout after 10 minutes
                if elapsed > 600:
                    return False, "", "Video generation timed out"
            
            # Download and save video
            if operation.response and operation.response.generated_videos:
                video = operation.response.generated_videos[0]
                
                # Generate output filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_prompt = safe_prompt.replace(' ', '_')
                output_filename = f"veo_video_{safe_prompt}_{timestamp}.mp4"
                output_path = os.path.join(const.OUTPUT_DIR, output_filename)
                
                # Ensure output directory exists
                os.makedirs(const.OUTPUT_DIR, exist_ok=True)
                
                # Download and save
                self.client.files.download(file=video.video)
                video.video.save(output_path)
                
                # Update app state
                if hasattr(self.app_state, 'selected_media'):
                    self.app_state.selected_media = output_path
                
                self.logger.info(f"Video generated successfully: {output_path}")
                return True, output_path, "Video generated successfully"
            else:
                return False, "", "No video was generated"
                
        except Exception as e:
            self.logger.error(f"Error generating video: {e}")
            return False, "", f"Error generating video: {str(e)}"
    
    def create_iterative_video(self, initial_prompt: str, 
                             feedback_prompts: List[str],
                             base_image: Optional[str] = None,
                             aspect_ratio: str = "16:9") -> Tuple[bool, List[str], str]:
        """
        Create multiple video iterations based on user feedback.
        
        Args:
            initial_prompt: Initial video description
            feedback_prompts: List of refinement prompts
            base_image: Optional base image to use
            aspect_ratio: Video aspect ratio
            
        Returns:
            Tuple[bool, List[str], str]: (success, list_of_video_paths, message)
        """
        video_paths = []
        
        try:
            self.logger.info(f"Starting iterative video creation with {len(feedback_prompts)} variations")
            
            # Generate initial video
            success, video_path, message = self.generate_marketing_video(
                initial_prompt, base_image, aspect_ratio
            )
            
            if success:
                video_paths.append(video_path)
                
                # Generate variations based on feedback
                for i, feedback in enumerate(feedback_prompts):
                    self.logger.info(f"Generating variation {i+1}: {feedback}")
                    refined_prompt = f"{initial_prompt}. {feedback}"
                    success, refined_video, _ = self.generate_marketing_video(
                        refined_prompt, base_image, aspect_ratio
                    )
                    if success:
                        video_paths.append(refined_video)
                    else:
                        self.logger.warning(f"Failed to generate variation {i+1}")
                
                return True, video_paths, f"Generated {len(video_paths)} video variations"
            else:
                return False, [], message
                
        except Exception as e:
            self.logger.error(f"Error in iterative video creation: {e}")
            return False, video_paths, f"Error: {str(e)}"
    
    def generate_social_media_variants(self, prompt: str, 
                                     platforms: List[str] = None,
                                     base_image: Optional[str] = None) -> Tuple[bool, Dict[str, str], str]:
        """
        Generate platform-specific video variants.
        
        Args:
            prompt: Video description
            platforms: List of platforms (instagram, tiktok, youtube, linkedin)
            base_image: Optional base image
            
        Returns:
            Tuple[bool, Dict[str, str], str]: (success, platform_video_paths, message)
        """
        if platforms is None:
            platforms = ["instagram", "tiktok", "youtube", "linkedin"]
        
        platform_configs = {
            "instagram": {"aspect_ratio": "9:16", "style": "vibrant and engaging"},
            "tiktok": {"aspect_ratio": "9:16", "style": "dynamic and trendy"},
            "youtube": {"aspect_ratio": "16:9", "style": "professional and polished"},
            "linkedin": {"aspect_ratio": "16:9", "style": "corporate and professional"}
        }
        
        video_paths = {}
        
        try:
            for platform in platforms:
                if platform not in platform_configs:
                    continue
                
                config = platform_configs[platform]
                platform_prompt = f"{prompt}, {config['style']} style, optimized for {platform}"
                
                self.logger.info(f"Generating video for {platform}")
                success, video_path, _ = self.generate_marketing_video(
                    platform_prompt,
                    base_image,
                    config["aspect_ratio"],
                    style_preset=config["style"]
                )
                
                if success:
                    video_paths[platform] = video_path
                else:
                    self.logger.warning(f"Failed to generate video for {platform}")
            
            if video_paths:
                return True, video_paths, f"Generated videos for {len(video_paths)} platforms"
            else:
                return False, {}, "Failed to generate any platform variants"
                
        except Exception as e:
            self.logger.error(f"Error generating social media variants: {e}")
            return False, video_paths, f"Error: {str(e)}"
    
    def _enhance_marketing_prompt(self, prompt: str, style_preset: str) -> str:
        """
        Enhance the prompt with marketing-specific details.
        
        Args:
            prompt: Original prompt
            style_preset: Style preset to apply
            
        Returns:
            Enhanced prompt
        """
        style_enhancements = {
            "cinematic": "cinematic lighting, professional camera work, smooth motion",
            "commercial": "commercial advertising style, bright lighting, product focus",
            "social": "social media optimized, engaging, eye-catching",
            "corporate": "professional, clean, business-appropriate",
            "creative": "artistic, unique perspective, creative composition"
        }
        
        enhancement = style_enhancements.get(style_preset, style_enhancements["cinematic"])
        
        # Add marketing-specific elements
        enhanced = f"{prompt}, {enhancement}, high quality, marketing video style"
        
        return enhanced
    
    def _get_mime_type(self, file_path: str) -> str:
        """
        Get MIME type from file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type string
        """
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp'
        }
        return mime_types.get(ext, 'image/jpeg')
    
    def get_generation_status(self) -> Dict[str, Any]:
        """
        Get current generation status and statistics.
        
        Returns:
            Status information
        """
        return {
            "handler_initialized": self.client is not None,
            "api_key_configured": GOOGLE_API_KEY is not None,
            "supported_models": ["veo-2.0-generate-001", "veo-3.0-generate-preview"],
            "supported_formats": ["16:9", "9:16"],
            "max_duration": 8,
            "min_duration": 5
        } 