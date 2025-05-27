Write-Host "🚀 Starting Veo 3 Test App..." -ForegroundColor Green
Write-Host ""

# Use environment variable instead of hardcoded key
if (-not $env:GOOGLE_API_KEY) {
    Write-Host "❌ Error: GOOGLE_API_KEY environment variable not set" -ForegroundColor Red
    Write-Host "Please set your Google API key as an environment variable:" -ForegroundColor Yellow
    Write-Host "  `$env:GOOGLE_API_KEY = 'your_api_key_here'" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
}

# Run the test app
Write-Host "🎬 Launching Veo Test App..." -ForegroundColor Cyan
python test_veo_app.py

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 