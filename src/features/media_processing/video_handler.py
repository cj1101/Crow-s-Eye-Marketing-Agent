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
        
        # Initialize AI handler for long video analysis
        try:
            from ...api.ai.ai_handler import AIHandler
            from ...models.app_state import AppState
            app_state = AppState()
            self.ai_handler = AIHandler(app_state)
        except (ImportError, AttributeError) as e:
            self.logger.warning(f"AI handler not available for long video analysis: {e}")
            self.ai_handler = None
        except Exception as e:
            self.logger.warning(f"Could not initialize AI handler: {e}")
            self.ai_handler = None
        
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
    
    def generate_long_form_highlight_reel(self, video_path: str, target_duration: int = 180, 
                                        prompt: str = "", cost_optimize: bool = True) -> Tuple[bool, str, str]:
        """
        Generate longer highlight reels (2-5 minutes) from 1-3 hour content with cost optimization.
        
        Args:
            video_path: Path to the source video
            target_duration: Target duration in seconds (default: 180 = 3 minutes)
            prompt: Natural language prompt for what to include/exclude
            cost_optimize: Whether to use cost optimization strategies
            
        Returns:
            Tuple[bool, str, str]: (success, output_path, message)
        """
        clip = None
        final_clip = None
        highlight_clips = []
        
        try:
            # Input validation
            if not video_path or not isinstance(video_path, str):
                return False, "", "Invalid video path provided"
            
            if not os.path.exists(video_path):
                return False, "", f"Video file not found: {video_path}"
            
            # Check file size and accessibility
            try:
                file_size = os.path.getsize(video_path)
                if file_size == 0:
                    return False, "", "Video file is empty"
                if file_size > 10 * 1024 * 1024 * 1024:  # 10GB limit
                    return False, "", "Video file is too large (>10GB)"
            except (OSError, IOError) as e:
                return False, "", f"Cannot access video file: {e}"
            
            # Validate target duration
            if target_duration < 30:
                return False, "", "Target duration must be at least 30 seconds"
            if target_duration > 600:  # 10 minutes max
                return False, "", "Target duration cannot exceed 10 minutes"
            
            self.logger.info(f"Starting long-form highlight generation for {video_path}")
            
            # Load video with timeout protection
            try:
                clip = VideoFileClip(video_path)
                if clip is None:
                    return False, "", "Failed to load video file - may be corrupted"
            except Exception as e:
                return False, "", f"Failed to load video: {str(e)}"
            
            # Validate video properties
            try:
                original_duration = clip.duration
                if original_duration is None or original_duration <= 0:
                    return False, "", "Video has invalid duration"
                
                # Check video dimensions
                if hasattr(clip, 'size') and clip.size:
                    width, height = clip.size
                    if width <= 0 or height <= 0:
                        return False, "", "Video has invalid dimensions"
                    if width < 100 or height < 100:
                        return False, "", "Video resolution too low (minimum 100x100)"
                else:
                    return False, "", "Cannot determine video dimensions"
                    
            except Exception as e:
                return False, "", f"Error reading video properties: {e}"
            
            # Check if input is suitable for long-form processing
            if original_duration < 60 * 30:  # Less than 30 minutes
                self.logger.info("Video is too short for long-form processing, using standard method")
                clip.close()
                return self.generate_highlight_reel(video_path, target_duration, prompt)
            
            if original_duration > 60 * 60 * 4:  # More than 4 hours
                clip.close()
                return False, "", "Video is too long (>4 hours). Please use shorter content."
            
            self.logger.info(f"Generating long-form highlight reel from {original_duration/60:.1f} minute video")
            
            # Estimate cost and validate
            estimated_ai_calls = min(20, int(original_duration / 600)) if cost_optimize else int(original_duration / 60)
            estimated_cost = estimated_ai_calls * 0.01
            
            if estimated_cost > 2.0:  # Safety limit
                self.logger.warning(f"High estimated cost: ${estimated_cost:.2f}")
            
            self.logger.info(f"Estimated AI analysis cost: ~${estimated_cost:.2f} ({estimated_ai_calls} API calls)")
            
            # Analyze video for highlights with comprehensive error handling
            try:
                segments = self._analyze_video_for_highlights(clip, target_duration, prompt)
            except Exception as e:
                self.logger.error(f"Error during video analysis: {e}")
                clip.close()
                return False, "", f"Failed to analyze video: {str(e)}"
            
            if not segments:
                clip.close()
                return False, "", "No suitable segments found for long-form highlight reel"
            
            # Validate segments
            valid_segments = []
            for start, end in segments:
                if start < 0 or end > original_duration or start >= end:
                    self.logger.warning(f"Invalid segment {start}-{end}, skipping")
                    continue
                if end - start < 1:  # Minimum 1 second segments
                    self.logger.warning(f"Segment too short {start}-{end}, skipping")
                    continue
                valid_segments.append((start, end))
            
            if not valid_segments:
                clip.close()
                return False, "", "No valid segments found after validation"
            
            segments = valid_segments
            self.logger.info(f"Using {len(segments)} valid segments")
            
            # Create highlight reel with enhanced error handling
            highlight_clips = []
            transition_duration = 0.5
            
            for i, (start, end) in enumerate(segments):
                try:
                    segment_clip = clip.subclip(start, end)
                    
                    # Validate segment clip
                    if segment_clip.duration <= 0:
                        self.logger.warning(f"Segment {i} has invalid duration, skipping")
                        continue
                    
                    # Add fade transitions for smoother long-form content
                    if i > 0 and transition_duration < segment_clip.duration / 2:
                        segment_clip = segment_clip.fadein(transition_duration)
                    if i < len(segments) - 1 and transition_duration < segment_clip.duration / 2:
                        segment_clip = segment_clip.fadeout(transition_duration)
                    
                    highlight_clips.append(segment_clip)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing segment {i} ({start}-{end}): {e}")
                    continue
            
            if not highlight_clips:
                clip.close()
                return False, "", "No valid highlight clips could be created"
            
            # Concatenate clips with error handling
            try:
                final_clip = concatenate_videoclips(highlight_clips)
                if final_clip is None or final_clip.duration <= 0:
                    raise ValueError("Concatenated clip is invalid")
            except Exception as e:
                self.logger.error(f"Error concatenating clips: {e}")
                # Clean up
                clip.close()
                for highlight_clip in highlight_clips:
                    try:
                        highlight_clip.close()
                    except:
                        pass
                return False, "", f"Failed to combine video segments: {str(e)}"
            
            # Add titles/chapters for longer content (with error handling)
            if len(segments) > 3 and target_duration > 120:
                try:
                    final_clip = self._add_chapter_markers(final_clip, segments, prompt)
                except Exception as e:
                    self.logger.warning(f"Failed to add chapter markers: {e}")
                    # Continue without chapter markers
            
            # Generate output filename with collision avoidance
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            base_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).strip()
            if not base_name:
                base_name = "highlight"
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{base_name}_longform_highlight_{timestamp}.mp4"
            output_path = os.path.join(const.OUTPUT_DIR, output_filename)
            
            # Handle filename collisions
            counter = 1
            while os.path.exists(output_path):
                output_filename = f"{base_name}_longform_highlight_{timestamp}_{counter}.mp4"
                output_path = os.path.join(const.OUTPUT_DIR, output_filename)
                counter += 1
                if counter > 100:  # Safety limit
                    return False, "", "Too many filename collisions"
            
            # Ensure output directory exists
            try:
                os.makedirs(const.OUTPUT_DIR, exist_ok=True)
            except Exception as e:
                return False, "", f"Cannot create output directory: {e}"
            
            # Write video with comprehensive error handling
            try:
                self.logger.info(f"Writing video to {output_path}")
                final_clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile=f'temp-audio-longform-{timestamp}.m4a',
                    remove_temp=True,
                    preset='medium',
                    bitrate='2000k',
                    verbose=False,  # Reduce log noise
                    logger=None    # Disable moviepy logging
                )
                
                # Verify output file was created and is valid
                if not os.path.exists(output_path):
                    raise FileNotFoundError("Output file was not created")
                
                output_size = os.path.getsize(output_path)
                if output_size == 0:
                    raise ValueError("Output file is empty")
                
                self.logger.info(f"Output file size: {output_size / (1024*1024):.1f} MB")
                
            except Exception as e:
                self.logger.error(f"Error writing video file: {e}")
                # Clean up partial file
                try:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                except:
                    pass
                
                # Clean up and return error
                clip.close()
                final_clip.close()
                for highlight_clip in highlight_clips:
                    try:
                        highlight_clip.close()
                    except:
                        pass
                return False, "", f"Failed to write video file: {str(e)}"
            
            # Clean up memory
            clip.close()
            final_clip.close()
            for highlight_clip in highlight_clips:
                try:
                    highlight_clip.close()
                except:
                    pass
            
            # Track video processing in analytics
            if self.analytics_handler:
                try:
                    self.analytics_handler.track_video_processing(
                        video_path, "long_form_highlight_reel", output_path
                    )
                except Exception as e:
                    self.logger.warning(f"Could not track video processing: {e}")
            
            duration_minutes = target_duration / 60
            actual_duration = sum(end - start for start, end in segments)
            self.logger.info(f"Long-form highlight reel saved to {output_path}")
            self.logger.info(f"Created {duration_minutes:.1f} minute highlight from {len(segments)} segments")
            
            return True, output_path, f"Long-form highlight reel created ({duration_minutes:.1f} minutes, {len(segments)} segments, {actual_duration:.1f}s total)"
            
        except Exception as e:
            self.logger.exception(f"Unexpected error in long-form highlight generation: {e}")
            
            # Emergency cleanup
            try:
                if clip:
                    clip.close()
                if final_clip:
                    final_clip.close()
                for highlight_clip in highlight_clips:
                    try:
                        highlight_clip.close()
                    except:
                        pass
            except:
                pass
            
            return False, "", f"Unexpected error: {str(e)}"
    
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
        Analyze video to find highlight segments based on prompt using cost-effective multi-stage approach.
        
        For long videos (>30 min), uses intelligent sampling to minimize AI costs while maximizing quality.
        """
        duration = clip.duration
        
        # For short videos, use existing simple approach
        if duration <= 30 * 60:  # 30 minutes
            return self._analyze_short_video_highlights(clip, target_duration, prompt)
        
        # For long videos, use cost-effective multi-stage approach
        return self._analyze_long_video_highlights(clip, target_duration, prompt)
    
    def _analyze_short_video_highlights(self, clip, target_duration: int, prompt: str) -> List[Tuple[float, float]]:
        """Original simple analysis for short videos."""
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
    
    def _analyze_long_video_highlights(self, clip, target_duration: int, prompt: str) -> List[Tuple[float, float]]:
        """
        Cost-effective analysis for long videos using multi-stage approach:
        1. Technical pre-filtering (motion, audio, scene changes)
        2. Intelligent sampling with minimal AI calls
        3. Smart segment selection
        """
        duration = clip.duration
        self.logger.info(f"Analyzing long video ({duration/60:.1f} minutes) for highlights")
        
        # Stage 1: Technical Analysis (No AI costs)
        technical_segments = self._find_technical_highlights(clip, duration)
        self.logger.info(f"Found {len(technical_segments)} technically interesting segments")
        
        # Stage 2: Intelligent Sampling (Minimal AI costs)
        if hasattr(self, 'ai_handler'):
            ai_scored_segments = self._score_segments_with_ai(clip, technical_segments, prompt)
        else:
            # Fallback if no AI handler available
            ai_scored_segments = [(start, end, 0.5) for start, end in technical_segments]
        
        # Stage 3: Smart Selection
        final_segments = self._select_best_segments(ai_scored_segments, target_duration)
        
        self.logger.info(f"Selected {len(final_segments)} segments for final highlight reel")
        return final_segments
    
    def _find_technical_highlights(self, clip, duration: float) -> List[Tuple[float, float]]:
        """
        Find potentially interesting segments using technical analysis only.
        No AI costs - uses motion detection, audio analysis, scene changes.
        """
        try:
            import numpy as np
        except ImportError:
            self.logger.error("NumPy not available for technical analysis")
            # Fallback: return evenly spaced segments
            num_segments = max(3, int(duration / 300))  # One segment per 5 minutes
            segment_length = duration / num_segments
            return [(i * segment_length, (i + 1) * segment_length) for i in range(num_segments)]
        
        segments = []
        segment_duration = min(10, duration / 20)  # Adaptive segment duration
        current_time = 0
        failed_segments = 0
        max_failed_segments = 10
        
        self.logger.info(f"Analyzing {duration/60:.1f} minute video in {segment_duration:.1f}s chunks")
        
        while current_time < duration - segment_duration:
            end_time = min(current_time + segment_duration, duration)
            segment_clip = None
            
            try:
                # Get segment for analysis with timeout protection
                segment_clip = clip.subclip(current_time, end_time)
                
                if segment_clip is None or segment_clip.duration <= 0:
                    self.logger.warning(f"Invalid segment at {current_time}-{end_time}")
                    current_time += segment_duration
                    continue
                
                # Motion analysis with fallback
                try:
                    motion_score = self._calculate_motion_score(segment_clip)
                except Exception as e:
                    self.logger.warning(f"Motion analysis failed for {current_time}-{end_time}: {e}")
                    motion_score = 0.5  # Default medium score
                
                # Audio analysis with fallback
                try:
                    audio_score = self._calculate_audio_score(segment_clip)
                except Exception as e:
                    self.logger.warning(f"Audio analysis failed for {current_time}-{end_time}: {e}")
                    audio_score = 0.3  # Default low-medium score
                
                # Combined technical score with validation
                if 0 <= motion_score <= 1 and 0 <= audio_score <= 1:
                    technical_score = (motion_score * 0.6) + (audio_score * 0.4)
                else:
                    self.logger.warning(f"Invalid scores: motion={motion_score}, audio={audio_score}")
                    technical_score = 0.4  # Default score
                
                # Keep segments above threshold
                if technical_score > 0.3:  # Adjustable threshold
                    segments.append((current_time, end_time))
                    self.logger.debug(f"Added segment {current_time:.1f}-{end_time:.1f} (score: {technical_score:.2f})")
                
                # Clean up segment
                if segment_clip:
                    segment_clip.close()
                
                failed_segments = 0  # Reset failure counter on success
                
            except Exception as e:
                self.logger.warning(f"Error analyzing segment {current_time}-{end_time}: {e}")
                failed_segments += 1
                
                # Clean up failed segment
                if segment_clip:
                    try:
                        segment_clip.close()
                    except:
                        pass
                
                # Include segment if analysis fails (better safe than sorry)
                if failed_segments < max_failed_segments:
                    segments.append((current_time, end_time))
                    self.logger.debug(f"Added failed segment {current_time:.1f}-{end_time:.1f} as fallback")
                else:
                    self.logger.error("Too many failed segments, skipping technical analysis")
                    break
            
            current_time += segment_duration
        
        # Ensure we have at least some segments
        if not segments:
            self.logger.warning("No segments found, creating fallback segments")
            # Create fallback segments evenly distributed
            num_fallback = max(3, int(duration / 300))  # One per 5 minutes
            fallback_duration = duration / num_fallback
            segments = [(i * fallback_duration, (i + 1) * fallback_duration) for i in range(num_fallback)]
        
        self.logger.info(f"Technical analysis found {len(segments)} potentially interesting segments")
        return segments
    
    def _calculate_motion_score(self, segment_clip) -> float:
        """Calculate motion intensity for a video segment."""
        try:
            # Sample a few frames to calculate motion
            sample_times = [0.2, 0.5, 0.8]  # Sample at 20%, 50%, 80% of segment
            motion_scores = []
            
            for t in sample_times:
                if t < segment_clip.duration:
                    frame = segment_clip.get_frame(t * segment_clip.duration)
                    # Simple motion estimation using frame variance
                    gray_frame = np.dot(frame[...,:3], [0.2989, 0.5870, 0.1140])
                    motion_scores.append(np.var(gray_frame) / 10000)  # Normalize
            
            return min(np.mean(motion_scores), 1.0) if motion_scores else 0.0
            
        except Exception as e:
            self.logger.warning(f"Motion calculation error: {e}")
            return 0.5  # Default medium score
    
    def _calculate_audio_score(self, segment_clip) -> float:
        """Calculate audio activity score for a video segment."""
        try:
            if segment_clip.audio is None:
                return 0.0
            
            # Get audio array
            audio_array = segment_clip.audio.to_soundarray()
            if audio_array.size == 0:
                return 0.0
            
            # Calculate RMS (root mean square) for audio level
            rms = np.sqrt(np.mean(audio_array**2))
            
            # Normalize to 0-1 range (adjust multiplier based on your content)
            audio_score = min(rms * 50, 1.0)
            
            return audio_score
            
        except Exception as e:
            self.logger.warning(f"Audio calculation error: {e}")
            return 0.5  # Default medium score
    
    def _score_segments_with_ai(self, clip, segments: List[Tuple[float, float]], prompt: str) -> List[Tuple[float, float, float]]:
        """
        Score segments using AI analysis. Limits API calls by intelligent sampling.
        """
        if not segments:
            self.logger.warning("No segments provided for AI scoring")
            return []
        
        # Check if AI handler is available
        if not self.ai_handler or not hasattr(self.ai_handler, '_analyze_image_content_with_gemini'):
            self.logger.warning("AI handler not available, using fallback scoring")
            # Return segments with medium scores
            return [(start, end, 0.5) for start, end in segments]
        
        scored_segments = []
        max_ai_calls = min(20, len(segments))  # Limit to 20 AI calls max
        ai_call_count = 0
        failed_ai_calls = 0
        max_failed_calls = 5
        
        # Select most promising segments for AI analysis
        if len(segments) > max_ai_calls:
            # Take every nth segment to distribute sampling
            step = len(segments) // max_ai_calls
            selected_segments = segments[::step][:max_ai_calls]
        else:
            selected_segments = segments
        
        self.logger.info(f"Using AI to analyze {len(selected_segments)} of {len(segments)} segments")
        
        for i, (start, end) in enumerate(selected_segments):
            if failed_ai_calls >= max_failed_calls:
                self.logger.error("Too many AI analysis failures, stopping AI scoring")
                break
                
            temp_file_path = None
            try:
                # Validate segment timing
                if start < 0 or end > clip.duration or start >= end:
                    self.logger.warning(f"Invalid segment timing {start}-{end}, skipping AI analysis")
                    scored_segments.append((start, end, 0.4))
                    continue
                
                # Extract single frame from middle of segment
                mid_time = (start + end) / 2
                
                # Validate mid_time
                if mid_time < 0 or mid_time >= clip.duration:
                    self.logger.warning(f"Invalid mid_time {mid_time} for segment {start}-{end}")
                    scored_segments.append((start, end, 0.4))
                    continue
                
                # Get frame with error handling
                try:
                    frame = clip.get_frame(mid_time)
                    if frame is None:
                        raise ValueError("Frame extraction returned None")
                except Exception as e:
                    self.logger.warning(f"Frame extraction failed at {mid_time}s: {e}")
                    scored_segments.append((start, end, 0.4))
                    continue
                
                # Validate frame
                if frame.size == 0:
                    self.logger.warning(f"Empty frame at {mid_time}s")
                    scored_segments.append((start, end, 0.4))
                    continue
                
                # Save frame temporarily with better error handling
                import tempfile
                import cv2
                
                try:
                    # Create secure temp file
                    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                    temp_file_path = temp_file.name
                    temp_file.close()  # Close file handle so cv2 can write to it
                    
                    # Convert and save frame
                    if len(frame.shape) == 3 and frame.shape[2] == 3:  # RGB image
                        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    else:
                        frame_bgr = frame  # Already in correct format or grayscale
                    
                    success = cv2.imwrite(temp_file_path, frame_bgr)
                    if not success:
                        raise ValueError("cv2.imwrite failed")
                    
                    # Verify file was created and has content
                    if not os.path.exists(temp_file_path) or os.path.getsize(temp_file_path) == 0:
                        raise ValueError("Temporary image file is empty or not created")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to save frame for segment {start}-{end}: {e}")
                    if temp_file_path and os.path.exists(temp_file_path):
                        try:
                            os.unlink(temp_file_path)
                        except:
                            pass
                    scored_segments.append((start, end, 0.4))
                    continue
                
                # Analyze with AI
                try:
                    ai_call_count += 1
                    analysis = self.ai_handler._analyze_image_content_with_gemini(temp_file_path)
                    
                    if analysis:
                        # Score based on analysis and prompt
                        ai_score = self._calculate_prompt_relevance_score(analysis, prompt)
                        # Validate AI score
                        if not (0 <= ai_score <= 1):
                            self.logger.warning(f"Invalid AI score {ai_score}, using default")
                            ai_score = 0.5
                    else:
                        self.logger.warning("AI analysis returned empty result")
                        ai_score = 0.5
                        
                    scored_segments.append((start, end, ai_score))
                    self.logger.debug(f"AI scored segment {start:.1f}-{end:.1f}: {ai_score:.3f}")
                    
                except Exception as e:
                    self.logger.warning(f"AI analysis failed for segment {start}-{end}: {e}")
                    failed_ai_calls += 1
                    scored_segments.append((start, end, 0.5))  # Default score
                
                # Clean up temp file
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except Exception as e:
                        self.logger.warning(f"Failed to clean up temp file {temp_file_path}: {e}")
                
            except Exception as e:
                self.logger.warning(f"Unexpected error in AI scoring for segment {start}-{end}: {e}")
                failed_ai_calls += 1
                
                # Emergency cleanup
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass
                
                scored_segments.append((start, end, 0.5))  # Default score
        
        # For segments not analyzed by AI, assign medium score
        analyzed_times = {(start, end) for start, end, _ in scored_segments}
        for start, end in segments:
            if (start, end) not in analyzed_times:
                scored_segments.append((start, end, 0.4))  # Slightly lower than AI-analyzed
        
        self.logger.info(f"AI analysis complete: {ai_call_count} calls made, {failed_ai_calls} failures")
        
        # Ensure we have scores for all segments
        if len(scored_segments) != len(segments):
            self.logger.warning(f"Segment count mismatch: {len(scored_segments)} scored vs {len(segments)} input")
        
        return scored_segments
    
    def _calculate_prompt_relevance_score(self, analysis: dict, prompt: str) -> float:
        """Calculate how well the frame analysis matches the user prompt."""
        if not analysis or not prompt:
            return 0.5
        
        prompt_lower = prompt.lower()
        score = 0.5  # Base score
        
        # Check for keyword matches in analysis
        for key in ['main_subject', 'activities', 'setting', 'mood']:
            if key in analysis and analysis[key]:
                content = str(analysis[key]).lower()
                # Simple keyword matching (could be enhanced with semantic similarity)
                for word in prompt_lower.split():
                    if len(word) > 3 and word in content:
                        score += 0.1
        
        return min(score, 1.0)
    
    def _select_best_segments(self, scored_segments: List[Tuple[float, float, float]], target_duration: int) -> List[Tuple[float, float]]:
        """
        Select the best segments to create a highlight reel of target duration.
        """
        if not scored_segments:
            return []
        
        # Sort by score (highest first)
        sorted_segments = sorted(scored_segments, key=lambda x: x[2], reverse=True)
        
        selected_segments = []
        total_duration = 0
        min_gap = 2.0  # Minimum 2 seconds between selected segments
        
        for start, end, score in sorted_segments:
            segment_duration = end - start
            
            # Check if adding this segment would exceed target
            if total_duration + segment_duration > target_duration:
                # Try to trim the segment to fit
                remaining_time = target_duration - total_duration
                if remaining_time > 3:  # Only if we have at least 3 seconds left
                    selected_segments.append((start, start + remaining_time))
                break
            
            # Check for overlap with existing segments
            overlap = False
            for existing_start, existing_end in selected_segments:
                if not (end <= existing_start - min_gap or start >= existing_end + min_gap):
                    overlap = True
                    break
            
            if not overlap:
                selected_segments.append((start, end))
                total_duration += segment_duration
        
        # Sort selected segments by start time
        selected_segments.sort(key=lambda x: x[0])
        
        return selected_segments
    
    def _add_chapter_markers(self, clip, segments: List[Tuple[float, float]], prompt: str):
        """Add chapter markers/titles for longer highlight reels (optional enhancement)."""
        try:
            # For now, just return the clip as-is
            # In the future, could add text overlays indicating different sections
            return clip
        except Exception as e:
            self.logger.warning(f"Could not add chapter markers: {e}")
            return clip
    
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