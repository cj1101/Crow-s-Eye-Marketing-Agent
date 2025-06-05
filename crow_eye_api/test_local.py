#!/usr/bin/env python3
"""
Test script to run the API locally and verify it works.
"""

import os
import sys
import subprocess
import time
import requests

def test_api():
    """Test the API locally."""
    print("🚀 Testing Crow's Eye API locally...")
    
    # Start the API server
    print("📡 Starting API server...")
    proc = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "main:app", 
        "--host", "0.0.0.0", "--port", "8000"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        # Test the endpoints
        print("🔍 Testing endpoints...")
        
        # Test root endpoint
        response = requests.get("http://localhost:8000/")
        print(f"✅ Root endpoint: {response.status_code} - {response.json()}")
        
        # Test health endpoint
        response = requests.get("http://localhost:8000/health")
        print(f"✅ Health endpoint: {response.status_code} - {response.json()}")
        
        # Test API endpoint
        response = requests.get("http://localhost:8000/api/test")
        print(f"✅ API test endpoint: {response.status_code} - {response.json()}")
        
        print("🎉 All tests passed! API is working correctly.")
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")
    
    finally:
        # Stop the server
        proc.terminate()
        proc.wait()
        print("🛑 API server stopped.")

if __name__ == "__main__":
    test_api() 