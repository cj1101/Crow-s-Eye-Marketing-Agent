# PowerShell script to run the Breadsmith Marketing Tool
# This script ensures proper directory navigation and execution

Write-Host "🚀 Starting Breadsmith Marketing Tool..." -ForegroundColor Green

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Change to the script directory
Set-Location $ScriptDir

# Check if Python is available
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "Python found, starting application..." -ForegroundColor Yellow
    python run.py
} else {
    Write-Host "Python not found in PATH. Please install Python or add it to your PATH." -ForegroundColor Red
    Read-Host "Press Enter to exit"
} 