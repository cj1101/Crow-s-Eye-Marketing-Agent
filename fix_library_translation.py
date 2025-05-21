"""
Fix for LibraryWindow translation (DISABLED)
"""
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("fix_translation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fix_translation")

def apply_direct_translations():
    """Apply direct translations in the library_window.py file (DISABLED)"""
    logger.info("Translation functionality has been disabled")
    return False

def main():
    """Run the fix (DISABLED)"""
    logger.info("LibraryWindow translation fix is disabled")
    logger.info("Translation functionality has been removed while keeping the language dropdown UI")

if __name__ == "__main__":
    main() 