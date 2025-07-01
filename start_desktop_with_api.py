#!/usr/bin/env python3
"""
Startup script for Crow's Eye Marketing Agent
Ensures both the API server and desktop application are running
"""

import os
import sys
import time
import signal
import logging
import subprocess
import threading
import requests
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("startup_log.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("startup")

class StartupManager:
    """Manages the startup and coordination of API server and desktop app."""
    
    def __init__(self):
        self.api_process = None
        self.desktop_process = None
        self.api_port = 8002
        self.api_url = f"http://localhost:{self.api_port}"
        self.shutdown_requested = False
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.shutdown_requested = True
        self.cleanup()
        sys.exit(0)
    
    def check_api_health(self):
        """Check if the API server is healthy."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def wait_for_api(self, timeout=30):
        """Wait for the API server to become ready."""
        logger.info("Waiting for API server to start...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.check_api_health():
                logger.info("API server is ready!")
                return True
            
            time.sleep(1)
        
        logger.error("API server failed to start within timeout")
        return False
    
    def start_api_server(self):
        """Start the API server."""
        try:
            logger.info("Starting API server...")
            
            # Use the run_local_server.py script
            server_script = project_root / "run_local_server.py"
            
            if not server_script.exists():
                logger.error("run_local_server.py not found!")
                return False
            
            # Start the server process
            self.api_process = subprocess.Popen([
                sys.executable, 
                str(server_script)
            ], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(project_root),
            env={**os.environ, "PYTHONPATH": str(project_root)}
            )
            
            logger.info(f"API server process started with PID: {self.api_process.pid}")
            
            # Wait for the server to be ready
            if self.wait_for_api():
                return True
            else:
                logger.error("API server failed to start properly")
                self.cleanup_api()
                return False
                
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            return False
    
    def start_desktop_app(self):
        """Start the desktop application."""
        try:
            logger.info("Starting desktop application...")
            
            # Import and run the desktop app
            from src.core.app import main
            
            # Set environment variable to use local API
            os.environ["USE_LOCAL_API"] = "true"
            os.environ["CROWS_EYE_API_URL"] = self.api_url
            
            # Run the desktop app
            exit_code = main()
            
            logger.info(f"Desktop application exited with code: {exit_code}")
            return exit_code
            
        except Exception as e:
            logger.error(f"Failed to start desktop application: {e}")
            return 1
    
    def cleanup_api(self):
        """Clean up the API server process."""
        if self.api_process:
            try:
                logger.info("Stopping API server...")
                self.api_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.api_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("API server didn't shut down gracefully, forcing...")
                    self.api_process.kill()
                    self.api_process.wait()
                
                logger.info("API server stopped")
            except Exception as e:
                logger.error(f"Error stopping API server: {e}")
            finally:
                self.api_process = None
    
    def cleanup(self):
        """Clean up all processes."""
        logger.info("Cleaning up processes...")
        self.cleanup_api()
    
    def run(self):
        """Main startup routine."""
        logger.info("=== Crow's Eye Marketing Agent Startup ===")
        
        try:
            # Check if API is already running
            if self.check_api_health():
                logger.info("API server is already running, skipping startup")
            else:
                # Start API server
                if not self.start_api_server():
                    logger.error("Failed to start API server")
                    return 1
            
            # Start desktop application
            exit_code = self.start_desktop_app()
            
            return exit_code
            
        except KeyboardInterrupt:
            logger.info("Startup interrupted by user")
            return 0
        except Exception as e:
            logger.error(f"Startup failed: {e}")
            return 1
        finally:
            self.cleanup()

def check_dependencies():
    """Check if required dependencies are available."""
    try:
        import PySide6
        import requests
        import uvicorn
        import fastapi
        import sqlalchemy
        logger.info("All required dependencies found")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        print(f"""
Missing required dependency: {e}

Please install the required dependencies:
pip install -r requirements.txt

Or install individually:
pip install PySide6 requests uvicorn fastapi sqlalchemy psycopg2-binary
""")
        return False

def main():
    """Main entry point."""
    print("=" * 60)
    print("🦅 Crow's Eye Marketing Agent")
    print("   Integrated API + Desktop Application")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Check if we're in the right directory
    if not (project_root / "src").exists():
        logger.error("Please run this script from the project root directory")
        return 1
    
    # Create and run startup manager
    startup_manager = StartupManager()
    return startup_manager.run()

if __name__ == "__main__":
    sys.exit(main()) 