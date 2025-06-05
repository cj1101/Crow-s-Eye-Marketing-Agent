"""
Test script for the simple Veo wrapper
"""
from veo_simple import SimpleVeoHandler

def test_simple_wrapper():
    """Test the simple Veo wrapper."""
    print("🧪 Testing Simple Veo Wrapper...")
    
    # Create handler
    handler = SimpleVeoHandler()
    
    # Check status
    status = handler.get_status()
    print(f"📊 Status: {status}")
    
    if not handler.is_ready():
        print("❌ Handler not ready - check your GOOGLE_API_KEY")
        return False
    
    # Test simple video generation
    print("\n🎬 Testing video generation...")
    prompt = "A peaceful sunset over calm water"
    
    success, result, message = handler.generate_simple_video(prompt)
    
    if success:
        print(f"✅ Success! Video saved to: {result}")
        print(f"📝 Message: {message}")
        return True
    else:
        print(f"❌ Failed: {message}")
        print(f"🔍 Error details: {result}")
        return False

if __name__ == "__main__":
    test_simple_wrapper() 