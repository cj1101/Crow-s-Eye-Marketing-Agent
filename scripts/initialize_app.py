#!/usr/bin/env python
"""
Initialization script for the Breadsmith Marketing Tool.
Creates necessary directories and installs requirements if needed.
"""
import os
import sys
import logging
import subprocess
from pathlib import Path

def setup_logging():
    """Set up basic logging for initialization."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("app_init.log", encoding="utf-8")
        ]
    )
    return logging.getLogger("init")

def create_directories():
    """Create required directories if they don't exist."""
    directories = [
        "data",
        "data/media",
        "data/output",
        "data/knowledge_base",
        "data/images",
        "data/media_gallery",
        "src/utils"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.info(f"Creating directory: {directory}")
            dir_path.mkdir(parents=True, exist_ok=True)
        else:
            logger.info(f"Directory already exists: {directory}")

def check_requirements():
    """Check if required packages are installed."""
    requirements = [
        "PyQt6",
        "Pillow"
    ]
    
    missing = []
    
    logger.info("Checking requirements...")
    for req in requirements:
        try:
            __import__(req.lower())
            logger.info(f"✅ {req} is installed")
        except ImportError:
            logger.warning(f"❌ {req} is not installed")
            missing.append(req)
            
    if missing:
        logger.info("Installing missing requirements...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            logger.info("Requirements installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install requirements: {e}")
            logger.info("Please install the following packages manually:")
            for pkg in missing:
                logger.info(f"  - {pkg}")

def create_default_files():
    """Create default configuration files if they don't exist."""
    # Meta credentials template
    if not os.path.exists("meta_credentials_template.json"):
        logger.info("Creating meta_credentials_template.json...")
        with open("meta_credentials_template.json", "w", encoding="utf-8") as f:
            f.write("""
{
    "app_id": "YOUR_APP_ID",
    "app_secret": "YOUR_APP_SECRET",
    "access_token": "YOUR_ACCESS_TOKEN",
    "instagram_business_id": "YOUR_INSTAGRAM_BUSINESS_ID"
}
            """.strip())
    
    # Presets file
    if not os.path.exists("presets.json"):
        logger.info("Creating presets.json...")
        with open("presets.json", "w", encoding="utf-8") as f:
            f.write("""
{
    "presets": {
        "Default": {
            "instructions": "Generate a warm, inviting caption that highlights the craft and quality of our bread.",
            "caption": "",
            "photo_edit": "warm"
        }
    },
    "schedules": []
}
            """.strip())
    
    # Library data file
    library_data_file = Path("data/library.json")
    if not library_data_file.exists():
        logger.info("Creating library data file...")
        library_data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(library_data_file, "w", encoding="utf-8") as f:
            f.write("""
{
    "version": "1.0",
    "items": {},
    "collections": {}
}
            """.strip())
            
    # Media status file
    if not os.path.exists("media_status.json"):
        logger.info("Creating media_status.json...")
        with open("media_status.json", "w", encoding="utf-8") as f:
            f.write("""
{
    "captions": {},
    "last_updated": ""
}
            """.strip())

def main():
    """Main initialization function."""
    logger.info("Starting initialization...")
    
    create_directories()
    check_requirements()
    create_default_files()
    
    logger.info("Initialization complete!")
    logger.info("You can now run the application with: python run.py")

if __name__ == "__main__":
    logger = setup_logging()
    main() 