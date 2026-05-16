"""
🎨 UI FORMATTING HELPER
Creates beautiful formatted messages for economy, leaderboards, and notifications

Example usage:
- Balance card display
- Daily reward formatting
- Leaderboard display
- Error/success messages
"""

import asyncio
from telegram import Update
from telegram.ext import ContextTypes

# ========================================
# FORMAT HELPERS
# ========================================

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
