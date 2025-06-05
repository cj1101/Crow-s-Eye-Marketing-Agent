@echo off
REM Crow's Eye API Startup Script for Windows
REM This script starts the FastAPI server with proper configuration

echo 🐦‍⬛ Starting Crow's Eye Marketing Platform API...

REM Set environment variables if not already set
if not defined PYTHONPATH set PYTHONPATH=%PYTHONPATH%;%CD%\src
if not defined JWT_SECRET_KEY set JWT_SECRET_KEY=crow-eye-secret-key-change-in-production

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Create necessary directories
echo 📁 Creating data directories...
if not exist "data\media" mkdir data\media
if not exist "data\audio" mkdir data\audio
if not exist "data\galleries" mkdir data\galleries

REM Start the API server
echo 🚀 Starting FastAPI server...
echo 📖 API Documentation will be available at: http://localhost:8000/docs
echo 🔄 Alternative docs at: http://localhost:8000/redoc
echo.

uvicorn crow_eye_api.main:app --host 0.0.0.0 --port 8000 --reload --log-level info

pause 