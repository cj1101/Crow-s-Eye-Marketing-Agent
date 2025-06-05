"""
Veo Video Generation Handler with Shared API Key Support
"""
import os
import logging
from typing import Optional

try:
    from google import genai
    from google.genai import types
    VEO_AVAILABLE = True
except ImportError:
    VEO_AVAILABLE = False

from ...config.shared_api_keys import get_google_api_key, is_using_shared_key

logger = logging.getLogger(__name__)

class VeoHandler:
    """Handler for Veo video generation with shared API key support."""
    
    def __init__(self, app_state=None):
        """Initialize the Veo handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.app_state = app_state
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Veo client with shared or user API key."""
        if not VEO_AVAILABLE:
            self.logger.warning("Veo not available - google-genai package not installed")
            return
        
        try:
            api_key = get_google_api_key()
            if not api_key:
                self.logger.warning("No Google API key available for Veo")
                return
            
            # Configure the client
            self.client = genai.Client(api_key=api_key)
            
            if is_using_shared_key("google"):
                self.logger.info("Veo client initialized with shared API key")
            else:
                self.logger.info("Veo client initialized with user's API key")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Veo client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Veo is available and properly configured."""
        return VEO_AVAILABLE and self.client is not None
    
    def generate_video(self, prompt: str, duration: int = 5) -> Optional[str]:
        """
        Generate a video using Veo.
        
        Args:
            prompt: Text description for the video
            duration: Duration in seconds (default: 5)
            
        Returns:
            str: Path to generated video file, or None if failed
        """
        if not self.is_available():
            self.logger.error("Veo is not available")
            return None
        
        try:
            self.logger.info(f"Generating video with prompt: {prompt[:50]}...")
            
            # Generate video using Veo with the latest API
            operation = self.client.models.generate_videos(
                model='veo-2.0-generate-001',
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    number_of_videos=1,
                    fps=24,
                    duration_seconds=duration,
                    enhance_prompt=True,
                ),
            )
            
            # Poll operation until completion
            import time
            while not operation.done:
                time.sleep(20)
                operation = self.client.operations.get(operation)
            
            if operation.result and operation.result.generated_videos:
                video = operation.result.generated_videos[0].video
                # Save video to temporary file
                video_path = self._save_video_data(video)
                self.logger.info(f"Video generated successfully: {video_path}")
                return video_path
            else:
                self.logger.warning("No video generated in response")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating video: {e}")
            return None
    
    def _save_video_data(self, video) -> Optional[str]:
        """Save video data to local file."""
        try:
            import tempfile
            import os
            
            # Create temporary file for video
            temp_dir = tempfile.gettempdir()
            video_filename = f"veo_video_{os.getpid()}.mp4"
            video_path = os.path.join(temp_dir, video_filename)
            
            # Save video data to file
            # The video object should have methods to save or export
            if hasattr(video, 'save'):
                video.save(video_path)
            elif hasattr(video, 'video_bytes'):
                with open(video_path, 'wb') as f:
                    f.write(video.video_bytes)
            else:
                self.logger.error("Unknown video format from Veo API")
                return None
            
            return video_path
            
        except Exception as e:
            self.logger.error(f"Error saving video: {e}")
            return None 