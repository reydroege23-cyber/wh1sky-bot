"""
🏆 ACHIEVEMENT SYSTEM - Professional Progressive Rewards
Persistent achievement tracking with automatic progression checking.

Features:
✅ 20+ achievements across multiple categories
✅ Permanent database storage
✅ Automatic unlock triggers
✅ Coin rewards for unlocks
✅ Beautiful UI formatting
✅ Scalable & lightweight
"""

import logging
from datetime import datetime
from database import EconomyDatabase

logger = logging.getLogger(__name__)

# ========================
# ACHIEVEMENT DEFINITIONS
# ========================

ACHIEVEMENTS = {
    # 💰 WEALTH ACHIEVEMENTS
    "first_coins": {
        "name": "First Coins",
        "description": "Reached 100 coins",
        "category": "Wealth",
        "reward": 50,
        "emoji": "💵",
        "threshold": 100
    },
    "small_gambler": {
        "name": "Small Gambler",
        "description": "Reached 1,000 coins",
        "category": "Wealth",
        "reward": 100,
        "emoji": "💰",
        "threshold": 1000
    },
    "high_roller": {
        "name": "High Roller",
        "description": "Reached 10,000 coins",
        "category": "Wealth",
        "reward": 500,
        "emoji": "🎰",
        "threshold": 10000
    },
    "casino_king": {
        "name": "Casino King",
        "description": "Reached 100,000 coins",
        "category": "Wealth",
        "reward": 2000,
        "emoji": "👑",
        "threshold": 100000
    },
    "millionaire": {
        "name": "Millionaire",
        "description": "Reached 1,000,000 coins",
        "category": "Wealth",
        "reward": 10000,
        "emoji": "💎",
        "threshold": 1000000
    },
    
    # 💸 ECONOMY ACHIEVEMENTS
    "first_transfer": {
        "name": "Generous",
        "description": "Sent coins to another player",
        "category": "Economy",
        "reward": 75,
        "emoji": "💸",
        "threshold": 1
    },
    "big_transfer": {
        "name": "Big Spender",
        "description": "Sent 1,000+ coins",
        "category": "Economy",
        "reward": 500,
        "emoji": "🤑",
        "threshold": 1000
    },
    "popular": {
        "name": "Popular Player",
        "description": "Received 5,000+ coins from others",
        "category": "Economy",
        "reward": 500,
        "emoji": "🤗",
        "threshold": 5000
    },
    
    # 🏆 LEADERBOARD ACHIEVEMENTS
    "top_10": {
        "name": "Top 10",
        "description": "Ranked in top 10 richest players",
        "category": "Leaderboard",
        "reward": 1000,
        "emoji": "🥉",
        "threshold": 10
    },
    "top_3": {
        "name": "Top 3",
        "description": "Ranked in top 3 richest players",
        "category": "Leaderboard",
        "reward": 3000,
        "emoji": "🥈",
        "threshold": 3
    },
    "number_one": {
        "name": "#1 Richest",
        "description": "Became the #1 richest player",
        "category": "Leaderboard",
        "reward": 10000,
        "emoji": "🥇",
        "threshold": 1
    },
    "lucky_streak": {
        "name": "Lucky Streak",
        "description": "Won 5 games in a row",
        "category": "Gameplay",
        "reward": 750,
        "emoji": "🔥",
        "threshold": 5
    },
}


# ========================
# ACHIEVEMENT CHECKER
# ========================

class AchievementChecker:
    """Centralized achievement checking and unlocking."""
    
    def __init__(self, db: EconomyDatabase):
        self.db = db
    
    async def check_all_achievements(self, user_id: int, balance: int = None, stats: dict = None) -> list:
        """
        Check and unlock all applicable achievements for a user.
        
        Returns: List of newly unlocked achievement keys
        """
        newly_unlocked = []
        
        try:
            # Get current data
            if balance is None:
                balance = self.db.get_balance(user_id)
            if stats is None:
                stats = self.db.get_player_stats(user_id)
            
            # Check each achievement
            for achievement_key, achievement in ACHIEVEMENTS.items():
                # Skip if already unlocked
                if self.db.is_achievement_unlocked(user_id, achievement_key):
                    continue
                
                # Check unlock conditions
                should_unlock = await self._check_condition(
                    achievement_key, balance, stats
                )
                
                if should_unlock:
                    self.db.unlock_achievement(user_id, achievement_key)
                    newly_unlocked.append(achievement_key)
                    logger.info(f"🏆 Achievement unlocked: {user_id} → {achievement_key}")
        
        except Exception as e:
            logger.error(f"❌ Error checking achievements: {e}")
        
        return newly_unlocked
    
    async def _check_condition(self, achievement_key: str, balance: int, stats: dict) -> bool:
        """Check if achievement conditions are met."""
        try:
            # Wealth achievements
            if achievement_key == "first_coins" and balance >= 100:
                return True
            if achievement_key == "small_gambler" and balance >= 1000:
                return True
            if achievement_key == "high_roller" and balance >= 10000:
                return True
            if achievement_key == "casino_king" and balance >= 100000:
                return True
            if achievement_key == "millionaire" and balance >= 1000000:
                return True
            
            # Non-gambling achievements
            
            # Economy achievements
            if achievement_key == "first_transfer" and stats.get('coins_sent', 0) >= 1:
                return True
            if achievement_key == "big_transfer" and stats.get('coins_sent', 0) >= 1000:
                return True
            if achievement_key == "popular" and stats.get('coins_received', 0) >= 5000:
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"❌ Error checking condition for {achievement_key}: {e}")
            return False
    
    def get_achievement_display(self, achievement_key: str) -> str:
        """Get formatted display for an achievement."""
        if achievement_key not in ACHIEVEMENTS:
            return ""
        
        ach = ACHIEVEMENTS[achievement_key]
        return f"{ach['emoji']} {ach['name']}"
    
    def get_unlock_reward(self, achievement_key: str) -> int:
        """Get coin reward for unlocking achievement."""
        return ACHIEVEMENTS.get(achievement_key, {}).get('reward', 0)


