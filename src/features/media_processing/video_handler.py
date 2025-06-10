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
from moviepy.video.fx import resize
from moviepy.video.fx.crop import crop
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
            
            # NEVER FAIL - always create something
            if not segments:
                self.logger.warning("No highlights found, creating emergency highlights")
                segments = self._create_emergency_highlights(clip, target_duration)
            
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
    
    def generate_example_based_highlight_reel(self, video_path: str, example_data: Dict[str, Any], 
                                            target_duration: int = 30, context_padding: float = 2.0,
                                            prompt: str = "") -> Tuple[bool, str, str]:
        """
        Generate a highlight reel using example segment-based similarity detection.
        
        Args:
            video_path: Path to the source video
            example_data: Dictionary containing example segment data (start_time, end_time, description)
            target_duration: Target duration in seconds (default: 30)
            context_padding: Seconds of context to add before each highlight scene
            prompt: Additional natural language prompt for guidance
            
        Returns:
            Tuple[bool, str, str]: (success, output_path, message)
        """
        try:
            if not os.path.exists(video_path):
                return False, "", f"Video file not found: {video_path}"
                
            if not example_data:
                return False, "", "Example data is required for example-based detection"
            
            # Check if we have a segment or just instructions/description
            has_segment = example_data.get('has_segment', False)
            if not has_segment and not prompt:
                return False, "", "Either example segment (start_time, end_time) or content instructions must be provided"
            
            self.logger.info(f"Generating example-based highlight reel from {video_path}")
            if has_segment:
                self.logger.info(f"Using example segment analysis")
            else:
                self.logger.info(f"Using prompt-based analysis with example context")
            self.logger.info(f"Context padding: {context_padding}s")
            
            # Load video
            clip = VideoFileClip(video_path)
            original_duration = clip.duration
            
            if original_duration <= target_duration:
                self.logger.info("Video is already shorter than target duration")
                return True, video_path, "Video is already the right length"
            
            # Choose analysis method based on available data
            if has_segment:
                # Validate example segment
                start_time = example_data['start_time']
                end_time = example_data['end_time']
                
                if start_time >= end_time:
                    clip.close()
                    return False, "", "Example segment start_time must be less than end_time"
                
                if start_time < 0 or end_time > original_duration:
                    clip.close()
                    return False, "", f"Example segment ({start_time:.1f}s - {end_time:.1f}s) is outside video duration (0 - {original_duration:.1f}s)"
                
                self.logger.info(f"Example segment: {start_time:.1f}s - {end_time:.1f}s")
                
                # Analyze video for similar segments based on example segment
                segments = self._analyze_video_for_segment_similarities(
                    clip, target_duration, example_data, context_padding, prompt
                )
            else:
                # Fall back to traditional prompt-based analysis
                self.logger.info("Using prompt-based analysis (no example segment provided)")
                segments = self._analyze_video_for_highlights(clip, target_duration, prompt)
            
            # NEVER FAIL - always create something
            if not segments:
                self.logger.warning("No similar segments found, creating emergency highlights")
                segments = self._create_emergency_highlights(clip, target_duration)
            
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
                output_filename = f"{base_name}_example_highlight_{timestamp}.mp4"
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
                            video_path, "example_based_highlight_reel", output_path
                        )
                    except Exception as e:
                        self.logger.warning(f"Could not track video processing: {e}")
                
                total_duration = sum(end - start for start, end in segments)
                self.logger.info(f"Example-based highlight reel saved to {output_path}")
                return True, output_path, f"Example-based highlight reel created ({len(segments)} segments, {total_duration:.1f}s total)"
            else:
                clip.close()
                return False, "", "No suitable segments found for highlight reel"
                
        except Exception as e:
            self.logger.exception(f"Error generating example-based highlight reel: {e}")
            return False, "", f"Error generating example-based highlight reel: {str(e)}"
    
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
            
            # Write video with better error handling
            try:
                final_clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    verbose=False,  # Reduce verbosity
                    logger=None  # Disable internal logging that might cause issues
                )
            except Exception as video_write_error:
                self.logger.warning(f"Video writing failed with audio, trying without audio: {video_write_error}")
                try:
                    # Try writing without audio if audio processing fails
                    final_clip_no_audio = final_clip.without_audio()
                    final_clip_no_audio.write_videofile(
                        output_path,
                        codec='libx264',
                        verbose=False,
                        logger=None
                    )
                    final_clip_no_audio.close()
                    self.logger.info("Video saved without audio due to audio processing issues")
                except Exception as final_error:
                    # Clean up and return error
                    self._cleanup_clips(clip, final_clip, highlight_clips)
                    return False, "", f"Failed to write video: {str(final_error)}"
            
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
        Analyze video to find the best segments for highlights with enhanced action detection.
        """
        duration = clip.duration
        
        # Check if this is an action-based prompt regardless of video length
        action_keywords = ['throwing', 'catching', 'running', 'jumping', 'dancing', 'playing', 'kicking', 'hitting', 'shooting',
                          'pokeball', 'pokemon', 'throw', 'catch', 'ball', 'game', 'gaming', 'mobile', 'AR', 'attempt']
        is_action_prompt = any(keyword in prompt.lower() for keyword in action_keywords)
        
        # Use action detection for action prompts or shorter videos
        if is_action_prompt or duration <= 180:  # 3 minutes threshold
            self.logger.info(f"Using enhanced action detection (action_prompt: {is_action_prompt}, duration: {duration:.1f}s)")
            return self._analyze_short_video_highlights(clip, target_duration, prompt)
        else:
            self.logger.info(f"Using standard long video analysis for {duration:.1f}s video")
            return self._analyze_long_video_highlights(clip, target_duration, prompt)
    
    def _analyze_short_video_highlights(self, clip, target_duration: int, prompt: str) -> List[Tuple[float, float]]:
        """
        Enhanced analysis for short videos with action-focused detection.
        """
        duration = clip.duration
        
        # Determine if this is an action-based prompt (expanded for Pokemon/gaming)
        action_keywords = ['throwing', 'catching', 'running', 'jumping', 'dancing', 'playing', 'kicking', 'hitting', 'shooting', 
                          'pokeball', 'pokemon', 'throw', 'catch', 'ball', 'game', 'gaming', 'mobile', 'AR', 'attempt']
        is_action_prompt = any(keyword in prompt.lower() for keyword in action_keywords)
        
        if is_action_prompt:
            # Use shorter, more precise segments for action detection
            segment_length = 2.0  # 2-second segments for actions
            min_segment_gap = 0.5  # Allow closer segments for actions
        else:
            segment_length = 8.0  # Longer segments for non-action content
            min_segment_gap = 2.0
        
        # Generate shorter segments
        segments = []
        current_time = 0
        while current_time + segment_length <= duration:
            segments.append((current_time, current_time + segment_length))
            current_time += segment_length * 0.7  # 30% overlap for better coverage
        
        # Add final segment if there's remaining content
        if current_time < duration and duration - current_time > 1.0:
            segments.append((current_time, duration))
        
        self.logger.info(f"Generated {len(segments)} segments for analysis (action prompt: {is_action_prompt})")
        
        if is_action_prompt:
            # Use enhanced action detection pipeline
            return self._analyze_action_segments(clip, segments, target_duration, prompt)
        else:
            # Use standard analysis
            scored_segments = self._score_segments_with_ai(clip, segments, prompt)
            return self._select_best_segments(scored_segments, target_duration)
    
    def _analyze_long_video_highlights(self, clip, target_duration: int, prompt: str) -> List[Tuple[float, float]]:
        """
        Analysis for long videos (>3 minutes) with cost optimization.
        """
        duration = clip.duration
        
        # For long videos, use larger segments to reduce AI API calls
        segment_length = 15.0  # 15-second segments for long videos
        segments = []
        current_time = 0
        
        while current_time + segment_length <= duration:
            segments.append((current_time, current_time + segment_length))
            current_time += segment_length * 0.8  # 20% overlap
        
        # Add final segment if there's remaining content
        if current_time < duration and duration - current_time > 3.0:
            segments.append((current_time, duration))
        
        self.logger.info(f"Generated {len(segments)} long video segments for analysis")
        
        # Use standard scoring for long videos (cost-optimized)
        scored_segments = self._score_segments_with_ai(clip, segments, prompt, max_segments=10)
        return self._select_best_segments(scored_segments, target_duration)
    
    def _analyze_action_segments(self, clip, segments: List[Tuple[float, float]], target_duration: int, prompt: str) -> List[Tuple[float, float]]:
        """
        Enhanced pipeline for sequence-aware action analysis with context inclusion.
        """
        # Step 1: Pre-filter segments using computer vision (free motion detection)
        self.logger.info("Pre-filtering segments with motion detection...")
        motion_filtered_segments = self._prefilter_segments_by_motion(clip, segments)
        
        # Step 2: Multi-frame analysis to identify action sequences
        self.logger.info(f"Analyzing {len(motion_filtered_segments)} motion-filtered segments for action sequences...")
        scored_segments = self._score_action_segments_with_ai(clip, motion_filtered_segments, prompt)
        
        # Step 3: Detect action sequences and expand with context
        self.logger.info("Detecting action sequences and expanding with context...")
        sequence_segments = self._detect_and_expand_action_sequences(clip, scored_segments, target_duration)
        
        # Step 4: Ensure temporal distribution across video if we have multiple sequences
        self.logger.info("Ensuring temporal distribution across video timeline...")
        distributed_segments = self._ensure_temporal_distribution(sequence_segments, clip.duration)
        
        # Step 5: Context-aware selection
        final_segments = self._select_sequence_segments(distributed_segments, target_duration)
        
        # Emergency fallback: if no segments selected, force some highlights
        if not final_segments:
            self.logger.warning("No segments selected, creating emergency highlights")
            final_segments = self._create_emergency_highlights(clip, target_duration)
        
        return final_segments
    
    def _prefilter_segments_by_motion(self, clip, segments: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Pre-filter segments using computer vision motion detection (no AI cost).
        """
        motion_segments = []
        
        for start, end in segments:
            try:
                # Extract 3 frames from the segment
                frame_times = [start + 0.2, (start + end) / 2, end - 0.2]
                frames = []
                
                for t in frame_times:
                    if 0 <= t < clip.duration:
                        frame = clip.get_frame(t)
                        if frame is not None:
                            frames.append(frame)
                
                if len(frames) >= 2:
                    # Calculate motion between frames using optical flow
                    motion_score = self._calculate_frame_motion(frames)
                    
                    # More permissive threshold for motion filtering
                    if motion_score > 0.15:  # Keep more segments with any reasonable motion
                        motion_segments.append((start, end, motion_score))
                        self.logger.debug(f"Segment {start:.1f}-{end:.1f} motion score: {motion_score:.3f}")
                
            except Exception as e:
                self.logger.warning(f"Motion analysis failed for segment {start}-{end}: {e}")
                # Include segment if motion analysis fails (safe fallback)
                motion_segments.append((start, end, 0.5))
        
        # Sort by motion score and keep top candidates
        motion_segments.sort(key=lambda x: x[2], reverse=True)
        
        # Keep more segments but still control costs - be more permissive
        max_segments = min(15, max(8, len(motion_segments) // 2))  # Keep more segments to increase success rate
        selected_segments = [(start, end) for start, end, _ in motion_segments[:max_segments]]
        
        self.logger.info(f"Motion filtering: {len(segments)} to {len(selected_segments)} segments")
        return selected_segments
    
    def _calculate_frame_motion(self, frames: List[np.ndarray]) -> float:
        """
        Calculate motion between frames using frame differencing.
        """
        if len(frames) < 2:
            return 0.0
        
        try:
            # Convert frames to grayscale for motion calculation
            gray_frames = []
            for frame in frames:
                if len(frame.shape) == 3:
                    # Convert RGB to grayscale
                    gray = np.dot(frame[...,:3], [0.299, 0.587, 0.114])
                else:
                    gray = frame
                gray_frames.append(gray.astype(np.float32))
            
            # Calculate motion as average frame difference
            motion_scores = []
            for i in range(len(gray_frames) - 1):
                diff = np.abs(gray_frames[i+1] - gray_frames[i])
                motion_score = np.mean(diff) / 255.0  # Normalize to 0-1
                motion_scores.append(motion_score)
            
            # Return average motion score
            return np.mean(motion_scores) if motion_scores else 0.0
            
        except Exception as e:
            self.logger.debug(f"Error calculating frame motion: {e}")
            return 0.0
    
    def _calculate_simple_motion(self, frames: List) -> float:
        """
        Fallback motion calculation using simple frame difference.
        """
        if len(frames) < 2:
            return 0.0
            
        try:
            # Simple frame difference calculation
            total_diff = 0
            for i in range(len(frames) - 1):
                # Convert frames to grayscale if needed
                frame1 = frames[i]
                frame2 = frames[i + 1]
                
                if len(frame1.shape) == 3:
                    frame1 = np.mean(frame1, axis=2)
                if len(frame2.shape) == 3:
                    frame2 = np.mean(frame2, axis=2)
                
                # Calculate difference
                diff = np.mean(np.abs(frame1.astype(float) - frame2.astype(float)))
                total_diff += diff
            
            return total_diff / (len(frames) - 1) / 255.0  # Normalize
            
        except Exception as e:
            self.logger.debug(f"Error in simple motion calculation: {e}")
            return 0.0
            else:
                # Fall back to traditional prompt-based analysis
                self.logger.info("Using prompt-based analysis (no example segment provided)")
                segments = self._analyze_video_for_highlights(clip, target_duration, prompt)
            
            # NEVER FAIL - always create something
            if not segments:
                self.logger.warning("No similar segments found, creating emergency highlights")
                segments = self._create_emergency_highlights(clip, target_duration)
            
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
                output_filename = f"{base_name}_example_highlight_{timestamp}.mp4"
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
                            video_path, "example_based_highlight_reel", output_path
                        )
                    except Exception as e:
                        self.logger.warning(f"Could not track video processing: {e}")
                
                total_duration = sum(end - start for start, end in segments)
                self.logger.info(f"Example-based highlight reel saved to {output_path}")
                return True, output_path, f"Example-based highlight reel created ({len(segments)} segments, {total_duration:.1f}s total)"
            else:
                clip.close()
                return False, "", "No suitable segments found for highlight reel"
                
        except Exception as e:
            self.logger.exception(f"Error generating example-based highlight reel: {e}")
            return False, "", f"Error generating example-based highlight reel: {str(e)}"
    
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
            
            # Write video with better error handling
            try:
                final_clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    verbose=False,  # Reduce verbosity
                    logger=None  # Disable internal logging that might cause issues
                )
            except Exception as video_write_error:
                self.logger.warning(f"Video writing failed with audio, trying without audio: {video_write_error}")
                try:
                    # Try writing without audio if audio processing fails
                    final_clip_no_audio = final_clip.without_audio()
                    final_clip_no_audio.write_videofile(
                        output_path,
                        codec='libx264',
                        verbose=False,
                        logger=None
                    )
                    final_clip_no_audio.close()
                    self.logger.info("Video saved without audio due to audio processing issues")
                except Exception as final_error:
                    # Clean up and return error
                    self._cleanup_clips(clip, final_clip, highlight_clips)
                    return False, "", f"Failed to write video: {str(final_error)}"
            
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
        Analyze video to find the best segments for highlights with enhanced action detection.
        """
        duration = clip.duration
        
        # Check if this is an action-based prompt regardless of video length
        action_keywords = ['throwing', 'catching', 'running', 'jumping', 'dancing', 'playing', 'kicking', 'hitting', 'shooting',
                          'pokeball', 'pokemon', 'throw', 'catch', 'ball', 'game', 'gaming', 'mobile', 'AR', 'attempt']
        is_action_prompt = any(keyword in prompt.lower() for keyword in action_keywords)
        
        # Use action detection for action prompts or shorter videos
        if is_action_prompt or duration <= 180:  # 3 minutes threshold
            self.logger.info(f"Using enhanced action detection (action_prompt: {is_action_prompt}, duration: {duration:.1f}s)")
            return self._analyze_short_video_highlights(clip, target_duration, prompt)
        else:
            self.logger.info(f"Using standard long video analysis for {duration:.1f}s video")
            return self._analyze_long_video_highlights(clip, target_duration, prompt)
    
    def _analyze_short_video_highlights(self, clip, target_duration: int, prompt: str) -> List[Tuple[float, float]]:
        """
        Enhanced analysis for short videos with action-focused detection.
        """
        duration = clip.duration
        
        # Determine if this is an action-based prompt (expanded for Pokemon/gaming)
        action_keywords = ['throwing', 'catching', 'running', 'jumping', 'dancing', 'playing', 'kicking', 'hitting', 'shooting', 
                          'pokeball', 'pokemon', 'throw', 'catch', 'ball', 'game', 'gaming', 'mobile', 'AR', 'attempt']
        is_action_prompt = any(keyword in prompt.lower() for keyword in action_keywords)
        
        if is_action_prompt:
            # Use shorter, more precise segments for action detection
            segment_length = 2.0  # 2-second segments for actions
            min_segment_gap = 0.5  # Allow closer segments for actions
        else:
            segment_length = 8.0  # Longer segments for non-action content
            min_segment_gap = 2.0
        
        # Generate shorter segments
        segments = []
        current_time = 0
        while current_time + segment_length <= duration:
            segments.append((current_time, current_time + segment_length))
            current_time += segment_length * 0.7  # 30% overlap for better coverage
        
        # Add final segment if there's remaining content
        if current_time < duration and duration - current_time > 1.0:
            segments.append((current_time, duration))
        
        self.logger.info(f"Generated {len(segments)} segments for analysis (action prompt: {is_action_prompt})")
        
        if is_action_prompt:
            # Use enhanced action detection pipeline
            return self._analyze_action_segments(clip, segments, target_duration, prompt)
        else:
            # Use standard analysis
            scored_segments = self._score_segments_with_ai(clip, segments, prompt)
            return self._select_best_segments(scored_segments, target_duration)
    
    def _analyze_long_video_highlights(self, clip, target_duration: int, prompt: str) -> List[Tuple[float, float]]:
        """
        Analysis for long videos (>3 minutes) with cost optimization.
        """
        duration = clip.duration
        
        # For long videos, use larger segments to reduce AI API calls
        segment_length = 15.0  # 15-second segments for long videos
        segments = []
        current_time = 0
        
        while current_time + segment_length <= duration:
            segments.append((current_time, current_time + segment_length))
            current_time += segment_length * 0.8  # 20% overlap
        
        # Add final segment if there's remaining content
        if current_time < duration and duration - current_time > 3.0:
            segments.append((current_time, duration))
        
        self.logger.info(f"Generated {len(segments)} long video segments for analysis")
        
        # Use standard scoring for long videos (cost-optimized)
        scored_segments = self._score_segments_with_ai(clip, segments, prompt, max_segments=10)
        return self._select_best_segments(scored_segments, target_duration)
    
    def _analyze_action_segments(self, clip, segments: List[Tuple[float, float]], target_duration: int, prompt: str) -> List[Tuple[float, float]]:
        """
        Enhanced pipeline for sequence-aware action analysis with context inclusion.
        """
        # Step 1: Pre-filter segments using computer vision (free motion detection)
        self.logger.info("Pre-filtering segments with motion detection...")
        motion_filtered_segments = self._prefilter_segments_by_motion(clip, segments)
        
        # Step 2: Multi-frame analysis to identify action sequences
        self.logger.info(f"Analyzing {len(motion_filtered_segments)} motion-filtered segments for action sequences...")
        scored_segments = self._score_action_segments_with_ai(clip, motion_filtered_segments, prompt)
        
        # Step 3: Detect action sequences and expand with context
        self.logger.info("Detecting action sequences and expanding with context...")
        sequence_segments = self._detect_and_expand_action_sequences(clip, scored_segments, target_duration)
        
        # Step 4: Ensure temporal distribution across video if we have multiple sequences
        self.logger.info("Ensuring temporal distribution across video timeline...")
        distributed_segments = self._ensure_temporal_distribution(sequence_segments, clip.duration)
        
        # Step 5: Context-aware selection
        final_segments = self._select_sequence_segments(distributed_segments, target_duration)
        
        # Emergency fallback: if no segments selected, force some highlights
        if not final_segments:
            self.logger.warning("No segments selected, creating emergency highlights")
            final_segments = self._create_emergency_highlights(clip, target_duration)
        
        return final_segments
    
    def _prefilter_segments_by_motion(self, clip, segments: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Pre-filter segments using computer vision motion detection (no AI cost).
        """
        motion_segments = []
        
        for start, end in segments:
            try:
                # Extract 3 frames from the segment
                frame_times = [start + 0.2, (start + end) / 2, end - 0.2]
                frames = []
                
                for t in frame_times:
                    if 0 <= t < clip.duration:
                        frame = clip.get_frame(t)
                        if frame is not None:
                            frames.append(frame)
                
                if len(frames) >= 2:
                    # Calculate motion between frames using optical flow
                    motion_score = self._calculate_frame_motion(frames)
                    
                    # More permissive threshold for motion filtering
                    if motion_score > 0.15:  # Keep more segments with any reasonable motion
                        motion_segments.append((start, end, motion_score))
                        self.logger.debug(f"Segment {start:.1f}-{end:.1f} motion score: {motion_score:.3f}")
                
            except Exception as e:
                self.logger.warning(f"Motion analysis failed for segment {start}-{end}: {e}")
                # Include segment if motion analysis fails (safe fallback)
                motion_segments.append((start, end, 0.5))
        
        # Sort by motion score and keep top candidates
        motion_segments.sort(key=lambda x: x[2], reverse=True)
        
        # Keep more segments but still control costs - be more permissive
        max_segments = min(15, max(8, len(motion_segments) // 2))  # Keep more segments to increase success rate
        selected_segments = [(start, end) for start, end, _ in motion_segments[:max_segments]]
        
        self.logger.info(f"Motion filtering: {len(segments)} to {len(selected_segments)} segments")
        return selected_segments
    
    def _calculate_frame_motion(self, frames: List) -> float:
        """
        Calculate motion between consecutive frames using optical flow.
        """
        try:
            import cv2
            import numpy as np
            
            if len(frames) < 2:
                return 0.0
            
            total_motion = 0.0
            comparisons = 0
            
            for i in range(len(frames) - 1):
                # Convert frames to grayscale
                gray1 = cv2.cvtColor(frames[i], cv2.COLOR_RGB2GRAY)
                gray2 = cv2.cvtColor(frames[i + 1], cv2.COLOR_RGB2GRAY)
                
                # Calculate optical flow
                flow = cv2.calcOpticalFlowPyrLK(
                    gray1, gray2, 
                    np.array([[x, y] for y in range(0, gray1.shape[0], 20) 
                             for x in range(0, gray1.shape[1], 20)], dtype=np.float32),
                    None
                )[0]
                
                if flow is not None and len(flow) > 0:
                    # Calculate magnitude of motion vectors
                    motion_magnitude = np.mean(np.sqrt(np.sum(flow**2, axis=1)))
                    total_motion += motion_magnitude
                    comparisons += 1
            
            return total_motion / comparisons if comparisons > 0 else 0.0
            
        except Exception as e:
            self.logger.debug(f"Optical flow calculation failed: {e}")
            # Fallback: simple frame difference
            return self._calculate_simple_motion(frames)
    
    def _calculate_simple_motion(self, frames: List) -> float:
        """
        Fallback motion calculation using simple frame difference.
        """
        try:
            import cv2
            import numpy as np
            
            if len(frames) < 2:
                return 0.0
            
            total_diff = 0.0
            comparisons = 0
            
            for i in range(len(frames) - 1):
                # Convert to grayscale and calculate difference
                gray1 = cv2.cvtColor(frames[i], cv2.COLOR_RGB2GRAY)
                gray2 = cv2.cvtColor(frames[i + 1], cv2.COLOR_RGB2GRAY)
                
                diff = cv2.absdiff(gray1, gray2)
                motion_score = np.mean(diff) / 255.0
                total_diff += motion_score
                comparisons += 1
            
            return total_diff / comparisons if comparisons > 0 else 0.0
            
        except Exception:
            return 0.5  # Default fallback score
    
    def _score_action_segments_with_ai(self, clip, segments: List[Tuple[float, float]], prompt: str) -> List[Tuple[float, float, float]]:
        """
        Enhanced AI scoring with better fallback handling.
        """
        if not segments:
            return []
        
        scored_segments = []
        ai_call_count = 0
        failed_ai_calls = 0
        max_failed_calls = 5  # More tolerant of failures
        
        self.logger.info(f"Analyzing {len(segments)} segments with AI analysis (max failures: {max_failed_calls})")
        
        for start, end in segments:
            if failed_ai_calls >= max_failed_calls:
                self.logger.warning("Too many AI failures, using motion-based scoring for remaining segments")
                # Use enhanced motion scoring as fallback
                motion_score = self._analyze_segment_motion_enhanced(clip, start, end)
                scored_segments.append((start, end, motion_score))
                continue
            
            try:
                # Try to get AI analysis for the middle frame
                frame_time = (start + end) / 2
                
                if 0 <= frame_time < clip.duration:
                    ai_score = self._analyze_action_frame(clip, frame_time, prompt)
                    
                    if ai_score is not None:
                        ai_call_count += 1
                        scored_segments.append((start, end, ai_score))
                        self.logger.debug(f"AI scored segment {start:.1f}-{end:.1f}s: {ai_score:.3f}")
                    else:
                        failed_ai_calls += 1
                        # Fallback to motion analysis
                        motion_score = self._analyze_segment_motion_enhanced(clip, start, end)
                        scored_segments.append((start, end, motion_score))
                        self.logger.debug(f"AI failed, motion scored segment {start:.1f}-{end:.1f}s: {motion_score:.3f}")
                else:
                    # Frame time out of bounds
                    failed_ai_calls += 1
                    motion_score = self._analyze_segment_motion_enhanced(clip, start, end)
                    scored_segments.append((start, end, motion_score))
                
            except Exception as e:
                self.logger.debug(f"Segment analysis failed for {start}-{end}: {e}")
                failed_ai_calls += 1
                # Fallback to motion analysis
                motion_score = self._analyze_segment_motion_enhanced(clip, start, end)
                scored_segments.append((start, end, motion_score))
        
        self.logger.info(f"Action AI analysis: {ai_call_count} successful analyses, {failed_ai_calls} failures")
        
        # If we got no AI results at all, log a warning
        if ai_call_count == 0:
            self.logger.warning("No AI analysis succeeded - check API configuration and connectivity")
        
        return scored_segments
    
    def _analyze_action_frame(self, clip, frame_time: float, prompt: str) -> Optional[float]:
        """
        Analyze a single frame for action content with action-specific prompting.
        """
        temp_file_path = None
        try:
            # Extract frame
            frame = clip.get_frame(frame_time)
            if frame is None or frame.size == 0:
                return None
            
            # Save frame temporarily
            import tempfile
            import cv2
            
            temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Convert and save
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                frame_bgr = frame
            
            if not cv2.imwrite(temp_file_path, frame_bgr):
                return None
            
            # Analyze with action-specific AI
            analysis = self._analyze_frame_for_action(temp_file_path, prompt)
            
            if analysis:
                return self._calculate_action_relevance_score(analysis, prompt)
            else:
                return None
                
        except Exception as e:
            self.logger.debug(f"Frame analysis failed at {frame_time}s: {e}")
            return None
        finally:
            # Cleanup
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
    
    def _analyze_frame_for_action(self, image_path: str, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Analyze frame specifically for action content with focused prompting.
        """
        try:
            # Create a specialized prompt that includes the user's specific request
            enhanced_prompt = f"""
            Analyze this image looking specifically for: "{prompt}"
            
            Focus on detecting Pokemon Go gameplay sequences. Be EXTREMELY DETAILED in your sequence analysis:
            
            PRIMARY FOCUS - Pokemon Go Sequence Detection:
            1. SETUP/AIMING PHASE: Look for targeting circles, crosshairs, aiming interfaces, user focusing on screen
            2. THROWING MOTION: Look for arm extension, hand gestures indicating throwing, releasing motion, forward arm movement (typically 1-3 seconds)
            3. POKEBALL FLIGHT: Look for ball/sphere objects moving across screen, projectile motion
            4. IMPACT/OUTCOME PHASE: Look for pokeball shaking, stars appearing, "Pokemon caught" messages, or Pokemon escaping
            5. SUCCESS INDICATORS: Stars popping out of pokeball, success messages, celebratory gestures
            6. FAILURE INDICATORS: Pokemon hopping out of pokeball, disappointed reactions, retry attempts
            
            DETAILED ANALYSIS:
            1. Main subject matter - Describe every person, object, and character visible with extreme detail
            2. Setting/environment - Indoor/outdoor, gaming setup, room details, background elements
            3. Actions and movements - Describe EVERY gesture, movement, and action in detail, especially arm/hand movements
            4. Objects present - List ALL visible items, focusing on round objects, gaming equipment, devices, toys
            5. Body language and posture - Describe exact positioning of arms, hands, body stance, facial expressions
            6. Movement indicators - Any signs of motion blur, action, dynamic activity, throwing trajectories
            7. Gaming elements - Screens, interfaces, gaming setups, Pokemon-related visuals
            8. Emotional state - Excitement, concentration, disappointment, celebration
            9. Success/failure evidence - Visual cues indicating whether actions succeeded or failed
            
            Rate how well this image fits into a Pokemon Go gameplay sequence on a scale of 1-10, where:
            - 10 = Shows clear sequence element (aiming target, throwing motion, pokeball shaking, success/failure outcome)
            - 8-9 = Strong sequence indicators (gaming interface, Pokemon on screen, throwing gesture, outcome messages)
            - 6-7 = Some sequence elements (mobile gaming, potential throwing setup, Pokemon-related content)
            - 4-5 = Minimal gaming content or unclear sequence relevance
            - 1-3 = No Pokemon Go or sequence-related content
            
            SEQUENCE CONTEXT: Consider if this frame likely comes before, during, or after a pokeball throwing sequence.
            
            Format your response as a JSON with these keys: main_subject, setting, activities, objects, body_language, movement_indicators, mood, themes, distinctive_elements, gaming_elements, success_failure_indicators, prompt_match_score, reasoning
            """
            
            # Use enhanced AI analysis
            analysis = self._call_enhanced_ai_analysis(image_path, enhanced_prompt)
            
            if not analysis:
                return None
            
            # Add action-specific scoring context
            analysis['action_prompt'] = prompt.lower()
            analysis['user_request'] = prompt
            return analysis
            
        except Exception as e:
            self.logger.debug(f"AI action analysis failed: {e}")
            return None
    
    def _call_enhanced_ai_analysis(self, image_path: str, enhanced_prompt: str) -> Optional[Dict[str, Any]]:
        """Call AI with enhanced prompt and better error handling."""
        try:
            # Check if AI handler is available and working
            if not self.ai_handler:
                self.logger.debug("AI handler not available")
                return None
            
            # Use the existing AI handler method if available
            if hasattr(self.ai_handler, '_analyze_image_content_with_gemini'):
                # Use the existing method with our enhanced prompt
                try:
                    result = self.ai_handler._analyze_image_content_with_gemini(image_path, enhanced_prompt)
                    if result and isinstance(result, dict):
                        return result
                except Exception as e:
                    self.logger.debug(f"Existing AI method failed: {e}")
            
            # Fallback: Try direct Gemini call if configured
            try:
                # Try multiple ways to get the API key
                GEMINI_API_KEY = None
                
                # Method 1: From config file
                try:
                    from ...config.api_keys import GEMINI_API_KEY
                except ImportError:
                    pass
                
                # Method 2: From environment variables
                if not GEMINI_API_KEY:
                    import os
                    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
                
                # Method 3: From auth handler
                if not GEMINI_API_KEY:
                    try:
                        from ...features.authentication.auth_handler import AuthHandler
                        auth_handler = AuthHandler()
                        GEMINI_API_KEY = auth_handler.get_gemini_api_key()
                    except Exception:
                        pass
                
                if not GEMINI_API_KEY:
                    self.logger.debug("No Gemini API key available from any source")
                    return None
                
                import google.generativeai as genai
                import base64
                import json
                import re
                
                # Configure Gemini
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Read and encode image
                with open(image_path, "rb") as img_file:
                    image_data = img_file.read()
                
                # Create simplified prompt for better parsing
                simple_prompt = f"""
                Analyze this image for Pokemon Go gameplay elements. Look for:
                1. Throwing motions (arm movements, gestures)
                2. Pokeball objects or spherical items
                3. Gaming interfaces or screens
                4. Success/failure indicators
                
                Rate relevance to Pokemon Go action from 1-10.
                
                Respond with JSON: {{"score": number, "description": "brief description", "has_action": boolean}}
                """
                
                # Generate response
                response = model.generate_content([simple_prompt, {"mime_type": "image/jpeg", "data": base64.b64encode(image_data).decode()}])
                
                if not response or not response.text:
                    return None
                
                # Try to parse JSON response
                response_text = response.text.strip()
                
                # Look for JSON in response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        # Normalize the result
                        normalized_result = {
                            "prompt_match_score": result.get("score", 5),
                            "content_description": result.get("description", ""),
                            "has_action": result.get("has_action", False),
                            "main_subject": result.get("description", ""),
                            "reasoning": "Direct Gemini analysis"
                        }
                        return normalized_result
                    except json.JSONDecodeError:
                        pass
                
                # Fallback: Create result from text
                score = 5  # Default score
                score_match = re.search(r'(?:score|rating).*?(\d+)', response_text, re.IGNORECASE)
                if score_match:
                    score = int(score_match.group(1))
                
                return {
                    "prompt_match_score": score,
                    "content_description": response_text[:200],
                    "main_subject": "AI analysis",
                    "reasoning": "Parsed from text response"
                }
                
            except ImportError:
                self.logger.debug("Google Generative AI not available")
                return None
            except Exception as e:
                self.logger.debug(f"Direct Gemini call failed: {e}")
                return None
            
        except Exception as e:
            self.logger.debug(f"Enhanced AI analysis failed: {e}")
            return None
    
    def _calculate_action_relevance_score(self, analysis: dict, prompt: str) -> float:
        """
        Calculate relevance score specifically optimized for action detection with AI prompt matching.
        """
        if not analysis or not prompt:
            return 0.4
        
        prompt_lower = prompt.lower()
        score = 0.2  # Lower base score, more room for action-based improvements
        
        # 1. Use AI's direct prompt match score if available (most important)
        if 'prompt_match_score' in analysis and analysis['prompt_match_score']:
            try:
                ai_match_score = float(analysis['prompt_match_score']) / 10.0  # Convert 1-10 to 0-1
                score += ai_match_score * 0.6  # Heavy weight for AI's direct assessment
                
                # Debug logging for AI's assessment
                reasoning = analysis.get('reasoning', 'No reasoning provided')
                self.logger.info(f"AI prompt match: {analysis['prompt_match_score']}/10 for '{prompt}' - {reasoning}")
                
            except (ValueError, TypeError):
                pass
        
        # Combine all analysis text for additional scoring
        analysis_text = ""
        for key in ['main_subject', 'activities', 'setting', 'objects', 'body_language', 'movement_indicators', 'mood', 'themes', 'distinctive_elements', 'gaming_elements', 'success_failure_indicators', 'content_description']:
            if key in analysis and analysis[key]:
                if isinstance(analysis[key], list):
                    analysis_text += " " + " ".join(str(item) for item in analysis[key])
                else:
                    analysis_text += " " + str(analysis[key])
        
        analysis_text = analysis_text.lower()
        
        # 2. Direct word matches (medium weight)
        prompt_words = prompt_lower.split()
        matched_words = 0
        for word in prompt_words:
            if len(word) > 2 and word in analysis_text:
                matched_words += 1
                score += 0.15
        
        # 3. Action-specific semantic matching (lower weight since AI score is primary)
        action_semantic_score = self._calculate_action_semantic_score(prompt_lower, analysis_text)
        score += action_semantic_score * 0.15
        
        # Debug logging for transparency
        if score > 0.7:
            activities = analysis.get('activities', 'N/A')
            objects = analysis.get('objects', 'N/A')
            self.logger.info(f"High relevance score {score:.3f}: Activities='{activities}', Objects='{objects}'")
        
        return min(score, 1.0)
    
    def _calculate_action_semantic_score(self, prompt: str, analysis_text: str) -> float:
        """
        Enhanced semantic scoring specifically for actions.
        """
        # Sequence-aware semantic mappings with Pokemon Go gameplay focus
        action_mappings = {
            'throwing': ['toss', 'launch', 'hurl', 'pitch', 'cast', 'release', 'motion', 'arm movement', 'gesture', 'forward motion', 'extending', 'reaching', 'arm extension', 'throwing motion'],
            'catching': ['grab', 'grasp', 'receive', 'snatch', 'hold', 'grasping', 'hands', 'arms extended', 'grabbing', 'reaching', 'catch attempt'],
            'pokeball': ['ball', 'sphere', 'round object', 'gaming', 'toy', 'pokemon', 'circular', 'object', 'pokeball', 'poke ball', 'device', 'gaming device', 'projectile', 'flying object'],
            'pokemon': ['game', 'gaming', 'character', 'anime', 'creature', 'trainer', 'pokemon go', 'mobile game', 'augmented reality', 'AR', 'interface', 'screen'],
            'aiming': ['target', 'crosshair', 'circle', 'aiming', 'targeting', 'focus', 'concentration', 'preparing', 'setup', 'getting ready'],
            'success': ['celebration', 'victory', 'happy', 'excited', 'success', 'caught', 'successful', 'joy', 'celebration gesture', 'fist pump', 'smile', 'stars', 'sparkles', 'caught message'],
            'failure': ['disappointment', 'frustrated', 'missed', 'failed', 'failure', 'sad', 'disappointed', 'upset', 'missed catch', 'escaped', 'hopping out', 'broke free'],
            'sequence': ['shaking', 'wiggling', 'moving', 'animation', 'effect', 'transition', 'outcome', 'result', 'impact'],
            'interface': ['screen', 'mobile', 'phone', 'app', 'UI', 'interface', 'menu', 'buttons', 'gaming interface'],
            'running': ['jogging', 'sprint', 'moving quickly', 'exercise', 'athletic', 'legs', 'movement', 'motion'],
            'jumping': ['leap', 'hop', 'bounce', 'athletic movement', 'airborne', 'legs'],
            'playing': ['gaming', 'entertainment', 'recreational', 'fun activity', 'interactive', 'mobile gaming', 'AR gaming'],
            'kicking': ['foot', 'leg', 'soccer', 'football', 'ball', 'striking'],
            'hitting': ['striking', 'contact', 'impact', 'swing', 'bat', 'racket'],
        }
        
        matches = 0.0
        prompt_words = prompt.split()
        
        for word in prompt_words:
            if word in action_mappings:
                for related_word in action_mappings[word]:
                    if related_word in analysis_text:
                        matches += 0.6  # Higher weight for action-related semantic matches
                        break
        
        return matches
    
    def _select_action_segments(self, scored_segments: List[Tuple[float, float, float]], target_duration: int) -> List[Tuple[float, float]]:
        """
        Select best action segments with action-first prioritization.
        """
        if not scored_segments:
            return []
        
        # Sort by score (highest first) - action scores should be much higher
        sorted_segments = sorted(scored_segments, key=lambda x: x[2], reverse=True)
        
        # Log top scores for debugging
        if sorted_segments:
            top_5 = sorted_segments[:5]
            self.logger.info(f"Top action scores: {[(f'{start:.1f}-{end:.1f}', f'{score:.3f}') for start, end, score in top_5]}")
        
        selected_segments = []
        total_duration = 0
        min_gap = 1.0  # Shorter gap for actions
        
        for start, end, score in sorted_segments:
            segment_duration = end - start
            
            # For actions, prioritize high-scoring segments even if they exceed target slightly
            if total_duration + segment_duration > target_duration:
                remaining_time = target_duration - total_duration
                # Be more flexible with action segments
                if remaining_time > 1.5 and score > 0.7:  # Keep high-scoring action segments
                    selected_segments.append((start, start + remaining_time))
                break
            
            # Check for overlap (more permissive for high-scoring actions)
            overlap = False
            for existing_start, existing_end in selected_segments:
                if not (end <= existing_start - min_gap or start >= existing_end + min_gap):
                    # Allow some overlap for very high-scoring action segments
                    if score < 0.8:
                        overlap = True
                    break
            
            if not overlap:
                selected_segments.append((start, end))
                total_duration += segment_duration
                
                # Stop early if we have enough high-quality action content
                if total_duration >= target_duration * 0.8 and score > 0.7:
                    break
        
        # Sort by start time
        selected_segments.sort(key=lambda x: x[0])
        
        self.logger.info(f"Selected {len(selected_segments)} action segments, total duration: {sum(end-start for start, end in selected_segments):.1f}s")
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

    def _cleanup_clips(self, main_clip, final_clip, highlight_clips):
        """Safely clean up video clips to prevent memory leaks."""
        try:
            if main_clip:
                main_clip.close()
        except Exception as e:
            self.logger.debug(f"Error closing main clip: {e}")
        
        try:
            if final_clip:
                final_clip.close()
        except Exception as e:
            self.logger.debug(f"Error closing final clip: {e}")
        
        for clip in highlight_clips:
            try:
                if clip:
                    clip.close()
            except Exception as e:
                self.logger.debug(f"Error closing highlight clip: {e}")

    def _score_segments_with_ai(self, clip, segments: List[Tuple[float, float]], prompt: str, max_segments: int = 15) -> List[Tuple[float, float, float]]:
        """
        Standard AI scoring for video segments (cost-optimized for longer videos).
        """
        if not segments:
            return []
        
        # Limit segments for cost control
        if len(segments) > max_segments:
            # Take evenly distributed segments
            step = len(segments) // max_segments
            segments = segments[::step][:max_segments]
            self.logger.info(f"Limited to {len(segments)} segments for cost optimization")
        
        # Check if AI handler is available
        if not self.ai_handler or not hasattr(self.ai_handler, '_analyze_image_content_with_gemini'):
            self.logger.warning("AI handler not available, using default scoring")
            return [(start, end, 0.5) for start, end in segments]
        
        scored_segments = []
        ai_call_count = 0
        failed_ai_calls = 0
        max_failed_calls = 5
        
        self.logger.info(f"Analyzing {len(segments)} segments with standard AI analysis")
        
        for start, end in segments:
            if failed_ai_calls >= max_failed_calls:
                self.logger.warning("Too many AI failures, using default scoring for remaining segments")
                scored_segments.append((start, end, 0.4))
                continue
            
            try:
                # Single frame analysis for standard scoring (cost-effective)
                frame_time = (start + end) / 2  # Middle of segment
                score = self._analyze_standard_frame(clip, frame_time, prompt)
                
                if score is not None:
                    scored_segments.append((start, end, score))
                    ai_call_count += 1
                else:
                    scored_segments.append((start, end, 0.3))
                    failed_ai_calls += 1
                
            except Exception as e:
                self.logger.warning(f"Standard analysis failed for segment {start}-{end}: {e}")
                failed_ai_calls += 1
                scored_segments.append((start, end, 0.3))
        
        self.logger.info(f"Standard AI analysis: {ai_call_count} frame analyses, {failed_ai_calls} failures")
        return scored_segments

    def _analyze_standard_frame(self, clip, frame_time: float, prompt: str) -> Optional[float]:
        """
        Analyze a single frame for standard content matching.
        """
        temp_file_path = None
        try:
            # Extract frame
            frame = clip.get_frame(frame_time)
            if frame is None or frame.size == 0:
                return None
            
            # Save frame temporarily
            import tempfile
            import cv2
            
            temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Convert and save
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                frame_bgr = frame
            
            if not cv2.imwrite(temp_file_path, frame_bgr):
                return None
            
            # Analyze with standard AI
            analysis = self._analyze_frame_for_standard(temp_file_path, prompt)
            
            if analysis:
                return self._calculate_standard_relevance_score(analysis, prompt)
            else:
                return None
                
        except Exception as e:
            self.logger.debug(f"Standard frame analysis failed at {frame_time}s: {e}")
            return None
        finally:
            # Cleanup
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

    def _analyze_frame_for_standard(self, image_path: str, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Analyze frame with standard prompting (simpler than action analysis).
        """
        try:
            # Create a standard prompt
            standard_prompt = f"""
            Analyze this image for content related to: "{prompt}"
            
            Describe:
            1. Main subject matter and activities
            2. Setting or environment
            3. Objects present
            4. General mood or theme
            
            Rate how well this image matches "{prompt}" on a scale of 1-10.
            
            Format as: Main subject: [description], Setting: [description], Objects: [description], Mood: [description], Match score: [1-10], Reason: [explanation]
            """
            
            # Use the AI handler's basic analysis
            if not self.ai_handler or not hasattr(self.ai_handler, '_analyze_image_content_with_gemini'):
                return None
            
            # Use a simplified analysis call
            response = self.ai_handler._analyze_image_content_with_gemini(image_path, standard_prompt)
            
            if response:
                # Parse the response for match score
                analysis = {
                    'content_description': response,
                    'match_score': 5  # Default
                }
                
                # Try to extract match score from response
                import re
                score_match = re.search(r'[Mm]atch\s+score:\s*(\d+)', response)
                if score_match:
                    try:
                        analysis['match_score'] = int(score_match.group(1))
                    except ValueError:
                        pass
                
                return analysis
            
            return None
            
        except Exception as e:
            self.logger.debug(f"AI standard analysis failed: {e}")
            return None

    def _calculate_standard_relevance_score(self, analysis: dict, prompt: str) -> float:
        """
        Calculate relevance score for standard content matching.
        """
        if not analysis or not prompt:
            return 0.4
        
        score = 0.3  # Base score
        
        # Use match score if available
        if 'match_score' in analysis and analysis['match_score']:
            try:
                match_score = float(analysis['match_score']) / 10.0
                score += match_score * 0.5
            except (ValueError, TypeError):
                pass
        
        # Text matching for additional scoring
        content = analysis.get('content_description', '').lower()
        prompt_lower = prompt.lower()
        
        # Count word matches
        prompt_words = prompt_lower.split()
        matched_words = sum(1 for word in prompt_words if len(word) > 2 and word in content)
        
        if prompt_words:
            word_match_ratio = matched_words / len(prompt_words)
            score += word_match_ratio * 0.3
        
        return min(score, 1.0)

    def _select_best_segments(self, scored_segments: List[Tuple[float, float, float]], target_duration: int) -> List[Tuple[float, float]]:
        """
        Select best segments based on the scored segments.
        """
        if not scored_segments:
            return []
        
        # Sort by score (highest first)
        sorted_segments = sorted(scored_segments, key=lambda x: x[2], reverse=True)
        
        # Log top scores for debugging
        if sorted_segments:
            top_5 = sorted_segments[:5]
            self.logger.info(f"Top scores: {[(f'{start:.1f}-{end:.1f}', f'{score:.3f}') for start, end, score in top_5]}")
        
        selected_segments = []
        total_duration = 0
        min_gap = 1.0  # Shorter gap for actions
        
        for start, end, score in sorted_segments:
            segment_duration = end - start
            
            # For actions, prioritize high-scoring segments even if they exceed target slightly
            if total_duration + segment_duration > target_duration:
                remaining_time = target_duration - total_duration
                # Be more flexible with action segments
                if remaining_time > 1.5 and score > 0.7:  # Keep high-scoring action segments
                    selected_segments.append((start, start + remaining_time))
                break
            
            # Check for overlap (more permissive for high-scoring actions)
            overlap = False
            for existing_start, existing_end in selected_segments:
                if not (end <= existing_start - min_gap or start >= existing_end + min_gap):
                    # Allow some overlap for very high-scoring action segments
                    if score < 0.8:
                        overlap = True
                    break
            
            if not overlap:
                selected_segments.append((start, end))
                total_duration += segment_duration
                
                # Stop early if we have enough high-quality action content
                if total_duration >= target_duration * 0.8 and score > 0.7:
                    break
        
        # Sort by start time
        selected_segments.sort(key=lambda x: x[0])
        
        self.logger.info(f"Selected {len(selected_segments)} segments, total duration: {sum(end-start for start, end in selected_segments):.1f}s")
        return selected_segments
    
    def _detect_and_expand_action_sequences(self, clip, scored_segments: List[Tuple[float, float, float]], target_duration: int) -> List[Tuple[float, float, float, str]]:
        """
        NEW APPROACH: Find ALL action instances first, compile in chronological order,
        then add context only if total duration is less than target.
        """
        if not scored_segments:
            return []
        
        duration = clip.duration
        
        # Step 1: Extract ALL action instances (no context yet)
        # Sort by time to get chronological order
        time_sorted = sorted(scored_segments, key=lambda x: x[0])
        
        self.logger.info(f"Processing {len(scored_segments)} segments to find ALL action instances")
        
        # Identify all discrete actions based on score thresholds
        action_instances = []
        for start, end, score in time_sorted:
            # Action detection based on score quality
            if score >= 0.6:  # High-confidence actions
                action_type = "high_confidence_action"
                action_instances.append((start, end, score, action_type))
                self.logger.info(f"High-confidence action: {start:.1f}-{end:.1f}s, score: {score:.3f}")
            elif score >= 0.4:  # Moderate-confidence actions
                action_type = "moderate_action"
                action_instances.append((start, end, score, action_type))
                self.logger.info(f"Moderate action: {start:.1f}-{end:.1f}s, score: {score:.3f}")
            elif score >= 0.3:  # Lower-confidence but potentially valid
                action_type = "potential_action"
                action_instances.append((start, end, score, action_type))
                self.logger.debug(f"Potential action: {start:.1f}-{end:.1f}s, score: {score:.3f}")
        
        if not action_instances:
            self.logger.warning("No action instances found with current scoring")
            return []
        
        self.logger.info(f"Found {len(action_instances)} total action instances")
        
        # Step 2: Calculate total duration of all raw actions
        total_action_duration = sum(end - start for start, end, _, _ in action_instances)
        self.logger.info(f"Total raw action duration: {total_action_duration:.1f}s, target: {target_duration}s")
        
        # Step 3: Decide on context strategy based on duration gap
        if total_action_duration >= target_duration:
            # We have enough action content - return best actions without context
            self.logger.info("Sufficient action content found - using raw actions without context")
            return action_instances
        else:
            # Need to add context to reach target duration
            duration_gap = target_duration - total_action_duration
            context_per_clip = duration_gap / len(action_instances) if action_instances else 0
            
            self.logger.info(f"Need {duration_gap:.1f}s more content - adding {context_per_clip:.1f}s context per clip")
            
            # Step 4: Add context proportionally to each action
            contextualized_actions = []
            for start, end, score, action_type in action_instances:
                # Calculate context based on clip length and available time, not video length
                clip_duration = end - start
                
                # Context should be proportional to clip length and constrained by available gap
                if clip_duration <= 2.0:  # Very short clips (like pokeball throws)
                    max_context_before = min(1.5, context_per_clip * 0.6)  # 60% of context before
                    max_context_after = min(1.0, context_per_clip * 0.4)   # 40% of context after
                elif clip_duration <= 4.0:  # Short clips
                    max_context_before = min(1.0, context_per_clip * 0.5)
                    max_context_after = min(0.8, context_per_clip * 0.5)
                else:  # Longer clips need less relative context
                    max_context_before = min(0.5, context_per_clip * 0.3)
                    max_context_after = min(0.5, context_per_clip * 0.3)
                
                # Ensure we don't exceed video boundaries
                context_before = min(max_context_before, start)
                context_after = min(max_context_after, duration - end)
                
                # Create contextualized clip
                expanded_start = max(0, start - context_before)
                expanded_end = min(duration, end + context_after)
                
                # Slight score boost for properly contextualized actions
                context_boost = min(0.1, (context_before + context_after) / 5.0)
                final_score = min(1.0, score + context_boost)
                
                contextualized_actions.append((expanded_start, expanded_end, final_score, f"{action_type}_with_context"))
                
                self.logger.info(f"Contextualized action: {start:.1f}-{end:.1f}s -> {expanded_start:.1f}-{expanded_end:.1f}s (+{context_before:.1f}s/-{context_after:.1f}s)")
            
            return contextualized_actions

    def _select_sequence_segments(self, sequence_segments: List[Tuple[float, float, float, str]], target_duration: int) -> List[Tuple[float, float]]:
        """
        Select the best action clips to fit target duration, prioritizing action quality.
        """
        if not sequence_segments:
            return []
        
        # Sort by score (best actions first)
        score_sorted = sorted(sequence_segments, key=lambda x: x[2], reverse=True)
        
        selected_clips = []
        total_duration = 0
        
        self.logger.info(f"Selecting clips from {len(sequence_segments)} candidates for {target_duration}s target")
        
        # Select clips until we reach target duration, prioritizing best scores
        for start, end, score, action_type in score_sorted:
            clip_duration = end - start
            
            # Check if adding this clip would exceed target duration
            if total_duration + clip_duration > target_duration:
                # Check if we have room for a shorter version of this clip
                remaining_time = target_duration - total_duration
                if remaining_time >= 2.0:  # Minimum useful clip length
                    # Trim the clip to fit
                    trimmed_end = start + remaining_time
                    selected_clips.append((start, trimmed_end))
                    total_duration += remaining_time
                    self.logger.info(f"Selected trimmed clip: {start:.1f}-{trimmed_end:.1f}s ({remaining_time:.1f}s), score: {score:.3f}")
                break
            
            # Add the full clip
            selected_clips.append((start, end))
            total_duration += clip_duration
            self.logger.info(f"Selected full clip: {start:.1f}-{end:.1f}s ({clip_duration:.1f}s), score: {score:.3f}")
            
            # Stop if we've reached target duration
            if total_duration >= target_duration:
                break
        
        # Sort final clips by start time (chronological order)
        selected_clips.sort(key=lambda x: x[0])
        
        self.logger.info(f"Final selection: {len(selected_clips)} clips, total duration: {total_duration:.1f}s")
        
        return selected_clips

    def _ensure_temporal_distribution(self, sequence_segments: List[Tuple[float, float, float, str]], video_duration: float) -> List[Tuple[float, float, float, str]]:
        """
        Ensure highlights are distributed across the entire video timeline for completeness.
        """
        if not sequence_segments or len(sequence_segments) <= 2:
            return sequence_segments
        
        # Divide video into thirds for temporal analysis
        third = video_duration / 3
        first_third = third
        second_third = third * 2
        
        # Categorize segments by timeline position
        early_segments = []
        middle_segments = []
        late_segments = []
        
        for seg in sequence_segments:
            start, end, score, seq_type = seg
            midpoint = (start + end) / 2
            
            if midpoint < first_third:
                early_segments.append(seg)
            elif midpoint < second_third:
                middle_segments.append(seg)
            else:
                late_segments.append(seg)
        
        self.logger.info(f"Temporal distribution: Early={len(early_segments)}, Middle={len(middle_segments)}, Late={len(late_segments)}")
        
        # Sort each group by score
        early_segments.sort(key=lambda x: x[2], reverse=True)
        middle_segments.sort(key=lambda x: x[2], reverse=True)
        late_segments.sort(key=lambda x: x[2], reverse=True)
        
        # Select distributed segments (prioritize balance but allow concentration if one period has much better content)
        distributed = []
        
        # Take at least one from each period if available, but prioritize quality
        if early_segments:
            distributed.extend(early_segments[:2])  # Top 2 from early
        if middle_segments:
            distributed.extend(middle_segments[:2])  # Top 2 from middle  
        if late_segments:
            distributed.extend(late_segments[:2])  # Top 2 from late
        
        # Add remaining high-scoring segments from any period
        all_remaining = early_segments[2:] + middle_segments[2:] + late_segments[2:]
        all_remaining.sort(key=lambda x: x[2], reverse=True)
        
        # Add top remaining segments to reach reasonable count
        max_total = min(10, len(sequence_segments))  # Don't exceed original count
        distributed.extend(all_remaining[:max_total - len(distributed)])
        
        # Sort by timeline position for final output
        distributed.sort(key=lambda x: x[0])
        
        self.logger.info(f"Distributed selection: {len(distributed)} segments across timeline")
        return distributed

    def _score_segments_with_enhanced_motion(self, clip, segments: List[Tuple[float, float]], prompt: str) -> List[Tuple[float, float, float]]:
        """
        Enhanced motion-based scoring when AI analysis fails, with prompt-aware scoring.
        """
        self.logger.info("Using enhanced motion analysis as fallback...")
        scored_segments = []
        
        # Extract key terms from prompt for motion-based relevance
        prompt_lower = prompt.lower()
        action_indicators = ['throw', 'catch', 'ball', 'game', 'pokemon', 'mobile', 'phone', 'AR']
        prompt_has_action = any(indicator in prompt_lower for indicator in action_indicators)
        
        for start, end in segments:
            try:
                # Enhanced motion analysis for this segment
                motion_score = self._analyze_segment_motion_enhanced(clip, start, end)
                
                # Base score from motion
                score = 0.4 + (motion_score * 0.4)  # 0.4 to 0.8 range
                
                # Boost score if segment seems relevant to prompt
                if prompt_has_action:
                    # Check if this segment has characteristics matching the prompt
                    segment_duration = end - start
                    
                    # Prefer shorter segments for throwing actions (1-3 seconds typical)
                    if 1.0 <= segment_duration <= 4.0:
                        score += 0.15
                    
                    # Boost segments with high motion (likely action)
                    if motion_score > 0.7:
                        score += 0.2
                
                scored_segments.append((start, end, min(score, 1.0)))
                
            except Exception as e:
                self.logger.debug(f"Enhanced motion analysis failed for {start}-{end}: {e}")
                scored_segments.append((start, end, 0.5))  # Default fallback
        
        self.logger.info(f"Enhanced motion scoring completed for {len(scored_segments)} segments")
        return scored_segments

    def _analyze_segment_motion_enhanced(self, clip, start: float, end: float) -> float:
        """
        Enhanced motion analysis for a specific segment.
        """
        try:
            # Sample multiple frames across the segment
            segment_duration = end - start
            if segment_duration < 0.5:
                frame_times = [start + segment_duration/2]
            elif segment_duration < 2.0:
                frame_times = [start + 0.2, end - 0.2]
            else:
                # Sample 3-4 frames across the segment
                step = segment_duration / 4
                frame_times = [start + step, start + 2*step, start + 3*step]
            
            # Extract frames
            frames = []
            for t in frame_times:
                if 0 <= t < clip.duration:
                    frame = clip.get_frame(t)
                    if frame is not None:
                        frames.append(frame)
            
            if len(frames) < 2:
                return 0.3
            
            # Calculate motion across all frame pairs
            motion_scores = []
            for i in range(len(frames) - 1):
                motion = self._calculate_frame_motion([frames[i], frames[i+1]])
                motion_scores.append(motion)
            
            # Return average motion score
            avg_motion = sum(motion_scores) / len(motion_scores) if motion_scores else 0.3
            return min(avg_motion, 1.0)
            
        except Exception as e:
            self.logger.debug(f"Enhanced segment motion analysis failed: {e}")
            return 0.3

    def _create_emergency_highlights(self, clip, target_duration: int) -> List[Tuple[float, float]]:
        """
        Emergency fallback to create highlights when all other methods fail.
        Always produces some segments, even if they're not perfect.
        """
        self.logger.info("Creating emergency highlights - ensuring user always gets output")
        
        duration = clip.duration
        segments = []
        
        # Strategy 1: Distribute segments evenly across video timeline
        if duration > target_duration:
            # Create 3-5 segments distributed across the video
            num_segments = min(5, max(3, target_duration // 8))  # 3-5 segments of ~8s each
            segment_duration = min(8.0, target_duration / num_segments)
            
            # Distribute across timeline
            time_step = duration / (num_segments + 1)  # +1 to avoid endpoints
            
            for i in range(num_segments):
                start_time = time_step * (i + 1) - segment_duration / 2
                start_time = max(0, start_time)
                end_time = min(duration, start_time + segment_duration)
                
                # Adjust if we go beyond video end
                if end_time > duration:
                    end_time = duration
                    start_time = max(0, end_time - segment_duration)
                
                segments.append((start_time, end_time))
                self.logger.info(f"Emergency segment {i+1}: {start_time:.1f}-{end_time:.1f}s")
        else:
            # Video is shorter than target, just use the whole thing
            segments.append((0, duration))
        
        # Strategy 2: If we still have time to fill, add more segments
        total_used = sum(end - start for start, end in segments)
        if total_used < target_duration * 0.8 and len(segments) < 6:
            # Add some shorter segments in between
            remaining_time = target_duration - total_used
            extra_segments_needed = min(3, int(remaining_time // 4))
            
            for i in range(extra_segments_needed):
                # Find gaps between existing segments
                if len(segments) > 1:
                    gap_start = segments[i][1] + 1  # 1s after previous segment ends
                    gap_end = gap_start + min(4.0, remaining_time / extra_segments_needed)
                    
                    if gap_end < duration - 1:
                        segments.append((gap_start, gap_end))
                        self.logger.info(f"Emergency filler segment: {gap_start:.1f}-{gap_end:.1f}s")
        
        # Sort by timeline and trim to target duration
        segments.sort(key=lambda x: x[0])
        
        # Trim segments if we exceed target duration
        total_duration = 0
        final_segments = []
        for start, end in segments:
            segment_duration = end - start
            if total_duration + segment_duration <= target_duration:
                final_segments.append((start, end))
                total_duration += segment_duration
            else:
                # Add partial segment to reach target
                remaining = target_duration - total_duration
                if remaining > 1.0:  # Only add if at least 1 second
                    final_segments.append((start, start + remaining))
                break
        
        if not final_segments:
            # Absolute final fallback: just take the first 30 seconds
            final_segments = [(0, min(target_duration, duration))]
            self.logger.warning("Absolute fallback: using first portion of video")
        
        total_final = sum(end - start for start, end in final_segments)
        self.logger.info(f"Emergency highlights created: {len(final_segments)} segments, total: {total_final:.1f}s")
        
        return final_segments

    def _analyze_video_for_segment_similarities(self, clip, target_duration: int, 
                                              example_data: Dict[str, Any], 
                                              context_padding: float, 
                                              prompt: str) -> List[Tuple[float, float]]:
        """
        Analyze video to find segments similar to the provided example segment.
        This is the core method for segment-based highlight detection.
        """
        self.logger.info("Starting segment-based similarity analysis")
        
        # Step 1: Extract and analyze the example segment
        example_analysis = self._analyze_example_segment(clip, example_data, prompt)
        if not example_analysis:
            self.logger.error("Failed to analyze example segment")
            return []
        
        # Step 2: Calculate optimal sampling strategy with price optimization
        video_duration = clip.duration
        example_duration = example_analysis['duration']
        
        # SUPER CHEAP: Analyze way fewer frames and be much less picky
        if video_duration <= 300:  # 5 minutes or less
            sample_interval = 5.0  # Much cheaper
            max_samples = 20  # Cap at 20 frames max
        elif video_duration <= 1800:  # 30 minutes or less
            sample_interval = 10.0  # Very cheap
            max_samples = 30  # Cap at 30 frames max
        else:  # Longer videos
            sample_interval = 20.0  # Super cheap
            max_samples = 40  # Cap at 40 frames max
        
        # Adjust based on example segment length (longer examples need more careful analysis)
        if example_duration > 10:  # Long example segment
            sample_interval *= 0.8  # Slightly more frequent sampling
            max_samples = min(max_samples, int(video_duration / sample_interval))
        
        estimated_cost = max_samples * 0.01  # Rough estimate - much cheaper now!
        self.logger.info(f"COST-OPTIMIZED: every {sample_interval:.1f}s, max {max_samples} samples")
        self.logger.info(f"Estimated analysis cost: ~${estimated_cost:.2f} (MUCH CHEAPER!)")
        
        # Step 3: Find similar frames with budget controls (MUCH cheaper and less strict)
        similar_frames = self._find_similar_frames_optimized(clip, example_analysis, sample_interval, max_samples, prompt)
        
        if not similar_frames:
            self.logger.warning("No similar frames found, using fallback strategy")
            # FALLBACK: Use best guess segments from video to always deliver a result
            return self._create_fallback_highlight_reel(clip, target_duration, example_analysis, context_padding)
        
        self.logger.info(f"Found {len(similar_frames)} potentially similar frames")
        
        # Step 4: Group similar frames into segments
        segments = self._group_similar_frames_into_segments(similar_frames, video_duration)
        
        # Step 5: Extend segments with context padding
        extended_segments = self._extend_segments_with_context(segments, context_padding, video_duration)
        
        # Step 6: Select best segments to fit target duration
        final_segments = self._select_best_similarity_segments(extended_segments, target_duration)
        
        total_duration = sum(end - start for start, end in final_segments)
        self.logger.info(f"Selected {len(final_segments)} segments with total duration {total_duration:.1f}s")
        
        return final_segments
    
    def _create_fallback_highlight_reel(self, clip, target_duration: int, example_analysis: Dict[str, Any], context_padding: float) -> List[Tuple[float, float]]:
        """
        ALWAYS create a highlight reel even if no similar segments found.
        Use best guess based on video structure and the example segment timing.
        """
        self.logger.info("Creating fallback highlight reel - ALWAYS deliver a result!")
        
        video_duration = clip.duration
        example_start = example_analysis.get('start_time', 0)
        example_end = example_analysis.get('end_time', 5)
        example_duration = example_end - example_start
        
        # Strategy: Take segments from similar positions in the video timeline
        segments = []
        
        # Calculate how many segments we need
        segment_count = max(3, min(8, target_duration // max(3, example_duration)))
        segment_duration = min(target_duration / segment_count, example_duration * 1.5)
        
        # Distribute segments across the video timeline
        for i in range(int(segment_count)):
            # Place segments at similar relative positions to the example
            relative_position = example_start / video_duration if video_duration > 0 else 0.5
            
            # Add some variation to avoid taking the exact same moment
            position_variation = (i - segment_count/2) * 0.1  # Spread around the relative position
            target_position = max(0, min(1, relative_position + position_variation))
            
            start_time = target_position * (video_duration - segment_duration)
            end_time = start_time + segment_duration
            
            # Ensure we don't go beyond video bounds
            if end_time > video_duration:
                end_time = video_duration
                start_time = max(0, end_time - segment_duration)
            
            segments.append((start_time, end_time))
            self.logger.info(f"Fallback segment {i+1}: {start_time:.1f}s - {end_time:.1f}s")
        
        # Remove overlaps and ensure we hit target duration
        segments = self._clean_and_optimize_segments(segments, target_duration)
        
        total_duration = sum(end - start for start, end in segments)
        self.logger.info(f"Fallback highlight reel created: {len(segments)} segments, {total_duration:.1f}s total")
        
        return segments
    
    def _clean_and_optimize_segments(self, segments: List[Tuple[float, float]], target_duration: int) -> List[Tuple[float, float]]:
        """Clean up segments and ensure they hit the target duration."""
        if not segments:
            return []
        
        # Sort by start time
        segments = sorted(segments, key=lambda x: x[0])
        
        # Remove overlaps
        cleaned_segments = []
        for start, end in segments:
            if not cleaned_segments:
                cleaned_segments.append((start, end))
            else:
                last_start, last_end = cleaned_segments[-1]
                if start >= last_end:  # No overlap
                    cleaned_segments.append((start, end))
                else:  # Overlap - merge or skip
                    if end > last_end:  # Extend the last segment
                        cleaned_segments[-1] = (last_start, end)
        
        # Adjust to hit target duration
        current_duration = sum(end - start for start, end in cleaned_segments)
        
        if current_duration < target_duration and len(cleaned_segments) > 0:
            # Extend segments proportionally
            scale_factor = target_duration / current_duration
            scaled_segments = []
            for start, end in cleaned_segments:
                duration = end - start
                new_duration = duration * scale_factor
                scaled_segments.append((start, start + new_duration))
            cleaned_segments = scaled_segments
        
        elif current_duration > target_duration:
            # Trim segments to fit target
            running_total = 0
            trimmed_segments = []
            for start, end in cleaned_segments:
                duration = end - start
                if running_total + duration <= target_duration:
                    trimmed_segments.append((start, end))
                    running_total += duration
                else:
                    # Partial segment to complete target
                    remaining = target_duration - running_total
                    if remaining > 1:  # Only if at least 1 second left
                        trimmed_segments.append((start, start + remaining))
                    break
            cleaned_segments = trimmed_segments
        
        return cleaned_segments

    def _analyze_example_segment(self, clip, example_data: Dict[str, Any], prompt: str) -> Optional[Dict[str, Any]]:
        """
        Extract and analyze the example segment from the video.
        """
        try:
            start_time = example_data['start_time']
            end_time = example_data['end_time']
            description = example_data.get('description', '')
            
            self.logger.info(f"Analyzing example segment: {start_time:.1f}s - {end_time:.1f}s")
            
            # Extract the example segment
            example_segment = clip.subclip(start_time, end_time)
            segment_duration = end_time - start_time
            
            # Sample multiple frames from the segment for analysis
            sample_count = max(3, min(8, int(segment_duration * 2)))  # 2 frames per second, min 3, max 8
            frame_times = []
            
            if sample_count == 1:
                frame_times = [start_time + segment_duration / 2]
            else:
                step = segment_duration / (sample_count - 1)
                frame_times = [start_time + i * step for i in range(sample_count)]
            
            # Analyze each frame in the segment
            frame_analyses = []
            for i, frame_time in enumerate(frame_times):
                try:
                    frame = clip.get_frame(frame_time)
                    if frame is None:
                        continue
                    
                    # Save frame to temporary file
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                        from PIL import Image
                        img = Image.fromarray(frame)
                        img.save(temp_file.name, 'JPEG')
                        temp_path = temp_file.name
                    
                    try:
                        # Analyze this frame intensely
                        frame_analysis = self._analyze_segment_frame_intensely(temp_path, frame_time, description, prompt, i, sample_count)
                        if frame_analysis:
                            frame_analyses.append(frame_analysis)
                    finally:
                        try:
                            os.unlink(temp_path)
                        except:
                            pass
                            
                except Exception as e:
                    self.logger.debug(f"Error analyzing frame at {frame_time:.1f}s: {e}")
                    continue
            
            if not frame_analyses:
                self.logger.warning("No frames could be analyzed from example segment")
                return None
            
            # Combine analyses into segment summary
            segment_analysis = {
                'start_time': start_time,
                'end_time': end_time,
                'duration': segment_duration,
                'description': description,
                'frame_count': len(frame_analyses),
                'frame_analyses': frame_analyses,
                'combined_features': self._combine_frame_analyses(frame_analyses),
                'segment_type': 'user_selected_example'
            }
            
            example_segment.close()
            self.logger.info(f"Successfully analyzed example segment with {len(frame_analyses)} frames")
            return segment_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing example segment: {e}")
            return None

    def _analyze_example_image_intensely(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Analyze the example image intensely to understand what to look for.
        """
        try:
            # Save image to temporary file for analysis
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(image_data)
                temp_path = temp_file.name
            
            try:
                # Use the existing AI analysis method but with enhanced prompt
                enhanced_prompt = """
                Analyze this reference image EXTREMELY thoroughly. This image represents what the user wants to find in their video.
                
                Focus on:
                1. VISUAL ELEMENTS: Colors, shapes, objects, textures, lighting, composition
                2. ACTIONS: Any movements, gestures, activities, poses
                3. CONTEXT: Setting, environment, background elements
                4. PEOPLE: Number of people, their positioning, clothing, expressions
                5. OBJECTS: Specific items, tools, devices, toys, etc.
                6. STYLE: Visual style, quality, camera angle, perspective
                7. MOOD: Emotional tone, atmosphere, energy level
                
                Be extremely detailed and specific in your analysis. This analysis will be used to find similar moments in a video.
                
                Return JSON with keys: main_elements, visual_style, actions_detected, context_clues, distinctive_features, search_keywords
                """
                
                analysis = self._call_enhanced_ai_analysis(temp_path, enhanced_prompt)
                
                if analysis:
                    # Enhance the analysis with additional processing
                    analysis['similarity_keywords'] = self._extract_similarity_keywords(analysis)
                    return analysis
                else:
                    self.logger.warning("AI analysis of example image failed")
                    return None
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Error analyzing example image: {e}")
            return None

    def _extract_similarity_keywords(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Extract keywords from the analysis that will be useful for similarity matching.
        """
        keywords = []
        
        # Extract from different analysis fields
        for field in ['main_elements', 'actions_detected', 'context_clues', 'distinctive_features']:
            if field in analysis and analysis[field]:
                text = str(analysis[field]).lower()
                # Simple keyword extraction - could be enhanced with NLP
                words = text.split()
                keywords.extend([word.strip('.,!?') for word in words if len(word) > 3])
        
        # Remove duplicates and return
        return list(set(keywords))

    def _find_similar_frames_optimized(self, clip, example_analysis: Dict[str, Any], 
                                      sample_interval: float, max_samples: int, prompt: str) -> List[Tuple[float, float]]:
        """
        Find frames in the video that are similar to the example segment with budget optimization.
        Returns list of (timestamp, similarity_score) tuples.
        """
        similar_frames = []
        video_duration = clip.duration
        
        # Sample frames across the video with budget limits
        current_time = 0
        frame_count = 0
        samples_processed = 0
        
        while current_time < video_duration and samples_processed < max_samples:
            try:
                # Extract frame at current time
                frame = clip.get_frame(current_time)
                if frame is None:
                    current_time += sample_interval
                    continue
                
                # Save frame to temporary file for analysis
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                    from PIL import Image
                    img = Image.fromarray(frame)
                    img.save(temp_file.name, 'JPEG')
                    temp_path = temp_file.name
                
                try:
                    # Analyze frame for similarity to example
                    similarity_score = self._calculate_frame_similarity_to_example(
                        temp_path, example_analysis, prompt
                    )
                    
                    if similarity_score > 0.3:  # Much lower threshold - accept "close enough"
                        similar_frames.append((current_time, similarity_score))
                        self.logger.debug(f"Similar frame found at {current_time:.1f}s (score: {similarity_score:.2f})")
                    
                    frame_count += 1
                    samples_processed += 1
                    
                    if frame_count % 20 == 0:
                        progress = (samples_processed / max_samples) * 100
                        self.logger.info(f"Progress: {progress:.1f}% - Analyzed {frame_count} frames, found {len(similar_frames)} similar frames")
                        
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                
            except Exception as e:
                self.logger.debug(f"Error analyzing frame at {current_time:.1f}s: {e}")
            
            current_time += sample_interval
        
        budget_status = "within budget" if samples_processed < max_samples else "budget limit reached"
        self.logger.info(f"Completed frame analysis ({budget_status}): {frame_count} frames analyzed, {len(similar_frames)} similar frames found")
        return similar_frames

    def _calculate_frame_similarity_to_example(self, frame_path: str, 
                                             example_analysis: Dict[str, Any], 
                                             prompt: str) -> float:
        """
        Calculate how similar a frame is to the example segment.
        """
        try:
            # Create a similarity-focused prompt based on segment analysis
            combined_features = example_analysis.get('combined_features', {})
            segment_summary = combined_features.get('segment_summary', 'analyzed segment')
            key_search_terms = combined_features.get('key_search_terms', [])
            
            # Build description from segment analysis
            if key_search_terms:
                example_description = f"{segment_summary}. Key elements: {', '.join(key_search_terms[:8])}"
            else:
                example_description = segment_summary
            
            similarity_prompt = f"""
            Compare this frame to the reference example. The reference example contains: {example_description}
            
            Rate the similarity on a scale of 0-10 where:
            - 10: Nearly identical or very similar scene/action/composition
            - 8-9: Strong similarity in key elements (same action, similar objects, similar setting)
            - 6-7: Moderate similarity (some matching elements but different context)
            - 4-5: Some similarity (few matching elements)
            - 0-3: Little to no similarity
            
            Focus on: {prompt if prompt else "visual similarity, actions, objects, and context"}
            
            Return JSON with: {{"similarity_score": number, "matching_elements": "description", "differences": "description"}}
            """
            
            # Use AI to analyze similarity
            analysis = self._call_enhanced_ai_analysis(frame_path, similarity_prompt)
            
            if analysis and 'similarity_score' in analysis:
                score = float(analysis['similarity_score']) / 10.0  # Convert to 0-1 scale
                return min(max(score, 0.0), 1.0)  # Clamp to 0-1 range
            else:
                return 0.0
                
        except Exception as e:
            self.logger.debug(f"Error calculating frame similarity: {e}")
            return 0.0

    def _group_similar_frames_into_segments(self, similar_frames: List[Tuple[float, float]], 
                                          video_duration: float) -> List[Tuple[float, float, float]]:
        """
        Group nearby similar frames into continuous segments.
        Returns list of (start_time, end_time, avg_score) tuples.
        """
        if not similar_frames:
            return []
        
        # Sort by timestamp
        similar_frames.sort(key=lambda x: x[0])
        
        segments = []
        current_start = similar_frames[0][0]
        current_end = similar_frames[0][0]
        current_scores = [similar_frames[0][1]]
        
        gap_threshold = 3.0  # Seconds - frames within this gap are considered part of the same segment
        
        for i in range(1, len(similar_frames)):
            timestamp, score = similar_frames[i]
            
            if timestamp - current_end <= gap_threshold:
                # Continue current segment
                current_end = timestamp
                current_scores.append(score)
            else:
                # Start new segment
                avg_score = sum(current_scores) / len(current_scores)
                segments.append((current_start, current_end, avg_score))
                
                current_start = timestamp
                current_end = timestamp
                current_scores = [score]
        
        # Add the last segment
        if current_scores:
            avg_score = sum(current_scores) / len(current_scores)
            segments.append((current_start, current_end, avg_score))
        
        self.logger.info(f"Grouped {len(similar_frames)} similar frames into {len(segments)} segments")
        return segments

    def _extend_segments_with_context(self, segments: List[Tuple[float, float, float]], 
                                    context_padding: float, 
                                    video_duration: float) -> List[Tuple[float, float, float]]:
        """
        Extend segments with context padding before each scene.
        """
        extended_segments = []
        
        for start, end, score in segments:
            # Add context padding before the segment
            extended_start = max(0, start - context_padding)
            
            # Ensure we don't extend beyond video duration
            extended_end = min(video_duration, end)
            
            # Ensure minimum segment length
            if extended_end - extended_start < 1.0:
                extended_end = min(video_duration, extended_start + 1.0)
            
            extended_segments.append((extended_start, extended_end, score))
        
        self.logger.info(f"Extended {len(segments)} segments with {context_padding}s context padding")
        return extended_segments

    def _select_best_similarity_segments(self, segments: List[Tuple[float, float, float]], 
                                       target_duration: int) -> List[Tuple[float, float]]:
        """
        Select the best segments to fit the target duration.
        """
        if not segments:
            return []
        
        # Sort segments by score (descending)
        segments.sort(key=lambda x: x[2], reverse=True)
        
        selected_segments = []
        total_duration = 0
        
        for start, end, score in segments:
            segment_duration = end - start
            
            if total_duration + segment_duration <= target_duration:
                selected_segments.append((start, end))
                total_duration += segment_duration
                self.logger.debug(f"Selected segment {start:.1f}-{end:.1f}s (score: {score:.2f})")
            else:
                # Check if we can fit a trimmed version of this segment
                remaining_duration = target_duration - total_duration
                if remaining_duration > 2.0:  # Only if we have at least 2 seconds left
                    # Take the beginning of this segment
                    selected_segments.append((start, start + remaining_duration))
                    total_duration = target_duration
                    self.logger.debug(f"Selected trimmed segment {start:.1f}-{start + remaining_duration:.1f}s")
                break
        
        # Sort final segments by timeline order
        selected_segments.sort(key=lambda x: x[0])
        
        self.logger.info(f"Selected {len(selected_segments)} segments totaling {total_duration:.1f}s")
        return selected_segments

    def _analyze_segment_frame_intensely(self, frame_path: str, frame_time: float, 
                                       description: str, prompt: str, 
                                       frame_index: int, total_frames: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a single frame from the example segment intensely.
        """
        try:
            # Create enhanced prompt for segment frame analysis
            enhanced_prompt = f"""
            Analyze this frame from a user-selected example segment (frame {frame_index + 1} of {total_frames}).
            
            CONTEXT:
            - This frame is from timestamp {frame_time:.1f}s in the video
            - User description: "{description if description else 'No description provided'}"
            - Additional context: "{prompt if prompt else 'General highlight analysis'}"
            
            ANALYSIS FOCUS - This frame represents what the user wants to find more of:
            1. VISUAL CHARACTERISTICS: Lighting, colors, composition, camera angle, image quality
            2. SUBJECTS: People, objects, characters - their positioning, appearance, clothing, expressions
            3. ACTIONS: Any movements, gestures, activities, interactions happening
            4. ENVIRONMENT: Setting, background, indoor/outdoor, time of day
            5. STYLE: Gaming interface, real-world scene, artistic style, video quality
            6. EMOTIONAL TONE: Mood, energy level, atmosphere
            7. TECHNICAL ELEMENTS: Screen elements, UI, effects, overlays
            
            IMPORTANT: Be extremely detailed and specific. This analysis will be used to find similar moments throughout the video.
            Focus on what makes this moment unique and interesting to the user.
            
            Return JSON with keys: visual_elements, subjects, actions, environment, style, mood, technical_aspects, uniqueness_factors, search_keywords
            """
            
            analysis = self._call_enhanced_ai_analysis(frame_path, enhanced_prompt)
            
            if analysis:
                # Add frame-specific metadata
                analysis['frame_time'] = frame_time
                analysis['frame_index'] = frame_index
                analysis['analysis_timestamp'] = datetime.now().isoformat()
                return analysis
            else:
                self.logger.warning(f"AI analysis failed for frame at {frame_time:.1f}s")
                return None
                
        except Exception as e:
            self.logger.debug(f"Error analyzing segment frame at {frame_time:.1f}s: {e}")
            return None

    def _combine_frame_analyses(self, frame_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine multiple frame analyses into a unified segment understanding.
        """
        try:
            if not frame_analyses:
                return {}
            
            combined = {
                'dominant_visual_elements': [],
                'consistent_subjects': [],
                'primary_actions': [],
                'environment_type': '',
                'overall_style': '',
                'mood_indicators': [],
                'technical_patterns': [],
                'key_search_terms': [],
                'segment_summary': '',
                'confidence_score': 0.0
            }
            
            # Collect all elements from each frame
            all_elements = {}
            for analysis in frame_analyses:
                for key in ['visual_elements', 'subjects', 'actions', 'environment', 'style', 'mood', 'technical_aspects']:
                    if key in analysis and analysis[key]:
                        text = str(analysis[key]).lower()
                        words = text.split()
                        for word in words:
                            clean_word = word.strip('.,!?()[]{}')
                            if len(clean_word) > 3:
                                all_elements[clean_word] = all_elements.get(clean_word, 0) + 1
            
            # Find most frequent elements (appear in multiple frames)
            frame_count = len(frame_analyses)
            frequent_threshold = max(1, frame_count // 2)  # Must appear in at least half the frames
            
            frequent_elements = {k: v for k, v in all_elements.items() if v >= frequent_threshold}
            combined['key_search_terms'] = list(frequent_elements.keys())
            
            # Create segment summary
            if frequent_elements:
                top_elements = sorted(frequent_elements.keys(), key=lambda x: frequent_elements[x], reverse=True)[:10]
                combined['segment_summary'] = f"Segment featuring: {', '.join(top_elements[:5])}"
                combined['confidence_score'] = min(1.0, len(frequent_elements) / 10.0)
            else:
                combined['segment_summary'] = "Analyzed segment with unique characteristics"
                combined['confidence_score'] = 0.5
            
            self.logger.debug(f"Combined analysis: {len(frequent_elements)} frequent elements, confidence: {combined['confidence_score']:.2f}")
            return combined
            
        except Exception as e:
            self.logger.warning(f"Error combining frame analyses: {e}")
            return {'segment_summary': 'Analysis combination failed', 'confidence_score': 0.3}
    
    def generate_extended_highlight_reel_beta(self, video_path: str, target_duration: int = 900, 
                                            prompt: str = "", max_cost: float = 1.0) -> Tuple[bool, str, str]:
        """
        BETA: Generate highlight reels from extended videos (hours long) while keeping costs under $1.
        Uses multi-stage analysis: cheap pre-filtering + smart AI analysis on promising segments only.
        
        Args:
            video_path: Path to the source video
            target_duration: Target duration in seconds (default: 15 minutes = 900s)
            prompt: Natural language prompt for content guidance
            max_cost: Maximum cost allowed for analysis (default: $1.00)
            
        Returns:
            Tuple[bool, str, str]: (success, output_path, message)
        """
        try:
            if not os.path.exists(video_path):
                return False, "", f"Video file not found: {video_path}"
            
            self.logger.info(f"[BETA] Extended highlight reel generation from {video_path}")
            self.logger.info(f"[BETA] Target duration: {target_duration}s ({target_duration/60:.1f} minutes)")
            self.logger.info(f"[BETA] Max cost budget: ${max_cost:.2f}")
            
            # Load video
            clip = VideoFileClip(video_path)
            original_duration = clip.duration
            
            if original_duration <= target_duration:
                self.logger.info("Video is already shorter than target duration")
                return True, video_path, "Video is already the right length"
            
            self.logger.info(f"[BETA] Processing {original_duration/3600:.1f} hour video")
            
            # Multi-stage analysis for cost efficiency
            segments = self._extended_video_analysis_beta(clip, target_duration, prompt, max_cost)
            
            # Always ensure we have segments
            if not segments:
                self.logger.warning("[BETA] No segments found, using emergency highlights")
                segments = self._create_emergency_highlights(clip, target_duration)
            
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
                output_filename = f"{base_name}_extended_highlight_beta_{timestamp}.mp4"
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
                            video_path, "extended_highlight_reel_beta", output_path
                        )
                    except Exception as e:
                        self.logger.warning(f"Could not track video processing: {e}")
                
                total_duration = sum(end - start for start, end in segments)
                self.logger.info(f"[BETA] Extended highlight reel saved to {output_path}")
                return True, output_path, f"Extended highlight reel created ({len(segments)} segments, {total_duration:.1f}s total) - BETA"
            else:
                clip.close()
                return False, "", "Failed to create extended highlight reel"
                
        except Exception as e:
            self.logger.exception(f"Error generating extended highlight reel: {e}")
            return False, "", f"Error generating extended highlight reel: {str(e)}"
    
    def _extended_video_analysis_beta(self, clip, target_duration: int, prompt: str, max_cost: float) -> List[Tuple[float, float]]:
        """
        Multi-stage analysis for extended videos to keep costs under budget.
        
        Stage 1: Cheap motion/audio detection to find promising segments
        Stage 2: Smart sampling with cost controls
        Stage 3: AI analysis on filtered segments only
        """
        video_duration = clip.duration
        self.logger.info(f"[BETA] Starting multi-stage analysis for {video_duration/3600:.1f}h video")
        
        # Stage 1: Cheap pre-filtering (no AI cost)
        self.logger.info("[BETA] Stage 1: Motion and audio pre-filtering...")
        promising_segments = self._find_promising_segments_cheap(clip, video_duration, target_duration)
        
        # Stage 2: Smart sampling strategy based on budget
        self.logger.info(f"[BETA] Stage 2: Smart sampling from {len(promising_segments)} promising segments...")
        sampled_segments = self._smart_sample_for_budget(promising_segments, max_cost, video_duration)
        
        # Stage 3: AI analysis on filtered segments only
        self.logger.info(f"[BETA] Stage 3: AI analysis on {len(sampled_segments)} selected segments...")
        final_segments = self._analyze_sampled_segments_beta(clip, sampled_segments, target_duration, prompt)
        
        self.logger.info(f"[BETA] Multi-stage analysis complete: {len(final_segments)} final segments")
        return final_segments
    
    def _find_promising_segments_cheap(self, clip, video_duration: float, target_duration: int) -> List[Tuple[float, float, float]]:
        """
        Stage 1: Find promising segments using cheap methods (no AI cost).
        Returns segments with estimated quality scores.
        """
        segments = []
        
        # Strategy 1: Motion-based detection (very cheap)
        motion_segments = self._detect_high_motion_segments(clip, video_duration)
        
        # Strategy 2: Audio energy detection (very cheap)
        audio_segments = self._detect_high_audio_energy_segments(clip, video_duration)
        
        # Strategy 3: Scene change detection (very cheap)
        scene_segments = self._detect_scene_changes(clip, video_duration)
        
        # Combine and score all segments
        all_candidates = motion_segments + audio_segments + scene_segments
        
        # Remove duplicates and merge overlapping segments
        merged_segments = self._merge_overlapping_segments(all_candidates)
        
        # Score based on multiple factors
        scored_segments = []
        for start, end, base_score in merged_segments:
            # Boost score based on position (beginning/end often have good content)
            position_boost = self._calculate_position_boost(start, end, video_duration)
            
            # Duration bonus (prefer segments of reasonable length)
            duration = end - start
            duration_bonus = 1.0 if 3 <= duration <= 15 else 0.5
            
            final_score = base_score * position_boost * duration_bonus
            scored_segments.append((start, end, final_score))
        
        # Sort by score and return top candidates
        scored_segments.sort(key=lambda x: x[2], reverse=True)
        
        # Return top segments that could fill ~3x target duration (for redundancy)
        target_candidates = target_duration * 3
        selected_segments = []
        total_duration = 0
        
        for start, end, score in scored_segments:
            duration = end - start
            if total_duration + duration <= target_candidates:
                selected_segments.append((start, end, score))
                total_duration += duration
        
        self.logger.info(f"[BETA] Stage 1 found {len(selected_segments)} promising segments ({total_duration:.1f}s total)")
        return selected_segments
    
    def _detect_high_motion_segments(self, clip, video_duration: float) -> List[Tuple[float, float, float]]:
        """Detect segments with high motion using computer vision (no AI cost)."""
        segments = []
        sample_interval = max(30, video_duration / 100)  # Sample every 30s or 1% of video
        window_size = 10  # 10-second windows
        
        current_time = 0
        while current_time < video_duration - window_size:
            try:
                # Sample 3 frames from this window
                frame_times = [
                    current_time + 1,
                    current_time + window_size/2,
                    current_time + window_size - 1
                ]
                
                frames = []
                for t in frame_times:
                    if t < video_duration:
                        frame = clip.get_frame(t)
                        if frame is not None:
                            frames.append(frame)
                
                if len(frames) >= 2:
                    motion_score = self._calculate_frame_motion(frames)
                    if motion_score > 0.2:  # Threshold for "high motion"
                        segments.append((current_time, current_time + window_size, motion_score))
                
            except Exception as e:
                self.logger.debug(f"Motion detection error at {current_time}s: {e}")
            
            current_time += sample_interval
        
        return segments
    
    def _detect_high_audio_energy_segments(self, clip, video_duration: float) -> List[Tuple[float, float, float]]:
        """Detect segments with high audio energy (no AI cost)."""
        segments = []
        
        try:
            if not hasattr(clip, 'audio') or clip.audio is None:
                return segments
            
            # Sample audio energy at regular intervals
            sample_interval = max(15, video_duration / 200)  # Every 15s or 0.5% of video
            window_size = 5  # 5-second windows
            
            current_time = 0
            while current_time < video_duration - window_size:
                try:
                    # Get audio segment
                    audio_segment = clip.audio.subclip(current_time, min(current_time + window_size, video_duration))
                    
                    # Calculate RMS energy (rough approximation)
                    audio_array = audio_segment.to_soundarray()
                    if audio_array.size > 0:
                        rms = np.sqrt(np.mean(audio_array**2))
                        
                        if rms > 0.05:  # Threshold for "high energy"
                            segments.append((current_time, current_time + window_size, float(rms)))
                    
                    audio_segment.close()
                    
                except Exception as e:
                    self.logger.debug(f"Audio analysis error at {current_time}s: {e}")
                
                current_time += sample_interval
                
        except Exception as e:
            self.logger.debug(f"Audio detection failed: {e}")
        
        return segments
    
    def _detect_scene_changes(self, clip, video_duration: float) -> List[Tuple[float, float, float]]:
        """Detect scene changes using simple frame difference (no AI cost)."""
        segments = []
        sample_interval = max(60, video_duration / 50)  # Every minute or 2% of video
        
        prev_frame = None
        current_time = 0
        
        while current_time < video_duration:
            try:
                frame = clip.get_frame(current_time)
                if frame is not None and prev_frame is not None:
                    # Calculate frame difference
                    diff = np.mean(np.abs(frame.astype(float) - prev_frame.astype(float)))
                    
                    if diff > 50:  # Threshold for scene change
                        # Add segment around scene change
                        start_time = max(0, current_time - 5)
                        end_time = min(video_duration, current_time + 10)
                        segments.append((start_time, end_time, diff / 100))
                
                prev_frame = frame
                
            except Exception as e:
                self.logger.debug(f"Scene detection error at {current_time}s: {e}")
            
            current_time += sample_interval
        
        return segments
    
    def _smart_sample_for_budget(self, segments: List[Tuple[float, float, float]], max_cost: float, video_duration: float) -> List[Tuple[float, float, float]]:
        """Stage 2: Smart sampling to stay within budget."""
        # Calculate how many AI analyses we can afford
        cost_per_analysis = 0.01  # Rough estimate
        max_analyses = int(max_cost / cost_per_analysis)
        
        self.logger.info(f"[BETA] Budget allows ~{max_analyses} AI analyses (${max_cost:.2f} budget)")
        
        if len(segments) <= max_analyses:
            return segments
        
        # Use intelligent sampling to pick the best segments
        # Strategy: Take highest scoring segments but ensure temporal distribution
        
        # Sort by score
        sorted_segments = sorted(segments, key=lambda x: x[2], reverse=True)
        
        # Ensure temporal distribution across the video
        time_buckets = {}
        bucket_size = video_duration / 10  # Divide video into 10 time buckets
        
        selected_segments = []
        
        # First pass: Take top segments from each time bucket
        for start, end, score in sorted_segments:
            bucket = int(start / bucket_size)
            
            if bucket not in time_buckets:
                time_buckets[bucket] = []
            
            time_buckets[bucket].append((start, end, score))
        
        # Take best segment from each bucket first
        for bucket_segments in time_buckets.values():
            if selected_segments and len(selected_segments) >= max_analyses:
                break
            if bucket_segments:
                selected_segments.append(bucket_segments[0])  # Highest scored in bucket
        
        # Second pass: Fill remaining slots with highest scores
        remaining_slots = max_analyses - len(selected_segments)
        if remaining_slots > 0:
            # Get segments not already selected
            selected_starts = {s[0] for s in selected_segments}
            remaining_segments = [s for s in sorted_segments if s[0] not in selected_starts]
            
            # Add highest scoring remaining segments
            selected_segments.extend(remaining_segments[:remaining_slots])
        
        self.logger.info(f"[BETA] Sampled {len(selected_segments)} segments for AI analysis")
        return selected_segments
    
    def _analyze_sampled_segments_beta(self, clip, segments: List[Tuple[float, float, float]], target_duration: int, prompt: str) -> List[Tuple[float, float]]:
        """Stage 3: AI analysis on pre-filtered segments only."""
        if not segments:
            return []
        
        # Use the existing AI analysis method but on pre-filtered segments
        segment_pairs = [(start, end) for start, end, score in segments]
        
        # Score with AI (this is where the cost is incurred)
        scored_segments = self._score_segments_with_ai(clip, segment_pairs, prompt, max_segments=len(segments))
        
        # Use existing selection logic
        final_segments = self._select_best_segments(scored_segments, target_duration)
        
        return final_segments

    def _merge_overlapping_segments(self, segments: List[Tuple[float, float, float]]) -> List[Tuple[float, float, float]]:
        """
        Merge overlapping segments to reduce redundancy.
        """
        if not segments:
            return []
        
        # Sort segments by start time
        segments.sort(key=lambda x: x[0])
        
        merged_segments = []
        current_start, current_end, current_score = segments[0]
        
        for start, end, score in segments[1:]:
            if start <= current_end:
                # Overlapping segment - extend the current segment
                current_end = max(current_end, end)
                current_score = max(current_score, score)
            else:
                # Non-overlapping segment - add the current segment to the list and start a new one
                merged_segments.append((current_start, current_end, current_score))
                current_start, current_end, current_score = start, end, score
        
        # Add the last segment
        merged_segments.append((current_start, current_end, current_score))
        
        return merged_segments
    
    def _calculate_position_boost(self, start: float, end: float, video_duration: float) -> float:
        """
        Calculate position boost based on segment position in the video.
        """
        if start <= 0:
            return 1.0  # Beginning of video is most valuable
        elif end >= video_duration:
            return 0.5  # End of video is less valuable
        else:
            return 1.0  # Middle of video is neutral

    def _analyze_segment_motion_enhanced(self, clip, start: float, end: float) -> float:
        """
        Enhanced motion analysis for a specific segment.
        """
        try:
            # Sample multiple frames across the segment
            segment_duration = end - start
            if segment_duration < 0.5:
                frame_times = [start + segment_duration/2]
            elif segment_duration < 2.0:
                frame_times = [start + 0.2, end - 0.2]
            else:
                # Sample 3-4 frames across the segment
                step = segment_duration / 4
                frame_times = [start + step, start + 2*step, start + 3*step]
            
            # Extract frames
            frames = []
            for t in frame_times:
                if 0 <= t < clip.duration:
                    frame = clip.get_frame(t)
                    if frame is not None:
                        frames.append(frame)
            
            if len(frames) < 2:
                return 0.3
            
            # Calculate motion across all frame pairs
            motion_scores = []
            for i in range(len(frames) - 1):
                motion = self._calculate_frame_motion([frames[i], frames[i+1]])
                motion_scores.append(motion)
            
            # Return average motion score
            avg_motion = sum(motion_scores) / len(motion_scores) if motion_scores else 0.3
            return min(avg_motion, 1.0)
            
        except Exception as e:
            self.logger.debug(f"Enhanced segment motion analysis failed: {e}")
            return 0.3

    def _create_emergency_highlights(self, clip, target_duration: int) -> List[Tuple[float, float]]:
        """
        Emergency fallback to create highlights when all other methods fail.
        Always produces some segments, even if they're not perfect.
        """
        self.logger.info("Creating emergency highlights - ensuring user always gets output")
        
        duration = clip.duration
        segments = []
        
        # Strategy 1: Distribute segments evenly across video timeline
        if duration > target_duration:
            # Create 3-5 segments distributed across the video
            num_segments = min(5, max(3, target_duration // 8))  # 3-5 segments of ~8s each
            segment_duration = min(8.0, target_duration / num_segments)
            
            # Distribute across timeline
            time_step = duration / (num_segments + 1)  # +1 to avoid endpoints
            
            for i in range(num_segments):
                start_time = time_step * (i + 1) - segment_duration / 2
                start_time = max(0, start_time)
                end_time = min(duration, start_time + segment_duration)
                
                # Adjust if we go beyond video end
                if end_time > duration:
                    end_time = duration
                    start_time = max(0, end_time - segment_duration)
                
                segments.append((start_time, end_time))
                self.logger.info(f"Emergency segment {i+1}: {start_time:.1f}-{end_time:.1f}s")
        else:
            # Video is shorter than target, just use the whole thing
            segments.append((0, duration))
        
        # Strategy 2: If we still have time to fill, add more segments
        total_used = sum(end - start for start, end in segments)
        if total_used < target_duration * 0.8 and len(segments) < 6:
            # Add some shorter segments in between
            remaining_time = target_duration - total_used
            extra_segments_needed = min(3, int(remaining_time // 4))
            
            for i in range(extra_segments_needed):
                # Find gaps between existing segments
                if len(segments) > 1:
                    gap_start = segments[i][1] + 1  # 1s after previous segment ends
                    gap_end = gap_start + min(4.0, remaining_time / extra_segments_needed)
                    
                    if gap_end < duration - 1:
                        segments.append((gap_start, gap_end))
                        self.logger.info(f"Emergency filler segment: {gap_start:.1f}-{gap_end:.1f}s")
        
        # Sort by timeline and trim to target duration
        segments.sort(key=lambda x: x[0])
        
        # Trim segments if we exceed target duration
        total_duration = 0
        final_segments = []
        for start, end in segments:
            segment_duration = end - start
            if total_duration + segment_duration <= target_duration:
                final_segments.append((start, end))
                total_duration += segment_duration
            else:
                # Add partial segment to reach target
                remaining = target_duration - total_duration
                if remaining > 1.0:  # Only add if at least 1 second
                    final_segments.append((start, start + remaining))
                break
        
        if not final_segments:
            # Absolute final fallback: just take the first 30 seconds
            final_segments = [(0, min(target_duration, duration))]
            self.logger.warning("Absolute fallback: using first portion of video")
        
        total_final = sum(end - start for start, end in final_segments)
        self.logger.info(f"Emergency highlights created: {len(final_segments)} segments, total: {total_final:.1f}s")
        
        return final_segments

    def _analyze_video_for_segment_similarities(self, clip, target_duration: int, 
                                              example_data: Dict[str, Any], 
                                              context_padding: float, 
                                              prompt: str) -> List[Tuple[float, float]]:
        """
        Analyze video to find segments similar to the provided example segment.
        This is the core method for segment-based highlight detection.
        """
        self.logger.info("Starting segment-based similarity analysis")
        
        # Step 1: Extract and analyze the example segment
        example_analysis = self._analyze_example_segment(clip, example_data, prompt)
        if not example_analysis:
            self.logger.error("Failed to analyze example segment")
            return []
        
        # Step 2: Calculate optimal sampling strategy with price optimization
        video_duration = clip.duration
        example_duration = example_analysis['duration']
        
        # SUPER CHEAP: Analyze way fewer frames and be much less picky
        if video_duration <= 300:  # 5 minutes or less
            sample_interval = 5.0  # Much cheaper
            max_samples = 20  # Cap at 20 frames max
        elif video_duration <= 1800:  # 30 minutes or less
            sample_interval = 10.0  # Very cheap
            max_samples = 30  # Cap at 30 frames max
        else:  # Longer videos
            sample_interval = 20.0  # Super cheap
            max_samples = 40  # Cap at 40 frames max
        
        # Adjust based on example segment length (longer examples need more careful analysis)
        if example_duration > 10:  # Long example segment
            sample_interval *= 0.8  # Slightly more frequent sampling
            max_samples = min(max_samples, int(video_duration / sample_interval))
        
        estimated_cost = max_samples * 0.01  # Rough estimate - much cheaper now!
        self.logger.info(f"COST-OPTIMIZED: every {sample_interval:.1f}s, max {max_samples} samples")
        self.logger.info(f"Estimated analysis cost: ~${estimated_cost:.2f} (MUCH CHEAPER!)")
        
        # Step 3: Find similar frames with budget controls (MUCH cheaper and less strict)
        similar_frames = self._find_similar_frames_optimized(clip, example_analysis, sample_interval, max_samples, prompt)
        
        if not similar_frames:
            self.logger.warning("No similar frames found, using fallback strategy")
            # FALLBACK: Use best guess segments from video to always deliver a result
            return self._create_fallback_highlight_reel(clip, target_duration, example_analysis, context_padding)
        
        self.logger.info(f"Found {len(similar_frames)} potentially similar frames")
        
        # Step 4: Group similar frames into segments
        segments = self._group_similar_frames_into_segments(similar_frames, video_duration)
        
        # Step 5: Extend segments with context padding
        extended_segments = self._extend_segments_with_context(segments, context_padding, video_duration)
        
        # Step 6: Select best segments to fit target duration
        final_segments = self._select_best_similarity_segments(extended_segments, target_duration)
        
        total_duration = sum(end - start for start, end in final_segments)
        self.logger.info(f"Selected {len(final_segments)} segments with total duration {total_duration:.1f}s")
        
        return final_segments
    
    def _create_fallback_highlight_reel(self, clip, target_duration: int, example_analysis: Dict[str, Any], context_padding: float) -> List[Tuple[float, float]]:
        """
        ALWAYS create a highlight reel even if no similar segments found.
        Use best guess based on video structure and the example segment timing.
        """
        self.logger.info("Creating fallback highlight reel - ALWAYS deliver a result!")
        
        video_duration = clip.duration
        example_start = example_analysis.get('start_time', 0)
        example_end = example_analysis.get('end_time', 5)
        example_duration = example_end - example_start
        
        # Strategy: Take segments from similar positions in the video timeline
        segments = []
        
        # Calculate how many segments we need
        segment_count = max(3, min(8, target_duration // max(3, example_duration)))
        segment_duration = min(target_duration / segment_count, example_duration * 1.5)
        
        # Distribute segments across the video timeline
        for i in range(int(segment_count)):
            # Place segments at similar relative positions to the example
            relative_position = example_start / video_duration if video_duration > 0 else 0.5
            
            # Add some variation to avoid taking the exact same moment
            position_variation = (i - segment_count/2) * 0.1  # Spread around the relative position
            target_position = max(0, min(1, relative_position + position_variation))
            
            start_time = target_position * (video_duration - segment_duration)
            end_time = start_time + segment_duration
            
            # Ensure we don't go beyond video bounds
            if end_time > video_duration:
                end_time = video_duration
                start_time = max(0, end_time - segment_duration)
            
            segments.append((start_time, end_time))
            self.logger.info(f"Fallback segment {i+1}: {start_time:.1f}s - {end_time:.1f}s")
        
        # Remove overlaps and ensure we hit target duration
        segments = self._clean_and_optimize_segments(segments, target_duration)
        
        total_duration = sum(end - start for start, end in segments)
        self.logger.info(f"Fallback highlight reel created: {len(segments)} segments, {total_duration:.1f}s total")
        
        return segments
    
    def _clean_and_optimize_segments(self, segments: List[Tuple[float, float]], target_duration: int) -> List[Tuple[float, float]]:
        """Clean up segments and ensure they hit the target duration."""
        if not segments:
            return []
        
        # Sort by start time
        segments = sorted(segments, key=lambda x: x[0])
        
        # Remove overlaps
        cleaned_segments = []
        for start, end in segments:
            if not cleaned_segments:
                cleaned_segments.append((start, end))
            else:
                last_start, last_end = cleaned_segments[-1]
                if start >= last_end:  # No overlap
                    cleaned_segments.append((start, end))
                else:  # Overlap - merge or skip
                    if end > last_end:  # Extend the last segment
                        cleaned_segments[-1] = (last_start, end)
        
        # Adjust to hit target duration
        current_duration = sum(end - start for start, end in cleaned_segments)
        
        if current_duration < target_duration and len(cleaned_segments) > 0:
            # Extend segments proportionally
            scale_factor = target_duration / current_duration
            scaled_segments = []
            for start, end in cleaned_segments:
                duration = end - start
                new_duration = duration * scale_factor
                scaled_segments.append((start, start + new_duration))
            cleaned_segments = scaled_segments
        
        elif current_duration > target_duration:
            # Trim segments to fit target
            running_total = 0
            trimmed_segments = []
            for start, end in cleaned_segments:
                duration = end - start
                if running_total + duration <= target_duration:
                    trimmed_segments.append((start, end))
                    running_total += duration
                else:
                    # Partial segment to complete target
                    remaining = target_duration - running_total
                    if remaining > 1:  # Only if at least 1 second left
                        trimmed_segments.append((start, start + remaining))
                    break
            cleaned_segments = trimmed_segments
        
        return cleaned_segments

    def _analyze_example_segment(self, clip, example_data: Dict[str, Any], prompt: str) -> Optional[Dict[str, Any]]:
        """
        Extract and analyze the example segment from the video.
        """
        try:
            start_time = example_data['start_time']
            end_time = example_data['end_time']
            description = example_data.get('description', '')
            
            self.logger.info(f"Analyzing example segment: {start_time:.1f}s - {end_time:.1f}s")
            
            # Extract the example segment
            example_segment = clip.subclip(start_time, end_time)
            segment_duration = end_time - start_time
            
            # Sample multiple frames from the segment for analysis
            sample_count = max(3, min(8, int(segment_duration * 2)))  # 2 frames per second, min 3, max 8
            frame_times = []
            
            if sample_count == 1:
                frame_times = [start_time + segment_duration / 2]
            else:
                step = segment_duration / (sample_count - 1)
                frame_times = [start_time + i * step for i in range(sample_count)]
            
            # Analyze each frame in the segment
            frame_analyses = []
            for i, frame_time in enumerate(frame_times):
                try:
                    frame = clip.get_frame(frame_time)
                    if frame is None:
                        continue
                    
                    # Save frame to temporary file
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                        from PIL import Image
                        img = Image.fromarray(frame)
                        img.save(temp_file.name, 'JPEG')
                        temp_path = temp_file.name
                    
                    try:
                        # Analyze this frame intensely
                        frame_analysis = self._analyze_segment_frame_intensely(temp_path, frame_time, description, prompt, i, sample_count)
                        if frame_analysis:
                            frame_analyses.append(frame_analysis)
                    finally:
                        try:
                            os.unlink(temp_path)
                        except:
                            pass
                            
                except Exception as e:
                    self.logger.debug(f"Error analyzing frame at {frame_time:.1f}s: {e}")
                    continue
            
            if not frame_analyses:
                self.logger.warning("No frames could be analyzed from example segment")
                return None
            
            # Combine analyses into segment summary
            segment_analysis = {
                'start_time': start_time,
                'end_time': end_time,
                'duration': segment_duration,
                'description': description,
                'frame_count': len(frame_analyses),
                'frame_analyses': frame_analyses,
                'combined_features': self._combine_frame_analyses(frame_analyses),
                'segment_type': 'user_selected_example'
            }
            
            example_segment.close()
            self.logger.info(f"Successfully analyzed example segment with {len(frame_analyses)} frames")
            return segment_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing example segment: {e}")
            return None

    def _analyze_example_image_intensely(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Analyze the example image intensely to understand what to look for.
        """
        try:
            # Save image to temporary file for analysis
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(image_data)
                temp_path = temp_file.name
            
            try:
                # Use the existing AI analysis method but with enhanced prompt
                enhanced_prompt = """
                Analyze this reference image EXTREMELY thoroughly. This image represents what the user wants to find in their video.
                
                Focus on:
                1. VISUAL ELEMENTS: Colors, shapes, objects, textures, lighting, composition
                2. ACTIONS: Any movements, gestures, activities, poses
                3. CONTEXT: Setting, environment, background elements
                4. PEOPLE: Number of people, their positioning, clothing, expressions
                5. OBJECTS: Specific items, tools, devices, toys, etc.
                6. STYLE: Visual style, quality, camera angle, perspective
                7. MOOD: Emotional tone, atmosphere, energy level
                
                Be extremely detailed and specific in your analysis. This analysis will be used to find similar moments in a video.
                
                Return JSON with keys: main_elements, visual_style, actions_detected, context_clues, distinctive_features, search_keywords
                """
                
                analysis = self._call_enhanced_ai_analysis(temp_path, enhanced_prompt)
                
                if analysis:
                    # Enhance the analysis with additional processing
                    analysis['similarity_keywords'] = self._extract_similarity_keywords(analysis)
                    return analysis
                else:
                    self.logger.warning("AI analysis of example image failed")
                    return None
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Error analyzing example image: {e}")
            return None

    def _extract_similarity_keywords(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Extract keywords from the analysis that will be useful for similarity matching.
        """
        keywords = []
        
        # Extract from different analysis fields
        for field in ['main_elements', 'actions_detected', 'context_clues', 'distinctive_features']:
            if field in analysis and analysis[field]:
                text = str(analysis[field]).lower()
                # Simple keyword extraction - could be enhanced with NLP
                words = text.split()
                keywords.extend([word.strip('.,!?') for word in words if len(word) > 3])
        
        # Remove duplicates and return
        return list(set(keywords))

    def _find_similar_frames_optimized(self, clip, example_analysis: Dict[str, Any], 
                                      sample_interval: float, max_samples: int, prompt: str) -> List[Tuple[float, float]]:
        """
        Find frames in the video that are similar to the example segment with budget optimization.
        Returns list of (timestamp, similarity_score) tuples.
        """
        similar_frames = []
        video_duration = clip.duration
        
        # Sample frames across the video with budget limits
        current_time = 0
        frame_count = 0
        samples_processed = 0
        
        while current_time < video_duration and samples_processed < max_samples:
            try:
                # Extract frame at current time
                frame = clip.get_frame(current_time)
                if frame is None:
                    current_time += sample_interval
                    continue
                
                # Save frame to temporary file for analysis
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                    from PIL import Image
                    img = Image.fromarray(frame)
                    img.save(temp_file.name, 'JPEG')
                    temp_path = temp_file.name
                
                try:
                    # Analyze frame for similarity to example
                    similarity_score = self._calculate_frame_similarity_to_example(
                        temp_path, example_analysis, prompt
                    )
                    
                    if similarity_score > 0.3:  # Much lower threshold - accept "close enough"
                        similar_frames.append((current_time, similarity_score))
                        self.logger.debug(f"Similar frame found at {current_time:.1f}s (score: {similarity_score:.2f})")
                    
                    frame_count += 1
                    samples_processed += 1
                    
                    if frame_count % 20 == 0:
                        progress = (samples_processed / max_samples) * 100
                        self.logger.info(f"Progress: {progress:.1f}% - Analyzed {frame_count} frames, found {len(similar_frames)} similar frames")
                        
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                
            except Exception as e:
                self.logger.debug(f"Error analyzing frame at {current_time:.1f}s: {e}")
            
            current_time += sample_interval
        
        budget_status = "within budget" if samples_processed < max_samples else "budget limit reached"
        self.logger.info(f"Completed frame analysis ({budget_status}): {frame_count} frames analyzed, {len(similar_frames)} similar frames found")
        return similar_frames

    def _calculate_frame_similarity_to_example(self, frame_path: str, 
                                             example_analysis: Dict[str, Any], 
                                             prompt: str) -> float:
        """
        Calculate how similar a frame is to the example segment.
        """
        try:
            # Create a similarity-focused prompt based on segment analysis
            combined_features = example_analysis.get('combined_features', {})
            segment_summary = combined_features.get('segment_summary', 'analyzed segment')
            key_search_terms = combined_features.get('key_search_terms', [])
            
            # Build description from segment analysis
            if key_search_terms:
                example_description = f"{segment_summary}. Key elements: {', '.join(key_search_terms[:8])}"
            else:
                example_description = segment_summary
            
            similarity_prompt = f"""
            Compare this frame to the reference example. The reference example contains: {example_description}
            
            Rate the similarity on a scale of 0-10 where:
            - 10: Nearly identical or very similar scene/action/composition
            - 8-9: Strong similarity in key elements (same action, similar objects, similar setting)
            - 6-7: Moderate similarity (some matching elements but different context)
            - 4-5: Some similarity (few matching elements)
            - 0-3: Little to no similarity
            
            Focus on: {prompt if prompt else "visual similarity, actions, objects, and context"}
            
            Return JSON with: {{"similarity_score": number, "matching_elements": "description", "differences": "description"}}
            """
            
            # Use AI to analyze similarity
            analysis = self._call_enhanced_ai_analysis(frame_path, similarity_prompt)
            
            if analysis and 'similarity_score' in analysis:
                score = float(analysis['similarity_score']) / 10.0  # Convert to 0-1 scale
                return min(max(score, 0.0), 1.0)  # Clamp to 0-1 range
            else:
                return 0.0
                
        except Exception as e:
            self.logger.debug(f"Error calculating frame similarity: {e}")
            return 0.0

    def _group_similar_frames_into_segments(self, similar_frames: List[Tuple[float, float]], 
                                          video_duration: float) -> List[Tuple[float, float, float]]:
        """
        Group nearby similar frames into continuous segments.
        Returns list of (start_time, end_time, avg_score) tuples.
        """
        if not similar_frames:
            return []
        
        # Sort by timestamp
        similar_frames.sort(key=lambda x: x[0])
        
        segments = []
        current_start = similar_frames[0][0]
        current_end = similar_frames[0][0]
        current_scores = [similar_frames[0][1]]
        
        gap_threshold = 3.0  # Seconds - frames within this gap are considered part of the same segment
        
        for i in range(1, len(similar_frames)):
            timestamp, score = similar_frames[i]
            
            if timestamp - current_end <= gap_threshold:
                # Continue current segment
                current_end = timestamp
                current_scores.append(score)
            else:
                # Start new segment
                avg_score = sum(current_scores) / len(current_scores)
                segments.append((current_start, current_end, avg_score))
                
                current_start = timestamp
                current_end = timestamp
                current_scores = [score]
        
        # Add the last segment
        if current_scores:
            avg_score = sum(current_scores) / len(current_scores)
            segments.append((current_start, current_end, avg_score))
        
        self.logger.info(f"Grouped {len(similar_frames)} similar frames into {len(segments)} segments")
        return segments

    def _extend_segments_with_context(self, segments: List[Tuple[float, float, float]], 
                                    context_padding: float, 
                                    video_duration: float) -> List[Tuple[float, float, float]]:
        """
        Extend segments with context padding before each scene.
        """
        extended_segments = []
        
        for start, end, score in segments:
            # Add context padding before the segment
            extended_start = max(0, start - context_padding)
            
            # Ensure we don't extend beyond video duration
            extended_end = min(video_duration, end)
            
            # Ensure minimum segment length
            if extended_end - extended_start < 1.0:
                extended_end = min(video_duration, extended_start + 1.0)
            
            extended_segments.append((extended_start, extended_end, score))
        
        self.logger.info(f"Extended {len(segments)} segments with {context_padding}s context padding")
        return extended_segments

    def _select_best_similarity_segments(self, segments: List[Tuple[float, float, float]], 
                                       target_duration: int) -> List[Tuple[float, float]]:
        """
        Select the best segments to fit the target duration.
        """
        if not segments:
            return []
        
        # Sort segments by score (descending)
        segments.sort(key=lambda x: x[2], reverse=True)
        
        selected_segments = []
        total_duration = 0
        
        for start, end, score in segments:
            segment_duration = end - start
            
            if total_duration + segment_duration <= target_duration:
                selected_segments.append((start, end))
                total_duration += segment_duration
                self.logger.debug(f"Selected segment {start:.1f}-{end:.1f}s (score: {score:.2f})")
            else:
                # Check if we can fit a trimmed version of this segment
                remaining_duration = target_duration - total_duration
                if remaining_duration > 2.0:  # Only if we have at least 2 seconds left
                    # Take the beginning of this segment
                    selected_segments.append((start, start + remaining_duration))
                    total_duration = target_duration
                    self.logger.debug(f"Selected trimmed segment {start:.1f}-{start + remaining_duration:.1f}s")
                break
        
        # Sort final segments by timeline order
        selected_segments.sort(key=lambda x: x[0])
        
        self.logger.info(f"Selected {len(selected_segments)} segments totaling {total_duration:.1f}s")
        return selected_segments

    def _analyze_segment_frame_intensely(self, frame_path: str, frame_time: float, 
                                       description: str, prompt: str, 
                                       frame_index: int, total_frames: int) -> Optional[Dict[str, Any]]:
        """
        Analyze a single frame from the example segment intensely.
        """
        try:
            # Create enhanced prompt for segment frame analysis
            enhanced_prompt = f"""
            Analyze this frame from a user-selected example segment (frame {frame_index + 1} of {total_frames}).
            
            CONTEXT:
            - This frame is from timestamp {frame_time:.1f}s in the video
            - User description: "{description if description else 'No description provided'}"
            - Additional context: "{prompt if prompt else 'General highlight analysis'}"
            
            ANALYSIS FOCUS - This frame represents what the user wants to find more of:
            1. VISUAL CHARACTERISTICS: Lighting, colors, composition, camera angle, image quality
            2. SUBJECTS: People, objects, characters - their positioning, appearance, clothing, expressions
            3. ACTIONS: Any movements, gestures, activities, interactions happening
            4. ENVIRONMENT: Setting, background, indoor/outdoor, time of day
            5. STYLE: Gaming interface, real-world scene, artistic style, video quality
            6. EMOTIONAL TONE: Mood, energy level, atmosphere
            7. TECHNICAL ELEMENTS: Screen elements, UI, effects, overlays
            
            IMPORTANT: Be extremely detailed and specific. This analysis will be used to find similar moments throughout the video.
            Focus on what makes this moment unique and interesting to the user.
            
            Return JSON with keys: visual_elements, subjects, actions, environment, style, mood, technical_aspects, uniqueness_factors, search_keywords
            """
            
            analysis = self._call_enhanced_ai_analysis(frame_path, enhanced_prompt)
            
            if analysis:
                # Add frame-specific metadata
                analysis['frame_time'] = frame_time
                analysis['frame_index'] = frame_index
                analysis['analysis_timestamp'] = datetime.now().isoformat()
                return analysis
            else:
                self.logger.warning(f"AI analysis failed for frame at {frame_time:.1f}s")
                return None
                
        except Exception as e:
            self.logger.debug(f"Error analyzing segment frame at {frame_time:.1f}s: {e}")
            return None

    def _combine_frame_analyses(self, frame_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine multiple frame analyses into a unified segment understanding.
        """
        try:
            if not frame_analyses:
                return {}
            
            combined = {
                'dominant_visual_elements': [],
                'consistent_subjects': [],
                'primary_actions': [],
                'environment_type': '',
                'overall_style': '',
                'mood_indicators': [],
                'technical_patterns': [],
                'key_search_terms': [],
                'segment_summary': '',
                'confidence_score': 0.0
            }
            
            # Collect all elements from each frame
            all_elements = {}
            for analysis in frame_analyses:
                for key in ['visual_elements', 'subjects', 'actions', 'environment', 'style', 'mood', 'technical_aspects']:
                    if key in analysis and analysis[key]:
                        text = str(analysis[key]).lower()
                        words = text.split()
                        for word in words:
                            clean_word = word.strip('.,!?()[]{}')
                            if len(clean_word) > 3:
                                all_elements[clean_word] = all_elements.get(clean_word, 0) + 1
            
            # Find most frequent elements (appear in multiple frames)
            frame_count = len(frame_analyses)
            frequent_threshold = max(1, frame_count // 2)  # Must appear in at least half the frames
            
            frequent_elements = {k: v for k, v in all_elements.items() if v >= frequent_threshold}
            combined['key_search_terms'] = list(frequent_elements.keys())
            
            # Create segment summary
            if frequent_elements:
                top_elements = sorted(frequent_elements.keys(), key=lambda x: frequent_elements[x], reverse=True)[:10]
                combined['segment_summary'] = f"Segment featuring: {', '.join(top_elements[:5])}"
                combined['confidence_score'] = min(1.0, len(frequent_elements) / 10.0)
            else:
                combined['segment_summary'] = "Analyzed segment with unique characteristics"
                combined['confidence_score'] = 0.5
            
            self.logger.debug(f"Combined analysis: {len(frequent_elements)} frequent elements, confidence: {combined['confidence_score']:.2f}")
            return combined
            
        except Exception as e:
            self.logger.warning(f"Error combining frame analyses: {e}")
            return {'segment_summary': 'Analysis combination failed', 'confidence_score': 0.3}
 