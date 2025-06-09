#!/usr/bin/env python3
"""
Comprehensive API Testing Script for Crow's Eye Web Application
Tests all implemented endpoints with authentication and error handling.
"""

import requests
import json
import time
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

class CrowsEyeAPITester:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results."""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
    
    def authenticate(self, email: str = "test@example.com", password: str = "testpassword"):
        """Authenticate with the API."""
        try:
            response = self.session.post(
                f"{self.base_url}/login/access-token",
                data={"username": email, "password": password}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_test("Authentication", True, "Successfully authenticated")
                return True
            else:
                self.log_test("Authentication", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Error: {str(e)}")
            return False
    
    def test_health_endpoints(self):
        """Test health and status endpoints."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            success = response.status_code == 200
            self.log_test("API Health Check", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("API Health Check", False, f"Error: {str(e)}")
    
    def test_post_management(self):
        """Test post management endpoints."""
        post_data = {
            "media_id": "test_media_123",
            "caption": "Test post caption",
            "platforms": ["instagram", "facebook"],
            "custom_instructions": "Make it engaging",
            "formatting": {
                "vertical_optimization": True,
                "caption_overlay": False,
                "aspect_ratio": "1:1"
            },
            "context_files": [],
            "is_recurring": False
        }
        
        try:
            response = self.session.post(f"{self.base_url}/posts/", json=post_data)
            success = response.status_code in [200, 201]
            self.log_test("Create Post", success, f"Status: {response.status_code}")
            
            response = self.session.get(f"{self.base_url}/posts/")
            success = response.status_code == 200
            self.log_test("List Posts", success, f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Post Management", False, f"Error: {str(e)}")
    
    def test_scheduling(self):
        """Test scheduling endpoints."""
        schedule_data = {
            "name": "Test Schedule",
            "description": "Automated posting schedule",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "posts_per_day": 2,
            "platforms": ["instagram", "facebook"],
            "posting_times": ["09:00", "17:00"],
            "is_active": True,
            "content_sources": {
                "media_library": True,
                "ai_generated": False,
                "templates": []
            },
            "rules": {
                "skip_weekends": False,
                "skip_holidays": True,
                "minimum_interval": 120
            }
        }
        
        try:
            # Test create schedule
            response = self.session.post(f"{self.base_url}/schedules/", json=schedule_data)
            success = response.status_code in [200, 201]
            schedule_id = None
            if success:
                schedule_id = response.json().get("id")
            self.log_test("Create Schedule", success, f"Status: {response.status_code}")
            
            # Test get schedules
            response = self.session.get(f"{self.base_url}/schedules/")
            success = response.status_code == 200
            self.log_test("List Schedules", success, f"Status: {response.status_code}")
            
            # Test calendar view
            start_date = date.today()
            end_date = start_date + timedelta(days=30)
            response = self.session.get(
                f"{self.base_url}/schedules/calendar",
                params={"start": start_date.isoformat(), "end": end_date.isoformat()}
            )
            success = response.status_code == 200
            self.log_test("Schedule Calendar", success, f"Status: {response.status_code}")
            
            # Test schedule actions if we have a schedule ID
            if schedule_id:
                # Test toggle schedule
                response = self.session.post(f"{self.base_url}/schedules/{schedule_id}/toggle")
                success = response.status_code in [200, 201]
                self.log_test("Toggle Schedule", success, f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Scheduling", False, f"Error: {str(e)}")
    
    def test_analytics(self):
        """Test analytics endpoints."""
        try:
            # Test post analytics
            response = self.session.get(f"{self.base_url}/analytics/posts/test_post_123")
            success = response.status_code == 200
            self.log_test("Post Analytics", success, f"Status: {response.status_code}")
            
            # Test platform analytics
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()
            response = self.session.get(
                f"{self.base_url}/analytics/platforms",
                params={"start": start_date.isoformat(), "end": end_date.isoformat()}
            )
            success = response.status_code == 200
            self.log_test("Platform Analytics", success, f"Status: {response.status_code}")
            
            # Test engagement trends
            response = self.session.get(
                f"{self.base_url}/analytics/trends",
                params={"period": "7d", "platform": "instagram"}
            )
            success = response.status_code == 200
            self.log_test("Engagement Trends", success, f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Analytics", False, f"Error: {str(e)}")
    
    def test_templates(self):
        """Test template management endpoints."""
        template_data = {
            "name": "Test Template",
            "description": "A test template for posts",
            "category": "general",
            "platforms": ["instagram", "facebook"],
            "template": {
                "caption_template": "Check out this {product}! {description}",
                "hashtag_template": "#{category} #awesome #test",
                "formatting": {
                    "vertical_optimization": True,
                    "caption_overlay": False
                }
            },
            "variables": [
                {
                    "name": "product",
                    "type": "text",
                    "required": True
                },
                {
                    "name": "description",
                    "type": "text",
                    "required": False
                },
                {
                    "name": "category",
                    "type": "select",
                    "required": True,
                    "options": ["tech", "lifestyle", "business"]
                }
            ]
        }
        
        try:
            # Test create template
            response = self.session.post(f"{self.base_url}/templates/", json=template_data)
            success = response.status_code in [200, 201]
            template_id = None
            if success:
                template_id = response.json().get("id")
            self.log_test("Create Template", success, f"Status: {response.status_code}")
            
            # Test get templates
            response = self.session.get(f"{self.base_url}/templates/")
            success = response.status_code == 200
            self.log_test("List Templates", success, f"Status: {response.status_code}")
            
            # Test apply template if we have a template ID
            if template_id:
                apply_data = {
                    "variables": {
                        "product": "Amazing Widget",
                        "description": "The best widget you'll ever use!",
                        "category": "tech"
                    },
                    "media_id": "test_media_123"
                }
                response = self.session.post(f"{self.base_url}/templates/{template_id}/apply", json=apply_data)
                success = response.status_code in [200, 201]
                self.log_test("Apply Template", success, f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Templates", False, f"Error: {str(e)}")
    
    def test_ai_endpoints(self):
        """Test AI content generation endpoints."""
        try:
            # Test caption generation
            caption_data = {
                "tone": "professional",
                "platforms": ["instagram", "linkedin"],
                "customInstructions": "Focus on innovation",
                "includeHashtags": True,
                "maxLength": 280
            }
            response = self.session.post(f"{self.base_url}/ai/caption", json=caption_data)
            success = response.status_code == 200
            self.log_test("AI Caption Generation", success, f"Status: {response.status_code}")
            
            # Test hashtag generation
            hashtag_data = {
                "content": "Amazing sunset photo",
                "platforms": ["instagram"],
                "niche": "photography",
                "count": 10
            }
            response = self.session.post(f"{self.base_url}/ai/hashtags", json=hashtag_data)
            success = response.status_code == 200
            self.log_test("AI Hashtag Generation", success, f"Status: {response.status_code}")
            
            # Test content suggestions
            suggestions_data = {
                "mediaId": "test_media_123",
                "platforms": ["instagram"],
                "contentType": "caption",
                "variations": 3
            }
            response = self.session.post(f"{self.base_url}/ai/suggestions", json=suggestions_data)
            success = response.status_code == 200
            self.log_test("AI Content Suggestions", success, f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("AI Endpoints", False, f"Error: {str(e)}")
    
    def test_media_processing(self):
        """Test media processing endpoints."""
        try:
            # Test media processing with instructions
            processing_data = {
                "instructions": "Make this image more vibrant and add a vintage filter",
                "output_format": "image",
                "platforms": ["instagram", "facebook"],
                "formatting": {
                    "vertical_optimization": True,
                    "aspect_ratio": "1:1"
                }
            }
            response = self.session.post(f"{self.base_url}/media/123/process", json=processing_data)
            success = response.status_code in [200, 201]
            self.log_test("Media Processing", success, f"Status: {response.status_code}")
            
            # Test media optimization
            optimization_data = {
                "platforms": ["instagram", "tiktok"],
                "variations": {
                    "aspect_ratios": ["1:1", "9:16"],
                    "sizes": ["standard", "high-res"]
                }
            }
            response = self.session.post(f"{self.base_url}/media/123/optimize", json=optimization_data)
            success = response.status_code in [200, 201]
            self.log_test("Media Optimization", success, f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Media Processing", False, f"Error: {str(e)}")
    
    def test_webhooks(self):
        """Test webhook endpoints."""
        try:
            # Test webhook status
            response = self.session.get(f"{self.base_url}/webhooks/status")
            success = response.status_code == 200
            self.log_test("Webhook Status", success, f"Status: {response.status_code}")
            
            # Test post status webhook (simulate)
            webhook_data = {
                "post_id": "test_post_123",
                "status": "published",
                "platform": "instagram",
                "timestamp": datetime.now().isoformat()
            }
            response = self.session.post(f"{self.base_url}/webhooks/post-status", json=webhook_data)
            success = response.status_code == 200
            self.log_test("Post Status Webhook", success, f"Status: {response.status_code}")
            
            # Test platform notification webhook (simulate)
            notification_data = {
                "platform": "instagram",
                "type": "comment",
                "post_id": "test_post_123",
                "user_id": "test_user",
                "content": "Great post!",
                "timestamp": datetime.now().isoformat()
            }
            response = self.session.post(f"{self.base_url}/webhooks/platform-notifications", json=notification_data)
            success = response.status_code == 200
            self.log_test("Platform Notification Webhook", success, f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Webhooks", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all API tests."""
        print("🚀 Starting Crow's Eye API Comprehensive Testing")
        print("=" * 60)
        
        # Test without authentication first (demo mode)
        print("\n📋 Testing Demo Mode (No Authentication)")
        self.test_health_endpoints()
        
        # Authenticate for protected endpoints
        print("\n🔐 Testing Authentication")
        if self.authenticate():
            print("\n📝 Testing Post Management")
            self.test_post_management()
            
            print("\n📅 Testing Scheduling")
            self.test_scheduling()
            
            print("\n📊 Testing Analytics")
            self.test_analytics()
            
            print("\n📋 Testing Templates")
            self.test_templates()
            
            print("\n🤖 Testing AI Endpoints")
            self.test_ai_endpoints()
            
            print("\n🎨 Testing Media Processing")
            self.test_media_processing()
            
            print("\n🔗 Testing Webhooks")
            self.test_webhooks()
        
        # Generate test report
        self.generate_report()
    
    def generate_report(self):
        """Generate a comprehensive test report."""
        print("\n" + "=" * 60)
        print("📊 TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        # Save detailed report
        with open("api_test_report.json", "w") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": success_rate,
                    "timestamp": datetime.now().isoformat()
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: api_test_report.json")

def main():
    """Main function to run the API tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Crow's Eye API")
    parser.add_argument("--url", default="http://localhost:8000/api/v1", 
                       help="API base URL (default: http://localhost:8000/api/v1)")
    parser.add_argument("--email", default="test@example.com", 
                       help="Test user email")
    parser.add_argument("--password", default="testpassword", 
                       help="Test user password")
    
    args = parser.parse_args()
    
    tester = CrowsEyeAPITester(args.url)
    tester.run_all_tests()

if __name__ == "__main__":
    main() 