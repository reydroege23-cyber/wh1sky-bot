"""
🥃 WHISKY_BOT - ELITE VERSION
Advanced Telegram Bot with AI Integration & Premium Features
"""

from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)

import google.generativeai as genai
from datetime import timedelta, datetime
import logging
import json
from pathlib import Path
from functools import wraps
from config import *
import asyncio

# =========================
# LOGGING SETUP (ENHANCED)
# =========================

logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =========================
# AI SETUP
# =========================

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(AI_MODEL)
    AI_AVAILABLE = True
    logger.info("✅ Gemini AI configured successfully")
except Exception as e:
    logger.warning(f"⚠️ AI configuration failed: {e}")
    AI_AVAILABLE = False

# =========================
# DATA STORAGE (ENHANCED)
# =========================

def load_data():
    """Load bot data with enhanced error handling."""
    if Path(DATA_FILE).exists():
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                logger.info(f"📦 Loaded data for {len(data.get('stats', {}))} users")
                return data
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
    return {"warnings": {}, "stats": {}, "mutes": {}, "metadata": {}}

def save_data(data):
    """Save bot data with enhanced error handling."""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"❌ Error saving data: {e}")

# Load initial data
bot_data = load_data()

# =========================
# DECORATORS (ENHANCED)
# =========================

def admin_only(func):
    """Check if user is admin."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in ADMIN_IDS:
            logger.warning(f"🚫 Unauthorized access by {update.effective_user.id}")
            return
        return await func(update, context)
    return wrapper

def reply_required(func):
    """Check if command is a reply."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Please reply to a message.")
            return
        return await func(update, context)
    return wrapper

def user_tracking(func):
    """Track user statistics."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if user_id not in bot_data["stats"]:
            bot_data["stats"][user_id] = {
                "messages": 0, "ai_queries": 0, "warnings": 0,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat()
            }
        bot_data["stats"][user_id]["last_seen"] = datetime.now().isoformat()
        bot_data["stats"][user_id]["messages"] += 1
        save_data(bot_data)
        return await func(update, context)
    return wrapper

# =========================
# AI FUNCTIONS (ENHANCED)
# =========================

async def ask_ai(message: str) -> str:
    """Get response from Gemini AI with error handling."""
    if not AI_AVAILABLE:
        return "⚠️ AI service is offline. Contact admin."
    
    try:
        response = model.generate_content(message, timeout=AI_TIMEOUT)
        text = response.text[:MAX_RESPONSE_LENGTH]
        logger.info(f"✅ AI response: {len(text)} chars")
        return text
    except asyncio.TimeoutError:
        logger.error("⏱️ AI request timeout")
        return "❌ Request timed out. Try shorter question."
    except Exception as e:
        logger.error(f"❌ AI Error: {e}")
        return "❌ AI service error. Try again later."

# =========================
# START COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced start command."""
    user = update.effective_user
    welcome = f"""
👋 **Welcome to Whisky_bot, {user.first_name}!**

I'm an AI-powered Telegram bot with advanced moderation features.

🤖 **Key Features:**
• Ask me anything with `/ai <question>`
• View your stats with `/stats`
• Get help with `/help`

🔐 **Admin only:** Advanced moderation tools available

Use `/help` for complete command list!
    """
    await update.message.reply_text(welcome, parse_mode="Markdown")
    logger.info(f"👤 New user: {user.id} ({user.first_name})")

# =========================
# HELP COMMAND
# =========================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced help command."""
    help_text = f"""
**📚 WHISKY_BOT - COMMAND REFERENCE**

**👥 USER COMMANDS:**
• `/start` - Welcome message
• `/help` - This menu
• `/ai <question>` - Ask Gemini AI
• `/stats` - Your statistics
• `/ping` - Check bot status

**👮 ADMIN COMMANDS:**
*Reply to a message to execute:*
• `/warn` - Issue warning
• `/warns` - Check warnings
• `/clear_warns` - Reset warnings
• `/mute` - Silence user (10 min)
• `/unmute` - Restore user voice
• `/kick` - Remove from chat
• `/ban` - Permanently ban
• `/unban` - Restore access
• `/info` - User information
• `/admins` - List admins

**⚙️ BOT SETTINGS:**
• Max Warnings: {MAX_WARNINGS}
• Mute Duration: {MUTE_DURATION} min
• AI Model: {AI_MODEL}
• Moderation: ENABLED ✅

**📞 Need help?** Contact an admin or check logs.
    """
    await update.message.reply_text(help_text, parse_mode="Markdown")

