@echo off
title Breadsmith Marketing Tool - Safe Build
echo.
echo ====================================================
echo   Breadsmith Marketing Tool - Safe Build Process
echo ====================================================
echo.
echo This script will build the application with antivirus-friendly settings.
echo.
pause

echo Starting safe build process...
python build_safe.py

echo.
echo Build process completed!
echo.
echo Check the 'dist' folder for the output files:
echo   - Breadsmith_Marketing_Tool (Main application)
echo   - Breadsmith_Marketing_Tool_Portable (Portable version) 
echo   - README_DOWNLOAD_SAFETY.txt (Safety instructions)
echo.
pause 