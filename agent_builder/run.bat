@echo off
REM AI Agent Builder - Startup Script

echo.
echo ====================================================================
echo  🚀 AI AGENT BUILDER - STARTUP
echo ====================================================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo ❌ .env file not found!
    echo.
    echo Quick setup:
    echo   1. Run: python setup_env.py
    echo   2. Enter your API credentials
    echo   3. Run this script again
    echo.
    pause
    exit /b 1
)

REM Check if Ollama is running
echo Checking Ollama...
timeout /t 1 /nobreak >nul

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Install Python 3.8+
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt >nul 2>&1

REM Verify credentials
echo.
echo Verifying credentials...
python setup_env.py --check

REM Clear screen
cls

echo.
echo ====================================================================
echo  ✅ READY TO START!
echo ====================================================================
echo.
echo Starting AI Agent Builder...
echo.
echo 🌐 Visit: http://localhost:7861
echo.
echo Press Ctrl+C to stop the server
echo.
echo ====================================================================
echo.

REM Run app
python app.py

pause
