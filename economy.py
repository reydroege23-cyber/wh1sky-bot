"""
💰 ECONOMY MODULE - Persistent Virtual Coin System
Manages user balances, transactions, and leaderboards

Uses SQLite database for production-ready persistence:
✔ Survives bot restarts
✔ Survives crashes
✔ Survives redeployments
✔ Real-time leaderboard

⚠️ VIRTUAL CURRENCY ONLY - Entertainment purposes ONLY
"""

import logging
from datetime import datetime, timedelta
from typing import List
from config import (
    STARTING_BALANCE, 
    MIN_BET, 
    MAX_BET,
    DAILY_REWARD,
    DAILY_COOLDOWN,
)
from database import EconomyDatabase

logger = logging.getLogger(__name__)


class Economy:
    """
    Production-ready economy system using SQLite persistence.
    
    What it does:
    1. Tracks coin balance for each user (in database, not RAM)
    2. Allows adding/removing coins (atomic operations)
    3. Handles daily rewards with cooldown
    4. Shows top users (real-time leaderboard)
    5. SURVIVES bot restarts, crashes, and redeployments
    """
    
    def __init__(self, bot_data: dict = None):
        """
        Initialize with database connection.
        bot_data is kept for legacy support (warnings, stats, etc)
        but economy data uses SQLite.
        """
        self.bot_data = bot_data or {}
        self.db = EconomyDatabase("economy.db")  # Persistent database
        self._ensure_legacy_structure()
    
    def _ensure_legacy_structure(self):
        """Initialize legacy bot_data structure (warnings, stats, etc)."""
        # Daily claims are now persisted in database, not in-memory JSON
        pass
    
    # ========================================
    # BALANCE OPERATIONS (DATABASE-BACKED)
    # ========================================
    
    def get_balance(self, user_id: int) -> int:
        """
        Get user's coin balance from database.
        
        What it does:
        - Reads from persistent SQLite database
        - Auto-creates user if doesn't exist
        - Returns balance (never loses data)
        """
        return self.db.get_balance(user_id, STARTING_BALANCE)
    
    def add_coins(self, user_id: int, amount: int, reason: str = "") -> bool:
        """
        Add coins to user (atomic operation).
        
        Args:
            user_id: User's Telegram ID
            amount: Coins to add
            reason: Log reason (e.g., "Roulette win", "Daily reward")
        
        Returns: True if successful
        """
        if amount <= 0:
            logger.warning(f"⚠️ Attempted to add {amount} coins to {user_id}")
            return False
        
        success = self.db.add_balance(user_id, amount)
        if success:
            logger.info(f"✅ Added {amount} coins to {user_id}: {reason}")
        else:
            logger.error(f"❌ Failed to add {amount} coins to {user_id}")
        return success
    
    def remove_coins(self, user_id: int, amount: int, reason: str = "") -> bool:
        """
        Remove coins from user (atomic operation).
        
        Args:
            user_id: User's Telegram ID
            amount: Coins to remove
            reason: Log reason (e.g., "Roulette bet", "Coinflip loss")
        
        Returns: True if successful
        """
        if amount <= 0:
            logger.warning(f"⚠️ Attempted to remove {amount} coins from {user_id}")
            return False
        
        current = self.get_balance(user_id)
        if current < amount:
            logger.warning(f"⚠️ Insufficient balance: {user_id} has {current}, tried to remove {amount}")
            return False
        
        success = self.db.subtract_balance(user_id, amount)
        if success:
            logger.info(f"✅ Removed {amount} coins from {user_id}: {reason}")
        else:
            logger.error(f"❌ Failed to remove {amount} coins from {user_id}")
        return success
    
    def set_balance(self, user_id: int, balance: int, reason: str = "") -> bool:
        """
        Set user's balance to exact amount (admin operation).
        
        Returns: True if successful
        """
        success = self.db.set_balance(user_id, balance)
        if success:
            logger.info(f"✅ Set {user_id} balance to {balance}: {reason}")
        else:
            logger.error(f"❌ Failed to set {user_id} balance")
        return success
    
    # ========================================
    # USER TRACKING (PERSISTENT)
    # ========================================
    
    def track_user(self, user_id: int, username: str = "", first_name: str = "") -> bool:
        """
        Register user and update info (auto-called on all commands).
        
        Ensures user exists in database with up-to-date info.
        """
        return self.db.update_user_info(user_id, username, first_name)
    
    # ========================================
    # WIN/LOSS TRACKING (PERSISTENT)
    # ========================================
    
    def record_win(self, user_id: int, bet_amount: int, winnings: int, game_name: str = "") -> bool:
        """
        Record a game win (atomic operation).
        
        Args:
            user_id: User's Telegram ID
            bet_amount: Amount wagered
            winnings: Amount won (coins gained)
            game_name: Game type (e.g., "Coinflip", "Slots")
        
        Returns: True if successful
        """
        success = self.db.increment_wins(user_id)
        if success:
            logger.info(f"🎉 {game_name} WIN for {user_id}: wagered {bet_amount}, won {winnings} coins")
        return success
    
    def record_loss(self, user_id: int, bet_amount: int, game_name: str = "") -> bool:
        """
        Record a game loss (atomic operation).
        
        Args:
            user_id: User's Telegram ID
            bet_amount: Amount wagered
            game_name: Game type (e.g., "Coinflip", "Slots")
        
        Returns: True if successful
        """
        success = self.db.increment_losses(user_id)
        if success:
            logger.info(f"😢 {game_name} LOSS for {user_id}: lost {bet_amount} coins")
        return success
    
    # ========================================
    # BETTING VALIDATION
    # ========================================
    
    def validate_bet(self, bet_amount: int, current_balance: int) -> tuple:
        """
        Validate bet is within limits.
        
        Returns: (is_valid: bool, message: str)
        """
        if bet_amount < MIN_BET:
            return False, f"❌ Minimum bet: **{MIN_BET}** coins"
        
        if bet_amount > MAX_BET:
            return False, f"❌ Maximum bet: **{MAX_BET}** coins"
        
        if bet_amount > current_balance:
            return False, f"❌ Insufficient balance! You have **{current_balance}** coins"
        
        return True, "✅ Bet valid"
    
    # ========================================
    # DAILY REWARDS (PERSISTENT COOLDOWN)
    # ========================================
    
    def claim_daily(self, user_id: int) -> dict:
        """
        Claim daily reward with persistent cooldown check (stored in database).
        
        Returns: {
            'success': bool,
            'message': str,
            'coins_gained': int,
            'next_claim': timestamp
        }
        """
        now = datetime.now()
        
        # Get last claim from DATABASE (persistent across restarts)
        last_claim_time = self.db.get_last_daily_claim(user_id)
        
        if last_claim_time:
            time_since_claim = now - last_claim_time
            cooldown_duration = timedelta(hours=DAILY_COOLDOWN)
            
            if time_since_claim < cooldown_duration:
                hours_left = int((cooldown_duration - time_since_claim).total_seconds() // 3600) + 1
                next_claim_time = (last_claim_time + cooldown_duration).isoformat()
                
                return {
                    'success': False,
                    'message': f"⏱️ Come back in {hours_left}h for your next daily reward",
                    'coins_gained': 0,
                    'next_claim': next_claim_time
                }
        
        # Give reward and persist timestamp to DB (survives bot restarts)
        self.add_coins(user_id, DAILY_REWARD, "Daily reward")
        self.db.set_daily_claim(user_id)  # Persist to database
        
        next_claim = (now + timedelta(hours=DAILY_COOLDOWN)).isoformat()
        
        return {
            'success': True,
            'message': f"🎁 You claimed **{DAILY_REWARD}** coins!",
            'coins_gained': DAILY_REWARD,
            'next_claim': next_claim
        }
    
    # ========================================
    # LEADERBOARD (REAL-TIME FROM DATABASE)
    # ========================================
    
    def get_top_users(self, limit: int = 10) -> list:
        """
        Get top users by balance (real-time from database).
        
        Returns: [(user_id, balance), ...]
        Always queries fresh data - never uses cache.
        """
        return self.db.get_top_users(limit)
    
    def get_user_count(self) -> int:
        """Get total number of users with balances."""
        return self.db.get_user_count()
    
    # ========================================
    # PLAYER-TO-PLAYER TRANSFERS (ATOMIC)
    # ========================================
    
    def transfer_coins(self, sender_id: int, receiver_id: int, amount: int) -> tuple:
        """
        Transfer coins from sender to receiver (atomic, persistent).
        
        Returns: (success: bool, message: str)
        
        Validation:
        ✅ Prevents negative amounts
        ✅ Prevents self-transfer
        ✅ Checks sender balance
        ✅ Auto-creates receiver if needed
        ✅ Atomic database commit (no partial transfers)
        """
        return self.db.transfer_coins(sender_id, receiver_id, amount)
    
    # ========================================
    # DATABASE VALIDATION & CLEANUP
    # ========================================
    
    def cleanup_fake_users(self) -> dict:
        """
        Remove all FAKE/INVALID user IDs from database.
        
        Returns: {
            'success': True,
            'removed_count': int,
            'removed_ids': List[int],
            'message': str
        }
        
        This function:
        ✔ Identifies all invalid Telegram user IDs
        ✔ Removes them from database permanently
        ✔ Logs all changes
        ✔ Returns details for verification
        """
        removed_count, removed_ids = self.db.cleanup_fake_users()
        
        message = f"✅ Database cleaned! Removed {removed_count} fake user(s)."
        if removed_count > 0:
            message += f"\nRemoved IDs: {removed_ids}"
        
        return {
            'success': removed_count >= 0,
            'removed_count': removed_count,
            'removed_ids': removed_ids,
            'message': message
        }
    
    def get_fake_users_list(self) -> List[int]:
        """
        Get list of all FAKE/INVALID user IDs (without deleting).
        
        Useful for verification before cleanup.
        
        Returns: List of invalid user IDs
        """
        return self.db.get_fake_users()
