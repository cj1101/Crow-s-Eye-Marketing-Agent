#!/usr/bin/env python3
"""
Setup script for Phase 2: Google Cloud Storage integration

This script helps configure your environment for the new features.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_step(message):
    print(f"\n🔧 {message}")

def print_success(message):
    print(f"✅ {message}")

def print_warning(message):
    print(f"⚠️  {message}")

def print_error(message):
    print(f"❌ {message}")

def check_dependencies():
    """Check if required dependencies can be imported."""
    print_step("Checking new dependencies...")
    
    try:
        import google.cloud.storage
        print_success("Google Cloud Storage SDK available")
    except ImportError:
        print_error("Google Cloud Storage SDK not found")
        return False
    
    try:
        from PIL import Image
        print_success("Pillow (PIL) available")
    except ImportError:
        print_error("Pillow not found")
        return False
    
    try:
        import magic
        print_success("python-magic available")
    except ImportError:
        print_warning("python-magic not found - file type detection may be limited")
    
    return True

def check_environment_file():
    """Check if .env file exists and has required variables."""
    print_step("Checking environment configuration...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print_warning(".env file not found")
        create_env_file()
        return False
    
    # Read existing .env
    with open(env_file, 'r') as f:
        content = f.read()
    
    required_vars = [
        'GOOGLE_CLOUD_PROJECT',
        'GOOGLE_CLOUD_STORAGE_BUCKET'
    ]
    
    missing_vars = []
    for var in required_vars:
        if var not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print_warning(f"Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print_success("Environment file looks good")
    return True

def create_env_file():
    """Create a basic .env file."""
    print_step("Creating .env file template...")
    
    env_content = '''# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./data/crow_eye.db

# JWT Configuration  
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=Crow Eye API

# Google Cloud Configuration (REQUIRED FOR PHASE 2)
GOOGLE_CLOUD_PROJECT=your-project-id-here
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name-here

# AI Services (Optional)
GEMINI_API_KEY=your-gemini-api-key-here
OPENAI_API_KEY=your-openai-api-key-here

# Environment
ENVIRONMENT=development
'''
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print_success(".env file created!")
    print_warning("Please edit .env and add your actual Google Cloud project ID and bucket name")

def print_next_steps():
    """Print instructions for what to do next."""
    print("\n" + "="*60)
    print("🚀 PHASE 2 SETUP COMPLETE!")
    print("="*60)
    
    print("\n📋 NEXT STEPS:")
    print("1. Edit your .env file with your actual Google Cloud settings:")
    print("   - GOOGLE_CLOUD_PROJECT: Your GCP project ID")
    print("   - GOOGLE_CLOUD_STORAGE_BUCKET: Your bucket name")
    
    print("\n2. Set up Google Cloud authentication:")
    print("   Option A: Use Application Default Credentials")
    print("   gcloud auth application-default login")
    print("   ")
    print("   Option B: Use Service Account (for production)")
    print("   export GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json")
    
    print("\n3. Test the API:")
    print("   uvicorn crow_eye_api.main:app --host 0.0.0.0 --port 8000 --reload")
    print("   Then visit: http://localhost:8000/docs")
    
    print("\n4. NEW FEATURES TO TEST:")
    print("   📁 File Upload: POST /api/v1/media/upload")
    print("   🤖 AI Captions: POST /api/v1/ai/captions/generate")
    print("   🏷️  AI Tags: POST /api/v1/ai/media/{id}/tags")
    print("   🔗 Download URLs: GET /api/v1/media/{id}/download")
    print("   🖼️  Thumbnails: GET /api/v1/media/{id}/thumbnail")
    
    print("\n💡 For authorization in Swagger UI:")
    print("   1. Create a user: POST /api/v1/users/")
    print("   2. Login: POST /api/v1/login/access-token")
    print("   3. Copy the access_token")
    print("   4. Click 'Authorize' button in Swagger UI")
    print("   5. Enter: Bearer YOUR_ACCESS_TOKEN")

def main():
    """Main setup function."""
    print("🏗️  Setting up Crow Eye API - Phase 2: Cloud Integration")
    print("="*60)
    
    # Check if we're in the right directory
    if not Path("crow_eye_api").exists():
        print_error("crow_eye_api directory not found. Please run this from the project root.")
        sys.exit(1)
    
    # Check dependencies
    deps_ok = check_dependencies()
    if not deps_ok:
        print_error("Some dependencies are missing. Please install them:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    # Check environment
    env_ok = check_environment_file()
    
    # Always print next steps
    print_next_steps()
    
    if env_ok:
        print("\n🎉 Setup complete! Your API is ready for Phase 2 testing.")
    else:
        print("\n⚠️  Setup partially complete. Please configure your .env file.")

if __name__ == "__main__":
    main() 