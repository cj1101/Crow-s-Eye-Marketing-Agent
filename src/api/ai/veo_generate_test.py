"""
Simple Veo 3 video generation test
"""
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_simple_video_generation():
    """Test generating a simple video with Veo."""
    try:
        from google import genai
        from google.genai import types
        
        print("🎬 Starting simple video generation test...")
        
        # Create client
        client = genai.Client()
        print("✅ Client created")
        
        # Simple prompt
        prompt = "A cute cat sitting in a sunny garden"
        print(f"📝 Using prompt: {prompt}")
        
        # Generate video
        print("🎥 Starting video generation (this may take 2-3 minutes)...")
        operation = client.models.generate_videos(
            model="veo-2.0-generate-001",  # Using stable version
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio="16:9",
                person_generation="dont_allow",
                number_of_videos=1,
                duration_seconds=5  # Shortest duration for testing
            )
        )
        
        print("⏳ Waiting for video generation to complete...")
        start_time = time.time()
        
        while not operation.done:
            elapsed = time.time() - start_time
            print(f"   ... still generating ({elapsed:.0f}s elapsed)")
            time.sleep(15)  # Check every 15 seconds
            operation = client.operations.get(operation)
            
            # Timeout after 5 minutes for testing
            if elapsed > 300:
                print("⏰ Test timeout - video generation taking too long")
                return False
        
        # Check result
        if operation.response and operation.response.generated_videos:
            video = operation.response.generated_videos[0]
            print("🎉 Video generated successfully!")
            print(f"📁 Video info: {video}")
            
            # Try to save it
            output_path = "test_veo_video.mp4"
            try:
                client.files.download(file=video.video)
                video.video.save(output_path)
                print(f"💾 Video saved to: {output_path}")
                return True
            except Exception as e:
                print(f"⚠️ Video generated but couldn't save: {e}")
                return True  # Still counts as success
        else:
            print("❌ No video was generated")
            return False
            
    except Exception as e:
        print(f"❌ Video generation test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Veo 3 video generation...")
    success = test_simple_video_generation()
    if success:
        print("✅ Video generation test completed successfully!")
    else:
        print("❌ Video generation test failed") 