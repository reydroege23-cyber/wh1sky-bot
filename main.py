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

from openai import OpenAI
from datetime import timedelta, datetime
import logging
import json
from pathlib import Path
from functools import wraps
from config import *
import asyncio
import random
import base64
import traceback
import os

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
# AI SETUP (OpenRouter)
# =========================

try:
    logger.info("🔧 Configuring OpenRouter AI...")
    logger.info(f"📝 API Key present: {bool(OPENROUTER_API_KEY)}")
    logger.info(f"🤖 Model: {AI_MODEL}")
    
    # Initialize OpenRouter client (OpenAI-compatible)
    ai_client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY
    )
    logger.info("✅ OpenRouter configured successfully")
    
    # Mark as available - test will happen on first /ai or /test command
    AI_AVAILABLE = True
    logger.info("✅ AI will be tested on first use")
        
except Exception as e:
    logger.warning(f"⚠️ AI configuration failed: {type(e).__name__}: {e}")
    import traceback
    logger.warning(traceback.format_exc())
    AI_AVAILABLE = False
    ai_client = None

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
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            logger.warning(f"🚫 Unauthorized access by {user_id}")
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
# RATE LIMITING (COOLDOWNS)
# =========================

# Track cooldowns per user: {"command_user_id": timestamp}
command_cooldowns = {}
ai_cooldowns = {}
speak_cooldowns = {}

def check_cooldown(user_id: int, cooldown_type: str, cooldown_seconds: int) -> tuple[bool, str]:
    """Check if user is in cooldown. Returns (is_allowed, message)."""
    if not ENABLE_RATE_LIMITING:
        return True, ""
    
    # Admins always bypass cooldowns
    if user_id in ADMIN_IDS:
        return True, ""
    
    current_time = datetime.now()
    cooldown_key = f"{cooldown_type}_{user_id}"
    
    # Get appropriate cooldown dict
    if cooldown_type == "ai":
        cooldown_dict = ai_cooldowns
    elif cooldown_type == "speak":
        cooldown_dict = speak_cooldowns
    else:
        cooldown_dict = command_cooldowns
    
    # Check if user has a cooldown
    if cooldown_key in cooldown_dict:
        last_time = cooldown_dict[cooldown_key]
        time_diff = (current_time - last_time).total_seconds()
        
        if time_diff < cooldown_seconds:
            remaining = cooldown_seconds - int(time_diff)
            return False, f"⏱️ Cooldown active. Wait {remaining}s"
    
    # Update cooldown
    cooldown_dict[cooldown_key] = current_time
    return True, ""

def rate_limit(cooldown_type: str = "command", cooldown_seconds: int = None):
    """Rate limiting decorator for commands."""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            
            # Determine cooldown time
            if cooldown_seconds is not None:
                cooldown_time = cooldown_seconds
            elif cooldown_type == "ai":
                cooldown_time = AI_COOLDOWN
            elif cooldown_type == "speak":
                cooldown_time = SPEAK_COOLDOWN
            else:
                cooldown_time = COMMAND_COOLDOWN
            
            # Check cooldown
            allowed, message = check_cooldown(user_id, cooldown_type, cooldown_time)
            if not allowed:
                await update.message.reply_text(message)
                return
            
            return await func(update, context)
        return wrapper
    return decorator

# =========================
# AI FUNCTIONS (ENHANCED)
# =========================

