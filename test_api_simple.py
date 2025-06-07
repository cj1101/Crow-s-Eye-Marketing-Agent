#!/usr/bin/env python3
"""
Simple API Test Script for Crow's Eye Marketing Platform
Tests the basic functionality of the cleaned up backend.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8080"  # Change for production
ENDPOINTS = {
    "health": "/health",
    "root": "/",
    "test": "/api/test",
    "test_array": "/api/test-array", 
    "status": "/api/status",
    "gallery": "/api/gallery",
    "gallery_debug": "/api/gallery/debug"
}

def test_endpoint(endpoint_name, url, expected_status=200):
    """Test a single endpoint."""
    print(f"\n🧪 Testing {endpoint_name}: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print("   ✅ Success")
            
            # Try to parse JSON response
            try:
                data = response.json()
                print(f"   📊 Response keys: {list(data.keys())}")
                
                # Show key info based on endpoint
                if endpoint_name == "health":
                    print(f"   💚 API Status: {data.get('status', 'unknown')}")
                elif endpoint_name == "test_array":
                    print(f"   📦 Data count: {len(data.get('data', []))}")
                elif endpoint_name == "gallery":
                    print(f"   🖼️  Galleries count: {len(data.get('galleries', []))}")
                    print(f"   🎯 Success: {data.get('success', 'unknown')}")
                    
            except json.JSONDecodeError:
                print("   ⚠️  Non-JSON response")
                print(f"   📝 Content: {response.text[:100]}...")
                
        else:
            print(f"   ❌ Failed (expected {expected_status})")
            print(f"   📝 Response: {response.text[:200]}...")
            
    except requests.exceptions.ConnectionError:
        print("   🔌 Connection failed - is the API running?")
    except requests.exceptions.Timeout:
        print("   ⏰ Request timed out")
    except Exception as e:
        print(f"   💥 Unexpected error: {e}")

def main():
    """Run all API tests."""
    print("=" * 60)
    print("🏹 CROW'S EYE API SIMPLE TEST SUITE")
    print("=" * 60)
    print(f"🎯 Target: {API_BASE_URL}")
    print(f"⏰ Time: {datetime.now().isoformat()}")
    
    # Test all endpoints
    for endpoint_name, path in ENDPOINTS.items():
        url = f"{API_BASE_URL}{path}"
        test_endpoint(endpoint_name, url)
        time.sleep(0.5)  # Small delay between requests
    
    print("\n" + "=" * 60)
    print("🏁 Test suite completed!")
    print("\n💡 If tests fail:")
    print("   1. Make sure the API is running: python start-api.py")
    print("   2. Check the correct port in the API_BASE_URL")
    print("   3. Verify no firewall is blocking the connection")

if __name__ == "__main__":
    main() 