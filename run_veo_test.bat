@echo off
echo 🚀 Starting Veo 3 Test App...
echo.

REM Set the API key
set GOOGLE_API_KEY=AIzaSyARQhyKXzTvCzUEOL7hBOo691w5BDUarfU

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo 📦 Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Run the test app
echo 🎬 Launching Veo Test App...
python test_veo_app.py

pause 