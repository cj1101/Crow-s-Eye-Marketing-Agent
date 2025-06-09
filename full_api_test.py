#!/usr/bin/env python3

import subprocess
import time
import requests
import sys
import os
from pathlib import Path

def print_banner(message, char="="):
    """Print a banner message"""
    print()
    print(char * 60)
    print(f" {message}")
    print(char * 60)

def check_server_status():
    """Check if the server is already running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def test_endpoint(url, description):
    """Test an API endpoint"""
    try:
        print(f"🧪 Testing {description}...")
        response = requests.get(url, timeout=10)
        print(f"   ✅ Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   📄 Response: {response.text[:100]}...")
            return True
        else:
            print(f"   ❌ Error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def main():
    print_banner("🔧 Crow's Eye API Full Test", "=")
    
    # Check current directory
    current_dir = Path.cwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Navigate to API directory if needed
    if not (current_dir / "main.py").exists():
        api_dir = current_dir / "crow_eye_api"
        if api_dir.exists() and (api_dir / "main.py").exists():
            os.chdir(api_dir)
            print(f"✅ Changed to API directory: {api_dir}")
        else:
            print("❌ Cannot find main.py file")
            return False
    
    print_banner("🧪 Testing Module Import")
    
    # Test import
    try:
        import main
        print("✅ Main module imported successfully")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    print_banner("🚀 Starting/Checking API Server")
    
    # Check if server is already running
    if check_server_status():
        print("✅ Server is already running!")
    else:
        print("🚀 Starting new server...")
        # Note: In a real scenario, you'd start the server in background
        # For now, we'll just check if it can be imported
    
    # Wait a moment
    time.sleep(2)
    
    print_banner("🔍 Testing API Endpoints")
    
    # Test endpoints
    endpoints = [
        ("http://localhost:8000/", "Root endpoint"),
        ("http://localhost:8000/health", "Health endpoint"),
        ("http://localhost:8000/api/v1/health", "API v1 Health endpoint"),
    ]
    
    results = []
    for url, description in endpoints:
        success = test_endpoint(url, description)
        results.append((description, success))
        time.sleep(1)
    
    print_banner("📋 Test Results Summary")
    
    all_passed = True
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {description}")
        if not success:
            all_passed = False
    
    if all_passed:
        print_banner("🎉 All Tests Passed!", "🎉")
        print("✅ Root endpoint is working")
        print("✅ Health endpoint is working") 
        print("✅ API v1 health endpoint is working")
        print()
        print("🌐 Your API is fully functional!")
        print("📖 API Documentation: http://localhost:8000/docs")
        print("🔍 API Status: http://localhost:8000/health")
        return True
    else:
        print_banner("⚠️ Some Tests Failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 