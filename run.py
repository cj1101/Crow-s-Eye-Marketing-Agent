#!/usr/bin/env python
"""
Run the Breadsmith Marketing Tool application with scheduling enabled
"""
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app_log.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("run")
logger.info("Starting Breadsmith Marketing Tool with scheduling enabled")

# Make sure src is in the path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Make sure the current directory is in the path
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

if __name__ == "__main__":
    # Always run with scheduling enabled
    from src.main import main
    sys.exit(main(enable_scheduling=True)) 