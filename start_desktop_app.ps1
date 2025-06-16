#!/usr/bin/env pwsh
# PowerShell script to start the Crow's Eye Desktop Application

Write-Host "🦅 Starting Crow's Eye Desktop Application" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+ and add it to PATH" -ForegroundColor Red
    exit 1
}

# Check if we're in the correct directory
if (-not (Test-Path "src/__main__.py")) {
    Write-Host "❌ src/__main__.py not found. Please run this script from the project root directory." -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (Test-Path "venv/Scripts/Activate.ps1") {
    Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
    & "./venv/Scripts/Activate.ps1"
} elseif (Test-Path ".venv/Scripts/Activate.ps1") {
    Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
    & "./.venv/Scripts/Activate.ps1"
} else {
    Write-Host "⚠️  No virtual environment found. Using system Python." -ForegroundColor Yellow
}

# Install requirements if needed
if (Test-Path "requirements.txt") {
    Write-Host "📦 Checking dependencies..." -ForegroundColor Blue
    pip install -r requirements.txt --quiet
}

Write-Host "🚀 Starting desktop application..." -ForegroundColor Green
Write-Host "📍 To close the application, press Ctrl+C in this terminal" -ForegroundColor Blue
Write-Host "===============================================" -ForegroundColor Green

# Start the desktop application
try {
    python -m src
} catch {
    Write-Host "❌ Error starting desktop application: $_" -ForegroundColor Red
    Write-Host "💡 Try running: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

Write-Host "👋 Desktop application closed." -ForegroundColor Green 