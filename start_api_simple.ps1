#!/usr/bin/env powershell

Write-Host "🚀 Starting Crow's Eye API Server..." -ForegroundColor Green
Write-Host ""
Write-Host "📖 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🔍 Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "🧪 Test Endpoint: http://localhost:8000/test" -ForegroundColor Cyan
Write-Host ""

uvicorn crow_eye_api.main:app --host 0.0.0.0 --port 8000 --reload

Read-Host "Press Enter to continue..." 