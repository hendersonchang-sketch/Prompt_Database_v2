@echo off
chcp 65001 >nul
REM BananaDB Quick Start Script
REM This script will start the FastAPI server automatically

echo ========================================
echo   BananaDB Starting...
echo ========================================
echo.

REM Check if .env file exists
if not exist .env (
    echo WARNING: .env file not found
    echo Please copy .env.example to .env and set GEMINI_API_KEY
    echo.
    pause
    exit /b 1
)

REM Check if API key is configured
findstr /C:"your-gemini-api-key-here" .env >nul
if %errorlevel%==0 (
    echo WARNING: Gemini API key not configured
    echo Please edit .env file and enter your actual API key
    echo.
    pause
    exit /b 1
)

echo Environment variables configured
echo.
echo Starting FastAPI server...
echo Web UI: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python -m uvicorn app:app --reload --port 8000
