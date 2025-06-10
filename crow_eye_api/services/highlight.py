import asyncio
import tempfile
import os
import shutil
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging

from crow_eye_api.services.storage import storage_service


@dataclass
class HighlightResult:
    """Result of highlight generation operation."""
    success: bool
    output_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: float = 0.0
    style_used: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    error_message: Optional[str] = None


class HighlightService:
    """Service for generating video highlights using the desktop VideoHandler."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.temp_dir = tempfile.gettempdir()
        
    async def generate_highlight_reel(
        self,
        media_item,
        target_duration: int = 30,
        highlight_type: str = "story",
        style: str = "dynamic",
        include_text: bool = True,
        include_music: bool = False,
        prompt: str = "",
        example_data: Optional[Dict[str, Any]] = None,
        context_padding: float = 2.0,
        content_instructions: Optional[str] = None
    ) -> HighlightResult:
        """
        Generate a highlight reel from a video media item.
        
        Args:
            media_item: Database media item containing video information
            target_duration: Target duration in seconds
            highlight_type: Type of highlight (story, reel, short)
            style: Style of the highlight (dynamic, minimal, elegant)
            include_text: Whether to include text overlays
            include_music: Whether to include background music
            prompt: Optional prompt for AI guidance
            example_data: Optional example segment data for similarity-based detection
            context_padding: Seconds of context to add before each highlight scene
            content_instructions: Additional content guidance and instructions
            
        Returns:
            HighlightResult with success status and output information
        """
        temp_input_path = None
        temp_output_path = None
        
        try:
            # Download video from storage to temporary location
            self.logger.info(f"Downloading video for highlight generation: {media_item.filename}")
            temp_input_path = await self._download_media_to_temp(media_item)
            
            if not temp_input_path or not os.path.exists(temp_input_path):
                return HighlightResult(
                    success=False,
                    error_message="Failed to download video from storage"
                )
            
            # Import VideoHandler dynamically to avoid circular imports
            try:
                # Try to import from the desktop application's VideoHandler
                import sys
                import importlib.util
                
                # Look for VideoHandler in the parent directory structure
                video_handler_path = None
                current_dir = os.path.dirname(os.path.abspath(__file__))
                
                # Try different possible paths
                possible_paths = [
                    os.path.join(current_dir, "../../../src/features/media_processing/video_handler.py"),
                    os.path.join(current_dir, "../../src/features/media_processing/video_handler.py"),
                    os.path.join(current_dir, "../src/features/media_processing/video_handler.py"),
                ]
                
                for path in possible_paths:
                    abs_path = os.path.abspath(path)
                    if os.path.exists(abs_path):
                        video_handler_path = abs_path
                        break
                
                if not video_handler_path:
                    return HighlightResult(
                        success=False,
                        error_message="VideoHandler not found in expected locations"
                    )
                
                # Load VideoHandler module
                spec = importlib.util.spec_from_file_location("video_handler", video_handler_path)
                video_handler_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(video_handler_module)
                
                VideoHandler = video_handler_module.VideoHandler
                
            except Exception as e:
                self.logger.error(f"Failed to import VideoHandler: {e}")
                return HighlightResult(
                    success=False,
                    error_message=f"Failed to load video processing module: {str(e)}"
                )
            
            # Initialize VideoHandler
            video_handler = VideoHandler()
            
            # Build prompt based on parameters
            if not prompt:
                prompt = self._build_prompt_from_params(highlight_type, style, include_text, include_music)
            
            # Add content instructions to prompt if provided
            if content_instructions:
                prompt = f"{prompt}\n\nAdditional instructions: {content_instructions}"
            
            # Generate highlight reel with example-based detection
            self.logger.info(f"Generating highlight reel with duration {target_duration}s")
            if example_data:
                self.logger.info("Using example-based similarity detection")
                success, output_path, message = await asyncio.get_event_loop().run_in_executor(
                    None,
                    video_handler.generate_example_based_highlight_reel,
                    temp_input_path,
                    example_data,
                    target_duration,
                    context_padding,
                    prompt
                )
            else:
                success, output_path, message = await asyncio.get_event_loop().run_in_executor(
                    None,
                    video_handler.generate_highlight_reel,
                    temp_input_path,
                    target_duration,
                    prompt
                )
            
            if not success:
                return HighlightResult(
                    success=False,
                    error_message=message or "Highlight generation failed"
                )
            
            # Upload result back to storage
            output_url = await self._upload_result_to_storage(output_path, media_item)
            
            # Generate thumbnail
            thumbnail_url = await self._generate_and_upload_thumbnail(output_path, media_item)
            
            # Get video info for metadata
            video_info = video_handler.get_video_info(output_path)
            
            # Clean up temporary files
            if temp_input_path and os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
            if output_path and os.path.exists(output_path):
                os.unlink(output_path)
            
            return HighlightResult(
                success=True,
                output_url=output_url,
                thumbnail_url=thumbnail_url,
                duration=video_info.get('duration', target_duration),
                style_used=style,
                metadata={
                    'original_filename': media_item.filename,
                    'highlight_type': highlight_type,
                    'target_duration': target_duration,
                    'actual_duration': video_info.get('duration', target_duration),
                    'generation_time': datetime.now().isoformat(),
                    'prompt_used': prompt,
                    'include_text': include_text,
                    'include_music': include_music
                },
                message=message or f"Successfully generated {highlight_type} highlight"
            )
            
        except Exception as e:
            self.logger.exception(f"Error generating highlight reel: {e}")
            
            # Clean up temporary files on error
            if temp_input_path and os.path.exists(temp_input_path):
                try:
                    os.unlink(temp_input_path)
                except:
                    pass
            
            return HighlightResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def _download_media_to_temp(self, media_item) -> Optional[str]:
        """Download media from storage to temporary file."""
        try:
            # Create temporary file with appropriate extension
            file_ext = os.path.splitext(media_item.filename)[1] or '.mp4'
            temp_fd, temp_path = tempfile.mkstemp(suffix=file_ext)
            os.close(temp_fd)
            
            # Download from storage
            blob = storage_service.bucket.blob(media_item.filename)
            await asyncio.get_event_loop().run_in_executor(
                None,
                blob.download_to_filename,
                temp_path
            )
            
            return temp_path
            
        except Exception as e:
            self.logger.error(f"Failed to download media to temp: {e}")
            return None
    
    async def _upload_result_to_storage(self, local_path: str, original_media_item) -> str:
        """Upload generated highlight to storage and return URL."""
        try:
            # Generate new filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(original_media_item.filename)[0]
            new_filename = f"{base_name}_highlight_{timestamp}.mp4"
            
            # Upload to storage
            blob = storage_service.bucket.blob(f"highlights/{new_filename}")
            await asyncio.get_event_loop().run_in_executor(
                None,
                blob.upload_from_filename,
                local_path
            )
            
            # Return public URL or signed URL
            return blob.public_url if blob.public_url else blob.generate_signed_url(
                expiration=datetime.now() + timedelta(hours=24)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to upload result to storage: {e}")
            return ""
    
    async def _generate_and_upload_thumbnail(self, video_path: str, original_media_item) -> str:
        """Generate thumbnail from video and upload to storage."""
        try:
            import cv2
            
            # Extract frame from video
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_MSEC, 1000)  # 1 second into video
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return ""
            
            # Save thumbnail to temp file
            temp_fd, temp_thumb_path = tempfile.mkstemp(suffix='.jpg')
            os.close(temp_fd)
            cv2.imwrite(temp_thumb_path, frame)
            
            # Upload thumbnail
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(original_media_item.filename)[0]
            thumb_filename = f"{base_name}_highlight_{timestamp}_thumb.jpg"
            
            blob = storage_service.bucket.blob(f"thumbnails/{thumb_filename}")
            await asyncio.get_event_loop().run_in_executor(
                None,
                blob.upload_from_filename,
                temp_thumb_path
            )
            
            # Clean up temp file
            os.unlink(temp_thumb_path)
            
            return blob.public_url if blob.public_url else blob.generate_signed_url(
                expiration=datetime.now() + timedelta(hours=24)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate thumbnail: {e}")
            return ""
    
    def _build_prompt_from_params(
        self, 
        highlight_type: str, 
        style: str, 
        include_text: bool, 
        include_music: bool
    ) -> str:
        """Build AI prompt based on highlight parameters."""
        prompts = {
            "story": "Create engaging story highlights with smooth transitions",
            "reel": "Generate dynamic reel content with high energy moments",
            "short": "Focus on quick, attention-grabbing moments for short-form content",
            "action": "Emphasize action sequences and movement",
            "highlights": "Extract the most interesting and engaging moments"
        }
        
        base_prompt = prompts.get(highlight_type, prompts["highlights"])
        
        style_modifiers = {
            "dynamic": "with dynamic pacing and energy",
            "minimal": "with clean, minimal transitions",
            "elegant": "with smooth, elegant flow",
            "cinematic": "with cinematic timing and composition"
        }
        
        if style in style_modifiers:
            base_prompt += f" {style_modifiers[style]}"
        
        if include_text:
            base_prompt += ". Include moments suitable for text overlays"
        
        if include_music:
            base_prompt += ". Focus on moments that would work well with background music"
        
        return base_prompt

    async def generate_extended_highlight_reel_beta(
        self,
        media_item,
        target_duration: int = 900,  # 15 minutes default
        prompt: str = "",
        max_cost: float = 1.0,
        content_instructions: Optional[str] = None
    ) -> HighlightResult:
        """
        BETA: Generate highlight reels from extended videos (hours long) while keeping costs under $1.
        Uses multi-stage analysis: cheap pre-filtering + smart AI analysis on promising segments only.
        
        Args:
            media_item: Database media item containing video information
            target_duration: Target duration in seconds (default: 15 minutes = 900s)
            prompt: Natural language prompt for content guidance
            max_cost: Maximum cost allowed for analysis (default: $1.00)
            content_instructions: Additional content guidance and instructions
            
        Returns:
            HighlightResult with success status and output information
        """
        temp_input_path = None
        temp_output_path = None
        
        try:
            # Download video from storage to temporary location
            self.logger.info(f"[BETA] Downloading extended video for highlight generation: {media_item.filename}")
            temp_input_path = await self._download_media_to_temp(media_item)
            
            if not temp_input_path or not os.path.exists(temp_input_path):
                return HighlightResult(
                    success=False,
                    error_message="Failed to download video from storage"
                )
            
            # Import VideoHandler
            try:
                import sys
                import importlib.util
                
                # Look for VideoHandler in the parent directory structure
                video_handler_path = None
                current_dir = os.path.dirname(os.path.abspath(__file__))
                
                # Try different possible paths
                possible_paths = [
                    os.path.join(current_dir, "../../../src/features/media_processing/video_handler.py"),
                    os.path.join(current_dir, "../../src/features/media_processing/video_handler.py"),
                    os.path.join(current_dir, "../src/features/media_processing/video_handler.py"),
                ]
                
                for path in possible_paths:
                    abs_path = os.path.abspath(path)
                    if os.path.exists(abs_path):
                        video_handler_path = abs_path
                        break
                
                if not video_handler_path:
                    return HighlightResult(
                        success=False,
                        error_message="VideoHandler not found in expected locations"
                    )
                
                # Load VideoHandler module
                spec = importlib.util.spec_from_file_location("video_handler", video_handler_path)
                video_handler_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(video_handler_module)
                
                VideoHandler = video_handler_module.VideoHandler
                
            except Exception as e:
                self.logger.error(f"Failed to import VideoHandler: {e}")
                return HighlightResult(
                    success=False,
                    error_message=f"Failed to load video processing module: {str(e)}"
                )
            
            # Initialize VideoHandler
            video_handler = VideoHandler()
            
            # Add content instructions to prompt if provided
            if content_instructions:
                prompt = f"{prompt}\n\nAdditional instructions: {content_instructions}"
            
            # Generate extended highlight reel using BETA method
            self.logger.info(f"[BETA] Generating extended highlight reel with duration {target_duration}s, max cost ${max_cost:.2f}")
            success, output_path, message = await asyncio.get_event_loop().run_in_executor(
                None,
                video_handler.generate_extended_highlight_reel_beta,
                temp_input_path,
                target_duration,
                prompt,
                max_cost
            )
            
            if not success:
                return HighlightResult(
                    success=False,
                    error_message=message or "Extended highlight generation failed"
                )
            
            # Upload result back to storage
            output_url = await self._upload_result_to_storage(output_path, media_item)
            
            # Generate thumbnail
            thumbnail_url = await self._generate_and_upload_thumbnail(output_path, media_item)
            
            # Get video info for metadata
            video_info = video_handler.get_video_info(output_path)
            
            # Clean up temporary files
            if temp_input_path and os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
            if output_path and os.path.exists(output_path):
                os.unlink(output_path)
            
            return HighlightResult(
                success=True,
                output_url=output_url,
                thumbnail_url=thumbnail_url,
                duration=video_info.get('duration', target_duration),
                style_used="extended_beta",
                metadata={
                    'original_filename': media_item.filename,
                    'highlight_type': 'extended_beta',
                    'target_duration': target_duration,
                    'actual_duration': video_info.get('duration', target_duration),
                    'generation_time': datetime.now().isoformat(),
                    'prompt_used': prompt,
                    'max_cost_budget': max_cost,
                    'processing_mode': 'BETA_extended_video',
                    'cost_optimized': True
                },
                message=f"{message} - BETA Extended Mode" if message else f"Successfully generated extended highlight (BETA) - cost optimized for long videos"
            )
            
        except Exception as e:
            self.logger.exception(f"Error generating extended highlight reel: {e}")
            
            # Clean up temporary files on error
            if temp_input_path and os.path.exists(temp_input_path):
                try:
                    os.unlink(temp_input_path)
                except:
                    pass
            
            return HighlightResult(
                success=False,
                error_message=f"Extended highlight generation failed: {str(e)}"
            )


# Create service instance
highlight_service = HighlightService() 