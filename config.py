"""
Configuration file for Whisky_bot
Store all configuration in one place for easy management
"""

import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =========================
# API CREDENTIALS
# =========================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8771300086:AAHpos-PeRziKVr3za4XbMq0_MibJUVOznA"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyB0QWChnufXOBLuvcGY1wOta3SBspSO6vQ"

# Validate credentials exist
if not TELEGRAM_TOKEN:
    print("⚠️ Warning: TELEGRAM_TOKEN not found in environment")
if not GEMINI_API_KEY:
    print("⚠️ Warning: GEMINI_API_KEY not found in environment")

# =========================
# BOT SETTINGS
# =========================

# Admin user IDs
ADMIN_IDS = [
    8537521522,
    8577797097,
    8707676185,
    8737737935,
]

# Maximum warnings before auto-ban
MAX_WARNINGS = 3

# Mute duration in minutes
MUTE_DURATION = 10

# =========================
# CONTENT FILTERING
# =========================

BAD_WORDS = [
    "fuck arya",
    "rape arya",
    "fuck u arya",
    "fuck arya mother",
    "fuck arya dad",
    "fuck arya father",
    "fuck arya mom",
    "sex with arya",
    "/fuck arya",
    "/rape arya",
    "/sex arya","fuck arya",
    "arya bitch",
    "arya slut",
    "arya trash",
    "arya loser",
    "arya idiot",
    "arya clown",
    "arya sucks",
    "ugly arya",
    "stupid arya",
    "hate arya",
    "shut up arya",
    "arya annoying",
    "arya fake",
    "arya toxic",
    "arya cringe",
    "arya pathetic"

]

# =========================
# SPAM PROTECTION
# =========================

SPAM_LIMIT = 5  # messages per time period
SPAM_TIME = 10  # seconds

# =========================
# AI SETTINGS
# =========================

AI_MODEL = "gemini-2.0-flash"
AI_TIMEOUT = 10  # seconds
MAX_RESPONSE_LENGTH = 4096  # Telegram limit

# =========================
# DATA STORAGE
# =========================

DATA_FILE = "bot_data.json"
LOG_FILE = "bot.log"

# =========================
# LOGGING
# =========================

LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# =========================
# FEATURE FLAGS
# =========================

ENABLE_STATS = True  # Track user statistics
ENABLE_LOGGING = True  # Log all activity
ENABLE_AUTO_MODERATION = True  # Auto-delete NSFW content
