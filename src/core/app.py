"""
Main module for Breadsmith Marketing Tool application.
"""
import os
import sys
import logging
import platform
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator, QLibraryInfo, QLocale, Qt

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app_log.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")

def create_required_directories():
    """Create required directories if they don't exist."""
    directories = [
        "media_library",
        "output",
        "knowledge_base",
        "library",
        "library/images",
        "library/data",
        "media_gallery"
    ]
    
    for directory in directories:
        dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', directory)
        if not os.path.exists(dir_path):
            logger.info(f"Creating directory: {directory}")
            os.makedirs(dir_path, exist_ok=True)
        else:
            logger.debug(f"Directory already exists: {directory}")

def load_translations(app, lang_code: str):
    """
    Load translations functionality (Currently disabled).
    
    Args:
        app: The QApplication instance
        lang_code: The language code (e.g. 'en', 'fr')
    
    Returns:
        bool: Always returns True since functionality is disabled
    """
    # Translations functionality has been disabled
    # Only keeping the function for future implementation
    logger.info(f"Translation loading for {lang_code} is disabled")
    return True

def main(enable_scheduling=False):
    """
    Main function to run the application.
    
    Args:
        enable_scheduling: Whether to enable scheduling
        
    Returns:
        int: Exit code
    """
    # Log startup information
    logger.info("Logging initialized")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"System: {platform.system()} {platform.release()}")
    
    # Create required directories
    create_required_directories()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Crow's Eye")
    app.setApplicationVersion("5.0.0")
    
    # Ensure proper scaling on high DPI screens
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Default language is English, ignoring command line args for language
    app.setProperty("current_language", "en")
    app.setProperty("json_translations", {})  # Empty dict for default language
    
    # Initialize I18N system
    from ..i18n import i18n
    
    # Create application state
    from ..models.app_state import AppState
    from ..features.media_processing.media_handler import MediaHandler
    from ..handlers.library_handler import LibraryManager
    from ..ui.main_window import MainWindow
    
    app_state = AppState()
    
    # Create media handler
    media_handler = MediaHandler(app_state)
    
    # Create library manager
    library_manager = LibraryManager()
    
    # Create main window
    window = MainWindow(
        app_state=app_state,
        media_handler=media_handler,
        library_manager=library_manager
    )
    
    window.show()
    
    # Run application
    return app.exec_()

if __name__ == "__main__":
    # Run without scheduling by default
    sys.exit(main(enable_scheduling=False)) 