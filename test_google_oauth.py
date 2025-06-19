#!/usr/bin/env python3
"""
Google OAuth Configuration Test Script

This script tests the Google OAuth configuration and provides setup instructions.
Run this to verify your Google OAuth credentials are properly configured.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils.google_oauth_helper import check_google_services_status, get_google_oauth_helper

def print_banner():
    """Print a banner for the test script."""
    print("="*60)
    print("🔍 Google OAuth Configuration Test")
    print("="*60)
    print()

def test_environment_loading():
    """Test if environment variables are loading correctly."""
    print("📋 Checking environment configuration...")
    
    # Load .env file
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Found .env file: {env_file.absolute()}")
    else:
        print(f"⚠️  No .env file found at: {env_file.absolute()}")
        print("   Create one from env_template.txt")
        return False
    
    return True

def test_google_services():
    """Test Google services configuration."""
    print("\n📡 Checking Google services configuration...")
    
    status = check_google_services_status()
    helper = get_google_oauth_helper()
    
    if status['configured_services']:
        print(f"✅ Configured services: {', '.join(status['configured_services'])}")
        for service in status['configured_services']:
            config = helper.get_service_config(service)
            print(f"   📌 {service}:")
            print(f"      Client ID: {config['client_id'][:10]}...{config['client_id'][-10:] if len(config['client_id']) > 20 else config['client_id']}")
            print(f"      Redirect URI: {config['redirect_uri']}")
    
    if status['missing_services']:
        print(f"❌ Missing services: {', '.join(status['missing_services'])}")
    
    if status['recommendations']:
        print("\n💡 Recommendations:")
        for rec in status['recommendations']:
            print(f"   • {rec['message']}")
    
    return len(status['configured_services']) > 0

def test_api_connection():
    """Test connection to the API backend."""
    print("\n🌐 Testing API connection...")
    
    try:
        import requests
        
        api_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        test_url = f"{api_url}/api/v1/google-photos/health"
        
        print(f"   Connecting to: {test_url}")
        
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('configured'):
                print("✅ API backend is running and Google Photos is configured")
                return True
            else:
                print("⚠️  API backend is running but Google Photos not configured")
                print(f"   Error: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API backend")
        print("   Make sure the backend server is running:")
        print("   • Run: python -m uvicorn crow_eye_api.main:app --reload")
        print("   • Or: python scripts/run.py")
        return False
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def provide_setup_instructions():
    """Provide setup instructions for Google OAuth."""
    print("\n📚 Setup Instructions:")
    print("="*40)
    
    print("\n1. 🏗️  Google Cloud Console Setup:")
    print("   • Go to https://console.cloud.google.com/")
    print("   • Create a new project or select existing one")
    print("   • Enable the following APIs:")
    print("     - Google Photos Library API")
    print("     - YouTube Data API v3 (if using YouTube)")
    print("     - Google My Business API (if using GMB)")
    
    print("\n2. 🔐 OAuth 2.0 Credentials:")
    print("   • Go to 'Credentials' in Google Cloud Console")
    print("   • Click 'Create Credentials' > 'OAuth 2.0 Client ID'")
    print("   • Choose 'Desktop application' as application type")
    print("   • Add these redirect URIs:")
    print("     - http://localhost:8080/auth/google-photos/callback")
    print("     - http://localhost:8080/auth/youtube/callback")
    print("     - http://localhost:8080/auth/google-business/callback")
    
    print("\n3. 📝 Environment Configuration:")
    print("   • Copy env_template.txt to .env")
    print("   • Fill in your OAuth credentials:")
    print("     GOOGLE_PHOTOS_CLIENT_ID=your_client_id_here")
    print("     GOOGLE_PHOTOS_CLIENT_SECRET=your_client_secret_here")
    
    print("\n4. 🚀 Start the Services:")
    print("   • Start API backend: python -m uvicorn crow_eye_api.main:app --reload")
    print("   • Start desktop app: python main.py")
    print("   • Open Google Services dialog and authenticate")

def main():
    """Main test function."""
    print_banner()
    
    # Test environment loading
    env_ok = test_environment_loading()
    
    # Test Google services configuration
    services_ok = test_google_services()
    
    # Test API connection
    api_ok = test_api_connection()
    
    # Summary
    print("\n📊 Summary:")
    print("-" * 30)
    print(f"Environment file: {'✅' if env_ok else '❌'}")
    print(f"Google services:  {'✅' if services_ok else '❌'}")
    print(f"API connection:   {'✅' if api_ok else '❌'}")
    
    if env_ok and services_ok and api_ok:
        print("\n🎉 All tests passed! Google OAuth should work correctly.")
        print("   You can now use the Google Services dialog in the desktop app.")
    else:
        print("\n⚠️  Some issues found. See recommendations above.")
        provide_setup_instructions()
    
    print("\n" + "="*60)

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    main() 