"""
Database module for Whisky_bot
Handles all data persistence operations - BOTH File-based JSON and SQLite Economy
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from config import DATA_FILE
from datetime import datetime

logger = logging.getLogger(__name__)

# ========================
# FILE-BASED JSON DATABASE (Legacy: warnings, mutes, etc)
# ========================

class BotDatabase:
    """Simple file-based database for bot data."""
    
    def __init__(self, filepath: str = DATA_FILE):
        self.filepath = filepath
        self.data = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Load data from file."""
        if Path(self.filepath).exists():
            try:
                with open(self.filepath, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading database: {e}")
        return self._default_data()
    
    @staticmethod
    def _default_data() -> Dict[str, Any]:
        """Return default data structure."""
        return {
            "warnings": {},
            "stats": {},
            "mutes": {}
        }
    
    def save(self) -> bool:
        """Save data to file."""
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.data, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving database: {e}")
            return False
    
    # Warnings
    def get_warnings(self, user_id: int) -> int:
        """Get warning count for user."""
        return int(self.data["warnings"].get(str(user_id), 0))
    
    def add_warning(self, user_id: int) -> int:
        """Add warning to user and return new count."""
        user_id_str = str(user_id)
        self.data["warnings"][user_id_str] = self.get_warnings(user_id) + 1
        self.save()
        return self.data["warnings"][user_id_str]
    
    def reset_warnings(self, user_id: int) -> bool:
        """Reset user warnings."""
        user_id_str = str(user_id)
        if user_id_str in self.data["warnings"]:
            self.data["warnings"][user_id_str] = 0
            return self.save()
        return False
    
    # Stats
    def get_stats(self, user_id: int) -> Dict[str, int]:
        """Get user statistics."""
        user_id_str = str(user_id)
        return self.data["stats"].get(user_id_str, {
            "messages_sent": 0,
            "ai_queries": 0,
            "warnings": 0
        })
    
    def init_user_stats(self, user_id: int) -> None:
        """Initialize stats for new user."""
        user_id_str = str(user_id)
        if user_id_str not in self.data["stats"]:
            self.data["stats"][user_id_str] = {
                "messages_sent": 0,
                "ai_queries": 0,
                "warnings": 0
            }
    
    def increment_messages(self, user_id: int) -> int:
        """Increment message count and return new value."""
        user_id_str = str(user_id)
        self.init_user_stats(user_id)
        self.data["stats"][user_id_str]["messages_sent"] += 1
        self.save()
        return self.data["stats"][user_id_str]["messages_sent"]
    
    def increment_ai_queries(self, user_id: int) -> int:
        """Increment AI query count and return new value."""
        user_id_str = str(user_id)
        self.init_user_stats(user_id)
        self.data["stats"][user_id_str]["ai_queries"] += 1
        self.save()
        return self.data["stats"][user_id_str]["ai_queries"]
    
    def increment_warnings_stat(self, user_id: int) -> int:
        """Increment warning stat count."""
        user_id_str = str(user_id)
        self.init_user_stats(user_id)
        self.data["stats"][user_id_str]["warnings"] += 1
        self.save()
        return self.data["stats"][user_id_str]["warnings"]
    
    # Admin utilities
    def get_all_users(self) -> list:
        """Get all tracked users."""
        return list(self.data["stats"].keys())
    
    def get_user_count(self) -> int:
        """Get total number of tracked users."""
        return len(self.data["stats"])
    
    def get_total_messages(self) -> int:
        """Get total messages across all users."""
        return sum(u.get("messages_sent", 0) for u in self.data["stats"].values())
    
    def get_total_ai_queries(self) -> int:
        """Get total AI queries across all users."""
        return sum(u.get("ai_queries", 0) for u in self.data["stats"].values())

# ========================
# SQLITE ECONOMY DATABASE (Persistent user balances)
# ========================

class EconomyDatabase:
    """
    SQLite-based persistent economy system.
    Survives bot restarts, crashes, and redeployments.
    """
    
    def __init__(self, db_file: str = "economy.db"):
        """Initialize SQLite economy database."""
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """Create users table if it doesn't exist with full schema and indexes."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Create users table with all persistence columns
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        balance INTEGER DEFAULT 100,
                        total_wins INTEGER DEFAULT 0,
                        total_losses INTEGER DEFAULT 0,
                        daily_claim_timestamp TIMESTAMP,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create performance indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_balance 
                    ON users(balance DESC)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_daily_claim 
                    ON users(daily_claim_timestamp)
                """)
                
                conn.commit()
                logger.info(f"✅ Economy database initialized with indexes: {self.db_file}")
        except Exception as e:
            logger.error(f"❌ Error initializing economy database: {e}")
    
    def register_user(self, user_id: int, username: str = "", first_name: str = "", starting_balance: int = 100) -> bool:
        """
        Auto-register user if not exists.
        Returns True if user was created or already exists.
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO users (user_id, username, first_name, balance)
                    VALUES (?, ?, ?, ?)
                """, (user_id, username or "", first_name or "", starting_balance))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error registering user {user_id}: {e}")
            return False
    
    def get_balance(self, user_id: int, starting_balance: int = 100) -> int:
        """
        Get user balance from database.
        Auto-creates user if not exists.
        """
        try:
            # Auto-register if needed
            self.register_user(user_id, starting_balance=starting_balance)
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                return result[0] if result else starting_balance
        except Exception as e:
            logger.error(f"❌ Error getting balance for {user_id}: {e}")
            return starting_balance
    
    def set_balance(self, user_id: int, balance: int) -> bool:
        """Atomically set user balance."""
        try:
            self.register_user(user_id)
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET balance = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (balance, user_id))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error setting balance for {user_id}: {e}")
            return False
    
    def add_balance(self, user_id: int, amount: int) -> bool:
        """Atomically add to user balance."""
        try:
            self.register_user(user_id)
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET balance = balance + ?, last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (amount, user_id))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error adding balance for {user_id}: {e}")
            return False
    
    def subtract_balance(self, user_id: int, amount: int) -> bool:
        """Atomically subtract from user balance."""
        return self.add_balance(user_id, -amount)
    
    def get_top_users(self, limit: int = 10) -> List[Tuple[int, int]]:
        """
        Get top users by balance (for leaderboard).
        Returns list of (user_id, balance) tuples.
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, balance
                    FROM users
                    ORDER BY balance DESC
                    LIMIT ?
                """, (limit,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Error getting top users: {e}")
            return []
    
    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Get all info for a user."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"❌ Error getting user info for {user_id}: {e}")
            return None
    
    def update_user_info(self, user_id: int, username: str = "", first_name: str = "") -> bool:
        """Update user's username and first name."""
        try:
            self.register_user(user_id, username, first_name)
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET username = ?, first_name = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (username, first_name, user_id))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error updating user info for {user_id}: {e}")
            return False
    
    def increment_wins(self, user_id: int) -> bool:
        """Increment win count."""
        try:
            self.register_user(user_id)
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET total_wins = total_wins + 1, last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (user_id,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error incrementing wins for {user_id}: {e}")
            return False
    
    def increment_losses(self, user_id: int) -> bool:
        """Increment loss count."""
        try:
            self.register_user(user_id)
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET total_losses = total_losses + 1, last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (user_id,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error incrementing losses for {user_id}: {e}")
            return False
    
    def get_user_count(self) -> int:
        """Get total number of users in economy."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"❌ Error getting user count: {e}")
            return 0
    
    def get_last_daily_claim(self, user_id: int) -> Optional[datetime]:
        """Get user's last daily claim timestamp from database (persistent)."""
        try:
            self.register_user(user_id)
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT daily_claim_timestamp FROM users WHERE user_id = ?",
                    (user_id,)
                )
                result = cursor.fetchone()
                if result and result[0]:
                    return datetime.fromisoformat(result[0])
                return None
        except Exception as e:
            logger.error(f"❌ Error getting daily claim timestamp for {user_id}: {e}")
            return None
    
    def set_daily_claim(self, user_id: int) -> bool:
        """Update user's daily claim timestamp to NOW (persistent)."""
        try:
            self.register_user(user_id)
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET daily_claim_timestamp = CURRENT_TIMESTAMP, last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (user_id,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error setting daily claim for {user_id}: {e}")
            return False
