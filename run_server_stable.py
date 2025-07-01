"""
Stable server runner for testing - no file watching
"""

import uvicorn
import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if __name__ == "__main__":
    print("Starting Crow's Eye API server (stable mode - no auto-reload)...")
    print("Server will run on: http://localhost:8002")
    print("Access API docs at: http://localhost:8002/docs")
    
    # Run server without reload for stable testing
    uvicorn.run(
        "crow_eye_api.main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,  # Disable auto-reload for stable testing
        log_level="info"
    ) 