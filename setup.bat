@echo off
REM Setup script for Whisky_bot on Windows

echo.
echo ========================================
echo  Whisky_bot Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo [3/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/4] Creating .env file from template...
if not exist ".env" (
    copy .env.example .env
    echo .env file created! Please edit it with your tokens.
) else (
    echo .env file already exists.
)

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your tokens:
echo    - TELEGRAM_TOKEN: Get from @BotFather on Telegram
echo    - OPENROUTER_API_KEY: Get from https://openrouter.ai/keys
echo.
echo 2. Run the bot:
echo    python main.py
echo.
pause
