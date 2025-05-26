#!/usr/bin/env python
"""
Run Breadsmith Marketing Tool application without scheduling.
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
logger = logging.getLogger("run")

def main():
    """Run the application without scheduling."""
    logger.info("Starting Breadsmith Marketing Tool with scheduling enabled")
    
    # Import from src
    from src.main import main as src_main
    
    # Run with scheduling enabled
    return src_main(enable_scheduling=True)

if __name__ == "__main__":
    # Remove any language parameters from sys.argv
    sys.argv = [arg for arg in sys.argv if not arg.startswith("--lang=")]
    sys.exit(main()) 