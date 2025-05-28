#!/usr/bin/env python3
"""
Firebase Configuration Sync Script for Crow's Eye Platform

This script helps synchronize Firebase configuration between:
1. Crow's Eye Website (Next.js)
2. Crow's Eye Python Application

It will guide you through getting the proper Firebase configuration
and setting it up in both projects.
"""

import os
import json
import sys
from pathlib import Path

def print_header():
    """Print script header"""
    print("🔥" * 50)
    print("🔥 Firebase Configuration Sync for Crow's Eye 🔥")
    print("🔥" * 50)
    print()

def check_firebase_project():
    """Check if Firebase project exists"""
    website_path = Path(r"C:\Users\charl\CodingProjets\Crow's Eye Website")
    firebaserc_path = website_path / ".firebaserc"
    
    if firebaserc_path.exists():
        with open(firebaserc_path, 'r') as f:
            config = json.load(f)
            project_id = config.get('projects', {}).get('default')
            print(f"✅ Found Firebase project: {project_id}")
            return project_id
    else:
        print("❌ No Firebase project configuration found")
        return None

def get_firebase_config_instructions():
    """Get instructions for Firebase configuration"""
    return """
📋 To get your Firebase configuration:

1. Go to Firebase Console: https://console.firebase.google.com/
2. Select your project: crows-eye-website
3. Click on the gear icon (⚙️) → Project settings
4. Scroll down to "Your apps" section
5. If you don't have a web app, click "Add app" → Web (</>) 
6. If you have a web app, click on it
7. Copy the configuration values:

const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "crows-eye-website.firebaseapp.com",
  projectId: "crows-eye-website",
  storageBucket: "crows-eye-website.appspot.com",
  messagingSenderId: "123456789",
  appId: "your-app-id"
};

8. You'll need these values:
   - apiKey
   - messagingSenderId  
   - appId
"""

def update_website_env(api_key, sender_id, app_id):
    """Update website .env.local file"""
    website_path = Path(r"C:\Users\charl\CodingProjets\Crow's Eye Website")
    env_path = website_path / ".env.local"
    
    if not env_path.exists():
        print(f"❌ Website .env.local not found at {env_path}")
        return False
    
    # Read current content
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Replace placeholder values
    content = content.replace(
        "NEXT_PUBLIC_FIREBASE_API_KEY=your-actual-api-key-hereSettings → General → Your apps",
        f"NEXT_PUBLIC_FIREBASE_API_KEY={api_key}"
    )
    content = content.replace(
        "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com",
        "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=crows-eye-website.firebaseapp.com"
    )
    content = content.replace(
        "NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id",
        "NEXT_PUBLIC_FIREBASE_PROJECT_ID=crows-eye-website"
    )
    content = content.replace(
        "NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com",
        "NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=crows-eye-website.appspot.com"
    )
    content = content.replace(
        "NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-messaging-sender-id",
        f"NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID={sender_id}"
    )
    content = content.replace(
        "NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id",
        f"NEXT_PUBLIC_FIREBASE_APP_ID={app_id}"
    )
    
    # Write updated content
    with open(env_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated website .env.local")
    return True

def update_python_env(api_key, sender_id, app_id):
    """Update Python application .env file"""
    env_path = Path(".env")
    
    # Read current content
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Remove existing Firebase variables
    lines = [line for line in lines if not any(var in line for var in [
        'FIREBASE_API_KEY=',
        'FIREBASE_MESSAGING_SENDER_ID=',
        'FIREBASE_APP_ID='
    ])]
    
    # Add new Firebase variables
    lines.append(f"\n# Firebase Configuration\n")
    lines.append(f"FIREBASE_API_KEY={api_key}\n")
    lines.append(f"FIREBASE_MESSAGING_SENDER_ID={sender_id}\n")
    lines.append(f"FIREBASE_APP_ID={app_id}\n")
    
    # Write updated content
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Updated Python .env file")
    return True

def main():
    """Main function"""
    print_header()
    
    # Check Firebase project
    project_id = check_firebase_project()
    if not project_id:
        print("Please set up Firebase project first")
        return
    
    print(get_firebase_config_instructions())
    
    print("\n" + "="*60)
    print("🔧 Enter your Firebase configuration values:")
    print("="*60)
    
    # Get configuration from user
    api_key = input("Enter your Firebase API Key: ").strip()
    if not api_key:
        print("❌ API Key is required")
        return
    
    sender_id = input("Enter your Messaging Sender ID: ").strip()
    if not sender_id:
        print("❌ Messaging Sender ID is required")
        return
    
    app_id = input("Enter your App ID: ").strip()
    if not app_id:
        print("❌ App ID is required")
        return
    
    print("\n" + "="*60)
    print("🔄 Updating configuration files...")
    print("="*60)
    
    # Update both projects
    website_success = update_website_env(api_key, sender_id, app_id)
    python_success = update_python_env(api_key, sender_id, app_id)
    
    if website_success and python_success:
        print("\n✅ Configuration updated successfully!")
        print("\n📋 Next steps:")
        print("1. Restart your Python application")
        print("2. Restart your Next.js website (if running)")
        print("3. Try logging in with your website account")
        print("\n🎉 Both projects should now use the same Firebase authentication!")
    else:
        print("\n❌ Some updates failed. Please check the errors above.")

if __name__ == "__main__":
    main() 