"""
Utility functions for Whisky_bot
AI integration and common helpers
"""

from openai import OpenAI
import logging
import asyncio
import os
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, AI_MODEL, AI_TIMEOUT, MAX_RESPONSE_LENGTH

logger = logging.getLogger(__name__)

# Configure OpenRouter client (OpenAI-compatible)
ai_client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY
)

async def ask_gemini(prompt: str) -> str:
    """
    Send a prompt to OpenRouter AI and get a response.
    
    Args:
        prompt: The user's question or prompt
        
    Returns:
        AI response text (truncated to Telegram limit)
    """
    try:
        # Use OpenRouter API
        response = await asyncio.wait_for(
            asyncio.to_thread(
                lambda: ai_client.chat.completions.create(
                    model=AI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful Telegram assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
            ),
            timeout=AI_TIMEOUT
        )
        
        # Extract text from response
        text = response.choices[0].message.content.strip()[:MAX_RESPONSE_LENGTH]
        
        logger.info(f"AI query successful: {len(text)} chars")
        return text
        
    except asyncio.TimeoutError:
        logger.error("AI request timed out")
        return "❌ AI request timed out. Please try again."
    except Exception as e:
        logger.error(f"AI Error: {type(e).__name__}: {e}")
        return f"❌ AI Error: {str(e)[:100]}"


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
