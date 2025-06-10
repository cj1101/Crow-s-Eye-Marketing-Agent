#!/usr/bin/env python3
"""
Platform Compliance Test Suite

Tests platform compliance validation for all 7 supported platforms:
- Instagram
- Facebook  
- TikTok
- Pinterest
- BlueSky
- Threads
- Google My Business

This test ensures that content validation works correctly and all platform
requirements are properly enforced.
"""

import requests
import json
import time
from typing import Dict, List, Any


class PlatformComplianceTest:
    """Test suite for platform compliance validation."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.platforms = [
            "instagram", "facebook", "tiktok", "pinterest", 
            "bluesky", "threads", "google_business"
        ]
    
    def test_platform_list(self):
        """Test that all 7 platforms are available."""
        print("🔍 Testing platform availability...")
        
        response = self.session.get(f"{self.base_url}/platform-compliance/platforms")
        
        if response.status_code == 200:
            data = response.json()
            platforms = [p["platform_id"] for p in data["platforms"]]
            
            print(f"✅ Found {len(platforms)} platforms: {', '.join(platforms)}")
            
            missing_platforms = set(self.platforms) - set(platforms)
            if missing_platforms:
                print(f"❌ Missing platforms: {', '.join(missing_platforms)}")
                return False
            
            extra_platforms = set(platforms) - set(self.platforms)
            if extra_platforms:
                print(f"ℹ️  Extra platforms found: {', '.join(extra_platforms)}")
            
            return True
        else:
            print(f"❌ Failed to get platform list: {response.status_code}")
            return False
    
    def test_platform_details(self):
        """Test that each platform has proper configuration."""
        print("\n🔍 Testing platform details...")
        
        success_count = 0
        
        for platform in self.platforms:
            print(f"  Testing {platform}...")
            
            response = self.session.get(f"{self.base_url}/platform-compliance/platforms/{platform}")
            
            if response.status_code == 200:
                data = response.json()
                platform_info = data["platform_info"]
                
                # Check required sections
                required_sections = ["content", "media", "posting"]
                missing_sections = []
                
                for section in required_sections:
                    if section not in platform_info:
                        missing_sections.append(section)
                
                if missing_sections:
                    print(f"    ❌ Missing sections: {', '.join(missing_sections)}")
                else:
                    print(f"    ✅ {platform} configuration complete")
                    success_count += 1
            else:
                print(f"    ❌ Failed to get details: {response.status_code}")
        
        print(f"\n📊 Platform details: {success_count}/{len(self.platforms)} platforms configured")
        return success_count == len(self.platforms)
    
    def test_content_validation(self):
        """Test content validation for each platform."""
        print("\n🔍 Testing content validation...")
        
        test_cases = [
            {
                "name": "Valid Instagram Post",
                "platform": "instagram",
                "content_type": "image",
                "caption": "Beautiful sunset! 🌅 #photography #nature #sunset",
                "media_format": "jpg",
                "media_size_mb": 5.2,
                "media_resolution": "1080x1080",
                "hashtags": ["#photography", "#nature", "#sunset"],
                "expected_valid": True
            },
            {
                "name": "Invalid Caption Length",
                "platform": "bluesky",
                "content_type": "text",
                "caption": "This is a very long caption that exceeds the BlueSky character limit of 300 characters. " * 5,
                "expected_valid": False
            },
            {
                "name": "TikTok Video",
                "platform": "tiktok",
                "content_type": "video",
                "caption": "Dancing to trending music! #fyp #dance #viral",
                "media_format": "mp4",
                "media_size_mb": 25.0,
                "media_resolution": "1080x1920",
                "media_duration_seconds": 15,
                "hashtags": ["#fyp", "#dance", "#viral"],
                "expected_valid": True
            },
            {
                "name": "Pinterest Pin",
                "platform": "pinterest",
                "content_type": "image",
                "caption": "DIY home decor ideas for small spaces",
                "media_format": "png",
                "media_size_mb": 15.0,
                "media_resolution": "735x1102",  # 2:3 ratio
                "expected_valid": True
            },
            {
                "name": "Facebook Video Too Large",
                "platform": "facebook",
                "content_type": "video",
                "caption": "Family vacation memories",
                "media_format": "mp4",
                "media_size_mb": 5000.0,  # Exceeds 4GB limit
                "expected_valid": False
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"  Test {i}: {test_case['name']}")
            
            request_data = {
                "platform": test_case["platform"],
                "content_type": test_case["content_type"],
                "caption": test_case.get("caption"),
                "media_format": test_case.get("media_format"),
                "media_size_mb": test_case.get("media_size_mb"),
                "media_resolution": test_case.get("media_resolution"),
                "media_duration_seconds": test_case.get("media_duration_seconds"),
                "hashtags": test_case.get("hashtags", []),
                "mentions": test_case.get("mentions", [])
            }
            
            response = self.session.post(
                f"{self.base_url}/platform-compliance/validate",
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                is_valid = result["is_valid"]
                expected_valid = test_case["expected_valid"]
                
                if is_valid == expected_valid:
                    print(f"    ✅ Validation correct (valid: {is_valid})")
                    print(f"    📊 Compliance score: {result['compliance_score']:.1f}%")
                    success_count += 1
                else:
                    print(f"    ❌ Expected valid: {expected_valid}, got: {is_valid}")
                    if result["errors"]:
                        print(f"    🔍 Errors: {', '.join(result['errors'])}")
            else:
                print(f"    ❌ Request failed: {response.status_code}")
        
        print(f"\n📊 Content validation: {success_count}/{len(test_cases)} tests passed")
        return success_count == len(test_cases)
    
    def test_bulk_validation(self):
        """Test bulk validation across multiple platforms."""
        print("\n🔍 Testing bulk validation...")
        
        request_data = {
            "platforms": ["instagram", "facebook", "threads"],
            "content_type": "image",
            "caption": "Great content for multiple platforms! #social #marketing",
            "media_format": "jpg",
            "media_size_mb": 3.5,
            "media_resolution": "1080x1080",
            "hashtags": ["#social", "#marketing"]
        }
        
        response = self.session.post(
            f"{self.base_url}/platform-compliance/validate-bulk",
            json=request_data
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"  ✅ Bulk validation successful")
            print(f"  📊 Overall score: {result['overall_score']:.1f}%")
            print(f"  🎯 Recommended platforms: {', '.join(result['recommended_platforms'])}")
            
            # Check that all platforms were validated
            validated_platforms = list(result["platform_results"].keys())
            if set(validated_platforms) == set(request_data["platforms"]):
                print(f"  ✅ All platforms validated: {', '.join(validated_platforms)}")
                return True
            else:
                print(f"  ❌ Missing platform results")
                return False
        else:
            print(f"  ❌ Bulk validation failed: {response.status_code}")
            return False
    
    def test_quick_compliance_check(self):
        """Test quick compliance check endpoint."""
        print("\n🔍 Testing quick compliance check...")
        
        params = {
            "platforms": "instagram,facebook,tiktok",
            "content_type": "video",
            "caption_length": 150,
            "media_size_mb": 50.0,
            "hashtag_count": 5
        }
        
        response = self.session.get(
            f"{self.base_url}/platform-compliance/compliance-check",
            params=params
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"  ✅ Quick check successful")
            print(f"  📊 Compliance: {result['compliance_percentage']:.1f}%")
            print(f"  ✅ Compliant platforms: {', '.join(result['compliant_platforms'])}")
            
            if result["issues"]:
                print(f"  ⚠️  Issues found: {len(result['issues'])}")
                for issue in result["issues"][:3]:  # Show first 3 issues
                    print(f"    - {issue}")
            
            return result["total_platforms_checked"] == 3
        else:
            print(f"  ❌ Quick check failed: {response.status_code}")
            return False
    
    def test_platform_specific_requirements(self):
        """Test platform-specific validation requirements."""
        print("\n🔍 Testing platform-specific requirements...")
        
        platform_tests = {
            "instagram": {
                "business_account_required": True,
                "max_caption_length": 2200,
                "max_hashtags": 30,
                "supports_links": False
            },
            "tiktok": {
                "verification_required": True,
                "video_only": True,
                "max_duration": 600,
                "aspect_ratio": "9:16"
            },
            "pinterest": {
                "business_account_required": True,
                "max_caption_length": 500,
                "supports_links": True
            },
            "bluesky": {
                "max_caption_length": 300,
                "decentralized": True,
                "scheduling_support": False
            }
        }
        
        success_count = 0
        
        for platform, requirements in platform_tests.items():
            print(f"  Testing {platform} requirements...")
            
            response = self.session.get(f"{self.base_url}/platform-compliance/platforms/{platform}")
            
            if response.status_code == 200:
                data = response.json()
                platform_info = data["platform_info"]
                
                checks_passed = 0
                total_checks = 0
                
                # Check business account requirement
                if "business_account_required" in requirements:
                    total_checks += 1
                    expected = requirements["business_account_required"]
                    actual = platform_info["posting"]["business_account_required"]
                    if actual == expected:
                        checks_passed += 1
                    else:
                        print(f"    ❌ Business account requirement mismatch: expected {expected}, got {actual}")
                
                # Check caption length
                if "max_caption_length" in requirements:
                    total_checks += 1
                    expected = requirements["max_caption_length"]
                    actual = platform_info["content"]["max_caption_length"]
                    if actual == expected:
                        checks_passed += 1
                    else:
                        print(f"    ❌ Caption length mismatch: expected {expected}, got {actual}")
                
                # Check link support
                if "supports_links" in requirements:
                    total_checks += 1
                    expected = requirements["supports_links"]
                    actual = platform_info["content"].get("supports_links", True)
                    if actual == expected:
                        checks_passed += 1
                    else:
                        print(f"    ❌ Link support mismatch: expected {expected}, got {actual}")
                
                if checks_passed == total_checks:
                    print(f"    ✅ {platform} requirements validated ({checks_passed}/{total_checks})")
                    success_count += 1
                else:
                    print(f"    ❌ {platform} requirements failed ({checks_passed}/{total_checks})")
            else:
                print(f"    ❌ Failed to get {platform} details")
        
        print(f"\n📊 Platform requirements: {success_count}/{len(platform_tests)} platforms passed")
        return success_count == len(platform_tests)
    
    def run_all_tests(self):
        """Run all platform compliance tests."""
        print("🚀 Starting Platform Compliance Test Suite")
        print("=" * 60)
        
        tests = [
            ("Platform Availability", self.test_platform_list),
            ("Platform Configuration", self.test_platform_details),
            ("Content Validation", self.test_content_validation),
            ("Bulk Validation", self.test_bulk_validation),
            ("Quick Compliance Check", self.test_quick_compliance_check),
            ("Platform-Specific Requirements", self.test_platform_specific_requirements)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
                print()
            except Exception as e:
                print(f"❌ {test_name} failed with error: {str(e)}")
                results.append((test_name, False))
                print()
        
        # Print summary
        print("=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status:8} {test_name}")
            if result:
                passed += 1
        
        print("-" * 60)
        print(f"Overall: {passed}/{len(results)} tests passed ({passed/len(results)*100:.1f}%)")
        
        if passed == len(results):
            print("\n🎉 All platform compliance tests passed!")
            print("✅ All 7 platforms are properly configured and validated")
        else:
            print(f"\n⚠️  {len(results) - passed} test(s) failed")
            print("❌ Platform compliance needs attention")
        
        return passed == len(results)


def main():
    """Run the platform compliance test suite."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test platform compliance for all 7 social media platforms")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for the API")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"Testing API at: {args.url}")
        print(f"Target platforms: {', '.join(['Instagram', 'Facebook', 'TikTok', 'Pinterest', 'BlueSky', 'Threads', 'Google My Business'])}")
        print()
    
    tester = PlatformComplianceTest(base_url=args.url)
    
    try:
        success = tester.run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test suite interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n\n💥 Test suite failed with error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main() 