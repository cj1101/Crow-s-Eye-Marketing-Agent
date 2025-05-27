Write-Host "🚀 Starting Veo 3 Test App..." -ForegroundColor Green
Write-Host ""

# Set the API key
$env:GOOGLE_API_KEY = "AIzaSyARQhyKXzTvCzUEOL7hBOo691w5BDUarfU"
Write-Host "✅ API key set" -ForegroundColor Green

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