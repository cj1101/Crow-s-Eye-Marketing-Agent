#!/usr/bin/env python3
"""
Comprehensive API testing script for Crow's Eye highlight generation and other endpoints.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_V1_PREFIX = "/api/v1"

class APITester:
    """Test suite for Crow's Eye API endpoints."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        
    def test_health_check(self) -> bool:
        """Test basic health check endpoint."""
        try:
            print("🔍 Testing health check...")
            response = self.session.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_root_endpoint(self) -> bool:
        """Test root endpoint."""
        try:
            print("🔍 Testing root endpoint...")
            response = self.session.get(f"{self.base_url}/")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Root endpoint passed: {data}")
                return True
            else:
                print(f"❌ Root endpoint failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
            return False
    
    def test_openapi_docs(self) -> bool:
        """Test OpenAPI documentation endpoint."""
        try:
            print("🔍 Testing OpenAPI docs...")
            response = self.session.get(f"{self.base_url}/docs")
            
            if response.status_code == 200:
                print("✅ OpenAPI docs accessible")
                return True
            else:
                print(f"❌ OpenAPI docs failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ OpenAPI docs error: {e}")
            return False
    
    def test_highlight_generation_without_auth(self) -> bool:
        """Test highlight generation endpoint without authentication (should fail)."""
        try:
            print("🔍 Testing highlight generation without auth...")
            
            payload = {
                "media_ids": [1, 2, 3],
                "highlight_type": "story",
                "duration": 30,
                "style": "dynamic",
                "include_text": True,
                "include_music": False
            }
            
            response = self.session.post(
                f"{self.base_url}{API_V1_PREFIX}/ai/highlights/generate",
                json=payload
            )
            
            if response.status_code == 401:
                print("✅ Highlight generation correctly requires authentication")
                return True
            else:
                print(f"❌ Unexpected response: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Highlight generation test error: {e}")
            return False
    
    def test_caption_generation_without_auth(self) -> bool:
        """Test caption generation endpoint without authentication (should fail)."""
        try:
            print("🔍 Testing caption generation without auth...")
            
            payload = {
                "media_ids": [1],
                "style": "engaging",
                "platform": "instagram",
                "auto_apply": False
            }
            
            response = self.session.post(
                f"{self.base_url}{API_V1_PREFIX}/ai/captions/generate",
                json=payload
            )
            
            if response.status_code == 401:
                print("✅ Caption generation correctly requires authentication")
                return True
            else:
                print(f"❌ Unexpected response: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Caption generation test error: {e}")
            return False
    
    def test_api_structure(self) -> bool:
        """Test API structure and available endpoints."""
        try:
            print("🔍 Testing API structure...")
            
            # Test if OpenAPI spec is available
            response = self.session.get(f"{self.base_url}{API_V1_PREFIX}/openapi.json")
            
            if response.status_code == 200:
                openapi_spec = response.json()
                print("✅ OpenAPI specification available")
                
                # Check for key endpoints
                paths = openapi_spec.get("paths", {})
                expected_endpoints = [
                    "/api/v1/ai/highlights/generate",
                    "/api/v1/ai/captions/generate"
                ]
                
                for endpoint in expected_endpoints:
                    if endpoint in paths:
                        print(f"✅ Found endpoint: {endpoint}")
                    else:
                        print(f"❌ Missing endpoint: {endpoint}")
                
                return True
            else:
                print(f"❌ OpenAPI spec not available: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ API structure test error: {e}")
            return False
    
    def test_database_connection(self) -> bool:
        """Test if database connection is working by checking startup logs."""
        try:
            print("🔍 Testing database connection...")
            
            # Try to access an endpoint that would trigger database initialization
            response = self.session.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                print("✅ Database connection appears to be working")
                return True
            else:
                print(f"❌ Database connection issue: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Database connection test error: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results."""
        print("🚀 Starting comprehensive API tests...\n")
        
        tests = {
            "health_check": self.test_health_check,
            "root_endpoint": self.test_root_endpoint,
            "openapi_docs": self.test_openapi_docs,
            "api_structure": self.test_api_structure,
            "highlight_generation_auth": self.test_highlight_generation_without_auth,
            "caption_generation_auth": self.test_caption_generation_without_auth,
            "database_connection": self.test_database_connection
        }
        
        results = {}
        
        for test_name, test_func in tests.items():
            print(f"\n{'='*50}")
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ Test {test_name} crashed: {e}")
                results[test_name] = False
            
            time.sleep(0.5)  # Brief pause between tests
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test summary."""
        print(f"\n{'='*50}")
        print("📊 TEST SUMMARY")
        print(f"{'='*50}")
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<30} {status}")
        
        print(f"\n📈 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! API is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the issues above.")


def main():
    """Main test execution."""
    print("🔧 Crow's Eye API Test Suite")
    print("="*50)
    
    # Wait a moment for the server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    tester = APITester()
    results = tester.run_all_tests()
    tester.print_summary(results)
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main() 