async def ask_ai(message: str) -> str:
    """Get response from AI using OpenRouter API."""
    if not AI_AVAILABLE or ai_client is None:
        return "⚠️ AI service is offline. Contact admin."
    
    try:
        # Use OpenRouter API via asyncio thread
        response = await asyncio.wait_for(
            asyncio.to_thread(
                lambda: ai_client.chat.completions.create(
                    model=AI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful Telegram assistant. Respond concisely and friendly."},
                        {"role": "user", "content": message}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
            ),
            timeout=AI_TIMEOUT
        )
        
        # Extract text from response
        if not response or not response.choices:
            logger.error("❌ Empty response from OpenRouter API")
            return "❌ AI returned empty response. Try again."
        
        text = response.choices[0].message.content.strip()
        
        # Check if text is empty
        if not text:
            logger.error("❌ AI returned empty text")
            return "❌ AI returned empty response. Try again."
        
        # Truncate to max length
        text = text[:MAX_RESPONSE_LENGTH]
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
• `/ai <question>` - Ask Whisky AI
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
• `/speak` - Enable Whisky AI speak mode
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
            status_msg += "✅ Whisky AI: Ready\n"
            status_msg += f"⚡ Response Time: {response_time_ms:.0f}ms"
        else:
            status_msg = "🟡 **BOT STATUS: DEGRADED**\n\n"
            status_msg += "✅ Telegram: Connected\n"
            status_msg += "❌ Whisky AI: Offline\n\n"
            status_msg += "**Possible causes:**\n"
            status_msg += "• Invalid API key\n"
            status_msg += "• Network connection issue\n"
            status_msg += "• API rate limit exceeded\n"
            status_msg += "• Whisky AI service unavailable\n\n"
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
📢 **WHISKY BOT - LATEST UPDATES**

**✨ RECENT CHANGES:**
• ✅ Removed authorization system - all users have access
• ✅ Removed /authorize commands - no more access restrictions
• ✅ Simplified admin system - cleaner codebase

**🎮 FUN COMMANDS:**
• /roll [sides] - Roll dice
• /coin - Flip a coin
• /calc <math> - Calculator
• /echo <text> - Echo text
• /time - Current time
• /roast - Get a funny roast
• /ship <user1> <user2> - Love calculator
• /rate <thing> - Rate something
• /meme - Random meme
• /truth - Truth question
• /dare - Dare challenge
• /compliment - Get a compliment
• /insult - Get an insult
• /ascii <text> - ASCII art
• /hack <user> - Fake hacking
• /fancy <text> - Fancy fonts
• /hotrate - Hotness rating
• /iq <user> - IQ score
• /gayrate - Fun vibes meter

**🤖 AI COMMANDS:**
• /ai <question> - Ask Whisky AI
• /speak - AI respond mode (admin)

**🛡️ ADMIN COMMANDS:**
• /warn <user> - Issue warning
• /warns <user> - Check warnings
• /clear_warns - Clear all warnings
• /Shut <user> - Silence user
• /unmute - Restore user
• /kick - Remove user
• /ban - Ban user
• /unban - Unban user
• /info <user> - User info
• /admins - List admins

**📊 UTILITY:**
• /start - Welcome message
• /help - Full command list
• /stats - Your statistics
• /ping - Bot status
• /updates - This message

**📝 VERSION:** 2.6+

🎉 Enjoy using Whisky Bot!
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
@rate_limit(cooldown_type="ai")
async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ai command to ask Whisky AI."""
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
        if user_id in bot_data["stats"]:
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
        # SPEAK MODE - Whisky AI responds to all messages
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
                
                if user_id in bot_data["stats"]:
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
    """Issue warning - 3 warnings = permanent ban (FIXED)."""
    user_id = None
    user_id_str = None
    username = None
    
    try:
        # Get user from reply, mention, or user ID
        user_id, username = await get_user_from_command(update, context)
        
        if not user_id:
            await update.message.reply_text(
                "❌ Please reply to a message or mention a username.\n"
                "Example: `/warn @username`"
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
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban user - STRICT: Requires /ban @username or reply ONLY."""
    try:
        # STRICT: Check if this is a reply message context
        # If replying, allow ban without additional args
        if update.message.reply_to_message:
            user_id = update.message.reply_to_message.from_user.id
            username = update.message.reply_to_message.from_user.first_name or "User"
        else:
            # NOT replying: MUST have explicit @username in args
            if not context.args:
                await update.message.reply_text(
                    "❌ Please reply to a message or provide a username.\\n"
                    "Example: `/ban @username`"
                )
                return
            
            arg = context.args[0]
            
            # MUST start with @
            if not arg.startswith('@'):
                await update.message.reply_text(
                    "❌ Please mention a user with @username.\\n"
                    "Example: `/ban @username`"
                )
                return
            
            username = arg[1:]  # Remove @
            
            try:
                # Try to resolve @username
                user = await context.bot.get_chat_member(
                    chat_id=update.effective_chat.id,
                    user_id=f"@{username}"
                )
                if user:
                    user_id = user.user.id
                else:
                    await update.message.reply_text(f"❌ User @{username} not found in chat")
                    return
            except Exception as e:
                logger.error(f"Failed to resolve @{username}: {e}")
                await update.message.reply_text(f"❌ User @{username} not found")
                return
        
        # Check if admin
        if user_id in ADMIN_IDS:
            await update.message.reply_text("❌ Cannot ban admins.")
            return

        # BAN THE USER
        await context.bot.ban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text(f"🚫 {username} banned")
        logger.info(f"🚫 {user_id} banned by {update.effective_user.id}")
        
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
async def nuke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete recent messages from chat. Usage: /nuke [count] (default: 20, max: 100)"""
    try:
        # Get number of messages to delete
        count = 20  # default
        if context.args:
            try:
                count = int(context.args[0])
                if count < 1 or count > 100:
                    await update.message.reply_text("❌ Count must be between 1 and 100")
                    return
            except ValueError:
                await update.message.reply_text("❌ Invalid number. Usage: `/nuke [1-100]`", parse_mode="Markdown")
                return
        
        chat_id = update.effective_chat.id
        message_id = update.message.message_id
        deleted = 0
        failed = 0
        
        # Delete the command message first
        try:
            await context.bot.delete_message(chat_id, message_id)
            deleted += 1
        except Exception as e:
            logger.warning(f"Could not delete command message: {e}")
        
        # Delete previous messages
        for msg_id in range(message_id - 1, message_id - count - 1, -1):
            if msg_id < 1:
                break
            try:
                await context.bot.delete_message(chat_id, msg_id)
                deleted += 1
            except Exception as e:
                # Message may not exist or already deleted
                logger.debug(f"Could not delete message {msg_id}: {e}")
                failed += 1
                continue
        
        # Send confirmation message
        result_msg = await context.bot.send_message(
            chat_id,
            f"💣 **NUKED!** Deleted {deleted} message(s)"
        )
        logger.info(f"💣 Nuked {deleted} messages in {chat_id} by {update.effective_user.id}")
        
        # Delete confirmation after 3 seconds
        try:
            await asyncio.sleep(3)
            await context.bot.delete_message(chat_id, result_msg.message_id)
        except:
            pass
            
    except Exception as e:
        logger.error(f"Nuke error: {e}")
        await context.bot.send_message(update.effective_chat.id, f"❌ Failed to nuke: {str(e)[:100]}")

@admin_only
async def iloveu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Permanently ban user (alias for /ban)."""
    await ban(update, context)

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
async def dream(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a weird dream story using AI."""
    try:
        if not AI_AVAILABLE:
            await update.message.reply_text("🤖 AI service offline")
            return
        
        # Show thinking message
        thinking_msg = await update.message.reply_text("😴 Generating your dream...")
        
        # Generate dream prompt
        dream_prompt = "You are a creative dream generator. Generate a SHORT, WEIRD, and SURREAL dream story (2-3 sentences). Make it absurd, confusing, and dreamlike with unexpected twists. Be creative and weird!"
        
        # Get AI response
        dream_story = await ask_ai(dream_prompt)
        
        # Edit the thinking message with the dream
        try:
            await thinking_msg.edit_text(f"😴 **Your Dream:**\n\n{dream_story}")
        except Exception as e:
            logger.debug(f"Failed to edit message: {e}")
            await update.message.reply_text(f"😴 **Your Dream:**\n\n{dream_story}")
        
        logger.info(f"😴 {update.effective_user.id} generated a dream")
        
    except Exception as e:
        logger.error(f"Dream error: {e}")
        await update.message.reply_text("❌ Failed to generate dream")

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
async def daddy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Special command - Whisky The Great."""
    try:
        await update.message.reply_text("👑 Whisky The Great")
        logger.info(f"👑 {update.effective_user.id} triggered daddy")
    except Exception as e:
        logger.error(f"Daddy error: {e}")

@user_tracking
async def waleed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Special command - football kid."""
    try:
        await update.message.reply_text("⚽ football kid")
        logger.info(f"⚽ {update.effective_user.id} triggered waleed")
    except Exception as e:
        logger.error(f"Waleed error: {e}")

@user_tracking
async def kiss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Special command - Mauh by whisky."""
    try:
        await update.message.reply_text("💋 Mauh by whisky")
        logger.info(f"💋 {update.effective_user.id} triggered kiss")
    except Exception as e:
        logger.error(f"Kiss error: {e}")

@rate_limit(cooldown_type="command", cooldown_seconds=0)
@user_tracking
@admin_only
async def speak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable Whisky AI speak mode for admins."""
    try:
        # Ensure metadata exists
        if "metadata" not in bot_data:
            bot_data["metadata"] = {}
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
    """Disable Whisky AI speak mode."""
    try:
        # Ensure metadata exists
        if "metadata" not in bot_data:
            bot_data["metadata"] = {}
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
    """Alias for stop_speak - disable Whisky AI speak mode."""
    await stop_speak(update, context)

# =========================
# FUN COMMANDS (NEW)
# =========================

@user_tracking
async def roast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roast a user with a funny insult."""
    roasts = [
        "You're so boring, even your wifi disconnects from you.",
        "You bring everyone so much joy... when you leave the room.",
        "I'd roast you harder, but my mommy said I can't bully people with disabilities.",
        "You're the reason the gene pool needs a lifeguard.",
        "If you were a vegetable, you'd be a radish... because you're absolutely radishing in negativity.",
        "You're like a cloud. When you disappear, it's a beautiful day.",
        "I'd explain it to you, but I don't have a crayon small enough.",
        "You're proof that evolution can go in reverse.",
        "Keep rolling your eyes, maybe you'll find a brain back there.",
        "You're not stupid, you just have bad luck when you think.",
        "You're not useless… you can always be a bad example.",
        "Somewhere out there, a tree is replacing the oxygen you waste.",
        "Your conversations have unskippable cutscenes.",
        "Your jokes arrive with internet explorer speed.",
        "You argue like a broken CAPTCHA.",
        "You look AI-generated with low settings.",
        "Your brain runs on trial version software.",
        "You have the survival instincts of a loading screen tip.",
        "If mistakes were achievements, you'd be legendary.",
        "Your vibe screams 'buffering…'",
        "Even NPCs have more personality.",
        "You make silence uncomfortable.",
        "Your decisions should require parental approval.",
        "Your aura smells like expired updates.",
        "You could lose a debate against a mirror.",
        "You're the human version of a typo.",
        "Your confidence is inversely proportional to your intelligence.",
        "Your train of thought keeps derailing.",
        "Even your excuses sound copy-pasted.",
        "You're like a bug report nobody fixes."
    ]
    try:
        if update.message.reply_to_message:
            target_name = update.message.reply_to_message.from_user.first_name or "User"
        elif context.args:
            target_name = context.args[0].replace('@', '')
        else:
            target_name = "you"
        
        roast_msg = random.choice(roasts)
        await update.message.reply_text(f"🔥 Hey {target_name}:\n\n{roast_msg}")
        logger.info(f"🔥 {update.effective_user.id} roasted {target_name}")
    except Exception as e:
        logger.error(f"Roast error: {e}")
        await update.message.reply_text("❌ Failed to roast")

@user_tracking
async def ship(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Calculate love percentage between two users."""
    try:
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ Usage: /ship @user1 @user2\n"
                "Example: `/ship @john @jane`"
            )
            return
        
        user1 = context.args[0].replace('@', '')
        user2 = context.args[1].replace('@', '')
        
        # Generate "random" but consistent score based on names
        score = (hash(user1 + user2) % 101)
        
        # Create love meter
        filled = score // 10
        empty = 10 - filled
        meter = "❤️" * filled + "🤍" * empty
        
        message = f"💑 **{user1}** + **{user2}**\n\n"
        message += f"{meter}\n"
        message += f"**Love Score: {score}%**\n\n"
        
        if score > 80:
            message += "🔥 Perfect match! Better start planning the wedding!"
        elif score > 60:
            message += "💕 Great chemistry! You two would be cute together."
        elif score > 40:
            message += "😊 Could work out with effort."
        else:
            message += "😬 Maybe just stay friends?"
        
        await update.message.reply_text(message, parse_mode="Markdown")
        logger.info(f"💑 {update.effective_user.id} shipped {user1} & {user2}")
    except Exception as e:
        logger.error(f"Ship error: {e}")
        await update.message.reply_text("❌ Failed to ship")

@user_tracking
async def rate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rate something 1-10."""
    try:
        if not context.args:
            await update.message.reply_text(
                "❌ Usage: /rate <text>\n"
                "Example: `/rate pizza`"
            )
            return
        
        text = " ".join(context.args)
        score = (hash(text) % 10) + 1  # 1-10 rating
        
        stars = "⭐" * score + "☆" * (10 - score)
        
        await update.message.reply_text(f"\n📊 **Rating: {text}**\n\n{stars}\n\n**Score: {score}/10**", parse_mode="Markdown")
        logger.info(f"⭐ {update.effective_user.id} rated '{text}'")
    except Exception as e:
        logger.error(f"Rate error: {e}")
        await update.message.reply_text("❌ Failed to rate")

@user_tracking
async def meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get a random meme description."""
    memes = [
        "When you're trying to look busy at work but your boss walks by.",
        "Me pretending to work while my boss is looking.",
        "POV: You're about to fail your exam.",
        "When someone asks if you're okay and you say 'yeah I'm fine'.",
        "Me: *exists* | My brain at 3am: Remember that embarrassing thing you did in 3rd grade?",
        "Monday: exists | Me:",
        "When the teacher asks who didn't do homework and you look straight ahead.",
        "Me explaining why I'm late to work: [complicated excuse]",
        "POV: You just realized it's been raining the entire time.",
        "When someone says 'relax' to you:"
    ]
    try:
        meme_text = random.choice(memes)
        await update.message.reply_text(f"😂 **MEME:**\n\n{meme_text}")
        logger.info(f"😂 {update.effective_user.id} got a meme")
    except Exception as e:
        logger.error(f"Meme error: {e}")
        await update.message.reply_text("❌ Failed to get meme")

@user_tracking
async def truth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get a random truth question."""
    truths = [
        "What's your biggest secret?",
        "Who do you have a crush on?",
        "What's something you've never told anyone?",
        "What's your biggest fear?",
        "Have you ever cheated on someone?",
        "What's the most embarrassing thing you've done?",
        "What would you never admit to your parents?",
        "What's your guilty pleasure?",
        "Have you ever lied to your best friend?",
        "Have you ever been caught fucking yourself in the shower?",
        "What's the weirdest thing you've done for a dare?",
        "What is your ass size in cm?",
        "What is your Dick size in cm?",
        "Do you Suck someone dick?",
        "Do you like to suck dick?",
        "Are u gay?",
        "Are u straight?",
        "Are u Femboy?",
        "Do u love Dick?"
    ]
    
    # Initialize used truths tracking if not exists
    if "used_truths" not in bot_data:
        bot_data["used_truths"] = {}
    
    current_time = datetime.now()
    available_truths = []
    
    for truth in truths:
        last_used = bot_data["used_truths"].get(truth)
        if last_used is None or (current_time - datetime.fromisoformat(last_used)) > timedelta(minutes=1):
            available_truths.append(truth)
    
    # If no truths available (all used within last minute), allow reuse
    if not available_truths:
        available_truths = truths
    
    try:
        truth_q = random.choice(available_truths)
        # Record usage time
        bot_data["used_truths"][truth_q] = current_time.isoformat()
        save_data(bot_data)
        
        await update.message.reply_text(f"🎯 **TRUTH:**\n\n{truth_q}", parse_mode="Markdown")
        logger.info(f"🎯 {update.effective_user.id} got a truth question")
    except Exception as e:
        logger.error(f"Truth error: {e}")
        await update.message.reply_text("❌ Failed to get truth")

@user_tracking
async def dare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get a random dare challenge."""
    dares = [
        "Sing your favorite song out loud.",
        "Do 10 pushups right now.",
        "Text your crush and ask them out.",
        "Call your mom and tell her you love her.",
        "Speak in an accent for the next 5 minutes.",
        "Do a funny dance and film it.",
        "Imitate someone in the chat.",
        "Pretend to be a news anchor for 1 minute.",
        "Send a funny meme to your group chat.",
        "Post a selfie making a weird face.",
        "Try to do a somersault and send a video of it."
        "Send a voice message of you doing your best impression of a famous politician."
        "Pretend to be a tour guide and give a tour of your city or neighborhood, then send a voice message of it."
        "Try to do a handstand pushup and send a video of it."
        "Send a voice message of you doing your best impression of a famous historical figure."
        "Pretend to be a fitness instructor and give a workout routine for beginners, then send a voice message of it."
        "Try to do a one-handed pushup and send a video of it."
        "Send a voice message of you doing your best impression of a famous author."
        "Pretend to be a life coach and give advice on how to be successful, then send a voice message of it."
        "Try to do a handstand on a chair and send a video of it."
        # High probability dares (added multiple times for higher chance)
        "Put Toy in your ass and send a video of it.",
        "Put Toy in your ass and send a video of it.",
        "Put Toy in your ass and send a video of it.",
        "Put Toy in your ass and send a video of it.",
        "Let whisky rape you ",
        "Let whisky rape you ",
        "Let whisky rape you ",
        "Let whisky rape you ",
        "Send ass picture",
        "Send ass picture",
        "Send ass picture",
        "Send ass picture",
        "Send dick picture",
        "Send dick picture",
        "Send dick picture",
        "Send dick picture",
        "Send boobs picture",
        "Send boobs picture",
        "Send boobs picture",
        "Send boobs picture",
        "By who u get raped",
        "By who u get raped",
        "By who u get raped",
        "By who u get raped",
        "Suck your own dick",
        "Suck your own dick",
        "Suck your own dick",
        "Suck your own dick",
        "Let A pedo rape you",
        "Let A pedo rape you",
        "Let A pedo rape you",
        "Let A pedo rape you",
        "Put big Cucumber in your ass",
        "Put big Cucumber in your ass",
        "Put big Cucumber in your ass",
        "Put big Cucumber in your ass",
        "Eat your own shit",
        "Eat your own shit",
        "Eat your own shit",
        "Eat your own shit",
        "Put big Cucumber in your mouth and send ss ",
        "Put big Cucumber in your mouth and send ss ",
        "Put big Cucumber in your mouth and send ss ",
        "Put big Cucumber in your mouth and send ss ",
        "Rape yourself",
        "Rape yourself",
        "Rape yourself",
        "Rape yourself"
        
    ]
    
    # Initialize used dares tracking if not exists
    if "used_dares" not in bot_data:
        bot_data["used_dares"] = {}
    
    current_time = datetime.now()
    available_dares = []
    
    for dare in dares:
        last_used = bot_data["used_dares"].get(dare)
        if last_used is None or (current_time - datetime.fromisoformat(last_used)) > timedelta(minutes=1):
            available_dares.append(dare)
    
    # If no dares available (all used within last minute), allow reuse
    if not available_dares:
        available_dares = dares
    
    try:
        dare_msg = random.choice(available_dares)
        # Record usage time
        bot_data["used_dares"][dare_msg] = current_time.isoformat()
        save_data(bot_data)
        
        await update.message.reply_text(f"😈 **DARE:**\n\n{dare_msg}", parse_mode="Markdown")
        logger.info(f"😈 {update.effective_user.id} got a dare")
    except Exception as e:
        logger.error(f"Dare error: {e}")
        await update.message.reply_text("❌ Failed to get dare")

@user_tracking
async def compliment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Give someone a compliment."""
    compliments = [
        "You're an awesome person!",
        "You light up the room!",
        "You're a great listener!",
        "You have a great sense of humor!",
        "You're a strong person!",
        "Your perspective is refreshing!",
        "You're incredibly thoughtful!",
        "You're a gift to those around you!",
        "You're a smart cookie!",
        "You're a real go-getter!"
    ]
    try:
        if update.message.reply_to_message:
            target_name = update.message.reply_to_message.from_user.first_name or "User"
        elif context.args:
            target_name = context.args[0].replace('@', '')
        else:
            target_name = "you"
        
        compliment_msg = random.choice(compliments)
        await update.message.reply_text(f"💝 Hey {target_name}:\n\n{compliment_msg}")
        logger.info(f"💝 {update.effective_user.id} complimented {target_name}")
    except Exception as e:
        logger.error(f"Compliment error: {e}")
        await update.message.reply_text("❌ Failed to compliment")

@user_tracking
async def insult(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Give someone a funny insult."""
    insults = [
        "You're like a human version of a bad wifi connection.",
        "If you were a vegetable, you'd be a carrot... because you're pretty orange.",
        "You're the human equivalent of a participation trophy.",
        "You make a better door than a window.",
        "You're about as useful as a chocolate teapot.",
        "I'd agree with you but then we'd both be wrong.",
        "You're the reason God created the mute button.",
        "You're so dumb, you thought a QB was a Quickback.",
        "You're not the brightest bulb in the box.",
        "You're a perfect example of why some animals eat their young."
    ]
    try:
        if update.message.reply_to_message:
            target_name = update.message.reply_to_message.from_user.first_name or "User"
        elif context.args:
            target_name = context.args[0].replace('@', '')
        else:
            target_name = "you"
        
        insult_msg = random.choice(insults)
        await update.message.reply_text(f"😬 Hey {target_name}:\n\n{insult_msg}")
        logger.info(f"😬 {update.effective_user.id} insulted {target_name}")
    except Exception as e:
        logger.error(f"Insult error: {e}")
        await update.message.reply_text("❌ Failed to insult")

@user_tracking
async def ascii_art(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Convert text to ASCII art style."""
    try:
        if not context.args:
            await update.message.reply_text(
                "❌ Usage: /ascii <text>\n"
                "Example: `/ascii HELLO`"
            )
            return
        
        text = " ".join(context.args).upper()[:10]  # Limit to 10 chars
        
        ascii_map = {
            'A': ' █ ', 'B': '██', 'C': ' █ ', 'D': '██ ', 'E': '███',
            'F': '██ ', 'G': ' █ ', 'H': '█ █', 'I': ' █ ', 'J': '  █',
            'K': '█ █', 'L': '█  ', 'M': '█ █', 'N': '█ █', 'O': ' █ ',
            'P': '██ ', 'Q': ' █ ', 'R': '██ ', 'S': ' ██', 'T': '███',
            'U': '█ █', 'V': '█ █', 'W': '█ █', 'X': '█ █', 'Y': '█ █',
            'Z': '███', ' ': '   '
        }
        
        result = ""
        for char in text:
            result += ascii_map.get(char, '█')
        
        await update.message.reply_text(f"```\n{result}\n```", parse_mode="Markdown")
        logger.info(f"🎨 {update.effective_user.id} created ASCII art")
    except Exception as e:
        logger.error(f"ASCII error: {e}")
        await update.message.reply_text("❌ Failed to create ASCII art")

@user_tracking
async def hack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fake hacking animation for a user."""
    try:
        if update.message.reply_to_message:
            target_name = update.message.reply_to_message.from_user.first_name or "User"
        elif context.args:
            target_name = context.args[0].replace('@', '')
        else:
            target_name = "you"
        
        hack_msg = f"🔓 **HACKING {target_name.upper()}**\n\n"
        hack_msg += "```\n"
        hack_msg += "[████████░░] 56%\n\n"
        hack_msg += "➜ Accessing files...\n"
        hack_msg += "➜ Bypassing firewall...\n"
        hack_msg += "➜ Downloading data...\n\n"
        hack_msg += "[**HACK COMPLETE**]\n\n"
        hack_msg += "Files found:\n"
        hack_msg += "├─ selfies.zip\n"
        hack_msg += "├─ passwords.txt\n"
        hack_msg += "├─ memes/\n"
        hack_msg += "├─ secrets.doc\n"
        hack_msg += "└─ cringe_photos/\n"
        hack_msg += "```\n\n"
        hack_msg += "⚠️ Just kidding! This is a fake hack animation! 😄"
        
        await update.message.reply_text(hack_msg, parse_mode="Markdown")
        logger.info(f"🔓 {update.effective_user.id} hacked {target_name}")
    except Exception as e:
        logger.error(f"Hack error: {e}")
        await update.message.reply_text("❌ Failed to hack")

@user_tracking
async def fancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Convert text to fancy fonts."""
    fancy_map = {
        'a': '𝒂', 'b': '𝒃', 'c': '𝒄', 'd': '𝒅', 'e': '𝒆', 'f': '𝒇',
        'g': '𝒈', 'h': '𝒉', 'i': '𝒊', 'j': '𝒋', 'k': '𝒌', 'l': '𝒍',
        'm': '𝒎', 'n': '𝒏', 'o': '𝒐', 'p': '𝒑', 'q': '𝒒', 'r': '𝒓',
        's': '𝒔', 't': '𝒕', 'u': '𝒖', 'v': '𝒗', 'w': '𝒘', 'x': '𝒙',
        'y': '𝒚', 'z': '𝒛',
        'A': '𝑨', 'B': '𝑩', 'C': '𝑪', 'D': '𝑫', 'E': '𝑬', 'F': '𝑭',
        'G': '𝑮', 'H': '𝑯', 'I': '𝑰', 'J': '𝑱', 'K': '𝑲', 'L': '𝑳',
        'M': '𝑴', 'N': '𝑵', 'O': '𝑶', 'P': '𝑷', 'Q': '𝑸', 'R': '𝑹',
        'S': '𝑺', 'T': '𝑻', 'U': '𝑼', 'V': '𝑽', 'W': '𝑾', 'X': '𝑿',
        'Y': '𝒀', 'Z': '𝒁'
    }
    try:
        if not context.args:
            await update.message.reply_text(
                "❌ Usage: /fancy <text>\n"
                "Example: `/fancy hello`"
            )
            return
        
        text = " ".join(context.args)
        fancy_text = "".join([fancy_map.get(char, char) for char in text])
        
        await update.message.reply_text(f"✨ **{fancy_text}**", parse_mode="Markdown")
        logger.info(f"✨ {update.effective_user.id} used fancy fonts")
    except Exception as e:
        logger.error(f"Fancy error: {e}")
        await update.message.reply_text("❌ Failed to fancy")

@user_tracking
async def hotrate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rate someone's hotness percentage."""
    try:
        if update.message.reply_to_message:
            target_name = update.message.reply_to_message.from_user.first_name or "User"
            target_id = update.message.reply_to_message.from_user.id
        elif context.args:
            target_name = context.args[0].replace('@', '')
            target_id = hash(target_name)
        else:
            target_name = "you"
            target_id = update.effective_user.id
        
        score = (hash(str(target_id)) % 101)
        fire = "🔥" * (score // 10)
        
        message = f"🌡️ **HOTNESS RATING: {target_name}**\n\n"
        message += f"{fire}\n"
        message += f"**{score}% 🔥**\n\n"
        
        if score > 90:
            message += "🥵 SMOKING HOT!!!"
        elif score > 75:
            message += "😍 Very attractive!"
        elif score > 50:
            message += "😊 Pretty cute!"
        else:
            message += "👀 Decent looking."
        
        await update.message.reply_text(message, parse_mode="Markdown")
        logger.info(f"🌡️ {update.effective_user.id} rated {target_name}'s hotness")
    except Exception as e:
        logger.error(f"Hotrate error: {e}")
        await update.message.reply_text("❌ Failed to rate hotness")

@user_tracking
async def iq_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a random IQ score for a user."""
    try:
        if update.message.reply_to_message:
            target_name = update.message.reply_to_message.from_user.first_name or "User"
            target_id = update.message.reply_to_message.from_user.id
        elif context.args:
            target_name = context.args[0].replace('@', '')
            target_id = hash(target_name)
        else:
            target_name = "you"
            target_id = update.effective_user.id
        
        iq_score = (hash(str(target_id)) % 200) + 50  # 50-250 IQ
        
        message = f"🧠 **IQ SCORE: {target_name}**\n\n"
        message += f"**IQ: {iq_score}**\n\n"
        
        if iq_score > 160:
            message += "🤓 GENIUS LEVEL!"
        elif iq_score > 130:
            message += "📚 Very intelligent!"
        elif iq_score > 100:
            message += "✅ Above average!"
        elif iq_score > 85:
            message += "😊 Average intelligence."
        elif iq_score > 70:
            message += "🤔 Below average."
        else:
            message += "😅 Might need to study more!"
        
        await update.message.reply_text(message, parse_mode="Markdown")
        logger.info(f"🧠 {update.effective_user.id} checked {target_name}'s IQ")
    except Exception as e:
        logger.error(f"IQ error: {e}")
        await update.message.reply_text("❌ Failed to check IQ")

@user_tracking
async def gayrate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rate someone's "gay" (fun) percentage - just a meme stat."""
    try:
        if update.message.reply_to_message:
            target_name = update.message.reply_to_message.from_user.first_name or "User"
            target_id = update.message.reply_to_message.from_user.id
        elif context.args:
            target_name = context.args[0].replace('@', '')
            target_id = hash(target_name)
        else:
            target_name = "you"
            target_id = update.effective_user.id
        
        score = (hash(str(target_id)) % 101)
        rainbow = "🌈" * (score // 10)
        
        message = f"🌈 **FUN VIBES: {target_name}**\n\n"
        message += f"{rainbow}\n"
        message += f"**{score}% 🎉**\n\n"
        message += "(This is just a meme stat for fun!)"
        
        await update.message.reply_text(message, parse_mode="Markdown")
        logger.info(f"🌈 {update.effective_user.id} checked {target_name}'s fun vibes")
    except Exception as e:
        logger.error(f"Gayrate error: {e}")
        await update.message.reply_text("❌ Failed to rate fun vibes")

@user_tracking
async def sleep_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a sleep message."""
    try:
        await update.message.reply_text(
            "😴 **GOODNIGHT!**\n\n"
            "Get some rest! 🛌\n"
            "Sweet dreams! 💤\n\n"
            "Sleep well, see you tomorrow! 🌙",
            parse_mode="Markdown"
        )
        logger.info(f"😴 {update.effective_user.id} went to sleep")
    except Exception as e:
        logger.error(f"Sleep error: {e}")
        await update.message.reply_text("❌ Failed to send sleep message")

@user_tracking
async def goodmorning_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a good morning message."""
    try:
        await update.message.reply_text(
            "☀️ **GOOD MORNING!**\n\n"
            "Rise and shine! ✨\n"
            "Have an amazing day! 💪\n\n"
            "Let's make it a great one! 🚀",
            parse_mode="Markdown"
        )
        logger.info(f"☀️ {update.effective_user.id} got a morning greeting")
    except Exception as e:
        logger.error(f"Goodmorning error: {e}")
        await update.message.reply_text("❌ Failed to send morning message")

@user_tracking
async def goodnight_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a good night message."""
    try:
        await update.message.reply_text(
            "🌙 **GOODNIGHT!**\n\n"
            "Sleep tight! 🛌\n"
            "Don't let the bedbugs bite! 🪳😄\n"
            "See you in the morning! ⭐",
            parse_mode="Markdown"
        )
        logger.info(f"🌙 {update.effective_user.id} got a night message")
    except Exception as e:
        logger.error(f"Goodnight error: {e}")
        await update.message.reply_text("❌ Failed to send night message")

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
    app.add_handler(CommandHandler("updates", update_command))
    app.add_handler(CommandHandler("test", test_ai))
    app.add_handler(CommandHandler("ai", ai_command))
    app.add_handler(CommandHandler("ilikeu", warn))
    app.add_handler(CommandHandler("warns", check_warns))
    app.add_handler(CommandHandler("clear_warns", clear_warns))
    app.add_handler(CommandHandler("Shut", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("unshut", unmute))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("nuke", nuke))
    app.add_handler(CommandHandler("iloveu", iloveu))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("info", user_info))
    app.add_handler(CommandHandler("admins", admins))
    app.add_handler(CommandHandler("debug_warns", debug_warns))
    app.add_handler(CommandHandler("roll", roll))
    app.add_handler(CommandHandler("coin", coin))
    app.add_handler(CommandHandler("calc", calc))
    app.add_handler(CommandHandler("echo", echo))
    app.add_handler(CommandHandler("time", time_cmd))
    app.add_handler(CommandHandler("Rape", Rape))
    app.add_handler(CommandHandler("8ball", eightball))
    app.add_handler(CommandHandler("reverse", reverse))
    app.add_handler(CommandHandler("fact", fact))
    app.add_handler(CommandHandler("dream", dream))
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
    app.add_handler(CommandHandler("daddy", daddy))
    app.add_handler(CommandHandler("Waleed", waleed))
    app.add_handler(CommandHandler("kiss", kiss))
    app.add_handler(CommandHandler("speak", speak))
    app.add_handler(CommandHandler("stop_speak", stop_speak))
    app.add_handler(CommandHandler("unSpeak", unspeak))
    
    # New Fun Commands
    app.add_handler(CommandHandler("roast", roast))
    app.add_handler(CommandHandler("ship", ship))
    app.add_handler(CommandHandler("rate", rate_cmd))
    app.add_handler(CommandHandler("meme", meme))
    app.add_handler(CommandHandler("truth", truth))
    app.add_handler(CommandHandler("dare", dare))
    app.add_handler(CommandHandler("compliment", compliment))
    app.add_handler(CommandHandler("insult", insult))
    app.add_handler(CommandHandler("ascii", ascii_art))
    app.add_handler(CommandHandler("hack", hack))
    app.add_handler(CommandHandler("fancy", fancy))
    app.add_handler(CommandHandler("hotrate", hotrate))
    app.add_handler(CommandHandler("iq", iq_rate))
    app.add_handler(CommandHandler("gayrate", gayrate))
    app.add_handler(CommandHandler("sleep", sleep_cmd))
    app.add_handler(CommandHandler("goodmorning", goodmorning_cmd))
    app.add_handler(CommandHandler("goodnight", goodnight_cmd))
    
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