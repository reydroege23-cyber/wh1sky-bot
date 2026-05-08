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
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =========================
# AI SETUP
# =========================

try:
    logger.info("🔧 Configuring Gemini AI...")
    logger.info(f"📝 API Key present: {bool(GEMINI_API_KEY)}")
    logger.info(f"🤖 Model: {AI_MODEL}")
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(AI_MODEL)
    logger.info("✅ Gemini configured successfully")
    
    # Mark as available - test will happen on first /ai or /test command
    AI_AVAILABLE = True
    logger.info("✅ AI will be tested on first use")
        
except Exception as e:
    logger.warning(f"⚠️ AI configuration failed: {type(e).__name__}: {e}")
    import traceback
    logger.warning(traceback.format_exc())
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
            await update.message.reply_text("❌ Only admins can use this command.")
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

def authorized_only(func):
    """Check if user is authorized to use bot."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        # Admins bypass authorization check
        if user_id in ADMIN_IDS:
            return await func(update, context)
        
        # Check if user is authorized (handle both int and string types)
        authorized_users = bot_data.get("metadata", {}).get("authorized_users", [])
        # Convert to strings for comparison to handle JSON type issues
        authorized_users_str = [str(uid) for uid in authorized_users]
        if str(user_id) not in authorized_users_str:
            await update.message.reply_text("❌ You are not authorized to use this bot.\nContact an admin for access.")
            logger.warning(f"🚫 Unauthorized bot access attempt by {user_id}")
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
        # Run the synchronous API call in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: model.generate_content(message)),
            timeout=AI_TIMEOUT
        )
        
        # Check if response exists
        if not response:
            logger.error("❌ Empty response from Gemini API")
            return "❌ AI returned empty response. Try again."
        
        # Check if response has text attribute
        if not hasattr(response, 'text'):
            logger.error(f"❌ Response object has no text attribute: {type(response)}")
            return "❌ AI response format error. Try again."
        
        # Check if text is empty
        if not response.text or response.text.strip() == "":
            logger.error("❌ AI returned empty text")
            return "❌ AI returned empty response. Try again."
        
        text = response.text[:MAX_RESPONSE_LENGTH]
        logger.info(f"✅ AI response: {len(text)} chars")
        return text
        
    except asyncio.TimeoutError:
        logger.error("⏱️ AI request timeout")
        return "❌ Request timed out. Try shorter question."
    except Exception as e:
        logger.error(f"❌ AI Error: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return f"❌ AI Error: {str(e)[:80]}"

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

**👥 USER COMMANDS (26):**
• `/start` - Welcome message
• `/help` - This menu
• `/ai <question>` - Ask Gemini AI
• `/stats` - Your statistics
• `/ping` - Check bot status

**🎮 FUN COMMANDS (11):**
• `/roll [sides]` - Roll dice (default 6)
• `/dice` - Roll dice (1-6)
• `/coin` - Flip a coin
• `/8ball` - Magic 8 ball
• `/joke` - Random joke
• `/fact` - Interesting fact
• `/flip <text>` - Upside down text
• `/reverse <text>` - Reverse text
• `/morse <text>` - Convert to Morse code
• `/random [min] [max]` - Random number (1-100 default)
• `/guess <num>` - Number guessing game

**👤 PROFILE COMMANDS (5):**
• `/userid` - Your user ID
• `/profile` - Your profile info
• `/invite` - Get chat invite link
• `/members` - Member count
• `/uptime` - Bot uptime

**🧮 UTILITY COMMANDS:**
• `/calc <expression>` - Simple calculator
• `/echo <text>` - Echo your message
• `/time` - Show current time
• `/b64 <text>` - Encode to base64
• `/quote` - Inspirational quote
• `/hajhanm` - Special command 😂
• `/hoba` - Special command 👑
• `/Amanj` - Special command 👑
• `/Arya` - Special command 🚩
• `/kurdishezdi` - Special command 🇮🇶
• `/Serok` - Music link 🎵

**👮 ADMIN COMMANDS (11):**
*Reply to a message to execute:*
• `/ilikeu` - Issue warning
• `/warns` - Check warnings
• `/clear_warns` - Reset warnings
• `/Shut` - Silence user (10 min)
• `/unmute` - Restore user voice
• `/unshut` - Restore user voice (alias)
• `/kick` - Remove from chat
• `/iloveu` - Permanently ban
• `/unban` - Restore access
• `/info` - User information
• `/admins` - List admins
• `/speak` - Enable Gemini speak mode
• `/stop_speak` - Disable speak mode
• `/unSpeak` - Disable speak mode (alias)

**⚙️ BOT SETTINGS:**
• Max Warnings: {MAX_WARNINGS}
• Mute Duration: {MUTE_DURATION} min
• AI Model: {AI_MODEL}
• Moderation: ENABLED ✅
• Total Commands: 40+

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
    """Bot status check with diagnostics."""
    import time
    import datetime
    try:
        # Calculate actual response time from when message was received
        msg_time = update.message.date
        current_time = datetime.datetime.now(datetime.timezone.utc)
        response_time_ms = (current_time - msg_time).total_seconds() * 1000
        
        if AI_AVAILABLE:
            status_msg = "🟢 **BOT STATUS: ONLINE**\n\n"
            status_msg += "✅ Telegram: Connected\n"
            status_msg += "✅ Gemini AI: Ready\n"
            status_msg += f"⚡ Response Time: {response_time_ms:.0f}ms"
        else:
            status_msg = "🟡 **BOT STATUS: DEGRADED**\n\n"
            status_msg += "✅ Telegram: Connected\n"
            status_msg += "❌ Gemini AI: Offline\n\n"
            status_msg += "**Possible causes:**\n"
            status_msg += "• Invalid API key\n"
            status_msg += "• Network connection issue\n"
            status_msg += "• API rate limit exceeded\n"
            status_msg += "• Gemini service unavailable\n\n"
            status_msg += "Admins: Use `/test` to diagnose"
        
        await update.message.reply_text(status_msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ping error: {e}")
        await update.message.reply_text("❌ Ping failed")

# =========================
# UPDATE COMMAND
# =========================

@user_tracking
async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show latest updates and new features."""
    try:
        update_msg = """
📢 **LATEST UPDATES & NEW FEATURES**

**🔧 RECENT FIXES:**
• Fixed `/ai` command - Now works with proper async handling
• Fixed `/speak` mode - AI responds to all messages smoothly
• Fixed `/rape` command - Ignores bot replies
• Fixed `/authorize` - User ID consistency
• Improved `/ping` - Shows actual response time

**🎉 NEW FEATURES:**
• `/test` - Admin diagnostic tool for AI health
• Enhanced error messages with detailed logging
• Better AI initialization with live status updates

**📊 BOT STATUS:**
• Total Commands: 40+
• Admin Tools: 15
• Fun Commands: 25+
• AI Integration: Active ✅

**🚀 COMMAND HIGHLIGHTS:**
• `/ai <question>` - Ask Gemini AI
• `/speak` - Enable AI respond mode (admin)
• `/stats` - View your usage
• `/help` - Full command list

**📝 VERSION:** 2.5+

For full changelog, use `/help`
        """
        await update.message.reply_text(update_msg, parse_mode="Markdown")
        logger.info(f"📢 {update.effective_user.id} viewed updates")
    except Exception as e:
        logger.error(f"Update command error: {e}")
        await update.message.reply_text("❌ Failed to load updates")

