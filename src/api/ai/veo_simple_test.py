"""
Simple Veo 3 test script - Basic functionality check
"""
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_veo_basic():
    """Test basic Veo functionality with minimal code."""
    try:
        # Check if API key exists
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ No GOOGLE_API_KEY found in environment")
            return False
        
        print("✅ API key found")
        
        # Try to import the Google Gen AI library
        try:
            from google import genai
            print("✅ Google Gen AI library imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import google.genai: {e}")
            return False
        
        # Try to create a client
        try:
            client = genai.Client()
            print("✅ Gen AI client created successfully")
        except Exception as e:
            print(f"❌ Failed to create client: {e}")
            return False
        
        print("🎉 Basic Veo setup test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing basic Veo 3 setup...")
    test_veo_basic() 