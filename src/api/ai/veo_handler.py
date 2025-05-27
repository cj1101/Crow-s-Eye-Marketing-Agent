"""
Veo Video Generation Handler with Shared API Key Support
"""
import os
import logging
from typing import Optional

try:
    from google import genai
    VEO_AVAILABLE = True
except ImportError:
    VEO_AVAILABLE = False

from ...config.shared_api_keys import get_google_api_key, is_using_shared_key

logger = logging.getLogger(__name__)

class VeoHandler:
    """Handler for Veo video generation with shared API key support."""
    
    def __init__(self):
        """Initialize the Veo handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
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
            os.environ["GOOGLE_API_KEY"] = api_key
            self.client = genai.Client()
            
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
            
            # Generate video using Veo
            response = self.client.models.generate_content(
                model="veo-3",
                contents=[{
                    "role": "user",
                    "parts": [{
                        "text": f"Generate a {duration}-second video: {prompt}"
                    }]
                }]
            )
            
            # Handle the response and save video
            # This is a simplified implementation - actual Veo API may differ
            if response and hasattr(response, 'video_url'):
                # Download and save the video
                video_path = self._download_video(response.video_url)
                self.logger.info(f"Video generated successfully: {video_path}")
                return video_path
            else:
                self.logger.warning("No video URL in response")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating video: {e}")
            return None
    
    def _download_video(self, video_url: str) -> Optional[str]:
        """Download video from URL and save locally."""
        try:
            import requests
            import tempfile
            import os
            
            # Create temporary file for video
            temp_dir = tempfile.gettempdir()
            video_filename = f"veo_video_{os.getpid()}.mp4"
            video_path = os.path.join(temp_dir, video_filename)
            
            # Download video
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return video_path
            
        except Exception as e:
            self.logger.error(f"Error downloading video: {e}")
            return None 