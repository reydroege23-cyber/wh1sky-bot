"""
💰 ECONOMY MODULE - Virtual Coin System
Manages user balances, transactions, and leaderboards

⚠️ VIRTUAL CURRENCY ONLY - Entertainment purposes ONLY

SIMPLE STRUCTURE:
- get_balance() → Get coins
- add_coins() → Give coins  
- remove_coins() → Take coins
- claim_daily() → Daily reward
"""

import logging
from datetime import datetime, timedelta
from config import (
    STARTING_BALANCE, 
    MIN_BET, 
    MAX_BET,
    DAILY_REWARD,
    DAILY_COOLDOWN,
)

logger = logging.getLogger(__name__)


class Economy:
    """
    Simple, beginner-friendly economy system.
    
    What it does:
    1. Tracks coin balance for each user
    2. Allows adding/removing coins
    3. Handles daily rewards with cooldown
    4. Shows top users (leaderboard)
    """
    
    def __init__(self, bot_data: dict):
        """Initialize with bot_data storage."""
        self.bot_data = bot_data
        self._ensure_structure()
    
    def _ensure_structure(self):
        """Create data structures if they don't exist."""
        if "economy" not in self.bot_data:
            self.bot_data["economy"] = {}
        if "daily_claims" not in self.bot_data:
            self.bot_data["daily_claims"] = {}
        if "economy_log" not in self.bot_data:
            self.bot_data["economy_log"] = []
        if "user_metadata" not in self.bot_data:
            self.bot_data["user_metadata"] = {}  # Track usernames/names for leaderboard
    
    # ========================================
    # BALANCE OPERATIONS
    # ========================================
    
    def get_balance(self, user_id: int) -> int:
        """
        Get user's coin balance.
        
        What it does:
        - Returns coins if user exists
        - Creates new user with STARTING_BALANCE if doesn't exist
        """
        user_id_str = str(user_id)
        
        # Create new user if needed
        if user_id_str not in self.bot_data["economy"]:
            self.bot_data["economy"][user_id_str] = STARTING_BALANCE
            logger.info(f"👤 New user {user_id}: {STARTING_BALANCE} coins")
        
        return self.bot_data["economy"][user_id_str]
    
    def track_user(self, user_id: int, username: str = "", first_name: str = ""):
        """
        Track user metadata for leaderboard persistence.
        
        What it does:
        - Saves username and first_name to ensure leaderboard survives restarts
        - Called whenever user interacts with economy commands
        """
        user_id_str = str(user_id)
        
        if user_id_str not in self.bot_data["user_metadata"]:
            self.bot_data["user_metadata"][user_id_str] = {}
        
        # Update metadata
        if username:
            self.bot_data["user_metadata"][user_id_str]["username"] = username
        if first_name:
            self.bot_data["user_metadata"][user_id_str]["first_name"] = first_name
        
        # Ensure user has balance entry
        if user_id_str not in self.bot_data["economy"]:
            self.bot_data["economy"][user_id_str] = STARTING_BALANCE

    
    def add_coins(self, user_id: int, amount: int, reason: str = "") -> bool:
        """
        Add coins to user.
        
        Returns: True if successful
        """
        user_id_str = str(user_id)
        
        if amount < 0:
            logger.error(f"❌ Cannot add negative coins")
            return False
        
        # Get current balance (creates user if new)
        balance = self.get_balance(user_id)
        new_balance = balance + amount
        
        # Update balance
        self.bot_data["economy"][user_id_str] = new_balance
        self._log(user_id, amount, new_balance, reason or "Added coins")
        
        return True
    
    def remove_coins(self, user_id: int, amount: int, reason: str = "") -> tuple[bool, str]:
        """
        Remove coins from user.
        
        Returns: (success, error_message)
        """
        user_id_str = str(user_id)
        
        if amount < 0:
            return False, "❌ Invalid amount"
        
        balance = self.get_balance(user_id)
        
        # Check if user has enough
        if balance < amount:
            return False, f"❌ Need {amount}, you have {balance}"
        
        new_balance = balance - amount
        self.bot_data["economy"][user_id_str] = new_balance
        self._log(user_id, -amount, new_balance, reason or "Removed coins")
        
        return True, ""
    
    def set_coins(self, user_id: int, amount: int, reason: str = "") -> bool:
        """Set exact balance (admin only)."""
        user_id_str = str(user_id)
        
        if amount < 0:
            return False
        
        self.bot_data["economy"][user_id_str] = amount
        self._log(user_id, 0, amount, reason or "Admin set balance")
        
        return True
    
    # ========================================
    # VALIDATION
    # ========================================
    
    def validate_bet(self, amount: int, user_balance: int) -> tuple[bool, str]:
        """
        Check if bet is valid.
        
        Returns: (is_valid, error_message)
        """
        
        if amount < MIN_BET:
            return False, f"❌ Minimum bet: {MIN_BET}"
        
        if amount > MAX_BET:
            return False, f"❌ Maximum bet: {MAX_BET}"
        
        if amount > user_balance:
            return False, f"❌ You only have {user_balance}"
        
        return True, ""
    
    # ========================================
    # DAILY REWARDS
    # ========================================
    
    def claim_daily(self, user_id: int) -> tuple[bool, str, int]:
        """
        Claim daily reward.
        
        Returns: (success, message, coins_gained)
        """
        user_id_str = str(user_id)
        now = datetime.now()
        
        # Check if already claimed today
        if user_id_str in self.bot_data["daily_claims"]:
            last_claim = datetime.fromisoformat(
                self.bot_data["daily_claims"][user_id_str]
            )
            next_claim = last_claim + timedelta(seconds=DAILY_COOLDOWN)
            
            # Not ready yet
            if now < next_claim:
                hours = int((next_claim - now).total_seconds() / 3600)
                mins = int(((next_claim - now).total_seconds() % 3600) / 60)
                return False, f"⏱️ Available in {hours}h {mins}m", 0
        
        # Give reward
        self.bot_data["daily_claims"][user_id_str] = now.isoformat()
        self.add_coins(user_id, DAILY_REWARD, "Daily reward")
        
        return True, f"🎁 Claimed {DAILY_REWARD} coins!", DAILY_REWARD
    
    # ========================================
    # LEADERBOARD
    # ========================================
    
    def get_top_users(self, limit: int = 10) -> list:
        """Get top users by coin balance."""
        users = []
        
        for user_id_str, balance in self.bot_data["economy"].items():
            users.append((int(user_id_str), balance))
        
        # Sort: highest coins first
        users.sort(key=lambda x: x[1], reverse=True)
        
        return users[:limit]
    
    # ========================================
    # LOGGING
    # ========================================
    
    def _log(self, user_id: int, delta: int, new_balance: int, reason: str):
        """Log transaction for debugging."""
        log_entry = {
            "time": datetime.now().isoformat(),
            "user": user_id,
            "delta": delta,
            "balance": new_balance,
            "reason": reason
        }
        self.bot_data["economy_log"].append(log_entry)
        
        # Keep only last 500 to save space
        if len(self.bot_data["economy_log"]) > 500:
            self.bot_data["economy_log"] = self.bot_data["economy_log"][-500:]
        
        logger.info(f"💰 {user_id}: {delta:+d} → {new_balance} ({reason})")
