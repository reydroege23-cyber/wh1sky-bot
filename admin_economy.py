"""
Admin Economy Commands for Whisky_bot
Admin commands for managing virtual coins
Only OWNER_ID has access to these commands
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from functools import wraps
from config import OWNER_ID
from economy import Economy

logger = logging.getLogger(__name__)

def owner_only(func):
    """Decorator to restrict commands to owner only."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if user_id != OWNER_ID:
            logger.warning(f"🚫 Unauthorized economy admin access by {user_id}")
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        return await func(update, context)
    return wrapper

async def addcoins(update: Update, context: ContextTypes.DEFAULT_TYPE, economy: Economy):
    """Add coins to a user. Admin only."""
    user = update.effective_user
    
    # Check authorization
    if user.id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        logger.warning(f"🚫 Unauthorized /addcoins attempt by {user.id}")
        return
    
    # Parse arguments
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/addcoins @username_or_id amount`\n"
            "Example: `/addcoins @john 100`",
            parse_mode="Markdown"
        )
        return
    
    # Get target user
    target_str = context.args[0]
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number")
        return
    
    # Try to get user ID from reply or mention
    target_id = None
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif target_str.startswith("@"):
        # Username mention - would need bot to have access to user info
        await update.message.reply_text("❌ Please reply to the user's message or use their ID directly")
        return
    else:
        try:
            target_id = int(target_str)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID or mention")
            return
    
    if amount < 0:
        await update.message.reply_text("❌ Amount must be positive")
        return
    
    # Add coins
    success, msg = economy.add_coins(target_id, amount, f"Added by admin {user.id}")
    await update.message.reply_text(msg, parse_mode="Markdown")
    logger.info(f"💰 Admin {user.id} added {amount} coins to {target_id}")

async def removecoins(update: Update, context: ContextTypes.DEFAULT_TYPE, economy: Economy):
    """Remove coins from a user. Admin only."""
    user = update.effective_user
    
    # Check authorization
    if user.id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        logger.warning(f"🚫 Unauthorized /removecoins attempt by {user.id}")
        return
    
    # Parse arguments
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/removecoins @username_or_id amount`\n"
            "Example: `/removecoins @john 50`",
            parse_mode="Markdown"
        )
        return
    
    # Get target user
    target_str = context.args[0]
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number")
        return
    
    # Try to get user ID from reply or mention
    target_id = None
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif target_str.startswith("@"):
        await update.message.reply_text("❌ Please reply to the user's message or use their ID directly")
        return
    else:
        try:
            target_id = int(target_str)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID or mention")
            return
    
    if amount < 0:
        await update.message.reply_text("❌ Amount must be positive")
        return
    
    # Remove coins
    success, msg = economy.remove_coins(target_id, amount, f"Removed by admin {user.id}")
    await update.message.reply_text(msg, parse_mode="Markdown")
    logger.info(f"💰 Admin {user.id} removed {amount} coins from {target_id}")

async def setcoins(update: Update, context: ContextTypes.DEFAULT_TYPE, economy: Economy):
    """Set a user's coin balance to exact amount. Admin only."""
    user = update.effective_user
    
    # Check authorization
    if user.id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        logger.warning(f"🚫 Unauthorized /setcoins attempt by {user.id}")
        return
    
    # Parse arguments
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/setcoins @username_or_id amount`\n"
            "Example: `/setcoins @john 500`",
            parse_mode="Markdown"
        )
        return
    
    # Get target user
    target_str = context.args[0]
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number")
        return
    
    # Try to get user ID from reply or mention
    target_id = None
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif target_str.startswith("@"):
        await update.message.reply_text("❌ Please reply to the user's message or use their ID directly")
        return
    else:
        try:
            target_id = int(target_str)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID or mention")
            return
    
    if amount < 0:
        await update.message.reply_text("❌ Amount must be non-negative")
        return
    
    # Set coins
    success, msg = economy.set_coins(target_id, amount, f"Set by admin {user.id}")
    await update.message.reply_text(msg, parse_mode="Markdown")
    logger.info(f"💰 Admin {user.id} set {target_id} balance to {amount} coins")
