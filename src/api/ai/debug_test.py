"""
Debug test for Veo setup
"""
import os

print("🔍 Debug Test Starting...")

# Check environment variable
api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key found: {api_key is not None}")
if api_key:
    print(f"API Key starts with: {api_key[:10]}...")

# Try importing
try:
    print("Trying to import google.genai...")
    from google import genai
    print("✅ Import successful!")
    
    print("Trying to create client...")
    client = genai.Client()
    print("✅ Client created!")
    
    print("🎉 All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 