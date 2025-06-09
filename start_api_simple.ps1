#!/usr/bin/env powershell

Write-Host "🔧 Starting Crow's Eye API..." -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Yellow

# Check if we're in the right directory
$currentLocation = Get-Location
Write-Host "📁 Current directory: $currentLocation" -ForegroundColor Cyan

# Navigate to the API directory if needed
if (-not (Test-Path "main.py")) {
    if (Test-Path "crow_eye_api\main.py") {
        Set-Location "crow_eye_api"
        Write-Host "✅ Changed to API directory" -ForegroundColor Green
    } else {
        Write-Host "❌ Cannot find main.py file" -ForegroundColor Red
        exit 1
    }
}

# Test import first
Write-Host "🧪 Testing module import..." -ForegroundColor Cyan
try {
    python -c "import main; print('✅ Main module imported successfully')"
} catch {
    Write-Host "❌ Module import failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🚀 Starting server on http://0.0.0.0:8000" -ForegroundColor Green
Write-Host "📖 API Documentation: http://0.0.0.0:8000/docs" -ForegroundColor Blue
Write-Host "🔍 Health check: http://0.0.0.0:8000/health" -ForegroundColor Blue
Write-Host "🔍 Root endpoint: http://0.0.0.0:8000/" -ForegroundColor Blue
Write-Host "🔍 API Health: http://0.0.0.0:8000/api/v1/health" -ForegroundColor Blue
Write-Host "=================================" -ForegroundColor Yellow

# Start the server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload 