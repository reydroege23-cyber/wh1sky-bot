"""
Admin Economy Commands for Whisky_bot
Admin commands for managing virtual coins
Only OWNER_ID has access to these commands

Supported command formats:
1. Reply method (most reliable):
   - Reply to a user's message with: /setcoins 500
   
2. Direct user ID:
   - /setcoins 123456789 500
   
3. Username (if available):
   - /setcoins @username 500
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

async def _resolve_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple:
    """
    Resolve target user ID from message.
    
    Returns: (target_user_id, error_message)
    - If successful: (user_id, None)
    - If error: (None, error_message)
    
    Supports:
    1. Reply to a message (most reliable)
    2. Direct user ID: /command 123456789 amount
    3. Username: /command @username amount
    """
    
    # Method 1: Check if replying to a message
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        logger.info(f"✅ Resolved user from reply: {target_id}")
        return (target_id, None)
    
    # Method 2/3: Use context.args to find user
    if not context.args or len(context.args) < 1:
        return (None, "❌ Usage:\n1. Reply to user + `/command amount`\n2. `/command <user_id> <amount>`")
    
    target_str = context.args[0]
    
    # Try direct user ID
    if target_str.isdigit():
        target_id = int(target_str)
        logger.info(f"✅ Resolved user from ID: {target_id}")
        return (target_id, None)
    
    # Try username
    if target_str.startswith("@"):
        username = target_str[1:]  # Remove @
        logger.info(f"⚠️  Username provided: @{username} (direct ID lookup preferred)")
        
        # Try to get user from chat member
        try:
            member = await context.bot.get_chat_member(update.effective_chat.id, f"@{username}")
            target_id = member.user.id
            logger.info(f"✅ Resolved @{username} to user ID: {target_id}")
            return (target_id, None)
        except Exception as e:
            logger.warning(f"⚠️  Could not resolve @{username}: {e}")
            return (None, f"❌ Could not find user @{username}. Try replying to their message instead.")
    
    # Invalid format
    return (None, "❌ Invalid user format. Use:\n1. Reply to user\n2. User ID (number)\n3. @username")

async def addcoins(update: Update, context: ContextTypes.DEFAULT_TYPE, economy: Economy):
    """Add coins to a user. Admin only."""
    user = update.effective_user
    
    # Check authorization
    if user.id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        logger.warning(f"🚫 Unauthorized /addcoins attempt by {user.id}")
        return
    
    # Resolve target user
    target_id, error = await _resolve_target_user(update, context)
    if error:
        await update.message.reply_text(error)
        return
    
    # Get amount argument
    if update.message.reply_to_message:
        # Reply method: /addcoins 500
        if not context.args or len(context.args) < 1:
            await update.message.reply_text("❌ Usage: Reply to user + `/addcoins <amount>`")
            return
        try:
            amount = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Amount must be a number")
            return
    else:
        # Direct method: /addcoins 123456789 500
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("❌ Usage: `/addcoins <user_id> <amount>`")
            return
        try:
            amount = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Amount must be a number")
            return
    
    if amount < 0:
        await update.message.reply_text("❌ Amount must be positive")
        return
    
    # Ensure user exists in economy
    economy.get_balance(target_id)  # This auto-creates user if needed
    
    # Add coins
    success = economy.add_coins(target_id, amount, f"Added by admin {user.id}")
    new_balance = economy.get_balance(target_id)
    
    result_msg = f"✅ Added **{amount}** coins to user **{target_id}**\n💰 New balance: **{new_balance}**"
    await update.message.reply_text(result_msg, parse_mode="Markdown")
    logger.info(f"💰 Admin {user.id} added {amount} coins to {target_id}. New balance: {new_balance}")

async def removecoins(update: Update, context: ContextTypes.DEFAULT_TYPE, economy: Economy):
    """Remove coins from a user. Admin only."""
    user = update.effective_user
    
    # Check authorization
    if user.id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        logger.warning(f"🚫 Unauthorized /removecoins attempt by {user.id}")
        return
    
    # Resolve target user
    target_id, error = await _resolve_target_user(update, context)
    if error:
        await update.message.reply_text(error)
        return
    
    # Get amount argument
    if update.message.reply_to_message:
        # Reply method: /removecoins 500
        if not context.args or len(context.args) < 1:
            await update.message.reply_text("❌ Usage: Reply to user + `/removecoins <amount>`")
            return
        try:
            amount = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Amount must be a number")
            return
    else:
        # Direct method: /removecoins 123456789 500
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("❌ Usage: `/removecoins <user_id> <amount>`")
            return
        try:
            amount = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Amount must be a number")
            return
    
    if amount < 0:
        await update.message.reply_text("❌ Amount must be positive")
        return
    
    # Ensure user exists in economy
    current_balance = economy.get_balance(target_id)
    
    if current_balance < amount:
        await update.message.reply_text(f"❌ User only has **{current_balance}** coins!\nCannot remove **{amount}**", parse_mode="Markdown")
        return
    
    # Remove coins
    success, msg = economy.remove_coins(target_id, amount, f"Removed by admin {user.id}")
    new_balance = economy.get_balance(target_id)
    
    result_msg = f"✅ Removed **{amount}** coins from user **{target_id}**\n💰 New balance: **{new_balance}**"
    await update.message.reply_text(result_msg, parse_mode="Markdown")
    logger.info(f"💰 Admin {user.id} removed {amount} coins from {target_id}. New balance: {new_balance}")

async def setcoins(update: Update, context: ContextTypes.DEFAULT_TYPE, economy: Economy):
    """Set a user's coin balance to exact amount. Admin only."""
    user = update.effective_user
    
    # Check authorization
    if user.id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        logger.warning(f"🚫 Unauthorized /setcoins attempt by {user.id}")
        return
    
    # Resolve target user
    target_id, error = await _resolve_target_user(update, context)
    if error:
        await update.message.reply_text(error)
        return
    
    # Get amount argument
    if update.message.reply_to_message:
        # Reply method: /setcoins 500
        if not context.args or len(context.args) < 1:
            await update.message.reply_text("❌ Usage: Reply to user + `/setcoins <amount>`")
            return
        try:
            amount = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Amount must be a number")
            return
    else:
        # Direct method: /setcoins 123456789 500
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("❌ Usage: `/setcoins <user_id> <amount>`")
            return
        try:
            amount = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Amount must be a number")
            return
    
    if amount < 0:
        await update.message.reply_text("❌ Amount must be non-negative")
        return
    
    # Ensure user exists in economy (auto-create if needed)
    old_balance = economy.get_balance(target_id)
    
    # Set coins
    success = economy.set_balance(target_id, amount, f"Set by admin {user.id}")
    new_balance = economy.get_balance(target_id)
    
    result_msg = f"✅ Set user **{target_id}** balance to **{amount}** coins\n💰 Previous: **{old_balance}** → New: **{new_balance}**"
    await update.message.reply_text(result_msg, parse_mode="Markdown")
    logger.info(f"💰 Admin {user.id} set {target_id} balance from {old_balance} to {amount} coins")
