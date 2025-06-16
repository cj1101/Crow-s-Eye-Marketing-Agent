@echo off
REM Batch script to start the Crow's Eye Desktop Application

echo 🦅 Starting Crow's Eye Desktop Application
echo =========================================

REM Check if we're in the correct directory
if not exist "src\__main__.py" (
    echo ❌ src\__main__.py not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Check if virtual environment exists and activate it
if exist "venv\Scripts\activate.bat" (
    echo 🔧 Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo 🔧 Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  No virtual environment found. Using system Python.
)

REM Install requirements if needed
if exist "requirements.txt" (
    echo 📦 Installing/updating dependencies...
    pip install -r requirements.txt --quiet
)

echo 🚀 Starting desktop application...
echo 📍 To close the application, close the GUI window or press Ctrl+C
echo ===============================================

REM Start the desktop application
python -m src

if errorlevel 1 (
    echo ❌ Error starting desktop application
    echo 💡 Try running: pip install -r requirements.txt
    pause
    exit /b 1
)

echo 👋 Desktop application closed.
pause 