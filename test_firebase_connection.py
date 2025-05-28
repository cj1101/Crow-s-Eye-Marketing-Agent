#!/usr/bin/env python3
"""
Test Firebase Connection Script

This script helps test the Firebase connection and check for users
from the Crow's Eye website.
"""

import sys
import logging
from src.auth.firebase_admin_auth import get_firebase_admin_auth, get_service_account_instructions
from src.features.authentication.firebase_auth_handler import firebase_auth_handler

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_firebase_admin():
    """Test Firebase Admin SDK connection"""
    print("🔥" * 50)
    print("🔥 Testing Firebase Admin SDK Connection")
    print("🔥" * 50)
    print()
    
    firebase_admin = get_firebase_admin_auth()
    
    if firebase_admin.initialize():
        print("✅ Firebase Admin SDK initialized successfully!")
        
        # Try to list users
        print("\n📋 Listing users from website:")
        users = firebase_admin.list_users(max_results=5)
        
        if users:
            print(f"Found {len(users)} users:")
            for i, user in enumerate(users, 1):
                print(f"  {i}. {user['email']} - {user.get('display_name', 'No name')}")
        else:
            print("No users found or unable to access user database")
        
        return True
    else:
        print("❌ Firebase Admin SDK initialization failed")
        print("\n" + get_service_account_instructions())
        return False

def test_firebase_auth_handler():
    """Test Firebase Auth Handler"""
    print("\n" + "🔧" * 50)
    print("🔧 Testing Firebase Auth Handler")
    print("🔧" * 50)
    print()
    
    if firebase_auth_handler.initialize():
        print("✅ Firebase Auth Handler initialized successfully!")
        
        status = firebase_auth_handler.get_setup_status()
        print(f"Setup type: {status['setup_type']}")
        print(f"Admin SDK available: {status['admin_sdk_available']}")
        print(f"Client config available: {status['client_config_available']}")
        
        return True
    else:
        print("❌ Firebase Auth Handler initialization failed")
        print(firebase_auth_handler.get_setup_instructions())
        return False

def test_user_lookup():
    """Test looking up a specific user"""
    print("\n" + "🔍" * 50)
    print("🔍 Testing User Lookup")
    print("🔍" * 50)
    print()
    
    firebase_admin = get_firebase_admin_auth()
    
    if not firebase_admin._initialized:
        print("❌ Firebase Admin SDK not initialized")
        return False
    
    email = input("Enter email address to look up (or press Enter to skip): ").strip()
    
    if not email:
        print("Skipping user lookup")
        return True
    
    user_data = firebase_admin.get_user_by_email(email)
    
    if user_data:
        print(f"✅ Found user: {email}")
        print(f"   UID: {user_data['uid']}")
        print(f"   Display Name: {user_data.get('display_name', 'None')}")
        print(f"   Email Verified: {user_data.get('email_verified', False)}")
        print(f"   Created: {user_data.get('creation_timestamp', 'Unknown')}")
        
        # Try to get profile from Firestore
        profile = firebase_admin.get_user_profile(user_data['uid'])
        if profile:
            print(f"   Profile found in Firestore")
            print(f"   Subscription: {profile.get('subscription', {}).get('plan', 'free')}")
        else:
            print(f"   No profile found in Firestore")
        
        return True
    else:
        print(f"❌ User not found: {email}")
        return False

def main():
    """Main test function"""
    print("🐦‍⬛ Crow's Eye Firebase Connection Test")
    print("=" * 60)
    
    # Test Firebase Admin SDK
    admin_success = test_firebase_admin()
    
    # Test Firebase Auth Handler
    handler_success = test_firebase_auth_handler()
    
    # Test user lookup if admin SDK is working
    if admin_success:
        test_user_lookup()
    
    print("\n" + "=" * 60)
    print("🎯 Test Summary:")
    print(f"   Firebase Admin SDK: {'✅ Working' if admin_success else '❌ Failed'}")
    print(f"   Firebase Auth Handler: {'✅ Working' if handler_success else '❌ Failed'}")
    
    if admin_success and handler_success:
        print("\n🎉 Firebase is ready! You can now log in with your website account.")
    elif handler_success:
        print("\n⚠️ Basic Firebase config available, but Admin SDK needed for full functionality.")
    else:
        print("\n❌ Firebase setup required. Please follow the setup instructions above.")

if __name__ == "__main__":
    main() 