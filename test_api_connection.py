#!/usr/bin/env python3
"""
Test script to verify Crow's Eye API connection and data structures.
Tests the deployed Google Cloud API.
"""

import requests
import json
import sys
from typing import Dict, Any

def test_endpoint(url: str, description: str) -> Dict[str, Any]:
    """Test a single API endpoint."""
    try:
        print(f"\n🧪 Testing: {description}")
        print(f"📡 URL: {url}")
        
        response = requests.get(url, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {description}")
            
            # Check if data has array properties that frontend might use
            if isinstance(data, dict):
                if 'data' in data and isinstance(data['data'], list):
                    print(f"📋 Found array data with {len(data['data'])} items")
                if 'galleries' in data and isinstance(data['galleries'], list):
                    print(f"🖼️ Found galleries array with {len(data['galleries'])} items")
                if 'total' in data:
                    print(f"🔢 Total count: {data['total']}")
            
            return {"success": True, "data": data, "status_code": response.status_code}
        else:
            print(f"❌ Failed: {description} - Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"🚨 Error Response: {error_data}")
                return {"success": False, "error": error_data, "status_code": response.status_code}
            except:
                print(f"🚨 Error Response: {response.text}")
                return {"success": False, "error": response.text, "status_code": response.status_code}
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error for {description}: {e}")
        return {"success": False, "error": str(e), "status_code": None}

def main():
    """Test the Cloud Run API."""
    
    # Use the actual Cloud Run URL
    BASE_URL = "https://crow-eye-api-605899951231.us-central1.run.app"
    
    print("🚀 Testing Crow's Eye API Connection")
    print(f"🌐 Base URL: {BASE_URL}")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        ("Basic API Check", f"{BASE_URL}/"),
        ("Health Check", f"{BASE_URL}/health"),
        ("API Status", f"{BASE_URL}/status"),
        ("Test Array Endpoint", f"{BASE_URL}/api/test-array"),
        ("Gallery Test Endpoint", f"{BASE_URL}/api/gallery-test"),
        ("Gallery Endpoint", f"{BASE_URL}/api/gallery"),
    ]
    
    results = []
    
    for description, url in endpoints:
        result = test_endpoint(url, description)
        results.append({"endpoint": description, "url": url, "result": result})
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    success_count = sum(1 for r in results if r["result"]["success"])
    total_count = len(results)
    
    print(f"✅ Successful: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 All tests passed! API is working correctly.")
        print(f"🔗 Your frontend should connect to: {BASE_URL}")
        print("\n📌 Key URLs for frontend integration:")
        print(f"   - Gallery data: {BASE_URL}/api/gallery")
        print(f"   - Test data: {BASE_URL}/api/test-array")
        print(f"   - API docs: {BASE_URL}/docs")
    else:
        print(f"\n⚠️ Some tests failed. Check the API deployment.")
        
        # Show failed tests
        failed_tests = [r for r in results if not r["result"]["success"]]
        if failed_tests:
            print("\n❌ Failed endpoints:")
            for test in failed_tests:
                print(f"   - {test['endpoint']}: {test['result'].get('error', 'Unknown error')}")

if __name__ == "__main__":
    main() 