# Crow's Eye API Startup Script for PowerShell
# This script properly starts the API server with correct module paths

Write-Host "🔧 Crow's Eye API Startup Script" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "crow_eye_api")) {
    Write-Host "❌ crow_eye_api directory not found. Please run from project root." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Found crow_eye_api directory" -ForegroundColor Green

# Start the API server using our startup script
Write-Host "🚀 Starting API server..." -ForegroundColor Yellow
Write-Host "📖 API Documentation will be available at: http://localhost:8000/docs" -ForegroundColor Blue
Write-Host "🔍 Health check: http://localhost:8000/health" -ForegroundColor Blue
Write-Host "🛑 Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan

try {
    python start_api.py
} catch {
    Write-Host "❌ Failed to start API server: $_" -ForegroundColor Red
    exit 1
} 