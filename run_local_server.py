#!/usr/bin/env python3
"""
Run the API server locally with proper environment configuration.
"""

import os
import sys
import subprocess

# Set environment variables for local development
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/crow_eye.db"
os.environ["JWT_SECRET_KEY"] = "pfxyGkNmRtHqLvWdZbJcEuPnSgKjDhGfTrYwMxBvNmQpLkJhGfDsEtRyUiOpAsWxCvBnMjKhGfDsEr"
os.environ["PROJECT_NAME"] = "Crow's Eye Marketing Agent - Local Development"
os.environ["ENVIRONMENT"] = "development"

print("🚀 Starting Crow's Eye API server locally...")
print(f"📁 Database: {os.environ['DATABASE_URL']}")
print(f"🔧 Environment: {os.environ['ENVIRONMENT']}")
print(f"🌐 Server will run on: http://localhost:8002")
print()

# Run uvicorn from the root directory so paths work correctly
try:
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "crow_eye_api.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8002",
        "--reload"
    ], check=True)
except KeyboardInterrupt:
    print("\n👋 Server stopped by user")
except Exception as e:
    print(f"❌ Server failed to start: {e}")
    sys.exit(1) 