# =========================
# STATS COMMAND
# =========================

@user_tracking
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced stats command."""
    user_id = str(update.effective_user.id)
    user_stats = bot_data["stats"].get(user_id, {})
    warnings = bot_data["warnings"].get(user_id, 0)
    
    stats_text = f"""
📊 **YOUR STATISTICS**

📨 Messages: {user_stats.get('messages', 0)}
🤖 AI Queries: {user_stats.get('ai_queries', 0)}
⚠️ Warnings: {warnings}/{MAX_WARNINGS}
📅 Member since: {user_stats.get('first_seen', 'Unknown')[:10]}
    """
    await update.message.reply_text(stats_text, parse_mode="Markdown")

# =========================
# PING COMMAND
# =========================

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot status check."""
    status = "🟢 ONLINE" if AI_AVAILABLE else "🟡 DEGRADED"
    await update.message.reply_text(f"{status}\n⚡ Response Time: Fast")

# =========================
# MESSAGE HANDLER (ENHANCED)
# =========================

@user_tracking
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced message handling."""
    if not update.message or not update.message.text:
        return

    user_id = str(update.effective_user.id)
    text = update.message.text.lower()
    
    try:
        # NSFW FILTER
        if ENABLE_AUTO_MODERATION:
            for word in BAD_WORDS:
                if word in text:
                    await update.message.delete()
                    await update.message.reply_text(
                        "🚫 18+ content is prohibited.\n"
                        "⚠️ Warning issued."
                    )
                    bot_data["warnings"][user_id] = bot_data["warnings"].get(user_id, 0) + 1
                    logger.warning(f"🔞 NSFW from {user_id}")
                    save_data(bot_data)
                    return

        # AI COMMAND
        if text.startswith("/ai"):
            query = text.replace("/ai", "").strip()
            if not query:
                await update.message.reply_text(
                    "❓ Ask me something!\n\n"
                    "Example: `/ai What is Python?`",
                    parse_mode="Markdown"
                )
                return
            
            try:
                typing_msg = await update.message.reply_text("🤖 Thinking...")
                response = await ask_ai(query)
                await typing_msg.edit_text(response)
                
                bot_data["stats"][user_id]["ai_queries"] = bot_data["stats"][user_id].get("ai_queries", 0) + 1
                logger.info(f"🤖 AI query from {user_id}")
            except Exception as e:
                logger.error(f"AI handler error: {e}")
                await update.message.reply_text("❌ Error processing query")
            
        save_data(bot_data)
            
    except Exception as e:
        logger.error(f"❌ Message handler error: {e}")
        await update.message.reply_text("❌ An error occurred.")

# =========================
# HELPER FUNCTION FOR ADMIN COMMANDS
# =========================

async def get_user_from_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Extract user from reply or @username mention.
    Returns: (user_id, username) or (None, None) if not found
    """
    # OPTION 1: Check if replying to someone
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        username = update.message.reply_to_message.from_user.first_name or "User"
        return user_id, username
    
    # OPTION 2: Check for @username mention in command args
    if context.args:
        arg = context.args[0]
        
        # If it's a mention like @username
        if arg.startswith('@'):
            username = arg[1:]  # Remove the @ symbol
            
            try:
                # Try to get the user from chat members by username
                chat_members = await context.bot.get_chat(update.effective_chat.id)
                
                # Get all chat members and search for matching username
                # Using get_chat_member with username
                user = await context.bot.get_chat_member(
                    chat_id=update.effective_chat.id,
                    user_id=f"@{username}"  # Try to get by username
                )
                
                if user:
                    user_id = user.user.id
                    return user_id, username
                else:
                    return None, None
                    
            except Exception as e:
                logger.error(f"Failed to resolve @{username}: {e}")
                return None, None
        
        return None, None
    
    return None, None

# =========================
# ADMIN COMMANDS (ENHANCED)
# =========================

