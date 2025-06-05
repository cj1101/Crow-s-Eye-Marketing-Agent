#!/usr/bin/env python3
"""
Test script for image editing functionality.
This tests the enhanced fallback system when Gemini is not available.
"""

import os
import sys
import tempfile
from PIL import Image

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.features.media_processing.image_edit_handler import ImageEditHandler

def create_test_image():
    """Create a simple test image."""
    # Create a simple test image
    img = Image.new('RGB', (800, 600), color='lightblue')
    
    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    img.save(temp_file.name, 'JPEG')
    temp_file.close()
    
    return temp_file.name

def test_image_editing():
    """Test the image editing functionality."""
    print("🧪 Testing Image Editing Functionality")
    print("=" * 50)
    
    # Create test image
    test_image_path = create_test_image()
    print(f"✅ Created test image: {test_image_path}")
    
    # Initialize image handler
    handler = ImageEditHandler()
    
    # Test different editing instructions
    test_cases = [
        "Make it warmer and more vibrant",
        "Apply a vintage sepia effect",
        "Add a dramatic cinematic look",
        "Make it black and white",
        "Apply soft lighting",
        "Enhance the colors and sharpness"
    ]
    
    for i, instructions in enumerate(test_cases, 1):
        print(f"\n🎨 Test {i}: {instructions}")
        
        try:
            success, edited_path, message = handler.edit_image_with_gemini(test_image_path, instructions)
            
            if success:
                print(f"✅ Success: {message}")
                print(f"📁 Edited image saved to: {edited_path}")
                
                # Verify the file exists and is valid
                if os.path.exists(edited_path):
                    try:
                        edited_img = Image.open(edited_path)
                        print(f"📏 Image size: {edited_img.size}")
                        print(f"🎨 Image mode: {edited_img.mode}")
                    except Exception as e:
                        print(f"❌ Error verifying edited image: {e}")
                else:
                    print(f"❌ Edited image file not found: {edited_path}")
            else:
                print(f"❌ Failed: {message}")
                
        except Exception as e:
            print(f"❌ Exception during editing: {e}")
    
    # Clean up
    try:
        os.unlink(test_image_path)
        print(f"\n🧹 Cleaned up test image: {test_image_path}")
    except:
        pass
    
    print("\n🎉 Image editing tests completed!")

if __name__ == "__main__":
    test_image_editing() 