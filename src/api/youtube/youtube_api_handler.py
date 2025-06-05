"""
YouTube API handler for posting content using the official YouTube Data API v3.
Supports video uploads, YouTube Shorts, playlists, and channel management.
"""
import os
import json
import logging
import requests
import mimetypes
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from PySide6.QtCore import QObject, Signal

try:
    import googleapiclient.discovery
    import googleapiclient.errors
    from googleapiclient.http import MediaFileUpload
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False
    logging.warning("Google APIs not available. Install google-auth, google-auth-oauthlib, and google-api-python-client")

from ...config import constants as const

# YouTube API scopes
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.readonly'
]

class YouTubeAPISignals(QObject):
    """Signals for YouTube API operations."""
    upload_started = Signal(str)  # platform
    upload_progress = Signal(str, int)  # message, percentage
    upload_success = Signal(str, dict)  # platform, response_data
    upload_error = Signal(str, str)  # platform, error_message
    status_update = Signal(str)

class YouTubeAPIHandler:
    """Handler for YouTube API operations."""
    
    def __init__(self):
        """Initialize the YouTube API handler."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.signals = YouTubeAPISignals()
        self.credentials = None
        self.youtube_service = None
        self.credentials_file = os.path.join(const.ROOT_DIR, 'youtube_credentials.json')
        self.token_file = os.path.join(const.ROOT_DIR, 'youtube_token.json')
        
        if GOOGLE_APIS_AVAILABLE:
            self._load_credentials()
        else:
            self.logger.warning("Google APIs not available. YouTube integration disabled.")
    
    def _load_credentials(self) -> bool:
        """Load YouTube credentials and initialize service."""
        try:
            if not GOOGLE_APIS_AVAILABLE:
                return False
            
            # Check if we have saved credentials
            if os.path.exists(self.token_file):
                self.credentials = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            
            # If there are no (valid) credentials available, let the user log in
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    if os.path.exists(self.credentials_file):
                        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                        self.credentials = flow.run_local_server(port=0)
                    else:
                        self.logger.warning("YouTube credentials file not found")
                        return False
                
                # Save the credentials for the next run
                with open(self.token_file, 'w') as token:
                    token.write(self.credentials.to_json())
            
            # Build the YouTube service
            self.youtube_service = googleapiclient.discovery.build('youtube', 'v3', credentials=self.credentials)
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading YouTube credentials: {e}")
            return False
    
    def save_credentials(self, credentials_data: Dict[str, Any]) -> bool:
        """Save YouTube OAuth2 client credentials to file."""
        try:
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(credentials_data, f, indent=4)
            
            self.logger.info("YouTube credentials saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error saving YouTube credentials: {e}")
            return False
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test the YouTube API connection."""
        try:
            if not GOOGLE_APIS_AVAILABLE:
                return False, "Google APIs not installed"
            
            if not self.youtube_service:
                return False, "YouTube service not initialized"
            
            # Test with channels list endpoint
            request = self.youtube_service.channels().list(
                part="snippet,statistics",
                mine=True
            )
            response = request.execute()
            
            if 'items' in response and len(response['items']) > 0:
                channel = response['items'][0]
                channel_title = channel['snippet']['title']
                subscriber_count = channel['statistics'].get('subscriberCount', '0')
                return True, f"Connected to YouTube channel: {channel_title} ({subscriber_count} subscribers)"
            else:
                return False, "No YouTube channel found for this account"
                
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    def post_media(self, media_path: str, caption: str = "", is_video: bool = False, 
                   is_short: bool = False, **kwargs) -> Tuple[bool, str]:
        """
        Post media to YouTube.
        
        Args:
            media_path: Path to the media file
            caption: Caption/description for the video
            is_video: Whether the media is a video (YouTube only supports videos)
            is_short: Whether this is a YouTube Short
            **kwargs: Additional parameters (title, tags, category, privacy)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            platform_name = "youtube_shorts" if is_short else "youtube"
            self.signals.upload_started.emit(platform_name)
            self.signals.status_update.emit(f"Starting {platform_name} upload...")
            
            if not GOOGLE_APIS_AVAILABLE:
                error_msg = "Google APIs not installed. Please install required packages."
                self.signals.upload_error.emit(platform_name, error_msg)
                return False, error_msg
            
            if not self.youtube_service:
                error_msg = "YouTube not authenticated. Please connect your account first."
                self.signals.upload_error.emit(platform_name, error_msg)
                return False, error_msg
            
            if not os.path.exists(media_path):
                error_msg = f"Media file not found: {media_path}"
                self.signals.upload_error.emit(platform_name, error_msg)
                return False, error_msg
            
            # YouTube only supports video content
            if not is_video:
                error_msg = "YouTube only supports video content. Please select a video file."
                self.signals.upload_error.emit(platform_name, error_msg)
                return False, error_msg
            
            # Validate media file
            valid, validation_msg = self.validate_media_file(media_path, is_short)
            if not valid:
                self.signals.upload_error.emit(platform_name, validation_msg)
                return False, validation_msg
            
            return self._upload_video(media_path, caption, is_short, **kwargs)
                
        except Exception as e:
            platform_name = "youtube_shorts" if is_short else "youtube"
            error_msg = f"Error posting to YouTube: {str(e)}"
            self.logger.exception(error_msg)
            self.signals.upload_error.emit(platform_name, error_msg)
            return False, error_msg
    
    def _upload_video(self, media_path: str, description: str, is_short: bool = False, 
                      **kwargs) -> Tuple[bool, str]:
        """Upload video to YouTube."""
        try:
            platform_name = "youtube_shorts" if is_short else "youtube"
            self.signals.upload_progress.emit(f"Preparing {platform_name} video upload...", 10)
            
            # Extract additional parameters
            title = kwargs.get('title', os.path.splitext(os.path.basename(media_path))[0])
            tags = kwargs.get('tags', [])
            category_id = kwargs.get('category_id', '22')  # People & Blogs
            privacy_status = kwargs.get('privacy_status', 'public')
            thumbnail_path = kwargs.get('thumbnail_path')
            
            # For YouTube Shorts, add #Shorts to title if not present
            if is_short and '#Shorts' not in title:
                title = f"{title} #Shorts"
            
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': title[:100],  # YouTube title limit
                    'description': description[:5000],  # YouTube description limit
                    'tags': tags[:500] if isinstance(tags, list) else [],  # YouTube tags limit
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Add shorts-specific metadata
            if is_short:
                body['snippet']['description'] = f"{description}\n\n#Shorts" if description else "#Shorts"
            
            self.signals.upload_progress.emit(f"Uploading video to {platform_name}...", 25)
            
            # Create media upload object
            media = MediaFileUpload(
                media_path,
                mimetype=None,  # Auto-detect
                resumable=True,
                chunksize=1024*1024  # 1MB chunks
            )
            
            # Insert video
            insert_request = self.youtube_service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            video_id = None
            response = None
            
            # Execute upload with progress tracking
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    progress = int(status.progress() * 60) + 25  # 25-85% for upload
                    self.signals.upload_progress.emit(f"Uploading... {progress-25}% complete", progress)
            
            if 'id' in response:
                video_id = response['id']
                self.signals.upload_progress.emit("Video uploaded successfully!", 85)
                
                # Upload thumbnail if provided
                if thumbnail_path and os.path.exists(thumbnail_path):
                    self.signals.upload_progress.emit("Uploading thumbnail...", 90)
                    self._upload_thumbnail(video_id, thumbnail_path)
                
                self.signals.upload_progress.emit(f"{platform_name} upload complete!", 100)
                
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                
                self.signals.upload_success.emit(platform_name, {
                    'video_id': video_id,
                    'video_url': video_url,
                    'title': title,
                    'is_short': is_short,
                    'platform': platform_name
                })
                
                return True, f"Successfully uploaded to YouTube: {video_url}"
            else:
                error_msg = "Upload failed: No video ID returned"
                self.signals.upload_error.emit(platform_name, error_msg)
                return False, error_msg
                
        except Exception as e:
            platform_name = "youtube_shorts" if is_short else "youtube"
            error_msg = f"Upload error: {str(e)}"
            self.logger.error(error_msg)
            self.signals.upload_error.emit(platform_name, error_msg)
            return False, error_msg
    
    def _upload_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """Upload custom thumbnail for video."""
        try:
            media = MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
            request = self.youtube_service.thumbnails().set(
                videoId=video_id,
                media_body=media
            )
            request.execute()
            self.logger.info(f"Thumbnail uploaded for video {video_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to upload thumbnail: {e}")
            return False
    
    def create_playlist(self, title: str, description: str = "", privacy: str = "public") -> Tuple[bool, str]:
        """Create a new YouTube playlist."""
        try:
            if not GOOGLE_APIS_AVAILABLE or not self.youtube_service:
                return False, "YouTube service not available"
            
            body = {
                'snippet': {
                    'title': title,
                    'description': description
                },
                'status': {
                    'privacyStatus': privacy
                }
            }
            
            request = self.youtube_service.playlists().insert(
                part='snippet,status',
                body=body
            )
            response = request.execute()
            
            playlist_id = response['id']
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
            
            return True, f"Playlist created: {playlist_url}"
            
        except Exception as e:
            return False, f"Failed to create playlist: {str(e)}"
    
    def add_to_playlist(self, video_id: str, playlist_id: str) -> Tuple[bool, str]:
        """Add video to playlist."""
        try:
            body = {
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }
            
            request = self.youtube_service.playlistItems().insert(
                part='snippet',
                body=body
            )
            request.execute()
            
            return True, "Video added to playlist successfully"
            
        except Exception as e:
            return False, f"Failed to add video to playlist: {str(e)}"
    
    def get_channel_analytics(self) -> Dict[str, Any]:
        """Get basic channel analytics."""
        try:
            # Get channel info
            channels_request = self.youtube_service.channels().list(
                part="snippet,statistics",
                mine=True
            )
            channels_response = channels_request.execute()
            
            if not channels_response['items']:
                return {}
            
            channel = channels_response['items'][0]
            stats = channel['statistics']
            
            return {
                'channel_title': channel['snippet']['title'],
                'subscriber_count': int(stats.get('subscriberCount', 0)),
                'video_count': int(stats.get('videoCount', 0)),
                'view_count': int(stats.get('viewCount', 0)),
                'custom_url': channel['snippet'].get('customUrl', ''),
                'description': channel['snippet'].get('description', '')
            }
            
        except Exception as e:
            self.logger.error(f"Error getting channel analytics: {e}")
            return {}
    
    def validate_media_file(self, media_path: str, is_short: bool = False) -> Tuple[bool, str]:
        """Validate media file for YouTube upload."""
        try:
            if not os.path.exists(media_path):
                return False, "File not found"
            
            # Check file size (2GB limit for YouTube)
            file_size = os.path.getsize(media_path)
            max_size = 2 * 1024 * 1024 * 1024  # 2GB
            if file_size > max_size:
                return False, f"File too large. Maximum size is 2GB, got {file_size / (1024**3):.1f}GB"
            
            # Check file type
            mime_type, _ = mimetypes.guess_type(media_path)
            if not mime_type or not mime_type.startswith('video/'):
                return False, "Invalid video format. Please use MP4, MOV, AVI, WMV, or other supported video formats"
            
            # Additional validation for YouTube Shorts
            if is_short:
                # Import video processing library to check duration
                try:
                    from moviepy.editor import VideoFileClip
                    with VideoFileClip(media_path) as clip:
                        duration = clip.duration
                        if duration > 60:
                            return False, f"YouTube Shorts must be 60 seconds or less. Video is {duration:.1f} seconds"
                        
                        # Check aspect ratio for Shorts (should be vertical)
                        if clip.w >= clip.h:
                            self.logger.warning("YouTube Shorts work best with vertical videos (9:16 aspect ratio)")
                        
                except ImportError:
                    self.logger.warning("MoviePy not available for duration checking")
                except Exception as e:
                    self.logger.warning(f"Could not check video properties: {e}")
            
            return True, "Valid video file"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_posting_status(self) -> Dict[str, Any]:
        """Get current posting status and capabilities."""
        return {
            'platform': 'youtube',
            'authenticated': self.youtube_service is not None,
            'supports_video': True,
            'supports_image': False,
            'supports_shorts': True,
            'max_video_size_gb': 2,
            'max_title_length': 100,
            'max_description_length': 5000,
            'apis_available': GOOGLE_APIS_AVAILABLE
        }
    
    def logout(self) -> None:
        """Logout from YouTube (clear credentials)."""
        try:
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
            self.credentials = None
            self.youtube_service = None
            self.logger.info("YouTube logout successful")
        except Exception as e:
            self.logger.error(f"Error during YouTube logout: {e}") 