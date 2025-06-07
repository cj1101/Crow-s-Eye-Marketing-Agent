@echo off
REM Crow's Eye API Start Script for Windows
REM This script starts the API server for local development

echo Starting Crow's Eye API...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.7 or higher.
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking dependencies...
pip install -r requirements.txt --quiet

REM Set environment variables
set ENVIRONMENT=development
set JWT_SECRET=your-secret-key-change-in-production

REM Start the API server
echo.
echo Starting API server on http://localhost:8000
echo API documentation available at http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the API
uvicorn crow_eye_api.main:app --reload --host 0.0.0.0 --port 8000

pause