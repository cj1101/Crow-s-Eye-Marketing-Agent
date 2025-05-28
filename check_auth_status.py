#!/usr/bin/env python3
"""
Quick authentication status checker for Crow's Eye Marketing Platform.
Checks Firebase configuration and user authentication status.
"""
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config.firebase_config import (
    is_firebase_configured, 
    check_environment_setup,
    get_setup_instructions,
    validate_firebase_connection
)
from src.models.user import user_manager

def main():
    """Check authentication status and Firebase configuration."""
    print("🐦‍⬛ Crow's Eye Authentication Status Check")
    print("=" * 50)
    
    # Check Firebase configuration
    print("\n🔥 Firebase Configuration:")
    if is_firebase_configured():
        print("✅ Firebase is properly configured")
        if validate_firebase_connection():
            print("✅ Firebase connection validated")
        else:
            print("❌ Firebase connection validation failed")
    else:
        print("❌ Firebase is NOT configured")
        print("\n📋 Environment Variables Status:")
        env_status = check_environment_setup()
        for env_var, status in env_status.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {env_var}")
        
        print(get_setup_instructions())
    
    # Check user authentication
    print("\n👤 User Authentication:")
    if user_manager.is_authenticated():
        user = user_manager.get_current_user()
        print(f"✅ User is logged in: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Subscription: {user.get_subscription_status()}")
        print(f"   User ID: {user.user_id}")
    else:
        print("❌ No user is currently logged in")
    
    # Check data directory
    print(f"\n📁 Data Directory: {user_manager.data_dir}")
    print(f"   Users file exists: {user_manager.users_file.exists()}")
    print(f"   Current user file exists: {user_manager.current_user_file.exists()}")
    
    # Load and show available users (without passwords)
    try:
        users = user_manager._load_users()
        print(f"\n📊 Available Users: {len(users)}")
        for user_id, user_data in users.items():
            email = user_data.get('email', 'Unknown')
            username = user_data.get('username', 'Unknown')
            tier = user_data.get('subscription', {}).get('tier', 'Unknown')
            print(f"   • {username} ({email}) - {tier}")
    except Exception as e:
        print(f"❌ Error loading users: {e}")
    
    print("\n" + "=" * 50)
    print("💡 Next Steps:")
    
    if not is_firebase_configured():
        print("1. Set up Firebase configuration (see FIREBASE_SETUP_GUIDE.md)")
        print("2. Update Crow's Eye Website .env.local with real Firebase credentials")
        print("3. Test authentication in the website first")
        print("4. Then try logging in to the marketing tool")
    elif not user_manager.is_authenticated():
        print("1. Run the test script: python test_subscription_system.py")
        print("2. Create a new account or log in with existing credentials")
        print("3. Test the subscription features")
    else:
        print("✅ Everything looks good! You can use the marketing tool.")
    
    print("\n🔧 Troubleshooting:")
    print("- Check FIREBASE_SETUP_GUIDE.md for detailed setup instructions")
    print("- Run 'python test_subscription_system.py' to test the system")
    print("- Check app_log.log for detailed error messages")

if __name__ == "__main__":
    main() 