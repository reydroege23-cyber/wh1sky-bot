"""
Admin Economy Commands for Marine
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
from config import OWNER_ID, SILENT_PERMISSION_MODE
from economy import Economy
from services.group_management import store

logger = logging.getLogger(__name__)


def _chat_id(update: Update) -> int:
    return int(update.effective_chat.id) if update.effective_chat else 0


def _actor_id(update: Update) -> int | None:
    return int(update.effective_user.id) if update.effective_user else None


def _command_text(update: Update) -> str:
    if update.message:
        return str(getattr(update.message, "text", "") or "").split(maxsplit=1)[0]
    return "unknown"


def _silent_permission_mode(update: Update) -> bool:
    try:
        return bool(store.get_setting(_chat_id(update), "silent_permission_mode", SILENT_PERMISSION_MODE))
    except Exception:
        return SILENT_PERMISSION_MODE


async def _log_unauthorized(update: Update, command: str) -> None:
    user = update.effective_user
    user_id = _actor_id(update)
    username = getattr(user, "username", None) or getattr(user, "full_name", None) or "unknown"
    reason = f"required=owner; username={username}; command={command}"
    logger.warning(
        "Unauthorized economy admin attempt user=%s username=%s chat=%s command=%s",
        user_id,
        username,
        _chat_id(update),
        command,
    )
    try:
        store.log_action(_chat_id(update), user_id, "unauthorized_command", reason=reason)
    except Exception as exc:
        logger.debug("Failed to persist unauthorized economy attempt: %s", exc)


async def _deny_if_not_owner(update: Update) -> bool:
    if _actor_id(update) == OWNER_ID:
        return False
    await _log_unauthorized(update, _command_text(update))
    if update.message and not _silent_permission_mode(update):
        await update.message.reply_text("You don't have permission to use this command.")
    return True

def owner_only(func):
    """Decorator to restrict commands to owner only."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await _deny_if_not_owner(update):
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
    if await _deny_if_not_owner(update):
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
    if await _deny_if_not_owner(update):
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
    if await _deny_if_not_owner(update):
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

# ========================================
# DATABASE CLEANUP - REMOVE FAKE USERS
# ========================================

