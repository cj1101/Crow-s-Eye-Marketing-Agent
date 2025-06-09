#!/usr/bin/env python3
"""
Google Cloud Deployment Script for Crow's Eye API
"""

import subprocess
import sys
import os
import json
from pathlib import Path

def print_banner(message, char="="):
    """Print a banner message"""
    print()
    print(char * 60)
    print(f" {message}")
    print(char * 60)

def run_command(command, description=None):
    """Run a command and handle errors"""
    if description:
        print(f"🔧 {description}...")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"   Details: {e.stderr.strip()}")
        return False

def check_gcloud_auth():
    """Check if user is authenticated with gcloud"""
    try:
        result = subprocess.run(["gcloud", "auth", "list", "--format=json"], 
                              capture_output=True, text=True, check=True)
        accounts = json.loads(result.stdout)
        active_accounts = [acc for acc in accounts if acc.get('status') == 'ACTIVE']
        return len(active_accounts) > 0
    except:
        return False

def get_current_project():
    """Get current gcloud project"""
    try:
        result = subprocess.run(["gcloud", "config", "get-value", "project"], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
        return None

def main():
    print_banner("🚀 Crow's Eye API - Google Cloud Deployment", "🚀")
    
    # Check if we're in the right directory
    if not Path("app.yaml").exists():
        print("❌ app.yaml not found. Make sure you're in the project root directory.")
        return False
    
    print("📁 Found app.yaml - proceeding with deployment")
    
    # Check gcloud CLI
    print_banner("🔧 Checking Google Cloud CLI")
    
    if not run_command("gcloud version", "Checking gcloud installation"):
        print("❌ Google Cloud CLI not found. Please install it first:")
        print("   https://cloud.google.com/sdk/docs/install")
        return False
    
    # Check authentication
    if not check_gcloud_auth():
        print("🔑 Not authenticated with Google Cloud. Please run:")
        print("   gcloud auth login")
        return False
    
    print("✅ Authenticated with Google Cloud")
    
    # Get current project
    project = get_current_project()
    if project:
        print(f"📋 Current project: {project}")
    else:
        print("⚠️  No default project set. You may need to set one with:")
        print("   gcloud config set project YOUR_PROJECT_ID")
    
    print_banner("🔍 Pre-deployment Checks")
    
    # Check if App Engine API is enabled
    print("🔧 Checking App Engine API status...")
    
    # Enable required APIs
    apis_to_enable = [
        "appengine.googleapis.com",
        "cloudbuild.googleapis.com",
        "storage.googleapis.com"
    ]
    
    for api in apis_to_enable:
        run_command(f"gcloud services enable {api}", f"Enabling {api}")
    
    print_banner("📦 Preparing for Deployment")
    
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    if not data_dir.exists():
        data_dir.mkdir()
        print("✅ Created data directory")
    
    # Check requirements.txt
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False
    
    print("✅ requirements.txt found")
    
    print_banner("🚀 Deploying to Google App Engine")
    
    # Deploy to App Engine
    deploy_command = "gcloud app deploy app.yaml --quiet"
    
    print("🚀 Starting deployment...")
    print("   This may take several minutes...")
    
    if run_command(deploy_command, "Deploying to Google App Engine"):
        print_banner("🎉 Deployment Successful!", "🎉")
        
        # Get the deployed URL
        try:
            result = subprocess.run(["gcloud", "app", "browse", "--no-launch-browser"], 
                                  capture_output=True, text=True, check=True)
            url = result.stderr.strip() if result.stderr else "https://your-project.uc.r.appspot.com"
            
            print("🌐 Your API is now live at:")
            print(f"   {url}")
            print()
            print("🔍 Available endpoints:")
            print(f"   {url}/")
            print(f"   {url}/health")
            print(f"   {url}/api/v1/health")
            print(f"   {url}/docs")
            print()
            print("📖 API Documentation:")
            print(f"   {url}/docs")
            print(f"   {url}/redoc")
            
        except:
            print("🌐 Deployment successful! Check Google Cloud Console for the URL.")
        
        print_banner("✅ Deployment Complete")
        return True
    else:
        print_banner("❌ Deployment Failed")
        print("🔧 Troubleshooting tips:")
        print("   1. Check your Google Cloud project settings")
        print("   2. Ensure App Engine is initialized in your project")
        print("   3. Verify your app.yaml configuration")
        print("   4. Check the deployment logs in Google Cloud Console")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 