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
import os

logger = logging.getLogger(__name__)

# ========================
# USER VALIDATION FUNCTIONS
# ========================

def is_valid_telegram_id(user_id: int) -> bool:
    """
    Validate if user_id is a legitimate Telegram ID.
    
    Rules:
    ✔ Must be >= 100000000 (9+ digits, realistic Telegram ID range)
    ✔ Must be <= 9999999999 (reasonable upper bound)
    ✔ Cannot start with "000" pattern
    ✔ Cannot be suspiciously formatted
    
    Returns: True if valid, False if fake/invalid
    """
    # Convert to int if string
    if isinstance(user_id, str):
        try:
            user_id = int(user_id)
        except ValueError:
            logger.warning(f"⚠️ Invalid user_id format: {user_id}")
            return False
    
    # Telegram user IDs should be >= 100000000 (9+ digits)
    if user_id < 100000000:
        logger.warning(f"❌ FAKE USER ID DETECTED: {user_id} (too small)")
        return False
    
    # Reasonable upper bound for user IDs
    if user_id > 9999999999:
        logger.warning(f"❌ FAKE USER ID DETECTED: {user_id} (too large)")
        return False
    
    # Check for suspicious patterns
    user_str = str(user_id)
    
    # Starts with "000" pattern (like "00000010", "00010000")
    if user_str.startswith("000"):
        logger.warning(f"❌ FAKE USER ID DETECTED: {user_id} (suspicious 000 pattern)")
        return False
    
    return True

# ========================
# ENSURE DATA DIRECTORY EXISTS
# ========================

# Use absolute path for database persistence
# This ensures data survives bot redeployments
SCRIPT_DIR = Path(__file__).parent.absolute()
DATA_DIR = SCRIPT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

