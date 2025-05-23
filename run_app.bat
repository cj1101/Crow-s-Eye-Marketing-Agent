@echo off
echo Starting Crow's Eye Marketing Assistant...
python -m src.main

REM Check if a Python environment is activated
if defined VIRTUAL_ENV (
    python run.py
) else (
    REM Try to find Python in PATH
    python run.py
    if errorlevel 1 (
        echo Python not found in PATH. Trying with python3...
        python3 run.py
    )
)

if %errorlevel% neq 0 (
    echo Application exited with an error. See app_log.log for details.
)

echo Application closed.
pause 