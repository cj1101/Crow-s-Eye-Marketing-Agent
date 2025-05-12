"""
Main module for Breadsmith Marketing Tool application.
"""
import os
import sys
import logging
import platform
from PySide6.QtWidgets import QApplication

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
        "library/data"
    ]
    
    for directory in directories:
        dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', directory)
        if not os.path.exists(dir_path):
            logger.info(f"Creating directory: {directory}")
            os.makedirs(dir_path, exist_ok=True)
        else:
            logger.debug(f"Directory already exists: {directory}")

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
    logger.info(f"Starting application v5.0.0 {'with scheduling' if enable_scheduling else ''}")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"System: {platform.system()} {platform.release()}")
    
    # Create required directories
    create_required_directories()
    
    # Create and run the application
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Social Media Caption Generator")
    app.setApplicationVersion("5.0.0")
    app.setOrganizationName("Breadsmith Marketing")
    
    # Load stylesheet if exists
    if os.path.exists("styles.qss"):
        with open("styles.qss", "r") as f:
            app.setStyleSheet(f.read())
    
    # Import here to avoid circular imports
    from .models.app_state import AppState
    from .handlers.media_handler import MediaHandler
    from .handlers.library_handler import LibraryManager
    from .ui.main_window import MainWindow
    
    # Initialize components
    app_state = AppState()
    media_handler = MediaHandler(app_state)
    library_manager = LibraryManager()
    
    if enable_scheduling:
        # Import scheduling components
        from .handlers.scheduling_handler import PostScheduler, SchedulingSignals
        
        # Initialize scheduler
        scheduling_signals = SchedulingSignals()
        scheduler = PostScheduler(app_state, scheduling_signals)
        
        # Create main window with scheduler
        window = MainWindow(
            app_state=app_state,
            media_handler=media_handler,
            library_manager=library_manager,
            scheduler=scheduler
        )
        
        # Start scheduler
        scheduler.start()
    else:
        # Create main window without scheduler
        window = MainWindow(
            app_state=app_state,
            media_handler=media_handler,
            library_manager=library_manager
        )
    
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    # Run without scheduling by default
    sys.exit(main(enable_scheduling=False)) 