@admin_only
async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Issue warning."""
    user_id, username = await get_user_from_command(update, context)
    
    if not user_id:
        await update.message.reply_text(
            "❌ Please reply to a message or provide a user ID.\n"
            "Example: `/warn 123456789`"
        )
        return
    
    user_id_str = str(user_id)
    
    if user_id in ADMIN_IDS:
        await update.message.reply_text("❌ Cannot warn admins.")
        return
    
    bot_data["warnings"][user_id_str] = bot_data["warnings"].get(user_id_str, 0) + 1
    count = bot_data["warnings"][user_id_str]
    
    await update.message.reply_text(
        f"⚠️ {username} warned ({count}/{MAX_WARNINGS})"
    )
    
    if count >= MAX_WARNINGS:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, user_id)
            await update.message.reply_text(f"🚫 {username} auto-banned (max warnings)")
            logger.warning(f"🚫 Auto-banned {user_id} after {count} warnings")
        except Exception as e:
            logger.error(f"Ban error: {e}")
    
    save_data(bot_data)

@admin_only
async def check_warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check warnings."""
    user_id, username = await get_user_from_command(update, context)
    
    if not user_id:
        await update.message.reply_text(
            "❌ Please reply to a message or mention a username.\n"
            "Example: `/warns @username`"
        )
        return
    
    user_id_str = str(user_id)
    warns = bot_data["warnings"].get(user_id_str, 0)
    
    await update.message.reply_text(
        f"⚠️ {username}: {warns}/{MAX_WARNINGS} warnings"
    )

@admin_only
async def clear_warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear warnings."""
    user_id, username = await get_user_from_command(update, context)
    
    if not user_id:
        await update.message.reply_text(
            "❌ Please reply to a message or mention a username.\n"
            "Example: `/clear_warns @username`"
        )
        return
    
    user_id_str = str(user_id)
    bot_data["warnings"][user_id_str] = 0
    await update.message.reply_text(f"✅ {username}'s warnings cleared")
    save_data(bot_data)
    logger.info(f"✅ Warnings cleared for {user_id}")

@admin_only
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mute user."""
    try:
        user_id, username = await get_user_from_command(update, context)
        
        if not user_id:
            await update.message.reply_text(
                "❌ Please reply to a message or mention a username.\n"
                "Example: `/mute @username`"
            )
            return
        
        if user_id in ADMIN_IDS:
            await update.message.reply_text("❌ Cannot mute admins.")
            return

        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            user_id,
            ChatPermissions(can_send_messages=False),
            until_date=timedelta(minutes=MUTE_DURATION)
        )
        await update.message.reply_text(f"🔇 {username} muted ({MUTE_DURATION}m)")
        logger.info(f"🔇 {user_id} muted")
    except Exception as e:
        logger.error(f"Mute error: {e}")
        await update.message.reply_text("❌ Failed to mute user")

@admin_only
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unmute user."""
    try:
        user_id, username = await get_user_from_command(update, context)
        
        if not user_id:
            await update.message.reply_text(
                "❌ Please reply to a message or mention a username.\n"
                "Example: `/unmute @username`"
            )
            return

        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            user_id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_add_web_page_previews=True
            )
        )
        await update.message.reply_text(f"🔊 {username} unmuted")
        logger.info(f"🔊 {user_id} unmuted")
    except Exception as e:
        logger.error(f"Unmute error: {e}")
        await update.message.reply_text("❌ Failed to unmute user")

@admin_only
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kick user."""
    try:
        user_id, username = await get_user_from_command(update, context)
        
        if not user_id:
            await update.message.reply_text(
                "❌ Please reply to a message or mention a username.\n"
                "Example: `/kick @username`"
            )
            return
        
        if user_id in ADMIN_IDS:
            await update.message.reply_text("❌ Cannot kick admins.")
            return

        await context.bot.ban_chat_member(update.effective_chat.id, user_id)
        await context.bot.unban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text(f"👢 {username} kicked")
        logger.info(f"👢 {user_id} kicked")
    except Exception as e:
        logger.error(f"Kick error: {e}")
        await update.message.reply_text("❌ Failed to kick user")