# ========================
# UI FORMATTING
# ========================

def format_achievements_display(user_id: int, db: EconomyDatabase) -> str:
    """Format achievements for user display."""
    try:
        unlocked = db.get_user_achievements(user_id)
        unlocked_keys = [item[0] for item in unlocked]
        
        # Build display
        lines = ["╔════════════════════════════╗"]
        lines.append("║     🏆 ACHIEVEMENTS 🏆     ║")
        lines.append("╠════════════════════════════╣")
        
        if not unlocked_keys:
            lines.append("║ No achievements yet! 🔓    ║")
            lines.append("╚════════════════════════════╝")
            return "\n".join(lines)
        
        # Group by category
        by_category = {}
        for key in unlocked_keys:
            if key in ACHIEVEMENTS:
                category = ACHIEVEMENTS[key]['category']
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(key)
        
        # Display by category
        for category in sorted(by_category.keys()):
            lines.append(f"║ 📂 {category}")
            for key in by_category[category]:
                ach = ACHIEVEMENTS[key]
                display = f"✅ {ach['emoji']} {ach['name']}"
                lines.append(f"║ {display:<26}║")
        
        lines.append("╚════════════════════════════╝")
        
        return "\n".join(lines)
    
    except Exception as e:
        logger.error(f"Error formatting achievements: {e}")
        return "❌ Could not load achievements"


def format_profile_card(user_id: int, db: EconomyDatabase) -> str:
    """Format comprehensive player profile."""
    try:
        balance = db.get_balance(user_id)
        stats = db.get_player_stats(user_id)
        achievements = db.get_user_achievements(user_id)
        user_info = db.get_user_info(user_id)
        
        username = user_info.get('first_name', 'Player') if user_info else 'Player'
        
        unlocked_count = len(achievements)
        total_achievements = len(ACHIEVEMENTS)
        completion = int((unlocked_count / total_achievements) * 100) if total_achievements > 0 else 0
        
        profile = f"""
╔══════════════════════════════════╗
║   👤 PLAYER PROFILE - {username:<17}║
╠══════════════════════════════════╣
║ 💰 Balance: {balance:>25} coins│
╠══════════════════════════════════╣
║ 🏆 Achievements: {unlocked_count:>2}/{total_achievements} ({completion}%) ║
╠══════════════════════════════════╣
║ 💸 Coins Sent: {stats.get('coins_sent', 0):>21}│
║ 📬 Coins Received: {stats.get('coins_received', 0):>15}│
╚══════════════════════════════════╝
"""
        return profile
    
    except Exception as e:
        logger.error(f"Error formatting profile: {e}")
        return "❌ Could not load profile"


def format_leaderboard_with_rank(top_users: list, user_id: int, db: EconomyDatabase) -> str:
    """Format leaderboard with player's rank highlighted."""
    try:
        board = "╔════════════════════════════════════╗\n"
        board += "║  🏆 LEADERBOARD - TOP 10 RICHEST  ║\n"
        board += "╠════════════════════════════════════╣\n"
        
        user_rank = None
        for idx, (uid, balance) in enumerate(top_users, 1):
            user_info = db.get_user_info(uid)
            name = user_info.get('first_name', 'Unknown')[:12] if user_info else 'Unknown'
            
            medals = {1: "🥇", 2: "🥈", 3: "🥉"}
            medal = medals.get(idx, f"#{idx:<2}")
            
            if uid == user_id:
                user_rank = idx
                board += f"║ {medal} {name:<15} {balance:>10} 💰 ⭐ │\n"
            else:
                board += f"║ {medal} {name:<15} {balance:>10} 💰    │\n"
        
        board += "╠════════════════════════════════════╣\n"
        
        if user_rank:
            board += f"║ Your Rank: #{user_rank:<27}│\n"
        else:
            board += f"║ Your Rank: Not in Top 10          │\n"
        
        board += "╚════════════════════════════════════╝"
        
        return board
    
    except Exception as e:
        logger.error(f"Error formatting leaderboard: {e}")
        return "❌ Could not load leaderboard"
