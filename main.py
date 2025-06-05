#!/usr/bin/env python3
"""
Crow's Eye Marketing Platform
Main entry point for the application.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.app import main

if __name__ == "__main__":
    main() 