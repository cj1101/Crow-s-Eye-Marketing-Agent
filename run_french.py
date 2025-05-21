"""
Run the marketing tool application (French language functionality disabled).
"""
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app_log.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run the app normally"""
    logger.info("French language functionality has been disabled")
    
    # Import main function
    from src.main import main as original_main
    
    # Run the original main function
    return original_main(enable_scheduling=True)

if __name__ == "__main__":
    sys.exit(main()) 