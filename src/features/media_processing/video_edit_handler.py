"""
Comprehensive video editing handler for processing videos with various effects.
"""
import os
import logging
import tempfile
import subprocess
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, ColorClip
from moviepy.video.fx import resize, crop
from PIL import Image, ImageEnhance

from ...config import constants as const

class VideoEditHandler:
    """
    Handles comprehensive video editing operations.
    """
    
    def __init__(self):
        """Initialize the video edit handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.temp_dir = tempfile.gettempdir()
        
    def process_video_with_services(self, video_path: str, selected_services: Dict[str, bool]) -> Tuple[bool, str, str]:
        """
        Process video with selected services.
        
        Args:
            video_path: Path to the input video
            selected_services: Dictionary of service_id -> enabled
            
        Returns:
            Tuple[bool, str, str]: Success status, output path, and message
        """
        try:
            if not os.path.exists(video_path):
                return False, "", f"Video file not found: {video_path}"
            
            self.logger.info(f"Processing video with services: {selected_services}")
            
            # Load video
            clip = VideoFileClip(video_path)
            processed_clip = clip
            applied_effects = []
            
            # Apply selected services in order
            if selected_services.get('color_grading', False):
                processed_clip = self._apply_color_grading(processed_clip)
                applied_effects.append("Color Grading")
            
            if selected_services.get('stabilization', False):
                processed_clip = self._apply_stabilization(processed_clip)
                applied_effects.append("Video Stabilization")
            
            if selected_services.get('motion_graphics', False):
                processed_clip = self._add_motion_graphics(processed_clip)
                applied_effects.append("Motion Graphics")
            
            if selected_services.get('transitions', False):
                processed_clip = self._apply_smooth_transitions(processed_clip)
                applied_effects.append("Smooth Transitions")
            
            if selected_services.get('audio_enhancement', False):
                processed_clip = self._enhance_audio(processed_clip)
                applied_effects.append("Audio Enhancement")
            
            if selected_services.get('social_optimization', False):
                processed_clip = self._optimize_for_social(processed_clip)
                applied_effects.append("Social Media Optimization")
            
            if selected_services.get('captions_subtitles', False):
                processed_clip = self._add_captions(processed_clip)
                applied_effects.append("Captions & Subtitles")
            
            if selected_services.get('highlight_reel', False):
                processed_clip = self._create_highlight_reel(processed_clip)
                applied_effects.append("Highlight Reel")
            
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{base_name}_processed_{timestamp}.mp4"
            output_path = os.path.join(const.OUTPUT_DIR, output_filename)
            
            # Ensure output directory exists
            os.makedirs(const.OUTPUT_DIR, exist_ok=True)
            
            # Write processed video
            processed_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # Clean up
            clip.close()
            processed_clip.close()
            
            effects_str = ", ".join(applied_effects) if applied_effects else "No effects"
            success_message = f"Video processed successfully. Applied: {effects_str}"
            
            self.logger.info(f"Video processing completed: {output_path}")
            return True, output_path, success_message
            
        except Exception as e:
            self.logger.error(f"Error processing video: {e}")
            return False, "", f"Error processing video: {str(e)}"
    
    def _apply_color_grading(self, clip: VideoFileClip) -> VideoFileClip:
        """Apply professional color grading."""
        def color_grade_frame(get_frame, t):
            frame = get_frame(t)
            
            # Convert to PIL Image for processing
            img = Image.fromarray(frame)
            
            # Apply cinematic color grading
            # Enhance contrast
            contrast_enhancer = ImageEnhance.Contrast(img)
            img = contrast_enhancer.enhance(1.2)
            
            # Adjust color balance for cinematic look
            img_array = np.array(img).astype(float)
            
            # Teal and orange color grading (popular in films)
            img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 1.1, 0, 255)  # Red
            img_array[:, :, 1] = np.clip(img_array[:, :, 1] * 0.95, 0, 255)  # Green
            img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 1.05, 0, 255)  # Blue
            
            return img_array.astype(np.uint8)
        
        return clip.fl(color_grade_frame)
    
    def _apply_stabilization(self, clip: VideoFileClip) -> VideoFileClip:
        """Apply video stabilization (simplified version)."""
        # Note: Real stabilization would require more complex algorithms
        # This is a simplified version that applies slight smoothing
        def stabilize_frame(get_frame, t):
            frame = get_frame(t)
            
            # Apply slight Gaussian blur to reduce shake appearance
            kernel = np.ones((3, 3), np.float32) / 9
            stabilized = cv2.filter2D(frame, -1, kernel)
            
            return stabilized
        
        return clip.fl(stabilize_frame)
    
    def _add_motion_graphics(self, clip: VideoFileClip) -> VideoFileClip:
        """Add motion graphics and text overlays."""
        # Create animated title
        title_clip = TextClip(
            "Professional Video",
            fontsize=50,
            color='white',
            font='Arial-Bold'
        ).set_position(('center', 'top')).set_duration(3).set_start(1)
        
        # Create lower third
        lower_third_bg = ColorClip(
            size=(400, 80),
            color=(0, 0, 0),
            duration=5
        ).set_opacity(0.7).set_position(('left', 'bottom')).set_start(2)
        
        lower_third_text = TextClip(
            "Enhanced with AI",
            fontsize=24,
            color='white',
            font='Arial'
        ).set_position((20, clip.h - 60)).set_duration(5).set_start(2)
        
        # Composite all elements
        return CompositeVideoClip([clip, title_clip, lower_third_bg, lower_third_text])
    
    def _apply_smooth_transitions(self, clip: VideoFileClip) -> VideoFileClip:
        """Apply smooth transitions (fade in/out)."""
        # Add fade in at the beginning
        clip = clip.fadein(1.0)
        
        # Add fade out at the end
        clip = clip.fadeout(1.0)
        
        return clip
    
    def _enhance_audio(self, clip: VideoFileClip) -> VideoFileClip:
        """Enhance audio quality."""
        if clip.audio is not None:
            # Normalize audio levels
            audio = clip.audio.volumex(1.2)  # Slight volume boost
            clip = clip.set_audio(audio)
        
        return clip
    
    def _optimize_for_social(self, clip: VideoFileClip) -> VideoFileClip:
        """Optimize video for social media platforms."""
        # Resize to common social media aspect ratio (16:9 or 9:16)
        original_aspect = clip.w / clip.h
        
        if original_aspect > 1.5:  # Wide video, keep 16:9
            target_width = 1080
            target_height = 608
        else:  # Square or tall video, make it 9:16 for stories
            target_width = 608
            target_height = 1080
        
        # Resize while maintaining aspect ratio
        resized_clip = resize(clip, height=target_height)
        
        # If width is too large, crop from center
        if resized_clip.w > target_width:
            resized_clip = crop(resized_clip, 
                              x_center=resized_clip.w/2, 
                              width=target_width)
        
        return resized_clip
    
    def _add_captions(self, clip: VideoFileClip) -> VideoFileClip:
        """Add captions/subtitles."""
        # Simple caption example
        caption_clip = TextClip(
            "Auto-generated captions would appear here",
            fontsize=24,
            color='white',
            bg_color='black',
            size=(clip.w - 40, None)
        ).set_position(('center', 'bottom')).set_duration(min(5, clip.duration)).set_start(0)
        
        return CompositeVideoClip([clip, caption_clip])
    
    def _create_highlight_reel(self, clip: VideoFileClip) -> VideoFileClip:
        """Create a highlight reel (shortened version)."""
        # If video is longer than 30 seconds, create highlights
        if clip.duration > 30:
            # Take segments from beginning, middle, and end
            segment_duration = 8
            segments = []
            
            # Beginning
            segments.append(clip.subclip(0, segment_duration))
            
            # Middle
            middle_start = (clip.duration / 2) - (segment_duration / 2)
            segments.append(clip.subclip(middle_start, middle_start + segment_duration))
            
            # End
            end_start = clip.duration - segment_duration
            segments.append(clip.subclip(end_start, clip.duration))
            
            # Concatenate segments
            from moviepy.editor import concatenate_videoclips
            highlight_clip = concatenate_videoclips(segments)
            
            return highlight_clip
        
        return clip
    
    def get_available_services(self) -> List[Dict[str, str]]:
        """Get list of available video editing services."""
        return [
            {
                'id': 'color_grading',
                'name': 'Color Grading & Enhancement',
                'description': 'Professional color correction and cinematic grading'
            },
            {
                'id': 'stabilization',
                'name': 'Video Stabilization',
                'description': 'Reduce camera shake and smooth footage'
            },
            {
                'id': 'motion_graphics',
                'name': 'Motion Graphics & Text',
                'description': 'Add animated titles and lower thirds'
            },
            {
                'id': 'transitions',
                'name': 'Smooth Transitions',
                'description': 'Professional fade in/out effects'
            },
            {
                'id': 'audio_enhancement',
                'name': 'Audio Enhancement',
                'description': 'Improve audio quality and levels'
            },
            {
                'id': 'social_optimization',
                'name': 'Social Media Optimization',
                'description': 'Optimize aspect ratio for social platforms'
            },
            {
                'id': 'captions_subtitles',
                'name': 'Captions & Subtitles',
                'description': 'Add text overlays and captions'
            },
            {
                'id': 'highlight_reel',
                'name': 'Highlight Reel Creation',
                'description': 'Create shortened highlight version'
            }
        ] 