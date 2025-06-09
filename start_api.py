#!/usr/bin/env python3
"""
Startup script for Crow's Eye API server.
Handles proper module path setup and server initialization.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def setup_environment():
    """Setup the Python environment for the API."""
    # Get the current directory
    current_dir = Path(__file__).parent.absolute()
    
    # Add current directory to Python path
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # Change to the API directory
    api_dir = current_dir / "crow_eye_api"
    if api_dir.exists():
        os.chdir(api_dir)
        print(f"✅ Changed to API directory: {api_dir}")
    else:
        print(f"❌ API directory not found: {api_dir}")
        return False
    
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "pydantic-settings"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def start_server(host="0.0.0.0", port=8000, reload=True):
    """Start the API server."""
    try:
        print(f"🚀 Starting Crow's Eye API server on {host}:{port}")
        print(f"📖 API Documentation will be available at: http://{host}:{port}/docs")
        print(f"🔍 Health check: http://{host}:{port}/health")
        print("="*60)
        
        # Set environment variable for Python path
        import os
        current_dir = os.getcwd()
        parent_dir = os.path.dirname(current_dir)
        
        # Add both current and parent directories to PYTHONPATH
        python_path = os.environ.get('PYTHONPATH', '')
        new_paths = [current_dir, parent_dir]
        
        for path in new_paths:
            if path not in python_path:
                python_path = f"{path}{os.pathsep}{python_path}" if python_path else path
        
        os.environ['PYTHONPATH'] = python_path
        
        # Use uvicorn directly
        import uvicorn
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return False
    
    return True

def main():
    """Main startup function."""
    print("🔧 Crow's Eye API Startup Script")
    print("="*50)
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        sys.exit(1)
    
    # Start server
    print("\n🚀 Starting server...")
    start_server()

if __name__ == "__main__":
    main() 