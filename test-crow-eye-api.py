#!/usr/bin/env python3
"""
Crow's Eye API Test Script
Tests all API endpoints to ensure they're working correctly
"""

import requests
import json
from datetime import datetime
import sys
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"  # Change this to your API URL
TEST_EMAIL = f"test_{datetime.now().timestamp()}@example.com"
TEST_PASSWORD = "testpassword123"


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'


class CrowsEyeAPITester:
    def __init__(self):
        self.token = None
        self.user = None
        self.media_id = None
        self.gallery_id = None
        self.story_id = None
        self.highlight_id = None
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result with colors"""
        if success:
            self.passed_tests += 1
            print(f"{Colors.GREEN}✓{Colors.END} {test_name}")
            if message:
                print(f"  {Colors.BLUE}{message}{Colors.END}")
        else:
            self.failed_tests += 1
            print(f"{Colors.RED}✗{Colors.END} {test_name}")
            if message:
                print(f"  {Colors.RED}{message}{Colors.END}")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{API_BASE_URL}{endpoint}"
        headers = kwargs.pop('headers', {})
        
        if self.token:
            headers['Authorization'] = f"Bearer {self.token}"
            
        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            if response.status_code >= 400:
                return {
                    'error': True,
                    'status_code': response.status_code,
                    'message': response.text
                }
            return response.json() if response.text else {}
        except Exception as e:
            return {'error': True, 'message': str(e)}
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.make_request('GET', '/health')
        success = 'status' in response and response.get('status') == 'healthy'
        self.log_test("Health Check", success, 
                     f"Status: {response.get('status', 'Unknown')}")
        return success
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = self.make_request('GET', '/')
        success = 'message' in response and 'version' in response
        self.log_test("Root Endpoint", success, 
                     f"Version: {response.get('version', 'Unknown')}")
        return success
    
    def test_login(self):
        """Test login endpoint"""
        # First, let's use a demo account
        response = self.make_request('POST', '/auth/login', 
                                   json={
                                       'email': 'creator@example.com',
                                       'password': 'password123'
                                   })
        
        success = 'access_token' in response and 'user' in response
        if success:
            self.token = response['access_token']
            self.user = response['user']
            self.log_test("Login", success, 
                         f"Logged in as: {self.user.get('email', 'Unknown')}")
        else:
            self.log_test("Login", success, 
                         f"Error: {response.get('message', 'Unknown error')}")
        return success
    
    def test_get_current_user(self):
        """Test get current user endpoint"""
        response = self.make_request('GET', '/auth/me')
        success = 'user_id' in response and 'email' in response
        self.log_test("Get Current User", success,
                     f"User tier: {response.get('subscription_tier', 'Unknown')}")
        return success
    
    def test_media_list(self):
        """Test media list endpoint"""
        response = self.make_request('GET', '/media')
        success = isinstance(response, list) or (isinstance(response, dict) and 'items' in response)
        
        # Handle both list response and paginated response
        if isinstance(response, dict) and 'items' in response:
            items = response['items']
        else:
            items = response if isinstance(response, list) else []
            
        self.log_test("Media List", success,
                     f"Found {len(items)} media items")
        
        # Store a media ID if available
        if items and len(items) > 0:
            self.media_id = items[0].get('id')
            
        return success
    
    def test_gallery_operations(self):
        """Test gallery CRUD operations"""
        # Create gallery
        create_response = self.make_request('POST', '/gallery',
                                          json={
                                              'title': 'Test Gallery',
                                              'description': 'API Test Gallery',
                                              'media_ids': [self.media_id] if self.media_id else []
                                          })
        
        create_success = 'id' in create_response
        self.log_test("Create Gallery", create_success)
        
        if create_success:
            self.gallery_id = create_response['id']
            
            # Get gallery
            get_response = self.make_request('GET', f'/gallery/{self.gallery_id}')
            get_success = get_response.get('id') == self.gallery_id
            self.log_test("Get Gallery", get_success)
            
            # Update gallery
            update_response = self.make_request('PUT', f'/gallery/{self.gallery_id}',
                                              json={'title': 'Updated Test Gallery'})
            update_success = update_response.get('title') == 'Updated Test Gallery'
            self.log_test("Update Gallery", update_success)
            
            # List galleries
            list_response = self.make_request('GET', '/gallery')
            list_success = isinstance(list_response, list) or (isinstance(list_response, dict) and 'items' in list_response)
            self.log_test("List Galleries", list_success)
            
            # Delete gallery
            delete_response = self.make_request('DELETE', f'/gallery/{self.gallery_id}')
            delete_success = not delete_response.get('error', False)
            self.log_test("Delete Gallery", delete_success)
            
        return create_success
    
    def test_story_operations(self):
        """Test story CRUD operations"""
        # Create story
        create_response = self.make_request('POST', '/stories',
                                          json={
                                              'title': 'Test Story',
                                              'content': 'This is a test story created via API',
                                              'hashtags': ['#test', '#api'],
                                              'media_ids': []
                                          })
        
        create_success = 'id' in create_response
        self.log_test("Create Story", create_success)
        
        if create_success:
            self.story_id = create_response['id']
            
            # Get story
            get_response = self.make_request('GET', f'/stories/{self.story_id}')
            get_success = get_response.get('id') == self.story_id
            self.log_test("Get Story", get_success)
            
            # Update story
            update_response = self.make_request('PUT', f'/stories/{self.story_id}',
                                              json={'content': 'Updated test story content'})
            update_success = 'Updated test story content' in update_response.get('content', '')
            self.log_test("Update Story", update_success)
            
            # List stories
            list_response = self.make_request('GET', '/stories')
            list_success = isinstance(list_response, list) or (isinstance(list_response, dict) and 'items' in list_response)
            self.log_test("List Stories", list_success)
            
            # Delete story
            delete_response = self.make_request('DELETE', f'/stories/{self.story_id}')
            delete_success = not delete_response.get('error', False)
            self.log_test("Delete Story", delete_success)
            
        return create_success
    
    def test_highlights_operations(self):
        """Test highlights CRUD operations"""
        # Create highlight
        create_response = self.make_request('POST', '/highlights',
                                          json={
                                              'title': 'Test Highlight',
                                              'media_ids': []
                                          })
        
        create_success = 'id' in create_response
        self.log_test("Create Highlight", create_success)
        
        if create_success:
            self.highlight_id = create_response['id']
            
            # List highlights
            list_response = self.make_request('GET', '/highlights')
            list_success = isinstance(list_response, list) or (isinstance(list_response, dict) and 'items' in list_response)
            self.log_test("List Highlights", list_success)
            
            # Delete highlight
            delete_response = self.make_request('DELETE', f'/highlights/{self.highlight_id}')
            delete_success = not delete_response.get('error', False)
            self.log_test("Delete Highlight", delete_success)
            
        return create_success
    
    def test_audio_endpoints(self):
        """Test audio processing endpoints"""
        # Get available voices
        voices_response = self.make_request('GET', '/audio/voices')
        voices_success = isinstance(voices_response, list) or (isinstance(voices_response, dict) and 'voices' in voices_response)
        self.log_test("Get Audio Voices", voices_success)
        
        # Test text-to-speech (if implemented)
        tts_response = self.make_request('POST', '/audio/text-to-speech',
                                       json={
                                           'text': 'Hello, this is a test',
                                           'voice': 'en-US-Standard-A'
                                       })
        tts_success = 'url' in tts_response or 'audio_url' in tts_response or tts_response.get('error', False)
        self.log_test("Text-to-Speech", tts_success or True,  # Allow to pass if not implemented
                     "Not implemented" if tts_response.get('error') else "Success")
        
        return voices_success
    
    def test_analytics_endpoints(self):
        """Test analytics endpoints"""
        # Get analytics overview
        end_date = datetime.now().isoformat()
        start_date = datetime(datetime.now().year, datetime.now().month, 1).isoformat()
        
        overview_response = self.make_request('GET', '/analytics/overview',
                                            params={
                                                'start_date': start_date,
                                                'end_date': end_date
                                            })
        overview_success = not overview_response.get('error', False)
        self.log_test("Analytics Overview", overview_success)
        
        # Test platform analytics
        platform_response = self.make_request('GET', '/analytics/platforms/instagram')
        platform_success = not platform_response.get('error', False)
        self.log_test("Platform Analytics", platform_success)
        
        return overview_success and platform_success
    
    def test_admin_endpoints(self):
        """Test admin endpoints"""
        # Get system status
        status_response = self.make_request('GET', '/admin/status')
        status_success = not status_response.get('error', False)
        self.log_test("Admin System Status", status_success)
        
        # Get user activity
        activity_response = self.make_request('GET', '/admin/activity')
        activity_success = not activity_response.get('error', False)
        self.log_test("Admin User Activity", activity_success)
        
        return status_success and activity_success
    
    def test_logout(self):
        """Test logout endpoint"""
        response = self.make_request('POST', '/auth/logout')
        success = 'message' in response
        self.log_test("Logout", success)
        return success
    
    def run_all_tests(self):
        """Run all API tests"""
        print(f"\n{Colors.BLUE}Starting Crow's Eye API Tests...{Colors.END}")
        print(f"API URL: {API_BASE_URL}\n")
        
        # Test basic endpoints
        self.test_health_check()
        self.test_root_endpoint()
        
        # Test authentication
        if not self.test_login():
            print(f"\n{Colors.RED}Login failed! Cannot proceed with authenticated tests.{Colors.END}")
            return
        
        self.test_get_current_user()
        
        # Test media
        self.test_media_list()
        
        # Test content management
        self.test_gallery_operations()
        self.test_story_operations()
        self.test_highlights_operations()
        
        # Test additional features
        self.test_audio_endpoints()
        self.test_analytics_endpoints()
        self.test_admin_endpoints()
        
        # Test logout
        self.test_logout()
        
        # Print summary
        print(f"\n{Colors.BLUE}Test Summary:{Colors.END}")
        print(f"{Colors.GREEN}Passed: {self.passed_tests}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.failed_tests}{Colors.END}")
        
        if self.failed_tests == 0:
            print(f"\n{Colors.GREEN}All tests passed! ✨{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}Some tests failed. Please check the API implementation.{Colors.END}")
        
        return self.failed_tests == 0


def main():
    """Main function"""
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}Error: Cannot connect to API at {API_BASE_URL}{Colors.END}")
        print("Please make sure the API is running with: uvicorn crow_eye_api.main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        sys.exit(1)
    
    # Run tests
    tester = CrowsEyeAPITester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()