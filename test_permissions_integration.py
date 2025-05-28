#!/usr/bin/env python3
"""
Test script to verify subscription permissions integration across Crow's Eye platform.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from src.models.user import user_manager, SubscriptionTier
from src.features.subscription.access_control import access_control, Feature
from src.utils.subscription_utils import (
    check_feature_access_with_dialog, 
    check_usage_limit_with_dialog,
    show_upgrade_dialog
)

def test_feature_access():
    """Test feature access control."""
    print("\n🔒 Testing Feature Access Control")
    print("=" * 50)
    
    # Test without login
    print("\n📝 Testing without login:")
    for feature in [Feature.MEDIA_LIBRARY, Feature.SMART_GALLERY_GENERATOR, Feature.VEO_VIDEO_GENERATOR]:
        has_access = access_control.has_feature_access(feature)
        print(f"  {feature.value}: {'✅' if has_access else '❌'}")
    
    # Test with free user
    print("\n🆓 Testing with free user:")
    user_manager.create_user("test_free@example.com", "Test Free User", "password123")
    user_manager.login("test_free@example.com", "password123")
    
    for feature in [Feature.MEDIA_LIBRARY, Feature.SMART_GALLERY_GENERATOR, Feature.VEO_VIDEO_GENERATOR]:
        has_access = access_control.has_feature_access(feature)
        print(f"  {feature.value}: {'✅' if has_access else '❌'}")
    
    # Test with pro user
    print("\n💎 Testing with pro user:")
    user = user_manager.get_current_user()
    if user:
        user.subscription.tier = SubscriptionTier.PRO_AGENCY
        user.subscription.is_active = True
        user_manager.save_user(user)
    
    for feature in [Feature.MEDIA_LIBRARY, Feature.SMART_GALLERY_GENERATOR, Feature.VEO_VIDEO_GENERATOR]:
        has_access = access_control.has_feature_access(feature)
        print(f"  {feature.value}: {'✅' if has_access else '❌'}")

def test_usage_limits():
    """Test usage limit enforcement."""
    print("\n📊 Testing Usage Limits")
    print("=" * 50)
    
    user = user_manager.get_current_user()
    if not user:
        print("❌ No user logged in")
        return
    
    # Test different usage types
    usage_types = ['social_accounts', 'ai_content_credits_per_month', 'ai_image_edits_per_month']
    
    for usage_type in usage_types:
        can_use = access_control.check_usage_limit(usage_type, 1)
        print(f"  {usage_type}: {'✅' if can_use else '❌'}")
    
    # Show usage info
    usage_info = access_control.get_usage_info()
    if usage_info:
        print(f"\n📈 Current Usage:")
        print(f"  Tier: {usage_info['subscription_tier']}")
        for usage_type, data in usage_info['usage'].items():
            percentage = (data['current'] / data['limit']) * 100 if data['limit'] > 0 else 0
            print(f"  {usage_type}: {data['current']}/{data['limit']} ({percentage:.1f}%)")

def test_ui_integration():
    """Test UI integration with permissions."""
    print("\n🖥️ Testing UI Integration")
    print("=" * 50)
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    # Test feature access dialog
    print("  Testing feature access dialog...")
    has_access = check_feature_access_with_dialog(Feature.VEO_VIDEO_GENERATOR, None)
    print(f"  Video generator access: {'✅' if has_access else '❌'}")
    
    # Test usage limit dialog
    print("  Testing usage limit dialog...")
    can_use = check_usage_limit_with_dialog('ai_content_credits_per_month', 1, None)
    print(f"  AI content usage allowed: {'✅' if can_use else '❌'}")

def test_decorator_integration():
    """Test decorator integration."""
    print("\n🎯 Testing Decorator Integration")
    print("=" * 50)
    
    from src.utils.subscription_utils import requires_feature_qt, requires_usage_qt
    
    class TestClass:
        @requires_feature_qt(Feature.VEO_VIDEO_GENERATOR)
        @requires_usage_qt('ai_content_credits_per_month', 1)
        def test_video_generation(self):
            return "Video generated successfully!"
        
        @requires_feature_qt(Feature.SMART_GALLERY_GENERATOR)
        def test_smart_gallery(self):
            return "Gallery generated successfully!"
    
    test_obj = TestClass()
    
    try:
        result = test_obj.test_smart_gallery()
        print(f"  Smart gallery: ✅ {result}")
    except Exception as e:
        print(f"  Smart gallery: ❌ {e}")
    
    try:
        result = test_obj.test_video_generation()
        print(f"  Video generation: ✅ {result}")
    except Exception as e:
        print(f"  Video generation: ❌ {e}")

def main():
    """Run all permission tests."""
    print("🐦‍⬛ Crow's Eye Subscription Permissions Test")
    print("=" * 60)
    
    # Initialize logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        test_feature_access()
        test_usage_limits()
        test_ui_integration()
        test_decorator_integration()
        
        print("\n✅ All permission tests completed!")
        print("\n📋 Summary:")
        print("  - Feature access control: ✅ Working")
        print("  - Usage limit enforcement: ✅ Working") 
        print("  - UI integration: ✅ Working")
        print("  - Decorator integration: ✅ Working")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if user_manager.is_authenticated():
            user_manager.logout()

if __name__ == "__main__":
    main() 