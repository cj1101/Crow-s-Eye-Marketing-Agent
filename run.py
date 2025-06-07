#!/usr/bin/env python3
"""
Crow's Eye API Server - Local Development
For production, use main.py with Google Cloud App Engine
"""

import sys
import os
import uvicorn
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main startup function for local development."""
    
    # Add the src directory to the Python path
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    try:
        # Import the FastAPI app
        from crow_eye_api.main import app
        
        port = int(os.environ.get("PORT", 8080))
        
        logger.info("Starting Crow's Eye API Server for local development")
        logger.info(f"Server: http://localhost:{port}")
        logger.info(f"Docs: http://localhost:{port}/docs")
        logger.info("Note: For production, deploy to Google Cloud App Engine")
        
        # Run the server
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port,
            log_level="info"
        )
        
    except ImportError as e:
        logger.error(f"Failed to import app: {e}")
        logger.error("Make sure dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 