@admin_only
async def iloveu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban user - STRICT: /iloveu @username ONLY (NOT replies, NOT context guessing)."""
    try:
        # ❌ REJECT: If this is a reply message
        if update.message.reply_to_message:
            logger.info(f"❌ Ban ignored: reply message detected")
            return
        
        # ❌ REJECT: No arguments provided
        if not context.args:
            logger.info(f"❌ Ban ignored: no args provided")
            return
        
        arg = context.args[0]
        
        # ❌ REJECT: Argument doesn't start with @
        if not arg.startswith('@'):
            logger.info(f"❌ Ban ignored: arg '{arg}' doesn't start with @")
            return
        
        # ✅ VALID: Extract username
        username = arg[1:]  # Remove @
        
        try:
            # Try to resolve @username to user_id
            user = await context.bot.get_chat_member(
                chat_id=update.effective_chat.id,
                user_id=f"@{username}"
            )
            if user:
                user_id = user.user.id
            else:
                logger.info(f"❌ Ban ignored: @{username} not found in chat")
                return
        except Exception as e:
            logger.error(f"Failed to resolve @{username}: {e}")
            logger.info(f"❌ Ban ignored: resolution error for @{username}")
            return
        
        # ❌ REJECT: Target is admin
        if user_id in ADMIN_IDS:
            logger.warning(f"⚠️ Attempt to ban admin @{username}")
            return

        # ✅ EXECUTE: BAN THE USER
        await context.bot.ban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text(f"🚫 @{username} banned")
        logger.critical(f"🚫 BANNED: @{username} ({user_id}) by admin {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Ban error: {e}")

@admin_only
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban user."""
    try:
        user_id, username = await get_user_from_command(update, context)
        
        if not user_id:
            await update.message.reply_text(
                "❌ Please reply to a message or mention a username.\n"
                "Example: `/unban @username`"
            )
            return

        await context.bot.unban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text(f"✅ {username} unbanned")
        logger.info(f"✅ {user_id} unbanned")
    except Exception as e:
        logger.error(f"Unban error: {e}")
        await update.message.reply_text("❌ Failed to unban user")

@admin_only
async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user information."""
    try:
        user_id, username = await get_user_from_command(update, context)
        
        if not user_id:
            await update.message.reply_text(
                "❌ Please reply to a message or mention a username.\n"
                "Example: `/info @username`"
            )
            return

        user_id_str = str(user_id)
        stats = bot_data["stats"].get(user_id_str, {})
        warns = bot_data["warnings"].get(user_id_str, 0)
        
        info = f"""
👤 **USER INFORMATION**

ID: {user_id}
Name: {username}
Messages: {stats.get('messages', 0)}
AI Queries: {stats.get('ai_queries', 0)}
Warnings: {warns}/{MAX_WARNINGS}
        """
        await update.message.reply_text(info, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"User info error: {e}")
        await update.message.reply_text(f"❌ Failed to get user info: {str(e)}")

@admin_only
async def admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List admins."""
    admin_list = "\n".join([f"• {uid}" for uid in ADMIN_IDS])
    msg = f"**👮 ADMINS**\n\n{admin_list}"
    await update.message.reply_text(msg, parse_mode="Markdown")

# =========================
# ERROR HANDLER
# =========================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"❌ Error: {context.error}")

# =========================
# BOT SETUP
# =========================

def setup_bot():
    """Initialize and setup bot."""
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Error handler
    app.add_error_handler(error_handler)
    
    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("warns", check_warns))
    app.add_handler(CommandHandler("clear_warns", clear_warns))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("info", user_info))
    app.add_handler(CommandHandler("admins", admins))
    
    # Messages (must be last)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return app

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🥃 WHISKY_BOT - ELITE VERSION STARTING")
    logger.info(f"👮 Admin IDs: {ADMIN_IDS}")
    logger.info(f"🤖 AI Status: {'✅ ONLINE' if AI_AVAILABLE else '⚠️ OFFLINE'}")
    logger.info(f"📊 Tracking {len(bot_data['stats'])} users")
    logger.info("=" * 60)
    
    try:
        app = setup_bot()
        print("\n✅ Bot is running... Press Ctrl+C to stop\n")
        app.run_polling()
    except KeyboardInterrupt:
        logger.info("⛔ Bot stopped by user")
    except Exception as e:
        logger.error(f"🔥 Critical error: {e}")
