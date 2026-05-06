"""
Utility functions for Whisky_bot
AI integration and common helpers
"""

import google.generativeai as genai
import logging
from config import GEMINI_API_KEY, AI_MODEL, AI_TIMEOUT, MAX_RESPONSE_LENGTH

logger = logging.getLogger(__name__)

# Configure AI
genai.configure(api_key=GEMINI_API_KEY)

async def ask_gemini(prompt: str) -> str:
    """
    Send a prompt to Gemini AI and get a response.
    
    Args:
        prompt: The user's question or prompt
        
    Returns:
        AI response text (truncated to Telegram limit)
    """
    try:
        model = genai.GenerativeModel(AI_MODEL)
        response = model.generate_content(prompt, timeout=AI_TIMEOUT)
        
        # Ensure response is within Telegram's message limit
        text = response.text[:MAX_RESPONSE_LENGTH]
        
        logger.info(f"AI query successful: {len(text)} chars")
        return text
        
    except TimeoutError:
        logger.error("AI request timed out")
        return "❌ AI request timed out. Please try again."
    except Exception as e:
        logger.error(f"AI Error: {type(e).__name__}: {e}")
        return "❌ AI service temporarily unavailable. Please try again later."


def format_stats_message(stats: dict, user_warnings: int, max_warnings: int) -> str:
    """Format user statistics into a readable message."""
    return f"""
📊 **Your Statistics:**

📨 Messages sent: {stats.get('messages_sent', 0)}
🤖 AI queries: {stats.get('ai_queries', 0)}
⚠️ Warnings: {user_warnings}/{max_warnings}
    """


def format_help_message(max_warnings: int) -> str:
    """Format help message with all commands."""
    return f"""
**📚 Available Commands:**

**Regular Users:**
• `/start` - Start the bot
• `/help` - Show this help menu
• `/ai <message>` - Ask Gemini AI anything
• `/stats` - View your user statistics

**Admin Commands:**
• `/warn` - Warn a user (reply to message)
• `/mute` - Mute a user for 10 minutes (reply to message)
• `/unmute` - Unmute a user (reply to message)
• `/kick` - Kick a user from chat (reply to message)
• `/ban` - Ban a user (reply to message)
• `/unban` - Unban a user (reply to message)
• `/warns` - Check user warnings (reply to message)
• `/clear_warns` - Clear user warnings (reply to message)

**Filter Settings:**
• NSFW content is auto-deleted
• Max warnings before auto-ban: {max_warnings}
    """


def is_user_admin(user_id: int, admin_ids: list) -> bool:
    """Check if user is an admin."""
    return user_id in admin_ids


def get_username_or_id(update) -> str:
    """Get user's display name or ID."""
    user = update.effective_user
    if user.first_name:
        return user.first_name
    return str(user.id)
