import asyncio
import io
import uuid
from typing import Optional, Tuple
from datetime import datetime, timedelta

from google.cloud import storage
from google.cloud.exceptions import NotFound
from PIL import Image
import magic

from crow_eye_api.core.config import settings


class GoogleCloudStorageService:
    """Service for handling Google Cloud Storage operations."""
    
    def __init__(self):
        """Initialize GCS client."""
        try:
            self.client = storage.Client(project=settings.GOOGLE_CLOUD_PROJECT)
            self.bucket_name = settings.GOOGLE_CLOUD_STORAGE_BUCKET
            self.bucket = self.client.bucket(self.bucket_name)
        except Exception as e:
            print(f"Warning: Google Cloud Storage not configured: {e}")
            self.client = None
            self.bucket = None
    
    async def upload_file(
        self, 
        file_content: bytes, 
        filename: str, 
        content_type: str,
        user_id: int
    ) -> Tuple[str, dict]:
        """
        Upload file to Google Cloud Storage.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            content_type: MIME type of the file
            user_id: ID of the uploading user
            
        Returns:
            Tuple of (blob_name, file_metadata)
        """
        if not self.client or not self.bucket:
            raise Exception("Google Cloud Storage not configured. Please check your .env file and authentication.")
        # Generate unique filename
        file_extension = filename.split('.')[-1] if '.' in filename else ''
        unique_filename = f"{user_id}/{uuid.uuid4()}.{file_extension}"
        
        # Create blob
        blob = self.bucket.blob(unique_filename)
        
        # Set metadata
        blob.metadata = {
            'original_filename': filename,
            'uploaded_by': str(user_id),
            'upload_date': datetime.utcnow().isoformat()
        }
        
        # Upload file
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            lambda: blob.upload_from_string(file_content, content_type=content_type)
        )
        
        # Get file metadata
        metadata = await self._get_file_metadata(file_content, content_type)
        
        return unique_filename, metadata
    
    async def _get_file_metadata(self, file_content: bytes, content_type: str) -> dict:
        """Extract metadata from file content."""
        metadata = {
            'file_size': len(file_content),
            'content_type': content_type
        }
        
        # If it's an image, get dimensions
        if content_type.startswith('image/'):
            try:
                loop = asyncio.get_event_loop()
                image = await loop.run_in_executor(
                    None, lambda: Image.open(io.BytesIO(file_content))
                )
                metadata['width'] = image.width
                metadata['height'] = image.height
                metadata['media_type'] = 'image'
            except Exception:
                metadata['media_type'] = 'image'
        elif content_type.startswith('video/'):
            metadata['media_type'] = 'video'
            # Extract video metadata using ffprobe if available
            try:
                import subprocess
                import tempfile
                import json
                
                # Save video to temporary file for analysis
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                    temp_file.write(file_content)
                    temp_path = temp_file.name
                
                try:
                    # Use ffprobe to get video metadata
                    result = subprocess.run([
                        'ffprobe', '-v', 'quiet', '-print_format', 'json',
                        '-show_format', '-show_streams', temp_path
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        probe_data = json.loads(result.stdout)
                        
                        # Extract video stream info
                        for stream in probe_data.get('streams', []):
                            if stream.get('codec_type') == 'video':
                                metadata['width'] = stream.get('width', 0)
                                metadata['height'] = stream.get('height', 0)
                                metadata['duration'] = float(stream.get('duration', 0))
                                metadata['fps'] = eval(stream.get('r_frame_rate', '0/1'))
                                break
                        
                        # Extract format info
                        format_info = probe_data.get('format', {})
                        if 'duration' in format_info:
                            metadata['duration'] = float(format_info['duration'])
                        
                except subprocess.TimeoutExpired:
                    logger.warning("Video metadata extraction timed out")
                except subprocess.CalledProcessError:
                    logger.warning("ffprobe not available or failed")
                finally:
                    # Clean up temp file
                    import os
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                        
            except Exception as e:
                logger.warning(f"Could not extract video metadata: {e}")
                # Set basic video metadata
                metadata['width'] = 0
                metadata['height'] = 0
                metadata['duration'] = 0
        else:
            metadata['media_type'] = 'other'
            
        return metadata
    
    async def generate_thumbnail(
        self, 
        blob_name: str, 
        size: Tuple[int, int] = (300, 300)
    ) -> Optional[str]:
        """
        Generate thumbnail for image files.
        
        Args:
            blob_name: Original file blob name
            size: Thumbnail size (width, height)
            
        Returns:
            Thumbnail blob name or None if not an image
        """
        blob = self.bucket.blob(blob_name)
        
        try:
            # Download original file
            loop = asyncio.get_event_loop()
            file_content = await loop.run_in_executor(None, blob.download_as_bytes)
            
            # Check if it's an image
            if not blob.content_type or not blob.content_type.startswith('image/'):
                return None
            
            # Create thumbnail
            image = await loop.run_in_executor(
                None, lambda: Image.open(io.BytesIO(file_content))
            )
            
            # Convert to RGB if necessary (for JPEG compatibility)
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Create thumbnail
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail to bytes
            thumbnail_io = io.BytesIO()
            image.save(thumbnail_io, format='JPEG', optimize=True, quality=85)
            thumbnail_content = thumbnail_io.getvalue()
            
            # Upload thumbnail
            thumbnail_name = f"thumbnails/{blob_name}.thumb.jpg"
            thumbnail_blob = self.bucket.blob(thumbnail_name)
            
            await loop.run_in_executor(
                None,
                lambda: thumbnail_blob.upload_from_string(
                    thumbnail_content, 
                    content_type='image/jpeg'
                )
            )
            
            return thumbnail_name
            
        except Exception as e:
            print(f"Error generating thumbnail for {blob_name}: {e}")
            return None
    
    async def get_signed_url(
        self, 
        blob_name: str, 
        expiration: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Generate a signed URL for accessing a file.
        
        Args:
            blob_name: Name of the blob
            expiration: URL expiration time
            
        Returns:
            Signed URL string
        """
        blob = self.bucket.blob(blob_name)
        
        loop = asyncio.get_event_loop()
        url = await loop.run_in_executor(
            None,
            lambda: blob.generate_signed_url(
                version="v4",
                expiration=expiration,
                method="GET"
            )
        )
        
        return url
    
    async def delete_file(self, blob_name: str) -> bool:
        """
        Delete a file from Google Cloud Storage.
        
        Args:
            blob_name: Name of the blob to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            blob = self.bucket.blob(blob_name)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, blob.delete)
            
            # Also delete thumbnail if exists
            thumbnail_name = f"thumbnails/{blob_name}.thumb.jpg"
            try:
                thumbnail_blob = self.bucket.blob(thumbnail_name)
                await loop.run_in_executor(None, thumbnail_blob.delete)
            except NotFound:
                pass  # Thumbnail doesn't exist, that's fine
                
            return True
        except Exception as e:
            print(f"Error deleting file {blob_name}: {e}")
            return False
    
    async def file_exists(self, blob_name: str) -> bool:
        """Check if a file exists in storage."""
        blob = self.bucket.blob(blob_name)
        loop = asyncio.get_event_loop()
        exists = await loop.run_in_executor(None, blob.exists)
        return exists


# Global instance
storage_service = GoogleCloudStorageService() 