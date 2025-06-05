"""
Video processing handler for Crow's Eye marketing automation platform.
Implements highlight reel generation, story assistant, and thumbnail selection.
"""

import os
import logging
import tempfile
import math
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip
from moviepy.video.fx import resize, crop
from PIL import Image

from ...config import constants as const


class VideoHandler:
    """Handles video processing operations for Crow's Eye platform."""
    
    def __init__(self):
        """Initialize the video handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.temp_dir = tempfile.gettempdir()
        
        # Initialize analytics handler
        try:
            from ...handlers.analytics_handler import AnalyticsHandler
            self.analytics_handler = AnalyticsHandler()
        except Exception as e:
            self.logger.warning(f"Could not initialize analytics handler: {e}")
            self.analytics_handler = None
        
    def generate_highlight_reel(self, video_path: str, target_duration: int = 30, 
                              prompt: str = "") -> Tuple[bool, str, str]:
        """
        Generate a highlight reel from a long video.
        
        Args:
            video_path: Path to the source video
            target_duration: Target duration in seconds (default: 30)
            prompt: Natural language prompt for what to include/exclude
            
        Returns:
            Tuple[bool, str, str]: (success, output_path, message)
        """
        try:
            if not os.path.exists(video_path):
                return False, "", f"Video file not found: {video_path}"
            
            self.logger.info(f"Generating highlight reel from {video_path}")
            
            # Load video
            clip = VideoFileClip(video_path)
            original_duration = clip.duration
            
            if original_duration <= target_duration:
                self.logger.info("Video is already shorter than target duration")
                return True, video_path, "Video is already the right length"
            
            # Analyze prompt for specific instructions
            segments = self._analyze_video_for_highlights(clip, target_duration, prompt)
            
            # Create highlight reel
            highlight_clips = []
            for start, end in segments:
                highlight_clips.append(clip.subclip(start, end))
            
            # Concatenate clips
            if highlight_clips:
                final_clip = concatenate_videoclips(highlight_clips)
                
                # Generate output filename
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{base_name}_highlight_{timestamp}.mp4"
                output_path = os.path.join(const.OUTPUT_DIR, output_filename)
                
                # Ensure output directory exists
                os.makedirs(const.OUTPUT_DIR, exist_ok=True)
                
                # Write video
                final_clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True
                )
                
                # Clean up
                clip.close()
                final_clip.close()
                for highlight_clip in highlight_clips:
                    highlight_clip.close()
                
                # Track video processing in analytics
                if self.analytics_handler:
                    try:
                        self.analytics_handler.track_video_processing(
                            video_path, "highlight_reel", output_path
                        )
                    except Exception as e:
                        self.logger.warning(f"Could not track video processing: {e}")
                
                self.logger.info(f"Highlight reel saved to {output_path}")
                return True, output_path, f"Highlight reel created ({len(segments)} segments)"
            else:
                clip.close()
                return False, "", "No suitable segments found for highlight reel"
                
        except Exception as e:
            self.logger.exception(f"Error generating highlight reel: {e}")
            return False, "", f"Error generating highlight reel: {str(e)}"
    
    def create_story_clips(self, video_path: str, max_clip_duration: int = 60) -> Tuple[bool, List[str], str]:
        """
        Create story-formatted clips from a long video.
        
        Args:
            video_path: Path to the source video
            max_clip_duration: Maximum duration per clip in seconds
            
        Returns:
            Tuple[bool, List[str], str]: (success, list_of_output_paths, message)
        """
        try:
            if not os.path.exists(video_path):
                return False, [], f"Video file not found: {video_path}"
            
            self.logger.info(f"Creating story clips from {video_path}")
            
            # Load video
            clip = VideoFileClip(video_path)
            original_duration = clip.duration
            
            # Calculate number of clips needed
            num_clips = math.ceil(original_duration / max_clip_duration)
            
            output_paths = []
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Ensure output directory exists
            os.makedirs(const.OUTPUT_DIR, exist_ok=True)
            
            for i in range(num_clips):
                start_time = i * max_clip_duration
                end_time = min((i + 1) * max_clip_duration, original_duration)
                
                # Extract clip
                story_clip = clip.subclip(start_time, end_time)
                
                # Format for vertical story (9:16 aspect ratio)
                story_clip = self._format_for_story(story_clip)
                
                # Generate output filename
                output_filename = f"{base_name}_story_{i+1}_{timestamp}.mp4"
                output_path = os.path.join(const.OUTPUT_DIR, output_filename)
                
                # Write video
                story_clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile=f'temp-audio-{i}.m4a',
                    remove_temp=True
                )
                
                output_paths.append(output_path)
                story_clip.close()
            
            # Clean up
            clip.close()
            
            # Track video processing in analytics
            if self.analytics_handler:
                try:
                    for output_path in output_paths:
                        self.analytics_handler.track_video_processing(
                            video_path, "story_clips", output_path
                        )
                except Exception as e:
                    self.logger.warning(f"Could not track video processing: {e}")
            
            self.logger.info(f"Created {len(output_paths)} story clips")
            return True, output_paths, f"Created {len(output_paths)} story clips"
            
        except Exception as e:
            self.logger.exception(f"Error creating story clips: {e}")
            return False, [], f"Error creating story clips: {str(e)}"
    
    def generate_video_thumbnails(self, video_path: str, num_thumbnails: int = 6) -> Tuple[bool, List[str], str]:
        """
        Generate thumbnail images from a video for selection.
        
        Args:
            video_path: Path to the video file
            num_thumbnails: Number of thumbnails to generate
            
        Returns:
            Tuple[bool, List[str], str]: (success, list_of_thumbnail_paths, message)
        """
        try:
            if not os.path.exists(video_path):
                return False, [], f"Video file not found: {video_path}"
            
            self.logger.info(f"Generating thumbnails for {video_path}")
            
            # Load video
            clip = VideoFileClip(video_path)
            duration = clip.duration
            
            thumbnail_paths = []
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Ensure output directory exists
            os.makedirs(const.OUTPUT_DIR, exist_ok=True)
            
            # Generate thumbnails at evenly spaced intervals
            for i in range(num_thumbnails):
                # Calculate time position (avoid very beginning and end)
                time_position = (duration * (i + 1)) / (num_thumbnails + 1)
                
                # Extract frame
                frame = clip.get_frame(time_position)
                
                # Convert to PIL Image
                pil_image = Image.fromarray(frame)
                
                # Generate thumbnail filename
                thumbnail_filename = f"{base_name}_thumb_{i+1}_{timestamp}.jpg"
                thumbnail_path = os.path.join(const.OUTPUT_DIR, thumbnail_filename)
                
                # Save thumbnail
                pil_image.save(thumbnail_path, 'JPEG', quality=90)
                thumbnail_paths.append(thumbnail_path)
            
            # Clean up
            clip.close()
            
            self.logger.info(f"Generated {len(thumbnail_paths)} thumbnails")
            return True, thumbnail_paths, f"Generated {len(thumbnail_paths)} thumbnails"
            
        except Exception as e:
            self.logger.exception(f"Error generating thumbnails: {e}")
            return False, [], f"Error generating thumbnails: {str(e)}"
    
    def generate_thumbnail(self, video_path: str, timestamp: float = 1.0) -> Tuple[bool, str, str]:
        """
        Generate a single thumbnail from a video at a specific timestamp.
        
        Args:
            video_path: Path to the video file
            timestamp: Time position in seconds to extract thumbnail
            
        Returns:
            Tuple[bool, str, str]: (success, thumbnail_path, message)
        """
        try:
            if not os.path.exists(video_path):
                return False, "", f"Video file not found: {video_path}"
            
            self.logger.info(f"Generating thumbnail for {video_path} at {timestamp}s")
            
            # Load video
            clip = VideoFileClip(video_path)
            duration = clip.duration
            
            # Ensure timestamp is within video duration
            timestamp = min(timestamp, duration - 0.1)
            timestamp = max(0.1, timestamp)
            
            # Extract frame
            frame = clip.get_frame(timestamp)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(frame)
            
            # Generate thumbnail filename
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            thumbnail_filename = f"{base_name}_thumb_{timestamp_str}.jpg"
            thumbnail_path = os.path.join(const.OUTPUT_DIR, thumbnail_filename)
            
            # Ensure output directory exists
            os.makedirs(const.OUTPUT_DIR, exist_ok=True)
            
            # Save thumbnail
            pil_image.save(thumbnail_path, 'JPEG', quality=90)
            
            # Clean up
            clip.close()
            
            self.logger.info(f"Thumbnail saved to {thumbnail_path}")
            return True, thumbnail_path, "Thumbnail generated successfully"
            
        except Exception as e:
            self.logger.exception(f"Error generating thumbnail: {e}")
            return False, "", f"Error generating thumbnail: {str(e)}"

    def add_audio_overlay(self, video_path: str, audio_path: str, 
                         volume: float = 1.0, start_time: float = 0.0) -> Tuple[bool, str, str]:
        """
        Add audio overlay to a video.
        
        Args:
            video_path: Path to the video file
            audio_path: Path to the audio file
            volume: Audio volume (0.0 to 1.0)
            start_time: When to start the audio overlay
            
        Returns:
            Tuple[bool, str, str]: (success, output_path, message)
        """
        try:
            if not os.path.exists(video_path):
                return False, "", f"Video file not found: {video_path}"
            if not os.path.exists(audio_path):
                return False, "", f"Audio file not found: {audio_path}"
            
            self.logger.info(f"Adding audio overlay to {video_path}")
            
            # Load video and audio
            video_clip = VideoFileClip(video_path)
            from moviepy.editor import AudioFileClip
            audio_clip = AudioFileClip(audio_path)
            
            # Adjust audio volume
            if volume != 1.0:
                audio_clip = audio_clip.volumex(volume)
            
            # Set audio start time
            if start_time > 0:
                audio_clip = audio_clip.set_start(start_time)
            
            # Combine video with new audio
            final_clip = video_clip.set_audio(audio_clip)
            
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{base_name}_with_audio_{timestamp}.mp4"
            output_path = os.path.join(const.OUTPUT_DIR, output_filename)
            
            # Ensure output directory exists
            os.makedirs(const.OUTPUT_DIR, exist_ok=True)
            
            # Write video
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # Clean up
            video_clip.close()
            audio_clip.close()
            final_clip.close()
            
            self.logger.info(f"Video with audio overlay saved to {output_path}")
            return True, output_path, "Audio overlay added successfully"
            
        except Exception as e:
            self.logger.exception(f"Error adding audio overlay: {e}")
            return False, "", f"Error adding audio overlay: {str(e)}"
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dict containing video information, empty dict if file doesn't exist
        """
        try:
            if not os.path.exists(video_path):
                self.logger.warning(f"Video file not found: {video_path}")
                return {}
            
            # Use OpenCV for basic info
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self.logger.error(f"Could not open video file: {video_path}")
                return {}
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            # Get file size
            file_size = os.path.getsize(video_path)
            
            return {
                "width": width,
                "height": height,
                "fps": fps,
                "frame_count": frame_count,
                "duration": duration,
                "file_size": file_size,
                "aspect_ratio": width / height if height > 0 else 0,
                "is_vertical": height > width,
                "filename": os.path.basename(video_path)
            }
            
        except Exception as e:
            self.logger.exception(f"Error getting video info: {e}")
            return {}
    
    def _analyze_video_for_highlights(self, clip, target_duration: int, prompt: str) -> List[Tuple[float, float]]:
        """
        Analyze video to find highlight segments based on prompt.
        
        This is a simplified implementation. In a real-world scenario,
        you might use more sophisticated video analysis techniques.
        """
        duration = clip.duration
        segment_length = target_duration / 3  # Create 3 segments by default
        
        # Simple strategy: take segments from beginning, middle, and end
        segments = []
        
        if "beginning" in prompt.lower() or "start" in prompt.lower():
            segments.append((0, min(segment_length, duration)))
        elif "end" in prompt.lower() or "finish" in prompt.lower():
            start_time = max(0, duration - segment_length)
            segments.append((start_time, duration))
        elif "middle" in prompt.lower():
            start_time = (duration - segment_length) / 2
            segments.append((start_time, start_time + segment_length))
        else:
            # Default: take segments from beginning, middle, and end
            if duration > target_duration:
                # Beginning
                segments.append((0, segment_length))
                
                # Middle
                middle_start = (duration - segment_length) / 2
                segments.append((middle_start, middle_start + segment_length))
                
                # End
                end_start = duration - segment_length
                segments.append((end_start, duration))
            else:
                segments.append((0, duration))
        
        return segments
    
    def _format_for_story(self, clip):
        """
        Format a video clip for Instagram/Facebook Stories (9:16 aspect ratio).
        """
        # Get current dimensions
        width, height = clip.size
        current_ratio = width / height
        target_ratio = 9 / 16  # Story aspect ratio
        
        if abs(current_ratio - target_ratio) < 0.01:
            # Already correct ratio
            return clip
        
        # Calculate new dimensions
        if current_ratio > target_ratio:
            # Video is too wide, crop sides
            new_width = int(height * target_ratio)
            new_height = height
            x_offset = (width - new_width) // 2
            y_offset = 0
        else:
            # Video is too tall, crop top/bottom
            new_width = width
            new_height = int(width / target_ratio)
            x_offset = 0
            y_offset = (height - new_height) // 2
        
        # Crop the video
        cropped_clip = crop(clip, x1=x_offset, y1=y_offset, 
                           x2=x_offset + new_width, y2=y_offset + new_height)
        
        # Resize to standard story dimensions (1080x1920)
        final_clip = resize(cropped_clip, (1080, 1920))
        
        return final_clip 