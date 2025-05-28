#!/usr/bin/env python3
"""
Create a test user account for Crow's Eye Marketing Platform.
This allows immediate access while Firebase is being configured.
"""
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.user import user_manager

def create_test_user():
    """Create a test user account."""
    print("🐦‍⬛ Creating Test User Account")
    print("=" * 40)
    
    # User details
    email = "charlie@suarezhouse.net"
    username = "Charlie"
    password = "test123"  # Simple password for testing
    
    print(f"Creating user: {email}")
    print(f"Username: {username}")
    print(f"Password: {password}")
    
    # Create the user
    user = user_manager.create_user(email, username, password)
    
    if user:
        print("\n✅ User created successfully!")
        print(f"   Email: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Subscription: {user.get_subscription_status()}")
        print(f"   User ID: {user.user_id}")
        
        # Upgrade to Pro for testing
        print("\n🚀 Upgrading to Pro tier for testing...")
        if user_manager.upgrade_to_pro("test_payment"):
            print("✅ Upgraded to Pro tier!")
        else:
            print("❌ Failed to upgrade to Pro")
        
        print("\n💡 You can now log in with:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        
        return True
    else:
        print("❌ Failed to create user")
        return False

def main():
    """Main function."""
    if create_test_user():
        print("\n🎉 Test user created! You can now:")
        print("1. Run: python test_subscription_system.py")
        print("2. Log in with the credentials above")
        print("3. Test all the subscription features")
        print("\n🔧 Next steps:")
        print("- Set up Firebase for production use")
        print("- See FIREBASE_SETUP_GUIDE.md for instructions")
    else:
        print("\n❌ Failed to create test user")
        print("Check the logs for more details")

if __name__ == "__main__":
    main() 