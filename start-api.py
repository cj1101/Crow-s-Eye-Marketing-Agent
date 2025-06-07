#!/usr/bin/env python3
"""
Crow's Eye Marketing Platform API Startup Script
Unified startup for local development and production deployment.
"""

import os
import sys
import uvicorn
import argparse
from pathlib import Path

def get_port():
    """Get port from environment variables or default."""
    return int(os.environ.get("PORT", 8080))

def is_production():
    """Check if running in production environment."""
    return bool(os.environ.get("K_SERVICE")) or os.environ.get("NODE_ENV") == "production"

def setup_paths():
    """Setup Python paths for imports."""
    current_dir = Path(__file__).parent
    
    # Add current directory and src to Python path
    sys.path.insert(0, str(current_dir))
    sys.path.insert(0, str(current_dir / "src"))
    
    print(f"📁 Working directory: {current_dir}")
    print(f"🐍 Python path: {sys.path[:3]}...")

def check_environment():
    """Check and display environment information."""
    port = get_port()
    env_type = "Production" if is_production() else "Development"
    
    print(f"🌍 Environment: {env_type}")
    print(f"🚀 Port: {port}")
    print(f"🔑 JWT Secret: {'Set' if os.environ.get('JWT_SECRET_KEY') else 'Using default (change for production)'}")
    print(f"☁️  Google Cloud: {'Yes' if os.environ.get('K_SERVICE') else 'No'}")
    
    return port, env_type

def main():
    """Main startup function."""
    parser = argparse.ArgumentParser(description='Start Crow\'s Eye API')
    parser.add_argument('--dev', action='store_true', help='Run in development mode with auto-reload')
    parser.add_argument('--port', type=int, help='Port to run on (overrides environment)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--log-level', default='info', choices=['debug', 'info', 'warning', 'error'])
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🏹 CROW'S EYE MARKETING PLATFORM API")
    print("=" * 60)
    
    # Setup environment
    setup_paths()
    port, env_type = check_environment()
    
    # Override port if specified
    if args.port:
        port = args.port
        print(f"🔧 Port overridden to: {port}")
    
    # Import the FastAPI app
    try:
        from crow_eye_api.main import app
        print("✅ FastAPI application loaded successfully")
    except ImportError as e:
        print(f"❌ Failed to import FastAPI app: {e}")
        print("🔍 Checking available modules...")
        
        # Try alternative import paths
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'crow_eye_api'))
            from main import app
            print("✅ FastAPI application loaded from alternative path")
        except ImportError as e2:
            print(f"❌ Alternative import failed: {e2}")
            print(f"📁 Current working directory: {os.getcwd()}")
            print(f"📝 Files in current directory: {os.listdir('.')}")
            sys.exit(1)
    
    # Configure uvicorn settings
    uvicorn_config = {
        "app": app,
        "host": args.host,
        "port": port,
        "log_level": args.log_level
    }
    
    # Development mode settings
    if args.dev or not is_production():
        uvicorn_config.update({
            "reload": True,
            "reload_dirs": ["./crow_eye_api", "./src"],
            "reload_excludes": ["*.pyc", "__pycache__"]
        })
        print("🔄 Development mode: Auto-reload enabled")
    
    print("-" * 60)
    print(f"🚀 Starting server on http://{args.host}:{port}")
    print(f"📚 API Documentation: http://{args.host}:{port}/docs")
    print(f"❤️  Health Check: http://{args.host}:{port}/health")
    print("-" * 60)
    
    # Start the server
    try:
        uvicorn.run(**uvicorn_config)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 