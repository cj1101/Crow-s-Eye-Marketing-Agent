@echo off
echo 🎬 Running Veo Video Generation Test...
echo.

REM Check if GOOGLE_API_KEY environment variable is set
if "%GOOGLE_API_KEY%"=="" (
    echo ❌ Error: GOOGLE_API_KEY environment variable not set
    echo Please set your Google API key as an environment variable:
    echo   set GOOGLE_API_KEY=your_api_key_here
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Virtual environment activated
) else (
    echo ⚠️  No virtual environment found
)

REM Run the test
python -m tests.test_veo_app

echo.
echo ✅ Test completed!
pause 