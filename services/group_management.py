"""Production moderation and group-management services.

This module intentionally plugs into the current monolithic bot while providing
the durable foundation needed for a cleaner modular architecture.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


DB_PATH = Path("data/group_management.db")
BACKUP_DIR = Path("data/backups")


DEFAULT_SETTINGS = {
    "guardian": False,
    "antispam": True,
    "antilink": False,
    "antiflood": True,
    "antiemoji": False,
    "antiraid": True,
    "captcha": False,
    "ai_enabled": True,
    "slowmode": 0,
    "spam_threshold": 5,
    "flood_window": 10,
    "raid_join_threshold": 8,
    "raid_window": 60,
    "warnings_limit": 3,
    "punishment": "mute",
    "log_channel": "",
    "group_language": "en",
    "rules": "No rules have been set yet.",
    "welcome": "Welcome {mention} to {chat}!",
    "goodbye": "Goodbye {name}.",
}


@dataclass(frozen=True)
class TargetUser:
    user_id: int
    display_name: str


class GroupStore:
    """SQLite store for moderation logs, settings, reports, and analytics."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS mod_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    actor_id INTEGER,
                    target_id INTEGER,
                    action TEXT NOT NULL,
                    reason TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_mod_logs_chat_created
                    ON mod_logs(chat_id, created_at DESC);

                CREATE TABLE IF NOT EXISTS chat_settings (
                    chat_id INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(chat_id, key)
                );

                CREATE TABLE IF NOT EXISTS permanent_bans (
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    reason TEXT,
                    created_by INTEGER,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(chat_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS message_stats (
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    message_count INTEGER NOT NULL DEFAULT 0,
                    last_seen TEXT NOT NULL,
                    PRIMARY KEY(chat_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    reporter_id INTEGER NOT NULL,
                    target_id INTEGER,
                    reason TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER,
                    event_type TEXT NOT NULL,
                    detail TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS notes (
                    chat_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_by INTEGER,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(chat_id, name)
                );
                """
            )

    @staticmethod
    def now() -> str:
        return datetime.utcnow().isoformat(timespec="seconds")

    def log_action(
        self,
        chat_id: int,
        actor_id: int | None,
        action: str,
        target_id: int | None = None,
        reason: str | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO mod_logs(chat_id, actor_id, target_id, action, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (chat_id, actor_id, target_id, action, reason, self.now()),
            )

    def recent_logs(self, chat_id: int, limit: int = 10) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM mod_logs WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
                (chat_id, limit),
            ).fetchall()

    def set_setting(self, chat_id: int, key: str, value: Any) -> None:
        payload = json.dumps(value)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_settings(chat_id, key, value, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(chat_id, key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (chat_id, key, payload, self.now()),
            )

    def get_setting(self, chat_id: int, key: str, default: Any = None) -> Any:
        if default is None:
            default = DEFAULT_SETTINGS.get(key)
        with self.connect() as conn:
            row = conn.execute(
                "SELECT value FROM chat_settings WHERE chat_id = ? AND key = ?",
                (chat_id, key),
            ).fetchone()
        return json.loads(row["value"]) if row else default

    def all_settings(self, chat_id: int) -> dict[str, Any]:
        settings = dict(DEFAULT_SETTINGS)
        with self.connect() as conn:
            rows = conn.execute("SELECT key, value FROM chat_settings WHERE chat_id = ?", (chat_id,)).fetchall()
        for row in rows:
            settings[row["key"]] = json.loads(row["value"])
        return settings

    def add_permanent_ban(self, chat_id: int, user_id: int, reason: str, created_by: int) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO permanent_bans(chat_id, user_id, reason, created_by, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (chat_id, user_id, reason, created_by, self.now()),
            )
        self.log_action(chat_id, created_by, "permanent_ban", user_id, reason)

    def remove_permanent_ban(self, chat_id: int, user_id: int, actor_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM permanent_bans WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        self.log_action(chat_id, actor_id, "permanent_unban", user_id)

    def is_permanently_banned(self, chat_id: int, user_id: int) -> bool:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM permanent_bans WHERE chat_id = ? AND user_id = ?",
                (chat_id, user_id),
            ).fetchone()
        return row is not None

    def permanent_bans(self, chat_id: int, limit: int = 50) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM permanent_bans WHERE chat_id = ? ORDER BY created_at DESC LIMIT ?",
                (chat_id, limit),
            ).fetchall()

    def record_message(self, chat_id: int, user_id: int) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO message_stats(chat_id, user_id, message_count, last_seen)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(chat_id, user_id) DO UPDATE SET
                    message_count = message_count + 1,
                    last_seen = excluded.last_seen
                """,
                (chat_id, user_id, self.now()),
            )

    def top_active(self, chat_id: int, limit: int = 10) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM message_stats WHERE chat_id = ? ORDER BY message_count DESC LIMIT ?",
                (chat_id, limit),
            ).fetchall()

    def inactive(self, chat_id: int, days: int = 30, limit: int = 10) -> list[sqlite3.Row]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat(timespec="seconds")
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT * FROM message_stats
                WHERE chat_id = ? AND last_seen < ?
                ORDER BY last_seen ASC LIMIT ?
                """,
                (chat_id, cutoff, limit),
            ).fetchall()

    def add_report(self, chat_id: int, reporter_id: int, target_id: int | None, reason: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO reports(chat_id, reporter_id, target_id, reason, created_at) VALUES (?, ?, ?, ?, ?)",
                (chat_id, reporter_id, target_id, reason, self.now()),
            )
        self.log_action(chat_id, reporter_id, "report", target_id, reason)

    def log_security_event(self, chat_id: int, event_type: str, user_id: int | None = None, detail: str = "") -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO security_events(chat_id, user_id, event_type, detail, created_at) VALUES (?, ?, ?, ?, ?)",
                (chat_id, user_id, event_type, detail, self.now()),
            )

    def security_counts(self, chat_id: int, minutes: int = 60) -> dict[str, int]:
        cutoff = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat(timespec="seconds")
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT event_type, COUNT(*) AS count
                FROM security_events
                WHERE chat_id = ? AND created_at >= ?
                GROUP BY event_type
                """,
                (chat_id, cutoff),
            ).fetchall()
        return {row["event_type"]: row["count"] for row in rows}

    def save_note(self, chat_id: int, name: str, value: str, actor_id: int) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO notes(chat_id, name, value, created_by, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(chat_id, name) DO UPDATE SET
                    value = excluded.value,
                    created_by = excluded.created_by,
                    updated_at = excluded.updated_at
                """,
                (chat_id, name.lower(), value, actor_id, self.now()),
            )

    def get_note(self, chat_id: int, name: str) -> str | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT value FROM notes WHERE chat_id = ? AND name = ?",
                (chat_id, name.lower()),
            ).fetchone()
        return row["value"] if row else None

    def delete_note(self, chat_id: int, name: str) -> bool:
        with self.connect() as conn:
            cur = conn.execute("DELETE FROM notes WHERE chat_id = ? AND name = ?", (chat_id, name.lower()))
            return cur.rowcount > 0

    def list_notes(self, chat_id: int) -> list[str]:
        with self.connect() as conn:
            rows = conn.execute("SELECT name FROM notes WHERE chat_id = ? ORDER BY name", (chat_id,)).fetchall()
        return [row["name"] for row in rows]

    def backup(self) -> Path:
        stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        dest = BACKUP_DIR / f"group_management-{stamp}.db"
        shutil.copy2(self.db_path, dest)
        return dest


class SecurityService:
    """In-memory fast checks backed by durable incident logs."""

    def __init__(self, store: GroupStore) -> None:
        self.store = store
        self.messages: dict[tuple[int, int], list[tuple[float, str]]] = {}
        self.joins: dict[int, list[float]] = {}

    def record_join(self, chat_id: int, user_id: int) -> str | None:
        now = time.time()
        joins = self.joins.setdefault(chat_id, [])
        joins.append(now)
        joins[:] = [stamp for stamp in joins if now - stamp <= 60]
        threshold = int(self.store.get_setting(chat_id, "raid_join_threshold", 8))
        if len(joins) >= threshold:
            self.store.log_security_event(chat_id, "raid", user_id, f"{len(joins)} joins in 60s")
            return "Possible raid detected from excessive joins."
        return None

    def inspect_message(self, chat_id: int, user_id: int, text: str) -> list[str]:
        findings: list[str] = []
        now = time.time()
        key = (chat_id, user_id)
        window = int(self.store.get_setting(chat_id, "flood_window", 10))
        threshold = int(self.store.get_setting(chat_id, "spam_threshold", 5))
        messages = self.messages.setdefault(key, [])
        messages.append((now, text))
        messages[:] = [(stamp, msg) for stamp, msg in messages if now - stamp <= window]

        lowered = text.lower()
        if self.store.get_setting(chat_id, "antilink", False) and ("http://" in lowered or "https://" in lowered or "t.me/" in lowered):
            findings.append("link_spam")
        if self.store.get_setting(chat_id, "antiflood", True) and len(messages) >= threshold:
            findings.append("flood")
        if len({msg for _, msg in messages[-3:]}) == 1 and len(messages) >= 3:
            findings.append("repeated_messages")
        if text.count("@") >= 6:
            findings.append("mention_spam")
        if self.store.get_setting(chat_id, "antiemoji", False) and _emoji_density(text) > 0.65 and len(text) >= 12:
            findings.append("emoji_spam")

        for finding in findings:
            self.store.log_security_event(chat_id, finding, user_id, text[:200])
        return findings

    def threat_level(self, chat_id: int) -> str:
        counts = self.store.security_counts(chat_id, 60)
        score = sum(counts.values())
        if counts.get("raid", 0) or score >= 20:
            return "CRITICAL"
        if score >= 10:
            return "HIGH"
        if score >= 4:
            return "MEDIUM"
        return "LOW"

    def alt_risk(self, chat_id: int, user_id: int, username: str = "") -> tuple[str, list[str]]:
        counts = self.store.security_counts(chat_id, 24 * 60)
        reasons: list[str] = []
        score = 0
        if counts.get("flood", 0) or counts.get("repeated_messages", 0):
            score += 2
            reasons.append("recent spam-like behavior in the group")
        if counts.get("raid", 0):
            score += 2
            reasons.append("joined or appeared during suspicious join timing")
        if username and sum(ch.isdigit() for ch in username) >= 4:
            score += 1
            reasons.append("username contains many digits")
        with self.store.connect() as conn:
            punishments = conn.execute(
                "SELECT COUNT(*) AS count FROM mod_logs WHERE chat_id = ? AND target_id = ?",
                (chat_id, user_id),
            ).fetchone()["count"]
        if punishments:
            score += 2
            reasons.append("previous moderation history exists")
        if score >= 4:
            return "HIGH RISK", reasons
        if score >= 2:
            return "MEDIUM RISK", reasons
        return "LOW RISK", reasons or ["no strong suspicious indicators found"]


def _emoji_density(text: str) -> float:
    if not text:
        return 0.0
    emoji_like = sum(1 for char in text if ord(char) > 10000)
    return emoji_like / max(len(text), 1)


store = GroupStore()
security_service = SecurityService(store)
