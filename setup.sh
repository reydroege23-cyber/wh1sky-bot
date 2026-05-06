#!/bin/bash

# Setup script for Whisky_bot on Linux/Mac

echo ""
echo "========================================"
echo " Whisky_bot Setup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8+ using:"
    echo "  - macOS: brew install python"
    echo "  - Ubuntu: sudo apt install python3 python3-venv"
    exit 1
fi

echo "[1/4] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

echo "[2/4] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment"
    exit 1
fi

echo "[3/4] Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo "[4/4] Creating .env file from template..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ".env file created! Please edit it with your tokens."
else
    echo ".env file already exists."
fi

echo ""
echo "========================================"
echo " Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your tokens:"
echo "   - TELEGRAM_TOKEN: Get from @BotFather on Telegram"
echo "   - GEMINI_API_KEY: Get from https://aistudio.google.com"
echo ""
echo "2. Run the bot:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
