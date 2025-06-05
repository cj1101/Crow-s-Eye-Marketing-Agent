"""
Simple Veo wrapper class - Start small and expand gradually
"""
import os
import time
import logging
from typing import Tuple, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SimpleVeoHandler:
    """
    Very simple Veo handler - just basic video generation
    """
    
    def __init__(self):
        """Initialize the simple Veo handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """Set up the Google Gen AI client."""
        try:
            from google import genai
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set")
            
            self.client = genai.Client(api_key=api_key)
            self.logger.info("✅ Veo client initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Veo client: {e}")
            self.client = None
    
    def is_ready(self) -> bool:
        """Check if the handler is ready to generate videos."""
        api_key = os.getenv("GOOGLE_API_KEY")
        return self.client is not None and api_key is not None
    
    def generate_simple_video(self, prompt: str) -> Tuple[bool, str, str]:
        """
        Generate a simple video with basic settings.
        
        Args:
            prompt: Text description of the video
            
        Returns:
            Tuple[bool, str, str]: (success, video_path_or_error, message)
        """
        if not self.is_ready():
            return False, "", "Veo handler not ready - check API key and setup"
        
        try:
            from google.genai import types
            
            self.logger.info(f"🎬 Generating video: {prompt[:50]}...")
            
            # Use simple, safe settings
            operation = self.client.models.generate_videos(
                model="veo-2.0-generate-001",
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio="16:9",
                    person_generation="dont_allow",  # Safe default
                    number_of_videos=1,
                    duration_seconds=5  # Short for testing
                )
            )
            
            # Wait for completion
            self.logger.info("⏳ Waiting for video generation...")
            start_time = time.time()
            
            while not operation.done:
                elapsed = time.time() - start_time
                if elapsed > 600:  # 10 minute timeout
                    return False, "", "Video generation timed out"
                
                time.sleep(20)
                operation = self.client.operations.get(operation)
            
            # Handle result
            if operation.response and operation.response.generated_videos:
                video = operation.response.generated_videos[0]
                
                # Generate simple filename
                timestamp = int(time.time())
                output_path = f"veo_video_{timestamp}.mp4"
                
                # Download and save
                self.client.files.download(file=video.video)
                video.video.save(output_path)
                
                self.logger.info(f"✅ Video saved: {output_path}")
                return True, output_path, "Video generated successfully"
            else:
                return False, "", "No video was generated"
                
        except Exception as e:
            self.logger.error(f"❌ Error generating video: {e}")
            return False, "", f"Error: {str(e)}"
    
    def get_status(self) -> dict:
        """Get simple status information."""
        return {
            "ready": self.is_ready(),
            "has_api_key": os.getenv("GOOGLE_API_KEY") is not None,
            "client_initialized": self.client is not None
        } 