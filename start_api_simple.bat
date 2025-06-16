@echo off
echo 🚀 Starting Crow's Eye API Server...
echo.
echo 📖 API Documentation: http://localhost:8000/docs
echo 🔍 Health Check: http://localhost:8000/health
echo 🧪 Test Endpoint: http://localhost:8000/test
echo.
uvicorn crow_eye_api.main:app --host 0.0.0.0 --port 8000 --reload
pause 