# =========================
# TEST COMMAND (DIAGNOSTIC)
# =========================

@admin_only
async def test_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test AI functionality - admin only."""
    try:
        msg = await update.message.reply_text("🧪 Testing AI connection...")
        logger.info("🧪 Starting AI test...")
        
        response = await ask_ai("Say 'AI is working' in one sentence")
        logger.info(f"🧪 Test response: {response}")
        
        await msg.edit_text(f"✅ AI Test Result:\n\n{response}")
    except Exception as e:
        logger.error(f"🧪 AI test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        await update.message.reply_text(f"❌ AI Test Failed:\n{str(e)[:200]}")

# =========================
# AI COMMAND
# =========================

@user_tracking
async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ai command to ask Gemini AI."""
    user_id = str(update.effective_user.id)
    
    # Get query from arguments
    query = " ".join(context.args).strip() if context.args else ""
    
    if not query:
        await update.message.reply_text(
            "❓ Ask me something!\n\n"
            "Example: `/ai What is Python?`",
            parse_mode="Markdown"
        )
        return
    
    typing_msg = None
    try:
        # Send thinking message
        typing_msg = await update.message.reply_text("🤖 Thinking...")
        logger.info(f"🤖 Processing AI query from {user_id}: {query[:50]}...")
        
        # Get AI response
        response = await ask_ai(query)
        logger.info(f"🤖 Got response: {len(response)} chars")
        
        # Try to edit the message
        if typing_msg:
            try:
                await typing_msg.edit_text(response)
            except Exception as edit_error:
                logger.error(f"Failed to edit message: {edit_error}")
                # If edit fails, send as new message
                await update.message.reply_text(response)
        else:
            await update.message.reply_text(response)
        
        # Update statistics
        bot_data["stats"][user_id]["ai_queries"] = bot_data["stats"][user_id].get("ai_queries", 0) + 1
        logger.info(f"✅ AI query successful from {user_id}")
        save_data(bot_data)
        
    except Exception as e:
        logger.error(f"❌ AI command error: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            if typing_msg:
                await typing_msg.edit_text(f"❌ Error: {str(e)[:80]}")
            else:
                await update.message.reply_text(f"❌ Error: {str(e)[:80]}")
        except:
            pass

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
        # SPEAK MODE - Gemini responds to all messages
        speak_mode = bot_data.get("metadata", {}).get("speak_mode", False)
        if speak_mode:
            typing_msg = None
            try:
                typing_msg = await update.message.reply_text("🤖 Thinking...")
                logger.info(f"🤖 Speak mode - processing from {user_id}")
                response = await ask_ai(update.message.text)
                logger.info(f"🤖 Got response: {len(response)} chars")
                
                if typing_msg:
                    try:
                        await typing_msg.edit_text(response)
                    except Exception as edit_error:
                        logger.error(f"Failed to edit speak mode message: {edit_error}")
                        await update.message.reply_text(response)
                else:
                    await update.message.reply_text(response)
                
                bot_data["stats"][user_id]["ai_queries"] = bot_data["stats"][user_id].get("ai_queries", 0) + 1
                logger.info(f"✅ Speak mode - AI response to {user_id}")
                save_data(bot_data)
                return
            except Exception as e:
                logger.error(f"❌ Speak mode error: {type(e).__name__}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                try:
                    if typing_msg:
                        await typing_msg.edit_text(f"❌ AI Error: {str(e)[:80]}")
                    else:
                        await update.message.reply_text(f"❌ AI Error: {str(e)[:80]}")
                except:
                    pass
        
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
    Extract user from reply, mention, or user ID.
    Returns: (user_id, username) or (None, None) if not found
    """
    # OPTION 1: Check if replying to someone
    if update.message.reply_to_message:
        user_id = update.message.reply_to_message.from_user.id
        username = update.message.reply_to_message.from_user.first_name or "User"
        return user_id, username
    
    # OPTION 2: Check for mentions (@username) or user ID in command args
    if context.args:
        arg = context.args[0]
        
        # If it's a mention like @username
        if arg.startswith('@'):
            username = arg[1:]  # Remove the @ symbol
            # For now, we can't directly resolve @username to user_id without chat member access
            # So we'll need to use a different approach or ask for ID
            # For this version, we'll tell the user to use ID instead
            return None, None
        
        # If it's a user ID (numeric)
        try:
            user_id = int(arg)
            # We don't have the username directly, so we'll try to fetch from context
            # For now, use "User" as fallback
            username = f"User {user_id}"
            return user_id, username
        except ValueError:
            return None, None
    
    return None, None

# =========================
# ADMIN COMMANDS (ENHANCED)
# =========================

@admin_only
async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Issue warning - 3 warnings = permanent ban (FIXED)."""
    user_id = None
    user_id_str = None
    username = None
    
    try:
        # Get user from reply, mention, or user ID
        user_id, username = await get_user_from_command(update, context)
        
        if not user_id:
            await update.message.reply_text(
                "❌ Please reply to a message, mention someone (@user), or provide a user ID.\n"
                "Example: `/warn @username` or `/warn 123456789`"
            )
            return
        
        user_id_str = str(user_id)
        logger.info(f"⚠️ WARN COMMAND: Starting warning process for {username} ({user_id})")
        
        # Admin check
        if user_id in ADMIN_IDS:
            await update.message.reply_text("❌ Cannot warn admins.")
            logger.warning(f"⚠️ Attempt to warn admin {user_id}")
            return
        
        # STEP 1: Get current warning count from persistent storage
        current_warns = bot_data["warnings"].get(user_id_str, 0)
        logger.info(f"📍 Current warns for {username}: {current_warns}")
        
        # STEP 2: Increment the counter
        new_count = current_warns + 1
        bot_data["warnings"][user_id_str] = new_count
        logger.info(f"📍 New count set to: {new_count}")
        
        # STEP 3: Save immediately - CRITICAL STEP
        save_data(bot_data)
        logger.info(f"💾 Data saved to file")
        
        # STEP 4: Verify the save was successful by reloading
        verification_data = load_data()
        verify_count = verification_data["warnings"].get(user_id_str, 0)
        logger.info(f"✅ Verification: Warns in file = {verify_count}")
        
        if verify_count != new_count:
            logger.error(f"❌ VERIFICATION FAILED: Expected {new_count}, got {verify_count}")
        
        # STEP 5: Send feedback message to admin
        await update.message.reply_text(
            f"⚠️ {username} warned ({new_count}/{MAX_WARNINGS})"
        )
        logger.info(f"📢 Warned {username}: {new_count}/{MAX_WARNINGS}")
        
        # STEP 6: Check if ban threshold reached
        if new_count >= MAX_WARNINGS:
            logger.critical(f"🚫 BAN THRESHOLD REACHED: {username} has {new_count} warnings - INITIATING BAN")
            
            try:
                # Execute ban
                await context.bot.ban_chat_member(update.effective_chat.id, user_id)
                logger.critical(f"✅ BAN EXECUTED: {username} ({user_id}) successfully banned")
                
                # Notify admins of successful ban
                await update.message.reply_text(
                    f"🚫 **{username} HAS BEEN PERMANENTLY BANNED**\n\n"
                    f"Reason: Reached {MAX_WARNINGS} warnings\n"
                    f"Action: Automatic ban executed"
                )
                
                # STEP 7: Reset warns to 0 after successful ban (mark as completed)
                bot_data["warnings"][user_id_str] = 0
                save_data(bot_data)
                logger.critical(f"✅ Warns reset to 0 for {username} after ban")
                
            except Exception as ban_error:
                logger.error(f"❌ BAN FAILED for {username}: {ban_error}")
                await update.message.reply_text(
                    f"❌ Failed to ban {username}: {str(ban_error)}\n"
                    f"⚠️ User has reached max warnings but manual ban required"
                )
        
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR in warn(): {e}", exc_info=True)
        if username:
            await update.message.reply_text(f"❌ Error warning {username}: {str(e)}")
        else:
            await update.message.reply_text("❌ Error processing warning")

@admin_only
async def check_warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check warnings."""
    user_id, username = await get_user_from_command(update, context)
    
    if not user_id:
        await update.message.reply_text(
            "❌ Please reply to a message or provide a user ID.\n"
            "Example: `/warns 123456789`"
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
            "❌ Please reply to a message or provide a user ID.\n"
            "Example: `/clear_warns 123456789`"
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
                "❌ Please reply to a message or provide a user ID.\n"
                "Example: `/mute 123456789`"
            )
            return
        
        if user_id in ADMIN_IDS:
            await update.message.reply_text("❌ Cannot mute admins.")
            return

        # Calculate Unix timestamp for mute duration
        until_date = datetime.now() + timedelta(minutes=MUTE_DURATION)
        
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            user_id,
            ChatPermissions(can_send_messages=False),
            until_date=int(until_date.timestamp())
        )
        await update.message.reply_text(f"🔇 {username} silenced ({MUTE_DURATION}m)")
        logger.info(f"🔇 {user_id} silenced for {MUTE_DURATION}m")
    except Exception as e:
        logger.error(f"Mute error: {e}")
        await update.message.reply_text(f"❌ Failed to mute user: {str(e)}")

@admin_only
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unmute user."""
    try:
        user_id, username = await get_user_from_command(update, context)
        
        if not user_id:
            await update.message.reply_text(
                "❌ Please reply to a message or provide a user ID.\n"
                "Example: `/unmute 123456789`"
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
                "❌ Please reply to a message or provide a user ID.\n"
                "Example: `/kick 123456789`"
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
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban user."""
    try:
        user_id, username = await get_user_from_command(update, context)
        
        if not user_id:
            await update.message.reply_text(
                "❌ Please reply to a message or provide a user ID.\n"
                "Example: `/ban 123456789`"
            )
            return
        
        if user_id in ADMIN_IDS:
            await update.message.reply_text("❌ Cannot ban admins.")
            return

        await context.bot.ban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text(f"🚫 {username} banned")
        logger.info(f"🚫 {user_id} banned")
    except Exception as e:
        logger.error(f"Ban error: {e}")
        await update.message.reply_text("❌ Failed to ban user")

@admin_only
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban user."""
    try:
        user_id, username = await get_user_from_command(update, context)
        
        if not user_id:
            await update.message.reply_text(
                "❌ Please reply to a message or provide a user ID.\n"
                "Example: `/unban 123456789`"
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
                "❌ Please reply to a message or provide a user ID.\n"
                "Example: `/info 123456789`"
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

@admin_only
async def debug_warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command - show all warnings data."""
    try:
        warns_data = bot_data["warnings"]
        if not warns_data:
            await update.message.reply_text("📊 No warnings recorded yet")
            return
        
        # Build message
        msg = "**🔍 WARNS DEBUG DATA**\n\n"
        for uid, count in warns_data.items():
            msg += f"User {uid}: {count} warns\n"
        
        msg += f"\n**Total users warned:** {len(warns_data)}"
        await update.message.reply_text(msg, parse_mode="Markdown")
        logger.info(f"🔍 Debug warns called - {len(warns_data)} users with warnings")
    except Exception as e:
        logger.error(f"Debug warns error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

@admin_only
async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Authorize a user to access the bot."""
    try:
        user_id, username = await get_user_from_command(update, context)
        
        if not user_id:
            await update.message.reply_text(
                "❌ Please reply to a message or provide a user ID.\n"
                "Example: `/authorize 123456789`"
            )
            return
        
        # Initialize authorized_users list if needed
        if "metadata" not in bot_data:
            bot_data["metadata"] = {}
        if "authorized_users" not in bot_data["metadata"]:
            bot_data["metadata"]["authorized_users"] = []
        
        authorized_users = bot_data["metadata"]["authorized_users"]
        
        # Convert all to integers for consistency
        authorized_users_int = [int(uid) for uid in authorized_users]
        
        # Check if already authorized
        if user_id in authorized_users_int:
            await update.message.reply_text(f"✅ {username} is already authorized")
            logger.info(f"ℹ️ {username} already authorized")
            return
        
        # Add to authorized users (as integer) and save with consistency
        bot_data["metadata"]["authorized_users"] = authorized_users_int + [user_id]
        save_data(bot_data)
        
        await update.message.reply_text(f"✅ {username} is now authorized to use the bot!")
        logger.info(f"✅ {username} ({user_id}) authorized")
        
    except Exception as e:
        logger.error(f"Authorize error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

@admin_only
@reply_required
async def deauthorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove authorization from a user."""
    try:
        user = update.message.reply_to_message.from_user
        user_id = int(user.id)  # Ensure integer
        username = user.first_name or "User"
        
        if "metadata" not in bot_data or "authorized_users" not in bot_data["metadata"]:
            await update.message.reply_text(f"❌ {username} is not authorized")
            return
        
        authorized_users = bot_data["metadata"]["authorized_users"]
        
        # Convert to integers for comparison
        authorized_users_int = [int(uid) for uid in authorized_users]
        
        # Check if authorized
        if user_id not in authorized_users_int:
            await update.message.reply_text(f"❌ {username} is not authorized")
            logger.info(f"ℹ️ {username} was not authorized")
            return
        
        # Remove from authorized users
        bot_data["metadata"]["authorized_users"] = [uid for uid in authorized_users_int if uid != user_id]
        save_data(bot_data)
        
        await update.message.reply_text(f"🚫 {username} is no longer authorized")
        logger.info(f"🚫 {username} ({user_id}) deauthorized")
        
    except Exception as e:
        logger.error(f"Deauthorize error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

@admin_only
async def authorized_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all authorized users."""
    try:
        if "metadata" not in bot_data or "authorized_users" not in bot_data["metadata"]:
            await update.message.reply_text("📊 No authorized users yet")
            return
        
        authorized_users = bot_data["metadata"]["authorized_users"]
        
        if not authorized_users:
            await update.message.reply_text("📊 No authorized users yet")
            return
        
        # Convert to integers and remove duplicates
        authorized_users_int = list(set(int(uid) for uid in authorized_users))
        # Update the data to ensure consistency
        bot_data["metadata"]["authorized_users"] = authorized_users_int
        save_data(bot_data)
        
        msg = "**✅ AUTHORIZED USERS**\n\n"
        for uid in sorted(authorized_users_int):
            msg += f"• {uid}\n"
        
        msg += f"\n**Total:** {len(authorized_users_int)} users"
        await update.message.reply_text(msg, parse_mode="Markdown")
        logger.info(f"📊 Authorized list viewed - {len(authorized_users_int)} users")
        
    except Exception as e:
        logger.error(f"Authorized list error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

@user_tracking
async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roll dice command."""
    import random
    try:
        if context.args and context.args[0]:
            sides = int(context.args[0])
            if sides < 2:
                await update.message.reply_text("❌ Dice must have at least 2 sides")
                return
        else:
            sides = 6
        
        result = random.randint(1, sides)
        await update.message.reply_text(f"🎲 **Rolled {sides}-sided dice: {result}**", parse_mode="Markdown")
        logger.info(f"🎲 {update.effective_user.id} rolled {sides}-sided dice")
    except ValueError:
        await update.message.reply_text("❌ Invalid number. Usage: /roll [sides]")
    except Exception as e:
        logger.error(f"Roll error: {e}")
        await update.message.reply_text("❌ Failed to roll dice")

@user_tracking
async def coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Flip a coin."""
    import random
    try:
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙 " if result == "Heads" else "🪙 "
        await update.message.reply_text(f"{emoji} **{result}**", parse_mode="Markdown")
        logger.info(f"🪙 {update.effective_user.id} flipped coin: {result}")
    except Exception as e:
        logger.error(f"Coin flip error: {e}")
        await update.message.reply_text("❌ Failed to flip coin")

@user_tracking
async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple calculator."""
    try:
        if not context.args:
            await update.message.reply_text("❌ Usage: /calc 2+2 or /calc 10*5")
            return
        
        expression = " ".join(context.args)
        # Only allow safe math operations
        if any(char in expression for char in ['_', '(', ')', '[', ']', '{', '}', '|', '&']):
            await update.message.reply_text("❌ Invalid characters in expression")
            return
        
        result = eval(expression)
        await update.message.reply_text(f"🧮 **{expression} = {result}**", parse_mode="Markdown")
        logger.info(f"🧮 {update.effective_user.id} calculated: {expression} = {result}")
    except ZeroDivisionError:
        await update.message.reply_text("❌ Cannot divide by zero!")
    except Exception as e:
        logger.error(f"Calc error: {e}")
        await update.message.reply_text("❌ Invalid calculation")

@user_tracking
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo message."""
    try:
        if not context.args:
            await update.message.reply_text("❌ Usage: /echo Hello World")
            return
        
        message = " ".join(context.args)
        if len(message) > 200:
            await update.message.reply_text("❌ Message too long (max 200 chars)")
            return
        
        await update.message.reply_text(f"🔊 {message}")
        logger.info(f"🔊 {update.effective_user.id} echoed: {message}")
    except Exception as e:
        logger.error(f"Echo error: {e}")
        await update.message.reply_text("❌ Failed to echo message")

@user_tracking
async def time_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current time."""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await update.message.reply_text(f"🕐 **{current_time}** (UTC+0)", parse_mode="Markdown")
        logger.info(f"🕐 {update.effective_user.id} checked time")
    except Exception as e:
        logger.error(f"Time error: {e}")
        await update.message.reply_text("❌ Failed to get time")

@user_tracking
async def Rape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tell a random Rape with target user's name - only works on user messages, not bots."""
    import random
    try:
        # Check if replying to someone
        if update.message.reply_to_message:
            # Only work if replying to a user, NOT a bot
            replied_user = update.message.reply_to_message.from_user
            if not replied_user:
                logger.info(f"ℹ️ {update.effective_user.id} tried /rape on system message - ignoring")
                return
            
            # Check if the replied message is from a bot
            if replied_user.is_bot:
                logger.info(f"ℹ️ {update.effective_user.id} tried /rape on bot message - ignoring")
                return
            
            # Process reply to user
            target_name = replied_user.first_name or "User"
            response = f"Rape {target_name}"
            await update.message.reply_text(response)
            logger.info(f"😂 {update.effective_user.id} raped {target_name}")
            return
        
        # Only do random Rape if NOT replying to anything
        Rape_list = [
            "RAPE Amanj",
            "RAPE kurdish ezidi",
            "RAPE kurdish Warrior",
            "RAPE KRD",
            "RAPE Kardox",
            "RAPE Namat",
            "RAPE ⛰️🏴"
        ]
        Rape_text = random.choice(Rape_list)
        await update.message.reply_text(f"😂 {Rape_text}")
        logger.info(f"😂 {update.effective_user.id} got a random Rape")
        
    except Exception as e:
        logger.error(f"Rape error: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())

@user_tracking
async def eightball(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Magic 8 ball."""
    import random
    answers = [
        "Yes, definitely!", "No, absolutely not.", "Maybe later.",
        "Ask again soon.", "The signs point to yes.", "Very doubtful.",
        "Outlook good.", "Without a doubt.", "Don't count on it.",
        "As I see it, yes.", "Better not tell you now.", "Concentrate and ask again."
    ]
    try:
        answer = random.choice(answers)
        await update.message.reply_text(f"🎱 **{answer}**", parse_mode="Markdown")
        logger.info(f"🎱 {update.effective_user.id} asked 8ball")
    except Exception as e:
        logger.error(f"8ball error: {e}")
        await update.message.reply_text("❌ Magic ball malfunction")

@user_tracking
async def reverse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reverse text."""
    try:
        if not context.args:
            await update.message.reply_text("❌ Usage: /reverse hello world")
            return
        text = " ".join(context.args)
        if len(text) > 100:
            await update.message.reply_text("❌ Text too long (max 100 chars)")
            return
        reversed_text = text[::-1]
        await update.message.reply_text(f"↩️ **{reversed_text}**", parse_mode="Markdown")
        logger.info(f"↩️ {update.effective_user.id} reversed text")
    except Exception as e:
        logger.error(f"Reverse error: {e}")
        await update.message.reply_text("❌ Failed to reverse")

@user_tracking
async def fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Random interesting fact."""
    facts = [
        "Honey never spoils. Archaeologists found 3000-year-old honey in Egyptian tombs!",
        "A group of flamingos is called a 'flamboyance'.",
        "Octopuses have three hearts!",
        "Bananas are berries, but strawberries aren't!",
        "The shortest war lasted 38 minutes.",
        "Cleopatra lived closer to the moon landing than to the building of the Great Pyramid.",
        "A day on Venus is longer than its year!",
        "Wombats have cubic poop!",
        "Cats have a third eyelid called the nictitating membrane.",
        "The smell of petrichor (rain on dry earth) is caused by bacteria!"
    ]
    import random
    try:
        fact_text = random.choice(facts)
        await update.message.reply_text(f"💡 **{fact_text}**", parse_mode="Markdown")
        logger.info(f"💡 {update.effective_user.id} got a fact")
    except Exception as e:
        logger.error(f"Fact error: {e}")
        await update.message.reply_text("❌ Failed to fetch fact")

@user_tracking
async def morse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Convert text to Morse code."""
    morse_dict = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
        'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
        'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
        'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
        'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
        '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
        '8': '---..', '9': '----.', ' ': '/'
    }
    try:
        if not context.args:
            await update.message.reply_text("❌ Usage: /morse hello")
            return
        text = " ".join(context.args).upper()
        morse = " ".join([morse_dict.get(char, '?') for char in text])
        await update.message.reply_text(f"📡 `{morse}`", parse_mode="Markdown")
        logger.info(f"📡 {update.effective_user.id} converted to morse")
    except Exception as e:
        logger.error(f"Morse error: {e}")
        await update.message.reply_text("❌ Failed to convert")

@user_tracking
async def random_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate random number."""
    import random
    try:
        if context.args and len(context.args) >= 2:
            min_num = int(context.args[0])
            max_num = int(context.args[1])
            if min_num > max_num:
                await update.message.reply_text("❌ Min must be less than max")
                return
        else:
            min_num, max_num = 1, 100
        
        result = random.randint(min_num, max_num)
        await update.message.reply_text(f"🎲 **Random: {result}** (between {min_num}-{max_num})", parse_mode="Markdown")
        logger.info(f"🎲 {update.effective_user.id} generated random number")
    except ValueError:
        await update.message.reply_text("❌ Usage: /random [min] [max] or /random for 1-100")
    except Exception as e:
        logger.error(f"Random error: {e}")
        await update.message.reply_text("❌ Failed to generate number")

@user_tracking
async def upside_down(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Flip text upside down."""
    flip_map = {
        'a': 'ɐ', 'b': 'q', 'c': 'ɔ', 'd': 'p', 'e': 'ǝ', 'f': 'ɟ',
        'g': 'ƃ', 'h': 'ɥ', 'i': 'ᴉ', 'j': 'ɾ', 'k': 'ʞ', 'l': 'l',
        'm': 'ɯ', 'n': 'u', 'o': 'o', 'p': 'd', 'q': 'b', 'r': 'ɹ',
        's': 's', 't': 'ʇ', 'u': 'n', 'v': 'ʌ', 'w': 'ʍ', 'x': 'x',
        'y': 'ʎ', 'z': 'z', '.': '˙', ',': '\'', '!': '¡', '?': '¿'
    }
    try:
        if not context.args:
            await update.message.reply_text("❌ Usage: /flip hello world")
            return
        text = " ".join(context.args).lower()
        flipped = "".join([flip_map.get(char, char) for char in text])[::-1]
        await update.message.reply_text(f"🙃 **{flipped}**", parse_mode="Markdown")
        logger.info(f"🙃 {update.effective_user.id} flipped text")
    except Exception as e:
        logger.error(f"Flip error: {e}")
        await update.message.reply_text("❌ Failed to flip")

@user_tracking
async def base64_encode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Encode text to base64."""
    import base64
    try:
        if not context.args:
            await update.message.reply_text("❌ Usage: /b64 hello world")
            return
        text = " ".join(context.args)
        encoded = base64.b64encode(text.encode()).decode()
        await update.message.reply_text(f"🔐 `{encoded}`", parse_mode="Markdown")
        logger.info(f"🔐 {update.effective_user.id} encoded base64")
    except Exception as e:
        logger.error(f"Base64 error: {e}")
        await update.message.reply_text("❌ Failed to encode")

@user_tracking
async def guess_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a number guessing game."""
    import random
    try:
        # Initialize game state if needed
        if not hasattr(context.user_data, 'secret_number'):
            context.user_data['secret_number'] = random.randint(1, 100)
            context.user_data['guesses'] = 0
            await update.message.reply_text("🎯 I'm thinking of a number 1-100. Guess it! Reply: /guess <number>")
            logger.info(f"🎯 {update.effective_user.id} started guess game")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Usage: /guess <number>")
            return
        
        guess = int(context.args[0])
        secret = context.user_data['secret_number']
        context.user_data['guesses'] += 1
        
        if guess == secret:
            msg = f"🎉 Correct! The number was {secret}! Guesses: {context.user_data['guesses']}"
            del context.user_data['secret_number']
            del context.user_data['guesses']
        elif guess < secret:
            msg = f"📈 Too low! Try higher."
        else:
            msg = f"📉 Too high! Try lower."
        
        await update.message.reply_text(msg)
        logger.info(f"🎯 {update.effective_user.id} guess: {guess}")
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number")
    except Exception as e:
        logger.error(f"Guess error: {e}")
        await update.message.reply_text("❌ Game error")

@user_tracking
async def user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get your user ID."""
    try:
        uid = update.effective_user.id
        name = update.effective_user.first_name
        await update.message.reply_text(f"👤 **Your ID:** `{uid}`\n📝 **Name:** {name}", parse_mode="Markdown")
        logger.info(f"👤 {uid} checked their ID")
    except Exception as e:
        logger.error(f"UserID error: {e}")
        await update.message.reply_text("❌ Failed to get ID")

@user_tracking
async def user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get your profile info."""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        user_id = str(user.id)
        
        stats = bot_data["stats"].get(user_id, {})
        msgs = stats.get("messages", 0)
        queries = stats.get("ai_queries", 0)
        warns = bot_data["warnings"].get(user_id, 0)
        
        profile = f"""
👤 **PROFILE**
├─ ID: `{user.id}`
├─ Name: {user.first_name}
├─ Username: @{user.username if user.username else "N/A"}
├─ Chat ID: `{chat_id}`
├─ Is Bot: {user.is_bot}
├─ Is Premium: {user.is_premium if hasattr(user, 'is_premium') else 'N/A'}

📊 **STATS**
├─ Messages: {msgs}
├─ AI Queries: {queries}
├─ Warnings: {warns}/{MAX_WARNINGS}
"""
        await update.message.reply_text(profile, parse_mode="Markdown")
        logger.info(f"👤 {user.id} viewed profile")
    except Exception as e:
        logger.error(f"Profile error: {e}")
        await update.message.reply_text("❌ Failed to load profile")

@user_tracking
async def invite_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get chat invite link."""
    try:
        chat_id = update.effective_chat.id
        try:
            link = await context.bot.create_chat_invite_link(chat_id)
            await update.message.reply_text(f"🔗 **Invite Link:**\n{link.invite_link}", parse_mode="Markdown")
            logger.info(f"🔗 {update.effective_user.id} generated invite link")
        except Exception:
            await update.message.reply_text("❌ Cannot generate invite link. Not group admin or private chat.")
    except Exception as e:
        logger.error(f"Invite error: {e}")
        await update.message.reply_text("❌ Failed to get invite link")

@user_tracking
async def members_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get member count."""
    try:
        chat_id = update.effective_chat.id
        count = await context.bot.get_chat_member_count(chat_id)
        chat = await context.bot.get_chat(chat_id)
        title = chat.title or "Private Chat"
        await update.message.reply_text(f"👥 **{title}**\n📊 Members: {count}", parse_mode="Markdown")
        logger.info(f"👥 {update.effective_user.id} checked members")
    except Exception as e:
        logger.error(f"Members error: {e}")
        await update.message.reply_text("❌ Failed to get member count")

@user_tracking
async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get random inspirational quote."""
    quotes = [
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Innovation distinguishes between a leader and a follower. - Steve Jobs",
        "Life is what happens when you're busy making other plans. - John Lennon",
        "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
        "It is during our darkest moments that we must focus to see the light. - Aristotle",
        "The only impossible journey is the one you never begin. - Tony Robbins",
        "Success is not final, failure is not fatal. - Winston Churchill",
        "What lies behind us and what lies before us are tiny matters compared to what lies within us. - Ralph Waldo Emerson",
        "Believe you can and you're halfway there. - Theodore Roosevelt",
        "The best time to plant a tree was 20 years ago. The second best time is now. - Chinese Proverb"
    ]
    import random
    try:
        quote_text = random.choice(quotes)
        await update.message.reply_text(f"💭 **{quote_text}**", parse_mode="Markdown")
        logger.info(f"💭 {update.effective_user.id} got a quote")
    except Exception as e:
        logger.error(f"Quote error: {e}")
        await update.message.reply_text("❌ Failed to get quote")

@user_tracking
async def dice_roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roll a dice (1-6)."""
    import random
    try:
        result = random.randint(1, 6)
        await update.message.reply_text(f"🎲 **You rolled: {result}**", parse_mode="Markdown")
        logger.info(f"🎲 {update.effective_user.id} rolled dice")
    except Exception as e:
        logger.error(f"Dice error: {e}")
        await update.message.reply_text("❌ Failed to roll dice")

@user_tracking
async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check bot uptime."""
    try:
        import time
        # Get start time from metadata
        start_time = bot_data.get("metadata", {}).get("bot_start_time")
        if not start_time:
            await update.message.reply_text("🟢 Bot is online! (Start time not tracked)")
            return
        
        elapsed = time.time() - start_time
        hours = int(elapsed // 3600)
        mins = int((elapsed % 3600) // 60)
        secs = int(elapsed % 60)
        
        await update.message.reply_text(f"⏱️ **Bot Uptime:** {hours}h {mins}m {secs}s", parse_mode="Markdown")
        logger.info(f"⏱️ {update.effective_user.id} checked uptime")
    except Exception as e:
        logger.error(f"Uptime error: {e}")
        await update.message.reply_text("❌ Failed to get uptime")

@user_tracking
async def hajhanm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Special command."""
    try:
        await update.message.reply_text("🤣 LOSERS")
        logger.info(f"😂 {update.effective_user.id} triggered hajhanm")
    except Exception as e:
        logger.error(f"Hajhanm error: {e}")

@user_tracking
async def hoba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Special command - Our Queen."""
    try:
        await update.message.reply_text("👑 OUR QUEEN")
        logger.info(f"👑 {update.effective_user.id} triggered hoba")
    except Exception as e:
        logger.error(f"Hoba error: {e}")

@user_tracking
async def serok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send Serok music link."""
    try:
        await update.message.reply_text(
            "🎵 SEROK MUSIC\n\n"
            "https://www.youtube.com/watch?v=T77sqGOd4J8&list=RDT77sqGOd4J8&start_radio=1"
        )
        logger.info(f"🎵 {update.effective_user.id} requested Serok music")
    except Exception as e:
        logger.error(f"Serok error: {e}")

@user_tracking
async def amanj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Special command - KING."""
    try:
        await update.message.reply_text("👑 KING")
        logger.info(f"👑 {update.effective_user.id} triggered amanj")
    except Exception as e:
        logger.error(f"Amanj error: {e}")

@user_tracking
async def arya(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Special command - Biji PKK."""
    try:
        await update.message.reply_text("🚩 Biji PKK")
        logger.info(f"🚩 {update.effective_user.id} triggered arya")
    except Exception as e:
        logger.error(f"Arya error: {e}")

@user_tracking
async def kurdishezdi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Special command - Biji Serok Barzani."""
    try:
        await update.message.reply_text("🇮🇶 BIJI SEROK BARZANI")
        logger.info(f"🇮🇶 {update.effective_user.id} triggered kurdishezdi")
    except Exception as e:
        logger.error(f"Kurdishezdi error: {e}")

@user_tracking
async def whisky_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Special command - Whisky price."""
    try:
        await update.message.reply_text("🥃 500$ WHISKY")
        logger.info(f"🥃 {update.effective_user.id} triggered whisky")
    except Exception as e:
        logger.error(f"Whisky error: {e}")

@user_tracking
@admin_only
async def speak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable Gemini speak mode for admins."""
    try:
        bot_data["metadata"]["speak_mode"] = True
        save_data(bot_data)
        await update.message.reply_text("🤖 SPEAK MODE ENABLED\n\nI will now respond to all messages with AI")
        logger.info(f"🤖 {update.effective_user.id} enabled speak mode")
    except Exception as e:
        logger.error(f"Speak error: {e}")
        await update.message.reply_text("❌ Failed to enable speak mode")

@user_tracking
@admin_only
async def stop_speak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Disable Gemini speak mode."""
    try:
        bot_data["metadata"]["speak_mode"] = False
        save_data(bot_data)
        await update.message.reply_text("🔇 SPEAK MODE DISABLED\n\nBack to command mode")
        logger.info(f"🤖 {update.effective_user.id} disabled speak mode")
    except Exception as e:
        logger.error(f"Stop speak error: {e}")
        await update.message.reply_text("❌ Failed to disable speak mode")

@user_tracking
@admin_only
async def unspeak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alias for stop_speak - disable Gemini speak mode."""
    await stop_speak(update, context)

# =========================
# ERROR HANDLER
# =========================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors with HTTP error detection."""
    error = context.error
    
    # Log the error
    logger.error(f"❌ Error: {error}")
    
    # Handle specific HTTP errors
    if hasattr(error, 'status_code'):
        if error.status_code == 429:
            logger.warning("⚠️ Rate limited by Telegram (429)")
        elif error.status_code == 400:
            logger.error("❌ Bad request (400) - Check bot configuration")
        elif error.status_code == 401:
            logger.error("❌ Unauthorized (401) - Check bot token")
        elif error.status_code == 403:
            logger.error("❌ Forbidden (403) - Bot may be blocked")
        elif error.status_code == 404:
            logger.error("❌ Not found (404) - Chat/user not found")
        elif error.status_code == 500:
            logger.error("❌ Telegram server error (500)")
    
    # Handle timeout errors
    if "timeout" in str(error).lower():
        logger.warning("⏱️ Request timeout - network may be slow")
    
    # Handle connection errors
    if "connection" in str(error).lower():
        logger.warning("🔌 Connection error - will retry")
    
    # Notify user if update exists
    if update and hasattr(update, 'message'):
        try:
            await update.message.reply_text("⚠️ Bot encountered an error. Check logs.")
        except:
            pass

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
    app.add_handler(CommandHandler("update", update_command))
    app.add_handler(CommandHandler("test", test_ai))
    app.add_handler(CommandHandler("ai", ai_command))
    app.add_handler(CommandHandler("ilikeu", warn))
    app.add_handler(CommandHandler("warns", check_warns))
    app.add_handler(CommandHandler("clear_warns", clear_warns))
    app.add_handler(CommandHandler("Shut", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("unshut", unmute))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("iloveu", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("info", user_info))
    app.add_handler(CommandHandler("admins", admins))
    app.add_handler(CommandHandler("debug_warns", debug_warns))
    app.add_handler(CommandHandler("authorize", authorize))
    app.add_handler(CommandHandler("deauthorize", deauthorize))
    app.add_handler(CommandHandler("authorized", authorized_list))
    app.add_handler(CommandHandler("roll", roll))
    app.add_handler(CommandHandler("coin", coin))
    app.add_handler(CommandHandler("calc", calc))
    app.add_handler(CommandHandler("echo", echo))
    app.add_handler(CommandHandler("time", time_cmd))
    app.add_handler(CommandHandler("Rape", Rape))
    app.add_handler(CommandHandler("8ball", eightball))
    app.add_handler(CommandHandler("reverse", reverse))
    app.add_handler(CommandHandler("fact", fact))
    app.add_handler(CommandHandler("morse", morse))
    app.add_handler(CommandHandler("random", random_num))
    app.add_handler(CommandHandler("flip", upside_down))
    app.add_handler(CommandHandler("b64", base64_encode))
    app.add_handler(CommandHandler("guess", guess_game))
    app.add_handler(CommandHandler("userid", user_id))
    app.add_handler(CommandHandler("profile", user_profile))
    app.add_handler(CommandHandler("invite", invite_link))
    app.add_handler(CommandHandler("members", members_count))
    app.add_handler(CommandHandler("quote", quote))
    app.add_handler(CommandHandler("dice", dice_roll))
    app.add_handler(CommandHandler("uptime", uptime))
    app.add_handler(CommandHandler("hajhanm", hajhanm))
    app.add_handler(CommandHandler("hoba", hoba))
    app.add_handler(CommandHandler("Serok", serok))
    app.add_handler(CommandHandler("Amanj", amanj))
    app.add_handler(CommandHandler("Arya", arya))
    app.add_handler(CommandHandler("kurdishezdi", kurdishezdi))
    app.add_handler(CommandHandler("Whisky", whisky_cmd))
    app.add_handler(CommandHandler("speak", speak))
    app.add_handler(CommandHandler("stop_speak", stop_speak))
    app.add_handler(CommandHandler("unSpeak", unspeak))
    
    # Messages (must be last)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return app

# =========================
# MAIN (24/7 OPERATION)
# =========================

def run_bot_with_recovery():
    """Run bot with automatic recovery and restart."""
    import time
    
    retry_count = 0
    max_retries = 5
    base_delay = 5  # seconds
    
    while True:
        try:
            logger.info("=" * 60)
            logger.info("🥃 WHISKY_BOT - ELITE VERSION STARTING")
            logger.info(f"👮 Admin IDs: {ADMIN_IDS}")
            logger.info(f"🤖 AI Status: {'✅ ONLINE' if AI_AVAILABLE else '⚠️ OFFLINE'}")
            logger.info(f"📊 Tracking {len(bot_data['stats'])} users")
            logger.info("=" * 60)
            
            app = setup_bot()
            print("\n✅ Bot is running 24/7... Press Ctrl+C to stop\n")
            
            retry_count = 0  # Reset retry count on successful connection
            app.run_polling(drop_pending_updates=True)
            
        except KeyboardInterrupt:
            logger.info("⛔ Bot stopped by user")
            break
            
        except Exception as e:
            retry_count += 1
            delay = min(base_delay * (2 ** retry_count), 300)  # Max 5 min delay
            
            logger.error(f"🔥 Error: {e}")
            logger.error(f"⏳ Retry {retry_count}/{max_retries} in {delay}s...")
            
            if retry_count >= max_retries:
                logger.critical(f"❌ Max retries reached. Bot failed.")
                break
            
            time.sleep(delay)

if __name__ == "__main__":
    run_bot_with_recovery()