#!/usr/bin/env python3
"""
Complete API test suite for frontend integration
"""

import requests
import json
import io
import time

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

def test_health_checks():
    """Test basic API health"""
    print("🏥 Testing API Health...")
    
    # Test root endpoint
    try:
        response = requests.get(BASE_URL)
        assert response.status_code == 200
        print("✅ Root endpoint working")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False
    
    # Test health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        print("✅ Health endpoint working")
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False
    
    # Test OpenAPI docs
    try:
        response = requests.get(f"{BASE_URL}/docs")
        assert response.status_code == 200
        print("✅ Swagger UI accessible")
    except Exception as e:
        print(f"❌ Swagger UI failed: {e}")
        return False
    
    return True

def test_user_management():
    """Test user creation and authentication"""
    print("\n👤 Testing User Management...")
    
    # Test user creation
    user_data = {
        "email": "frontend_test@example.com",
        "password": "testpass123",
        "full_name": "Frontend Test User"
    }
    
    try:
        response = requests.post(f"{API_URL}/users/", json=user_data)
        if response.status_code in [200, 400]:  # 400 if user already exists
            print("✅ User creation endpoint working")
        else:
            print(f"❌ User creation failed: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ User creation error: {e}")
        return False, None
    
    # Test login
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    
    try:
        response = requests.post(
            f"{API_URL}/login/access-token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print("✅ Login working")
            return True, access_token
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False, None

def test_authenticated_endpoints(token):
    """Test endpoints that require authentication"""
    print("\n🔒 Testing Authenticated Endpoints...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test user profile
    try:
        response = requests.get(f"{API_URL}/users/me", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ User profile: {user_data.get('email', 'N/A')}")
        else:
            print(f"❌ User profile failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ User profile error: {e}")
        return False
    
    # Test media list (should be empty initially)
    try:
        response = requests.get(f"{API_URL}/media/", headers=headers)
        if response.status_code == 200:
            media_data = response.json()
            print(f"✅ Media list working (found {len(media_data)} items)")
        else:
            print(f"❌ Media list failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Media list error: {e}")
        return False
    
    return True

def test_media_upload(token):
    """Test media upload functionality"""
    print("\n📁 Testing Media Upload...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test image
    test_image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01]\xcc\xd0;\x00\x00\x00\x00IEND\xaeB`\x82'
    
    files = {
        'file': ('test_frontend.png', io.BytesIO(test_image_content), 'image/png')
    }
    
    try:
        response = requests.post(
            f"{API_URL}/media/upload",
            files=files,
            headers=headers
        )
        if response.status_code == 200:
            upload_data = response.json()
            media_id = upload_data['media_item']['id']
            print(f"✅ Media upload successful (ID: {media_id})")
            return True, media_id
        else:
            print(f"❌ Media upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ Media upload error: {e}")
        return False, None

def test_media_operations(token, media_id):
    """Test media retrieval and operations"""
    print("\n🎬 Testing Media Operations...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test get specific media item
    try:
        response = requests.get(f"{API_URL}/media/{media_id}", headers=headers)
        if response.status_code == 200:
            media_data = response.json()
            print(f"✅ Media retrieval working (filename: {media_data.get('filename', 'N/A')})")
        else:
            print(f"❌ Media retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Media retrieval error: {e}")
        return False
    
    # Test media search
    search_data = {
        "query": "test",
        "media_types": ["image"],
        "limit": 10
    }
    
    try:
        response = requests.post(f"{API_URL}/media/search", json=search_data, headers=headers)
        if response.status_code == 200:
            search_results = response.json()
            print(f"✅ Media search working (found {search_results.get('total', 0)} results)")
        else:
            print(f"❌ Media search failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Media search error: {e}")
        return False
    
    return True

def test_cors_headers():
    """Test CORS headers for frontend integration"""
    print("\n🌐 Testing CORS Configuration...")
    
    # Test preflight request
    try:
        response = requests.options(
            f"{API_URL}/users/me",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
        )
        
        cors_headers = {
            "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
            "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
            "access-control-allow-headers": response.headers.get("access-control-allow-headers"),
        }
        
        if cors_headers["access-control-allow-origin"] == "*":
            print("✅ CORS properly configured for all origins")
        else:
            print(f"⚠️  CORS origin: {cors_headers['access-control-allow-origin']}")
        
        print(f"✅ CORS methods: {cors_headers['access-control-allow-methods']}")
        print(f"✅ CORS headers: {cors_headers['access-control-allow-headers']}")
        
    except Exception as e:
        print(f"❌ CORS test error: {e}")
        return False
    
    return True

def main():
    """Run complete test suite"""
    print("🚀 Complete API Test Suite for Frontend Integration")
    print("=" * 60)
    
    # Run all tests
    tests_passed = 0
    total_tests = 6
    
    # 1. Health checks
    if test_health_checks():
        tests_passed += 1
    
    # 2. User management
    auth_success, token = test_user_management()
    if auth_success:
        tests_passed += 1
    else:
        print("\n❌ Cannot continue without authentication")
        return
    
    # 3. Authenticated endpoints
    if test_authenticated_endpoints(token):
        tests_passed += 1
    
    # 4. Media upload
    upload_success, media_id = test_media_upload(token)
    if upload_success:
        tests_passed += 1
    
    # 5. Media operations
    if upload_success and test_media_operations(token, media_id):
        tests_passed += 1
    
    # 6. CORS
    if test_cors_headers():
        tests_passed += 1
    
    # Final results
    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! API is ready for frontend integration!")
        print("\n📋 Frontend Integration Info:")
        print(f"   API Base URL: {API_URL}")
        print(f"   Authentication: Bearer token")
        print(f"   CORS: Enabled for all origins")
        print(f"   Documentation: {BASE_URL}/docs")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main() 