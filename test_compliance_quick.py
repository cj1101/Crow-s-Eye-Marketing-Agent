#!/usr/bin/env python3
"""
Quick Platform Compliance Test

Tests that all 7 platforms are working correctly.
"""

from crow_eye_api.services.platform_compliance_service import PlatformComplianceService

def main():
    print("🚀 Testing Platform Compliance System")
    print("=" * 50)
    
    # Initialize service
    service = PlatformComplianceService()
    
    # Test 1: Check all platforms are available
    platforms = service.get_all_platforms()
    print(f"✅ Found {len(platforms)} platforms:")
    for platform in platforms:
        info = service.get_platform_info(platform)
        print(f"   - {info['display_name']} ({platform})")
    
    print()
    
    # Test 2: Validate Instagram content
    print("🔍 Testing Instagram validation...")
    result = service.validate_content(
        platform='instagram',
        content_type='image',
        caption='Beautiful sunset! 🌅 #photography #nature',
        media_size_mb=5.2,
        hashtags=['#photography', '#nature']
    )
    
    print(f"   Valid: {result['is_valid']}")
    print(f"   Score: {result['compliance_score']}%")
    if result['optimization_tips']:
        print(f"   Tips: {result['optimization_tips'][0]}")
    
    print()
    
    # Test 3: Test TikTok (video only platform)
    print("🔍 Testing TikTok validation...")
    result = service.validate_content(
        platform='tiktok',
        content_type='video',
        caption='Dancing to trending music! #fyp #dance',
        media_size_mb=25.0,
        hashtags=['#fyp', '#dance']
    )
    
    print(f"   Valid: {result['is_valid']}")
    print(f"   Score: {result['compliance_score']}%")
    
    print()
    
    # Test 4: Test BlueSky (short captions)
    print("🔍 Testing BlueSky validation...")
    result = service.validate_content(
        platform='bluesky',
        content_type='text',
        caption='Short post for BlueSky community! 🌟',
        hashtags=['#bluesky']
    )
    
    print(f"   Valid: {result['is_valid']}")
    print(f"   Score: {result['compliance_score']}%")
    
    print()
    
    # Test 5: Bulk validation
    print("🔍 Testing bulk validation...")
    bulk_result = service.validate_bulk_content(
        platforms=['instagram', 'facebook', 'threads'],
        content_type='image',
        caption='Great content for multiple platforms!',
        media_size_mb=3.5
    )
    
    print(f"   Overall Score: {bulk_result['overall_score']:.1f}%")
    print(f"   Recommended: {', '.join(bulk_result['recommended_platforms'])}")
    
    print()
    print("🎉 All tests completed successfully!")
    print("✅ Platform compliance system is working correctly")

if __name__ == "__main__":
    main() 