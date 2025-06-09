#!/usr/bin/env python3
"""
Safe Build Script for Breadsmith Marketing Tool
This script builds the application with antivirus-friendly settings.
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

def print_status(message):
    """Print status message with formatting."""
    print(f"🔨 {message}")

def print_warning(message):
    """Print warning message."""
    print(f"⚠️  {message}")

def print_success(message):
    """Print success message."""
    print(f"✅ {message}")

def print_error(message):
    """Print error message."""
    print(f"❌ {message}")

def check_requirements():
    """Check if all build requirements are met."""
    print_status("Checking build requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print_error("Python 3.8 or higher is required")
        return False
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print_success(f"PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print_error("PyInstaller not found. Install with: pip install PyInstaller")
        return False
    
    # Check if entry point exists
    if not os.path.exists('scripts/run.py'):
        print_error("Entry point 'scripts/run.py' not found")
        return False
    
    return True

def clean_build_dirs():
    """Clean previous build directories."""
    print_status("Cleaning previous build directories...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print_success(f"Cleaned {dir_name}/")

def create_build_info():
    """Create build information file."""
    print_status("Creating build information...")
    
    build_info = {
        "build_date": "2024-01-01",
        "version": "5.0.0",
        "build_type": "safe_release",
        "antivirus_optimized": True,
        "signed": False,
        "upx_compressed": False
    }
    
    with open('build_info.json', 'w') as f:
        json.dump(build_info, f, indent=2)
    
    print_success("Build info created")

def build_application():
    """Build the application using PyInstaller."""
    print_status("Building application with PyInstaller...")
    
    # Build command with safe settings
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        'breadsmith_marketing_tool.spec',
        '--clean',
        '--noconfirm',
        '--log-level=INFO'
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print_success("Build completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Build failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False

def create_installer_readme():
    """Create README for the installer."""
    print_status("Creating installer documentation...")
    
    readme_content = """# Breadsmith Marketing Tool - Safe Download

## 🛡️ Antivirus False Positive Notice

This application may trigger false positive warnings from some antivirus software. This is common with PyInstaller-built applications and is NOT a virus.

### Why This Happens:
- **PyInstaller Bundling**: The app bundles Python and libraries into a single executable
- **Heuristic Scanning**: Some antivirus software flags unknown executables
- **Unsigned Executable**: The app is not digitally signed (would require expensive certificate)

### How to Safely Download:
1. **Temporarily disable real-time protection** in your antivirus during download
2. **Add exception** for the download folder in your antivirus settings
3. **Verify the source** - only download from official sources
4. **Check file hash** (provided below) to ensure integrity

### Alternative Installation Methods:
1. **Python Source**: Run directly from Python source code
2. **Portable Version**: Use the portable folder version instead
3. **Web Version**: Use the web-based version at [your-website.com]

### File Information:
- **Application**: Breadsmith Marketing Tool
- **Version**: 5.0.0
- **Build Type**: Safe Release (No UPX compression)
- **Digital Signature**: None (unsigned)
- **Build Date**: 2024-01-01

### Support:
If you encounter issues, please contact support or use the Python source version.

---
**This is legitimate software for social media marketing and content creation.**
"""
    
    with open('dist/README_DOWNLOAD_SAFETY.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print_success("Installer documentation created")

def create_portable_version():
    """Create a portable version to avoid antivirus issues."""
    print_status("Creating portable version...")
    
    portable_dir = Path('dist/Breadsmith_Marketing_Tool_Portable')
    portable_dir.mkdir(exist_ok=True)
    
    # Copy the built application
    if os.path.exists('dist/Breadsmith_Marketing_Tool'):
        shutil.copytree('dist/Breadsmith_Marketing_Tool', portable_dir / 'App', dirs_exist_ok=True)
    
    # Create launcher script
    launcher_content = '''@echo off
title Breadsmith Marketing Tool
echo Starting Breadsmith Marketing Tool...
echo.
echo If Windows Defender shows a warning, this is a false positive.
echo This is legitimate software for social media marketing.
echo.
pause
cd /d "%~dp0App"
start "" "Breadsmith_Marketing_Tool.exe"
'''
    
    with open(portable_dir / 'Launch_Breadsmith_Marketing_Tool.bat', 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    
    print_success("Portable version created")

def create_web_installer_info():
    """Create information for web-based installer."""
    print_status("Creating web installer information...")
    
    # Web installer HTML template
    web_info = {
        "download_methods": [
            {
                "name": "Direct Download",
                "description": "Download executable directly",
                "warning": "May trigger antivirus false positive",
                "safe_download_steps": [
                    "Temporarily disable antivirus real-time protection",
                    "Download the file",
                    "Add exception for the download folder",
                    "Run the application",
                    "Re-enable antivirus protection"
                ]
            },
            {
                "name": "Portable Version",
                "description": "Extract and run without installation",
                "warning": "Recommended for users with strict antivirus",
                "safe_download_steps": [
                    "Download the portable ZIP",
                    "Extract to a folder",
                    "Run the launcher script",
                    "Add folder to antivirus exceptions if needed"
                ]
            },
            {
                "name": "Python Source",
                "description": "Run from Python source code",
                "warning": "Requires Python 3.8+ installed",
                "safe_download_steps": [
                    "Install Python 3.8+",
                    "Download source code",
                    "Run: pip install -r requirements.txt",
                    "Run: python scripts/run.py"
                ]
            }
        ],
        "antivirus_whitelist_instructions": {
            "windows_defender": [
                "Open Windows Security",
                "Go to Virus & threat protection",
                "Click 'Manage settings' under Virus & threat protection settings",
                "Click 'Add or remove exclusions'",
                "Add the download folder or executable"
            ],
            "generic_antivirus": [
                "Open your antivirus software",
                "Look for 'Exceptions', 'Exclusions', or 'Whitelist' settings",
                "Add the downloaded file or folder",
                "Temporarily disable real-time protection during download"
            ]
        }
    }
    
    with open('dist/web_installer_info.json', 'w', encoding='utf-8') as f:
        json.dump(web_info, f, indent=2)
    
    print_success("Web installer information created")

def main():
    """Main build process."""
    print("🚀 Breadsmith Marketing Tool - Safe Build Process")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Clean previous builds
    clean_build_dirs()
    
    # Create build info
    create_build_info()
    
    # Build application
    if not build_application():
        sys.exit(1)
    
    # Create additional files
    create_installer_readme()
    create_portable_version()
    create_web_installer_info()
    
    print("\n" + "=" * 50)
    print_success("Build completed successfully!")
    print("\n📦 Output files:")
    print("  - dist/Breadsmith_Marketing_Tool/ (Main application)")
    print("  - dist/Breadsmith_Marketing_Tool_Portable/ (Portable version)")
    print("  - dist/README_DOWNLOAD_SAFETY.txt (Safety instructions)")
    print("  - dist/web_installer_info.json (Web installer data)")
    
    print("\n🛡️ Antivirus Safety Notes:")
    print("  - UPX compression disabled to reduce false positives")
    print("  - Version information added to executable")
    print("  - Console mode enabled for transparency")
    print("  - Portable version created as alternative")
    
    print("\n🌐 For Web Distribution:")
    print("  - Use the web_installer_info.json for your website")
    print("  - Provide multiple download options")
    print("  - Include clear safety instructions")
    print("  - Consider offering Python source as alternative")

if __name__ == "__main__":
    main() 