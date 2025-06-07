#!/bin/bash

# Crow's Eye API Start Script
# This script starts the API server for local development

echo "🚀 Starting Crow's Eye API..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

# Check if requirements are installed
echo "📦 Checking dependencies..."
pip3 install -r requirements.txt --quiet

# Set environment variables
export ENVIRONMENT="development"
export JWT_SECRET="your-secret-key-change-in-production"

# Start the API server
echo "🌐 Starting API server on http://localhost:8000"
echo "📖 API documentation available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the API
uvicorn crow_eye_api.main:app --reload --host 0.0.0.0 --port 8000