logger.info(f"📁 Data directory: {DATA_DIR}")

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
    
    ✅ Uses ABSOLUTE PATH to ensure data persists across updates
    ✅ Data stored in /data/economy.db (project directory)
    ✅ Never gets lost during redeployment
    """
    
    def __init__(self, db_file: str = "economy.db"):
        """Initialize SQLite economy database with ABSOLUTE path."""
        # Use absolute path to survive redeployments
        if Path(db_file).is_absolute():
            self.db_file = db_file
        else:
            # Store in data directory (persistent across deployments)
            self.db_file = str(DATA_DIR / db_file)
        
        logger.info(f"💾 Economy database path (ABSOLUTE): {self.db_file}")
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
                
                # Create achievements table (persistent achievement tracking)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS achievements (
                        user_id INTEGER,
                        achievement_key TEXT,
                        unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(user_id, achievement_key),
                        FOREIGN KEY(user_id) REFERENCES users(user_id)
                    )
                """)
                
                # Create player_stats table (extended statistics)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS player_stats (
                        user_id INTEGER PRIMARY KEY,
                        total_wins INTEGER DEFAULT 0,
                        total_losses INTEGER DEFAULT 0,
                        total_bets INTEGER DEFAULT 0,
                        biggest_win INTEGER DEFAULT 0,
                        coins_sent INTEGER DEFAULT 0,
                        coins_received INTEGER DEFAULT 0,
                        win_streak INTEGER DEFAULT 0,
                        max_win_streak INTEGER DEFAULT 0,
                        games_played INTEGER DEFAULT 0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(user_id)
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
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_achievements_user 
                    ON achievements(user_id)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_player_stats_wins 
                    ON player_stats(total_wins DESC)
                """)
                
                conn.commit()
                
                # Verify database is working
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM achievements")
                achievement_count = cursor.fetchone()[0]
                
                logger.info(f"✅ Economy database initialized")
                logger.info(f"   📁 Path: {self.db_file}")
                logger.info(f"   👥 Users: {user_count}")
                logger.info(f"   🏆 Achievements: {achievement_count}")
                logger.info(f"   ✨ Achievement system ACTIVE (persistent)")
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
    
    def get_top_users(self, limit: int = 10) -> List[Tuple[int, str, str, int]]:
        """
        Get top users by balance with validation (for leaderboard).
        
        Returns: [(user_id, username, first_name, balance), ...]
        
        Features:
        ✔ Automatically filters out FAKE/INVALID user IDs
        ✔ Only returns valid Telegram users
        ✔ Includes user display info (username, first_name)
        ✔ Real-time from database
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, username, first_name, balance
                    FROM users
                    ORDER BY balance DESC
                    LIMIT ?
                """, (limit * 2,))  # Fetch extra in case some are invalid
                
                all_users = cursor.fetchall()
            
            # Filter out FAKE/INVALID user IDs
            valid_users = []
            for user_id, username, first_name, balance in all_users:
                if is_valid_telegram_id(user_id):
                    valid_users.append((user_id, username, first_name, balance))
                    if len(valid_users) >= limit:
                        break  # Got enough valid users
                else:
                    logger.warning(f"⚠️ Skipping invalid user in leaderboard: {user_id}")
            
            return valid_users
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
    
    # ========================
    # COIN TRANSFER (ATOMIC)
    # ========================
    
    def transfer_coins(self, sender_id: int, receiver_id: int, amount: int) -> tuple[bool, str]:
        """
        Transfer coins from sender to receiver (ATOMIC operation).
        
        Returns: (success: bool, message: str)
        
        Validation:
        ✅ Prevents negative amounts
        ✅ Prevents self-transfer
        ✅ Checks sender balance
        ✅ Auto-creates receiver if needed
        ✅ Atomic commit (no partial transfers)
        """
        # ========== VALIDATION ==========
        
        if amount <= 0:
            return False, "Amount must be positive"
        
        if sender_id == receiver_id:
            return False, "Cannot send coins to yourself"
        
        try:
            # Auto-register both users
            self.register_user(sender_id)
            self.register_user(receiver_id)
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Check sender balance
                cursor.execute("SELECT balance FROM users WHERE user_id = ?", (sender_id,))
                result = cursor.fetchone()
                
                if not result or result[0] < amount:
                    return False, "Insufficient balance"
                
                # ========== TRANSFER (ATOMIC) ==========
                
                # Subtract from sender
                cursor.execute("""
                    UPDATE users
                    SET balance = balance - ?, last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (amount, sender_id))
                
                # Add to receiver
                cursor.execute("""
                    UPDATE users
                    SET balance = balance + ?, last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (amount, receiver_id))
                
                # Commit both changes atomically
                conn.commit()
                
                logger.info(f"💸 Transfer: {sender_id} → {receiver_id}: {amount} coins")
                return True, f"✅ Transferred {amount} coins to user {receiver_id}"
        
        except Exception as e:
            logger.error(f"❌ Transfer error: {e}")
            return False, "Transfer failed (database error)"
    
    # ========================
    # ACHIEVEMENT SYSTEM
    # ========================
    
    def unlock_achievement(self, user_id: int, achievement_key: str) -> bool:
        """
        Unlock an achievement for a user.
        Uses INSERT OR IGNORE to prevent duplicate unlocks.
        
        Returns: True if newly unlocked or already exists
        """
        try:
            self.register_user(user_id)
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO achievements (user_id, achievement_key)
                    VALUES (?, ?)
                """, (user_id, achievement_key))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error unlocking achievement {achievement_key} for {user_id}: {e}")
            return False
    
    def is_achievement_unlocked(self, user_id: int, achievement_key: str) -> bool:
        """Check if user has already unlocked an achievement."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 1 FROM achievements
                    WHERE user_id = ? AND achievement_key = ?
                """, (user_id, achievement_key))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"❌ Error checking achievement: {e}")
            return False
    
    def get_user_achievements(self, user_id: int) -> list:
        """Get all unlocked achievements for a user."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT achievement_key, unlocked_at FROM achievements
                    WHERE user_id = ?
                    ORDER BY unlocked_at DESC
                """, (user_id,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Error getting achievements: {e}")
            return []
    
    def get_player_stats(self, user_id: int) -> dict:
        """Get extended player statistics."""
        try:
            self.register_user(user_id)
            with sqlite3.connect(self.db_file) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM player_stats WHERE user_id = ?
                """, (user_id,))
                result = cursor.fetchone()
                
                if result:
                    return dict(result)
                else:
                    # Create default stats
                    cursor.execute("""
                        INSERT INTO player_stats (user_id)
                        VALUES (?)
                    """, (user_id,))
                    conn.commit()
                    return {
                        'user_id': user_id,
                        'total_wins': 0,
                        'total_losses': 0,
                        'total_bets': 0,
                        'biggest_win': 0,
                        'coins_sent': 0,
                        'coins_received': 0,
                        'win_streak': 0,
                        'max_win_streak': 0,
                        'games_played': 0
                    }
        except Exception as e:
            logger.error(f"❌ Error getting player stats: {e}")
            return {}
    
    def update_player_stats(self, user_id: int, **kwargs) -> bool:
        """
        Update player statistics (flexible).
        
        Example: update_player_stats(user_id, total_wins=10, biggest_win=500)
        """
        try:
            self.register_user(user_id)
            
            # Ensure stats entry exists
            self.get_player_stats(user_id)
            
            if not kwargs:
                return True
            
            # Build update query
            set_clause = ", ".join([f"{key} = {key} + ?" if key.startswith('total_') or key.startswith('coins_') else f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(user_id)
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE player_stats
                    SET {set_clause}, last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, values)
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error updating player stats: {e}")
            return False
    
    def increment_stat(self, user_id: int, stat_name: str, amount: int = 1) -> bool:
        """Increment a stat by amount (for counters)."""
        try:
            self.register_user(user_id)
            self.get_player_stats(user_id)  # Ensure exists
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE player_stats
                    SET {stat_name} = {stat_name} + ?, last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (amount, user_id))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error incrementing stat {stat_name}: {e}")
            return False
    
    def set_stat(self, user_id: int, stat_name: str, value: int) -> bool:
        """Set a stat to exact value."""
        try:
            self.register_user(user_id)
            self.get_player_stats(user_id)  # Ensure exists
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE player_stats
                    SET {stat_name} = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (value, user_id))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error setting stat {stat_name}: {e}")
            return False
    
    # ========================
    # DATABASE CLEANUP (REMOVE FAKE USERS)
    # ========================
    
    def cleanup_fake_users(self) -> tuple[int, List[int]]:
        """
        Remove all FAKE/INVALID user IDs from database.
        
        Returns: (removed_count: int, removed_ids: List[int])
        
        This function:
        ✔ Identifies all invalid user IDs
        ✔ Removes them from database
        ✔ Logs the cleanup
        ✔ Returns list of removed IDs for verification
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Get all users
                cursor.execute("SELECT user_id FROM users ORDER BY user_id")
                all_users = cursor.fetchall()
                
                removed_ids = []
                removed_count = 0
                
                # Check each user
                for (user_id,) in all_users:
                    if not is_valid_telegram_id(user_id):
                        # Delete this user
                        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                        removed_ids.append(user_id)
                        removed_count += 1
                        logger.warning(f"🗑️ Removed fake user from database: {user_id}")
                
                conn.commit()
                
                if removed_count > 0:
                    logger.info(f"✅ Database cleanup complete: Removed {removed_count} fake users")
                    logger.info(f"📋 Removed IDs: {removed_ids}")
                else:
                    logger.info(f"✅ Database cleanup complete: No fake users found")
                
                return removed_count, removed_ids
        except Exception as e:
            logger.error(f"❌ Error cleaning up fake users: {e}")
            return 0, []
    
    def get_fake_users(self) -> List[int]:
        """
        List all FAKE/INVALID user IDs without deleting them.
        
        Useful for verification before cleanup.
        
        Returns: List of invalid user IDs
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id FROM users ORDER BY user_id")
                all_users = cursor.fetchall()
                
                fake_users = []
                for (user_id,) in all_users:
                    if not is_valid_telegram_id(user_id):
                        fake_users.append(user_id)
                
                return fake_users
        except Exception as e:
            logger.error(f"❌ Error getting fake users list: {e}")
            return []
