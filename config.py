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
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or "sk-or-v1-your-key-here"

# Validate credentials exist
if not TELEGRAM_TOKEN:
    print("⚠️ Warning: TELEGRAM_TOKEN not found in environment")
if not OPENROUTER_API_KEY:
    print("⚠️ Warning: OPENROUTER_API_KEY not found in environment")

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
# AI SETTINGS (OpenRouter)
# =========================

AI_MODEL = "meta-llama/llama-3.1-8b-instruct"  # OpenRouter model
AI_TIMEOUT = 30  # seconds (increased for reliability)
MAX_RESPONSE_LENGTH = 4096  # Telegram limit
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# =========================
# COOLDOWN SETTINGS (per user)
# =========================

ENABLE_RATE_LIMITING = True  # Enable/disable cooldown system
AI_COOLDOWN = 5  # seconds between /ai commands
SPEAK_COOLDOWN = 3  # seconds between speak mode replies
COMMAND_COOLDOWN = 2  # seconds between other commands

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
# ECONOMY SYSTEM (VIRTUAL ONLY)
# =========================

# ⚠️ IMPORTANT: This system uses VIRTUAL CURRENCY ONLY - NO REAL MONEY VALUE

# Owner ID (only this user can use admin economy commands)
OWNER_ID = 8577797097

# Starting balance for new users
STARTING_BALANCE = 100

# Economy cooldowns (seconds)
DAILY_COOLDOWN = 86400  # 24 hours
GAMBLING_COOLDOWN = 2  # seconds between gambles

# Betting limits
MIN_BET = 1
MAX_BET = 1000000

# Daily reward amount
DAILY_REWARD = 50

# Gambling odds and rewards
COINFLIP_ODDS = 50  # 50/50
COINFLIP_MULTIPLIER = 2  # Win = 2x bet

SLOTS_JACKPOT_CHANCE = 0.02  # 2% chance
SLOTS_JACKPOT_MULTIPLIER = 10  # 10x bet for jackpot
SLOTS_WIN_CHANCE = 0.30  # 30% chance to win
SLOTS_WIN_MULTIPLIER = 1.5  # 1.5x bet for regular win

DICE_WIN_CHANCE = 0.50  # 50% chance
DICE_WIN_MULTIPLIER = 1.8  # 1.8x bet for win

# =========================
# FEATURE FLAGS
# =========================

ENABLE_STATS = True  # Track user statistics
ENABLE_LOGGING = True  # Log all activity
ENABLE_AUTO_MODERATION = True  # Auto-delete NSFW content
ENABLE_ECONOMY = True  # Enable virtual economy system
