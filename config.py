"""Configuration for Marine.

Secrets must come from environment variables or a local .env file. Do not put
real bot tokens or API keys in source control.
"""

import os

from dotenv import load_dotenv


load_dotenv()


def _csv_ints(name: str, default: list[int]) -> list[int]:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def require_runtime_config() -> None:
    """Validate settings required to start the bot."""
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN is required. Set it in .env or the process environment.")


# =========================
# API CREDENTIALS
# =========================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# =========================
# BOT SETTINGS
# =========================

ADMIN_IDS = _csv_ints(
    "ADMIN_IDS",
    [
        8537521522,
        8577797097,
        8707676185,
        8737737935,
    ],
)
MAX_WARNINGS = int(os.getenv("MAX_WARNINGS", "3"))
MUTE_DURATION = int(os.getenv("MUTE_DURATION", "10"))
SILENT_PERMISSION_MODE = os.getenv("SILENT_PERMISSION_MODE", "true").lower() == "true"

# =========================
# CONTENT FILTERING
# =========================

BAD_WORDS = [
    "rape",
]

# =========================
# SPAM PROTECTION
# =========================

SPAM_LIMIT = int(os.getenv("SPAM_LIMIT", "5"))
SPAM_TIME = int(os.getenv("SPAM_TIME", "10"))

# =========================
# AI SETTINGS (OpenRouter)
# =========================

AI_MODEL = os.getenv("AI_MODEL", "meta-llama/llama-3.1-8b-instruct")
AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "15"))
MAX_RESPONSE_LENGTH = int(os.getenv("MAX_RESPONSE_LENGTH", "4096"))
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# =========================
# COOLDOWN SETTINGS
# =========================

ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
AI_COOLDOWN = int(os.getenv("AI_COOLDOWN", "3"))
SPEAK_COOLDOWN = int(os.getenv("SPEAK_COOLDOWN", "2"))
COMMAND_COOLDOWN = int(os.getenv("COMMAND_COOLDOWN", "1"))

# =========================
# PERFORMANCE SETTINGS
# =========================

DATA_SAVE_BATCH_INTERVAL = int(os.getenv("DATA_SAVE_BATCH_INTERVAL", "5"))
ENABLE_ASYNC_SAVES = os.getenv("ENABLE_ASYNC_SAVES", "true").lower() == "true"
SINGLE_INSTANCE_LOCK = os.getenv("SINGLE_INSTANCE_LOCK", "true").lower() == "true"
EXIT_ON_TELEGRAM_CONFLICT = os.getenv("EXIT_ON_TELEGRAM_CONFLICT", "true").lower() == "true"
ENABLE_HEALTH_SERVER = os.getenv("ENABLE_HEALTH_SERVER", "true").lower() == "true"

# =========================
# DATA STORAGE
# =========================

DATA_FILE = os.getenv("DATA_FILE", "bot_data.json")
LOG_FILE = os.getenv("LOG_FILE", "bot.log")

# =========================
# LOGGING
# =========================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s | %(levelname)s | %(name)s | %(message)s")

# =========================
# ECONOMY SYSTEM (VIRTUAL ONLY)
# =========================

OWNER_ID = int(os.getenv("OWNER_ID", "8577797097"))
STARTING_BALANCE = int(os.getenv("STARTING_BALANCE", "100"))
DAILY_COOLDOWN = int(os.getenv("DAILY_COOLDOWN", "86400"))
DAILY_REWARD = int(os.getenv("DAILY_REWARD", "50"))

# =========================
# FEATURE FLAGS
# =========================

ENABLE_STATS = os.getenv("ENABLE_STATS", "true").lower() == "true"
ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
ENABLE_AUTO_MODERATION = os.getenv("ENABLE_AUTO_MODERATION", "true").lower() == "true"
ENABLE_ECONOMY = os.getenv("ENABLE_ECONOMY", "true").lower() == "true"
