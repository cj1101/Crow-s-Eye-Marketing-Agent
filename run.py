#!/usr/bin/env python3
"""
Launcher script for the Breadsmith Marketing Tool.
Run this file to start the application.
"""

import sys
import os

# Add the current directory to Python path so we can import src modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Now we can import and run the main application
from src.core.app import main

if __name__ == "__main__":
    print("🚀 Starting Breadsmith Marketing Tool...")
    sys.exit(main()) 