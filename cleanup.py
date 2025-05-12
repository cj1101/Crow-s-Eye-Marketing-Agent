#!/usr/bin/env python
"""
Cleanup script to remove redundant files after code refactoring.
"""
import os
import shutil
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cleanup")

# Files to be deleted (redundant or moved files)
FILES_TO_DELETE = [
    # Moved to src/ui
    "knowledge_management.py",
    "pending_messages.py",
    "knowledge_simulator.py",
    
    # Redundant entry points
    "src/__main__.py",
    "run_with_scheduling.py",  # No longer needed since run.py always uses scheduling
    
    # Empty directories to clean up
    "src/core"
]

def cleanup_files():
    """Delete redundant files."""
    for file_path in FILES_TO_DELETE:
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
            elif os.path.isdir(file_path):
                if not os.listdir(file_path):  # Only delete if directory is empty
                    os.rmdir(file_path)
                    logger.info(f"Deleted empty directory: {file_path}")
                else:
                    logger.warning(f"Directory not empty, skipping: {file_path}")
            else:
                logger.warning(f"File not found, skipping: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {e}")

def main():
    """Run the cleanup process."""
    logger.info("Starting cleanup process...")
    
    # Confirm with user
    print("\nThe following files will be deleted:")
    for file_path in FILES_TO_DELETE:
        print(f"  - {file_path}")
    
    response = input("\nDo you want to continue? (y/n): ")
    if response.lower() != 'y':
        logger.info("Cleanup cancelled by user.")
        return
    
    # Perform cleanup
    cleanup_files()
    
    logger.info("Cleanup completed.")

if __name__ == "__main__":
    main() 