#!/usr/bin/env python3

import requests
import time
import sys

def test_endpoint(url, description):
    """Test an API endpoint and print the result"""
    try:
        print(f"🧪 Testing {description}: {url}")
        response = requests.get(url, timeout=5)
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📄 Response: {response.text}")
        print()
        return True
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        print()
        return False

def main():
    print("🔍 Testing Crow's Eye API Endpoints")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    # Test endpoints
    endpoints = [
        ("http://localhost:8000/", "Root endpoint"),
        ("http://localhost:8000/health", "Health endpoint"),
        ("http://localhost:8000/api/v1/health", "API v1 Health endpoint"),
        ("http://localhost:8000/docs", "API Documentation"),
    ]
    
    results = []
    for url, description in endpoints:
        success = test_endpoint(url, description)
        results.append((url, description, success))
    
    # Summary
    print("📋 Test Summary:")
    print("-" * 30)
    for url, description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {description}")
    
    # Check if all tests passed
    all_passed = all(result[2] for result in results)
    if all_passed:
        print("\n🎉 All endpoints are working correctly!")
        sys.exit(0)
    else:
        print("\n⚠️  Some endpoints failed. Check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 