@owner_only
async def cleanup_fake_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin command: Remove all FAKE/INVALID user IDs from database.
    
    Usage: /cleanupfake
    
    This command:
    ✔ Identifies all invalid Telegram user IDs (< 100000000, suspicious patterns, etc.)
    ✔ Removes them from database
    ✔ Logs all removed IDs
    ✔ Shows verification report
    """
    try:
        user_id = update.effective_user.id
        
        # Get list of fake users before cleanup
        fake_users = economy.get_fake_users_list()
        
        if not fake_users:
            await update.message.reply_text(
                "✅ **Database Clean!**\n\nNo fake users found. Leaderboard is healthy!",
                parse_mode="Markdown"
            )
            logger.info(f"🔍 Admin {user_id} ran cleanup check - no fake users found")
            return
        
        # Show fake users to be removed
        fake_ids_str = ", ".join(str(uid) for uid in fake_users[:10])
        if len(fake_users) > 10:
            fake_ids_str += f", ... and {len(fake_users) - 10} more"
        
        await update.message.reply_text(
            f"🗑️ **Cleaning Database...**\n\nFound {len(fake_users)} fake user(s):\n`{fake_ids_str}`\n\nRemoving...",
            parse_mode="Markdown"
        )
        
        # Perform cleanup
        result = economy.cleanup_fake_users()
        
        # Show results
        if result['removed_count'] > 0:
            removed_msg = f"✅ **Cleanup Complete!**\n\n"
            removed_msg += f"🗑️ Removed: **{result['removed_count']}** fake user(s)\n"
            removed_msg += f"📋 IDs: `{', '.join(str(uid) for uid in result['removed_ids'][:20])}`"
            
            if len(result['removed_ids']) > 20:
                removed_msg += f"\n... and {len(result['removed_ids']) - 20} more"
            
            removed_msg += "\n\n✔️ Leaderboard is now clean!"
        else:
            removed_msg = "✅ **Cleanup Complete!**\n\nNo changes needed."
        
        await update.message.reply_text(removed_msg, parse_mode="Markdown")
        logger.info(f"🗑️ Admin {user_id} cleaned database: removed {result['removed_count']} fake users")
        
    except Exception as e:
        logger.exception("Cleanup error", exc_info=True)
        await update.message.reply_text("❌ Cleanup failed. See logs for details.")

@owner_only
async def cleanup_fake_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin command: Remove all FAKE/INVALID user IDs from database.
    
    Usage: /cleanupfake
    
    This command:
    ✔ Identifies all invalid Telegram user IDs (< 100000000, suspicious patterns, etc.)
    ✔ Removes them from database
    ✔ Logs all removed IDs
    ✔ Shows verification report
    """
    try:
        user_id = update.effective_user.id
        
        # Get list of fake users before cleanup
        fake_users = economy.get_fake_users_list()
        
        if not fake_users:
            await update.message.reply_text(
                "✅ **Database Clean!**\n\nNo fake users found. Leaderboard is healthy!",
                parse_mode="Markdown"
            )
            logger.info(f"🔍 Admin {user_id} ran cleanup check - no fake users found")
            return
        
        # Show fake users to be removed
        fake_ids_str = ", ".join(str(uid) for uid in fake_users[:10])
        if len(fake_users) > 10:
            fake_ids_str += f", ... and {len(fake_users) - 10} more"
        
        await update.message.reply_text(
            f"🗑️ **Cleaning Database...**\n\nFound {len(fake_users)} fake user(s):\n`{fake_ids_str}`\n\nRemoving...",
            parse_mode="Markdown"
        )
        
        # Perform cleanup
        result = economy.cleanup_fake_users()
        
        # Show results
        if result['removed_count'] > 0:
            removed_msg = f"✅ **Cleanup Complete!**\n\n"
            removed_msg += f"🗑️ Removed: **{result['removed_count']}** fake user(s)\n"
            removed_msg += f"📋 IDs: `{', '.join(str(uid) for uid in result['removed_ids'][:20])}`"
            
            if len(result['removed_ids']) > 20:
                removed_msg += f"\n... and {len(result['removed_ids']) - 20} more"
            
            removed_msg += "\n\n✔️ Leaderboard is now clean!"
        else:
            removed_msg = "✅ **Cleanup Complete!**\n\nNo changes needed."
        
        await update.message.reply_text(removed_msg, parse_mode="Markdown")
        logger.info(f"🗑️ Admin {user_id} cleaned database: removed {result['removed_count']} fake users")
        
    except Exception as e:
        logger.exception("Cleanup error", exc_info=True)
        await update.message.reply_text("❌ Cleanup failed. See logs for details.")

@owner_only
async def check_fake_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin command: Check for fake users WITHOUT deleting.
    
    Usage: /checkfake
    
    Shows list of invalid user IDs that would be removed.
    """
    try:
        user_id = update.effective_user.id
        
        # Get list of fake users
        fake_users = economy.get_fake_users_list()
        
        if not fake_users:
            await update.message.reply_text(
                "✅ **All Clear!**\n\nNo fake users detected in database.",
                parse_mode="Markdown"
            )
            logger.info(f"🔍 Admin {user_id} checked for fake users - none found")
            return
        
        # Show fake users
        check_msg = f"⚠️ **Fake Users Detected:** {len(fake_users)}\n\n"
        
        # Show first 20
        for uid in fake_users[:20]:
            check_msg += f"  ❌ {uid}\n"
        
        if len(fake_users) > 20:
            check_msg += f"\n  ... and {len(fake_users) - 20} more\n"
        
        check_msg += f"\n💡 **Run `/cleanupfake` to remove them.**"
        
        await update.message.reply_text(check_msg, parse_mode="Markdown")
        logger.info(f"🔍 Admin {user_id} checked database: found {len(fake_users)} fake users")
        
    except Exception as e:
        logger.exception("Check fake users error", exc_info=True)
        await update.message.reply_text("❌ Check failed. See logs for details.")
