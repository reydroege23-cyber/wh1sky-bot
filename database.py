"""
Database module for Whisky_bot
Handles all data persistence operations
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from config import DATA_FILE

logger = logging.getLogger(__name__)

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
