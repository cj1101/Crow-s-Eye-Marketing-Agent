#!/usr/bin/env python3
import requests
import json

def test_google_photos_endpoints():
    print("🔍 Testing Google Photos API endpoints...")
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test 1: Compliance endpoint with Google Photos
    print("\n1. Testing compliance platforms summary...")
    try:
        response = requests.get(f"{base_url}/compliance/platforms/summary")
        if response.status_code == 200:
            data = response.json()
            platforms = data.get('platforms_summary', {}).get('platforms', [])
            print(f"✅ Compliance endpoint working, platforms: {platforms}")
            if 'google_photos' in platforms:
                print("✅ Google Photos found in compliance platforms")
            else:
                print("❌ Google Photos NOT found in compliance platforms")
        else:
            print(f"❌ Compliance endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing compliance: {e}")
    
    # Test 2: Google Photos auth URL
    print("\n2. Testing Google Photos auth URL...")
    try:
        response = requests.get(f"{base_url}/google-photos/auth/url")
        if response.status_code == 200:
            print("✅ Google Photos auth URL endpoint working")
        else:
            print(f"❌ Google Photos auth URL failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing auth URL: {e}")
    
    # Test 3: Google Photos connection status
    print("\n3. Testing Google Photos connection status...")
    try:
        response = requests.get(f"{base_url}/google-photos/connection")
        if response.status_code == 200:
            print("✅ Google Photos connection endpoint working")
        else:
            print(f"❌ Google Photos connection failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
    
    # Test 4: Google Photos platform requirements
    print("\n4. Testing Google Photos platform requirements...")
    try:
        response = requests.get(f"{base_url}/compliance/platform/google_photos")
        if response.status_code == 200:
            data = response.json()
            platform_name = data.get('platform_requirements', {}).get('display_name')
            print(f"✅ Google Photos requirements endpoint working: {platform_name}")
        else:
            print(f"❌ Google Photos requirements failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing requirements: {e}")
    
    print("\n✅ Google Photos endpoint testing complete!")

if __name__ == "__main__":
    test_google_photos_endpoints() 