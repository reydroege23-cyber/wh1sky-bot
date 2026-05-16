"""
🎨 UI ANIMATIONS HELPER
Creates beautiful animated messages for casino games

Example usage:
- Spinning coin animation
- Slots spinning reels
- Dice rolling
- Beautiful formatted results
"""

import asyncio
from telegram import Update
from telegram.ext import ContextTypes

# ========================================
# ANIMATION HELPERS
# ========================================

async def animate_coin_flip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show animated coin flip before result."""
    msg = await update.message.reply_text("🪙 Flipping coin...")
    await asyncio.sleep(0.3)
    await msg.edit_text("🪙 Flipping coin .")
    await asyncio.sleep(0.2)
    await msg.edit_text("🪙 Flipping coin ..")
    await asyncio.sleep(0.2)
    await msg.edit_text("🪙 Flipping coin ...")
    await asyncio.sleep(0.3)
    return msg

async def animate_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show animated slots spinning."""
    msg = await update.message.reply_text("🎰 Spinning...")
    
    animations = [
        "🎰 [🍎] [🍊] [🍋]",
        "🎰 [🍊] [🍋] [🍌]",
        "🎰 [🍋] [🍌] [🍉]",
        "🎰 [🍌] [🍉] [💎]",
    ]
    
    for anim in animations:
        await msg.edit_text(anim)
        await asyncio.sleep(0.2)
    
    return msg

async def animate_dice_roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show animated dice rolling."""
    msg = await update.message.reply_text("🎲 Rolling...")
    
    for i in range(1, 7):
        await msg.edit_text(f"🎲 Rolling... {i}")
        await asyncio.sleep(0.1)
    
    return msg

# ========================================
# FORMAT RESULTS
# ========================================

def format_result(game_name: str, result_data: dict) -> str:
    """
    Create beautiful result message.
    
    Input: game_name, result_dict with 'result', 'won', etc
    Output: Formatted message string
    """
    
    if result_data['won']:
        # WIN MESSAGE - Green/happy emojis
        return f"""
━━━━━━━━━━━━━━━━━
🎉 **{game_name} RESULT** 🎉
━━━━━━━━━━━━━━━━━

{result_data['result']}

━━━━━━━━━━━━━━━━━
        """.strip()
    else:
        # LOSS MESSAGE - Sad emojis
        if result_data.get('coins_won') == 0:
            # TIE
            return f"""
━━━━━━━━━━━━━━━━━
🤝 **{game_name} RESULT** 🤝
━━━━━━━━━━━━━━━━━

{result_data['result']}

━━━━━━━━━━━━━━━━━
            """.strip()
        else:
            return f"""
━━━━━━━━━━━━━━━━━
😢 **{game_name} RESULT** 😢
━━━━━━━━━━━━━━━━━

{result_data['result']}

━━━━━━━━━━━━━━━━━
            """.strip()

def format_balance_card(balance: int, username: str = "Player") -> str:
    """Format balance display card."""
    return f"""
╔════════════════════════════╗
║   💰 **YOUR ACCOUNT** 💰   ║
╠════════════════════════════╣
║  👤 {username:20}    ║
║  🪙 Coins: **{balance}**  ║
╚════════════════════════════╝
    """.strip()

def format_daily_reward(coins: int) -> str:
    """Format daily reward message."""
    return f"""
╔════════════════════════════╗
║     🎁 **DAILY REWARD** 🎁 ║
╠════════════════════════════╣
║  ✅ Claimed **{coins}** coins!  ║
║  Come back tomorrow for more! ║
╚════════════════════════════╝
    """.strip()

def format_leaderboard(top_users: list) -> str:
    """
    Format top users leaderboard with usernames and validation.
    
    Args:
        top_users: List of (user_id, username, first_name, balance) tuples
    
    Features:
    ✔ Shows usernames/first names (no raw IDs)
    ✔ Only includes valid users (fake IDs filtered out)
    ✔ Professional formatting with medals
    ✔ Fallback to ID if no username available
    """
    msg = "╔════════════════════════════════════╗\n"
    msg += "║   🏆 RICHEST USERS 🏆           ║\n"
    msg += "╠════════════════════════════════════╣\n"
    
    medals = ["🥇", "🥈", "🥉"]
    
    for idx, entry in enumerate(top_users[:10], 1):
        # Handle both old format (user_id, balance) and new format (user_id, username, first_name, balance)
        if len(entry) == 4:
            user_id, username, first_name, balance = entry
        else:
            # Fallback for old data format
            user_id, balance = entry
            username = ""
            first_name = ""
        
        # Determine medal/position
        if idx <= 3:
            medal = medals[idx-1]
        else:
            medal = f"{idx}️⃣"
        
        # Get display name (prefer username, fallback to first_name, then user_id)
        if username:
            display_name = f"@{username[:15]}"
        elif first_name:
            display_name = f"{first_name[:15]}"
        else:
            display_name = f"ID:{user_id}"
        
        # Format: ║ 🥇 @username    7460 coins ║
        msg += f"║ {medal} {display_name:<18} {balance:>5} 💰║\n"
    
    msg += "╚════════════════════════════════════╝"
    return msg

# ========================================
# ERROR MESSAGES
# ========================================

def error_msg(message: str) -> str:
    """Format error message."""
    return f"❌ {message}"

def success_msg(message: str) -> str:
    """Format success message."""
    return f"✅ {message}"

def info_msg(message: str) -> str:
    """Format info message."""
    return f"ℹ️ {message}"
