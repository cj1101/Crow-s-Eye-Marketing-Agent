#!/bin/bash

# Crow's Eye API Startup Script
# This script starts the FastAPI server with proper configuration

echo "🐦‍⬛ Starting Crow's Eye Marketing Platform API..."

# Set environment variables if not already set
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-crow-eye-secret-key-change-in-production}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/media
mkdir -p data/audio
mkdir -p data/galleries

# Start the API server
echo "🚀 Starting FastAPI server..."
echo "📖 API Documentation will be available at: http://localhost:8000/docs"
echo "🔄 Alternative docs at: http://localhost:8000/redoc"
echo ""

uvicorn crow_eye_api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info 