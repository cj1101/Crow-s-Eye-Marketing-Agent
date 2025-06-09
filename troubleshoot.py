#!/usr/bin/env python3
"""
🔧 Crow's Eye Marketing Tool - Comprehensive Troubleshooting Guide
"""
import os
import sys
import importlib
import subprocess
import requests
from pathlib import Path

def print_header():
    print("=" * 60)
    print("🔧 CROW'S EYE MARKETING TOOL TROUBLESHOOTING")
    print("=" * 60)
    print()

def ask_yn(question: str) -> bool:
    """Ask a yes/no question and return boolean."""
    while True:
        answer = input(f"{question} (y/n): ").lower().strip()
        if answer in ['y', 'yes']:
            return True
        elif answer in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")

def test_python_version():
    """Test Python version compatibility."""
    print("🐍 Testing Python Version...")
    version = sys.version_info
    print(f"Current Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 9:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.9+ required")
        return False

def test_required_packages():
    """Test if required packages are installed."""
    print("\n📦 Testing Required Packages...")
    
    required_packages = [
        'PySide6', 'requests', 'pillow', 'openai', 
        'google-generativeai', 'google-cloud-storage'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'pillow':
                importlib.import_module('PIL')
            else:
                importlib.import_module(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        if ask_yn("Install missing packages now?"):
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
                print("✅ Packages installed successfully")
                return True
            except subprocess.CalledProcessError:
                print("❌ Failed to install packages")
                return False
        return False
    
    return True

def test_api_connection():
    """Test connection to the deployed API."""
    print("\n🌐 Testing API Connection...")
    
    api_url = "https://crows-eye-api-2mgwzdcmnq-uc.a.run.app"
    
    try:
        # Test root endpoint
        response = requests.get(f"{api_url}/", timeout=10)
        if response.status_code == 200:
            print(f"✅ API root endpoint working")
        else:
            print(f"❌ API root returned status {response.status_code}")
            return False
        
        # Test health endpoint
        response = requests.get(f"{api_url}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ API health endpoint working")
        else:
            print(f"❌ API health returned status {response.status_code}")
            return False
        
        print(f"✅ API is accessible at: {api_url}")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API at {api_url}")
        if ask_yn("Try using local API instead?"):
            # Set environment variable for local API
            os.environ['USE_LOCAL_API'] = 'true'
            print("🔄 Set to use local API. You'll need to start the local API server.")
            return True
        return False
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False

def test_file_structure():
    """Test if required files and directories exist."""
    print("\n📁 Testing File Structure...")
    
    required_paths = [
        'src/',
        'src/core/',
        'src/core/app.py',
        'src/__main__.py',
        'data/',
        'crow_eye_api/',
        'requirements.txt'
    ]
    
    missing_paths = []
    
    for path in required_paths:
        if os.path.exists(path):
            print(f"✅ {path}")
        else:
            print(f"❌ {path}")
            missing_paths.append(path)
    
    if missing_paths:
        print(f"\n⚠️  Missing files/directories: {', '.join(missing_paths)}")
        return False
    
    return True

def test_permissions():
    """Test file permissions."""
    print("\n🔐 Testing Permissions...")
    
    # Test write permissions for data directory
    try:
        test_file = os.path.join('data', 'test_permissions.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("✅ Write permissions OK")
        return True
    except Exception as e:
        print(f"❌ Permission error: {e}")
        return False

def test_desktop_app_import():
    """Test if the desktop app can be imported."""
    print("\n🖥️  Testing Desktop App Import...")
    
    try:
        sys.path.insert(0, os.getcwd())
        from src.core.app import main
        print("✅ Desktop app can be imported")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_directories():
    """Create required directories if they don't exist."""
    print("\n📂 Creating Required Directories...")
    
    directories = [
        'data',
        'data/media',
        'data/output',
        'data/knowledge_base',
        'data/images',
        'data/media_gallery'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ {directory}")

def run_startup_test():
    """Run a quick startup test."""
    print("\n🚀 Running Startup Test...")
    
    try:
        # Import the main app function
        sys.path.insert(0, os.getcwd())
        from src.core.app import create_required_directories
        
        # Test directory creation
        create_required_directories()
        print("✅ Directory creation works")
        
        # Test API config
        from src.config.api_config import api_config
        success, message = api_config.test_connection()
        if success:
            print(f"✅ API connection: {message}")
        else:
            print(f"⚠️  API connection: {message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Startup test failed: {e}")
        return False

def main():
    """Main troubleshooting function."""
    print_header()
    
    all_tests_passed = True
    
    # Step 1: Python version
    if not test_python_version():
        all_tests_passed = False
        if not ask_yn("Continue despite Python version issue?"):
            return
    
    # Step 2: Required packages
    if not test_required_packages():
        all_tests_passed = False
        if not ask_yn("Continue despite missing packages?"):
            return
    
    # Step 3: File structure
    if not test_file_structure():
        all_tests_passed = False
        if not ask_yn("Continue despite missing files?"):
            return
    
    # Step 4: Create directories
    create_directories()
    
    # Step 5: Permissions
    if not test_permissions():
        all_tests_passed = False
        if not ask_yn("Continue despite permission issues?"):
            return
    
    # Step 6: API connection
    if not test_api_connection():
        all_tests_passed = False
        if not ask_yn("Continue despite API connection issues?"):
            return
    
    # Step 7: Desktop app import
    if not test_desktop_app_import():
        all_tests_passed = False
        if not ask_yn("Continue despite import issues?"):
            return
    
    # Step 8: Startup test
    if not run_startup_test():
        all_tests_passed = False
    
    # Final results
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("Your Crow's Eye Marketing Tool is ready to run!")
        print("\n📋 To start the desktop app:")
        print("   python -m src")
        print("\n🌐 API Documentation:")
        print("   https://crows-eye-api-2mgwzdcmnq-uc.a.run.app/docs")
    else:
        print("⚠️  SOME ISSUES DETECTED")
        print("Please resolve the issues above before running the application.")
        
        if ask_yn("Show detailed troubleshooting tips?"):
            show_troubleshooting_tips()
    
    print("=" * 60)

def show_troubleshooting_tips():
    """Show detailed troubleshooting tips."""
    print("\n🔍 DETAILED TROUBLESHOOTING TIPS:")
    print()
    print("1. 📦 Package Installation Issues:")
    print("   pip install --upgrade pip")
    print("   pip install -r requirements.txt")
    print()
    print("2. 🐍 Python Path Issues:")
    print("   Make sure you're in the project root directory")
    print("   Try: set PYTHONPATH=%cd%")
    print()
    print("3. 🌐 API Connection Issues:")
    print("   Check your internet connection")
    print("   The deployed API might be temporarily unavailable")
    print("   You can run a local API if needed")
    print()
    print("4. 🔐 Permission Issues:")
    print("   Run as administrator if on Windows")
    print("   Check if antivirus is blocking file access")
    print()
    print("5. 📁 Missing Files:")
    print("   Re-clone the repository")
    print("   Make sure you're in the correct directory")

if __name__ == "__main__":
    main() 