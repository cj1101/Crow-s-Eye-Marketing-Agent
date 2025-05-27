"""
Test script for video thumbnail generation.
"""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.video_thumbnail_generator import VideoThumbnailGenerator

def test_thumbnail_generation():
    """Test video thumbnail generation."""
    # Test with a sample video path (you can replace this with an actual video file)
    test_video_path = "C:/Users/charl/Downloads/walkthrough1.mp4"
    
    if not os.path.exists(test_video_path):
        print(f"Test video not found: {test_video_path}")
        print("Please update the test_video_path variable with a valid video file.")
        return
    
    print(f"Testing thumbnail generation for: {test_video_path}")
    
    # Create thumbnail generator
    generator = VideoThumbnailGenerator()
    
    # Test single thumbnail generation
    print("Generating single thumbnail...")
    thumbnail = generator.generate_thumbnail(test_video_path, timestamp=2.0, size=(400, 300))
    
    if thumbnail and not thumbnail.isNull():
        print("✓ Single thumbnail generated successfully!")
        print(f"  Size: {thumbnail.width()}x{thumbnail.height()}")
    else:
        print("✗ Failed to generate single thumbnail")
    
    # Test multiple thumbnails
    print("\nGenerating multiple thumbnails...")
    thumbnails = generator.generate_multiple_thumbnails(test_video_path, count=3, size=(200, 150))
    
    if thumbnails:
        print(f"✓ Generated {len(thumbnails)} thumbnails successfully!")
        for i, thumb in enumerate(thumbnails):
            print(f"  Thumbnail {i+1}: {thumb.width()}x{thumb.height()}")
    else:
        print("✗ Failed to generate multiple thumbnails")
    
    # Test video preview pixmap
    print("\nGenerating video preview pixmap...")
    preview = generator.create_video_preview_pixmap(test_video_path, size=(400, 300))
    
    if preview and not preview.isNull():
        print("✓ Video preview pixmap generated successfully!")
        print(f"  Size: {preview.width()}x{preview.height()}")
    else:
        print("✗ Failed to generate video preview pixmap")

if __name__ == "__main__":
    test_thumbnail_generation() 