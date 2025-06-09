#!/usr/bin/env python3
"""
Crow's Eye Marketing Agent - Web App Installer v2.0
Complete installer for the modern React web app with API integration
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

def check_dependencies():
    """Check if required dependencies are installed"""
    dependencies = ["node", "npm", "git"]
    missing = []
    
    for cmd in dependencies:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            print(f"✅ {cmd} is installed")
        except:
            print(f"❌ {cmd} is not installed")
            missing.append(cmd)
    
    return len(missing) == 0

def create_package_json():
    """Create package.json for the web app"""
    package_json = {
        "name": "crows-eye-marketing-agent",
        "version": "2.0.0",
        "description": "AI-powered social media marketing agent",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview"
        },
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-router-dom": "^6.8.0",
            "axios": "^1.6.0",
            "lucide-react": "^0.294.0",
            "tailwindcss": "^3.3.6",
            "autoprefixer": "^10.4.16",
            "postcss": "^8.4.32"
        },
        "devDependencies": {
            "@types/react": "^18.2.37",
            "@types/react-dom": "^18.2.15",
            "@vitejs/plugin-react": "^4.1.1",
            "typescript": "^5.2.2",
            "vite": "^5.0.0"
        }
    }
    
    with open("package.json", 'w') as f:
        json.dump(package_json, f, indent=2)
    
    print("✅ Created package.json")

def main():
    print_banner("🦅 Crow's Eye Marketing Agent - Web App Installer v2.0")
    
    if not check_dependencies():
        print("❌ Please install missing dependencies first")
        return False
    
    # Create web app directory
    web_dir = Path("web_app")
    web_dir.mkdir(exist_ok=True)
    os.chdir(web_dir)
    
    # Create package.json
    create_package_json()
    
    print_banner("🎉 Web App Structure Created!")
    print("✅ Ready for development!")
    print()
    print("🚀 Next steps:")
    print("   1. cd web_app")
    print("   2. npm install")
    print("   3. Create your React components")
    print("   4. npm run dev")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 