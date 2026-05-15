"""
Economy System for Whisky_bot
Manages virtual coins, balances, and economy transactions
⚠️ VIRTUAL CURRENCY ONLY - NO REAL MONEY VALUE
"""

import logging
from datetime import datetime, timedelta
from config import (
    STARTING_BALANCE, 
    MIN_BET, 
    MAX_BET,
    DAILY_REWARD,
    DAILY_COOLDOWN,
    OWNER_ID
)
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# Economy data file
ECONOMY_FILE = "economy_data.json"

class Economy:
    """Handles all economy-related operations."""
    
    def __init__(self, data_dict: dict):
        """Initialize economy system with reference to bot_data."""
        self.bot_data = data_dict
        self._ensure_economy_structure()
    
    def _ensure_economy_structure(self):
        """Ensure economy data structure exists in bot_data."""
        if "economy" not in self.bot_data:
            self.bot_data["economy"] = {}
        if "daily_claims" not in self.bot_data:
            self.bot_data["daily_claims"] = {}
        if "economy_log" not in self.bot_data:
            self.bot_data["economy_log"] = []
    
    def get_balance(self, user_id: int) -> int:
        """Get user's coin balance. Returns starting balance if new user."""
        user_id_str = str(user_id)
        if user_id_str not in self.bot_data["economy"]:
            self.bot_data["economy"][user_id_str] = STARTING_BALANCE
            self._log_transaction("ACCOUNT_CREATED", user_id, 0, STARTING_BALANCE, f"New account started with {STARTING_BALANCE} coins")
        return self.bot_data["economy"][user_id_str]
    
    def add_coins(self, user_id: int, amount: int, reason: str = "Coins added") -> tuple[bool, str]:
        """Add coins to user's balance."""
        user_id_str = str(user_id)
        
        if amount < 0:
            return False, "❌ Cannot add negative coins"
        
        # Ensure user exists
        balance = self.get_balance(user_id)
        new_balance = balance + amount
        
        self.bot_data["economy"][user_id_str] = new_balance
        self._log_transaction("ADD_COINS", user_id, amount, new_balance, reason)
        
        return True, f"✅ Added {amount} coins to {user_id}"
    
    def remove_coins(self, user_id: int, amount: int, reason: str = "Coins removed") -> tuple[bool, str]:
        """Remove coins from user's balance."""
        user_id_str = str(user_id)
        
        if amount < 0:
            return False, "❌ Cannot remove negative coins"
        
        balance = self.get_balance(user_id)
        
        if balance < amount:
            return False, "❌ Insufficient balance"
        
        new_balance = balance - amount
        self.bot_data["economy"][user_id_str] = new_balance
        self._log_transaction("REMOVE_COINS", user_id, amount, new_balance, reason)
        
        return True, f"✅ Removed {amount} coins from {user_id}"
    
    def set_coins(self, user_id: int, amount: int, reason: str = "Balance set") -> tuple[bool, str]:
        """Set user's balance to exact amount."""
        user_id_str = str(user_id)
        
        if amount < 0:
            return False, "❌ Cannot set negative balance"
        
        old_balance = self.get_balance(user_id)
        self.bot_data["economy"][user_id_str] = amount
        self._log_transaction("SET_COINS", user_id, amount - old_balance, amount, reason)
        
        return True, f"✅ Set {user_id} balance to {amount} coins"
    
    def transfer_coins(self, from_user_id: int, to_user_id: int, amount: int) -> tuple[bool, str]:
        """Transfer coins between users."""
        # Check source has enough
        from_balance = self.get_balance(from_user_id)
        if from_balance < amount:
            return False, f"❌ You only have {from_balance} coins"
        
        # Remove from source
        success, msg = self.remove_coins(from_user_id, amount, f"Transferred to {to_user_id}")
        if not success:
            return False, msg
        
        # Add to recipient
        success, msg = self.add_coins(to_user_id, amount, f"Received from {from_user_id}")
        if not success:
            # Rollback
            self.add_coins(from_user_id, amount, "Transfer rollback")
            return False, msg
        
        return True, f"✅ Transferred {amount} coins"
    
    def validate_bet(self, amount: int) -> tuple[bool, str]:
        """Validate bet amount."""
        if amount < MIN_BET:
            return False, f"❌ Minimum bet is {MIN_BET} coins"
        if amount > MAX_BET:
            return False, f"❌ Maximum bet is {MAX_BET} coins"
        if amount < 1:
            return False, "❌ Bet must be positive"
        return True, ""
    
    def claim_daily(self, user_id: int) -> tuple[bool, str, int]:
        """Claim daily reward. Returns (success, message, coins_gained)."""
        user_id_str = str(user_id)
        now = datetime.now().isoformat()
        
        # Check if user already claimed today
        if user_id_str in self.bot_data["daily_claims"]:
            last_claim = datetime.fromisoformat(self.bot_data["daily_claims"][user_id_str])
            time_until_next = last_claim + timedelta(seconds=DAILY_COOLDOWN)
            
            if datetime.now() < time_until_next:
                hours_left = int((time_until_next - datetime.now()).total_seconds() / 3600)
                minutes_left = int(((time_until_next - datetime.now()).total_seconds() % 3600) / 60)
                return False, f"⏱️ Daily reward available in {hours_left}h {minutes_left}m", 0
        
        # Give daily reward
        self.bot_data["daily_claims"][user_id_str] = now
        success, msg = self.add_coins(user_id, DAILY_REWARD, "Daily reward claimed")
        
        return True, f"🎁 Claimed {DAILY_REWARD} coins!", DAILY_REWARD
    
    def get_top_users(self, limit: int = 10) -> list:
        """Get richest users (leaderboard)."""
        users = []
        for user_id_str, balance in self.bot_data["economy"].items():
            users.append((int(user_id_str), balance))
        
        # Sort by balance (highest first)
        users.sort(key=lambda x: x[1], reverse=True)
        return users[:limit]
    
    def _log_transaction(self, transaction_type: str, user_id: int, amount: int, new_balance: int, reason: str = ""):
        """Log all economy transactions."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": transaction_type,
            "user_id": user_id,
            "amount": amount,
            "new_balance": new_balance,
            "reason": reason
        }
        self.bot_data["economy_log"].append(log_entry)
        
        # Keep last 1000 transactions to prevent huge logs
        if len(self.bot_data["economy_log"]) > 1000:
            self.bot_data["economy_log"] = self.bot_data["economy_log"][-1000:]
        
        logger.info(f"💰 [{transaction_type}] User {user_id}: {amount} coins ({reason})")
